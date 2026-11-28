"""Content-addressed workspace assets and their transactional index."""
from contextlib import closing, contextmanager
import hashlib
import os
from pathlib import Path
import re
import sqlite3
import stat
from tempfile import NamedTemporaryFile

MAX_ASSET = 16 * 1024 * 1024
APP_ID = 0x43464131
DATABASE = "assets.sqlite3"
_DIGEST = re.compile(r"[0-9a-f]{64}")


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _check_digest(value):
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        raise ValueError("expected a lowercase SHA-256 digest")


def _kind(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        return "other"
    if stat.S_ISDIR(info.st_mode):
        return "directory"
    if stat.S_ISREG(info.st_mode):
        return "file"
    return "other"


def _directory(path, *, create=False):
    if create:
        path.mkdir(exist_ok=True)
    if _kind(path) != "directory":
        raise ValueError(f"expected an ordinary directory: {path.name}")


def _flush_directory(path):
    if os.name == "posix":
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def _verified(path, digest, size):
    if _kind(path) != "file":
        raise ValueError("asset is missing or not an ordinary file")
    with path.open("rb") as stream:
        data = stream.read(MAX_ASSET + 1)
    if len(data) != size or _sha(data) != digest:
        raise ValueError("asset size or digest mismatch")
    return data


def _connect(path, mode):
    db = sqlite3.connect(path.absolute().as_uri() + "?mode=" + mode, uri=True, isolation_level=None)
    db.execute("PRAGMA trusted_schema=OFF")
    return db


def _validate(db):
    if (db.execute("PRAGMA application_id").fetchone()[0] != APP_ID
            or db.execute("PRAGMA user_version").fetchone()[0] != 1):
        raise ValueError("unrecognized asset index format")


class AssetStore:
    """A local workspace index. All cooperating writers serialize through SQLite."""
    def __init__(self, root, db):
        self.root = root
        self._db = db
        self.objects = root / "objects/sha256"

    @classmethod
    def create(cls, root: Path):
        _directory(root)
        path = root / DATABASE
        if _kind(path) is not None:
            raise FileExistsError(path)
        for folder in (root / "objects", root / "objects/sha256"):
            _directory(folder, create=True)
        with path.open("xb"):
            pass
        db = _connect(path, "rw")
        try:
            db.executescript(f"""
                BEGIN IMMEDIATE;
                PRAGMA application_id={APP_ID};
                PRAGMA user_version=1;
                CREATE TABLE asset (digest TEXT PRIMARY KEY, byte_count INTEGER NOT NULL
                                    CHECK (byte_count BETWEEN 0 AND {MAX_ASSET})) STRICT;
                COMMIT;
            """)
            if db.execute("PRAGMA journal_mode=WAL").fetchone()[0] != "wal":
                raise ValueError("asset index requires local SQLite WAL")
            return cls(root, db)
        except BaseException:
            db.close()
            raise

    @classmethod
    def open(cls, root: Path):
        for folder in (root, root / "objects", root / "objects/sha256"):
            _directory(folder)
        path = root / DATABASE
        if _kind(path) != "file":
            raise ValueError("missing or unsupported asset index")
        # Reject foreign databases before giving SQLite a writable connection.
        try:
            with closing(_connect(path, "ro")) as read_only:
                _validate(read_only)
        except sqlite3.DatabaseError as exc:
            raise ValueError("unreadable asset index") from exc
        db = _connect(path, "rw")
        try:
            _validate(db)
            return cls(root, db)
        except BaseException:
            db.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._db.close()

    @contextmanager
    def _transaction(self):
        self._db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self._db.commit()
        except BaseException:
            self._db.rollback()
            raise

    def _path(self, digest):
        _check_digest(digest)
        _directory(self.objects.parent)
        _directory(self.objects)
        return self.objects / digest[:2] / digest

    def _size(self, digest):
        row = self._db.execute("SELECT byte_count FROM asset WHERE digest=?", (digest,)).fetchone()
        return None if row is None else row[0]

    def put(self, data: bytes, digest: str):
        target = self._path(digest)
        if type(data) is not bytes or len(data) > MAX_ASSET or _sha(data) != digest:
            raise ValueError("asset does not match the supplied digest or size limit")
        with self._transaction():
            size = self._size(digest)
            if size is not None:
                self.read(digest)
                return digest
            _directory(target.parent, create=True)
            if _kind(target) is None:
                temp = None
                try:
                    with NamedTemporaryFile(prefix=".asset-", dir=target.parent, delete=False) as stream:
                        temp = Path(stream.name)
                        stream.write(data)
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.replace(temp, target)
                finally:
                    if temp is not None:
                        temp.unlink(missing_ok=True)
            _verified(target, digest, len(data))
            _flush_directory(target.parent)
            _flush_directory(self.objects)
            self._db.execute("INSERT INTO asset VALUES (?, ?)", (digest, len(data)))
        return digest

    def read(self, digest):
        path = self._path(digest)
        size = self._size(digest)
        if size is None:
            raise ValueError("asset is not indexed")
        _directory(path.parent)
        return _verified(path, digest, size)

    def orphans(self):
        """Report unindexed digest-shaped objects without deleting or adopting them."""
        with self._transaction():
            return tuple(sorted(member.name for folder in self.objects.iterdir()
                                if _kind(folder) == "directory" and re.fullmatch(r"[0-9a-f]{2}", folder.name)
                                for member in folder.iterdir()
                                if _DIGEST.fullmatch(member.name) and member.name[:2] == folder.name
                                and self._size(member.name) is None))
