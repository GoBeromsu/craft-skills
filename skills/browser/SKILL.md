---
name: browser
description: Routes live-browser work across Aside, agent-browser, and an existing authenticated browser session. Use when a request says "Use Aside to inspect my logged-in dashboard", "inspect my signed-in dashboard", "open this in my browser", "click this button", "fill out this form", "use agent-browser", or "브라우저로 열어줘" and the page needs login, JavaScript, or multi-step interaction. Not for static public extraction — use defuddle — or plain JSON API responses — use an HTTP client.
metadata:
  version: 1.1.0
---

# Browser

Drive authenticated or interactive web work through one backend while protecting account identity, existing browser state, and uncertain writes.
Success means the selected backend reaches the intended account and target read state before any target-site mutation, and finalization preserves every resource not created by this task.

## Procedure references

- [Aside procedure](references/aside.md) covers the Aside CLI, MCP, REPL, and in-app task controls.
- [agent-browser procedure](references/agent-browser.md) covers dedicated-instance automation.
- [Existing-session procedure](references/existing-session.md) covers the user's current authenticated browser surface.

## Route and preflight

Classify the request as read-only or potentially mutating, record an explicitly requested browser tool, and record whether an existing authenticated browser session is required.
The explicitly user-requested tool wins; do not silently substitute another backend.
When no tool is requested and an existing authenticated browser session is required, use existing-session.
Otherwise use Aside.

Before setup, capture the observable baseline for the candidate: processes, instances, tabs, tasks, selected profile, intended account/session, task-required state, and unrelated active work exposed by the supported surface.
For Aside, include observable task-required and unrelated tabs, tasks, profile, and session identifiers.
Record unavailable fields as unknown rather than inferring them.

Create or select only the minimal reversible process, instance, task, window, or tab needed to establish connection and read access.
Ledger every newly created handle as task-owned when it is created.
Do not mutate the target site during baseline or setup.

Complete preflight by proving installation, connection, the intended account/session, and read-only access to the target site.
A healthy tool alone is insufficient.
Permit target-site mutation only after all four checks pass.

For a default Aside startup failure, try agent-browser and then existing-session, repeating baseline, setup, and preflight for each candidate.
Do not silently replace an explicitly requested backend.
Do not replace required existing-session work with a different account or identity.

## Aside connection-hang recovery

Treat a running Aside connection hang separately from normal cleanup.
On macOS, fully quit and relaunch Aside immediately once, even when unrelated Aside work exists or its recoverability cannot be proven.
Do not use this restart as cleanup and do not replay a target-site action during recovery.
On another operating system, use an equivalent restart only when official documentation or installed-state evidence supports it; otherwise handle the condition as startup-unavailable.

After relaunch, reconnect and compare observable tabs, tasks, profile, session, and account identifiers with the baseline.
Verify the intended account/session and required task state without requiring the old process identity.
Report every missing, changed, unobservable, or unrecovered item.
Missing recovery evidence prevents further target-site mutation but does not reverse the required macOS restart.

After an unrecovered hang or state, read-only fallback may use another backend only after proving the same target-site account and resuming at the last confirmed checkpoint.
For potentially mutating work, report the last confirmed checkpoint, missing or unrecovered state, and every uncertain action, then stop.
Never auto-replay an uncertain write.

## Evidence for mutable tools

For an external CLI, API, service, or runtime fact that is unknown, ambiguous, or version-dependent, consult official primary documentation first rather than inferring it from memory or nearby prose.
State the relevant version and platform boundary when available.
When sources conflict, disclose the conflict and prefer a more-specific repository-local contract for this repository's behavior or matching-version and platform reproducible runtime evidence over general or stale documentation.
When official material is unavailable or qualifying evidence does not resolve the fact, label it unknown and follow the safe stop or fallback boundary.
Do not invent commands, capabilities, or platform promises.

## Finalize

Close only terminable handles ledgered as task-created.
Preserve pre-existing and ambiguous processes, instances, tabs, tasks, windows, cookies, sessions, and navigation state.
Report a cleanup failure without broadening the close scope.

## Boundaries

Use defuddle for static public pages that do not need an authenticated browser session.
Use an HTTP client for direct API or JSON work.
