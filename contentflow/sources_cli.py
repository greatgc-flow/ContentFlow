"""Commands for explicit source revision and policy-aware checkpoint operations."""
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from .sources import SourceLedger, checkpoint_sources, restore_sources


def register(parser):
    actions = parser.add_subparsers(dest="source_action", required=True)
    for action in ("init", "record", "retire", "checkpoint", "restore"):
        command = actions.add_parser(action)
        command.add_argument("root", type=Path)
        command.add_argument("--workspace-id", type=UUID, required=True)
        if action in ("record", "retire"):
            command.add_argument("source", type=UUID)
            command.add_argument("--expected", type=int, required=True)
        if action == "record":
            command.add_argument("--sha256", required=True)
            command.add_argument("--acquired-at", type=datetime.fromisoformat, required=True)
            command.add_argument("--retain-until", type=datetime.fromisoformat, required=True)
            command.add_argument("--license-ref", required=True)
            command.add_argument("--allow-backup", action="store_true")
        if action == "restore":
            command.add_argument("checkpoint", type=Path)
        if action in ("checkpoint", "restore"):
            command.add_argument("destination", type=Path)


def run(args):
    action = args.source_action
    if action == "init":
        with SourceLedger.create(args.root, args.workspace_id):
            return {"status": "INITIALIZED"}
    with SourceLedger.open(args.root, args.workspace_id) as ledger:
        if action == "record":
            rights = ("read", "backup") if args.allow_backup else ("read",)
            revision = ledger.record(args.source, args.expected, digest=args.sha256,
                                     acquired_at=args.acquired_at, retain_until=args.retain_until,
                                     license_ref=args.license_ref, rights=rights)
            return {"status": "RECORDED", "revision": revision}
        if action == "retire":
            revision = ledger.retire(args.source, args.expected)
            return {"status": "RETIRED", "revision": revision}
        now = datetime.now(timezone.utc)
        if action == "checkpoint":
            checkpoint_sources(ledger, args.destination, now)
            return {"status": "CHECKPOINTED"}
        restored = restore_sources(ledger, args.checkpoint, args.destination, now)
        return {"status": "RESTORED", "sources": restored}
