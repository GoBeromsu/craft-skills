# Codex CLI 런타임 훅 메커니즘

Codex의 도구-호출 훅은 Claude Code와 같은 모델을 따른다: 도구 호출 전에 명령이 발동하고, stdin으로 호출 페이로드를 받고, 비영(非零) 종료로 차단한다. 같은 가드 스크립트를 두 런타임에서 재사용한다.

## 등록 (config.toml)

프로젝트 `.codex/config.toml` 또는 글로벌 `~/.codex/config.toml`의 `[hooks]` 블록에 등록한다:

```toml
[hooks.pre_tool_use]
match = "edit|apply_patch|write"
command = "${CODEX_PROJECT_DIR}/scripts/guard.sh"
```

- `match`: Codex 빌드가 노출하는 파일 변경 도구 이름(편집/패치/쓰기)에 맞춘다.
- `command`: 셸 실행. 절대경로 하드코딩 대신 프로젝트 루트 환경변수를 쓴다.

스타터: `scripts/codex-hook.example.toml`.

## 버전 주의

Codex의 훅 필드 이름·이벤트 명세는 빌드에 따라 움직인다(`pre_tool_call`/`pre_tool_use`, `notify` 등). 위 형태는 **이식 가능한 의도**이지 고정 API가 아니다 — 설치한 버전의 `codex --help`와 config 스키마로 정확한 키를 확인하고 맞춘다.

## 공유 계약

가드 스크립트는 두 런타임에 동일한 입출력 계약을 유지한다:

- stdin: 도구 호출 JSON (`tool_name`, `tool_input.*`).
- 차단: 비영 종료 + stderr 사유, 또는 런타임이 지원하면 구조적 deny JSON.
- 통과: exit 0, 출력 없음.

이 계약 덕분에 규칙 하나를 한 번 저작해 Claude Code·Codex·pre-commit에 같이 건다. red 증명은 `references/claude-code-hooks.md`의 방법을 그대로 쓴다.
