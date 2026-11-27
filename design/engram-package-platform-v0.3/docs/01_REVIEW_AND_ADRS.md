# Evidence-based review and decision register

## 1. Observed baseline and gaps

Pinned main is `61076a4734d691fe917bee562a2e2bec9c7a9148` (3.11.13). Draft PR #144 head `e7b8e21bb6baab1fbf66a6416fb0cb8083b81318`; draft #145 head `4d629e39122496986fcda4d345bcc15bb7b97ada`. Neither is merged in the observed main. #145 includes #144; do not treat these as independent branches. Local AI Rev06 `c59c0e42bb6584bc873269b7128a1c94ecba3229`; WP0 `50d3ddd19a1fed292080266c233f70e5bf52ef03`. See Sources for exact files. This is a targeted design review, not a complete source security audit. CI counts are existing reported evidence for their own scope, never new pack acceptance.

| Finding | Severity | Evidence and v0.3 response |
|---|---|---|
| F01: existing catalog != application manager | High | README, runtime/AI CLI catalogs and dispatcher cover tool provisioning; never shoehorn mutable app DBs/models into tool install manifest. Extend at lifecycle boundary, keep tool catalog intact. |
| F02: registry is not yet a generalized runtime inventory | High | #145 `python_registry.py` exact schemas, owner-specific environment path and AI-specific alternative; nonempty external/vendor/rollback refs unsupported; existing build/env records immutable, no GC. Do not write unsupported fields or invent methods. Use general `env/python-envs/<owner>/<id>` path, add reviewed typed runtime transaction port in WP2/3. |
| F03: nested lock/journal conflict | Critical | `env_ops.execute` owns lifecycle lock and active journal; #145 `publish` invokes it again. Calling it inside another env_ops step is invalid. Factor pure prepare/validation and journaled steps, one outer transaction; test recovery and nested refusal. |
| F04: path root may be renamed | High | `core/root.py` resolves physical system root, not fixed directory name. Persist sys-relative paths; `_sys` is default presentation only. Reject case collisions, foreign roots, unsafe paths, reparse points. |
| F05: packaging allowlist is insufficient for new mutable subtrees | Critical | `tools/winget/build_package.py:112–200` recursively collects system files using exclusion sets. New `models`, `workspaces`, configs or venv content can accidentally enter a release. Exclude each managed slot and entire mutable runtime/state trees before traversal; include only reviewed static descriptor/wrapper source in core release. Synthetic canary secrets/media/models in both slots and future slot, no disclosure. |
| F06: uninstall requires a precise correction | Critical | `core/uninstaller.py:35–55,103–155` deletes named program entries including `data`/`env`, preserves unknown top-level slots, `.engram`, workspace by default. Previous description of unconditional whole `_sys` deletion was too broad. Do not add whole AI/CF slots to removal allowlist. Before deleting shared metadata/runtime, drain owned packs and export self-contained recovery metadata/data to verified preserved location or refuse. Keep external references and unowned bytes untouched. |
| F07: detached updater overlays stage | Critical | `core_update_helper.ps1` enumerates and copies staged files, restores backed-up targets on error. Candidate must exclude all pack-owned files; transaction across helper and Python is not automatically safe. Durable parent handoff and candidate version/protocol revalidation; old updater must not activate incompatible schema. |
| F08: legacy CLI flags already have meaning | High | `updater.py` parses `--only python/venv/packages`, restricts `--json`, `--latest`; maintain old outputs and selectors. Introduce `pack` namespace, no `--only pack:*` until compatibility extension proven. |
| F09: OS process identity not equal to app health or security | High | `env_lock` process/start-time guards mutation; no generic security sandbox. Distinguish local service liveness, receipt, generation, policy. No forced kill of PID/name, no process-global secrets. |
| F10: GPU sharing not yet implemented or qualified | High | WP0 partial for AI provider/PG/64K; successful Windows CPython probes do not prove GPU. Start with shared cooperative exclusive lease, not an always-on broker. |
| F11: nested package management could duplicate domain rules | High | CF v0.1 own pack/portable functions vs Engram v0.2 coordinator. One authority for host/runtime/app install; internal content assets/workspace backup stay domain-owned and must compose with host operations. |
| F12: bare schema is not admission | Critical | v0.2 example descriptor accepts semantically inconsistent IDs/slots/profiles/dependencies. Add strict structure + semantic validator + separate trusted release manifest and installed registry, pre-authorized publisher keys, no execution from catalog. |
| F13: rollback must respect app schema | Critical | An app generation pointer cannot reverse DB migration or undo a publish; retain old DB snapshot, migration compatibility, irreversible consent and reconcile unknown effects. |
| F14: older Engram can bypass new guards | Critical | Prior binaries do not understand pack registry; release gate requires downgrade/old updater compatibility tests. Never claim old executable enforces new guarantees; refuse unsupported manager downgrade and document manual use of obsolete binary as unsupported. |

## 2. Decisions (proposed unless explicitly user-approved)

