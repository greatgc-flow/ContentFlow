"""Immutable local revision and preview policy, using the CF-CJSON-1 profile."""
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

FORMAT = b"CF-CJSON-1\0"
MAX_INT = 2**53 - 1
MAX_BYTES = 1024 * 1024


def _validate(value, depth=0):
    if depth > 64:
        raise ValueError("document exceeds depth limit")
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                raise ValueError("expected a string key")
            _validate(child, depth + 1)
    elif type(value) is list:
        for child in value:
            _validate(child, depth + 1)
    elif type(value) is int:
        if abs(value) > MAX_INT:
            raise ValueError("integer exceeds canonical range")
    elif value is not None and type(value) not in (str, bool):
        raise ValueError("unsupported canonical value")


def canonical(value):
    _validate(value)
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(raw) > MAX_BYTES:
        raise ValueError("document exceeds byte limit")
    return raw


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def decode(raw):
    if len(raw) > MAX_BYTES:
        raise ValueError("document exceeds byte limit")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique)
    except RecursionError as exc:
        raise ValueError("document exceeds depth limit") from exc
    canonical(value)
    return value


def digest(value):
    return hashlib.sha256(FORMAT + canonical(value)).hexdigest()


def _uuid4(value):
    if not isinstance(value, UUID) or value.version != 4:
        raise ValueError("expected a UUID4")


def _utc(value):
    if not isinstance(value, datetime) or value.utcoffset() != timedelta(0):
        raise ValueError("expected an explicit UTC time")


@dataclass(frozen=True)
class Revision:
    workspace: UUID
    entity: UUID
    number: int
    body: bytes

    def __post_init__(self):
        _uuid4(self.workspace)
        _uuid4(self.entity)
        if type(self.number) is not int or not 1 <= self.number <= MAX_INT:
            raise ValueError("invalid revision")
        if type(self.body) is not bytes or canonical(decode(self.body)) != self.body:
            raise ValueError("expected immutable canonical bytes")

    @classmethod
    def create(cls, workspace, entity, document):
        return cls(workspace, entity, 1, canonical(document))

    def edit(self, workspace, expected, document):
        if workspace != self.workspace or type(expected) is not int or expected != self.number:
            raise ValueError("stale or foreign revision")
        return Revision(workspace, self.entity, self.number + 1, canonical(document))

    @property
    def digest(self):
        return hashlib.sha256(FORMAT + self.body).hexdigest()


@dataclass(frozen=True)
class Rights:
    permissions: frozenset[str]
    expires: datetime

    def __post_init__(self):
        if type(self.permissions) is not frozenset or not all(type(p) is str for p in self.permissions):
            raise ValueError("expected an immutable permission set")
        _utc(self.expires)


@dataclass(frozen=True)
class Review:
    """A local preview decision provided by a trusted caller, scoped to one snapshot."""
    document: Revision
    actor: UUID
    policy: str
    expires: datetime

    @classmethod
    def for_preview(cls, document, actor, policy, expires):
        _uuid4(actor)
        _utc(expires)
        if not isinstance(document, Revision) or type(policy) is not str or not policy.strip():
            raise ValueError("preview requires a revision and policy")
        return cls(document, actor, policy, expires)

    def permits_preview(self, *, document, actor, policy, rights, now):
        _utc(now)
        return (document == self.document and actor == self.actor and policy == self.policy
                and now < min(rights.expires, self.expires)
                and {"READ", "TRANSFORM"} <= rights.permissions)
