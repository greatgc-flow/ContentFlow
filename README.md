# ContentFlow — Pre-TDD Design v0.3

**Design only; not implemented, installed or released.** 2026-11-28. Independent local-first content production and monetization engine; optional Engram-managed portable deployment. No niche, platform, revenue model or paid provider must be chosen before development.

## Start here

- [Integration delta and product boundary](design/INTEGRATION_DELTA.md) — current normative decisions for ContentFlow's deployment and cross-repository behavior.
- [ContentFlow domain baseline v0.1](design/contentflow-v0.1/README.md) — preserved original design, 14 documents, 90 requirements, 180 planned tests, 16 schemas and synthetic examples.
- [Engram optional package platform v0.3](design/engram-package-platform-v0.3/README.md) — preserved common-platform proposal, 36 refined requirements, 102 planned tests, eight schemas, 24 shape/semantic fixtures; includes immutable v0.2 archive (28 earlier requirements, 56 cases, and original ContentFlow v0.1 archive). Common platform is to be implemented in Engram, not here.
- [Cross-repository development gates](planning/CROSS_REPO_GATES.md), [integration acceptance scenarios](planning/INTEGRATION_ACCEPTANCE.csv), [Work/Codex handoff](planning/WORK_HANDOFF.md).

## 운영 개념

Engram에서 `engram pack install contentflow --profile lite` (future command)로 설치하고 `contentflow` CLI 또는 `contentflow studio`로 실행한다. AI 패키지가 없어도 CPU 기반 오프라인 제작이 가능해야 한다. Python/FFmpeg/Node는 검증된 호환 런타임만 공유하고 개별 앱 환경은 분리한다. 독립 실행형은 동일 도메인 코어와 별도 배포 어댑터를 사용한다. 설치나 인증, API 비용, 공개 게시를 자동 승인하지 않는다.

## Authority

The domain baseline remains normative except where this integration delta explicitly supersedes standalone host/runtime lifecycle; v0.3 supersedes v0.2's common-package clauses only. Historical documents and acceptance IDs remain immutable; historical statements about repo nonexistence or write status describe their own snapshot. Actual Engram remote contracts must be rechecked before dependent implementation. Do not import Engram private modules; share versioned wire contracts only. No dependency on AI, PeerHub or external accounts for the Lite vertical slice. All executable TDD and live/host/production acceptance remains NOT_RUN or BLOCKED. Public repository contains design, synthetic data and static audit only. License choice for future software and third-party redistribution remains open.
