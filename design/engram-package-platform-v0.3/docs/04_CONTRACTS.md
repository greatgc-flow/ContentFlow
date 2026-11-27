# Contracts and CLI freeze proposal

All schemas and examples shipped here are TEST_ONLY. JSON shape validation alone cannot establish trust, path containment, ownership, compatibility or authority. Production codec must reject duplicate keys, noncanonical/oversize input, NaN/Infinity, unknown major, ambiguous enum, invalid timestamps and unrecognized fields. UTF-8 strict, no BOM on wire; bounded depth/size. Use deterministic canonical JSON (RFC 8785/JCS candidate; verify implementation before production, do not substitute pretty-print hash). Digest fields are lower-case SHA-256 over exact bytes, not path names; signed manifest canonicalization and trust root are pre-RED feasibility item O1.

## 1. Metadata contract and invariants

| Object | Authority and mandatory contents | Semantic invariants beyond schema |
|---|---|---|
| Descriptor | reviewed catalog: schema_version, package_id, slot_rel, display name, protocol range, aliases, profile capabilities, adapter capabilities, trust key IDs | canonical ID; slot map; unique aliases/profile IDs, default exists; reserved names incl Win32 device names blocked; P0 no hard-pack deps; known runtime capability; duplicate/cycle/missing dependency rejected. |
| Release manifest | package/version/platform, minimum/maximum manager protocol, artifact digest and bytes, expanded members, license evidence ref, SBOM digest, runtime lock, adapter entry relative path, app entrypoint relative path, domain schema compatibility, signing-key ref | pinned expected publisher independent of payload; every member hashed, exact file set; adapter/app entry owned member; no mutable state or secret; size sums and limits; signature/trust/revocation valid; descriptor/profile capability supported. |
| Registry | installation id, revision, entries keyed by canonical id, state/profile, active/previous generation, release ref/digest, runtime bindings and ownership receipt | installation matches env manifest, no overlap of writable paths; installed active only if exact release and environment proven; DATA_RETAINED has no active generation; immutable refs; compare-and-swap; all generations referenced resolve or report blocked. |
| Plan | op id, install id, expected pack/runtime revisions, root fingerprint, scope, before/after generations, actions, estimated bytes, effect classes, trust/policy revisions, created/expiry, digest | exact ordered plan digest calculated excluding digest field; no arbitrary executable/action; approved scope cannot expand; stale revision/trust/policy/root -> replan; path and disk revalidate before every critical effect. |
| Adapter request | protocol, operation/phase, request and parent op IDs, installation, pack ID, generation, plan digest, scope, deadline, relative checkpoint/working paths | trusted executable from exact manifest, allowed operation by capability, validated relative paths, no arbitrary args/URLs/tokens, no callback into lifecycle; effectful calls only with matching intent and approval. |
| Adapter response | echo request/package/op/generation, status, findings, receipt with effect IDs/checkpoint/probe, bounded next action enum | verify echo/ownership/digest, no claimed approval, receipt cannot prove external effect alone; protocol errors block; stderr diagnostic only (redacted). |

