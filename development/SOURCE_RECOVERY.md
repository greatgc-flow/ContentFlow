# Source retention and checkpoint replay

This increment adds a local source ledger to the standalone application. Each ledger belongs to a workspace UUID. Each source has an immutable sequence of revisions with an indexed asset digest, acquisition time, retention deadline, license reference and explicit rights. A new revision compares the expected head. A retirement records a terminal tombstone scoped to the source ID and preserves original asset bytes. Replaying the same retirement returns its existing revision.

## Operator commands

These examples use synthetic UUIDs and an already indexed CSV. Use the source checkout's `python -B -m contentflow` or the installed `contentflow` command.

```sh
workspace=85db404a-2c18-4c32-95bd-65508a312318
source=1a14bbcc-b03d-4356-b4e0-09ebca22f809
contentflow sources init local-workspace --workspace-id "$workspace"
contentflow sources record local-workspace "$source" --workspace-id "$workspace" \
  --expected 0 --sha256 8a458535a74a1631a13c2de8bb62d24574c1234e1f467679aab877f595d5ca45 \
  --acquired-at 2026-11-28T00:00:00Z --retain-until 2099-01-01T00:00:00Z \
  --license-ref fixture-license --allow-backup
contentflow sources checkpoint local-workspace snapshot --workspace-id "$workspace"
contentflow sources retire local-workspace "$source" --workspace-id "$workspace" --expected 1
contentflow sources restore local-workspace snapshot restored-workspace --workspace-id "$workspace"
```

Checkpoint creation includes only exact, current revisions with backup permission and unexpired retention. The sealed asset checkpoint admits only objects referenced by these revisions. The legacy asset-only checkpoint rejects source-managed workspaces. Restore requires access to the current authoritative local ledger as well as the older snapshot. It verifies all snapshot members and hashes, then copies only revisions that still exactly match eligible current revisions. It also copies the current tombstones. New destinations are exclusive. The operator supplies the current ledger path, so an outdated independent copy lacks evidence of subsequent retirements. This operation restores a source projection. General workspace recovery, archive authenticity, single active writer across copies, receipt preservation, derivative purge and physical erasure have separate gates.

## Evidence

- RED failed four tests at the missing source ledger. GREEN verified exact-digest provenance, optimistic revision checks, workspace identity, idempotent tombstone replay, expiry and tamper rejection.
- The next RED was a standalone CLI parser failure. GREEN exercised the actual source commands and proved that a newer revision reducing backup permission wins over a still-valid older archive.
- An older snapshot with a retired asset and a live asset restored only the live asset. The retired asset stayed in the original workspace. An expired source produced an empty projection. A foreign checkpoint identity or altered member failed before a destination was made.
- CF-007, CF-020/021 and CF-069/084 are partially exercised for local source revisions and checkpoint policy replay. CFX-07 remains open for full managed workspace migration and coherent rollback.

Run `python -B -m unittest discover -s tests -v` for the regression. The source command uses the system's UTC clock. API tests pass an explicit UTC time.
