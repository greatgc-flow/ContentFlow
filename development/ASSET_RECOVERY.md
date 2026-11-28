# Workspace asset recovery

This increment implements the asset-index portion of CF-008 and CF-009 and the SQLite snapshot plus integrity checks of CF-069 and CF-084. The frozen charts, catalogs and contracts retain their original bytes.

## Standalone use

From a source checkout run the examples with `python -B -m contentflow` in place of `contentflow`. Provide the digest from the reviewed source or manifest.

```sh
mkdir local-workspace
contentflow assets init local-workspace
contentflow assets add local-workspace contentflow/fixtures/processing-times.csv \
  --sha256 8a458535a74a1631a13c2de8bb62d24574c1234e1f467679aab877f595d5ca45
contentflow assets checkpoint local-workspace snapshot
contentflow assets verify snapshot
contentflow assets restore snapshot restored-workspace
```

The local workspace must be on an ordinary filesystem that supports SQLite WAL and same-volume hard links. The link publishes a synced staged file without replacing an existing path. Linux flushes the containing directories before SQLite publishes the row. Fixture tests cover an actual process exit before that database commit. Native power-loss durability remains to be measured. Assets have an explicit 16 MiB limit in this increment. The caller controls the local workspace and checkpoint parents.

Checkpoints contain the sealed asset index and verified indexed objects. Integrity checks compare the exact file set, database schema/application version, every asset's size and SHA-256, and SQLite quick check. Restore validates the source before creating a new destination and validates the private staged copy again before publishing the restored index. The checkpoint format provides integrity verification for owner-controlled backups. Authentication of transferred backups has its own gate.

## Receipt

| Stage | Observation |
|---|---|
| CAS RED | Four tests failed at the missing asset module. |
| CAS GREEN | Verified ordinary files, repeated writes by digest, corruption preservation, and actual `os._exit(75)` after object placement and before SQLite commit. Reopening showed one unindexed object. Exact replay registered the existing verified bytes. |
| Checkpoint RED | Three tests failed before the checkpoint API existed. |
| Checkpoint GREEN | Independent round trip passed. Corruption, missing objects, unexpected members, altered manifest and existing destinations were rejected. An unindexed object survived in the source and stayed outside the checkpoint. |
| CLI RED and GREEN | The standalone parser initially rejected the new command. The follow-up passed initialization, reviewed-digest import, checkpoint, inspection, restoration, and refusal to overwrite. |
| Regression | Local test command `unshare -Urn python -B -m unittest discover -s tests -v`. Hosted results are attached to draft PR #1. |

Run `python -B development/audit_design.py` with jsonschema for the frozen vertical and horizontal catalog checks. The other development track maps EPP-004 and EPP-008 to read-only fixture state and plan evidence in Engram draft #147.

This checkpoint covers one asset index. A full domain checkpoint still needs the workspace identity, outbox, rights and retention metadata, explicit deletion intents and replay, and restore rules for authorization and schedules. A whole managed install separately needs a compatible app/environment, exact ownership and the Engram lifecycle transaction. CFX-02, CFX-07 and CFX-08 remain gated for integrated execution. Connect durable source revisions and the deletion journal before enabling general workspace restore or purge.
