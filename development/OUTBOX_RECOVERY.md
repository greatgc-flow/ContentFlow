# Pending effect recovery review

The local fixture outbox now supports a standalone, sealed metadata checkpoint and a review-only restoration. This increment exercises the pending-effect and budget clauses of C1 and the domain checkpoint boundary in the integration delta.

```sh
contentflow outbox checkpoint live.sqlite3 before-change.json --workspace-id "$workspace"
contentflow outbox restore-review live.sqlite3 before-change.json review.json --workspace-id "$workspace"
contentflow outbox inspect-review review.json
```

These commands expect a current `FixtureOutbox` database, an explicit workspace UUID and new destinations. The JSON files contain operation IDs, payload and receipt digests, budget and reservation amounts, and the observed states. Payloads, raw receipts, credentials and execution authority stay with the current ledger. A consistent SQLite transaction captures the projection. The file uses the standard canonical digest and publishes from a synced same-directory temporary file.

Restoration compares the checkpoint against the current authoritative ledger. Workspace and budget identities must match, every historical operation must still exist, and intent identity and terminal settlement evidence must agree. States can advance from HELD through UNKNOWN to a terminal state. A checkpoint cannot move an UNKNOWN operation back to HELD or discard a newer charge. The review also reports outstanding reservations and any overage freeze. It is readable as a separate JSON format and always reports `execution_authorized: false`. Retrying or settling a live operation remains governed by the original ledger.

Two API tests failed on the missing recovery module before implementation. The CLI test then failed at command dispatch. The passing cases cover an old HELD snapshot projected against UNKNOWN, a new hold and later overage settlement, omission of payload and receipt secrets, rejection of incompatible or tampered snapshots, and refusal to overwrite an existing review. The frozen design audit remains independent of executable test evidence.

The sealed checksum detects corruption. Authenticating a transferred checkpoint and restoring an entire workspace in one transaction remain separate gates. A current ledger is required to review old pending effects safely. Existing fixture concurrency is serialized by SQLite. Cross-machine execution authority and production reconciliation remain outside this increment.
