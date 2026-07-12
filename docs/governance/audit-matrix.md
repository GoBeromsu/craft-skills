# craft-skills 감사 매트릭스 (20 skills × 9 fields)

수집: read-only subagent 4군 병렬 감사(2026-07-12) + 정합 재감사(신규 api·cicd·write-prd 3종, 변경 5종 재검증; 2026-07-12).
근거 문서: [omo 분석](../research/omo-analysis.md) · 스펙: deep-interview-craft-skills-omo-enhancement (fact-6/12/13은 IR-1로 superseded).
검증: `python3 scripts/governance/tools/audit_matrix_lint.py docs/governance/audit-matrix.md --rows 20`

처분 요약: change 19 / no-change 1 → 리배칭 k=ceil(19/5)=4 PR (5+5+5+4, 매트릭스 행 순서).

CI 참고: GitHub Actions는 계정 billing lock으로 모든 잡이 미기동 상태("account is locked due to a billing issue") — 코드 결함 아님, 운영자 결제 액션 필요. 게이트 증거는 로컬 실행으로 대체 기록.

| skill | 계약준수 | 과잉지시 | 라우팅겹침 | 가이드정합 | 원칙반영도 | Layer-1 | 처분 | 증거링크 |
|---|---|---|---|---|---|---|---|---|
| skillify | pass | high — stash 강제(운영자 상태 변형), branch→PR 규칙 5회 중복 | possible — distil/hookify 경계 흐림 | partial | med — 원자 커밋·root-cause 미명시 | pass | change | skills/skillify/SKILL.md:73-74,91-122; skills/skillify/references/lifecycle.md:14-26 |
| distil | pass | med — no-execute 불변조건 4회 중복, `&`/`$` denylist가 유효 URL 오거부 | possible — skillify/research 인접 | partial | med — 행동 검증·원자 커밋 위임만 | pass | change | skills/distil/SKILL.md:18-30,93-111 |
| research | pass | med — 인용 규칙 5개 섹션 중복, 검증이 인용 존재로 한정 | possible — document/distil 인접 | partial | med — 반증 탐색·모순 프로토콜 부재 | pass | change | skills/research/SKILL.md:43-50 |
| programming | pass | high — 전 참조 로드 강제, 모든 라인 red-first, 250 LOC 절대규칙 | likely — refactor와 smell 리뷰 중복 | partial | high — 원자 커밋만 누락 | pass | change | skills/programming/SKILL.md:14-21,52-62,72-76 |
| testing | pass | med — 계층별 커버리지 quota, 파일명 스캔 과신 | possible — programming TDD 경계 | partial | med — 재사용·root-cause 미소유 | pass | change | skills/testing/SKILL.md:32-60 |
| refactor | pass | high — 카탈로그 1move/전체 suite/10-15파일 상한 절대화 | likely — programming과 cleanup 중복 | partial | high — trust-boundary는 범위 외 | pass | change | skills/refactor/SKILL.md:31-53,72-79 |
| debug | pass | med — 재현 전 가설 금지·최소 2가설·계측 선행 강제 | possible — testing/programming 인접 | partial | med — 아티팩트 인벤토리·시나리오 QA 부재 | pass | change | skills/debug/SKILL.md:14-24 |
| frontend | pass | high — 모든 UI 편집에 탐지·전체 architecture ref·design.md 강제 | possible — programming TS 작업; API 계약은 api로 개선 분리 | partial — 무히트=greenfield 오분류 유지 | med — incumbent/API boundary 반영; root-cause·행동 테스트 부재 | pass | change | skills/frontend/SKILL.md:14-54,58-79; skills/frontend/references/architectures.md:18-35 |
| backend | pass | high — 고정 스택(FastAPI/uv 등) 무조건 규칙화, rule-of-three | possible — programming scaffold; API 계약은 api로 위임 | partial | med — 행동 테스트·원자 커밋 누락 | pass | change | skills/backend/SKILL.md:16-59,65-79; skills/backend/references/persistence.md:26-43 |
| security | pass | med — 좁은 리뷰에도 supply-chain ref·의존성 감사 반복 강제 | none | partial | high — 원자 커밋만 미명시 | pass | change | skills/security/SKILL.md:20-29,112-121 |
| agents | pass | med — 10-line prompt 규칙·고정 5+5 케이스 획일 적용 | likely — security와 tool-permission 충돌 | partial | high — 재사용·원자 커밋 누락 | pass | change | skills/agents/SKILL.md:3,42-58; skills/agents/references/evals.md:18-45 |
| ml | pass | med — uv/src/pyproject·특정 라이브러리를 incumbent 무관 요구 | none | partial | high — 원자 커밋·root-cause 규칙 누락 | pass | change | skills/ml/SKILL.md:18-37,65 |
| git | pass | med — 8-command gate 무조건 선행, 부재 가능한 origin/main fallback | none | partial | high — dirty work 보존 규칙 누락 | pass | change | skills/git/SKILL.md:12-25,134-143 |
| hookify | pass | med — "test suite 필요⇒application code" 반복, 증거 대신 간접 신호 | none | partial | med — 비자명 guard 회귀 테스트 약함 | pass | change | skills/hookify/SKILL.md:47-51,54-66 |
| init | pass | high — 요청 무관 5단계·정적 phase ordering·final-report 반복 강제 | likely — document의 docs/ scaffold와 중복; hook 소유권 충돌은 git 위임으로 해소 | poor | med — idempotency·기존 내용 보존 반영; 최소 변경·행동 테스트 약함 | pass | change | skills/init/SKILL.md:10-21,51-72,87-95,106-133; skills/init/references/phase-1-discovery.md:14-61 |
| document | warn — 트리거 7개(3-6 초과) | med — plan 불변·root >3 자동 이동 절대화 | likely — init의 docs/ scaffold와 `setting up docs/` 소유 중복 | partial | med — 요청 외 기존 문서 보존·행동 검증 약함 | pass | change | skills/document/SKILL.md:2-3,49-59,93-111 |
| write-report | pass | low — 반복이 enforced-report 불변조건에 한정 | none | good | high — source-first·validator 증거 직접 반영 | pass | no-change | skills/write-report/SKILL.md:10-25,69-121 |
| api | warn — 트리거 3-6 초과·한국어 변형 다수 | high — 기존 계약에도 /api/v1·무-envelope·전 목록 pagination·단일 ProblemDetail 강제 | none — backend/frontend/testing 경계 명시 | partial — contract-first이나 incumbent 보존보다 고정 규칙 우선 | med — 경계 1회 파싱·비밀 보호 반영; 시나리오 검증·원자 커밋 미명시 | pass | change | skills/api/SKILL.md:2,14-50; skills/api/references/conventions.md:1-31; skills/api/references/error-contract.md:1-43 |
| cicd | warn — 트리거 3-6 초과·한국어 변형 다수 | high — 전 CI/CD를 GitHub Actions+registry 없는 Jenkins/Compose 토폴로지로 고정 | possible — backend/testing/git 인접(hand-off 명시) | poor — 한 배포 토폴로지를 보편 불변조건화 | high — 값싼 검증·incumbent 명령·상태 증거·복구 반영 | pass | change | skills/cicd/SKILL.md:2,12-57; skills/cicd/references/ci-gating.md:1-31; skills/cicd/references/pipeline-safety.md:1-35 |
| write-prd | pass | med — 목표 ≤3·Features Out 상시·고정 fill order 일반화, template 안내 제거를 사후 정리로 전가 | possible — document 인접(PRD 경계 명시) | partial — SKILL과 518줄 template의 안내 중복 | med — 근거 우선·비발명·측정 결과 반영; 실행 검증 범위 밖 | pass | change | skills/write-prd/SKILL.md:14-105; skills/write-prd/templates/prd.template.md:16-37,447-518 |

## 배치 구성 (change 19행, 매트릭스 행 순서, k=ceil(19/5)=4 → 5+5+5+4)

| 배치 PR | 스킬 | 함께 작성할 라우팅 케이스 |
|---|---|---|
| 배치1 (PR-④) | skillify, distil, research, programming, testing | testing |
| 배치2 (PR-⑤) | refactor, debug, frontend, backend, security | refactor, frontend, backend, security |
| 배치3 (PR-⑥) | agents, ml, git, hookify, init | agents, ml |
| 배치4 (PR-⑦) | document, api, cicd, write-prd | api, cicd, write-prd (+write-report 커버 확인) |

coverage 단계: 현행 10 → 배치1 후 11 → 배치2 후 15 → 배치3 후 17 → 배치4 후 20 → ast-grep 후 21.

각 change 행의 구체 수정 목록은 [omo-analysis.md의 "스킬별 change 상세"](../research/omo-analysis.md#스킬별-change-상세)에 있다 (신규 3종 포함).
