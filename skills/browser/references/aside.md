# Aside procedure

Use Aside for its signed-in AI browser, not for a static public page or a direct API response.
Consult the [Aside developer documentation](https://docs.aside.com/help/developers) before relying on CLI, MCP, or REPL behavior that is version-dependent or unclear.
Consult the [Aside Help Center index](https://docs.aside.com/llms.txt) for in-app task, permissions, routine, credential, model, and recovery behavior.
Treat unavailable or conflicting vendor details as unknown and follow the router's safe-stop boundary rather than inventing a command.

## Select a surface

| Need | Surface |
|---|---|
| One-off or multi-step natural-language browser work | `aside "<task>"` |
| Continue a known session | `aside --session <session-id> "<task>"` |
| Non-interactive run with an explicit model | `aside exec -m <model> "<task>"` |
| Expose browser control to another agent | `aside mcp` with MCP client configuration |
| Deterministic inspection, screenshots, downloads, or scripted steps | `aside repl "<js>"` |
| Long-running work, a routine, or side-panel page context | Aside in-app task controls |

Use the documented installation path in Aside developer settings or the official developer documentation.
Do not assume a CLI subcommand, argument, or platform behavior not supported by current official or installed-version evidence.

## CLI and account procedure

Start a natural-language task with the smallest clear instruction.

```bash
aside "Open the staging dashboard and screenshot the error banner"
```

Continue a prior session only when its identifier and account are known.

```bash
aside --session <session-id> "Now export the failing rows as CSV"
```

Use the explicit-model form for a scripted non-interactive run when the installed version supports the selected model.

```bash
aside exec -m <model> "Plan this workflow"
```

Inspect the current account before account-sensitive work, and select or target the intended account rather than relying on a default.

```bash
aside account list
aside account status
aside account status <account-id>
aside account use <account-id>
aside --account <account-id> "Summarize this page"
aside exec --account <account-id> -m <model> "Plan this workflow"
```

A signed-out selected account can prevent built-in Aside models from running even when separately configured provider keys work.
Recover by signing in through **Aside Settings > Account** or by choosing a verified signed-in account.
Confirm that the target page is authenticated and that the requested evidence or effect occurred, because a successful command can still land on a login wall.

## MCP and REPL

Run the MCP server with the documented command.

```bash
aside mcp
```

For an MCP client that reads `mcp.json`, use this configuration.

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

When Aside developer settings provide a concrete CLI path, use that configured path for `command` instead of assuming `aside` is on `PATH`.
Use the REPL only for direct browser scripting supported by the installed surface.

```bash
aside repl "const p = await openTab('https://example.com')"
```

Use it for deterministic inspection, screenshots, downloads, or scripted browser steps instead of a free-form agent instruction.

## In-app task guidance

Set browser mode, permission mode, working folder, model, follow-up behavior, and a task description before starting an in-app task.
Default to Guard, use Read only for evidence gathering, and use Full access only when the task needs file writes outside approved folders.
Full access widens file permissions but does not expose stored password values.

Use Steer to correct a running task and Queue for instructions that can wait until the current run completes.
Start from the side panel when the current page should remain attached as task context, and remove the attachment for a clean start.

Aside fills credentials in the page without exposing raw password values to the agent.
Expect MFA, passkeys, CAPTCHAs, and identity verification to require human completion.
Wait for explicit approval before sensitive payments, posts, messages, or equivalent actions.

Manage scheduled work at **Agent Settings > Routines**.
Use a cron routine for a new task on a schedule and a heartbeat routine to continue an existing chat.
Avoid overlapping runs and verify that the target chat remains available.

Use Ultrabrowse only for source-heavy research such as comparisons, migration planning, or security, compliance, and pricing checks across several sites.
Use a standard task for single-page questions or basic searches.
Configure memories, models, and providers through Aside settings, and keep memory disabled for sensitive one-off work when retained context is not needed.

A task waiting for approval or an answer needs human input before it can continue.
For a stuck or wayward task, prefer Steer or Queue over restarting it.
A finished task is not proof of success, so verify the requested screenshot, value, download, or side effect.

## Connection and recovery

Follow the router's baseline, preflight, account, target-read-access, mutation, and cleanup rules before acting through Aside.
On a macOS Aside connection hang, the router requires one immediate full app quit and relaunch even when unrelated work is active.
After relaunch, compare observable logical tabs, tasks, profile, and session state with the pre-restart baseline, report missing or unknown state, and never replay an uncertain target-site write.
