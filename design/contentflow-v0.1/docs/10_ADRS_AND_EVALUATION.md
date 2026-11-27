# 10 — Architecture decisions and adoption evaluation

Decisions here are proposed baseline decisions, not approvals to spend or install. External versions, licenses and account entitlements remain activation gates. P0 avoids dependency on candidates that require cloud or large models.

| ADR | Decision | Reason / rejected alternative | Revisit trigger |
|---|---|---|---|
| A01 | Python modular monolith, domain/application/ports | avoid microservices and provider-coupled fork | measured scaling constraint |
| A02 | SQLite WAL + SHA-256 blobs, UUID4, UTC, integer minor-unit money | durable local recovery and portable backups | multi-host / tenant requirements |
| A03 | RFC 8785 canonical JSON for structured digests; no nonfinite values; integer timeline/money | deterministic approval/cache semantics; validate library compatibility before implementation | unsupported runtime, versioned migration |
| A04 | P0 FFmpeg/ffprobe CPU renderer; optional Remotion | minimal actual video path; React scenes later | rendering/quality benchmark and license |
| A05 | separate GPU worker, one slot by default | prevent VRAM contention and crashes | actual hardware benchmark |
| A06 | independently versioned interfaces; CLI P0, WebUI/REST P1, MCP P2 | same use cases, no separate business logic | user UX/pilot needs |
| A07 | default export-only, no public posting or spend; explicit approvals | unknown account/policy/billing constraints | permission and security gate |
| A08 | deterministic offline fixture providers; adapter for MoneyPrinterTurbo only if passes spike | reuse media functions without adopting editorial/publishing core | proven isolated operation and license |
| A09 | Engram/PeerHub optional file/structured task interchange | avoid Core changes and private interface assumptions | actual repo review and compatibility test |
| A10 | schema version + content/revision digest | traceability and fail-closed stale approvals | version migration ADR |
| A11 | no self-use TikTok Direct Post, no cookie/browser bypass | app policy and account risk | verified compliant product use |
| A12 | Python 3.12 candidate for Core, 3.11 compatibility target; model env independent | avoid coupling to rapid ML dependency shifts | dependency resolver and CI evidence |
| A13 | trusted built-in templates, no arbitrary workflow code | security and reproducibility | reviewed sandboxed plugin contract |
| A14 | no automated production decisions based solely on LLM confidence | review and factual grounding | improved evidence method with validation |
| A15 | no payment processor or multitenancy before P3 | legal, tax, security and real demand | approved commercial milestone |

## Candidate comparison (document inspection, no execution)

Criteria: architecture fit 25, evidence/compliance extensibility 20, local operability 20, licensing clarity 15, maintainability/testing 10, integration effort 10. Scores are engineering hypotheses, not audited security, quality or measured speed. Unknown capability is not presumed present. Must pass hard gates even if score high.

| Option | Fit | Evidence | Local | License | Maintain | Effort | Sum | Use |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Independent Core + FFmpeg | 24 | 19 | 18 | 12 | 9 | 5 | 87 | P0 baseline |
| Independent + MoneyPrinterTurbo adapter | 23 | 19 | 15 | 11 | 7 | 8 | 83 | P1 spike |
| Full MoneyPrinterTurbo fork | 14 | 8 | 15 | 11 | 7 | 7 | 62 | reject as baseline |
| Remotion sidecar | 19 | 15 | 14 | 9 | 8 | 7 | 72 | optional renderer |
| Short Video Maker adapter | 14 | 9 | 9 | 10 | 6 | 7 | 55 | research only initially |
| n8n workflow-only | 12 | 9 | 13 | 7 | 6 | 8 | 55 | optional orchestration |
| hosted text-to-video only | 8 | 6 | 2 | 6 | 5 | 8 | 35 | optional manual provider |

MoneyPrinterTurbo public pyproject declares MIT, Python >=3.11 and includes MoviePy, Streamlit, FastAPI, TTS/ASR and multiple provider dependencies (R10). This indicates useful composition functionality; it does not certify commercial rights to stock media, TTS, third-party services or secure default behavior. Do not use unattended unofficial TTS endpoints or assume subscription entitlement. Short Video Maker describes REST/MCP, Pexels and English-only Kokoro in current README; native Windows not supported per README (R11). Use WSL/container if later justified, but Korean voice and user-supplied assets need independent proof. Remotion commercial terms, telemetry and usage-based billing depend on use (R12); verify actual license for internal/SaaS use, not assume free. n8n is optional, licensing must be confirmed for internal vs embedded commercial service; current old docs URL did not resolve in this review (R13). Qwen3-TTS public repository is Apache-2.0 (R14); model checkpoint and voice rights separately verify. FFmpeg binary distribution license depends on build flags and linked libraries (R16).

## Spike protocol before adoption (no tests run yet)

1. Pin repository tag/commit, verify provenance, dependency graph, SBOM, licenses (source, binaries, models, fonts, assets, API terms), security advisory scan; document exact inspected state. No arbitrary remote code or auto-install in production.
2. Isolated Windows CPU and optional WSL/Linux env, network disabled first. Attempt fixture-driven rendering with owned sample assets; capture logs, secrets, output manifest, exit codes and local resource use. No real keys, downloads or charges without approval.
3. Compare CPU FFmpeg vs candidate with identical 15/60/90s and 8min scene fixtures; measure actual time, peak memory, captions, Korean glyphs, correctness, artifact rights and reproducibility. Hardware profile probe, no GPU claim without owner benchmark.
4. Fail cases: invalid assets, cancellation, OOM, disk full, restart, provider timeout, no unintended publication, missing credentials, stale license and policy. Check vendor-generated paths and network requests. Validate interface and result schemas; don't adopt monolith merely to reuse 1 function.
5. Go/no-go: all mandatory security/rights/offline/contract checks PASS, license owner-approved, no uncontrolled costs, actual integration maintenance quantified. If not, use simple own adapter. Record NOT_RUN and rationale for unavailable environments. No repository fork or code import in this design phase.

## Additional portable decisions

| ID | Decision | Rationale | Revisit trigger |
|---|---|---|---|
| A16 | portable Lite + optional versioned packs | no admin/global runtime by default; isolate heavy deps | clean-host failures |
| A17 | recreate env after root move from local locked wheelhouse | venv absolute paths; no surprise network | alternative proven relocatable distribution |
| A18 | local DB + authenticated remote media worker, no shared WAL | reliability and credential isolation | approved hosted migration |
| A19 | host drivers never installed automatically; CPU fallback explicit | hardware/OS constraints and cost control | supported host capability matrix |
