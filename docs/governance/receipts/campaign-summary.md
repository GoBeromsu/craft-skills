# 행동 eval 캠페인 요약 (campaign-2026-07-12)

- 대상: change 19스킬 + ast-grep = 20스킬 × 19케이스(트리거 8 should/8 near-miss + 행동 3) × 런타임 4레인 = **1,520케이스 전량 실측**
- 레인: Claude Code(`claude -p`), Codex(`codex exec`), Hermes(headless), generic(`claude -p` + 1문장 description만 제공하는 일반 에이전트 페르소나 — Not-for 경계 제거 조건)
- 프로토콜: 레인당 스킬별 3콜(라우팅 배치 16케이스 / 행동 답변 3 / 독립 판정 3). 영수증은 `run_evals.py` notary(tested_tree_sha·protocol_hash·raw_result_hash) 계약.
- 기준 tree: `cecd4bc` (baseline/no-skill ref: `e855f68` — 이니셔티브 이전 main)

## 총계

| 레인 | pass/380 | 트리거 실패 | 행동 실패 |
|---|---|---|---|
| Claude Code | 376 | 0 | 4 |
| Codex | 357 | 0 | 23 |
| Hermes | 367 | 2 | 11 |
| generic | 368 | 8 | 4 |
| **합계** | **1468/1520 (96.6%)** | 10 | 42 |

**라우팅 정확도**: full-context 3레인(설명+Not-for 경계 제공) 958/960 = **99.8%**; generic(경계 제거) 312/320 = 97.5%. → 스킬 description 라우팅 경계가 실측으로 검증됨.

## 영수증 판정

- **full-pass(validate exit 0)**: testing, frontend, cicd, ast-grep (76/76)
- **partial(실패 케이스 기록)**: 16스킬 — 실패는 은폐 없이 영수증 case-level에 사유와 함께 보존. `run_evals.py --validate`는 설계상 all-passed에서만 exit 0.

## 실패 분류 (52건)

1. **행동 판정 엄격성 (42건 대부분)** — eval 스크래치의 expected_behavior가 복합 체크리스트로 저작되어(예: skillify 답변이 clean-start·교정 기록을 다뤘어도 branch→PR 미언급 시 fail) 2-4문장 답변이 모든 요소를 못 덮음. 스킬 결함이 아니라 **기대치 저작 스타일** 신호 — 후속 스크래치 저작 시 단일 관찰 가능 행동 1개/케이스 권장.
2. **generic 라우팅 (8건)** — 경계 문장 제거 조건에서의 예상된 약화(agents 권한 near-miss 2, document/write-prd/security/debug 각 1-2). full-context에선 전부 통과 → description 결함 아님.
3. **Hermes 라우팅 (2건)** — programming 인접 케이스(backend/security로). 단일 레인 실패라 경계 결함으로 판정하지 않음.
4. **실제 행동 발견 (1건, 후속 후보)** — git behavior-03: "비교 기준 없음"을 기록한 뒤에도 merge-base 상대 diff를 수행하는 답변 경향. skills/git의 no-comparison-base 분기 문구를 더 단정적으로 만들 여지.

## 케이스 저작 결함 교정 (캠페인 중 4건)

실측에서 3개 full-context 레인이 일관되게 다른 스킬로 라우팅한 케이스는 라우터가 아니라 케이스 결함으로 판정, 교체 후 재평가(교체 후 full-context 16/16):

| 스킬 | 교체 전 | 문제 | 교체 후 |
|---|---|---|---|
| programming should-03 | "scaffold a Python service" | backend 소유가 정답 | "write the core loop for this algorithm in Python" |
| programming should-06 | "add validation at this API boundary" | api/security와 중의적 | "parse this JSON payload into a typed value at the trust boundary" |
| programming should-08 | "add decision-point logging to this TypeScript service" | 'service'가 backend 신호 | "add structured logging at this function's decision points" |
| agents nomiss-03 | "Validate tool-call arguments before executing them." | typed tool args는 agents 소유(중의적) | "enforce an execution allowlist for shell commands the agent can run" |

## 재현

레인 원본 산출물: `/tmp/eval-campaign/<lane>/<skill>.json` (세션 로컬). 영수증 재검증:
`python3 scripts/governance/tools/run_evals.py <skill> --validate docs/governance/receipts/<skill>-campaign-2026-07-12.json`
(주의: validate는 로컬 evals/ 스크래치와 tested_tree_sha가 발급 시점과 일치해야 함 — `--tree cecd4bc^{tree}` 지정)
