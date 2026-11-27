# 04 — Media factory and local GPU design

## 1. Render pipeline

Plan assets → authorize provider and estimate spend → create/import → inspect metadata → record rights/lineage → normalize audio and visuals → align narration and captions → build timeline → render preview/final → inspect QC → package. Assets immutable, file path never executable input. Fail closed on missing rights, scene references, corrupt media, or mismatched claims. A deterministic scene composition (text/chart/SVG/screenshot/owned media) is default; generative video is optional B-roll, not required. Keep originals and derived formats with permission-based retention. Source captions and branded music licenses might not transfer across platforms.

| Capability | P0 | P1/P2 candidates |
|---|---|---|
| Text/visual | template SVG/PNG, synthetic chart, owned asset | Remotion, SDXL/ComfyUI, authorized stock |
| Voice | deterministic synthetic tone fixture for unit tests, user-provided WAV for real offline E2E | Qwen3-TTS, licensed cloud TTS, human voice |
| Captions | deterministic alignment fixture, SRT | faster-whisper, forced alignment, ASS |
| Motion | FFmpeg compose existing assets | Remotion React scene renderer, optional generated clips |
| Recording | import owned clips | OBS/Playwright for authorized demos |
| Video | FFmpeg/ffprobe subprocess | approved render API, image-to-video, Veo/Runway etc |

User-provided or redistributable licensed narration required for pilot; fixture tone is never publishable. TTS voice ownership/permission and commercial terms recorded. No unauthorized voice cloning; consent covers speaker, use, scope, revocation. Music/SFX disabled initially, captions generated from actual narration; audio mix measures loudness. Stock adapter captures asset ID, attribution, license version and terms applicable to output/channel. No presumed commercial rights for any arbitrary model checkpoint.

## 2. Timeline contract and export

Use integer milliseconds for logical timeline; derive integer frames at rational FPS, decide rounding deterministically. Every scene [start,end) positive and bounded; overlap only explicit transition. Each referenced artifact hash validated before render. Captions have ordered start/end, no negative times, no beyond duration, max lines and characters configured per locale; Unicode grapheme-safe splitting, Korean fonts verified for glyphs, avoid safe-area collisions. Scene bundle passed via JSON plus read-only assets in isolated worker. FFmpeg argument list validated; filter templates fixed, user text escaped as data or rendered to image. Remotion is renderer candidate, not a dependency of Core. Pin npm lock, Chromium and fonts; network off while rendering; do not fetch remote scripts from arbitrary templates. Decode output fully for QC or use documented sampled probe plus full decode for release.

Internal output defaults: MP4 H.264 + AAC, yuv420p, 30 fps, 1080x1920 or 1920x1080, 48 kHz audio, faststart; encoder selection based on installed capability and distribution rights. User can select 720p preview and lower CPU load. No AV1 encode assumption for RTX 3060. Container defaults are house standards, not platform requirements. Default peak <= -1 dBTP, integrated loudness target -14 LUFS ±2 for narrated content, silence and black-frame thresholds configurable with exemptions. Technical QC: codec, dimensions, frame rate, duration tolerance <= one frame or codec padding tolerance documented, non-empty audio when required, caption sync sample, no unexpected silence, corrupted/blank frames, clipping, subtitle bounds, thumbnail validity, no restricted placeholder. Editorial QC: pronunciation of names/numbers, narrative comprehension, pacing, visual truthfulness, accessibility and consistency; human approval required. Never auto-approve merely because technical checks pass.

## 3. Hardware profiles

Discover `nvidia-smi` and FFmpeg encoders/decoders, VRAM total/free, driver, CUDA/cuDNN and CPU RAM/disk. RTX 3060 can be 6/8/12 GB variants; do not assume owner VRAM. P0 CPU-safe, P1 one GPU worker lease, default concurrency 1 for model inference, unload/stop child after task. Select small model and batch 1; probe actual peak VRAM; reserve headroom for display/system. If insufficient, use approved CPU/smaller model fallback or WAITING_REVIEW; never cloud fallback without consent. CUDA compatibility pinned per worker env; Qwen3-TTS Korean and faster-whisper candidates, no claimed measured compatibility. WSL2 and native separately benchmarked; do not install drivers or models without approval.

GPU OOM: cancel subprocess, release lease, verify memory reclaim; one bounded attempt with approved smaller profile then fail with actionable diagnostic. CPU fallback must meet time/budget limit, not infinite wait. GPU reset/driver loss requeues idempotent local step after health recovery. Use local queue, preflight estimated free disk and temp limit; clean only owned temporary files; preserve approved assets. Keep output frames cache size bounded.

### Benchmark plan (NOT RUN)

On actual hardware: 15/60/90 s vertical and 8 min horizontal, ko/en captions, cold/warm model; CPU and optional GPU paths. Record exact GPU, RAM, driver, OS, dependency versions, peak VRAM/RAM, wall time, real-time factor, energy estimate/meter if available, quality pass/fail, cost, OOM. Test 6GB/8GB/12GB only if available, otherwise label unavailable; CPU path mandatory. Initial engineering target 60s template video under 5 min on owner's machine (not a guarantee); adjust from measurements before setting SLO. Compare TTS intelligibility on a consented Korean test script, at least two human ratings when feasible; ASR error rate and latency for target locale. Render repeatability compares decoded frame/audio invariants; bitwise MP4 identity not guaranteed across encoders.

## 4. Media generation alternatives

Cloud/Web manual export: user imports asset with license/provider metadata, paid generation not automatically invoked. Cloud API: estimate per unit, reserve hard upper bound incl retry, poll status, uncertain bill remains reserved until reconciliation. Store request ID and model/version, no API keys in manifests. Local model: verify weights/license, downloaded checksum, no network in inference, no remote code trust by default. HTML/React templates sandbox and reviewed; no arbitrary JS in content source. B-roll quota default zero. Long-form to short uses timecodes on own/authorized video, tests context and captions, no copyrighted arbitrary clip extraction.
