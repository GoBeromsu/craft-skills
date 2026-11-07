---
name: craft-help
description: Guides users through craft-skills setup, craft-mode, and picking the skill, playbook, or principle for a task, then hands back a prompt they can send and the file the answer came from. Use for "craft-help", "which skill should I use", "how do I use craft-mode", "which playbook fits this", "how do I install craft-skills", or "my craft-mode run went wrong". Answers the question without starting the work. Not for doing the work - use craft-mode.
metadata:
  version: 1.0.8
---

# Craft help

Answer the user's question about craft-skills, hand them a prompt they can send, and link the file the answer came from. For a help question, don't start the work. The user asked how, and a craft-skills run spends real tokens, so let them send the prompt.

A message that asks for work, such as "use craft-skills to fix this bug", is not a help question. Read `craft-mode`, do the work under it, and mention once that a persistent mode keeps it on.

This file maps questions to the skills and files that hold the answers. Those files own the details. Read the file you route to before you quote it, and trust it when it disagrees with this map. The paths here point into the installed plugin, which the user may not be able to open, so give the user the file's public copy: `https://github.com/GoBeromsu/craft-skills/blob/main/` followed by its path.

## Find out what they need

Infer the need from the message and the conversation. A named situation, such as "which skill reviews a PR?", goes straight to its section. If the need is still unclear, ask one multiple-choice question with these options, then answer only the section they pick:

- Get set up
- Start a task with `/craft-mode`
- Pick a skill for a situation
- Fix a run that went wrong
- Make craft-skills my own

Check the state that changes the answer, and mention it only when it does:

- No craft-skills package in the runtime's skill list means craft-skills isn't installed for this user yet.
- No `verify-*` skill or other app harness in the project means agents have no scripted way to drive the app. Mention `principle-testing/references/verification-skills.md` when the question is about proving a change works.

When craft-skills isn't installed and it matters, give them the install route under Get set up, and answer their question too.

## Get set up

1. Install craft-skills through the runtime's channel in `README.md`: the Claude Code, Codex, or GJC plugin marketplace, the Hermes portable plugin (`hermes plugins install GoBeromsu/craft-skills --enable`), or a skills directory (`.cursor/skills`, `.grok/skills`, or `.agents/skills`) for Cursor, Grok-native, and plain Agent Skills runtimes.
2. Start a real task with craft-mode in the runtime's native syntax (`/craft-mode`, or the plugin-qualified handle where the runtime uses one), a goal, and a check that can pass or fail.

Installing changes nothing until the user invokes a skill. `README.md` has the details. Offer to word their first prompt with them, per [`references/prompting.md`](references/prompting.md).

If cost is the worry, say where the tokens go and how to spend fewer. craft-skills spends extra tokens on subagents and review panels. A shorter panel list runs fewer subagents, one for each entry. Save `/craft-mode` for work that needs rigor.

craft-skills uses the plain Agent Skills format, so every runtime in `README.md` reads the same files. Workflow skills that spawn subagents, including `/craft-mode`, `/how`, `/why`, and `/teach`, use whatever workers the runtime offers. `craft-mode/references/runtimes.md` maps each runtime's mechanics.

## Start a task with `/craft-mode`

`/craft-mode` matches the task to a playbook, copies the playbook's steps into the todo list, and runs the other skills as the steps need them. A step it skips stays in the list as `skip: <reason>`. A good prompt states the goal and how to tell it's done. It doesn't list skills, because a hand-written sequence tends to drop or reorder steps the playbook would keep. Read [`references/prompting.md`](references/prompting.md) before you help word one. [`references/recipes.md`](references/recipes.md) has examples.

Whether `/craft-mode` stays on depends on how the user starts it:

- Invoking `/craft-mode` attaches the skill to one message. It fades as the chat moves on.
- A persistent mode keeps it in context every turn until the user exits the mode, and it stays out of casual turns.
- Where the runtime has no persistent mode, start each new task with `/craft-mode`.

Link `craft-mode/references/runtimes.md` when this comes up. Mid-chat, "new task" makes the mode match a fresh playbook. `/craft-mode` already passes its style to the subagents its playbook steps spawn. To get the same style from a subagent of your own, have it read `craft-mode`.

## Pick a skill

The default answer is `/craft-mode`, which runs most of the others when its steps need them. Name a skill directly when the user wants more or less of something than the playbook gives. Read the skill before you recommend it, and give one example prompt.

| The user wants to | Skill |
|---|---|
| Do any non-trivial task with rigor | `/craft-mode` |
| Know how code works now, or where new code should live | `/how` |
| Know why code is shaped this way, or where a number came from | `/why` |
| Understand a change or subsystem, explained plainly | `/teach` |
| Catch up on their own recent work on a topic | `/recall` |
| Know what a small diff could break outside itself | `/blast-radius` |
| Settle types and module shape before code that crosses a function boundary | `/architect` |
| Get several attempts at one brief, merged into the best one | `/arena` |
| Run parallel checks over slices, or race workers, as cloud agents | `/swarm` |
| Have different models review a diff and try to break it | `/interrogate` |
| Triage an issue report, then reproduce and fix confirmed bugs | `/benny` |
| Fix a bug test-first when a cheap local test exists | `/tdd` |
| Apply TypeScript rules to `.ts` or `.tsx` work | `principle-programming/references/typescript.md` |
| Strip comments before review, using a reviewer that didn't write them | `principle-programming/references/comments.md` |
| Clean AI tells out of prose | `/unslop` |
| Write docs, an RFC, a README, a PR description, or a commit message to a standard | `document/references/technical-writing.md` |
| Hear the last reply again in plain words | `/bro` |
| Give agents a scripted way to drive the app and prove behavior | `principle-testing/references/verification-skills.md` |
| Bring a verification skill and its feature map back in line with the app | `principle-testing/references/verification-skills.md` |
| Vet a performance number before reporting or acting on it | `/benchmark-checklist` |
| Run a large or cross-cutting change, or one to review after stepping away | `/figure-it-out` |
| Keep a decision log during a run, and review it afterward | `/show-me-your-work` |
| Turn their own working habits into a personal mode skill | `/automate-me` |
| Turn what a finished task taught into skill edits | `/reflect` |
| Stop agents from repeating the same mistakes in this repo | `/correct` |
| Find their way around craft-skills | `/craft-help` |

