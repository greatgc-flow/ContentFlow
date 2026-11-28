"""Durable, workspace-scoped source revisions and policy-aware checkpoint replay."""
from contextlib import closing, contextmanager
from datetime import datetime
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID

from . import checkpoint
from .assets import (AssetStore, DATABASE, SOURCE_DB, _check_digest, _connect,
                     _directory, _flush_directory, _kind, _verified)
from .domain import MAX_BYTES, _utc, _uuid4, canonical, decode

_FORMAT = "source-checkpoint-v1"
_APP_ID = 0x43465331
_MARKER = "sources.json"


def _identity(value):
    _uuid4(value)
    return str(value)


def _time(value):
    _utc(value)
    return value.isoformat()


class SourceLedger:
    def __init__(self, root, workspace, db):
        self.root, self.workspace, self._db = root, workspace, db

    @classmethod
    def create(cls, root: Path, workspace: UUID):
        owner = _identity(workspace)
        path = root / SOURCE_DB
        with AssetStore.open(root) as assets, assets._transaction():
            with path.open("xb"):
                pass
            db = _connect(path, "rw")
            try:
                db.executescript(f"""
                    BEGIN IMMEDIATE;
                    PRAGMA application_id={_APP_ID};
                    PRAGMA user_version=1;
                    CREATE TABLE owner (id TEXT PRIMARY KEY) STRICT;
                    CREATE TABLE revision (source TEXT, rev INTEGER, data BLOB,
                                           PRIMARY KEY(source,rev)) STRICT;
                    CREATE TABLE tombstone (source TEXT PRIMARY KEY, rev INTEGER NOT NULL) STRICT;
                """)
                db.execute("INSERT INTO owner VALUES (?)", (owner,))
                db.commit()
                return cls(root, workspace, db)
            except BaseException:
                db.close()
                raise

    @classmethod
    def open(cls, root: Path, workspace: UUID):
        owner = _identity(workspace)
        _directory(root)
        path = root / SOURCE_DB
        if _kind(path) != "file":
            raise ValueError("source ledger is missing or unsupported")

        def validate(db):
            if (db.execute("PRAGMA application_id").fetchone()[0] != _APP_ID
                    or db.execute("PRAGMA user_version").fetchone()[0] != 1
                    or db.execute("SELECT id FROM owner").fetchall() != [(owner,)]):
                raise ValueError("unexpected source ledger identity")

        with closing(_connect(path, "ro")) as read_only:
            validate(read_only)
        db = _connect(path, "rw")
        try:
            validate(db)
            return cls(root, workspace, db)
        except BaseException:
            db.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._db.close()

    @contextmanager
    def _stable(self):
        self._db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self._db.commit()
        except BaseException:
            self._db.rollback()
            raise

    def _head(self, source):
        return self._db.execute("SELECT rev,data FROM revision WHERE source=? ORDER BY rev DESC LIMIT 1",
                                (source,)).fetchone()

    def _retired(self):
        return dict(self._db.execute("SELECT source,rev FROM tombstone"))

    def latest(self, source: UUID):
        key = _identity(source)
        row = self._db.execute(
            "SELECT data FROM revision WHERE source=? AND source NOT IN (SELECT source FROM tombstone) "
            "ORDER BY rev DESC LIMIT 1", (key,)).fetchone()
        return decode(row[0]) if row else None

    def record(self, source: UUID, expected_revision: int, *, digest: str, acquired_at: datetime,
               retain_until: datetime, license_ref: str, rights):
        key = _identity(source)
        _check_digest(digest)
        acquired, deadline = _time(acquired_at), _time(retain_until)
        if (type(expected_revision) is not int or not 0 <= expected_revision < 2**53 - 1
                or retain_until <= acquired_at or not isinstance(license_ref, str)
                or not license_ref.strip() or len(license_ref) > 256
                or not isinstance(rights, (list, tuple)) or not rights
                or any(right not in ("read", "backup") for right in rights) or "read" not in rights):
            raise ValueError("invalid source revision or rights")
        with self._stable():
            head = self._head(key)
            if key in self._retired() or (head[0] if head else 0) != expected_revision:
                raise ValueError("source revision conflict or retired source")
            with AssetStore.open(self.root) as store:
                store.read(digest)
            revision = expected_revision + 1
            body = {"revision": revision, "digest": digest, "acquired_at": acquired,
                    "retain_until": deadline, "license_ref": license_ref, "rights": sorted(set(rights))}
            self._db.execute("INSERT INTO revision VALUES (?,?,?)", (key, revision, canonical(body)))
            return revision

    def retire(self, source: UUID, expected_revision: int):
        """Persist a terminal source tombstone and keep stored objects for explicit retention handling."""
        key = _identity(source)
        if type(expected_revision) is not int or not 1 <= expected_revision < 2**53 - 1:
            raise ValueError("invalid retirement revision")
        with self._stable():
            retired = self._retired().get(key)
            head = self._head(key)
            if retired == expected_revision + 1:
                return retired
            if retired is not None or head is None or head[0] != expected_revision:
                raise ValueError("source retirement conflicts with current revision")
            revision = expected_revision + 1
            self._db.execute("INSERT INTO tombstone VALUES (?,?)", (key, revision))
            return revision

    def eligible(self, now: datetime):
        _utc(now)
        heads = self._db.execute(
            "SELECT r.source,r.data FROM revision r "
            "WHERE r.rev=(SELECT MAX(rev) FROM revision WHERE source=r.source) "
            "AND r.source NOT IN (SELECT source FROM tombstone)")
        eligible = {}
        for key, record in heads:
            body = decode(record)
            if ("backup" in body["rights"] and datetime.fromisoformat(body["acquired_at"]) <= now
                    < datetime.fromisoformat(body["retain_until"])):
                eligible[key] = body
        return eligible


