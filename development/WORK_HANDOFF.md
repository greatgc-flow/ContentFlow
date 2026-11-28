# ContentFlow and Engram development handoff

2026-11-28 KST. ContentFlow code, tests and static audit at c39bf40. CI definition at 417c432. Design baseline 9a40fa4. Engram package candidate d7a2777 on draft #147. Read COMPATIBILITY_REVIEW.md for the entry review. Original catalogs and historical checksums remain intact.

## Current entry points

Use CPython 3.12.14 from the checkout root. The standalone runtime has no third-party Python dependencies. Packaging uses setuptools 84.2.1. The development wheel is local only.

```sh
python -B -m contentflow brief preview --json
python -B -m contentflow run --workflow design/contentflow-v0.1/examples/workflow.example.json --dry-run --json
python -B -m unittest discover -s tests -v
python -B development/audit_design.py
python -B tools/probe_cpu.py render /path/to/new-private-directory
python -B tools/probe_cpu.py verify /path/to/new-private-directory
```

The first command calculates relative change from the bundled CSV. The second validates the offline DAG and prints its order. The native feasibility command requires the pinned Debian FFmpeg/FFprobe 7.1.5 build and locally installed DejaVu Sans. It refuses a different binary hash and refuses to render into an existing directory. A manifest is written after the final checks. Failed or interrupted candidates may contain incomplete files. The synthetic tone and private draft have no publication authority. The archived P0 export DTO, interactive editorial approval and a general renderer remain separate deliverables.

## Executed evidence

| Slice and design links | RED evidence | GREEN and follow-up evidence |
|---|---|---|
| Revision, canonical JSON, rights, standalone DAG. CF-006/007/010/011/040/048/065/072 | 6b5cf11: five import/file errors and one public CLI failure | 10822a9: six tests passed, including malformed steps, cross-workspace edits, expired and stale reviews. The pure preview compare binds workspace, entity, complete canonical snapshot, revision, actor, policy and expiry. Signed approval and publish scopes remain open. |
| Evidence and source calculation. CF-020/024/025/074 | 0171076: two missing-module errors and an invalid CLI command | bc60731: three tests passed. Changed inputs recompute the answer. Zero baseline, wrong unit, unknown or duplicate observation and nonnumeric expression are rejected. An extra test at 22e8a02 exposed an inherited decimal trap; 608d5b8 fixes the rounding context. The output remains an unreviewed draft. |
| Standalone packaging. CFX-01, EPP-029 | 1f22265: missing project metadata | 59882b6: console entry point and CSV included. Built a wheel with pip, no index/build isolation/dependencies and SOURCE_DATE_EPOCH=1795824000. Installed in a new empty venv with no dependencies. Both console commands worked from an unrelated directory with PYTHONPATH unset. Wheel SHA-256 f2bc15360cef5ae505c5b5c654a1f5522e089828ced0933dc2ce222ba8d5e8d9. |
| Job and step states, money and ambiguity. CF-013/019/063/064 | c7ca816: four missing-module errors | 3b84bf0: terminal and optional-step restrictions, integer KRW/USD minor units, exposure retention, evidenced settlement and overage. Currency coverage is limited to the two documented fixture currencies. |
| SQLite intent. CF-009/017/063/064, S09/S10/S11 | e88a54a: four missing-module errors | 9de6ef0: scoped create/open, unique replay, conflicting payload and receipt rejection, two competing transactions, unknown/frozen cost. At 22e8a02 a real child exits immediately before COMMIT and another exits after the durable claim. Reopen rolls back the first reservation and fences the second. These receipts cover the synthetic outbox database. Workspace migrations, CAS objects, backup/restore and a source deletion journal remain open. |
| Local media. CF-002/025/031/036/047/074, EPP-030, CFX-05 | aec16ef: missing native probe failed; b4ee577: a rehashed black replacement thumbnail passed the original oracle | ed3a3eb: real CPU render, full decode and stale caption failure. 35c6665 adds color samples inside and outside both bars in the thumbnail and decoded video. The black replacement now fails even when its manifest hash is updated. No licensed runtime binaries or fonts are included in the output. |

