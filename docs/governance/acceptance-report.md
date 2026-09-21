# omo-보강 이니셔티브 수용 대조표 (AC①~⑩)
이 문서는 2026-07 omo-보강 이니셔티브의 당시 관측 기록이다. 현재 수용·배포 증명이나 운영 요구가 아니며, 당시 하네스·행 수 쿼터·영수증 경로는 은퇴했다. 현재 검사는 루트 `AGENTS.md`와 실소유자가 정한다. 당시 측정 점수를 재실행하거나 반증하지 않았다. 구 산출물은 Git 이력에 남는다.

- 근거 계획: ralplan 합의본(스펙: deep-interview-craft-skills-omo-enhancement; fact-6/12/13은 IR-1로, AC④는 IR-2로 개정)
- 실행 기간: 2026-07-12 (PR #43–#51, 9개 머지)
- 검증 시점 커밋: main @ acceptance-report 머지 시점
- 재검증 명령은 각 행에 기재되어 있으나 당시 기록이다. CI 항목의 GitHub 계정 billing lock 서술은 2026-07 관측이며, 현재 운영 할 일이나 배포 증명이 아니다(하단 역사 기록).

| AC | 기준 | 상태 | 증거 / 재검증 명령 |
|---|---|---|---|
| ① | SHA 고정 omo 분석 + 25행 처분 원장 + 후속 PR 인용 | **충족** | `docs/research/omo-analysis.md` (pin `9b9f8e8f…6659`, 조회일 2026-07-11); `count_ledger_rows.py --section "처분 원장" --expect 25 --ledger --names-file scripts/governance/fixtures/omo-skills-25.txt` exit 0; PR #47–#51 본문·CHANGELOG가 문서 인용 |
| ② | 감사 매트릭스 무결 + 승인 | **충족** (20행으로 정합 개정) | `audit_matrix_lint.py docs/governance/audit-matrix.md --rows 20` exit 0; 승인은 IR-5 위임 하에 critic 자체반증 레인 4회(배치별)로 대체, 영수증은 ultragoal ledger |
| ③ | change 처분 전량 배치 PR 머지 + 범프/CHANGELOG/Layer-1/eval 영수증 | **충족(실측)** | change 19행 전량 4개 배치 PR(#47–#50) 머지; `check_version_bump.py` exit 0; Layer-1 배치별 exit 0; **eval 캠페인 실측 완료**: 20영수증 `docs/governance/receipts/` (1,520케이스, 96.6% pass; full-pass 4 / partial 16 — 실패 케이스 사유 포함 보존, [campaign-summary.md](receipts/campaign-summary.md)) |
| ④ | 통합 라우팅 패스 = 구조 + 행동 + 커버리지 (IR-2) | **충족** | (a) 구조: portable 하네스 exit 0, blocking 0; (b) 행동: 라우팅 실측 full-context 3레인 **99.8%**(958/960), generic 97.5% — 트리거 라우팅 경계 검증 완료; (c) 커버리지: 21집합 동치 exit 0 |
| ⑤ | Layer-1 2종 + portable 하네스 PR 필수 CI | **차단(외부)** (2026-07 관측, 현재 미검증) | 당시 워크플로 3잡은 `pr-check.yml`에 배선된 것으로 기록. **당시 GitHub 계정 billing lock으로 전 잡 미기동** + branch protection 미설정(404) — 당시 운영자 액션으로 적힌 결제 해제·required 3 context 지정(`pr-check / layer1-format`·`layer1-hygiene`·`harness-portable`)은 역사 기록이며 현재 운영 할 일이 아니다. |
| ⑥ | 프로파일 분리·객관만 blocking·주관 warning·fp 기록·단독 비차단 | **충족** | portable 단독 exit 0(adapter_parity 미실행·외부 neighbor 필터); 어휘 판정 advisory(`test_harness_profiles.py` assert); **fp 측정**: known-good 코퍼스=현행 21스킬 트리, portable blocking findings 0 = false-positive 0 기준선(본 문서가 기록 지점) |
| ⑦ | 경로 정합 + 런타임별 스모크 | **충족** | `check_install_paths.py` exit 0; 4런타임 스모크 라이브 통과(artifact /tmp/craft-smokes/): Codex install readback+21집합 동치, Claude 실로드+집합 동치, Hermes external_dirs 노출, generic 자기완결성 |
| ⑧ | 원칙 내재화(IR-1) | **충족** | 매트릭스 원칙반영도 열 20행 전부 채점(`audit_matrix_lint.py` 9필드 무결); change 19스킬 CHANGELOG 2026-07-12 bullet이 반영 원칙 명명; 채굴 원칙 12개는 `omo-analysis.md` 부록 |
| ⑨ | ast-grep eval + graceful | **충족** | graceful absence 라이브 확인; 인벤토리 21 동치; **영수증 full-pass 76/76** (`receipts/ast-grep-campaign-2026-07-12.json`, validate exit 0) |
| ⑩ | 벤더 가이드 갱신 체크리스트 | **충족** | `omo-analysis.md` `## 벤더 가이드 갱신 체크리스트` (Claude Fable 5 / GPT-5.6 Sol, 조회일 2026-07-11) |

## 당시 미결 기록 (역사, 현재 미검증)

1. ~~eval 캠페인~~ **완료(2026-07-12)**: 1,520케이스 실측, 20영수증 커밋. 잔여 신호는 당시 [campaign-summary.md](receipts/campaign-summary.md) — 행동 판정 42건은 기대치 저작 스타일 이슈(후속 스크래치 규율), git behavior-03은 후속 후보 1건. 영수증·요약은 Git 이력에 남으며 현재 운영 요구가 아니다.
2. **GitHub billing lock 해제** (⑤, 2026-07 관측): 당시 운영자 결제 액션으로 적힘. 해제 후 required status 3 context 지정 → `gh api repos/GoBeromsu/craft-skills/branches/main/protection --jq '.required_status_checks.checks[].context'` readback으로 완료 확인한다고 적혀 있다. 현재 상태 미검증이며 현재 운영 할 일이 아니다.
3. cross-repo 프로파일 검증은 형제 리포(bstack, oh-my-secondbrain) 체크아웃 환경에서만 의미 — `fixtures/repos.cross-repo.json` 준비 완료.

## 이니셔티브 요약

| 산출물 | PR |
|---|---|
| omo 분석(25행 원장) + 감사 매트릭스 + 검증 도구 2종 | #43 |
| 하네스 실행 프로파일 + eval notary + 버전 검사기 + CI 3잡 | #44 |
| 설치 규범 채널 + 경로 정합 + 스모크 4종 | #45 |
| 정합 재감사(매트릭스 20행) | #46 |
| 감사 배치 1–4 (change 19스킬, 원칙 내재화, omo 이식 7종) | #47–#50 |
| ast-grep 파일럿 + 인벤토리 21 + 동치 검사기 | #51 |