If a skill directory next to this one is missing from the table, read its frontmatter and route by its description. The `principle-*` directories are covered under principles below.

Close calls:

- `/how` explains what the code does. `/why` explains the reasons. `/teach` runs one or both and explains the result plainly.
- `/arena` gives every worker the same brief and merges the best parts. `/swarm` splits work into slices or a race and returns one report.
- `/architect` implements right after it settles the design. Add "with checkpoint" to review the design before it writes code.
- `/interrogate` reviews the diff. `/blast-radius` looks for breakage outside the diff and proves the one fact that makes the change safe.
- `/recall` rebuilds context across recent chats. Resuming one specific chat or branch is the Session pickup playbook.
- `/figure-it-out` designs one rigorous run. The Orchestrate playbook runs a program that spans days and many PRs. The Autonomous run playbook drives one task to a finish condition.

Not in craft-skills:

- A deslop pass and the project's UI/CLI control harness ship in a separate plugin.
- The runtime's loop and skill-creation commands are runtime built-ins.
- craft-skills has no `/orchestrate` skill. Orchestrate is a `/craft-mode` playbook. If the slash menu shows `/orchestrate`, another plugin provides it.

## Playbooks and principles

Playbooks are step lists inside `/craft-mode`, not skills, so they have no slash command. Inside `/craft-mode`, describing the task picks one, and these phrases name one directly:

- "babysit this pr" or "check on pr 123" runs Babysit. It drives the PR to merge-ready and stops there. It doesn't merge unless the user asks to merge, land, or ship.
- "land the stack" runs Shipping.
- "take over this branch" runs Session pickup.
- "pause safely" runs Pause safely.
- "full autopilot on this queue" runs Autopilot-full. "stack them, don't ship" runs Autopilot-stack.
- "run the eval playbook" runs Eval.

Without `/craft-mode`, a phrase such as "babysit this pr" can start the runtime's own skill for the same job instead. The Playbooks section of `craft-mode` lists every playbook and when it applies. `craft-mode/references/playbooks/opening-a-pr.md`, `craft-mode/references/playbooks/babysit.md`, and `craft-mode/references/playbooks/shipping.md` cover opening, babysitting, and landing a PR.

craft-skills has no planning skill. The runtime's plan mode works alongside it. For work that spans phases or stacked PRs, asking `/craft-mode` for a plan runs the Multi-phase plan playbook (`craft-mode/references/playbooks/multi-phase-plan.md`), which writes the plan and doesn't implement it. For a design question, the Prototype playbook or `/architect` settles it in code first.

Principles are one-rule skills that `/craft-mode` reads and cites in its replies. The user rarely invokes one. They steer with the names instead, as in "apply prove it works. show me the real output." Typing `/principle-<name>` still loads one on demand. `craft-mode` lists them.

## Fix a run that went wrong

| Symptom | Fix |
|---|---|
| The mode stopped applying after a few turns | It was attached to one message. Start it as a persistent mode, or start each task with `/craft-mode`. |
| A question got treated as the next step of the last task | Say "new task", or say the turn doesn't need the mode. |
| Runs cost more than expected | See the cost paragraph under Get set up. |
| A skill didn't load on its own | Skills load when the user types them or when `/craft-mode` runs them, and it doesn't run every skill. |
| Parallel agents overwrote each other | Give each agent its own worktree, or run them as cloud agents, which each get their own machine. |
| An overnight run moved but finished nothing | The loop needs a check that can pass or fail, not a duration. See `craft-mode/references/playbooks/autonomous-run.md`. |
| The reply claims success from a green build | Ask for the real command, flow, stored value, or profile. That's the prove-it-works principle. |

For a run that drifts, [`references/prompting.md`](references/prompting.md) has one-line steers. [`references/recipes.md`](references/recipes.md) has the recipes worth copying.

## Make craft-skills my own

- `/automate-me` drafts a personal mode skill from the user's own history, to use alongside `/craft-mode`.
- `/reflect` after a session turns its lessons into skill edits the user approves.
- `/craft-mode write a skill for <workflow>` runs the authoring playbook. The eval playbook tests a skill change blind.
- Fix a misbehaving skill in its own PR, not inside the feature work where it went wrong.

`automate-me`, `reflect`, `craft-mode/references/playbooks/authoring-a-skill.md`, and `craft-mode/references/playbooks/eval.md` cover each of these.

## Reply

Lead with the answer. Give at most one example prompt in a code block, adapted from [`references/recipes.md`](references/recipes.md) when one fits, then the link to that file. Keep it short unless the user asked for the whole map.
