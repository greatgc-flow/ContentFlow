"""Bounded TEST_ONLY host adapter for local workspace lifecycle operations."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3
import sys
from uuid import UUID

from .assets import _kind
from .checkpoint import _file_hash
from .domain import decode, digest
from .outbox import FixtureOutbox
from .sources import SourceLedger
from .workspace_recovery import checkpoint_workspace, restore_workspace

_LIMIT = 64 * 1024
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_GENERATION = re.compile(r"gen-[a-z0-9][a-z0-9-]{0,63}")
_LEAF = re.compile(r"[a-z][a-z0-9-]{0,63}")
_SHA = re.compile(r"[a-f0-9]{64}")
_ECHO = ("fixture_only", "schema_version", "protocol_version", "request_id", "parent_op_id",
         "installation_id", "package_id", "generation", "operation")
_FIELDS = set(_ECHO) | {"phase", "plan_digest", "scope", "deadline", "working_rel", "checkpoint_rel"}
_POLICY = {"health": ({"STAGED", "VERIFIED", "COMMITTED"}, "PROGRAM"),
           "checkpoint": ({"DRAINED"}, "BACKUP"),
           "restore": ({"APPLYING"}, "DOMAIN_DATA")}


def _matches(rule, value):
    return type(value) is str and rule.fullmatch(value) is not None


def _ordinary(root, relative, *, missing_leaf=False):
    if not root.is_absolute() or _kind(root) != "directory":
        raise ValueError("expected an ordinary system root")
    current = root
    parts = relative.split("/")
    for index, component in enumerate(parts):
        current /= component
        kind = _kind(current)
        if index == len(parts) - 1 and missing_leaf:
            if kind not in (None, "directory"):
                raise ValueError("invalid checkpoint candidate")
        elif kind != "directory":
            raise ValueError("invalid adapter directory")
    return current


def _validate(request, args, now):
    if (type(request) is not dict or request.keys() != _FIELDS or request["fixture_only"] is not True
            or request["schema_version"] != "1.0" or request["protocol_version"] != "1.0"
            or request["package_id"] != "contentflow"
            or request["installation_id"] != args.installation_id or not _matches(_ID, args.installation_id)
            or request["generation"] != args.generation or not _matches(_GENERATION, args.generation)
            or request["plan_digest"] != args.plan_digest or not _matches(_SHA, args.plan_digest)
            or not all(_matches(_ID, request[k]) for k in ("request_id", "parent_op_id"))
            or args.workspace_id.version != 4 or type(request["deadline"]) is not str):
        raise ValueError("invalid bound adapter request")
    deadline = datetime.fromisoformat(request["deadline"])
    if deadline.utcoffset() != timezone.utc.utcoffset(now) or now >= deadline:
        raise ValueError("expired or non-UTC deadline")
    working = f"ContentFlow/app/generations/{args.generation}"
    if request["working_rel"] != working:
        raise ValueError("working directory differs from admitted generation")
    _ordinary(args.root, working)
    op = request["operation"]
    if type(op) is not str or op not in _POLICY:
        raise ValueError("unknown fixture operation")
    phases, scope = _POLICY[op]
    if type(request["phase"]) is not str or request["phase"] not in phases or request["scope"] != [scope]:
        raise ValueError("operation phase or scope mismatch")
    checkpoint_rel = request["checkpoint_rel"]
    if op == "health":
        if checkpoint_rel is not None:
            raise ValueError("health must not name a checkpoint")
    elif not _matches(re.compile(r"ContentFlow/checkpoints/[a-z][a-z0-9-]{0,63}"), checkpoint_rel):
        raise ValueError("invalid checkpoint reference")
    return op


def _response(request, status, observed, *, sha=None, next_action="NONE"):
    receipt = {"effect_id": digest(request), "checkpoint_sha256": sha,
               "observed_state": observed, "owned_process_ids": []}
    return {key: request[key] for key in _ECHO} | {
        "status": status, "findings": [], "receipt": receipt, "next_action": next_action}


def _handle(request, args, op, now):
    if op == "health":
        return _response(request, "OK", "UNCHANGED")
    if not args.allow_fixture_writes:
        return _response(request, "BLOCKED", "UNCHANGED", next_action="REPLAN")
    checkpoint = _ordinary(args.root, request["checkpoint_rel"], missing_leaf=op == "checkpoint")
    target = checkpoint
    if op == "restore":
        key = request["request_id"]
        if not _matches(_LEAF, key):
            raise ValueError("invalid restore candidate identity")
        target = _ordinary(args.root, f"ContentFlow/recovery/{key}", missing_leaf=True)
    if target.exists():
        return _response(request, "UNKNOWN", "UNKNOWN", next_action="RECONCILE")
    live = _ordinary(args.root, "ContentFlow/data/live")
    outbox_path = live / "outbox.sqlite3"
    if _kind(outbox_path) != "file":
        raise ValueError("expected ordinary fixture outbox")
    try:
        with (SourceLedger.open(live, args.workspace_id) as sources,
              FixtureOutbox.open(outbox_path, args.workspace_id) as outbox):
            if op == "checkpoint":
                checkpoint_workspace(sources, outbox, target, now)
            else:
                restore_workspace(sources, outbox, checkpoint, target, now)
        return _response(request, "OK", "NEW", sha=_file_hash(target / "workspace.json"))
    except (OSError, ValueError, sqlite3.Error):
        return _response(request, "UNKNOWN", "UNKNOWN", next_action="RECONCILE")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="contentflow-host-adapter")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--installation-id", required=True)
    parser.add_argument("--generation", required=True)
    parser.add_argument("--workspace-id", type=UUID, required=True)
    parser.add_argument("--plan-digest", required=True)
    parser.add_argument("--allow-fixture-writes", action="store_true")
    args = parser.parse_args(argv)
    try:
        wire = sys.stdin.buffer.read(_LIMIT + 1)
        if len(wire) > _LIMIT:
            raise ValueError("oversized request")
        request = decode(wire)
        now = datetime.now(timezone.utc)
        op = _validate(request, args, now)
        response = _handle(request, args, op, now)
    except (OSError, ValueError):
        print("Invalid fixture adapter request.", file=sys.stderr)
        return 2
    print(json.dumps(response, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
