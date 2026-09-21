---
name: browser
description: Owns personal composition for live authenticated browser work through Aside as the sole managed route. Use when a request says "Use Aside to inspect my logged-in dashboard", "inspect my signed-in dashboard", "open this in my browser", "click this button", "fill out this form", "continue this Aside session", or "브라우저로 열어줘" and the page needs login, JavaScript, or multi-step interaction. Not for static public extraction — use defuddle — or plain JSON API responses — use an HTTP client. Not for rewriting official Aside product usage.
metadata:
  version: 2.0.0
---

# Browser

Compose live authenticated or interactive web work through Aside only.
Official Aside product controls belong to unmodified `aside-browser` and current `aside guide` / installed help.
This package owns personal identity, existing-app protection, owned-resource cleanup, same-session continuation, and observed-result readback.

State the intended account/session, the bound scope, whether the work is read-only or potentially mutating, observed evidence or the last confirmed checkpoint, and cleanup of task-owned resources only.
If Aside is unavailable, identity is unproven, existing work would be disturbed, or a write is uncertain, stop and report the last confirmed checkpoint.
Do not invent a second managed browser route.

## Official owner

For CLI, session resume/steer/queue/stop, effort, MCP, REPL, and other product syntax, run current `aside guide` and installed help after official `aside-browser`.
Do not copy those manuals here.
Current help owns syntax. Official web docs remain useful except where they still describe removed root `--session`; current `aside guide` / installed help win that conflict.
Do not claim official Aside skill absence.

## Personal boundaries

- Protect existing browser apps, profiles, tabs, tasks, cookies, sessions, and data. Do not quit, relaunch, or otherwise disturb unrelated work as a recovery recipe.
- Bind exact account/session identity and target-site scope before any effect. Do not substitute another identity. A successful CLI account command or process exit is not proof the target page is authenticated; confirm the intended signed-in surface.
- Reads need no extra generic approval. Do not replay an uncertain write.
- Native task IDs, acknowledgements, and exit codes are not proof of site success. Confirm the requested screenshot, value, download, or side effect, or report unknown.
- Continue or dedupe only in the same proven Aside session. Do not start a parallel session for the same bound work.
- Close only resources this task created and ledgered. Preserve pre-existing and ambiguous handles. Report cleanup failure without widening the close scope.
- Fallback routing to agent-browser, existing-session, Chrome, or other managed backends is retired. If Aside cannot do the work, stop.


## Requirements

- Official `aside-browser` and current `aside` CLI. Re-probe related official skills and CLI/agent runtimes on create/update using the `skillify` skill's contract §10.
- The `init` skill's tool-preflight reference (`tool-preflight.md` under its references) records Aside install and version probes.

## Boundaries

Use defuddle for static public pages that do not need an authenticated browser session.
Use an HTTP client for direct API or JSON work.
Do not delete installed browser apps, profiles, or user data.
