"""Cross-check immutable design catalogs, fixtures and integration gates offline."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = ROOT / "design/contentflow-v0.1"
PLATFORM = ROOT / "design/engram-package-platform-v0.3"


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def unique(rows_, key):
    result = {r[key]: r for r in rows_}
    if len(result) != len(rows_):
        raise ValueError(f"duplicate {key}")
    return result


def check():
    for line in (ROOT / "REPOSITORY_SHA256SUMS.txt").read_text().splitlines():
        expected, name = line.split("  ", 1)
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError("baseline checksum mismatch: " + name)
    subprocess.run([sys.executable, "-B", str(DOMAIN / "planning/verify_design.py")], check=True)
    reqs = unique(rows(PLATFORM / "planning/REQUIREMENTS.csv"), "requirement_id")
    cases = unique(rows(PLATFORM / "planning/TEST_CATALOG.csv"), "test_id")
    for req, row in reqs.items():
        if set(row["test_ids"].split()) != {k for k, v in cases.items() if v["requirement_id"] == req}:
            raise ValueError("one-way case mapping: " + req)
    for case, row in cases.items():
        if row["requirement_id"] not in reqs or row["status"] != "NOT_RUN":
            raise ValueError("invalid historical case: " + case)
    for table, column in (("BASELINE_CROSSWALK", "refined_by"), ("RISKS", "requirement_ids")):
        for row in rows(PLATFORM / f"planning/{table}.csv"):
            if not set(row[column].split()) <= reqs.keys():
                raise ValueError("unresolved " + table)
    domain = unique(rows(DOMAIN / "planning/REQUIREMENTS.csv"), "requirement_id")
    integration = unique(rows(ROOT / "planning/INTEGRATION_ACCEPTANCE.csv"), "case_id")
    for name, row in integration.items():
        if not set(row["requirements"].split()) <= (domain.keys() | reqs.keys()):
            raise ValueError("unresolved integration case: " + name)
    index = json.loads((PLATFORM / "fixtures/index.json").read_bytes())
    mapped = unique(index, "file")
    if set(mapped) != {p.name for p in (PLATFORM / "fixtures").glob("*.json")} - {"index.json"}:
        raise ValueError("orphaned fixture")
    for name, row in mapped.items():
        schema = json.loads((PLATFORM / "contracts" / row["schema"]).read_bytes())
        Draft202012Validator.check_schema(schema)
        v = Draft202012Validator(schema, format_checker=FormatChecker())
        if v.is_valid(json.loads((PLATFORM / "fixtures" / name).read_bytes())) != row["schema_valid"]:
            raise ValueError("fixture shape mismatch: " + name)
    print(f"{len(reqs)} platform requirements, {len(cases)} planned cases, "
          f"{len(mapped)} fixtures, {len(integration)} integration gates verified")


if __name__ == "__main__":
    check()
