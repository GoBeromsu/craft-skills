# Claude Code Runtime Hook Mechanism

The primary surface for tier-1 enforcement. Intervenes deterministically in the agent's tool-call lifecycle.

## Events and Blockability

| Event | Fires | Can block? |
|---|---|---|
| `PreToolUse` | Immediately **before** the tool runs | **Yes** — stops the side effect before it happens |
| `PostToolUse` | Immediately **after** the tool runs | No — the side effect already happened; feedback only |
| `UserPromptSubmit` | On prompt submission | Yes (blocks the prompt) |
| `Stop` / `SubagentStop` | At turn end | Yes (forces continuation) |

Put blocking rules on **PreToolUse**. `PostToolUse` cannot stop a side effect — use it for "what you just did was wrong" signals on reversible work, and move anything that needs to block up to `PreToolUse`.

## Registration (settings.json)

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

- `matcher`: a regex over tool names. Case-sensitive; alternation (`A|B`) works. Empty/omitted = every tool.
- `command`: runs in a shell. Use `$CLAUDE_PROJECT_DIR` for repo-root-relative paths — never hardcode an absolute path.
- Location: project `.claude/settings.json` or global `~/.claude/settings.json`. Only a committed project setting enforces identically for every actor.

## stdin Payload

The command receives JSON on stdin:

```json
{
  "session_id": "...",
  "tool_name": "Write",
  "tool_input": { "file_path": "/abs/path", "content": "..." }
}
```

Pull fields with `jq`: `tool_name`, `tool_input.file_path`, etc. `tool_input`'s schema varies by tool, so guard with a `// ""` default.

## Two Ways to Block

1. **Structured deny (recommended):** exit 0 + JSON on stdout.
   ```json
   {
     "hookSpecificOutput": {
       "hookEventName": "PreToolUse",
       "permissionDecision": "deny",
       "permissionDecisionReason": "<violated rule + how to fix it>"
     }
   }
   ```
   `permissionDecision`: `"deny"` (block) · `"allow"` (auto-approve) · `"ask"` (ask the user). `permissionDecisionReason` is the correction signal reaching the agent — state the rule and the fix in one line.

2. **Hard abort:** exit code `2` + reason on stderr. Blocks immediately with no JSON; stderr reaches the agent. Blunt but simple.

Any other non-zero exit code is treated as a non-blocking warning.

Starter implementation: `scripts/claude-code-pretooluse-guard.sh`, registration example: `scripts/settings-hooks.example.json`.

## Proving It Red (required after install)

Run a violating/clean input directly and watch it fire:

```sh
# should block (deny JSON printed)
echo '{"tool_name":"Write","tool_input":{"file_path":"'"$READONLY_PREFIX"'/x"}}' \
  | READONLY_PREFIX=/some/ro/dir scripts/claude-code-pretooluse-guard.sh

# should pass (no output, exit 0)
echo '{"tool_name":"Write","tool_input":{"file_path":"/tmp/ok"}}' \
  | READONLY_PREFIX=/some/ro/dir scripts/claude-code-pretooluse-guard.sh
```

Unfinished until you've seen the block with your own eyes.
