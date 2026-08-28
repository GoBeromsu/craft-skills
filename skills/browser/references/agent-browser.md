# agent-browser

`agent-browser` is the vercel-labs native Rust CLI for deterministic browser automation through CDP.
It drives a dedicated Chrome instance, not the user's already-open Chrome session.
Its interaction contract is snapshot refs (`@e1`, `@e2`, ...), not guessed selectors.

Upstream: https://github.com/vercel-labs/agent-browser

## Session and account model

This backend has its own browser instances and sessions.
Before setup, record observable existing instances, sessions, handles, and the intended identity.
Preserve all pre-existing instances, sessions, and user browser state.

Use `--profile <name|path>` only when existing authenticated Chrome cookies are required.
Use `--session <name> --restore` for a dedicated persistent session.

`--restore` automatically saves and restores that session's cookies and localStorage.
Use `--restore-save <auto|always|never>` to control when that save occurs.
`--state <path>` loads an explicit state file; `--auto-connect state save <path>` exports state from an already-connected authenticated browser.
Never hardcode credentials in commands; use headers/environment or `agent-browser auth save` / `agent-browser auth login`.

## Preflight and ownership

Before any target-site mutation, capture the baseline, then create or select only the minimal reversible instance, session, or tab required to establish connection, intended account/session, and read-only target-site access.
Ledger every newly created handle as task-owned immediately.
Tool health alone is not sufficient: installation, connection, intended identity/session, and read-only target access must all succeed before a submit, send, publish, edit, delete, purchase, permission change, or equivalent action.

The router controls startup fallback.
Do not silently select another backend here.
No additional restart policy applies to agent-browser.

During normal finalization, close only task-created dedicated instances, sessions, or tabs.
Preserve and report pre-existing or ambiguously owned resources.
If a write's result is uncertain, report the last confirmed state and never replay it automatically.

## Core procedure

1. Start or navigate the task-owned dedicated browser:

   ```bash
   agent-browser open <url>
   ```

2. Take a snapshot before interaction:

   ```bash
   agent-browser snapshot
   ```

3. Act on refs returned by that snapshot:

   ```bash
   agent-browser click @e2
   agent-browser fill @e3 "text"
   ```

A semantic locator is available when a stable ref is not yet known:

   ```bash
   agent-browser find role button click --name "Submit"
   ```

4. Re-snapshot after every navigation or DOM-changing action. Refs from the prior snapshot are stale and must not be reused.

5. Capture visual evidence when required:

   ```bash
   agent-browser screenshot [path]
   ```

6. Close the task-created session when work is complete:

   ```bash
   agent-browser close
   ```

The daemon otherwise persists and auto-exits only after one hour idle.

## MCP and isolation

For programmatic use by another coding agent, start the MCP server with the narrowest needed tool profile:

```bash
agent-browser mcp --tools core,network,react
```

Available profiles are `core`, `network`, `state`, `debug`, `tabs`, `react`, `mobile`, and `all`.
Use `--session <name>` to isolate concurrent work rather than racing the default session.

## Common failures

- Never guess a CSS selector from memory; snapshot first and use the returned ref.
- Never reuse a ref after navigation or a DOM change; take a fresh snapshot.
- Do not treat this dedicated browser as the user's existing Chrome session.
- Do not leave task-created browser work running: use `agent-browser close`, while preserving anything that existed before the task.