Production limits: 1 MiB descriptor/registry (review against #145 1 MiB), 8 MiB manifest candidate hard ceiling with bounded max file count; wire request/response 64 KiB each, stderr capped 64 KiB; deeper inventories use hashed local sidecar file explicitly named in request and independently validated (not arbitrary paths). Default inspect/health timeout 10 s, quiesce 60 s, longer snapshot/migrate exact plan deadline and progress; finite, configurable within policy. No fabricated performance guarantees. Duplicate JSON keys reject before schema validation. Do not use stdout parser to extract a trailing JSON substring from arbitrary logs.

## 2. Lifecycle adapter and operation matrix

Minimal packages need no domain process or checkpoint adapter beyond declared immutable app install. Generic manager owns download, stage, verify file hashes, runtime, publish pointer, generic removal and cache. A package declares capability set in reviewed descriptor; absence of required capability blocks relevant operation. All adapter invocations via pinned path from manifest, argument vector, explicit working root, cleaned environment, no shell, no PATH search, no secret values in args or JSON, standard input one JSON document, standard output one response, stderr log only. Adapter package code never imported in Core. Package subprocess not a security sandbox; first-party trust only. For a new candidate adapter, verify artifact and pinned dependencies before any execution in disposable environment. Default list/status/doctor never invokes package code, inspect explicit deep only.

| Adapter op | When / effect | Required response proof |
|---|---|---|
| `probe` | explicit local preflight, read-only or approved disposable scratch | version/protocol, schema support, exact environment identity, capabilities |
| `quiesce` | close package ingress, drain bounded owned processes/jobs; no unowned process termination | owned service state, pending intent IDs, consistency receipt |
| `checkpoint` | consistent domain data under approved destination | inventory/digest, schema, omitted assets, pending intent, checkpoint token |
| `migrate` | staged candidate data only, reviewed reversible migration | old/new schema, candidate checkpoint and validation, no remote effect |
| `restore` | apply explicitly approved checkpoint to staged target | verified target data and schema, new lineage/authorization flags |
| `relocate` | fix only managed config/env/owned service paths using relative refs | path changes & proof original evidence unmodified |
| `health` | bounded candidate/local postcommit probe; no inference/spend | exact generation, executable, service/DB check status |
| `resume` | reconcile previous effect only, no fresh arbitrary operation | observed old/new/unknown; no duplicate effect |
| `stop` | verified owned processes only after drain; timeout -> blocked | process identity exit proof |

No `apply` hook that receives arbitrary deletion path; host file effects are manager-owned. Adapter plans are bounded structured requests/observations, not approval or executable workflow. Need a DB? declare checkpoint, restore, migrate, health; mutable services additionally quiesce/stop. Unknown operation or version returns UNSUPPORTED without effects. Mutation timeout after dispatch is unknown until reconciled; not ordinary retry. Process spawn and completion receipt tested separately. For public CLI managed entrypoint use same runtime selection and gate but passthrough user arguments as literal argv; business application parses its own commands and permissions. Generic launcher cannot be forced into pack-manager operations by app argv. Direct run outside managed launch unsupported.

## 3. CLI grammar (proposed)

```
engram pack list [--json]                 # catalog + local state; offline/read-only
engram pack info ID [--json]              # metadata and inventory; no provider start
engram pack doctor [ID] [--deep] [--json] # shallow offline default, explicit probe
engram pack check [ID] [--offline] [--json] # approved metadata only, no blobs
engram pack install ID --profile P [--from FILE] [--offline] [--dry-run | --apply --yes]
engram pack update [ID] [--offline] [--dry-run | --apply --yes]
engram pack repair ID [--offline] [--dry-run | --apply --yes]
engram pack remove ID [--dry-run | --apply --yes]
engram pack backup ID --to PATH [--dry-run | --apply --yes]
engram pack restore ID --from PATH [--dry-run | --apply --yes]
engram pack rollback ID [--dry-run | --apply --yes]
engram pack purge ID [--dry-run | --apply]   # separate typed confirmation + verified backup
engram pack run ID -- [args...]            # exact managed executable, no implicit install
engram repair --resume / --rollback       # existing recovery entry, extends trusted step kinds
ai [args...] / contentflow [args...]       # thin alias -> generic launch (setup delegates to pack install)
```

Defaults: new mutators without `--apply` are preview (interactive may offer exact-plan confirmation; no hidden apply); `--yes` alone does not apply, cannot waive high-risk consent. `--dry-run` + `--apply` mutually exclusive for new namespace, not change legacy flags. `check` explicitly allows metadata if network policy approved; offline not contacted, report stale/unknown. `--deep` local only, no installed adapter execution unless explicit and safe scratch effect authorized; default core doctor no inference. Unsupported combinations exit usage (2) with guidance. Alias resolution from reviewed catalog, no ad-hoc command search; for additional package generic `engram pack run ID` always sufficient, alias optional and generated from trusted metadata, never write arbitrary batch contents. `contentflow setup` / `ai setup` are compatibility delegates, preserve Rev06 AI options; all use same coordinator. Use physical `find_root` and argv quoting tests for CMD/PowerShell/Git Bash, `!%^&()`, Korean/space paths; unsupported existing path characters surface clear diagnosis, not silently claim full support.

Exit codes for **new pack CLI only** proposed: 0 success/no-op/preview; 1 failed/partial/blocked/recovery (structured outcome distinguishes); 2 parse/unsupported flag; 3 cancelled; 11 concurrent lifecycle busy; 12 recovery-required if proven consistent with existing public mapping, otherwise use 1. Child run propagates child status unchanged. Legacy exit codes (`repair`, `update`, `uninstall` etc.) remain exactly existing until explicit compatibility tests; do not reinterpret `--only packages`, `--latest`, `--json`, `--force`, existing dry-run rules. No new `pack:*` selector in P0. All pack JSON output includes version, op/result, package outcomes, findings, recovery instructions, no secrets. Preserve legacy human output for no-pack installations and golden JSON shapes. `doctor` reads marker; if installed report bounded findings without write. Optional WebUI is ContentFlow domain, not required to install pack manager.

## 4. Error codes and retry policy

Stable semantic codes: `NOT_INSTALLED`, `UNKNOWN_ID`, `CORRUPT_REGISTRY`, `FOREIGN_SLOT`, `COLLISION`, `STALE_PLAN`, `UNSUPPORTED_SCHEMA`, `TRUST_UNAVAILABLE`, `HASH_MISMATCH`, `LICENSE_BLOCKED`, `OFFLINE_ARTIFACT_MISSING`, `DISK_INSUFFICIENT`, `RUNTIME_INCOMPATIBLE`, `BUSY`, `ADAPTER_PROTOCOL`, `TIMEOUT_UNKNOWN`, `CHECKPOINT_FAILED`, `MIGRATION_UNSAFE`, `OWNERSHIP_UNPROVEN`, `RECOVERY_REQUIRED`, `POLICY_DENIED`. No automatic retries for side effects with ambiguous result. Metadata/cache downloads idempotently retry within bounded policy; checksum mismatch quarantine and no use; retry on stale plan requires replan. Child exit nonzero is not proof of no effect. Error context gives operation and package id, safe next action and receipts; redacts token/credential paths/values. Status and error are not authorization.
