"""Standalone commands over the local asset index and its checkpoints."""
from pathlib import Path

from .assets import AssetStore, MAX_ASSET
from .checkpoint import checkpoint, restore, verify


def register(parser):
    actions = parser.add_subparsers(dest="asset_action", required=True)
    for action in ("init", "add", "checkpoint", "verify", "restore"):
        command = actions.add_parser(action)
        command.add_argument("root", type=Path)
        if action in ("checkpoint", "restore"):
            command.add_argument("destination", type=Path)
        if action == "add":
            command.add_argument("source", type=Path)
            command.add_argument("--sha256", required=True)


def run(args):
    action = args.asset_action
    if action == "verify":
        return {"status": "VERIFIED", "assets": verify(args.root)}
    if action == "restore":
        restore(args.root, args.destination)
        return {"status": "RESTORED"}
    if action == "init":
        with AssetStore.create(args.root):
            return {"status": "INITIALIZED"}
    with AssetStore.open(args.root) as store:
        if action == "checkpoint":
            checkpoint(store, args.destination)
            return {"status": "CHECKPOINTED"}
        if not args.source.is_file():
            raise ValueError("expected a regular source file")
        with args.source.open("rb") as stream:
            digest = store.put(stream.read(MAX_ASSET + 1), args.sha256)
        return {"status": "INDEXED", "sha256": digest}
