"""Commands for coordinated workspace checkpoint and review."""
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from .outbox import FixtureOutbox
from .sources import SourceLedger
from .workspace_recovery import checkpoint_workspace, inspect_workspace, restore_workspace


def register(parser):
    actions = parser.add_subparsers(dest="workspace_action", required=True)
    for action in ("checkpoint", "restore-review"):
        command = actions.add_parser(action)
        command.add_argument("live_sources", type=Path)
        command.add_argument("live_outbox", type=Path)
        command.add_argument("checkpoint", type=Path)
        if action == "restore-review":
            command.add_argument("destination", type=Path)
        command.add_argument("--workspace-id", type=UUID, required=True)
    inspect = actions.add_parser("inspect")
    inspect.add_argument("bundle", type=Path)


def run(args):
    if args.workspace_action == "inspect":
        return {"status": "INSPECTED"} | inspect_workspace(args.bundle)
    with (SourceLedger.open(args.live_sources, args.workspace_id) as sources,
          FixtureOutbox.open(args.live_outbox, args.workspace_id) as outbox):
        now = datetime.now(timezone.utc)
        if args.workspace_action == "checkpoint":
            checkpoint_workspace(sources, outbox, args.checkpoint, now)
            return {"status": "CHECKPOINTED"}
        restore_workspace(sources, outbox, args.checkpoint, args.destination, now)
        return {"status": "RESTORED_FOR_REVIEW"}
