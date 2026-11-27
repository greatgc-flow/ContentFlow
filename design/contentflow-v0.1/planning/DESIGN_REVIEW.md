# Design review — pre-TDD readiness

Date: 2026-11-28 KST. Scope: English design, Korean start instructions, normative requirements/test mapping, proposed JSON contracts and synthetic fixtures. This is a **design baseline, not a deployed or runnable application**.

## Review dimensions and disposition

| Dimension | Evidence | Result | Remaining gate |
|---|---|---|---|
| Product scope and revenue models | 01, 07, 13 | documented | niche and commercial validation after pilot |
| Dependency and Core boundaries | 02, 05, 10 | documented | actual import graph and adapter tests |
| Data, job, approvals, budgets | 02, 08, schemas | documented | canonicalization/ID decisions and relational tests in D0–D2 |
| Evidence, originality and rights | 03, 09, 12 | documented | legal/account-specific validation, live rule refresh |
| Media and GPU | 04, 10, 14 | documented | real fixture, measured GPU/CPU, binary and model licenses |
| WebUI/CLI/REST/MCP parity | 05, 14 | documented | P1/P2 implementations and security tests |
| Publishing and revenue accounting | 06, 07 | documented | fake tests first, actual permission and reconciliation later |
| Backup/restore/security | 08, 14 | documented | fault injection and clean-host validation |
| Portable packaging | 14 and portable schemas | documented | supported OS/runtime matrix, actual pack build, signature, transfer |
| Traceability | CSVs and verifier | structural PASS | implement all selected tests, review assertions and prioritization |
| Schema/example syntax | verifier | structural PASS | runtime/relational/domain checks are separate |

## Cross-checks

Vertical: each requirement links to a design document, scenario IDs and two planned test cases. Horizontal: each scenario appears in at least one requirement; cover normal and adverse/recovery path for every catalog requirement. This is mapping coverage, not proof of exhaustive behavior or correctness. Fixtures are synthetic. Design decisions were made to keep the engine local-first, portable-first, zero-spend/export-only by default, independent from existing projects; optional integration and hosted features are deferred. All 180 application tests are NOT_RUN. No business niche or monetization eligibility assumed.

Outstanding before real implementation: establish authorized repository/branch or local project, select Python/version and locked dependencies, exact FFmpeg build and license, canonical JSON implementation, ID strategy, supported Windows/Linux release matrix, synthetic media fixture, portability packaging and host preflight. These are D0 spike/decision tasks, not excuses to claim production readiness. No actual portable executable, runtime pack, driver install, GPU benchmark, network integration, live upload, security audit, revenue experiment or GitHub mutation was performed. Source registry distinguishes checked vs candidate/blocked references; reverify on activation.

## Reproducible static verification

Run `python planning/verify_design.py` with a compatible Python and jsonschema installed in an isolated environment. The script verifies mapping uniqueness/references, scenario coverage, schema syntax, synthetic examples and relative links. Do not interpret these as 180 passing tests. See `STATIC_VERIFICATION.txt` for the observed output of the static run. No secret or production data in the examples.
