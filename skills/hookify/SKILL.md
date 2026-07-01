---
name: hookify
description: Turn a convention or SE best-practice into LOCAL deterministic enforcement that forces agent and human behavior. Use when you say "force this rule locally", "make the agent stop doing X", "add a pre-commit / lint / hook guard", "hookify this", "enforce this without CI", "block edits to read-only paths", or "wire a Claude Code / Codex hook". Picks the earliest local enforcement surface (runtime hook → lint → pre-commit), ships a starter guard, and red-proves it fires.
version: 0.1.0
allowed-tools: [Bash, Read, Edit, Write, Grep, Glob]
compatibility: claude-code, codex, hermes
---

# hookify

규칙 하나를 **로컬 결정론적 강제**로 바꿔, 에이전트(와 사람)가 그 행동을 *하기 전에* 차단당하도록 만든다. CI가 아니다 — CI는 백스톱일 뿐, 강제는 로컬에서 in-loop으로 일어난다.

## Overview

강제의 목적은 영구 피해 방지가 아니라 **"틀렸다"는 교정 신호를 결정론적으로 주는 것**이다. 표면을 고르는 축은 "되돌릴 수 있나"가 아니라 **신호 지연 × 명료성 × 신뢰도**다. 같은 규칙이면 가장 이른 로컬 표면에 둔다. 훅은 체크의 품질을 결정론적으로 *증폭*할 뿐 — 좋은 규칙은 불가피하게, 나쁜 규칙은 세금으로 만든다. 그래서 차단 훅은 졸업장이지 시작점이 아니다.

## When to Use

- 산문 규범(`AGENTS.md`)을 에이전트가 반복해서 어길 때 → 결정론적 표면으로 올린다.
- 금지 경로 편집·위험 명령·read-only mutation을 in-loop으로 막고 싶을 때 → 티어 1 런타임 훅.
- 시크릿·보호 브랜치 직접 커밋·대형 blob 같은 비가역을 커밋 직전 막고 싶을 때 → 티어 3 pre-commit.
- Claude Code / Codex 양쪽에서 같은 규칙을 강제하고 싶을 때.

쓰지 않을 때: 규칙이 아직 표류 중이거나 오탐이 잦으면(아래 3-gate 미통과) 차단 훅이 아니라 산문/비차단 lint에 둔다.

## Core Process

### PHASE 0 — 규칙 한 줄로 진술

강제할 규칙을 *위반 조건 + 고치는 법*으로 한 문장에 적는다. 한 문장에 안 들어가면 규칙이 아직 안 익은 것 — 먼저 산문에 두고 관찰한다.

### PHASE 1 — 표면 선택

`references/surface-and-tier.md`의 사다리와 절차를 따른다. 요지:

1. **산문에 먼저 진술**(티어 0) — 강제는 산문이 실패한 자리의 백스톱이다.
2. **결정론적으로 잡을 가장 이른 로컬 표면을 고른다:**
   - 도구 행위(편집 경로·명령)로 드러나는 위반 → **티어 1 런타임 훅**.
   - 파일 내용 품질 → **티어 2 lint**.
   - 커밋되어야만 드러나는 비가역 → **티어 3 pre-commit**.
3. CI는 로컬을 건너뛴 경우의 백스톱일 뿐 — hookify의 초점이 아니다.

### PHASE 2 — 3-gate 졸업 판별

차단 훅에 올리기 전, 규칙이 세 게이트를 모두 통과하는지 확인한다(`references/surface-and-tier.md` 상세):

- **G1 싸다** — 빠르고 외부 상태(네트워크·라이브 백엔드) 의존 없음.
- **G2 정확하다** — 오탐 거의 없음. **가드가 자기 테스트 스위트를 필요로 하면 애플리케이션 코드** → 무른 표면으로 내린다.
- **G3 안정적이다** — 강제하는 구조가 더 이상 표류하지 않음.

하나라도 실패하면 비차단(lint 경고)으로 관찰하다가, 증명되면 졸업시킨다.

