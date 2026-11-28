"""Pure transition and monetary rules for the offline executor."""
from dataclasses import dataclass

from contentflow.domain import MAX_INT

_JOB = {
    "QUEUED": {"RUNNING", "CANCELED"},
    "RUNNING": {"WAITING_REVIEW", "WAITING_BUDGET", "WAITING_EXTERNAL", "QUEUED",
                "SUCCEEDED", "FAILED", "CANCELED"},
    "WAITING_REVIEW": {"QUEUED", "CANCELED"},
    "WAITING_BUDGET": {"QUEUED", "CANCELED"},
    "WAITING_EXTERNAL": {"QUEUED", "CANCELED"},
}
_STEP = {
    "PENDING": {"READY", "BLOCKED", "SKIPPED", "CANCELED"},
    "READY": {"RUNNING", "SKIPPED", "CANCELED"},
    "RUNNING": {"SUCCEEDED", "RETRYABLE_FAILED", "FAILED", "CANCELED", "BLOCKED"},
    "BLOCKED": {"READY", "CANCELED"},
    "RETRYABLE_FAILED": {"READY", "FAILED", "CANCELED"},
}


def job_transition(state, target):
    if target not in _JOB.get(state, ()):
        raise ValueError(f"job transition {state} to {target} is unavailable")
    return target


def step_transition(state, target, *, optional=False):
    if target not in _STEP.get(state, ()) or (target == "SKIPPED" and optional is not True):
        raise ValueError(f"step transition {state} to {target} is unavailable")
    return target


@dataclass(frozen=True)
class Money:
    """Known nonnegative exposure in the two currencies supported by the first fixture."""
    minor: int
    currency: str
    scale: int

    def __post_init__(self):
        if type(self.minor) is not int or not 0 <= self.minor <= MAX_INT:
            raise ValueError("amount must be nonnegative integer minor units")
        if type(self.scale) is not int or (self.currency, self.scale) not in (("KRW", 0), ("USD", 2)):
            raise ValueError("unsupported currency or scale")


def check_reservation(cap, used, upper):
    if cap.currency != used.currency or cap.currency != upper.currency:
        raise ValueError("reservation currency mismatch")
    if used.minor + upper.minor > cap.minor:
        raise ValueError("reservation exceeds budget")


@dataclass(frozen=True)
class Reservation:
    bound: Money
    state: str
    actual: Money | None = None
    receipt: str | None = None

    def __post_init__(self):
        if not isinstance(self.bound, Money):
            raise ValueError("a known upper bound is required")
        if self.state in ("HELD", "UNKNOWN"):
            if self.receipt is not None or self.actual is not None:
                raise ValueError("unresolved reservation has a receipt")
        elif (not isinstance(self.actual, Money) or self.actual.currency != self.bound.currency
              or not isinstance(self.receipt, str) or not self.receipt.strip()
              or self.state != ("SETTLED" if self.actual.minor else "RELEASED")):
            raise ValueError("invalid reservation settlement")

    @classmethod
    def hold(cls, bound):
        return cls(bound, "HELD")

    def unknown(self):
        if self.state != "HELD":
            raise ValueError("only a held reservation can become unknown")
        return Reservation(self.bound, "UNKNOWN")

    def resolve(self, actual, receipt):
        if self.state not in ("HELD", "UNKNOWN") or not isinstance(actual, Money):
            raise ValueError("reservation cannot be resolved")
        return Reservation(self.bound, "SETTLED" if actual.minor else "RELEASED", actual, receipt)

    @property
    def exposure(self):
        return self.actual if self.actual is not None else self.bound

    @property
    def over_limit(self):
        return self.exposure.minor > self.bound.minor
