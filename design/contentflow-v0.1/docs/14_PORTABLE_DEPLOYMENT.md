# 14 — Portable-first distribution and optional worker/server deployment

Status: normative proposal, not a built or tested release. Default target: Windows x64, non-administrator, supported Windows version to be confirmed in D0; Linux x64 separately packaged, not the same binary bundle. PortaKit compatibility is an optional integration, not a dependency or modification to the existing product. No driver installation, OS security policy bypass, service creation, public port, downloads, or network egress without explicit opt-in.

## 1. Orthogonal deployment modes

| Mode | Core location | Media location | Network | Target |
|---|---|---|---|---|
| PORTABLE_LITE | local ZIP, CPU | bundled FFmpeg, owned assets; manual/fixture narration | loopback only, offline | P0 required |
| PORTABLE_GPU | local ZIP | isolated optional local model packs and GPU worker | loopback or explicit API | P1 conditional |
| PORTABLE_HYBRID | local ZIP | local worker plus explicitly allowed cloud or remote renderer | allowlisted, authenticated | P2 |
| INSTALLED_LOCAL | same core, optional user-scoped launcher/service | same packs | optional | P2, not required |
| DEDICATED_WORKER | client + separately running worker | Linux/Windows GPU host | authenticated transport, no shared live DB | P2 spike |
| HOSTED_SERVER | separate service with persistent DB and tenant boundary | remote workers | TLS, authenticated | P3 separate review |

A CPU-only bundle must create projects, import sources, render simple real offline video from owned narration/visuals, export subtitles/article/manifest, analyze local metrics and back up without Python, Node, CUDA or model installs on the host. WebUI and local API use the same Core once implemented; not a prerequisite for the first TDD slice. The GPU bundle can be optional and independently updated. All operating modes use the same domain and provider ports, with explicit capability and trust-boundary checks. Lack of a capability must not silently trigger download, spend, cloud upload or a weaker QC gate.

## 2. Distribution layout and path contract

```text
ContentFlow/
  ContentFlow.cmd         # prospective zero-admin launcher; CLI args forwarded safely
  Studio.cmd              # prospective local WebUI launcher, P1
  Doctor.cmd              # prospective read-only capability probe
  runtime/                # managed per-platform runtimes; replaceable
    python/               # pinned standalone full CPython candidate
    uv/
    ffmpeg/
    node/                 # optional renderer pack only
    browser/              # optional pinned renderer browser
    envs/                 # rebuildable Python environments
  app/                    # versioned read-only application payload
  packs/                  # optional GPU/TTS/ASR/renderer packs
  wheelhouse/             # offline signed/hashed platform-specific wheels
  models/                 # separate, optional, rights-checked model cache
  config/                 # portable non-secret config, relative roots
  workspaces/             # local state, DB, CAS, exports, approvals, audit
  cache/                  # disposable per-tool cache
  logs/                   # redacted; rotation and opt-in diagnostics
  backups/                # verified snapshots; separate destination recommended
  manifests/              # signed release index, SBOM, pack manifests, lockfiles
  licenses/               # notices, build flags, source obligations
```

Root determined from launcher/executable location, not current working directory. Support root with spaces, Korean characters and drive-letter changes; never concatenate user strings into shell commands. Persistent records use logical IDs and relative artifact keys, not machine absolute paths. Resolve and validate canonical path inside designated writable root; reject traversal, links/reparse escapes, UNC/network DB paths and collisions. Explicit user-selected external model/workspace roots allowed only with preflight and separate trust declaration; export/restore maps aliases rather than silently following old absolute paths. Read-only bundle may run `doctor`/read-only inspection; writes require a separate explicitly selected local workspace. No registry edits, global PATH changes, scheduled jobs, or system services by default. OS/browser/driver/security products may retain their normal host traces; portable does not mean forensic trace-free.

Use process-scoped environment overrides for uv Python/bin/cache/project env, Hugging Face/model caches, XDG equivalents where honored, browser cache, TEMP/TMP and npm cache. Tool-specific behavior is verified via file-write observation; a variable alone is not proof of confinement. Do not set global HOME or copy OS profile; provider OAuth/keyring storage intentionally host/user-bound. Explicitly disclose and allowlist unavoidable OS writes. Store no bearer tokens, session cookies, API secrets or credential-bearing `.env` in transferable bundle or backup. Moving to a new host requires re-authentication for external operations; offline workflows continue.

## 3. Bootstrap and runtime compatibility

