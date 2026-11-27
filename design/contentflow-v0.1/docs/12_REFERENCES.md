# 12 — Reference registry and verification limits

Review date: 2026-11-28 KST. Official pages and project manifests are evidence for design constraints, not a permission token, audited code review, account-specific eligibility, or measured performance. Recheck on activation, record exact version/dates/evidence, and use the stricter allowed behavior. No full source copies included. V = directly checked in this design continuation; C = candidate/previous research, not independently reverified here; B = retrieval blocked/changed. All C/B external adapters disabled pending verification.

| ID | Reference | Status | Design use |
|---|---|---|---|
| R01 | [YPP changes](https://support.google.com/youtube/answer/12843009?hl=en) | V | 2027-02-01 thresholds for new entrants; activity, terms and Shorts maintenance separate |
| R02 | [Shorts monetization](https://support.google.com/youtube/answer/12504220) | V | future 10M maintenance; qualified-view timing, eligibility not public views |
| R03 | [Channel monetization policy](https://support.google.com/youtube/answer/1311392) | V | originality, inauthentic/reused content |
| R04 | [GenAI disclosure](https://support.google.com/youtube/answer/14328491) | V | realistic alteration/synthesis and relevant audio/music cases |
| R05 | [YouTube API revision history](https://developers.google.com/youtube/data/revision_history) | V | 2026-11-02 unverified-project upload reversal; explicit privacy; 2026-11-16 paid placement and co-view changes |
| R06 | [videos.insert](https://developers.google.com/youtube/v3/docs/videos/insert) | C | exact current API fields, scopes, quota; verify before enabling |
| R07 | [Analytics metrics](https://developers.google.com/youtube/analytics/metrics) | V | metric definitions, estimates |
| R08 | [YouTube developer policies](https://developers.google.com/youtube/terms/developer-policies) | V | consent, scope, refresh/deletion, aggregation/download limitations |
| R09 | [TikTok posting guidelines](https://developers.tiktok.com/doc/content-posting-api-guidelines/) | B | prior research indicated self-use restrictions; default disabled, verify official current text before even proposing adapter |
| R10 | [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo), [pyproject](https://github.com/harry0703/MoneyPrinterTurbo/blob/main/pyproject.toml) | V | candidate, MIT manifest; no run or dependency audit |
| R11 | [Short Video Maker](https://github.com/gyoridavid/short-video-maker) | V | public README and manifest, limitations; no run |
| R12 | [Remotion license](https://www.remotion.dev/docs/license) | V | licensing/telemetry/billing review before sidecar |
| R13 | [n8n docs](https://docs.n8n.io/) | B | previous sustainable-use URL redirected to not-found; locate current license before use |
| R14 | [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) | V | Apache-2.0 source repository; verify weights, voices and compatibility |
| R15 | [Meta developer docs](https://developers.facebook.com/docs/) | C | Instagram/Facebook capabilities require live review |
| R16 | [FFmpeg legal](https://ffmpeg.org/legal.html) | C | verify exact binary build flags/distribution terms |
| R17 | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | C | optional local ASR; verify CTranslate2/CUDA requirements |
| R18 | [Wan2.2](https://github.com/Wan-Video/Wan2.2) | C | high VRAM candidate, no promise on RTX 3060 |
| R19 | [Trafilatura](https://github.com/adbar/trafilatura), [Naver developer docs](https://developers.naver.com/docs/) | C | authorized collection candidates; rate and data terms dynamic |
| R20 | [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785) | C | canonical JSON specification to pin/verify in D0 |
| R21 | [JSON Schema 2020-12](https://json-schema.org/draft/2020-12) | C | schema draft used for proposed contracts |
| R22 | [국세청](https://www.nts.go.kr/), [공정거래위원회](https://www.ftc.go.kr/) | C | local business registration/advertising disclosure review; not legal conclusion |
| R23 | [GitHub REST API](https://docs.github.com/en/rest), [공공데이터포털](https://www.data.go.kr/) | C | permitted research sources, check individual license |
| R24 | [OpenAI API docs](https://platform.openai.com/docs), [Anthropic docs](https://platform.claude.com/docs), [Gemini API](https://ai.google.dev/gemini-api/docs) | C | provider candidates, verify current price/terms/CLI entitlement separately |
| R25 | [ComfyUI](https://github.com/comfyanonymous/ComfyUI) | C | optional image adapter, verify nodes/weights, no arbitrary plugins |

## Dated policy example

Current official R01/R02 state that new ads/Premium YPP entry thresholds rise to 8,000 qualified watch hours in 365 days or 20M qualified Shorts views in 90 days from 2027-02-01, with 1,000 subscribers; existing status and fan-funding have different rules. Shorts Creator Pool/Premium maintenance 10M qualified Shorts views over 90 days, measured on a defined prior-month window. Updated YPP modules and activity thresholds must be checked individually. R05 notes privacy default may be public, so never rely on default in any real upload. Do not implement these as unversioned constants or a promise of approval. Keep provider rule fixture explicitly synthetic and not valid for live account.

## Portable runtime references (checked in the continuation)

| ID | Reference | Status | Use |
|---|---|---|---|
| R26 | [Python Windows embeddable distribution](https://docs.python.org/3/using/windows.html) | V | isolated but not standard pip-managed |
| R27 | [uv storage paths](https://docs.astral.sh/uv/reference/storage/) | V | process-scoped runtime and cache roots |
| R28 | [Python venv](https://docs.python.org/3/library/venv.html) | V | absolute paths, recreate after move |
| R29 | [Playwright browsers](https://playwright.dev/docs/browsers) | V | local browser location; renderer-specific verification still required |
| R30 | [NVIDIA CUDA Windows installation](https://docs.nvidia.com/cuda/cuda-installation-guide-microsoft-windows/index.html) | V | host driver vs toolkit/runtime |
| R31 | [SQLite WAL](https://sqlite.org/wal.html) | V | local host filesystem |
| R32 | [FFmpeg legal](https://ffmpeg.org/legal.html) | V | exact binary flags/source/license obligations; no particular build approved |
