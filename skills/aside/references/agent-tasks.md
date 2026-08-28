# Aside browser agent — task controls and behavior

Agent-side knowledge for calling the Aside browser agent: task controls, the permission architecture, steering a live run, page context, credentials, routines, Ultrabrowse, memory, models, and recovery.
The `SKILL.md` body covers when to reach for each surface; this file is the depth behind running the agent well.

Provenance: distilled from the Aside Help Center (<https://docs.aside.com/llms.txt> — the tasks, security, automation, ultrabrowse, memory, side-panel, ai, password-manager, and troubleshooting pages), retrieved 2026-07-27.
Aside is a proprietary AI browser; treat these as vendor-documented behaviors, not a stable public API.

## Table of Contents

1. [Task controls](#1-task-controls)
2. [Permission architecture](#2-permission-architecture)
3. [Steering a running task](#3-steering-a-running-task)
4. [Page context via the side panel](#4-page-context-via-the-side-panel)
5. [Credentials and the agent boundary](#5-credentials-and-the-agent-boundary)
6. [Routines](#6-routines)
7. [Ultrabrowse](#7-ultrabrowse)
8. [Memory](#8-memory)
9. [Models and providers](#9-models-and-providers)
10. [Task states and recovery](#10-task-states-and-recovery)

---

## 1. Task controls

Every new task exposes six controls; set them before starting rather than mid-run.

| Control | Options | Notes |
| --- | --- | --- |
| Browser mode | Default / Incognito | Incognito runs without normal profile state and excludes profile data from the transcript; the password manager is unavailable there. |
| Permission mode | Read only / Guard / Full access | See §2; Guard is the default. |
| Working folder | Any folder | Where the task reads and writes; Guard prompts outside it. |
| Model | Plan, subscription, or API-key models | Ultrabrowse appears under `Reasoning` when the account can use it (§7). |
| Follow-up behavior | Queue / Steer | Set at `Settings > AI > Chat settings` (§3). |
| Task description | Free text | State the desired outcome, target sites/files, and constraints for sensitive or financial work. |

During execution a task can browse and search the web, read and write files, search browsing history, request approvals, autofill credentials for authorized accounts, and pause for input or resume after delays.
Regular task transcripts are stored in the task folder; generated files persist until manually deleted, with previews for images, PDFs, HTML, and text.

## 2. Permission architecture

Two layers: agent-wide defaults in `Agent Settings > Permissions`, and a per-task session mode that layers on top.

Agent-wide rule areas: Sandbox, Readable file roots, Writable file roots, Reads outside allowed roots, Writes outside allowed roots, Tool rules, Browser rules, and Network rules.
Each rule takes one of three values — Allow (use without asking), Ask (prompt first), Deny (block) — and Deny holds highest precedence.

Session permission modes for a new task:

| Mode | Behavior |
| --- | --- |
| Read only | Inspect browser and file context without changing files. |
| Guard (default) | Work in approved folders; ask before accessing other folders. |
| Full access | Read and write anywhere on the computer. |

Full access widens file permissions only — it never exposes stored password values (§5).
Default to Guard; drop to Read only for pure evidence-gathering, and grant Full access only when the task must write outside approved folders.

## 3. Steering a running task

Follow-up messages to a running task behave per `Settings > AI > Chat settings`:

- **Steer** injects the message into the active run — use it to correct course in real time, e.g. "Stop using the billing page. Use the invoices page instead, and do not send any emails."
- **Queue** buffers the message until the current run completes — use it for instructions that can wait.

Prefer steering over killing a wayward task; a restarted task loses the run's context and repeats its cost.

## 4. Page context via the side panel

The side panel starts a task from the page being viewed: open the panel, keep or remove the page attachment (title + hostname shown), describe the task, submit.
Keep the attachment when the agent should read or act from that page; remove it for a clean start.
Drafts persist per page context — leaving a page and returning later restores the draft tied to that tab.

## 5. Credentials and the agent boundary

The agent never receives raw password values; Aside fills credentials into the page itself after checking the target URL and the password access settings.

Access policies (global, overridable per item): Always allow, While unlocked, Never.
The password manager is unavailable in incognito sessions.

Steps the agent cannot complete alone — the task pauses for the human: MFA, passkey approvals, CAPTCHAs, and identity verification.
Sensitive actions such as payments, posts, and messages should wait for explicit confirmation when the task asks for approval.

Autofill not appearing → checklist at `Settings > Password`: "Use default password manager" enabled, "Enable Autofill" active, incognito exclusion, excluded-domains list, and insecure-site permission for the target site.

## 6. Routines

Routines run browser work on a schedule without manual kickoff; manage them at `Agent Settings > Routines` (create, edit schedule, pause/resume, delete, run now).

| Type | Behavior | Use for |
| --- | --- | --- |
| Cron routine | Starts a new task on a schedule. | Standalone repeating work, e.g. a weekly summary. |
| Heartbeat routine | Wakes an existing chat and continues it. | Resuming the same conversation with new context. |

Safeguards: overlapping routine runs are skipped, and a routine pauses when its target chat is unavailable.
Limits: 3 active routines on the Free plan, unlimited on Pro.
Aside also proposes draft routines from usage patterns — review, edit, then activate or dismiss; "Find more suggestions" requests more.

## 7. Ultrabrowse

Ultrabrowse is the heavyweight mode for source-heavy research: work needing citations, vendor or product comparisons, migration planning, and security/compliance/pricing checks across several sites.
It appears in the model selector under `Reasoning` when the account can use it (Free-plan users see a Pro upgrade prompt), and browser tasks can also start from the CLI.
Use a standard task for single-page questions or basic searches — Ultrabrowse is wasted there.

## 8. Memory

Aside can use browsing history as context and create memories from chats and task activity.
Controls live at `Agent Settings > Memory`: toggle memory on/off, inspect history, edit or delete saved memories.
Retention options: Never forget, 30 days, 90 days — pick shorter retention to shed day-to-day observations sooner.
Turn memory off when new chats or tasks should not create memories, e.g. sensitive one-off work.

## 9. Models and providers

Three pathways, configured at `Settings > AI`:

- **Aside plan models** — included with the plan; Free gets the basic set, Pro/Max expand access; requires cloud sign-in.
- **Subscription providers** — reuse ChatGPT Plus/Pro, Claude Pro/Max, or GitHub Copilot via OAuth popup.
- **API keys** — Anthropic, OpenAI, OpenRouter, Google, xAI, Vercel AI Gateway, Cloudflare AI Gateway.

Defaults and follow-up behavior are set at `Settings > AI > Chat settings`; model categories at `Settings > AI > Models`.
If the selected Aside account is signed out, built-in plan models fail while connected provider keys keep working.

## 10. Task states and recovery

Task states: waiting for approval, waiting for an answer, errored, finished.

A **waiting** task needs the human: open it, find the input or approval request, answer/approve/reject, complete any visible verification step (sign-in, MFA, passkey, CAPTCHA, identity check), then resume if offered.
A **stuck or wayward** task is corrected with Steer (live) or Queue (after the run) rather than restarted (§3).
A **finished** state is not evidence — confirm the screenshot, value, or side effect the task was supposed to produce.

Report bugs to support@aside.com with the task URL/ID, timestamp, website, expected vs. actual results, and error messages.