- Prefer pinned standalone Python distribution + bundled uv + locked wheels; choose Python 3.12 as candidate, actual supported version follows resolver/build/CI. Use an isolated runtime for ML packs; no global interpreter upgrade. Python embeddable ZIP may suit a fully vendored app but is not a standard pip-managed environment; evaluate separately. Do not mix two dependency strategies inside one env.
- Venvs are not intrinsically relocatable. Store an environment stamp (absolute resolved root, OS/arch, interpreter build ID, dependency lock hash, pack hashes). On move or mismatch, quarantine old disposable env and create fresh from local verified wheelhouse, no network; atomically select it after smoke check. If offline wheel missing, return actionable BLOCKED status, preserve all state. Avoid destructive cleanup of user directories.
- Ship pinned FFmpeg/FFprobe binary build and review distribution license, flags, matching source, notices, codecs and redistribution rights before shipping. Node and browser only when a renderer needs them; use explicit executable and browser paths, not global npm/Chrome or automatic browser downloads. WebUI can use the user's existing browser; server remains loopback-only with auth. GPU inference packs use their own dependency lock, runtime library compatibility and model license, not one giant venv.
- Host prerequisites: compatible OS/arch, system runtime libraries, writable local filesystem/space, compatible GPU driver for GPU execution. A GPU driver is host-installed; CUDA Toolkit is not universally necessary if required user-space libraries are available through supported runtime. `doctor` detects actual NVIDIA driver/VRAM, NVENC encoder listing AND small real encode/decode, model runtime import/probe, CPU instruction support, ports, disk, filesystem class, runtime hashes and privileges. Detect RTX 3060 6/8/12 GB variants rather than assume one; enforce one GPU slot initially. Probe is local and bounded; no model execution/network without permission. No automatic driver/admin install. If a required OS runtime is missing, give exact prerequisite and supported CPU/remote alternative.

## 4. Pack lifecycle, sizing, offline mode

| Pack | Contents | Rough planning size only | Required |
|---|---|---|---|
| Lite | application, Python, CPU FFmpeg, SQLite, fixture resources | 0.3–1.5 GB | yes |
| Studio | Node, renderer, browser/assets as needed | 0.5–2 GB additional | no |
| Voice/ASR | per-runtime libraries and selected models | 2–15+ GB | no |
| Image/GPU | inference libs, image model(s) | 5–30+ GB | no |
| LLM/Video | selected quantized weights/video models | 5–100+ GB | no |

Sizes are indicative engineering budgets, not downloaded or measured values. Manifest lists exact byte sizes, SHA-256, compatibility, dependencies, expected installed size, license and origin; compute available-space requirement for download + extraction + rollback + job temp + workspace reserve before install. Dedup by hash only within compatible licenses/trust domains. Pack installation explicit with preview of disk, network, license and cost; offline packs import from user-controlled file; verify signature from trusted key and each artifact hash, refuse traversal, symlink escape, decompression bomb and untrusted executable. Use versioned pack directories and atomic activation; pin job dependencies, do not change while running. Unknown provenance or license means disabled. If model not redistributable, provide instructions for separate authorized user download, not embed it. No automatic update in offline mode.

`OFFLINE_STRICT`: process network policy and explicit application capability denial; loopback WebUI permitted, external DNS/HTTP/telemetry denied; real assurance tested with network observation. `LOCAL_ONLY`: local production with separately opted-in authorized collection. `HYBRID`: explicitly approved egress with provider policy and budget. `EXPORT_ONLY` always supported. No platform publishing in offline mode. No disabling Defender, AppLocker, enterprise rules, TLS verification or sandbox to force operation.

## 5. Transfer, backup and recovery

A portable move is not live replication. `portable prepare-move` stops accepting jobs, waits/cancels bounded workers, reconciles remote-unknown intents without retry, closes DB handles, creates verified snapshot plus artifact manifest; if unknown intent remains, preserve it and require reconcile on destination. Never copy live WAL files or operate same workspace concurrently on different hosts. SQLite live DB must be on local supported storage (not SMB/NFS, OneDrive/Drive sync roots, or uncertified removable filesystem); removable SSD can be tested for local operation, otherwise USB is transfer media only and restore to local disk. A copied workspace is read-only until explicit activation with exclusive ownership and source deactivation/clone choice. Offline migration cannot prove original host is stopped: require owner attestation; disable publishing/spending after restore/clone until explicit reauthorization and reconciliation. A new project clone gets new workspace identity and no inherited side-effect authority.

