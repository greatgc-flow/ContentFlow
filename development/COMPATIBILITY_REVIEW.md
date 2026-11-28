# Compatibility review and C1 decisions

Review date 2026-11-28 KST. Owner authorized development on separate branches. All executable receipts belong outside the historical packages.

| Remote reference at entry | Revision | Evidence and decision |
|---|---|---|
| ContentFlow main / design/pre-tdd-v03 | 5ef54a9 / 9a40fa4 | The design is the implementation parent. No open PR at entry. |
| Engram main / Local AI Rev06 | 61076a4 / c59c0e4 | Main CI run 45899889659 succeeded. Keep Rev06 IDs and legacy paths. |
| Engram draft #144, source discovery | e7b8e21 | Windows CI 46033092889 succeeded. Source support and artifact availability are separate. |
| Engram draft #145, runtime registry | 5202ca4 | Windows CI 46039005106 succeeded. Includes #144. Selected as Engram catalog parent. |
| Engram provider-admission branch | f0ac2f7 | Child of #145 adding T59/T60 contract tests at entry, no workflow run on that SHA. Independent work continues there. |

## Requirements and boundary review

| Boundary | Decisions and remaining proof |
|---|---|
| Evidence and editorial | Immutable workspace revisions bind source bytes, policy and downstream review. Synthetic material stays private and TEST_ONLY. Collection, transformation, export and publication have separate scopes. Source hashes in archived examples are placeholders. |
| Workflow and effects | Declarative dependency graph, allowlisted CPU/local capabilities and deterministic scheduling. Plan is read-only. A review of a local draft cannot authorize a remote effect. Durable intent, lease fencing, cost reservations and unknown-effect recovery require transactional tests. |
| Media, distribution and business | CPU fixture uses 100 and 75 ms with a 25% relative decrease. Full C2 needs independently decoded media, real caption/audio/lineage checks and local export QC. Commercial policy, account eligibility, publication consent and settlement remain distinct. |
| Host and runtime | ContentFlow standalone has no Engram imports. Managed mode must use physical SYSTEM and the validated host context. Legacy Python and venv retain their paths. Share only an exact compatible base with separate immutable consumer environments and workspaces. No executable fallback. |
| Transactions and retention | Engram python_registry.publish enters env_ops.execute and owns the lifecycle lock. Wait for the runtime provider's coordinated prepare/step/recover API before grouped writes. Pack removal must preserve unknown files and durable data. Global uninstall needs an independent recovery inventory. |
| Packaging and trust | Engram's core ZIP collector walks the system tree with exclusions. Test sentinels and positive inclusion before introducing installed pack payloads. Old updater/downgrade, signature/revocation, license, native move and restore are separate gates. No production trust can be derived from fixture_only or a SHA alone. |
| Parallel development | Catalog semantics and independent C1 are open. Shared registry publication is blocked on WP1–3. C3 depends on C2 and E4. AI memory, GPU, Studio and external platform acceptance keep their original independent gates. |

## Baseline audit

The repository checksum manifest passed on the unmodified parent. The domain verifier resolved 90 requirements to 180 cases and 49 scenarios, checked all 16 schema/example pairs and rejected five negative examples. The EPP index has 24 fixtures, including six structurally valid semantic negatives, across eight schemas. The 36 requirements link in both directions to 102 planned cases. Crosswalk, risk and all 12 CFX integration rows resolve to requirement IDs. The embedded v0.2 archive SHA-256 is 977e8e3fee77c766268bbc0104056fdef1702b77aa2d7f059aa0996687152d07. Its nested domain archive is f7b8592abce66d9c9b25c3613c61e239f1e8ad318cdc11452ddaa5a04c7ca097. Both passed ZIP CRC validation. Engram's Rev06 checker verified eight manifest members, 150 cases, nine groups, 50 ADRs and 28 risks. Current checks cover structural traceability. Historical NOT_RUN rows remain intact.

## D0 implementation decisions

- Exact C1 test interpreter CPython 3.12.14, Linux x86-64. Application dependency lock is the Python standard library only. This development pin grants no Windows runtime or redistributable binary approval.
- Canonical format CF-CJSON-1: compact strict UTF-8 JSON, keys sorted by Unicode code point, no ASCII escaping or Unicode normalization. Admit scalar Unicode strings, booleans, null and signed integers within the interoperable 53-bit range. Reject floating point, duplicate source keys and invalid Unicode. Domain-separated structured hash is SHA-256 of ASCII format identifier, NUL, then canonical bytes. Raw assets retain ordinary SHA-256. This profile applies only inside CF and does not define the host signature format.
- Entity identifiers are workspace-scoped UUID4, allocated by the caller at creation. Revisions advance by one with an expected version. Pure policy evaluation takes an explicit UTC clock. Source-backed reviews and deterministic workflow planning are the first read-only slice.
- EPP descriptor v1.0 schema SHA-256 is 83056e568d9783fde96bb3a750a270327cd6e78ed197d32973fd1dd5d1df266f. Pin exact bytes of the AI, ContentFlow and Gamma descriptors for Engram's fixture gate. Each is metadata only.
