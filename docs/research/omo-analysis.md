# omo(lazycodex) 스킬 분석 — craft-skills 보강 결정 문서

- **고정 커밋**: `9b9f8e8f620e3f797567078734165350e1e46659` (code-yeongyu/lazycodex, main HEAD)
- **조회일**: 2026-07-11 (분석 통합: 2026-07-12)
- **인용 규칙**: 이 문서와 후속 PR은 raw main URL을 인용하지 않는다. 모든 omo 인용은 위 commit SHA 기준.
- **성격**: 결정 지향 문서. 25개 omo 스킬의 전수 카탈로그가 아니라 이식/기각 결정과 그 근거를 기록한다. 완전성은 아래 [처분 원장](#처분-원장)이 보장한다.
- **수집 방법**: read-only subagent 4군 병렬 감사(로컬 17스킬 × 9필드 + omo 25스킬 처분), 메인 세션 통합. 감사 결과는 [audit-matrix.md](../governance/audit-matrix.md).

## 요약 판단

omo는 Codex 단일 런타임 위에 세운 수직 통합 하네스다. 강점은 **결정 규칙 중심의 도구 교육**(ast-grep), **모드 게이트**(git-master의 COMMIT/REBASE/HISTORY/STATUS), **증거 수명주기**(visual-qa) 같은 이식 가능한 구조에 있고, 약점은 런타임 결합(ultrawork 계열, rules 주입 엔진)과 omo `programming`류의 "유일하게 허용되는 설정" 식 과잉 절대규칙에 있다. craft-skills는 멀티 벤더 제약상 전자만 이식하고 후자는 반면교사로 삼는다 — 실제로 이번 감사에서 우리 스킬 16/17개가 같은 과잉지시 패턴을 갖고 있음이 드러났다.

## 이식 후보 (11)

| omo 스킬 | 이식할 것 (정확히) | 반영 위치 |
|---|---|---|
| ast-grep | 교육 구조 전체: 한 문장 결정 테스트("syntax tree인가 bytes인가") → 3대 오해 모델(regex 아님·pattern은 parseable code·`--json`+`--update-all` 충돌) → 안전 경로(validate→search→dry-run→blast-radius→apply) → 진단 사다리 → invariant recap | WP8 신규 `skills/ast-grep/` 시드 |
| git-master | COMMIT/REBASE/HISTORY/STATUS 모드 게이트, 조사 요청에 mutation 금지, 요청된 변경만 커밋하고 unrelated dirty work 보존 | 배치4 `git` 보강 |
| debugging | 런타임 증거 > 그럴듯한 코드 읽기, 임시 아티팩트 전수 인벤토리·제거, 수정 후 실제 사용자 시나리오 QA | 배치2 `debug` 보강 |
| remove-ai-slops | trust-boundary 검증/에러 처리는 적대적 회귀 테스트가 중복성을 증명할 때만 제거 가능 | 배치2 `programming`/`security` 보강 |
| programming (omo) | 로깅 결정 규칙만: 기존 관행 추종, 소비자 기준 레벨, 결정 지점 배치, 안정 메시지+구조화 필드 | 배치1 `programming` 보강 |
| ulw-plan | 질문 전 증거 수집 필터, 구현 단계마다 구체 경로·수용 조건·실행 가능한 happy/failure QA 명시 | 배치4 `document`(plan 템플릿) 보강 |
| ulw-research | 위험 계층별 증거 규칙: 코드형 주장은 실행 검증, 중대 비코드 주장은 반증 탐색+독립 확증, 게이트 실패 시 유보 | 배치1 `research` 보강 |
| review-work | 실행자와 독립된 검증자, timeout/missing/inconclusive를 PASS로 세지 않음, 증거 redaction | 배치1 `skillify`(eval 규율) 참고 |
| frontend (omo) | 작은 reference set만 고르는 라우터 구조, concrete-reference/greenfield/incumbent 3분기 | 배치2 `frontend` 보강 |
| visual-qa | 증거 수명주기: 표면 유형 판별→상태/뷰포트 전수 목록→최신 캡처→동일 크기 diff→수치는 증거이지 verdict 아님; CJK/전각 체크 | 배치2 `frontend`·`testing` 참고 |
| lsp | 시맨틱 연산 선택 규칙만: diagnostics/definition/references/rename은 심볼 안전성이 필요할 때 텍스트 검색보다 우선 | 배치1 `programming`·배치2 `refactor`에 결정 규칙 1줄 |

## 기각 (13) — 사유 유형별

- **런타임 실행 모드/에이전트 운용** (craft-skills의 vendor-agnostic 계약 위반): `ultrawork`(hook 주입·notepad·Codex 서브에이전트), `ulw-loop`(mailbox 시맨틱), `start-work`(boulder.json·Stop hook), `teammode`(.omo/teams·transport API), `coding-agent-sessions`(벤더 세션 스토어).
- **벤더 플러그인 문서**: `rules`(CODEX_RULES_* 주입 엔진), `comment-checker`(PostToolUse hook), `lsp-setup`(BUILTIN_SERVERS·.codex config).
- **벤더 기여 워크플로**: `lcx-doctor`, `lcx-contribute-bug-fix`, `lcx-report-bug`(특정 repo ownership·gh 배달).
- **중복+과잉 절차**: `refactor`(omo)(로컬 characterization 워크플로와 중복, 6-phase 의식), `ultimate-browsing`(WAF 우회·cookie 주입 — 보안·유지보수 비용 > 이득).

## no-delta (1)

- `init-deep`: 복잡도 점수 기반 AGENTS.md 배치·중복 제거 — 로컬 `init`이 동일 구조를 이미 소유.

## 6트랙 시사점

1. **omo 분석(본 문서)**: omo의 과잉 절대규칙은 우리 감사 기준(과잉지시 열)의 실증 사례다. "반면교사" 판단이 감사에서 우리 스킬 16/17 change로 확인됨.
2. **skillify 재감사**: 이식 후보의 공통 형태는 "결정 규칙 + 증거 수명주기"다. 배치 편집의 방향은 절대규칙→결정 규칙 전환, 중복 제거, 원칙 내재화.
3. **원칙 내재화(IR-1)**: 별도 conventions 패키지 없음. 아래 [채굴 원칙](#채굴된-운영자-원칙-부록)을 각 도메인 스킬 본문에 반영하고 매트릭스 원칙반영도 열로 측정.
4. **도구 연동**: ast-grep 하나만 파일럿(WP8). lsp는 결정 규칙 1줄로 축소 반영, 스킬 신설은 반복 실패 증거 확보 시.
5. **하네스 적정성**: omo가 느슨한 건 단일 런타임이기 때문. 우리는 완화가 아닌 구조 교정(portable/cross-repo 분리) — WP2에서 실행.
6. **프롬프팅 가이드 정합**: 두 벤더 가이드의 공통 원칙(중복 제거·outcome-first·절대규칙은 진짜 불변조건만)이 감사 '가이드정합' 열의 판정 기준. 아래 체크리스트로 갱신 추적.

## 처분 원장

25개 omo 스킬 전수. 검증: `python3 scripts/governance/tools/count_ledger_rows.py docs/research/omo-analysis.md --section "처분 원장" --expect 25`

| omo skill | disposition | 근거 요약 |
|---|---|---|
| ast-grep | candidate | 교육 구조 전체가 WP8 시드 (pinned SKILL.md L14-L289) |
| git-master | candidate | 모드 게이트·조사-비변형·dirty work 보존 (L10-L57) |
| debugging | candidate | 아티팩트 인벤토리·시나리오 QA (L8-L13, L80-L105) |
| remove-ai-slops | candidate | 적대적 회귀 증명 시에만 guard 제거 (L45-L67) |
| programming | candidate | 로깅 결정 규칙만 (L226-L230) |
| ulw-plan | candidate | 증거-선행 필터·단계별 QA 명시 (L72-L95) |
| ulw-research | candidate | 위험 계층별 증거 규칙 (L219-L279) |
| review-work | candidate | 독립 검증자·비-PASS 규칙 (L48-L100) |
| frontend | candidate | reference 라우터·3분기 (L8-L61) |
| visual-qa | candidate | 증거 수명주기·CJK 체크 (L47-L145) |
| lsp | candidate | 시맨틱 연산 선택 규칙 (L8-L34) |
| init-deep | no-delta | 로컬 init이 동일 구조 소유 (L55-L300) |
| ultrawork | rejected | 런타임 실행 모드 (L9-L120) |
| ulw-loop | rejected | mailbox 시맨틱 어댑터 (L10-L57) |
| start-work | rejected | boulder.json·Stop hook 운용 (L7-L111) |
| teammode | rejected | .omo/teams transport 프로토콜 (L8-L110) |
| coding-agent-sessions | rejected | 벤더 세션 스토어 도구 (L10-L145) |
| rules | rejected | Codex 주입 엔진 문서 (L8-L31) |
| comment-checker | rejected | PostToolUse hook 운용 (L8-L16) |
| lsp-setup | rejected | 벤더 LSP 런타임 매뉴얼 (L10-L128) |
| lcx-doctor | rejected | 벤더 설치 진단 (L10-L90) |
| lcx-contribute-bug-fix | rejected | 벤더 기여 워크플로 (L10-L132) |
| lcx-report-bug | rejected | 벤더 버그 라우터 (L10-L126) |
| refactor | rejected | 로컬과 중복 + 절차 과잉 (L8-L95) |
| ultimate-browsing | rejected | WAF 우회·cookie 주입 리스크 (L8-L66) |

## 스킬별 change 상세

감사에서 처분=change로 확정된 16개 스킬의 구체 수정 목록. 배치 PR이 이 목록을 스코프로 삼는다.

### 배치1: skillify · distil · research · programming
- **skillify**: `stash unrelated work`를 비변형 clean-worktree 체크+격리 worktree 경로로 교체(SKILL.md:73-74); branch→PR 규칙을 references/lifecycle.md §6 단일 소유로 통합(5회 중복 제거); CHANGELOG/secret/validator 규칙 중복 제거.
- **distil**: `&`/`$` denylist를 https 스킴 파싱+구조화 인자 전달로 교체(SKILL.md:21-23); no-execute 불변조건을 Intake 1곳 소유로.
- **research**: 위험 비례 검증 추가(경합 주장 최소 실행 probe, 중대 비코드 주장 반증 탐색+독립 확증 — omo ulw-research 이식); 인용 불변조건 중복 제거.
- **programming**: 참조 로드를 작업 관련으로 한정(:14-21); "모든 라인 red-first"를 행동/위험 기준 규칙으로(:52); 250 LOC를 리뷰 신호로(:54-62); 도구 선택 incumbent-first(:72-76); omo 로깅 결정 규칙 이식; smell-only 리뷰는 refactor로 단일 라우팅.

### 배치2: testing · refactor · debug · frontend
- **testing**: 커버리지 quota를 위험/계약 결정 규칙으로(:32-46); prove-it을 재현 가능 결함에 스코프(:48-50); 파일명 스캔은 advisory(:52-60).
- **refactor**: 검증 체크포인트를 blast radius 비례로(:31-40); 10-15파일 상한을 응집도 기준으로(:42-45); smell 스캔은 해당 클래스만(:47-53); omo lsp 시맨틱 연산 규칙 1줄.
- **debug**: 직접 증거(스택 트레이스/실패 테스트)로 첫 가설 허용(:14); 복수 가설·계측은 증거 모호 시에만(:16,21); omo debugging 이식 — 아티팩트 전수 인벤토리·실제 시나리오 QA(:10,22).
- **frontend**: 무히트=greenfield 제거, known/unknown-incumbent/greenfield 3분기(:18-29 — omo frontend 라우터 이식); design.md 게이트를 설계 변경에만 스코프(:31-43); visual-qa 증거 수명주기 참고 반영.

### 배치3: backend · security · agents · ml
- **backend**: FastAPI/uv·Express/zod를 greenfield 기본값으로만(:33-59); folder triad는 후보 신호(:16-31); rule-of-three를 소유권/결합도 판단으로(:69).
- **security**: supply-chain ref·의존성 감사를 full audit 또는 해당 reachability로 스코프(:20-29); review-only와 fix 요청 구분(:52); omo remove-ai-slops 적대적 회귀 규칙 이식.
- **agents**: tool 행동 변경(agents) vs 권한 집행(security) 라우팅 분리(:3,58-62); 10-line prompt 규칙을 리뷰 가능성 결정으로(:42-54); 5+5 케이스를 위험 기반 시작점으로(references/evals.md:18-45).
- **ml**: uv/src/pyproject를 greenfield 예시로, incumbent 우선(:18,35-37,65); "costs nothing" 제거(:43); 검증을 관찰 가능한 결과 중심으로.

### 배치4: git · hookify · init · document
- **git**: BASE 결정을 origin/HEAD→실재 브랜치→"비교 기준 없음" 순으로(:12-25); "first edit 이전"을 "첫 git mutation 이전"으로(:134-143); omo git-master 이식 — 요청 파일만 커밋+dirty work 보존, 조사 요청 비변형.
- **hookify**: "test suite 필요⇒application code" 삭제, 측정 지표(지연·비결정성·오탐률) 기반 판단(:47-51); 비자명 guard에 red/green 회귀 테스트(:54-66); core.hooksPath 단독 소유권을 init/git 라우팅과 정합(:25-27).
- **init**: bootstrap/cartography를 outcome별 분기로(:11-21); 런타임 이름 맵을 capability 판단 1개로(:43-50); final-report 규칙 단일화(:19-21,93-119); hook 설치는 hookify로 라우팅(:54-61); omo ulw-plan 참고.
- **document**: "setting up docs/" 트리거 제거(7→6개)+`Not for repository docs scaffolding (use init)` 추가(:2-3); root >3 자동 이동을 조사·제안 신호로(:49-57); plan 불변성을 명시적 계약으로(:98-102); omo ulw-plan의 단계별 QA 명시를 plan 템플릿에 반영.

## 채굴된 운영자 원칙 부록

programming/testing/git 본문에서 채굴한 프로젝트-무관 원칙(12 후보 → 승인 목록). 배치 PR이 이 원칙들이 각 도메인 스킬 본문에 자연스럽게 반영되었는지(원칙반영도 열) 기준으로 삼는다.

1. 정확함이 유지보수성보다, 유지보수성이 간결함보다 먼저다 (programming:10).
2. 새로 만들기 전에 추측성 필요를 제거하고 기존 저장소 패턴 → stdlib/플랫폼 → 설치된 의존성 순으로 재사용한다 (programming:25-35).
3. 버그 리포트는 증상이다: 호출자 전체를 보고 공유 상류 지점을 한 번 고친다 (programming:37).
4. 신뢰 경계에서 한 번 타입 있는 값으로 파싱하고, 내부에서는 그 계약을 믿는다 (programming:47-51).
5. 검증은 관찰 가능한 행동을 실제 명령/시나리오로 실행하는 것이다; 동어반복 mock은 증거가 아니다 (programming/references/workflow.md:52-57).
6. 재현 가능한 결함은 결함이 사는 자연 계층에서 최소 failing→passing 회귀 테스트와 함께 출하한다 (testing:48-50).
7. 테스트는 검증 대상과 접촉 자원으로 분류하고, 필요한 확신을 주는 가장 싼 계층을 고른다 (testing:28-46).
8. 테스트는 결정적이고 행동 특정적이어야 한다: sleep/벽시계/무시드 랜덤을 제어 가능한 것으로 바꾼다 (testing:62-64).
9. 행동 전에 상태·diff·브랜치·히스토리라는 독립 ground truth를 수집한다; 기억은 증거가 아니다 (git:10-25).
10. 외부 표준을 자동 도입하지 말고 incumbent convention을 실측한 뒤 따른다 (git:27-36).
11. 커밋 경계는 파일 수가 아니라 하나의 논리적·독립 revert 가능한 변화다 (git:38-57).
12. 공유 상태를 바꾸는 파괴적 연산에는 협업자 상태를 덮지 않는 primitive와 명시적 복구 경로를 쓴다 (git:105-113).

## 벤더 가이드 갱신 체크리스트

모델 업데이트 시 이 체크리스트로 본 문서와 감사 기준을 갱신한다 (가이드 추적 스킬은 반복 증거 축적 시 생성 — 스펙 fact-10).

- [ ] Anthropic 최신 모델 프롬프팅 가이드 확인 (현재 기준: Claude Fable 5 가이드, 조회일 2026-07-11)
- [ ] OpenAI 최신 모델 프롬프팅 가이드 확인 (현재 기준: GPT-5.6 Sol 가이드, 조회일 2026-07-11)
- [ ] 두 가이드의 **공통** 원칙 추출 (벤더 전용 메커니즘 제외 — effort/send_to_user/PTC 등)
- [ ] 공통 원칙 변화가 있으면: 본 문서 6트랙 시사점 §6 갱신 → 감사 '가이드정합' 판정 기준 갱신 → 영향 스킬 change 재평가
- [ ] 갱신 시 조회일·가이드 리비전 기록