All 21 development unittest methods passed in the network-isolated Linux run, including native media. The design audit separately validated 90 domain requirements / 180 planned cases and 36 platform requirements / 102 planned cases. All 12 integration rows resolve. The historical verifier's NOT_RUN line describes its frozen design snapshot. The hosted domain regression skips the native media test when the exact fixture build is absent. Initial run 46044318382 passed Ubuntu 3.12.14 with 20 passes and that one skip. Windows setup failed before collecting tests because the Actions Windows x64 catalog has no 3.12.14 build. Its newest listed 3.12 artifact was python-3.12.10-win32-x64.zip. The Windows lane pins that patch as a separate compatibility test. Linux retains the D0 pin. Draft PR #1 records the final outcomes on both platforms.

### Native fixture receipts

| Measurement | Observed |
|---|---|
| Source and arithmetic | CSV records 2–3, 100 ms and 75 ms, 25% relative decrease. Source SHA-256 8a458535a74a1631a13c2de8bb62d24574c1234e1f467679aab877f595d5ca45. |
| Video | H.264, 1080 × 1920, 30 fps, 15 seconds, 450 fully decoded frames. |
| Audio and captions | AAC, 120,000 decoded mono samples at 8 kHz, peak 4,992; two parsed captions spanning 0–7.5 and 7.5–15 seconds. Tone only. |
| Repeatability | Three separate output directories had identical artifact bytes. MP4 SHA-256 b70d46064fb4a274d111ead167d5bf011d25bf9af65117057327239bac4537f9; manifest dbf48049c05fef872b5bc3ec5941a4206705ea1e2b9221cc84c33621032abc12. |
| Local provenance | Preinstalled Debian ffmpeg/ffprobe, GPL-enabled libx264 and librsvg, separately pinned system font. Local package copyright notice digests 28700587b4c278cd4e24adf4174a6fbe2510f27af962966d9ff15144b0b9ddbb (FFmpeg) and 63d3ba759d12804c5b31a9d5940d855c1820d1f5999e6b0872eb1c7ff045fbc9 (font). Redistribution and supported Windows build remain open. |
| Effects | Native render and verify ran under an isolated Linux network namespace. Python audit hooks on brief/plan and Engram shallow catalog observed 0 socket, 0 child and 0 write events. ptrace was unavailable, so there is no OS syscall-counter receipt. The native renderer does spawn the pinned local media tools. |

## Cross-repository gate review

| CFX scope | State and evidence boundary |
|---|---|
| 01 independent domain | PASS for both installed console entry points and frozen workflow fixture in an empty environment. |
| 02 relocation; 07 restore; 08 removal; 09 core upgrade | BLOCKED for managed execution pending E4 checkpoints, exact ownership, release allowlist, old updater and native move. |
| 03 shared runtime; 10 mixed packs | PARTIAL. Engram used one actual interpreter base and three distinct scratch environments. Each could load only its own synthetic module. Catalog accepts none, either, both and all three. Owned install, update, retain/reinstall and rollback await E2/E3. |
| 04 adapter; 06 grouped publication | BLOCKED for integrated use. E2 does not dispatch installed code or write the runtime registry. Need pinned wire/echo, durable receipt, one transaction owner and launch fencing. |
| 05 synthetic content | PASS for the Linux fixture oracle above. General app export authorization, full manifest DTO and Windows distributable are open. |
| 11 optional Studio/GPU; 12 external authority | NOT_RUN for the integrated operations. No models, providers, accounts or external publishers participated. Static absence of a public operation does not prove enforcement against arbitrary adapters. |

WP1 advanced independently to a7f76db in draft Engram #146 while this work ran. Runs 46042050493 and 46042050496 passed on that exact head. The provider now verifies publisher artifacts and joins scoped consumer evidence. The reviewed delta has no change to python_registry.publish or env_ops. Joining that provider into install/update remains gated on WP2/3 and coordinated recovery.

**Next independent REDs.** ContentFlow: introduce a durable source/asset commit with a missing object, corrupt digest and interrupted same-filesystem placement. Follow with verified checkpoint restore and source deletion replay. Connect domain policy and real media QC to the versioned export DTO before enabling a general export command. Engram: distinguish an owned retained tombstone from foreign, partial and corrupt registries using installation identity, and keep all ambiguous launches fenced. Follow with deterministic revision-bound plans, then single-journal fake transactions for all three packages. Native managed installation and release need the documented separate evidence and authority.
