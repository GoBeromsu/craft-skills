# Claude Code 런타임 훅 메커니즘

티어 1 강제의 1차 표면. 에이전트의 도구 호출 수명주기에 결정론적으로 개입한다.

## 이벤트와 차단 가능성

| 이벤트 | 발동 시점 | 차단 가능? |
|---|---|---|
| `PreToolUse` | 도구 실행 **직전** | **예** — 부작용 발생 전에 막는다 |
| `PostToolUse` | 도구 실행 **직후** | 아니오 — 부작용은 이미 일어났고, 피드백만 준다 |
| `UserPromptSubmit` | 프롬프트 제출 시 | 예 (프롬프트 차단) |
| `Stop` / `SubagentStop` | 턴 종료 시 | 예 (계속하도록 강제) |

강제 규칙은 **PreToolUse**에 둔다. PostToolUse는 부작용을 못 막으니 "방금 한 것이 틀렸다"는 사후 신호용일 뿐 — 가역 작업의 교정에는 쓰되, 차단이 필요하면 PreToolUse로 올린다.

## 등록 (settings.json)

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          { "type": "command", "command": "$CLAUDE_PROJECT_DIR/scripts/guard.sh" }
        ]
      }
    ]
  }
}
```

- `matcher`: 도구 이름에 대한 정규식. 대소문자 구분, 알터네이션(`A|B`) 가능. 빈 문자열/생략 = 모든 도구.
- `command`: 셸로 실행된다. `$CLAUDE_PROJECT_DIR`로 repo 루트 기준 경로를 쓴다(절대경로 하드코딩 금지).
- 위치: 프로젝트 `.claude/settings.json` 또는 글로벌 `~/.claude/settings.json`. 커밋된 프로젝트 설정이라야 모든 actor가 동일하게 강제된다.

## stdin 페이로드

command는 stdin으로 JSON을 받는다:

```json
{
  "session_id": "...",
  "tool_name": "Write",
  "tool_input": { "file_path": "/abs/path", "content": "..." }
}
```

`jq`로 뽑는다: `tool_name`, `tool_input.file_path` 등. 도구마다 `tool_input` 스키마가 다르므로 `// ""` 기본값으로 방어한다.

## 차단하는 두 방법

1. **구조적 거부 (권장):** exit 0 + stdout에 JSON.
   ```json
   {
     "hookSpecificOutput": {
       "hookEventName": "PreToolUse",
       "permissionDecision": "deny",
       "permissionDecisionReason": "<위반 규칙 + 고치는 법>"
     }
   }
   ```
   `permissionDecision`: `"deny"`(차단) · `"allow"`(자동승인) · `"ask"`(사용자에게 물음). `permissionDecisionReason`이 에이전트에게 전달되는 교정 신호다 — 규칙과 수정 방법을 한 줄로.

2. **하드 중단:** exit code `2` + stderr에 사유. JSON 없이 즉시 차단, stderr가 에이전트에 전달된다. 거칠지만 단순하다.

그 외 exit code(0 제외)는 비차단 경고로 처리된다.

스타터 구현: `scripts/claude-code-pretooluse-guard.sh`, 등록 예시: `scripts/settings-hooks.example.json`.

## red 증명 (설치 후 필수)

위반/정상 입력을 직접 흘려 발동을 확인한다:

```sh
# 차단되어야 함 (deny JSON 출력)
echo '{"tool_name":"Write","tool_input":{"file_path":"'"$READONLY_PREFIX"'/x"}}' \
  | READONLY_PREFIX=/some/ro/dir scripts/claude-code-pretooluse-guard.sh

# 통과해야 함 (출력 없음, exit 0)
echo '{"tool_name":"Write","tool_input":{"file_path":"/tmp/ok"}}' \
  | READONLY_PREFIX=/some/ro/dir scripts/claude-code-pretooluse-guard.sh
```

차단을 눈으로 보기 전엔 미완이다.
