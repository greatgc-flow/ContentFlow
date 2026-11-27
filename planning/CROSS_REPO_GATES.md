# Development sequencing and gates

| Gate | Owner | Evidence / pass condition | Status |
|---|---|---|---|
| D0 | ContentFlow | Owner reviews current design; exact Python/lock and canonicalization chosen before relevant RED; offline fixture/FFmpeg rights, source provenance. | DESIGN; feasibility open |
| C1 | ContentFlow | Pure domain RED/GREEN, revisions, claims, policies, DAG, money, outbox; SQLite later fault tests. | NOT_RUN |
| C2 | ContentFlow | CPU render + full ffprobe/decode and local artifact/claim hashes, no external effect; independent of host. | NOT_RUN |
| E1 | Engram | Reviewed WP1–3 current runtime provider, native standard-user, independent env, single transaction gate. | PARTIAL historical probes; new acceptance NOT_RUN |
| E2/E3 | Engram | Generic descriptor/plan, fake trusted release, single pointer, crash/recovery, no-pack golden behavior. | NOT_RUN |
| E4 | Engram | Signed/trusted exact release and license proof, Windows move/rebuild, old updater, package leak sentinels, uninstall checkpoint. | BLOCKED pending trust/runtime/host proof |
| C3 | Both | Same pinned contract digest and validated release; CF-only/AI-only/both/none, remove-retain, copy, restore, failure, third pack. | BLOCKED by C2/E4 |
| E5 | Engram | AI-specific original Rev06 gates, generic manager success alone not enough. | BLOCKED by AI vendor/GPU/memory gates |
| P1+ | Both | UI/security, GPU actual workload/lease, optional authorized providers. | NOT_RUN |
| Release | Both | Actual green receipts for exact candidate, license/SBOM, artifact hash, owner authorization. | NOT_RUN |

Start C1 independently after D0 decisions. Do not wait for AI memory, GPU or Engram merge for pure domain work. Start native integrated test only when matching runtime/trust/manager contracts are proven. All original acceptance cases remain NOT_RUN; separate receipts record actual results, with BLOCKED/FAIL distinct. Avoid circular runtime or test dependency: CF's contract tests use frozen proposal fixture; Engram's contract tests use fake descriptor and app artifact; integration suite runs only exact paired candidates. No automatic publish or merge. Fail closed when compatibility unknown.
