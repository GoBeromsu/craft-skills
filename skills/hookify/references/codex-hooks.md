# Codex CLI Runtime Hook Mechanism

Codex's tool-call hooks follow the same model as Claude Code: a command fires before the tool call, receives the call payload on stdin, and a non-zero exit blocks it. Reuse the same guard script across both runtimes.

## Registration (config.toml)

Register under the `[hooks]` block in project `.codex/config.toml` or global `~/.codex/config.toml`:

```toml
[hooks.pre_tool_use]
match = "edit|apply_patch|write"
command = "${CODEX_PROJECT_DIR}/scripts/guard.sh"
```

- `match`: matches the file-mutating tool names your Codex build exposes (edit/apply_patch/write).
- `command`: runs in a shell. Use a project-root env var instead of a hardcoded absolute path.

Starter: `scripts/codex-hook.example.toml`.

## Version Caveat

Codex's hook field names and event spec move by build (`pre_tool_call`/`pre_tool_use`, `notify`, etc.). The shape above is a **portable intent, not a frozen API** — check `codex --help` and your installed config schema for the exact keys and match them.

## Shared Contract

The guard script keeps the same input/output contract across both runtimes:

- stdin: the tool-call JSON (`tool_name`, `tool_input.*`).
- block: non-zero exit + reason on stderr, or a structured deny JSON if the runtime supports it.
- pass: exit 0, no output.

This contract is what lets one guard, authored once, run under Claude Code, Codex, and pre-commit. Prove it red the same way as `references/claude-code-hooks.md`.
