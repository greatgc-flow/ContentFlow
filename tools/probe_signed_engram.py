"""Explicit offline pairing of an exact ContentFlow wheel with an Engram checkout."""
import argparse
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from uuid import UUID
from zipfile import ZipFile

DEFAULT_WORKSPACE = UUID("00000000-0000-4000-8000-000000000001")
OPERATION = UUID("00000000-0000-4000-8000-000000000002")
_SOURCE = """
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib/contentflow.whl"))
"""
_APP = _SOURCE + """
from contentflow.__main__ import main
raise SystemExit(main(["brief", "preview", "--json"]))
"""
_ADAPTER = _SOURCE + """
from contentflow.host_adapter import main
raise SystemExit(main())
"""
_CONTRACTS = {
    "release_manifest": "be4245d4395dc057a37adcc8b59b3adb9d2c5615c97bd1e9ec052e90ebed5eaf",
    "adapter_request": "e32812274426f8fcc681403382b08baf07c501b6273c368a13d86f0b12a6706a",
    "adapter_response": "33bd6c85f37416249c339aff35f0d8a871009557913aa40dc5e172a7708271ac",
}
ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "design/engram-package-platform-v0.3"


def _bytes_digest(data):
    return sha256(data).hexdigest()


def _run(openssl, *args):
    subprocess.run([openssl, *args], stdin=subprocess.DEVNULL, capture_output=True,
                   check=True, timeout=15)


def _signer(openssl, scratch):
    private, public = scratch / "private.pem", scratch / "public.pem"
    _run(openssl, "genpkey", "-algorithm", "ED25519", "-out", private)
    _run(openssl, "pkey", "-in", private, "-pubout", "-out", public)

    def sign(data):
        manifest, signature = scratch / "manifest.json", scratch / "manifest.sig"
        manifest.write_bytes(data)
        _run(openssl, "pkeyutl", "-sign", "-inkey", private, "-rawin",
             "-in", manifest, "-out", signature)
        return signature.read_bytes()

    return public.read_bytes(), sign


def _release(wheel, app, policy):
    members = {"bin/app.py": app.encode(), "bin/adapter.py": _ADAPTER.encode(),
               "lib/contentflow.whl": wheel}
    temp = BytesIO()
    with ZipFile(temp, "w") as bundle:
        for name, data in members.items():
            bundle.writestr(name, data)
    archive = temp.getvalue()
    manifest = json.loads((BASELINE / "fixtures/cf.release.json").read_bytes())
    manifest.update(artifact_sha256=_bytes_digest(archive), artifact_bytes=len(archive),
                    expanded_bytes=sum(map(len, members.values())), runtime_lock_sha256=policy.runtime_lock_sha256,
                    sbom_sha256=policy.sbom_sha256, license_evidence_ref=policy.license_ref,
                    members=[{"path_rel": name, "sha256": _bytes_digest(data), "bytes": len(data),
                              "asset_class": "PROGRAM"} for name, data in members.items()])
    return json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("ascii"), archive


def _check(condition, message):
    if not condition:
        raise ValueError(message)


def _setup_ledgers(system, now):
    # This checkout seeds the live fixture. Only the signed wheel runs inside the managed subprocess.
    sys.path.insert(0, str(ROOT))
    from contentflow.assets import AssetStore
    from contentflow.execution import Money
    from contentflow.outbox import FixtureOutbox
    from contentflow.sources import SourceLedger

    live = system / "ContentFlow/data/live"
    live.mkdir(parents=True)
    for relative in ("checkpoints", "recovery"):
        (system / "ContentFlow" / relative).mkdir()
    fixture = b"offline pairing source"
    with AssetStore.create(live) as store:
        digest = store.put(fixture, _bytes_digest(fixture))
    with SourceLedger.create(live, DEFAULT_WORKSPACE) as ledger:
        ledger.record(OPERATION, 0, digest=digest, acquired_at=now - timedelta(seconds=1),
                      retain_until=now + timedelta(hours=1), license_ref="fixture-license",
                      rights=("read", "backup"))
    with FixtureOutbox.create(live / "outbox.sqlite3", DEFAULT_WORKSPACE, Money(100, "KRW", 0)) as outbox:
        outbox.prepare(OPERATION, {"fixture": True}, Money(70, "KRW", 0))
    return live, SourceLedger, FixtureOutbox


