# ContentFlow — pre-TDD design baseline

**Status:** v0.1.0-design · 2026-11-28 · Proposed, not implemented or released.

ContentFlow is a local-first, evidence-driven content production and monetization engine. The owner has not selected a niche or business model; this baseline deliberately preserves options rather than building every provider now. It is an independent application; Engram and PeerHub are optional ports, not prerequisites.

## 시작하기 (한국어)

- 아직 어떤 콘텐츠를 만들거나 어떤 수익모델을 사용할지 결정할 필요가 없다. `docs/01_PRODUCT.md`의 프로필을 바꾸면 된다.
- 첫 구현은 **가짜 데이터·가짜 공급자 → 검증된 로컬 영상 → 내보내기** 순서다. 실제 API 과금, 계정 연결, 공개 게시, 결제 연동은 기본 금지한다.
- Python 코어, SQLite, 콘텐츠 주소화 파일 저장소, FFmpeg/Remotion 후보를 사용한다. RTX 3060은 실제 VRAM·드라이버 검사 후 사용한다. WebUI, REST, MCP는 동일 유스케이스를 호출한다.
- 포터블 우선: 관리자 권한 없는 Windows ZIP + CPU Lite, 선택형 Studio/GPU 모델팩. 호스트 GPU 드라이버는 별도 전제이며, 별도 서버는 필요할 때만 도입한다. 이동/재설치 시 DB와 콘텐츠를 보존하고 가상환경을 오프라인 재구성한다.
- `planning/REQUIREMENTS.csv`와 `planning/TEST_CATALOG.csv`가 요구사항 및 테스트의 SSOT다. 실제 테스트 코드는 아직 작성하지 않았다.
- `planning/TDD_HANDOFF.md`를 새 Work/CLI 세션에 전달하면 시작할 수 있다. 기존 저장소의 브랜치 변경·병합·배포·API 사용은 하지 않았다.
- 정책과 라이선스는 가변적이다. `docs/09_COMPLIANCE.md`, `docs/12_REFERENCES.md`와 계정별 현재 상태를 먼저 확인한다.

## Reading order

| File | Purpose |
|---|---|
| [01_PRODUCT](docs/01_PRODUCT.md) | Vision, scope, monetization and channel experiment profiles |
| [02_ARCHITECTURE](docs/02_ARCHITECTURE.md) | Boundaries, deployment, workflow engine, data lifecycle |
| [03_RESEARCH_STUDIO](docs/03_RESEARCH_STUDIO.md) | Collection, claims, editorial planning, originality |
| [04_MEDIA](docs/04_MEDIA.md) | TTS, visuals, rendering, local GPU, media QC |
| [05_INTERFACES](docs/05_INTERFACES.md) | CLI, REST, WebUI, MCP, provider ports |
| [06_DISTRIBUTION](docs/06_DISTRIBUTION.md) | Export, platform capabilities, consent, exactly-once limitations |
| [07_BUSINESS](docs/07_BUSINESS.md) | Revenue models, analytics, attribution, unit economics |
| [08_OPERATIONS](docs/08_OPERATIONS.md) | Budgets, security, recovery, observability, release |
| [09_COMPLIANCE](docs/09_COMPLIANCE.md) | Source/asset rights, platform policies, review gates |
| [10_ADRS_AND_EVALUATION](docs/10_ADRS_AND_EVALUATION.md) | Build vs adopt, integration and PoC decision matrix |
| [11_DELIVERY](docs/11_DELIVERY.md) | Phases, quality gates, readiness, owner decisions |
| [12_REFERENCES](docs/12_REFERENCES.md) | Official source registry and evidence status |
| [13_SCENARIOS](docs/13_SCENARIOS.md) | End-to-end and failure scenarios |
| [14_PORTABLE_DEPLOYMENT](docs/14_PORTABLE_DEPLOYMENT.md) | Portable-first Windows/Linux, runtime packs, move/restore, optional worker/server |
| `contracts/*.schema.json` | Proposed JSON Schema contracts (not implementation) |
| `examples/` | Offline synthetic fixtures, configuration and workflow |
| `planning/REQUIREMENTS.csv` | Normative, numbered requirements |
| `planning/TEST_CATALOG.csv` | Planned tests with Given/When/Then and requirements mapping |
| [TDD_HANDOFF](planning/TDD_HANDOFF.md) | Implementation order and restart prompt |
| [DESIGN_REVIEW](planning/DESIGN_REVIEW.md) | Static consistency checks, gaps and conditions |

Precedence: this baseline's requirements and contracts > individual design narrative > illustrative examples. Conflicts must be recorded and resolved, not silently patched. Current platform/legal/provider terms override proposed behavior; unsafe or unverified capabilities stay disabled. No credentials, private data, production code, live tests, or media are included.