def checkpoint_sources(ledger: SourceLedger, destination: Path, now: datetime):
    if destination.resolve().is_relative_to(ledger.root.resolve()):
        raise ValueError("place source checkpoints outside the workspace")
    with ledger._stable():
        _capture_sources(ledger, destination, now)


def _capture_sources(ledger, destination, now):
    with checkpoint._new_directory(destination):
        records = ledger.eligible(now)
        with TemporaryDirectory(prefix=".sources-", dir=destination) as scratch:
            with AssetStore.open(ledger.root) as live, AssetStore.create(Path(scratch)) as selected:
                for asset in sorted({row["digest"] for row in records.values()}):
                    selected.put(live.read(asset), asset)
                checkpoint.checkpoint(selected, destination / "assets")
        body = {"format": _FORMAT, "workspace": str(ledger.workspace), "records": records,
                "assets_manifest_sha256": checkpoint._file_hash(destination / "assets" / checkpoint.MARKER)}
        checkpoint._put_file(destination / _MARKER, canonical(body))
        _flush_directory(destination)
        _flush_directory(destination.parent)

def _snapshot(source, workspace):
    _directory(source)
    if {p.name for p in source.iterdir()} != {_MARKER, "assets"} or _kind(source / _MARKER) != "file":
        raise ValueError("incomplete source checkpoint")
    with (source / _MARKER).open("rb") as stream:
        body = decode(stream.read(MAX_BYTES + 1))
    if (type(body) is not dict or body.keys() != {"format", "workspace", "records", "assets_manifest_sha256"}
            or body["format"] != _FORMAT or body["workspace"] != str(workspace)
            or type(body["records"]) is not dict):
        raise ValueError("invalid source checkpoint identity or metadata")
    assets = checkpoint.verify(source / "assets")
    if checkpoint._file_hash(source / "assets" / checkpoint.MARKER) != body["assets_manifest_sha256"]:
        raise ValueError("source checkpoint asset manifest mismatch")
    digests = set()
    for key, record in body["records"].items():
        _identity(UUID(key))
        if type(record) is not dict or "digest" not in record:
            raise ValueError("invalid checkpoint revision")
        _check_digest(record["digest"])
        digests.add(record["digest"])
    if digests != assets.keys():
        raise ValueError("source checkpoint contains unrelated or missing objects")
    return body["records"], assets


def restore_sources(live: SourceLedger, source: Path, destination: Path, now: datetime):
    """Project a checkpoint under current rights, revision and tombstone evidence."""
    if destination.resolve().is_relative_to(source.resolve()) or destination.resolve().is_relative_to(live.root.resolve()):
        raise ValueError("restore outside the checkpoint and live workspace")
    archived, assets = _snapshot(source, live.workspace)
    with live._stable():
        return _project_sources(live, source, destination, now, archived, assets)


def _project_sources(live, source, destination, now, archived, assets):
    records = {key: body for key, body in live.eligible(now).items() if archived.get(key) == body}
    tombstones = live._retired()
    with checkpoint._new_directory(destination), TemporaryDirectory(prefix=".restore-", dir=destination) as scratch:
        staged = Path(scratch)
        with AssetStore.create(staged) as store:
            for digest in sorted({row["digest"] for row in records.values()}):
                store.put(_verified(checkpoint._path(source / "assets", digest), digest, assets[digest]), digest)
        with SourceLedger.create(staged, live.workspace) as ledger, ledger._stable():
            ledger._db.executemany("INSERT INTO revision VALUES (?,?,?)",
                                   ((key, row["revision"], canonical(row)) for key, row in records.items()))
            ledger._db.executemany("INSERT INTO tombstone VALUES (?,?)", tombstones.items())
        # Publish the policy database before the asset index becomes available.
        for name in (SOURCE_DB, "objects", DATABASE):
            os.replace(staged / name, destination / name)
        _flush_directory(destination)
        _flush_directory(destination.parent)
    return tuple(sorted(records))
