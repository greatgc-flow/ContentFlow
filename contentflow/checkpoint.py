"""Consistent, self-contained checkpoints of a workspace's asset index and objects."""
from contextlib import closing, contextmanager
import hashlib
import os
from pathlib import Path
import shutil
import sqlite3
from tempfile import TemporaryDirectory

from .assets import (DATABASE, MAX_ASSET, _check_digest, _connect, _directory,
                     _flush_directory, _kind, _validate, _verified)
from .domain import MAX_BYTES, canonical, decode

MARKER = "checkpoint.json"
SCHEMA_VERSION = "asset-checkpoint-v1"


def _file_hash(path):
    if _kind(path) != "file":
        raise ValueError(f"expected a checkpoint file: {path.name}")
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _put_file(path, data):
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _index(db):
    _validate(db)
    rows = dict(db.execute("SELECT digest, byte_count FROM asset"))
    for digest, size in rows.items():
        _check_digest(digest)
        if type(size) is not int or not 0 <= size <= MAX_ASSET:
            raise ValueError("invalid checkpoint asset size")
    return rows


def _path(root, digest):
    return root / "objects/sha256" / digest[:2] / digest


def _directories(rows):
    return ("objects", "objects/sha256", *sorted({f"objects/sha256/{d[:2]}" for d in rows}))


@contextmanager
def _new_directory(destination):
    destination.mkdir()
    try:
        yield
    except BaseException:
        shutil.rmtree(destination)
        raise


def checkpoint(store, destination: Path):
    """Seal a new asset-only checkpoint, holding a stable view across DB and objects."""
    if destination.resolve().is_relative_to(store.root.resolve()):
        raise ValueError("place checkpoints outside the source workspace")
    with _new_directory(destination):
        database = destination / DATABASE
        with store._transaction():
            with (closing(_connect(store.root / DATABASE, "ro")) as source,
                  closing(sqlite3.connect(database)) as target):
                source.backup(target)
                target.execute("PRAGMA journal_mode=DELETE")
                assets = _index(target)
            for folder in _directories(assets):
                (destination / folder).mkdir()
            for digest in sorted(assets):
                _put_file(_path(destination, digest), store.read(digest))
        _flush_directory(destination)
        _put_file(destination / MARKER, canonical({"format": SCHEMA_VERSION, "assets": assets,
                                                  "index_sha256": _file_hash(database)}))
        verify(destination)
        for folder in reversed(_directories(assets)):
            _flush_directory(destination / folder)
        _flush_directory(destination)
        _flush_directory(destination.parent)


def verify(source: Path):
    """Verify exact members, SQLite identity and each referenced object without restoring."""
    _directory(source)
    if _kind(source / MARKER) != "file":
        raise ValueError("unsealed checkpoint")
    with (source / MARKER).open("rb") as stream:
        body = decode(stream.read(MAX_BYTES + 1))
    if (type(body) is not dict or body.keys() != {"format", "assets", "index_sha256"}
            or body["format"] != SCHEMA_VERSION or type(body["assets"]) is not dict):
        raise ValueError("invalid checkpoint manifest")
    listed = body["assets"]
    for digest in listed:
        _check_digest(digest)
        if type(listed[digest]) is not int or not 0 <= listed[digest] <= MAX_ASSET:
            raise ValueError("invalid checkpoint asset size")
    expected_dirs = _directories(listed)
    children = {source: {MARKER, DATABASE, "objects"}}
    for folder in expected_dirs:
        path = source / folder
        _directory(path)
        if path.parent != source:
            children[path.parent].add(path.name)
        children[path] = set()
    for digest in listed:
        path = _path(source, digest)
        children[path.parent].add(path.name)
    for path, members in children.items():
        if {p.name for p in path.iterdir()} != members:
            raise ValueError("checkpoint members differ from the manifest")
    database = source / DATABASE
    if _file_hash(database) != body["index_sha256"]:
        raise ValueError("checkpoint index digest mismatch")
    try:
        with closing(_connect(database, "ro&immutable=1")) as db:
            if _index(db) != listed or db.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
                raise ValueError("checkpoint index disagrees with manifest")
    except sqlite3.DatabaseError as exc:
        raise ValueError("invalid checkpoint index") from exc
    for digest, size in listed.items():
        _verified(_path(source, digest), digest, size)
    return listed


def restore(source: Path, destination: Path):
    """Verify a fresh copy in a private staging directory before exposing its index."""
    assets = verify(source)
    if destination.resolve().is_relative_to(source.resolve()):
        raise ValueError("restore outside the checkpoint directory")
    with _new_directory(destination):
        with TemporaryDirectory(prefix=".restore-", dir=destination) as scratch:
            staged = Path(scratch)
            for folder in _directories(assets):
                (staged / folder).mkdir()
            for digest, size in assets.items():
                _put_file(_path(staged, digest), _verified(_path(source, digest), digest, size))
            for name in (DATABASE, MARKER):
                shutil.copyfile(source / name, staged / name)
            verify(staged)
            with closing(_connect(staged / DATABASE, "rw")) as db:
                if db.execute("PRAGMA journal_mode=WAL").fetchone()[0] != "wal":
                    raise ValueError("restored asset index requires local SQLite WAL")
            with (staged / DATABASE).open("r+b") as db_file:
                os.fsync(db_file.fileno())
            for folder in reversed(_directories(assets)):
                _flush_directory(staged / folder)
            os.replace(staged / "objects", destination / "objects")
            _flush_directory(destination)
            os.replace(staged / DATABASE, destination / DATABASE)
        _flush_directory(destination)
        _flush_directory(destination.parent)
