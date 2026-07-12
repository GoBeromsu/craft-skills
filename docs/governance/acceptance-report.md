# omo-보강 이니셔티브 수용 대조표 (AC①~⑩)

- 근거 계획: ralplan 합의본(스펙: deep-interview-craft-skills-omo-enhancement; fact-6/12/13은 IR-1로, AC④는 IR-2로 개정)
- 실행 기간: 2026-07-12 (PR #43–#51, 9개 머지)
- 검증 시점 커밋: main @ acceptance-report 머지 시점
- 재검증 명령은 각 행에 기재. CI 항목은 GitHub 계정 billing lock으로 로컬 실행 증거로 대체(하단 미결 항목).

| AC | 기준 | 상태 | 증거 / 재검증 명령 |
|---|---|---|---|
| ① | SHA 고정 omo 분석 + 25행 처분 원장 + 후속 PR 인용 | **충족** | `docs/research/omo-analysis.md` (pin `9b9f8e8f…6659`, 조회일 2026-07-11); `count_ledger_rows.py --section "처분 원장" --expect 25 --ledger --names-file scripts/governance/fixtures/omo-skills-25.txt` exit 0; PR #47–#51 본문·CHANGELOG가 문서 인용 |
| ② | 감사 매트릭스 무결 + 승인 | **충족** (20행으로 정합 개정) | `audit_matrix_lint.py docs/governance/audit-matrix.md --rows 20` exit 0; 승인은 IR-5 위임 하에 critic 자체반증 레인 4회(배치별)로 대체, 영수증은 ultragoal ledger |
| ③ | change 처분 전량 배치 PR 머지 + 범프/CHANGELOG/Layer-1/eval 영수증 | **부분충족** | change 19행 전량 4개 배치 PR(#47–#50) 머지; `check_version_bump.py` exit 0; Layer-1 배치별 exit 0(5/5/5/4 패키지); **행동 eval 영수증(4런타임×19케이스)은 eval 캠페인으로 이월** — 로컬 eval 스크래치는 21스킬 작성 완료, 영수증 notary 도구 가동 준비 완료 |
| ④ | 통합 라우팅 패스 = 구조 + 행동 + 커버리지 (IR-2) | **부분충족** | (a) 구조: `harness.py --profile portable --config scripts/governance/fixtures/repos.portable.json …` exit 0, blocking 0; (c) 커버리지: 21집합 동치 `check_inventory_surfaces.py` exit 0; (b) 행동: eval 캠페인 이월(③과 동일) |
| ⑤ | Layer-1 2종 + portable 하네스 PR 필수 CI | **차단(외부)** | 워크플로 3잡은 `pr-check.yml`에 배선 완료(코드). **GitHub 계정 billing lock으로 전 잡 미기동** + branch protection 미설정(404) — 운영자 액션 2건 필요: 결제 해제, required 3 context 지정(`pr-check / layer1-format`·`layer1-hygiene`·`harness-portable`) |
| ⑥ | 프로파일 분리·객관만 blocking·주관 warning·fp 기록·단독 비차단 | **충족** | portable 단독 exit 0(adapter_parity 미실행·외부 neighbor 필터); 어휘 판정 advisory(`test_harness_profiles.py` assert); **fp 측정**: known-good 코퍼스=현행 21스킬 트리, portable blocking findings 0 = false-positive 0 기준선(본 문서가 기록 지점) |
| ⑦ | 경로 정합 + 런타임별 스모크 | **충족** | `check_install_paths.py` exit 0; 4런타임 스모크 라이브 통과(artifact /tmp/craft-smokes/): Codex install readback+21집합 동치, Claude 실로드+집합 동치, Hermes external_dirs 노출, generic 자기완결성 |
| ⑧ | 원칙 내재화(IR-1) | **충족** | 매트릭스 원칙반영도 열 20행 전부 채점(`audit_matrix_lint.py` 9필드 무결); change 19스킬 CHANGELOG 2026-07-12 bullet이 반영 원칙 명명; 채굴 원칙 12개는 `omo-analysis.md` 부록 |
| ⑨ | ast-grep eval + graceful | **부분충족** | graceful absence 라이브 확인(binary 부재 머신에서 폴백 분기 실행); 인벤토리 21 동치; **eval 영수증은 캠페인 이월** |
| ⑩ | 벤더 가이드 갱신 체크리스트 | **충족** | `omo-analysis.md` `## 벤더 가이드 갱신 체크리스트` (Claude Fable 5 / GPT-5.6 Sol, 조회일 2026-07-11) |

## 미결 항목 (내구 기록)

1. **eval 캠페인** (③④⑨의 행동 증거): 변경 21스킬 × 트리거 16 + 행동 3 × 런타임 4행 영수증을 `run_evals.py --emit/--validate`로 생성·검증. 도구·스키마·로컬 스크래치 준비 완료 — 실행은 별도 세션/CI 캠페인 권장(추정 ~1,300 모델 호출).
2. **GitHub billing lock 해제** (⑤): 운영자 결제 액션. 해제 후 required status 3 context 지정 → `gh api repos/GoBeromsu/craft-skills/branches/main/protection --jq '.required_status_checks.checks[].context'` readback으로 완료 확인.
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
