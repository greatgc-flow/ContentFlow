"""Checkpoint and restore review of synthetic effects without dispatch authority."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID

from .assets import _check_digest, _directory, _flush_directory, _kind
from .checkpoint import _put_file
from .domain import MAX_BYTES, canonical, decode, digest
from .execution import Money
from .outbox import FixtureOutbox, _transaction, _uuid

_ADVANCE = {
    "HELD": {"HELD", "UNKNOWN", "SETTLED", "RELEASED"},
    "UNKNOWN": {"UNKNOWN", "SETTLED", "RELEASED"},
    "SETTLED": {"SETTLED"},
    "RELEASED": {"RELEASED"},
}
_FIELDS = {"payload_digest", "upper_minor", "state", "actual", "receipt_digest"}


def _state(live):
    owner, = live._db.execute("SELECT workspace FROM budget").fetchone()
    cap = live._cap
    rows = live._db.execute("SELECT op, payload_digest, upper_minor, state, actual, receipt FROM intent")
    records = {}
    for row in rows:
        key, payload, upper, state, actual, receipt = row
        records[key] = {"payload_digest": payload, "upper_minor": upper, "state": state,
                        "actual": actual, "receipt_digest": digest(receipt) if receipt is not None else None}
    return {"workspace": owner, "budget": {"minor": cap.minor, "currency": cap.currency,
                                            "scale": cap.scale}, "operations": records}


def _validate(data):
    if type(data) is not dict or data.keys() != {"workspace", "budget", "operations"}:
        raise ValueError("invalid outbox checkpoint state")
    if not isinstance(data["workspace"], str) or _uuid(UUID(data["workspace"])) != data["workspace"]:
        raise ValueError("invalid outbox workspace identity")
    budget, records = data["budget"], data["operations"]
    if type(budget) is not dict or budget.keys() != {"minor", "currency", "scale"} or type(records) is not dict:
        raise ValueError("invalid outbox budget or operation map")
    cap = Money(**budget)
    for key, row in records.items():
        if (_uuid(UUID(key)) != key or type(row) is not dict or row.keys() != _FIELDS
                or row["state"] not in tuple(_ADVANCE)):
            raise ValueError("invalid outbox operation")
        _check_digest(row["payload_digest"])
        Money(row["upper_minor"], cap.currency, cap.scale)
        actual, receipt = row["actual"], row["receipt_digest"]
        if row["state"] in ("HELD", "UNKNOWN"):
            if actual is not None or receipt is not None:
                raise ValueError("unresolved operation has settlement evidence")
        else:
            Money(actual, cap.currency, cap.scale)
            _check_digest(receipt)
            if row["state"] != ("SETTLED" if actual else "RELEASED"):
                raise ValueError("terminal operation disagrees with recorded charge")


def _write(path, kind, state):
    _validate(state)
    body = {"format": kind, "state": state}
    wire = canonical({"body": body, "sha256": digest(body)})
    _directory(path.parent)
    with TemporaryDirectory(prefix=".outbox-", dir=path.parent) as scratch:
        staged = Path(scratch) / "sealed.json"
        _put_file(staged, wire)
        os.link(staged, path)
        _flush_directory(path.parent)


def _read(path, kind):
    if _kind(path) != "file":
        raise ValueError("expected an ordinary sealed outbox file")
    with path.open("rb") as stream:
        record = decode(stream.read(MAX_BYTES + 1))
    if type(record) is not dict or record.keys() != {"body", "sha256"}:
        raise ValueError("invalid outbox seal")
    body = record["body"]
    if (digest(body) != record["sha256"] or type(body) is not dict
            or body.keys() != {"format", "state"} or body["format"] != kind):
        raise ValueError("invalid outbox format or digest")
    _validate(body["state"])
    return body["state"]


def checkpoint(live: FixtureOutbox, path: Path):
    """Capture a single committed outbox view as bounded metadata."""
    with _transaction(live._db):
        _write(path, "outbox-checkpoint-v1", _state(live))


def restore_review(live: FixtureOutbox, snapshot: Path, destination: Path):
    archived = _read(snapshot, "outbox-checkpoint-v1")
    with _transaction(live._db):
        current = _state(live)
        if (archived["workspace"], archived["budget"]) != (current["workspace"], current["budget"]):
            raise ValueError("outbox workspace or budget differs from checkpoint")
        for key, old in archived["operations"].items():
            new = current["operations"].get(key)
            if (new is None or (new["payload_digest"], new["upper_minor"])
                    != (old["payload_digest"], old["upper_minor"])
                    or new["state"] not in _ADVANCE[old["state"]]
                    or (old["state"] in ("SETTLED", "RELEASED") and new != old)):
                raise ValueError("current outbox does not extend the checkpoint")
        _write(destination, "outbox-review-v1", current)


def read_review(path: Path):
    state = _read(path, "outbox-review-v1")
    return state | {"execution_authorized": False, "budget_frozen": any(
        row["actual"] is not None and row["actual"] > row["upper_minor"]
        for row in state["operations"].values())}
