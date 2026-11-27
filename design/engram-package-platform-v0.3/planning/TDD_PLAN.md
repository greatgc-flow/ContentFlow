# Pre-TDD plan and release evidence gates

## Entry point and explicit stop

This document is the test specification, not executable tests. Existing #144/#145 work continues in its own branch. Before RED, recheck remote main/drafts and CI, align WP1–3 final signatures and actual existing CLI/output fixtures, and review ADRs/risks. Synthetic pure descriptor/plan RED can begin independently after owner accepts this contract; native provider/security/release-dependent RED is gated by the applicable feasibility proof. No product code, user data or real account usage in this revision.

1. E2 RED-1: synthetic catalog with ai/contentflow/gamma; duplicate aliases/profiles/case/slot escapes, default profile absent, unsupported capability/protocol/unknown fields, P0 hard-dependency; semantic oracle independent of schema. Then no-pack fixture against exact historical golden CLI/registry/filesystem/network counters.
2. E2 RED-2: inventory without mutation, foreign/retained/corrupt markers and generation/ownership/ref graph. Pure plan determinism, revision+policy+scope+approval stale, byte math and offline facts. No provider calls.
3. E3 RED-3: fake artifacts/adapters, pinned archive admission, release trust stub controlled by fixture (not production auth). Exact argv/exit, adapter response validation, no package imports, no automatic install. Crash seams around intent, stage, probe, drain, migration, each runtime/pack CAS, commit, health, final receipt. Reopen with previous/new/extraneous bytes; fail closed on divergent. One env_lock/env_ops owner; concurrency (two processes, launch/update race). Native port only after WP3.
4. E4 RED-4: build verified disposable Windows x64 fixture with standard user, clean host (no global tools except OS prerequisites), network denied offline mode, exact pinned native runtime. FFmpeg/CF artifact gate separate. Check no host changes via before/after registry/PATH/service/task/roots; capture actual native imports, env paths, child argv, exit, process ownership. Same-volume move and cross-volume offline rebuild; Korean/spaces, unsupported path failure. Scope is supported tested OS, not all systems.
5. E4 RED-5: checkpoint/restore, data-retained remove and reinstall, old archive, corrupted backup, sole copy, helper update/uninstall. Core release exact allowlist and synthetic leakage sentinels. Old stable -> candidate via actual public updater, helper interrupted/rollback, runtime references, unsupported downgrade. Cross-pack independent vs coherent shared-runtime group. Never use actual customer data.
6. E5/C1–3: independent CF CPU pipeline then managed install and domain lifecycle; AI profile uses original Rev06 gates, not pack manager's generic success; same generic operations with third descriptor/artifact. Optional pack absence, partial, corrupted registry, retained slots. Only when baseline & new gates pass, release candidate may be considered (explicit owner authorization).
7. P1 RED: actual RTX 3060 device/driver and CPU/NVENC/GPU workloads, cross-root lease if needed, crash, OOM, owner/PID reuse, unowned task. AI provider/PG/memory and CF studio/voice/GPU separate evidence. No model fetch or provider cost without explicit approval. P2 remote worker/SaaS not part of first release.

## Matrix and risk crosses

Avoid exploding all combinations: pairwise coverage for ordinary axes and full targeted Cartesian for loss/security. Independent axes: package state absent/retained/installed/partial/corrupt/foreign; pack set none/A/CF/both/third; operation read/install/update/repair/backup/restore/move/clone/remove/purge/global; trust approved/unknown/revoked/offline stale; runtime legacy/extra/private/compatible/incompatible/pinned/missing; failure none/pre-intent/mid-stage/mid-pointer/after-commit/pre-ack; storage local/unsupported/moved/copy; service stopped/running/busy/unknown; approval current/stale/copied; GPU no/idle/owned/external. Mandatory crosses: two registries × each crash boundary × resume/rollback × launch attempt; install × stale plan × competitor; update × incompatible consumer × protected old binding; clone × copied paid/publish intent × network offline/online; global uninstall × checkpoint failure × unknown slot; legacy update × forbidden sentinels × renamed system root; schema migration × crash × old app; archive path × Windows normalization × preexisting reparse; GPU orphan × PID reuse × unknown external occupancy; old executable downgrade × retained data. Each test must assert durable bytes, ownership, actual process/socket/effect counters and receipt, not just exit 0.

## Gates / statuses

| Gate | Requirement | Required evidence | Current |
|---|---|---|---|
| G0 Design | reviewed source baseline, contracts and traceability; proposed decisions owner accepted | actual static audit, decision review, new branch baseline | static audit only; owner review pending |
| G1 WP1–3 | native provider+bindings, lock and recovery port | current #144/#145 receipts plus applicable new tests and native Windows | PARTIAL existing evidence; new NOT_RUN |
| G2 Common manager | pure plans/registry/adapter, legacy no-pack, fake install/update/remove, three-pack generic test | unit + fault/concurrency receipts | NOT_RUN |
| G3 Native and trust | exact approved artifact provenance, licensing, production key/revocation, standard-user clean-room | manifest/SBOM, signature verification, native Windows footprint, offline build | BLOCKED until O1/O4 and native proof |
| G4 Lifecycle | native move/backup/restore/uninstall/core self-update/old upgrade | checkpoint restore test, byte inventories, helper receipt, mixed pack results | NOT_RUN |
| G5 CF Lite | CF CPU synthetic source to valid MP4/SRT/article/manifest, managed install independent AI | native executable and content validation, no external effects | NOT_RUN |
| G6 AI | eligible selected profile + original Rev06 gates | provider and memory/consent/target hardware proofs | BLOCKED per WP0 |
| G7 P1 | studio, voice, GPU / host lease scope | target measured hardware, egress proof, UI security | NOT_RUN |
| G8 release | regression + exact signed candidate + owner approval | artifact hash, release allowlist, test matrix, recovery runbook | NOT_RUN |

Pass only on actual oracle receipt for exact commit/artifact/environment, failures stay visible; BLOCKED and NOT_RUN distinct, no auto-scoring to 100. Original WP0/#144/#145 passing tests are not equivalent to new tests. All rows in new TEST_CATALOG start NOT_RUN. Static audit only confirms structural contracts, referential integrity and original archive hash.
