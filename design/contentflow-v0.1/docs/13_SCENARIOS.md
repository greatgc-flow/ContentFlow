# 13 — End-to-end and exception scenario matrix

Each scenario is planned; none is a claim of implemented functionality. Test catalog is normative for specific assertions. All real side effects require separate owner authorization. Profiles and scenarios combine orthogonally rather than one class per platform.

| Scenario | Inputs and route | Expected evidence / disposition |
|---|---|---|
| S01 offline educational short | synthetic data, authored narration fixture, chart + claim + script + FFmpeg | playable local MP4, SRT, article, hash manifest; TEST_ONLY, zero spend/network |
| S02 no niche chosen | create TECH/DATA/EDUCATION profiles | independent settings and no provider obligations |
| S03 public data explainer | authorized dataset + calculation + uncertainty | recomputable numbers and cited chart; no claims of causality |
| S04 owned long video to short | owner-provided clip + transcript | context preserved, captions bounded, original rights inherited |
| S05 multilingual | approved original brief, ko/en variants | facts/units invariant; separate revision and review |
| S06 newsletter/article only | evidence pack → Markdown | no GPU/TTS requirement; disclosure and CTA carried |
| S07 enterprise private training | confidential manual → private local export | no egress or fallback, restricted workspace |
| S08 manual media import | user-produced/licensed image/narration | rights scoped, unknown rights block release |
| S09 external API plan | fresh known bound + explicit spend approval | transactional reserve, receipt, settle; fake only initially |
| S10 concurrent budget | two jobs exceed remaining cap together | at most one allowed, second waits |
| S11 uncertain billed request | provider accepts then timeout | UNKNOWN reservation held, reconcile; no retry |
| S12 source correction | updated statement or license revocation | impacted claims stale, approval invalid, published review queue |
| S13 near-duplicate output | multiple similar scripts | similarity warning + editorial review, no mass publication |
| S14 hostile input | source prompt injection, SSRF, malicious archive | reject/contain; no privilege escalation |
| S15 partial scan | mixed text/image PDF from allowed importer | incomplete coverage visible, OCR not silently assumed |
| S16 render interrupted | kill worker after object write/before DB or lease loss | reconcile orphan, fence stale worker, resume valid steps |
| S17 GPU unavailable | OOM/driver loss/missing driver | approved smaller/CPU fallback or wait; no cloud spend |
| S18 disk corruption | bad hash/disk full, backup restore | no corrupt export, recover verified state or stop |
| S19 dry run | CLI or REST planning, no credentials | no business state mutation or network/reservation |
| S20 stale approval | edit title/asset, policy expires after approval | block submit, show new digest |
| S21 manual publication | export-only, user uploads separately | optional attested receipt distinct from API verification |
| S22 approved private API pilot | supported official platform, explicit owner action | verified privacy + remote ID, only if approved; otherwise NOT_RUN |
| S23 remote publication timeout | request sent, no response | REMOTE_UNKNOWN, no duplicate; safe lookup or owner reconcile |
| S24 platform processing fails | upload accepted, processing rejects | render stays valid, publication FAILED, no success shown |
| S25 unsupported posting | TikTok self-use/unknown API/Naver unknown | export-only, no browser bypass |
| S26 revoke auth | provider account disconnected | prevent use, retention purge/refresh obligations |
| S27 public correction | source/asset complaint after posting | freeze reuse, queue separate approved action and verify receipt |
| S28 revenue estimate | different platform RPM and metrics | estimated not actual, unknown vs zero, units explicit |
| S29 refunds and payout | duplicate/corrected statement, fees/payouts | no double count, reconcile ledger and currency |
| S30 experiment | content → CTA → authorized aggregate conversion | observed not causal by default; no fingerprinting |
| S31 restart with no Engram/PeerHub | optional integrations absent | offline core works; clear capability unavailable |
| S32 SaaS future | simulated tenant/payment webhook | no live billing; separate readiness gate and tenant auth |
| S33 local WebUI | user previews then modifies script | revision conflict, stale approval, keyboard-accessible confirmation |
| S34 provider fallback | exhausted quota, unavailable preferred local provider | only allowed explicit fallback; unknown/costly routes blocked |
| S35 schedule | local timezone/DST, job delayed, rule expired | correct UTC, no late/stale automatic publish |
| S36 archive/purge | backup restored after deletion | deletion journal reapplied, no resurrected restricted data |
| S37 provider model license change | updated weights terms | old snapshot traceable, new jobs blocked until review |
| S38 manual web handoff | web-only AI/creator service | export prompt + assets + consent checklist; import result with provenance |
| S39 accessibility | ko-KR text and captions on vertical canvas | safe-area, clipping and font/glyph review; transcript alternative |
| S40 multiple revenue routes | ads+affiliate+product+SaaS scenario | eligibility per route, attribution and financial evidence distinct |

## Horizontal coverage

For each workflow, cover normal input, empty/missing, malformed/oversized, duplicate, stale, unauthorized, dependency outage, timeout/cancel, crash/restart, conflict/concurrency and unsupported feature. For each side effect, test intent persistence, exact approval, budget, post-send ambiguity, reconciliation, and no duplicate. For each artifact, cover version/hash, lineage, rights, expiration, retention and downstream invalidation. Matrix is a designed partition, not proof of exhaustive real-world behavior. Add provider-specific cases only after official capabilities and actual implementation are known.

## Portable extensions

| Scenario | Inputs and route | Expected evidence / disposition |
|---|---|---|
| S41 clean host | ZIP on supported Windows x64, standard user, offline | Lite fixture real export; no global install |
| S42 moved root | drive/path changes, locked local wheels | rebuilt environment, same project/artifact identities |
| S43 GPU unavailable | missing driver or incompatible runtime | explicit CPU path or BLOCKED, no external API |
| S44 interrupted pack | partial extraction, bad signature, disk full | previous active pack intact; no execution |
| S45 portable restore | verified snapshot, new host, old OAuth and unknown intent | reauth, no replay, restore read-only/explicit offline activate |
| S46 unsupported storage | network/synced DB root, USB eject | reject or verified recovery on local storage |
| S47 remote media worker | permitted local-to-worker transfer or forbidden private data | authenticated, scoped, verified artifact or deny |
| S48 update rollback | schema changed then release fails | verified pre-update snapshot; no destructive downgrade |
| S49 Studio | browser/port missing, shutdown | actionable diagnostics; local-only bind; no global install |
