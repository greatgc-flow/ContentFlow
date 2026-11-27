"""Derive a private draft claim from two synthetic integer millisecond measurements."""
import csv
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
from importlib.resources import files
import io
import re


def processing_time_brief(raw: bytes) -> dict:
    if len(raw) > 4096:
        raise ValueError("the two-record source exceeds 4096 bytes")
    try:
        rows = list(csv.reader(io.StringIO(raw.decode("utf-8"), newline=""), strict=True))
    except csv.Error as exc:
        raise ValueError("invalid CSV") from exc
    if len(rows) != 3 or rows[0] != ["sample", "value", "unit"]:
        raise ValueError("expected a header and two measurements")
    values = []
    for name, row in zip(("baseline", "optimized"), rows[1:], strict=True):
        if (len(row) != 3 or row[0] != name or row[2] != "ms"
                or not re.fullmatch(r"(?:0|[1-9][0-9]{0,8})", row[1])):
            raise ValueError("expected an integer millisecond observation")
        values.append(int(row[1]))
    baseline, optimized = values
    if baseline == 0:
        raise ValueError("relative change requires a positive baseline")
    with localcontext(Context(prec=28, rounding=ROUND_HALF_EVEN)):
        change = Decimal((baseline - optimized) * 100) / Decimal(baseline)
        percent = format(change.quantize(Decimal("0.000001")), "f").rstrip("0").rstrip(".")
    return {
        "review_status": "DRAFT", "test_only": True,
        "disclosure": "TEST_ONLY: synthetic data. This is a worked example, not a benchmark.",
        "source_sha256": hashlib.sha256(raw).hexdigest(), "locator": "CSV records 2-3",
        "baseline_ms": baseline, "optimized_ms": optimized, "relative_decrease_percent": percent,
        "formula": "(baseline - optimized) * 100 / baseline",
    }


def fixture_brief():
    source = files("contentflow").joinpath("fixtures", "processing-times.csv")
    return processing_time_brief(source.read_bytes())
