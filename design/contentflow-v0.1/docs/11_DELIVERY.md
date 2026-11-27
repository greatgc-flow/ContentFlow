# 11 — Delivery plan and definition of ready/done

## 1. Implementation increments (not dates or promises)

| Increment | Scope | Exit evidence | Deferred |
|---|---|---|---|
| D0 | validate baseline, choose Python/FFmpeg versions, canonicalization implementation, inspect repo/branch and dependency policy | decisions recorded, docs/contracts valid, no network/spend required | live integrations |
| D1 | domain states, revision, money, policy, approval, graph, test fakes | unit tests red/green/refactor, invariants verified | DB and rendering |
| D2 | SQLite storage, leases, outbox, budget, audit, backup, fault injection | recovery and concurrent reservation tests, migration | external calls |
| D3 | local source → claim/brief → script/scene → FFmpeg → QC → approved export | actual CPU MP4+SRT+article+manifest, offline E2E; not fake render | real LLM/TTS |
| D4 | offline analytics/ledger CSV, CLI usability, portable Lite packaging and move/restore | reconciliation, missing metric, economics, end-to-end CLI, clean non-admin host and move tests | payment and live metrics |
| D5 | WebUI/REST, provider capability registry, authorized RSS/local models and optional Studio/GPU packs | CLI/API parity, CSRF/auth/security, measured local GPU if available | automatic public post |
| D6 | optional Engram/PeerHub, MoneyPrinterTurbo/Remotion spikes, platform-specific export, permitted API adapters | contract, license, approved private test if explicitly authorized | unsupported platforms |
| D7 | experiments, long-form/short variants, distribution reconciliation | owner-reviewed pilot metrics, budget and quality thresholds | SaaS/payment |
| D8 | optional MCP, additional workflows, B2B/SaaS | separate threat, legal, commercialization review and explicit approval | no automatic expansion |

P0 is D0–D4. P1 covers D5–D6 and basic variants. P2 advanced providers, MCP and controlled experiments. P3 hosted multi-tenant and payment integrations. A feature in design may be deferred or rejected if a spike fails. All modes must degrade safely to export-only.

## 2. Definition of ready for first RED

- Requirements IDs and tests have bidirectional traceability. Critical paths mapped to failure and success scenarios. JSON Schemas and examples parse and validate; relational/temporal invariants explicitly marked as domain checks.
- Select working directory/repo, branch and Python version/lock strategy; no main merge. Document dependencies and license choice before copying third-party code. Select a compatible RFC8785 implementation or raise ADR; no handwaving around approval digest.
- Define real FFmpeg E2E fixture with owned/redistributable narration, static chart and no external network; fixture tone only unit-test use. Do not mark synthetic export publishable.
- Confirm Windows/Linux runner and capability probes, no live credentials. Owner decisions for actual niche, GPU, accounts, provider spend and business entity are NOT blockers for fake/offline TDD.

## 3. Definition of done per change

Requirements updated only if decision recorded; failing test written before production code; smallest passing implementation; refactor; targeted+regression tests; contract/schema check; security/rights/licensing review for touched dependencies; docs, CLI help and migration impact aligned; compare observed results with expected. Report PASS, FAIL, BLOCKED, NOT_RUN separately, attach exact command/tool version/commit/test counts. No fabricated test results. Production no secrets in tree. CI local/network-denied where feasible, Windows+Linux. Owner review for commercial release, account connection, public posting, purchase, model download requiring approval, hosted exposure and main merge.

## 4. Open decisions and conditions

Owner can defer niche, brand, channel, revenue route and language mix indefinitely; profile configuration independent. Need later actual VRAM/OS/driver/RAM, authorized content sources, licensed narration/assets, provider entitlement and account setup, business/licensing/tax review, and actual current private Engram/PeerHub adapter contracts. Need measured performance and spend; no target guaranteed. Core license for ContentFlow not chosen by owner; docs are internal design, do not infer permission to publish or choose license. P0 target Python 3.12 (3.11 compatibility candidate) subject to dependency spike. API and web automation features disabled until current official terms and actual account conditions validated. No requirement for a live platform or paid API to begin D1.