On start detect interrupted installation, unexpected disconnect, stale lock, moved root, bad hash, unsupported FS, insufficient disk, stale backup or incompatible DB/pack versions. Recover from journal and verified artifacts only; no deletion of the only copy; do not overwrite backup. Backup uses SQLite backup API and consistent immutable artifact manifest with rights/retention, redaction and deletion journal. Recovery verifies checksums and migration compatibility in staging. Move credentials not portable by default. Update separately from workspace; keep previous runtime/app, stage package, take pre-migration snapshot; incompatible rollback requires restoring verified snapshot, never opening newer schema with older app. Check source authenticity and signature before executing bootstrap. For untrusted or restricted storage do not automatically execute code from a content workspace.

## 6. Separate system option

When one PC is too slow, has no driver, or needs continuous processing, retain portable CLI/WebUI as control client and move only media worker onto a dedicated machine. P2 design: authenticated TLS transport or explicitly managed trusted tunnel, capability discovery, artifact manifest/hashes, job lease/fence, deadline/cancel and bounded retries; worker never receives publish/payment credentials. No network SQLite or implicit shared filesystem. Transfer only explicitly authorized assets; sensitive projects reject unauthorized remote host. Remote artifacts verified before local commit. Worker has isolated job directory, allowlisted actions, quotas, no arbitrary remote shell, no unsolicited inbound exposure. A server deployment has different installation/network/patching/auth obligations, separate owner-approved security gates and no auto migration. Hosted SaaS P3 needs tenant isolation, Postgres/objects, legal and billing review.

## 7. Prospective commands (not implemented)

```text
contentflow doctor --offline --json
contentflow portable inspect
contentflow pack list / pack verify
contentflow pack plan --name voice-ko --offline
contentflow pack install --from FILE --offline
contentflow portable prepare-move --snapshot DEST
contentflow portable restore --from FILE --verify-only
contentflow portable restore --from FILE --activate-offline
contentflow portable repair --dry-run
contentflow portable repair --offline
contentflow worker capabilities
contentflow worker connect --profile ID  # P2, requires explicit trust
```

These commands share Core policy, structured exit codes, audit and noninteractive semantics. Verify-only and dry-run must not mutate business state. `repair` may replace disposable runtime/cache after explicit confirmation, never source projects or sole backup. First launch in offline ZIP must succeed without admin or network on supported clean host; no preinstalled Python/Node/Git assumed. GUI double click calls same doctor/bootstrap/CLI; no permanent tray service or background process by default. Shutdown terminates child workers and releases port/leases; unknown remote operations preserved.

## 8. Release gates and tests

- P0 portable Windows x64: fresh non-admin VM, no Python/Node/FFmpeg preinstalled, network denied; verify fixture to MP4/SRT/article/manifest and logs, inspect registry/PATH and filesystem changes; move C: to D: or paths with Korean/spaces; recreate env offline; repeat identical semantic output; no provider calls. Test Linux archive separately. Check actual binary dependencies and signed hashes, licenses and SBOM. Missing dependency is a clear BLOCKED, not PASS.
- P0 backup/restore: active jobs, copy interrupted, read-only/low-disk, corrupted pack/backup, old version, locks, existing target, portable SSD detach, malicious archive, stale credential, unknown publication, clone and restore. Never auto replay remote intent. Ensure no old absolute path in persisted domain data.
- P1 GPU: actual RTX 3060 with owner-confirmed driver/VRAM, missing driver, unavailable encoder, CPU fallback, OOM, pack conflict, isolation, different hosts; record timing and peak resource use. P1 Studio: port conflict, shutdown, browser cache isolation, no telemetry or public bind, no hidden downloads.
- P2 worker: invalid certificate/token, no authorization, replay/fence, disconnect, wrong hash, rejected private data, cancel, duplicate request, CPU fallback only allowed route. No host/network changes without explicit consent.

Portability acceptance is empirical on the supported clean host matrix. No claim of USB universal compatibility, old Windows/PowerShell 2.x compatibility, no-trace operation, zero administrative prerequisites across every host, actual GPU performance, actual package sizes or completed implementation. Dedicated worker/server remains optional until demand and measured workload justify it.

## 9. Structural manifests

`contracts/pack_manifest.schema.json` defines pack ID/version/platform, dependencies pinned by manifest hash, provenance, license refs/status, archive/install/scratch byte sizes, lock hash, exact member records and detached signature metadata. The trusted key is external to the package; do not trust a key supplied by the package itself. `contracts/move_manifest.schema.json` defines snapshot/instance/workspace identities, creation time, app and DB schema versions, snapshot and object hashes, deletion journal hash, unresolved remote intent IDs and mandatory non-transfer of credentials/side-effect authority. These are structural schemas only; verify actual bytes, archive authenticity and domain invariants. Both examples are test-only, and no real package is included.