def probe(engram, wheel_path, expected_wheel, openssl):
    for name, expected in _CONTRACTS.items():
        raw = (BASELINE / "contracts" / f"{name}.schema.json").read_bytes()
        _check(_bytes_digest(raw) == expected, "fixture wire contract changed")
    sys.path.insert(0, str(engram / "tools/feasibility"))
    from pack_catalog import load_fixtures
    from optional_pack_group import initialize_fixture, recover
    from optional_pack_release import TrustPolicy, admit, install_signed, launch_adapter, launch_signed, remove_signed
    from core.env_ops import SimulatedCrash

    descriptor_path = engram / "_sys/tests/fixtures/optional-pack/cf.descriptor.json"
    _check(descriptor_path.read_bytes() == (BASELINE / "fixtures/cf.descriptor.json").read_bytes(),
           "fixture descriptor differs across checkouts")
    descriptor, = load_fixtures([descriptor_path])
    wheel = wheel_path.read_bytes()
    _check(_bytes_digest(wheel) == expected_wheel, "wheel differs from reviewed input")
    exe = Path(sys.executable).resolve()
    pin = _bytes_digest(exe.read_bytes())
    now = datetime.now(timezone.utc)
    with TemporaryDirectory(prefix="paired-offline-") as scratch:
        scratch = Path(scratch)
        public, sign = _signer(openssl, scratch)
        policy = TrustPolicy(openssl, _bytes_digest(openssl.read_bytes()), "synthetic-key", public,
                             now + timedelta(minutes=10), False, pin, expected_wheel, "fixture-license")
        system = scratch / "first system"
        system.mkdir()
        initialize_fixture(system)
        live, source_cls, outbox_cls = _setup_ledgers(system, now)
        raw, artifact = _release(wheel, _APP, policy)
        release = admit(descriptor, policy, raw, sign(raw), artifact, _bytes_digest(raw), now)
        _check(install_signed(system, descriptor, 0, "runtime-a", release, policy=policy, now=now)["phase"]
               == "COMMITTED", "regression in signed install")
        brief = json.loads(launch_signed(system, descriptor, release, exe, pin, policy=policy, now=now))
        _check(brief["relative_decrease_percent"] == "25" and brief["test_only"], "wrong native brief")
        generation = "gen-" + release.manifest_sha256
        request = json.loads((BASELINE / "fixtures/cf.request.json").read_bytes())
        request.update(generation=generation, working_rel="ContentFlow/app/generations/" + generation,
                       deadline=(now + timedelta(minutes=2)).isoformat(), plan_digest=release.manifest_sha256)

        def adapter(**changes):
            options = ("--root", str(system), "--installation-id", request["installation_id"],
                       "--generation", generation, "--workspace-id", str(DEFAULT_WORKSPACE),
                       "--plan-digest", request["plan_digest"], "--allow-fixture-writes")
            return launch_adapter(system, descriptor, release, exe, pin, request | changes, options,
                                  policy=policy, now=now)

        _check(adapter()["status"] == "OK", "native adapter health did not echo")
        changes = dict(operation="checkpoint", phase="DRAINED", scope=["BACKUP"],
                       checkpoint_rel="ContentFlow/checkpoints/first", request_id="checkpoint-1")
        completed = adapter(**changes)
        original = system / "ContentFlow/checkpoints/first/workspace.json"
        _check(completed["status"] == "OK" and completed["receipt"]["checkpoint_sha256"]
               == _bytes_digest(original.read_bytes()), "checkpoint receipt mismatch")
        _check(adapter(**changes)["next_action"] == "RECONCILE", "repeated effect was not fenced")
        with source_cls.open(live, DEFAULT_WORKSPACE) as ledger:
            ledger.retire(OPERATION, 1)
        with outbox_cls.open(live / "outbox.sqlite3", DEFAULT_WORKSPACE) as outbox:
            outbox.claim(OPERATION)
        changes.update(operation="restore", phase="APPLYING", scope=["DOMAIN_DATA"], request_id="restore-1")
        outcome = adapter(**changes)
        review = system / "ContentFlow/recovery/restore-1"
        _check(outcome["status"] == "OK" and outcome["receipt"]["checkpoint_sha256"]
               == _bytes_digest((review / "workspace.json").read_bytes()), "restore receipt mismatch")
        from contentflow.workspace_recovery import inspect_workspace
        state = inspect_workspace(review)
        _check(state["outbox"]["operations"][str(OPERATION)]["state"] == "UNKNOWN"
               and not state["execution_authorized"] and not any(p.is_file() for p in (review / "sources/objects").rglob("*")),
               "restore changed pending effect authority")
        with source_cls.open(review / "sources", DEFAULT_WORKSPACE) as restored:
            _check(restored.latest(OPERATION) is None, "restore revived a retired fixture source")

        proposal, archive = _release(wheel, _APP + "\n# signed update\n", policy)
        update = admit(descriptor, policy, proposal, sign(proposal), archive, _bytes_digest(proposal), now)
        try:
            install_signed(system, descriptor, 1, "runtime-b", update, policy=policy, now=now,
                           crash_after="fixture-runtime")
        except SimulatedCrash:
            pass
        else:
            raise ValueError("missing signed update interruption")
        try:
            launch_signed(system, descriptor, release, exe, pin, policy=policy, now=now)
        except ValueError:
            pass
        else:
            raise ValueError("an interrupted generation was launchable")
        _check(recover(system, descriptor, "rollback")["phase"] == "ROLLED_BACK", "signed rollback failed")
        moved = scratch / "moved 경로"
        system.rename(moved)
        _check(json.loads(launch_signed(moved, descriptor, release, exe, pin, policy=policy, now=now))
               ["relative_decrease_percent"] == "25", "signed generation failed after root move")
        retained_roots = (live.relative_to(system), original.parent.relative_to(system), review.relative_to(system))

        def retained_inventory():
            return {p.relative_to(moved): _bytes_digest(p.read_bytes())
                    for directory in retained_roots for p in (moved / directory).rglob("*") if p.is_file()}

        before = retained_inventory()
        _check(bool(before), "missing fixture workspace and checkpoint inventory")
        _check(remove_signed(moved, descriptor, 1, release, policy=policy, now=now)["phase"] == "COMMITTED",
               "signed retained removal failed")
        try:
            launch_signed(moved, descriptor, release, exe, pin, policy=policy, now=now)
        except ValueError as exc:
            _check("active signed generation" in str(exc), "removed generation was not checked")
        else:
            raise ValueError("a retired package was launchable")
        _check(retained_inventory() == before, "removal changed workspace, checkpoint or recovery bytes")
        _check(install_signed(moved, descriptor, 2, "runtime-a", release, policy=policy, now=now,
                              reuse_retained=True)["phase"] == "COMMITTED", "retained reinstall failed")
        _check(json.loads(launch_signed(moved, descriptor, release, exe, pin, policy=policy, now=now))
               ["relative_decrease_percent"] == "25", "reinstalled wheel did not run")
        _check(retained_inventory() == before, "reinstall changed workspace, checkpoint or recovery bytes")
        _check(not (moved / "AI").exists(), "ContentFlow depended on an AI slot")
        return {"wheel_sha256": expected_wheel, "release_sha256": release.manifest_sha256,
                "brief_percent": "25", "adapter": ["health", "checkpoint", "restore"],
                "pending": "UNKNOWN", "rollback": "ROLLED_BACK", "root_move": "PASS",
                "remove_reinstall": "PASS", "retained_file_count": len(before)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engram", type=Path, required=True)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--wheel-sha256", required=True)
    parser.add_argument("--openssl", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(probe(args.engram.resolve(), args.wheel.resolve(), args.wheel_sha256,
                           args.openssl.resolve()), sort_keys=True))


if __name__ == "__main__":
    main()
