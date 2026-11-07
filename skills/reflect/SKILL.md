---
name: reflect
description: "Reviews durable learnings from the current session through judgment, tooling, and divergent lenses, then routes each accepted learning to an edit on an existing skill. Use for \"reflect\", \"/reflect\", \"what did this session teach us\", or \"capture the workflow lessons from this conversation\". Reads a current-session source only when the runtime exposes it and presents edits for approval. Not for enforcing repeated repository mistakes - use correct; not for recovering older sessions - use recall."
metadata:
  version: 1.1.0
---

# Reflect

Mine the current conversation for durable learnings, then route them into skill edits.

Invoke when the user says "reflect" or "/reflect". Skip when the conversation is trivial, off-topic, or already covered by an existing skill the parent followed correctly. One-offs are not learnings.

## 1. Locate the active transcript

Before fanning out, find this conversation's transcript in the transcript directory the system prompt names for the active workspace. Do not glob across workspaces. That crosses workspace boundaries and reads private chats from unrelated projects.

```bash
ls -t <transcripts>/*.jsonl <transcripts>/*/*.jsonl <transcripts>/*/subagents/*.jsonl 2>/dev/null | head -10
```

That covers the legacy flat (`<id>.jsonl`), current nested (`<id>/<id>.jsonl`), and subagent (`<parent>/subagents/<child>.jsonl`) layouts. For each candidate, read the first JSONL line. Take the file whose `message.content[0].text` contains the conversation's opening user prompt. If none matches, pass a tight digest of the session instead.

## 2. Spawn three reviewers in parallel

One message, three general-purpose subagents, agent mode (not readonly). Reviewers need MCP access to look up the tickets, chat threads, and observability traces the transcript references, and readonly strips MCPs.

| Lens | Model | Prompt template |
|---|---|---|
| Judgment | Use the most capable setting available; this role runs once and weighs evidence. | `references/judgment-reviewer.md` |
| Tooling | Use the fastest, cheapest setting that still reads and reports accurately; this role runs many times over broad material. | `references/tooling-reviewer.md` |
| Divergent | Use the most capable setting available; this role runs once and weighs evidence. | `references/divergent-reviewer.md` |

Pick each subagent's reasoning level and fast or standard speed for the job, per the Subagents section of the **craft-mode** skill.

Pass each template verbatim, substituting the transcript path or digest where marked. Reviewers return findings in the subagent response body.

## 3. Synthesize

One general-purpose subagent, agent mode (not readonly), on the most capable setting available; this role runs once and weighs evidence. It spot-verifies citations through MCP, and readonly strips MCPs. Pass `references/synthesizer.md` verbatim, with each reviewer's full output inlined where marked. It returns an Accepted / Rejected / Backlog list.

## 4. Structural enforcement check

Move any Accepted item that a lint rule, script, metadata flag, or runtime check would enforce more reliably to Backlog. See the `correct/references/encode-lessons-in-structure.md` principle.

## 5. Apply

Present the synthesizer's full Accepted / Rejected / Backlog output and wait for explicit approval before applying any Accepted edit. The user picks the subset and may redirect routings. Skill changes affect every future agent in the org. Do not auto-apply.

File each Backlog item to your team's devex or backlog tracker without waiting. Only the Accepted list waits for approval.

Never edit a skill inside an installed plugin cache. Before approval, show its destination, the runtime's project or user skill directory. After approval, copy the skill folder there and edit the copy. Never open a PR or push.

Follow each approved row's Routing exactly:

- Trivial existing-skill edit (a one-line bullet, a tightened sentence, a stale fact corrected): the parent does it directly.
- Substantive existing-skill edit (a new section, a new pattern table, more than ~10 lines): hand to the runtime's skill-authoring workflow and run its draft / test / iterate loop.
- `tune description: <skill path>` (the skill exists but didn't trigger when it should have): hand to the runtime's skill-authoring workflow and run its description-optimization loop.
- `new skill: <kebab-name>`: hand creation to the runtime's skill-authoring workflow. Do not invent the shape ad hoc.

If your environment ships a SKILL.md validator, run it on every touched skill before declaring done.

## 6. Summarize for the user


Short list, no preamble:

- Edits applied: `<skill path>`. What changed, one line each.
- New skills created: `<skill path>`. One line each (rare).
- Backlog filed to the devex tracker: `<issue title>` (`<tags>`). One line each.
- Dropped: one line per rejected finding + reason from the synthesizer.
