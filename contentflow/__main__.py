"""Run ContentFlow's standalone offline commands."""
import argparse
import json
import sqlite3
import sys
from pathlib import Path
from uuid import uuid4

from .brief import fixture_brief
from .domain import MAX_BYTES, decode, digest
from .workflow import plan


def main(argv=None):
    parser = argparse.ArgumentParser(prog="contentflow")
    commands = parser.add_subparsers(dest="command", required=True)
    brief = commands.add_parser("brief").add_subparsers(required=True).add_parser("preview")
    brief.add_argument("--json", action="store_true")
    from . import assets_cli
    assets_cli.register(commands.add_parser("assets"))
    run = commands.add_parser("run")
    run.add_argument("--workflow", type=Path, required=True)
    run.add_argument("--dry-run", action="store_true", required=True)
    run.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    envelope = {"request_id": str(uuid4()), "warnings": []}
    if args.command == "assets":
        try:
            print(json.dumps(envelope | assets_cli.run(args)))
        except (OSError, ValueError, sqlite3.Error) as exc:
            print(json.dumps(envelope | {"status": "INVALID_INPUT", "reason": str(exc)}), file=sys.stderr)
            return 2
        return 0
    if args.command == "brief":
        result = envelope | fixture_brief()
        if args.json:
            print(json.dumps(result))
        else:
            print(result["disclosure"])
            print(f"Relative decrease: {result['relative_decrease_percent']}%")
        return 0
    try:
        with args.workflow.open("rb") as stream:
            workflow = decode(stream.read(MAX_BYTES + 1))
        steps = plan(workflow)
    except (OSError, ValueError) as exc:
        error = envelope | {"status": "INVALID_INPUT", "reason": str(exc)}
        print(json.dumps(error) if args.json else str(exc), file=sys.stderr)
        return 2
    result = envelope | {"status": "PLANNED", "workflow_id": workflow["workflow_id"],
                         "revision": workflow["revision"], "workflow_digest": digest(workflow),
                         "steps": steps, "test_only": True}
    print(json.dumps(result) if args.json else " -> ".join(steps))
    return 0


if __name__ == "__main__":
    sys.exit(main())
