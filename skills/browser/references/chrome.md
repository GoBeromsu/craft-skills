# Chrome

The Claude-in-Chrome extension exposes the `mcp__claude-in-chrome__*` MCP surface for the user's own already-open, authenticated Chrome browser.
It operates on that real profile, its tabs, cookies, and sessions; it is not a separate automation instance.

## Deferred tool loading

When Chrome MCP tools are deferred for the session, load the complete core set in one `ToolSearch` call before using this procedure:

```text
select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__computer,mcp__claude-in-chrome__read_page,mcp__claude-in-chrome__get_page_text,mcp__claude-in-chrome__tabs_create_mcp,mcp__claude-in-chrome__tabs_close_mcp
```

Add clearly needed task-specific tools to that same call: `read_console_messages`, `read_network_requests`, `form_input`, `gif_creator`, or `javascript_tool`.
Do not load tools one at a time across separate round trips.
If discovery returns no tools, report exactly what was observed (no tools returned, renamed methods, or an extension connection problem) and stop; do not assert a single cause or substitute another backend.
The router owns fallback decisions.

## Baseline, preflight, and user state

Before setup, record observable existing windows and tabs, the selected profile/account/session, and any user tab required for the task.
Existing Chrome-session work must retain that identity; it cannot fall back to another identity.

Create a new tab only when it is necessary for preflight or the work, and ledger it immediately as task-created.
Before any target-site mutation, prove all of the following: the extension/tools are available, the connection works, the intended account/session is selected, and the target site can be read.
A successful tool-health check alone does not permit a submit, send, publish, edit, delete, purchase, permission change, or equivalent target-site action.

Preserve existing windows, tabs, cookies, sessions, and navigation state.
At normal completion, close only tabs explicitly opened by the task with `tabs_close_mcp`; preserve and report pre-existing or ambiguous resources.
Never automatically replay a write whose outcome is uncertain.

## Core procedure

1. Call `tabs_context_mcp` first to inspect existing tabs. Reuse a user tab when the task concerns it rather than creating or navigating another tab.
2. Use `read_page` or `get_page_text` to extract text. Do not take a computer-use screenshot or click merely to read a page.
3. Use `computer` for real clicking, typing, and scrolling; use `form_input` for form interaction.
4. Use `read_console_messages` and `read_network_requests` for live-tab debugging without opening DevTools manually.
5. Close only a tab created and ledgered by this task when it is no longer needed.

## Native-dialog guard

Do not blindly use `computer` to trigger a native `alert`, `confirm`, or `beforeunload` dialog.
Once such a dialog is open, tool calls can hang because the browser event loop is blocked; `javascript_tool` cannot inspect it afterward.
Before an action that may prompt, use `javascript_tool` to pre-empt the dialog when appropriate, for example:

```javascript
window.confirm = () => true
```

If a native dialog is already open, stop and have the user dismiss it manually rather than attempting to inspect or automate it.

## Common failures

- Do not open a new tab for every task; inspect tab context and preserve existing user tabs.
- Do not treat this as a dedicated agent-browser instance; it uses the user's actual authenticated Chrome state.
- Do not perform a target-site write before baseline capture and complete preflight.
- Do not replay an uncertain write after a tool failure, navigation change, or blocked dialog.
