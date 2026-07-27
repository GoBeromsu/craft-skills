---
name: aside
description: Drive the Aside AI browser as a browser agent — in-app tasks and the side panel, or the terminal via its CLI, MCP server, and automation REPL — to do real work inside logged-in, authenticated web apps that a plain fetch can't reach. Use when calling the aside agent for a long multi-step browser task, choosing a task permission mode (Read only, Guard, Full access), scheduling a recurring routine, picking Ultrabrowse for source-heavy research, unsticking a task stuck waiting for approval, gathering evidence from a signed-in dashboard, or wiring Aside into another coding agent via mcp.json. Not for static public pages (use defuddle) or plain JSON API responses (use an HTTP fetch).
metadata:
  version: 1.1.0
---

# aside

## Overview

Aside is an AI browser whose agent runs real work inside a signed-in browser: pages behind a login, JavaScript-rendered dashboards, and multi-step flows inside authenticated web apps.
Call the agent from inside the app (a task or the side panel) or from the terminal through three developer surfaces: the `aside` CLI, an MCP server (`aside mcp`), and a browser-automation REPL (`aside repl`).
Success looks like the evidence or side effect you needed — a screenshot, a value read off a dashboard, a form submitted — produced under the right account and the narrowest permissions that let the task finish.

## When to Use

- Gathering evidence from a signed-in page — a CI run log, feature-flag console, Datadog trace, internal admin panel, or a staging screenshot — beyond a plain fetch's reach
- Running a long multi-step agent task across authenticated web apps (email, dashboards, internal tools), including tasks that read or write local files
- Scheduling recurring browser work as a routine, or source-heavy multi-site research via Ultrabrowse
- Wiring Aside into another coding agent as an MCP server so that agent can drive the browser
- Deterministic page inspection, screenshots, or downloads via the REPL

**NOT for:**
- Static, public, readable pages (blog post, docs, README) — use `defuddle`, which returns clean Markdown without spinning up a browser
- Plain JSON API responses or endpoints — use a plain HTTP fetch
- A page that a `curl` + `defuddle` pass already handles — reserve the browser for work that genuinely needs a login or JS rendering

## Process

### 1. Confirm the task actually needs a browser

Before reaching for Aside, ask whether a login or JavaScript rendering is truly required.
If the page is public and readable, `defuddle parse <url> --markdown` is cheaper and cleaner.
Aside earns its cost only when the work is behind authentication or needs real browser interaction.

### 2. Pick the surface

| Need | Surface |
| --- | --- |
| Task about the page you are viewing | Side panel, keeping the page attachment |
| One-off / multi-step task in natural language | `aside "<task>"` or an in-app task |
| Continue prior work in the same session | `aside --session <id> "<task>"` |
| Scripted, non-interactive run with an explicit model | `aside exec -m <model> "<task>"` |
| Recurring scheduled work | A routine (`Agent Settings > Routines`) |
| Source-heavy research needing citations | Ultrabrowse (model selector, under `Reasoning`) |
| Let another agent drive the browser | `aside mcp` + an `mcp.json` entry |
| Deterministic inspection, screenshots, downloads | `aside repl "<js>"` |

### 3. Scope the run before starting

Each task starts with six controls; the two that matter most are the permission mode and the working folder.
Keep Guard (the default: work in approved folders, ask elsewhere), drop to Read only for pure evidence-gathering, and grant Full access only when the task must write outside approved folders.
Use Incognito mode when the run should leave no profile state — the password manager is unavailable there.
Agent-wide defaults (sandbox, file roots, tool/browser/network rules as Allow/Ask/Deny) live in `Agent Settings > Permissions`; the task's session mode layers on top.
Full controls, permission architecture, and credential boundaries: `references/agent-tasks.md`.

### 4. Run and steer

```bash
aside "Open the staging dashboard and screenshot the error banner"
aside --session <session-id> "Now export the failing rows as CSV"
```

For the REPL, snippets are JavaScript evaluated against a live browser:

```bash
aside repl "const p = await openTab('https://example.com')"
```

While a task runs, follow-ups behave per `Settings > AI > Chat settings`: Steer injects into the live run (use it to correct course), Queue waits for the current run to finish.
A task that stops is usually waiting, not broken: open it and look for an approval, a question, or a human-only step — MFA, passkeys, CAPTCHAs, and identity checks cannot be automated, and sensitive actions like payments, posts, and messages wait for your explicit approval.

### 5. Select the right account

Every command runs under one selected Aside account.
When more than one is signed in, make the target explicit rather than trusting the default:

```bash
aside account list                       # * marks the current account
aside account use u1                      # set the default
aside --account u1 "Summarize this page"  # target one run without changing the default
```

If the selected account is signed out, built-in Aside models fail while your own provider keys keep working — sign in from **Aside Settings > Account** or switch with `aside account use <id>`.

### 6. Verify the result

Confirm the browser actually reached the authenticated state and produced the evidence — a non-empty screenshot, the expected value, a completed side effect.
A browser agent that silently landed on a login wall, or a task showing "finished" without its artifact, has not done the task.

See `references/developer-surfaces.md` for the full command reference, MCP setup, and account details; `references/agent-tasks.md` for task controls, permissions, steering, routines, Ultrabrowse, memory, credentials, and recovery.

## Wiring Aside into another agent (MCP)

```json
{
  "mcpServers": {
    "aside": {
      "command": "aside",
      "args": ["mcp"]
    }
  }
}
```

If Aside's developer settings surfaced a concrete CLI path, use that absolute path for `command` instead of the bare `aside` name.

## Requirements

- `aside` CLI on `PATH` (or an absolute path from Aside developer settings), installed via `curl -fsSL https://releases.aside.com/install.sh | bash`
- A signed-in Aside account for built-in models, **or** your own OpenAI/Anthropic provider keys configured in Aside
- For MCP use: a client that reads `mcp.json`

## Anti-patterns

- Reaching for Aside on a static public page → use `defuddle`; reserve the browser for login or JS-rendered work.
- `curl`-then-parse on a page behind a login or JS rendering → it lands on a wall; run it through Aside.
- Trusting whichever account is default for account-sensitive work → check `aside account list` and target with `--account`.
- Treating a zero exit code or a "finished" task state as proof → verify the evidence: the screenshot, the value, the side effect.
- Hardcoding the bare `aside` command in `mcp.json` when developer settings gave a concrete path → use the absolute path.
- Granting Full access to a task that only reads → keep Guard or Read only; widen only when the task must write outside approved folders.
- Killing and restarting a stalled task → open it first; it is usually waiting for approval, an answer, or a human-only step, and a live run is corrected with Steer.
- Expecting the agent to get through MFA, passkeys, or CAPTCHAs alone, or letting it fire payments, posts, or messages unreviewed → the former pause for the human by necessity, the latter wait for explicit approval by policy; plan the task around both.

## Verification

- [ ] The task genuinely needs a login or JS rendering (else `defuddle` / a fetch was used)
- [ ] The permission mode matches the work — Read only or Guard unless writes outside approved folders were needed
- [ ] The correct account was selected (`account list` / `use` / `--account`)
- [ ] The run produced the expected evidence or side effect, verified beyond the exit code or task state
- [ ] For MCP use, the `mcp.json` `command` points at a working `aside` path
