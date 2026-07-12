# Aside developer surfaces — command reference

Full command reference for the three Aside developer surfaces. The `SKILL.md` body
covers when to reach for each; this file is the exhaustive syntax.

Provenance: command syntax mirrors Aside's official developer docs
(<https://docs.aside.com/help/developers>), retrieved 2026-07-13. Aside is a proprietary
AI browser; treat these as the vendor's documented surfaces, not a stable public API.

## Install the CLI

The developer settings page shows this install command:

```bash
curl -fsSL https://releases.aside.com/install.sh | bash
```

The Aside app's developer settings page can also install, update, or reinstall the CLI
directly. If settings surfaced a concrete CLI path, prefer that absolute path (see MCP,
below) over relying on `PATH`.

## Run a browser task

Start a browser-agent session from the terminal with a natural-language instruction:

```bash
aside "Open localhost:3000 and run a smoke test"
```

Continue an existing session with `--session`:

```bash
aside --session <session-id> "Continue"
```

Non-interactive exec form (script it, pick a model):

```bash
aside exec -m openai-codex/gpt-5.5 "Plan this workflow"
```

## Manage accounts

If more than one Aside account is signed in on the device, each command runs under one
selected account. Inspect, switch, or target accounts:

```bash
aside account list            # list accounts; the current one is marked with *
aside account status          # show the current account
aside account status u1       # check a specific account by ID
aside account use u1          # set the default account for future commands
```

Target a single run at a specific account with `--account`. It works on both `aside` and
`aside exec`:

```bash
aside --account u1 "Summarize the current page"
aside exec --account u1 -m openai-codex/gpt-5.5 "Plan this workflow"
```

If the selected account is signed out, the CLI prints a recovery warning. Your own
provider keys (OpenAI, Anthropic) keep working, but built-in Aside models require an
active sign-in. Recover by signing in again from **Aside Settings > Account**, or switch
to a signed-in account with `aside account use <id>` or `--account <id>`.

## Use as an MCP server

Expose Aside to another agent or coding tool over the Model Context Protocol:

```bash
aside mcp
```

For clients that read `mcp.json`, register it:

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

If developer settings surfaced a concrete CLI path, use that absolute path for `command`
instead of the bare `aside` name. Aside can also install browser-automation setup for
supported coding tools directly from developer settings.

## Use the REPL

Run browser-automation REPL snippets — JavaScript evaluated against a live browser:

```bash
aside repl "const p = await openTab('https://example.com')"
```

Reach for the REPL when a task needs direct page inspection, screenshots, downloads, or
deterministic, scripted browser steps rather than a free-form agent instruction.

## Surface selection

| Need | Surface |
| --- | --- |
| One-off or multi-step task in natural language | `aside "<task>"` |
| Continue prior work | `aside --session <id> "<task>"` |
| Scripted / non-interactive run, explicit model | `aside exec -m <model> "<task>"` |
| Let another agent drive the browser | `aside mcp` + `mcp.json` |
| Deterministic page inspection, screenshots, downloads | `aside repl "<js>"` |
