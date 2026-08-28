# Chrome

Claude in Chrome can expose an MCP surface for the user's own already-open, authenticated Chrome browser.
It operates on that real profile, its tabs, cookies, and sessions; it is not a separate automation instance.
This procedure applies only when the current runtime has connected the Claude in Chrome integration; it does not promise a portable tool inventory across Claude Code, Claude Cowork, or other runtimes.

## Deferred tool loading

Discover the available Chrome tools at runtime before using this procedure. In Claude Code, run `/mcp`, select `claude-in-chrome`, then choose **View tools**. Where the runtime provides `ToolSearch`, search the discovered Claude-in-Chrome MCP server and select the task-required tools from the returned inventory.

Do not assume tool names, namespaces, or a complete core set from this reference: they are runtime- and installed-version-specific. If discovery returns no suitable tools, report exactly what was observed (no tools returned, renamed methods, or an extension connection problem) and stop; do not assert a single cause or substitute another backend.
The router owns fallback decisions.

## Baseline, preflight, and user state

Before setup, record observable existing windows and tabs, the selected profile/account/session, and any user tab required for the task.
Existing Chrome-session work must retain that identity; it cannot fall back to another identity.

Create a new tab only when it is necessary for preflight or the work, and ledger it immediately as task-created.
Before any target-site mutation, prove all of the following: the extension/tools are available, the connection works, the intended account/session is selected, and the target site can be read.
A successful tool-health check alone does not permit a submit, send, publish, edit, delete, purchase, permission change, or equivalent target-site action.

Preserve existing windows, tabs, cookies, sessions, and navigation state.
At normal completion, use the discovered tab-closing tool to close only tabs explicitly opened by the task; preserve and report pre-existing or ambiguous resources.
Never automatically replay a write whose outcome is uncertain.

## Core procedure

1. Use the discovered tab-context tool first to inspect existing tabs. Reuse a user tab when the task concerns it rather than creating or navigating another tab.
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
- Do not treat this as a dedicated agent-browser instance; it uses the user's actual authenticated Chrome state.
- Do not perform a target-site write before baseline capture and complete preflight.
- Do not replay an uncertain write after a tool failure, navigation change, or blocked dialog.

## Official sources

- [Use Claude Code with Chrome](https://code.claude.com/docs/en/chrome) — current Claude Code connection, runtime, and MCP-discovery guidance.
- [Get started with Claude in Chrome](https://support.claude.com/en/articles/12012173-getting-started-with-claude-in-chrome) — installation, availability, and extension capabilities.
- [Claude for Chrome permissions guide](https://support.claude.com/en/articles/12902446-claude-for-chrome-permissions-guide) — permission behavior and user controls.
