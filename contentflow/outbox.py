"""Local SQLite intent and budget experiment for explicit TEST_ONLY workspaces."""
from contextlib import closing, contextmanager
import sqlite3
from pathlib import Path
from uuid import UUID

from .domain import digest
from .execution import Money, Reservation, check_reservation


_APP_ID = 0x43465431  # CFT1 identifies the synthetic outbox file format.


def _uuid(value):
    if not isinstance(value, UUID) or value.version != 4:
        raise ValueError("expected a workspace or operation UUID4")
    return str(value)


def _connect(path, mode):
    if path.is_symlink():
        raise ValueError("the outbox cannot be a symbolic link")
    uri = path.absolute().as_uri() + "?mode=" + mode
    connection = sqlite3.connect(uri, uri=True, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA trusted_schema=OFF")
    return connection


@contextmanager
def _transaction(connection):
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield
        connection.commit()
    except BaseException:
        connection.rollback()
        raise


class FixtureOutbox:
    """Each instance owns a connection to a dedicated local fixture database."""
    def __init__(self, connection, cap):
        self._db = connection
        self._cap = cap

    @classmethod
    def create(cls, path: Path, workspace: UUID, cap: Money):
        owner = _uuid(workspace)
        if not isinstance(cap, Money):
            raise ValueError("expected a fixed fixture budget")
        with path.open("xb"):
            pass
        db = _connect(path, "rw")
        try:
            with _transaction(db):
                db.execute(f"PRAGMA application_id={_APP_ID}")
                db.execute("PRAGMA user_version=1")
                db.execute("CREATE TABLE budget (workspace TEXT PRIMARY KEY, cap INTEGER NOT NULL, "
                           "currency TEXT NOT NULL, scale INTEGER NOT NULL) STRICT")
                db.execute("INSERT INTO budget VALUES (?, ?, ?, ?)",
                           (owner, cap.minor, cap.currency, cap.scale))
                db.execute("CREATE TABLE intent (op TEXT PRIMARY KEY, payload_digest TEXT NOT NULL, "
                           "upper_minor INTEGER NOT NULL, state TEXT NOT NULL, actual INTEGER, "
                           "receipt TEXT UNIQUE) STRICT")
            if db.execute("PRAGMA journal_mode=WAL").fetchone()[0] != "wal":
                raise ValueError("fixture requires local SQLite WAL support")
            return cls(db, cap)
        except BaseException:
            db.close()
            raise

    @classmethod
    def open(cls, path: Path, workspace: UUID):
        owner = _uuid(workspace)
        # Check the dedicated file header before allowing SQLite to recover or open sidecars.
        if path.is_symlink() or not path.is_file():
            raise ValueError("expected an existing local fixture database")
        with path.open("rb") as stream:
            header = stream.read(100)
        if header[:16] != b"SQLite format 3\0" or header[68:72] != _APP_ID.to_bytes(4, "big"):
            raise ValueError("unrecognized fixture database")
        def identity(db):
            if db.execute("PRAGMA user_version").fetchone()[0] != 1:
                raise ValueError("unsupported fixture version")
            rows = db.execute("SELECT workspace, cap, currency, scale FROM budget LIMIT 2").fetchall()
            if len(rows) != 1 or rows[0]["workspace"] != owner:
                raise ValueError("foreign fixture workspace")
            return Money(rows[0]["cap"], rows[0]["currency"], rows[0]["scale"])
        with closing(_connect(path, "ro")) as readonly:
            identity(readonly)
        db = _connect(path, "rw")
        try:
            return cls(db, identity(db))
        except BaseException:
            db.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._db.close()

    def _row(self, op):
        row = self._db.execute("SELECT * FROM intent WHERE op=?", (_uuid(op),)).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["over_limit"] = row["actual"] is not None and row["actual"] > row["upper_minor"]
        return result

    def prepare(self, operation, payload, upper):
        key, payload_hash = _uuid(operation), digest(payload)
        if not isinstance(upper, Money) or upper.currency != self._cap.currency:
            raise ValueError("reservation currency mismatch")
        with _transaction(self._db):
            old = self._row(operation)
            if old is not None:
                if old["payload_digest"] != payload_hash or old["upper_minor"] != upper.minor:
                    raise ValueError("operation conflicts with its original intent")
                return old
            if self._db.execute("SELECT 1 FROM intent WHERE actual > upper_minor LIMIT 1").fetchone():
                raise ValueError("fixture budget is frozen after an overage")
            exposure = self._db.execute("SELECT COALESCE(SUM(COALESCE(actual, upper_minor)),0) "
                                        "FROM intent").fetchone()[0]
            check_reservation(self._cap, Money(exposure, upper.currency, upper.scale), upper)
            self._db.execute("INSERT INTO intent (op,payload_digest,upper_minor,state) "
                             "VALUES (?,?,?,'HELD')", (key, payload_hash, upper.minor))
            return self._row(operation)

    def claim(self, operation):
        with _transaction(self._db):
            change = self._db.execute("UPDATE intent SET state='UNKNOWN' WHERE op=? AND state='HELD'",
                                      (_uuid(operation),))
            if change.rowcount != 1:
                raise ValueError("intent requires reconciliation or has no reservation")
            return self._row(operation)

    def reconcile(self, operation, actual, receipt):
        with _transaction(self._db):
            row = self._row(operation)
            if row is None:
                raise ValueError("unknown operation")
            bound = Money(row["upper_minor"], self._cap.currency, self._cap.scale)
            result = Reservation(bound, "UNKNOWN").resolve(actual, receipt)
            if row["state"] in ("RELEASED", "SETTLED"):
                if (row["actual"], row["receipt"]) != (actual.minor, receipt):
                    raise ValueError("conflicting reconciliation receipt")
                return row
            if row["state"] != "UNKNOWN":
                raise ValueError("intent has not been claimed")
            self._db.execute("UPDATE intent SET state=?, actual=?, receipt=? WHERE op=?",
                             (result.state, actual.minor, receipt, _uuid(operation)))
            return self._row(operation)