### PHASE 3 — 가드 저작

`scripts/guard-skeleton.py`를 복제해 규칙 하나만 검사하게 만든다. 가드는:

- stdin 또는 인자로 대상(경로·내용)을 받는다.
- 위반이면 **비영 종료 + 위반 규칙과 정확한 수정 방법을 한 줄로** stderr에 낸다(모호한 메시지는 우회로 학습된다).
- 같은 가드를 티어 1·2·3에 재사용한다.

### PHASE 4 — 표면에 설치

- **Claude Code 런타임 훅:** `scripts/claude-code-pretooluse-guard.sh` + `scripts/settings-hooks.example.json`을 `.claude/settings.json`에 머지. 상세: `references/claude-code-hooks.md`. PreToolUse만 부작용을 막는다(PostToolUse는 못 막음).
- **Codex 런타임 훅:** `scripts/codex-hook.example.toml`을 `.codex/config.toml`에 머지. 같은 가드 재사용. 상세: `references/codex-hooks.md`.
- **lint:** 프로젝트 linter(ruff/eslint)에 규칙 추가 또는 가드 스크립트를 작업 명령에 노출.
- **pre-commit:** `git config core.hooksPath`로 커밋된 훅 디렉터리를 가리키고 `scripts/pre-commit.sh`가 가드들을 디스패치.

### PHASE 5 — red 증명

설치만 하고 발동을 안 본 가드는 미완이다. **위반 입력 → 차단, 정상 입력 → 통과**를 직접 실행해 눈으로 확인한다(`references/claude-code-hooks.md`의 echo|guard 예시). 가드 자체는 `--selfcheck`로 빨강/초록을 증명한다(`guard-skeleton.py --selfcheck`).

## Common Rationalizations

- *"CI에서 잡으면 되잖아."* — CI는 push 후·머지 차단으로 가장 늦은 신호다. 에이전트는 그 전에 이미 잘못된 행동을 끝낸다. 로컬에서 *하기 전에* 막아야 교정이 된다.
- *"가드에 테스트를 붙이면 더 튼튼하지."* — 가드가 자기 테스트 스위트를 요구하면 그건 잘못된 티어의 애플리케이션 코드다. 규칙을 무른 표면으로 내린다(G2).
- *"커버리지를 위해 가드를 더 넣자."* — 차단 훅은 유한한 신뢰 예산을 쓴다. 오탐 한 번이면 사람은 `--no-verify`, 에이전트는 우회 — 모든 훅의 신뢰가 깎인다. 적고 날카롭게.
- *"메시지는 대충 적어도 돼."* — 모호한 차단 사유는 우회로 학습된다. 규칙 + 수정 방법을 한 줄로.

## Red Flags

- 차단 훅을 깔았는데 위반 입력으로 발동을 본 적이 없다 → 미완(PHASE 5).
- 규칙을 한 문장으로 못 적는다 → 아직 강제할 만큼 안 익었다(PHASE 0).
- 가드가 네트워크/라이브 백엔드를 친다 → G1 실패, 차단 훅 부적격.
- PostToolUse로 부작용을 막으려 한다 → 못 막는다, PreToolUse로 올린다.
- 같은 규칙을 CI에만 두고 로컬엔 없다 → 신호가 가장 늦다, 로컬 표면으로 내린다.

## Verification

- [ ] 규칙이 위반 조건 + 수정 방법으로 한 문장에 적혔다.
- [ ] 가장 이른 로컬 표면을 골랐고 근거가 사다리로 설명된다.
- [ ] 차단 훅이면 3-gate(싸다·정확하다·안정적이다)를 통과했다.
- [ ] 가드 메시지가 위반 규칙 + 수정 방법을 한 줄로 준다.
- [ ] red 증명 완료: 위반 → 차단, 정상 → 통과를 직접 실행해 확인했다.

## Requirements

- `bash`, `jq` (Claude Code/Codex 런타임 가드)
- `python3` (가드 스켈레톤·selfcheck)
- `git` (pre-commit `core.hooksPath`)
