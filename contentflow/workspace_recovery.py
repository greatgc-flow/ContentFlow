"""Coordinated offline source and pending-effect checkpoint bundles."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID

from . import outbox_recovery, sources as source_recovery
from .assets import _directory, _flush_directory, _kind
from .checkpoint import _file_hash, _new_directory, _put_file
from .domain import MAX_BYTES, canonical, decode, digest
from .outbox import _transaction

_MARKER = "workspace.json"
_CHECKPOINT = "workspace-checkpoint-v1"
_REVIEW = "workspace-review-v1"


def _members(root):
    result = {}

    def scan(current):
        for member in current.iterdir():
            if current == root and member.name == _MARKER:
                continue
            name = member.relative_to(root).as_posix()
            kind = _kind(member)
            if kind == "directory":
                result[name] = None
                scan(member)
            elif kind == "file":
                result[name] = _file_hash(member)
            else:
                raise ValueError("workspace bundle contains an unsupported member")

    scan(root)
    return result


def _seal(root, workspace, kind):
    body = {"format": kind, "workspace": str(workspace), "members": _members(root)}
    wire = canonical({"body": body, "sha256": digest(body)})
    with TemporaryDirectory(prefix=".seal-", dir=root.parent) as scratch:
        stage = Path(scratch) / _MARKER
        _put_file(stage, wire)
        os.link(stage, root / _MARKER)
        _flush_directory(root)
        _flush_directory(root.parent)


def _read(root):
    _directory(root)
    if {p.name for p in root.iterdir()} != {"sources", "outbox.json", _MARKER} or _kind(root / _MARKER) != "file":
        raise ValueError("incomplete workspace bundle")
    with (root / _MARKER).open("rb") as stream:
        record = decode(stream.read(MAX_BYTES + 1))
    if type(record) is not dict or record.keys() != {"body", "sha256"}:
        raise ValueError("invalid workspace seal")
    body = record["body"]
    if (digest(body) != record["sha256"] or type(body) is not dict
            or body.keys() != {"format", "workspace", "members"}
            or body["format"] not in (_CHECKPOINT, _REVIEW)
            or not isinstance(body["workspace"], str) or body["members"] != _members(root)):
        raise ValueError("workspace bundle manifest mismatch")
    workspace = UUID(body["workspace"])
    if workspace.version != 4 or str(workspace) != body["workspace"]:
        raise ValueError("invalid workspace identity")
    return body, workspace


def _current(sources, outbox):
    state = outbox_recovery._state(outbox)
    if state["workspace"] != str(sources.workspace):
        raise ValueError("source and outbox workspace identities differ")
    return state


def _outside(sources, destination):
    if destination.resolve().is_relative_to(sources.root.resolve()):
        raise ValueError("place workspace bundles outside the live source workspace")


def checkpoint_workspace(sources, outbox, destination: Path, now):
    _outside(sources, destination)
    with sources._stable(), _transaction(outbox._db):
        state = _current(sources, outbox)
        with _new_directory(destination):
            source_recovery._capture_sources(sources, destination / "sources", now)
            outbox_recovery._write(destination / "outbox.json", "outbox-checkpoint-v1", state)
            _seal(destination, sources.workspace, _CHECKPOINT)


def restore_workspace(sources, outbox, checkpoint: Path, destination: Path, now):
    _outside(sources, destination)
    if destination.resolve().is_relative_to(checkpoint.resolve()):
        raise ValueError("restore outside the checkpoint")
    body, workspace = _read(checkpoint)
    if body["format"] != _CHECKPOINT or workspace != sources.workspace:
        raise ValueError("foreign or unsupported workspace checkpoint")
    archived, assets = source_recovery._snapshot(checkpoint / "sources", workspace)
    old = outbox_recovery._read(checkpoint / "outbox.json", "outbox-checkpoint-v1")
    with sources._stable(), _transaction(outbox._db):
        state = _current(sources, outbox)
        outbox_recovery._check_extension(old, state)
        with _new_directory(destination):
            source_recovery._project_sources(sources, checkpoint / "sources", destination / "sources",
                                              now, archived, assets)
            outbox_recovery._write(destination / "outbox.json", "outbox-review-v1", state)
            if _members(checkpoint) != body["members"]:
                raise ValueError("workspace checkpoint changed during restoration")
            _seal(destination, workspace, _REVIEW)


def inspect_workspace(root: Path):
    body, workspace = _read(root)
    if body["format"] == _CHECKPOINT:
        source_recovery._snapshot(root / "sources", workspace)
        state = outbox_recovery._read(root / "outbox.json", "outbox-checkpoint-v1")
    else:
        state = outbox_recovery.read_review(root / "outbox.json")
    if state["workspace"] != str(workspace):
        raise ValueError("workspace outbox identity mismatch")
    return {"format": body["format"], "workspace": str(workspace), "outbox": state,
            "execution_authorized": False}
