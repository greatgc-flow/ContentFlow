# 08 — Operations, security and cost control

## 1. Budget and execution control

Budget is an enforceable domain invariant, not a warning. Separate monetary budget from token/quota/VRAM limits. Offline profile: external spend cap = 0, network disabled. Suggested pilot envelope KRW 50,000 per calendar month, Asia/Seoul, opt-in only. Additional caps per project, provider, day, job and attempt; all applicable caps must pass. Currency-specific accounts and explicit, conservative FX conversion (quote timestamp, expiry, rate, fee buffer). Do not count provider promotional credits until verified; credits do not eliminate hard usage caps. No guarantee that remote provider bills match estimates.

Before a paid or uncertain-cost call: (1) estimate upper bound including retries, rounding, taxes/fees when known; (2) verify current price and entitlement; (3) check allowed data boundary; (4) request explicit owner approval for bounded amount; (5) reserve atomic amount across applicable scopes; (6) persist intent, then call; (7) settle actual cost, release unused reservation. Never use float money. If no upper bound, stale quote or exhausted cap, block. Unknown remote charge retains exposure as `UNKNOWN`; no retry or fallback until reconciled. If provider unexpectedly exceeds estimate, record full actual, freeze provider and alert; hard local cap cannot guarantee third-party billing. Budget resets do not erase unresolved exposure. All failed generation costs included in economic reports. Provider-side limits/billing alerts are defense in depth; verify live account controls rather than assume them.

Budget reservation transitions: `HELD -> SETTLED | RELEASED | UNKNOWN`; `UNKNOWN -> SETTLED | RELEASED` only on verified reconciliation. Release means no bill expected and evidence recorded; cancel does not imply no charge. Compare-and-swap with transaction; two concurrent jobs cannot reserve same remaining capacity. Approval applies to exact operation, provider, scope, currency and expiry. For P0 fake adapters, verify races, unknown and overage without network or charges.

## 2. Threat model and trust boundaries

| Boundary / threat | Mandatory control | Test evidence |
|---|---|---|
| Untrusted RSS/API/LLM output, indirect prompt injection | parse data only, no tool authority; schema, claim/asset checks, least privilege | malicious source fixture cannot invoke process/network/approval |
| SSRF via URL/redirect/DNS | HTTP(S) allowlisted destinations, block non-public IPs, recheck redirects and DNS at connection, reject arbitrary proxy | local service/private range blocked |
| Local import and archive traversal | scoped workspace, reject links/reparse traversal and path escape, size/expansion/MIME caps | malicious path, zip bomb, symlink fixtures |
| Media process / template | argument vector, trusted template ID, isolated worker with network off, resource bounds | injection and malformed media tests |
| Credentials and OAuth | OS credential store or env reference, minimal scopes, per-account tokens, revocation and rotate, no token in trace | log and backup secret scan |
| WebUI on local network | loopback only, session auth, random CSRF token, same-origin, CSP, XSS escaping, no public bind by default | unauthorized and cross-origin requests fail |
| AI/CLI adapter | noninteractive supported entrypoint, cwd sandbox, bounded stdout/stderr, no arbitrary shell, no session cookies | timeout, truncation, disallowed command fixtures |
| Plugin / model supply chain | pinned version and checksum, dependency audit/SBOM, no auto trust remote code, reviewed licenses and isolated env | deny unknown/changed plugin manifest |
| Sensitive enterprise / personal content | classify before egress, explicit project scope, redact/minimize, default local, audit access | no data crosses restricted boundary |
| Hosted tenant separation (P3) | tenant ID at every storage/auth boundary, isolated secrets/jobs/objects, abuse limits | independent security test before hosting |

Audit events: actor, action, UTC timestamp, scope, request/trace ID, target revision and result, safe reason and digests. Do not log raw source bodies, credentials, personally identifying records, private URL query tokens or copyrighted excerpts. Redact nested fields, CLI output and error bodies; no implicit telemetry. Local administrator can rewrite local storage; integrity checks detect corruption, not malicious admin guarantees. No autonomous engagement, account creation, spend, billing contract, remote deletion or visibility changes.

## 3. Reliability and recovery

Fault cases: crash before/after object rename, before/after DB commit, lease expiry, process OOM, timeout before/after remote acceptance, disk full, corrupt blob, auth revocation, rate limit, outage, changed policy/price, incompatible schema, deleted source, revoked asset permission. Local recovery uses staged files, hash verification, transaction/outbox, lease fencing, bounded retries. Remote unknown is quarantined for lookup/owner attestation; never infer absence from timeout. Resume uses new job linked to prior terminal attempt. Retry delays obey Retry-After and max deadline. Do not retry non-idempotent operations unless remote absence is verified and consent remains valid. No hidden provider fallback.

| Failure | Expected response |
|---|---|
| transient read | bounded retry and jitter |
| GPU OOM | release lease, inspect memory, approved smaller/CPU path at most once |
| provider quota/auth exhausted | wait for owner or reset; no key rotation to evade limits |
| denied rights/policy | hard block, rework input; no override |
| missing review/budget | explicit wait status |
| disk full | stop cleanly, preserve verified outputs, reclaim owned temp only |
| duplicate external receipt | reconcile unique remote ID, no double revenue or upload |
| remote status unknown | freeze attempt, reconcile; never blind retry |

Backup includes DB snapshot using supported backup API, permitted referenced blobs and manifest, config without secret values, deletion journal. Verify hashes and restore into fresh path; reapply retention/deletion obligations before opening restored workspace. Backup encryption if sensitive; export key separate. No copying active database/WAL blindly. Retain previous known-good release and documented migration rollback/restore. P0 targets (provisional, validate actual host): no loss of committed metadata under tested local crash points; recovery of expired local leases within two configured polling intervals; backup restore RPO at last successful backup, RTO measured, no false claim of zero loss. No service SLA until measured.

## 4. Telemetry and maintenance

Structured JSON logs with size rotation, optional local OpenTelemetry, health for DB/disk/FFmpeg/model/worker/queue/account/price and policy freshness. Metrics: queue depth, lease age, attempt count, duration, failure taxonomy, reserved/actual/unknown spend, cache hit, accepted assets, QC failures, provider latency/quota, stale approvals, rights expiry, unconfirmed publications. Monitor has summary + expandable detail, unknown shown explicitly; no raw secrets. `doctor` reports compatibility and remediation without installing or changing anything. Debug bundles are allowlisted and owner-reviewed. Job monitor distinguishes RUNNING, WAITING_REVIEW, WAITING_BUDGET, WAITING_EXTERNAL and terminal states.

## 5. Build and release policy

TDD stage: Windows and Linux CPU CI, fake network/provider by default, dependency lock, lint/type checks, unit and schema/contract tests, fault injection, integration and reproducible offline E2E with real FFmpeg. Optional GPU and remote integration suites require separately configured runner, credentials and explicit approval; mark missing environments NOT_RUN, not PASS. Security scan, license inventory including model weights/fonts/stock, SBOM, reproducible build metadata and signed/hash release manifest. Migration backup/restore dry run. Never auto-update provider model/terms or dependencies during production job. No main merge, tagging, releases, external account configuration or billing unless owner separately requests them. No implementation has run at this design stage.

## Portable operation

14 specifies clean-host acceptance, path isolation, explicit offline pack management, interrupted move/update recovery, device-bound credentials, local DB storage, and optional worker trust. No automatic driver or OS changes. Include portability checks in release and restore exercises.
