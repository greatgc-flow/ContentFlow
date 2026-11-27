# Engram Optional Package Platform — Pre-TDD revision 0.3

2026-11-28 KST | Design amendment, not executable software | English normative specification, Korean operator summary.

## 목적 / 읽는 순서

Engram의 AI 설계를 일반화하되 기존 portable dev 환경을 비대하게 만들지 않는다. ContentFlow는 독립 저장소/릴리스, Engram에서는 선택형 패키지. AI 설치가 ContentFlow의 전제조건이 아니다. 향후 세 번째 패키지의 설치·갱신·삭제·복구를 Core 제품별 분기 없이 검증한다. 현재 진행 중인 PR #144/#145를 대체하거나 병합하지 않는다.

- [Review and decisions](docs/01_REVIEW_AND_ADRS.md): 실제 코드/브랜치와 v0.2의 설계 차이, 설계 결정, 미해결 사항.
- [Architecture and layout](docs/02_ARCHITECTURE.md): 최소 공통 계층, 루트/권한/상태, registry/runtime boundaries.
- [Lifecycle and recovery](docs/03_LIFECYCLE.md): plan, stage, transaction, fault recovery, coordinated backup, remove, update.
- [Contracts and CLI](docs/04_CONTRACTS.md): precise descriptor/release/registry/plan/adapter wire contracts and CLI semantics.
- [Security and portability](docs/05_SECURITY_PORTABILITY.md): release, path and archive admission, ownership, GPU/credential/host boundary.
- [Integration and delivery](docs/06_INTEGRATION.md): AI/ContentFlow/third-pack integration, repo and PR strategy, vertical slice and release gates.
- [TDD plan](planning/TDD_PLAN.md), [requirements](planning/REQUIREMENTS.csv), [test catalog](planning/TEST_CATALOG.csv), [crosswalk](planning/BASELINE_CROSSWALK.csv), [risk register](planning/RISKS.csv), [handoff](planning/WORK_HANDOFF.md).
- `contracts/` and `fixtures/`: strict test-only structural contracts. No executable hooks, production keys, actual artifacts or authorization. Static schema validation is distinct from semantic and native tests.
- [Sources](planning/SOURCES.md), [static audit](planning/STATIC_AUDIT.md), `SHA256SUMS.txt`.
- `baseline/Engram_ContentFlow_Pack_Design_v0.2.zip`: unchanged historical archive; includes original ContentFlow v0.1.0. It preserves the original 118 design requirements and 236 test specifications; the present delta refines those, not a claim of independently additive coverage.

## Authority and stop line

1. User-approved direction: optional packages on Engram, portable first; preserve existing AI capabilities. Existing behavior on pinned main is the baseline. New remote facts must be rechecked before RED.
2. Rev06 and v0.2 remain immutable. For package management/integration only, explicit v0.3 decisions supersede conflicts; all domain, data and permission safeguards remain. A failed proof blocks the dependent feature, not the independent core or other pack.
3. PR #144/#145 are draft changes, not merged interfaces. Follow their eventual reviewed contracts. Use no real user data, provider credits or production system changes during TDD. No repo writes, main merges, installation, provider calls, or production RED/GREEN tests were performed in this revision.
4. Design choices (e.g. first-party trust, CLI naming, generation IDs, bounded resource protocol) are proposed defaults, not existing code. No new repository is required for the package manager; recommend one empty private ContentFlow repo for domain development. All native feasibility, cryptographic production trust, actual implementation and release gates remain NOT_RUN or BLOCKED.
