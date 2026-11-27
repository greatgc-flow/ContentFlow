# 05 — Interface and adapter contracts

## 1. Stable application surface

Commands return typed success/error with `request_id`, entity IDs, revision, status, warnings. CLI human output plus `--json` machine mode; errors to stderr, stable exit codes: 0 completed, 2 invalid, 3 policy/auth denied, 4 pending review/budget/external, 5 transient failure, 6 permanent failure, 130 interrupted. Async submit returns job handle (0 accepted) distinct from completed; `job wait` maps result. Dates timezone-aware, currency explicit. No prompting in `--non-interactive`. Secrets supplied through OS keyring/env reference, never argv, log or config export. All examples prospective.

```text
contentflow init --profile offline
contentflow doctor --json
contentflow project create --name demo --profile TECH
contentflow source import --project demo --file fixtures.json
contentflow collect --project demo --dry-run
contentflow topics rank --project demo
contentflow brief create --topic ID
contentflow brief verify --id ID
contentflow plan --brief ID --format short --lang ko-KR
contentflow run --workflow offline-short --content ID --dry-run
contentflow job show ID / job wait ID / job cancel ID / job resume ID
contentflow review show --content ID
contentflow approve --content ID --action export --digest HASH
contentflow export --content ID --destination youtube
contentflow publish plan --content ID --account ID
contentflow publish execute --intent ID --approval ID
contentflow publish reconcile --intent ID
contentflow metrics import --file metrics.csv
contentflow revenue reconcile --file settlement.csv
contentflow budget show / budget estimate --workflow ID
contentflow audit export --project ID
contentflow backup create / backup verify / backup restore
```

`--dry-run`: validate graph, capability, policy and estimated costs using cached/synthetic data; no network unless a separately authorized read-only probe, no writes to business state, no uploads or reservations. May emit plan to stdout. `--offline` forbids egress even for fallback. `--resume` never repeats unknown side effects. Approval is explicit action and digest bound to revision/account/visibility/metadata/rule revision/expiry (and max spend for budget approval). `--force` cannot override hard policy. Human confirmation for paid/public operations, but approval token can be created only via authenticated user action, not AI prompt content.

## 2. REST API proposal (P1)

Base `/v1` local authenticated service; OpenAPI generated from typed DTOs after implementation. JSON with schema version. POST mutation requires `Idempotency-Key` scoped by actor/workspace/route, request digest mismatch returns 409; same request returns same resource. Optimistic edit `If-Match` rev, 412 on stale. 202 async, 200/201 read/create, 400 validation, 401/403 auth/policy, 404 unknown (no cross-workspace leak), 409 conflict, 422 invalid domain transition, 429 limits, 503 transient. Structured error code and safe message. Pagination stable cursor; never secrets. No arbitrary filesystem access: upload with size/MIME checks, download via scoped IDs. No arbitrary command endpoint.

| Verb / path | Use case |
|---|---|
| POST /projects | create charter |
| POST /projects/{id}/sources | ingest authorized file/URL |
| POST /briefs | create from candidate |
| POST /briefs/{id}/verify | create verification job |
| POST /contents | plan revision |
| POST /jobs | validate/submit workflow |
| GET /jobs/{id} | status and safe events |
| POST /jobs/{id}/cancel, /resume | lifecycle |
| GET /contents/{id}/review | preview, claims, QC, budget |
| POST /approvals | explicit user authority only |
| POST /exports | artifact package |
| POST /publication-intents | plan only |
| POST /publications | execute approved intent |
| POST /publications/{id}/reconcile | status reconciliation |
| POST /metrics/imports, /ledger/imports | owned data imports |
| GET /budgets, /metrics, /ledger | report |
| GET /health, /capabilities | health and provider features |

WebUI P1 pages: workspace/settings (no secret reveal), research inbox, evidence editor, project studio storyboard, job/queue monitor, review/preview, export & destination, analytics & revenue, audit/budget. Clear dry-run/real distinction, show exact account + destination + visibility + cost bound before user approval, preview content hash; stale preview prompts re-review. Accessible keyboard controls and Korean labels; network-bound pages show unavailable not zero. Local session auth, CSRF, origin checks, XSS escaping, CSP, no remote tracking by default.

MCP P2 tools: list projects, list candidates, show claim/brief, estimate workflow, submit offline/draft job, inspect job, export preview. Read-only/draft by default. Paid/public side effects require UI/CLI owner approval independently; MCP cannot mint approvals or access keys. Treat model tool inputs as untrusted. Tool output bounded and redacted; no arbitrary shell. Expose capability and schema versions. Rate limit and authorization per tool.

## 3. Provider ports (conceptual signatures)

```text
Capabilities = {kind, provider_id, version, operations, formats, locales,
                data_boundary, auth_state, license_state, pricing_state,
                rate_limits, idempotency_support, retention_policy, health}
Provider.describe() -> Capabilities
Provider.estimate(request, context) -> Estimate[lower, upper, currency, expires]
Collector.discover(query, cursor, context) -> Page[SourceCandidate]
Collector.fetch(candidate, context) -> SourceRevision
LLM.generate(schema_id, evidence_bundle, limits, context) -> StructuredDraft
Verifier.assess(claims, sources, context) -> ReviewProposal
AssetProvider.create(spec, context) -> AssetResult | PendingRemote
Renderer.render(scene_bundle, context) -> Artifact | PendingRemote
Publisher.prepare(package, destination, context) -> Intent
Publisher.submit(intent, approval_ref, context) -> Receipt | PendingRemote | Unknown
Publisher.lookup(intent, remote_ref, context) -> RemoteState
Analytics.fetch(account, date_range, cursor, context) -> MetricPage
LedgerImporter.parse(file, mapping, context) -> LedgerProposal
Storage.put(bytes, expected_hash, context) -> ArtifactRef
```

Context includes workspace/project, actor, operation ID, trace, deadline, cancellation, policy snapshot, limits and permitted data boundary. Provider cannot authorize itself. Any `PendingRemote` has remote request ID when supplied, next poll and expiry; persist before polling. Unknown charge tracked in budget. `estimate` may be unknown; no paid call if upper bound missing. Provider has strict schema output validation, contract test suite and manifest; incompatible versions disabled. Failures classified; raw body never logged with personal information. Manual adapters use export/import receipt and user attestation, no pretend API success.

## 4. Portable interface extensions

See 14 for prospective launcher, `portable`, `pack`, `doctor` and worker commands. All actions use explicit offline/authorization mode and preserve existing exit semantics. Runtime repair may write disposable staging state but not mutate business state; dry-run and verify-only remain read-only.
