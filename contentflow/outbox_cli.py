"""Operator commands for synthetic outbox checkpoints and recovery review."""
from pathlib import Path
from uuid import UUID

from .outbox import FixtureOutbox
from .outbox_recovery import checkpoint, read_review, restore_review


def register(parser):
    actions = parser.add_subparsers(dest="outbox_action", required=True)
    for action in ("checkpoint", "restore-review", "inspect-review"):
        command = actions.add_parser(action)
        if action == "inspect-review":
            command.add_argument("review", type=Path)
        else:
            command.add_argument("live", type=Path)
            command.add_argument("snapshot", type=Path)
            command.add_argument("--workspace-id", type=UUID, required=True)
        if action == "restore-review":
            command.add_argument("review", type=Path)


def run(args):
    if args.outbox_action == "inspect-review":
        return {"status": "REVIEW"} | read_review(args.review)
    with FixtureOutbox.open(args.live, args.workspace_id) as live:
        if args.outbox_action == "checkpoint":
            checkpoint(live, args.snapshot)
            return {"status": "CHECKPOINTED"}
        restore_review(live, args.snapshot, args.review)
        return {"status": "RESTORED_FOR_REVIEW"}
