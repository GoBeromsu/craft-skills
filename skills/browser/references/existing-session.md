# Existing authenticated session

This backend uses the user's current authenticated browser surface when the active runtime exposes one.
It operates on the real profile, tabs, cookies, and sessions; it is not a dedicated automation instance.
Each runtime must discover its own current existing-session surface and verify its connection, intended account, and target-site read access before use.
Do not assume that any runtime exposes this surface, or that an available surface has a portable tool name, namespace, or capability set.

## Runtime discovery

Consult the current official documentation for the active runtime and inspect its currently available native browser or MCP surface before selecting a tool.
Use a native existing-session surface only when both runtime discovery and current documentation prove that it is available for the requested operation.
For Codex, Cursor, Grok, and Hermes, do not invent a command or tool name: absent that evidence, mark existing-session unavailable and return to the router fallback or stop boundary.
Report what was observed, such as no suitable tools, renamed methods, no connection, or unavailable account visibility; do not assert an unobserved cause.

### Claude Code: Claude in Chrome

In Claude Code only, Claude in Chrome may provide an existing-session MCP surface.
Discover it with `/mcp`: select `claude-in-chrome`, then choose **View tools**. Where available, use `ToolSearch` to search that discovered MCP server and select only the task-required tools from its returned inventory.
If discovery returns no suitable tool or the extension is not connected, mark this backend unavailable and return to the router; do not substitute a tool or assert a cause.

Official Anthropic sources:

- [Use Claude Code with Chrome](https://code.claude.com/docs/en/chrome)
- [Get started with Claude in Chrome](https://support.claude.com/en/articles/12012173-getting-started-with-claude-in-chrome)
- [Claude for Chrome permissions guide](https://support.claude.com/en/articles/12902446-claude-for-chrome-permissions-guide)

## Baseline, preflight, and user state

Before setup, record observable existing windows and tabs, the selected profile/account/session, and any user tab required for the task.
Required existing-session work must retain that identity; it cannot fall back to another identity.

Create a new tab only when it is necessary for preflight or the work, and ledger it immediately as task-created.
Before any target-site mutation, prove all of the following: the discovered surface/tools are available, the connection works, the intended account/session is selected, and the target site can be read.
A successful tool-health check alone does not permit a submit, send, publish, edit, delete, purchase, permission change, or equivalent target-site action.

Preserve existing windows, tabs, cookies, sessions, and navigation state.
At normal completion, use the discovered tab-closing tool to close only tabs explicitly opened by the task; preserve and report pre-existing or ambiguous resources.
Never automatically replay a write whose outcome is uncertain.

## Core procedure

1. Use a discovered tab-context tool first to inspect existing tabs. Reuse a user tab when the task concerns it rather than creating or navigating another tab.
2. Use a discovered page-text or page-reading tool to extract text. Do not take a computer-use screenshot or click merely to read a page.
3. Use the discovered interaction or form-input tool for real clicking, typing, scrolling, and form interaction.
4. Use discovered console-message and network-request readers for live-tab debugging without opening DevTools manually.
5. Close only a tab created and ledgered by this task when it is no longer needed.

## Native-dialog guard

Do not blindly use a browser-interaction tool to trigger a native `alert`, `confirm`, or `beforeunload` dialog.
Once such a dialog is open, tool calls can hang because the browser event loop is blocked; a script-evaluation tool cannot inspect it afterward.
Before an action that may prompt, use a discovered script-evaluation tool to pre-empt the dialog when appropriate, for example:

```javascript
window.confirm = () => true
```

If a native dialog is already open, stop and have the user dismiss it manually rather than attempting to inspect or automate it.

## Common failures

- Do not open a new tab for every task; inspect tab context and preserve existing user tabs.
- Do not treat this as a dedicated agent-browser instance; it uses the user's actual authenticated browser state.
- Do not perform a target-site write before baseline capture and complete preflight.
- Do not replay an uncertain write after a tool failure, navigation change, or blocked dialog.
