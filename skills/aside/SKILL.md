---
name: aside
description: Drive the Aside AI browser from the terminal — its CLI, MCP server, or automation REPL — to do real work inside logged-in, authenticated web apps that a plain fetch or static extractor can't reach. Use when a task needs evidence from a signed-in browser page (a CI dashboard, feature-flag console, Datadog trace, internal admin panel, or staging screenshot), when acting across authenticated sites (email, dashboards, internal tools) as a persistent browser agent, or when wiring Aside into another coding agent as an MCP server via mcp.json. Not for extracting static public pages (use defuddle) or plain JSON API responses (use an HTTP fetch).
metadata:
  version: 1.0.0
---

# aside

## Overview

Aside is an AI browser that ships three developer surfaces: a `aside` CLI, an MCP server
(`aside mcp`), and a browser-automation REPL (`aside repl`). It drives a real, signed-in
browser, so it reaches work that a plain HTTP fetch or a static content extractor cannot:
pages behind a login, JavaScript-rendered dashboards, and multi-step flows inside
authenticated web apps. Success looks like getting the evidence or side effect you needed
from a live browser session — a screenshot, a value read off a dashboard, a form
submitted — with the right account and the least ceremony.

## When to Use

- Gathering evidence from a signed-in page — a CI run log, feature-flag console, Datadog
  trace, internal admin panel, or a staging screenshot — that a fetch can't authenticate to
- Running a multi-step task inside an authenticated web app (email, dashboards, internal tools)
- Wiring Aside into another coding agent as an MCP server so that agent can drive the browser
- Deterministic page inspection, screenshots, or downloads via the REPL

**NOT for:**
- Static, public, readable pages (blog post, docs, README) — use `defuddle`, which returns
  clean Markdown without spinning up a browser
- Plain JSON API responses or endpoints — use a plain HTTP fetch
- A page that a `curl` + `defuddle` pass already handles — reserve the browser for work that
  genuinely needs a login or JS rendering

## Process

### 1. Confirm the task actually needs a browser

Before reaching for Aside, ask whether a login or JavaScript rendering is truly required.
If the page is public and readable, `defuddle parse <url> --markdown` is cheaper and
cleaner. Aside earns its cost only when the work is behind authentication or needs real
browser interaction.

### 2. Pick the surface

| Need | Command |
| --- | --- |
| One-off / multi-step task in natural language | `aside "<task>"` |
| Continue prior work in the same session | `aside --session <id> "<task>"` |
| Scripted, non-interactive run with an explicit model | `aside exec -m <model> "<task>"` |
| Let another agent drive the browser | `aside mcp` + an `mcp.json` entry |
| Deterministic inspection, screenshots, downloads | `aside repl "<js>"` |

### 3. Run the task

```bash
aside "Open the staging dashboard and screenshot the error banner"
aside --session <session-id> "Now export the failing rows as CSV"
```

For the REPL, snippets are JavaScript evaluated against a live browser:

```bash
aside repl "const p = await openTab('https://example.com')"
```

### 4. Select the right account

Every command runs under one selected Aside account. When more than one is signed in,
make the target explicit rather than trusting the default:

```bash
aside account list                       # * marks the current account
aside account use u1                      # set the default
aside --account u1 "Summarize this page"  # target one run without changing the default
```

If the selected account is signed out, built-in Aside models fail while your own provider
keys keep working — sign in from **Aside Settings > Account** or switch with
`aside account use <id>`.

### 5. Verify the result

Confirm the browser actually reached the authenticated state and produced the evidence —
a non-empty screenshot, the expected value, a completed side effect. A browser agent that
silently landed on a login wall has not done the task.

See `references/developer-surfaces.md` for the full command reference, MCP setup, and
account details.

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

If Aside's developer settings surfaced a concrete CLI path, use that absolute path for
`command` instead of the bare `aside` name.

## Requirements

- `aside` CLI on `PATH` (or an absolute path from Aside developer settings), installed via
  `curl -fsSL https://releases.aside.com/install.sh | bash`
- A signed-in Aside account for built-in models, **or** your own OpenAI/Anthropic provider
  keys configured in Aside
- For MCP use: a client that reads `mcp.json`

## Common Rationalizations

| Rationalization | Reality |
| --- | --- |
| "I'll just `curl` the page and parse it." | If it needs a login or JS rendering, `curl` lands on a wall. Use Aside; if it doesn't, use `defuddle`. |
| "Whichever account is default is fine." | Commands run under one account. For anything account-sensitive, target it with `--account`. |
| "The command exited 0, so it worked." | A browser agent can exit clean while stuck on a login page. Verify the evidence, not just the exit code. |
| "Aside is my default web reader." | For static readable pages, `defuddle` is cheaper and cleaner. Aside is for authenticated or interactive work. |

## Red Flags

- Reaching for Aside on a static public page that `defuddle` would extract more cheaply
- Running an account-sensitive task without checking `aside account list` first
- Treating a zero exit code as proof, without confirming the browser reached the intended state
- Hardcoding the bare `aside` command in `mcp.json` when developer settings gave a concrete path

## Verification

- [ ] The task genuinely needs a login or JS rendering (else `defuddle` / a fetch was used)
- [ ] The correct account was selected (`account list` / `use` / `--account`)
- [ ] The run produced the expected evidence or side effect, verified beyond the exit code
- [ ] For MCP use, the `mcp.json` `command` points at a working `aside` path