| ADR | Decision | Alternative rejected / reopen condition |
|---|---|---|
| EPP-ADR-01 | Engram owns host/installation lifecycle; AI/CF domain code owns domain state. Existing tool catalog and PeerHub independent. | Separate pack manager repo or giant suite. Revisit if independently reusable contract proven by external host. |
| EPP-ADR-02 | One new repo `greatgc-flow/ContentFlow`, preferably private/empty; release artifacts consumed by Engram. | Monorepo or submodule coupling. No repo creation or upload implied. |
| EPP-ADR-03 | Canonical lowercase IDs; `AI`, `ContentFlow` are reviewed sys-relative compatibility slots; future `packages/<id>`. One naming policy, trusted slot mapping. | Renaming existing AI or arbitrary `slot` provided by remote. |
| EPP-ADR-04 | Core ships descriptors and generic launcher only; install application artifacts explicitly. Preserve base lightweight. | Bundle full AI/CF into Engram, download at first launch, import plugins in Core. |
| EPP-ADR-05 | First-party reviewed catalog, artifact trust roots separate from payload, explicit offline import of approved artifacts. | Public marketplace, transitive untrusted plugins, script URLs. |
| EPP-ADR-06 | One mutation gate/journal owner, existing env_ops where capable; no nested `publish` or duplicate lock. | Per-package independent install journals in Core. |
| EPP-ADR-07 | Immutable app/env/artifact generations, explicit pointer, previous generation & verified data checkpoint. | In-place overwrite, universal snapshot rollback. |
| EPP-ADR-08 | Share exact compatible binary identities only, separate environments/data. | Shared venv, blind latest, model store symlink sharing. |
| EPP-ADR-09 | No pack hard-dep in P0 (profiles depend on capabilities). DAG contract allows future dependencies after proof. | Arbitrary package solver/auto-install dependencies. |
| EPP-ADR-10 | `engram pack` management; package CLI direct; preserve legacy flags and result format. | Reuse `--only packages` or add new root CMD/EXE. |
| EPP-ADR-11 | Package-specific trusted subprocess adapter only for domain-specific lifecycle; generic acquire/stage/remove in manager. | 13 mandatory hooks per trivial pack; all hooks optional except required capability with checked contract. |
| EPP-ADR-12 | Generic direct exec for versioned entrypoint and stdio JSON lifecycle; no arbitrary shell. | Import vendor libraries, external scripts, hook PATH lookup. |
| EPP-ADR-13 | Installed state distinct from health, catalog, retained data and operation. | Treat folder existence as install/permission. |
| EPP-ADR-14 | Existing `reset` scope unchanged; preserve data on removal; explicit separate verified external export/purge before whole uninstall when needed. | Delete entire slot; pretend data inside deleted path survived. |
| EPP-ADR-15 | Move same identity only with source deactivation proof/attestation; copy/restore fenced, fresh identity for clone, no external authority. | Active shared DB/live directory sync. |
| EPP-ADR-16 | Common GPU lease P1; no persistent new scheduler, per managed OS session/installation admission first, host-wide shared namespace only after validation. | Claim full cross-host scheduling or control external jobs. |
| EPP-ADR-17 | Core `doctor` read-only and no pack code execution on default; deep local probe separately explicit. | Run inference or vendor self-updater during inspect. |
| EPP-ADR-18 | P0 supported Windows x64 local NTFS, standard user; independent CF domain can support Linux later. | Universal filesystem/OS promise. |
| EPP-ADR-19 | Scope security enforced at application/OS boundary, not merely process env. `OFFLINE_STRICT` only claim after effective egress proof. | Claim plugin subprocess is sandbox or no-network by naming. |
| EPP-ADR-20 | Stop before production test-code writing. Preserve original IDs/status, append crosswalk and new focused cases. | Synthetic counts or self-rating as production proof. |

## 3. Open decisions / stop gates

- O1: upstream runtime artifact pins, trust/signature bootstrap, revocation and offline root freshness; no production artifact until verified source, compatibility, license and release approval. Candidate trust chain uses reviewed first-party pinned key + signed canonical manifest; cryptographic implementation and key custody require separate WP0 proof/owner choice. Fixture SHA does not authenticate anyone.
- O2: exact final WP1/2/3 interfaces and `env_ops` recovery API, nested ownership, registry schema evolution and old journal behavior. #145 is not a stable port. No production pack transaction until coordinated proof.
- O3: detached update and whole uninstall helper support for retained metadata and external checkpoint; previous updater and legacy installer upgrade/downgrade gates. If unsupported keep pack mutations explicitly separate and block unsafe global operations, not silently report success.
- O4: ContentFlow CPU renderer and distributable FFmpeg build, Node/browser lock, GPU pack native deps/model license; no redistribution until approved. Actual RTX 3060/target Windows test pending. AI WP0 blockers remain.
- O5: OS-level no-network/effective plugin containment and host-wide resource lease across multiple installations/users; P0 trusted first-party code only; no auto service/egress or unauthorized spend. Multi-user GPU fairness and arbitrary plugin execution deferred.
- O6: repository release visibility and signing key management; private repo recommended until rights/security review. No paid publishing/hosting setup now.
