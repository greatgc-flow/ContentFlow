# Coordinated workspace checkpoint and review

The offline workspace command coordinates the current source and fixture outbox SQLite ledgers under their common workspace UUID. It acquires the source writer lock before the outbox writer lock. It captures source rights and retention, referenced assets, pending effects and budget state while both writers are excluded. A digest seal lists every directory and the SHA-256 of every file. The seal publishes last, using an exclusive link. An interrupted candidate remains invalid through the workspace inspection and restore paths. Existing bundle and restore destinations are exclusive.

```sh
contentflow workspace checkpoint live-sources live.sqlite3 checkpoint --workspace-id "$workspace"
contentflow workspace restore-review live-sources live.sqlite3 checkpoint restored --workspace-id "$workspace"
contentflow workspace inspect restored
```

Restore validates the bundle and both current ledgers. It projects sources against current rights, expiry and retirement, then includes the current outbox as review metadata with no execution authority. Pending requests retain their current states. Raw request payloads and receipts stay with the original outbox. The result contains a source workspace and an inert JSON outbox. Editing the materialized source workspace invalidates the review seal.

Both original ledgers are required for safe replay. The current approach is a local consistency protocol for cooperating writers, not an authentication proof for a transferred archive. Other workspace state, installed migration, production authority and power-loss durability remain separate gates.

## TDD evidence

The initial RED showed the missing coordinated recovery module. GREEN covered tombstone and UNKNOWN replay, mismatched ledger identity, altered members and cleanup after unsuccessful sealing. The subsequent CLI RED failed at command dispatch. The child-process crash oracle interrupts immediately before publication of the bundle seal. The incomplete output is rejected while the original source remains readable. The final RED checks a resealed invalid workspace UUID. The parallel writer oracle verifies that SQLite rejects a second writer to either ledger during source capture.
