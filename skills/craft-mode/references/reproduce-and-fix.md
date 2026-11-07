# Reproduce and fix issues

Start from the **issue-triage** skill's intake verdict when one exists; otherwise from the user's report. Reproduce the exact symptom through the target app's real UI. Verify an existing fix when one exists. Attempt a bounded fix only after a confirmed repro.

Take the control skill and feature map from the repository's AGENTS.md. When either is missing, ask the user to name the control skill, or draft a feature map in the format of the **principle-testing** skill's `references/feature-map-example/`. A capability that is absent mid-run ends the run as `Blocked` with the missing capability named, never a claimed repro. Default budgets are 60 minutes for the repro and 90 minutes for the fix; the user may override them.

## Hard safety rules

- Freeze the source issue/thread identity before doing any work.
- Never create a new issue/thread to deliver a source verdict.
- Preflight the source parent before every source issue/thread post.
- The coordinator is the only source poster.
- Delegated analysis workers are read-only and return findings or media notes.
- A fix-phase code worker may edit only when its environment provably excludes source credentials and every source write action. Otherwise the coordinator edits.
- Every child prompt must explicitly forbid all source writes.
- Never give a child a source token, posting instructions, source coordinates for posting, or permission to report externally.
- If a child needs source write access to run, do not launch it.
- Utility bots are evidence sources. They do not own the fix unless a person explicitly delegated the fix to them.
- The exact discriminating symptom must appear twice through real UI interaction.
- State inspection may confirm an observation. It must not inject or force the symptom.
- No confirmed repro means no authored fix.
- Existing pull requests or commits switch the run to verify mode. Do not author over them.
- Keep captures, recordings, logs, and tokens out of source control.
- Open a draft pull request; this overrides Opening a PR's readiness rule. Never merge or deploy from this workflow.
- Status and evidence go to the user in this session: Reproducing, Could not reproduce, Blocked, Reproduced, Verifying existing fix, Attempting bounded fix, Draft pull request opened, Fix did not land.
- Use [guard-the-context-window.md](guard-the-context-window.md) for delegated analysis.
- Apply the **principle-testing** skill's `references/sequence-verifiable-units.md` and `references/prove-it-works.md`, and the **debug** skill's `references/fix-root-causes.md`, through repro, fix, and verification.

## 1. Freeze source coordinates

Before making a work list or delegating:

1. Use the source origin the user linked or pasted. For pasted text, use the same user message as triage.
2. Set `SOURCE_ID` to the source issue/thread identity, not a reply identity.
3. Require a nonempty `SOURCE_ID`.
4. Store `SOURCE_ORIGIN` and `SOURCE_ID` as immutable values.
5. Read the source issue/thread and verify its parent has that exact identity; for pasted text, verify the original user message.
6. Fetch the source permalink when one exists. Never invent one for pasted text.

Never replace these values with a reply identity.

Before every source post:

1. Read the source by its immutable identity.
2. Confirm the parent exists, is not deleted, and still belongs to `SOURCE_ORIGIN`.
3. Send only on `SOURCE_ID`. For pasted text, return the result to the user instead.
4. Read the source again and verify the new verdict belongs to that issue/thread.

If any check fails, post nothing. Never retry in a new issue/thread or a fallback destination.

## 2. Start from the issue-triage verdict

When the **issue-triage** skill's intake verdict exists for this source, consume its frozen source and repro notes. Proceed only for a bug or performance verdict, and capture its optional tracker URL. Stop for `other` or conflicting verdicts.

Without a verdict, start from the user's report and the user's go-ahead.

## 3. Apply ownership and fix-artifact gates

Re-read the thread immediately before starting work.

### Someone is explicitly fixing it

Stop when a person clearly claims the fix, gives a concrete implementation plan, or asks another agent to implement, patch, fix, or open a pull request.

Do not treat these as fix ownership:

- A bot summarizes evidence.
- A tool looks up logs or tickets.
- Someone asks a bot to diagnose, explain, inspect, or reproduce.
- A bot posts a cause hypothesis without agreeing to implement it.

Judge the requested action, not the presence of a bot.

### A fix artifact already exists

If an open pull request or merged commit plausibly fixes this report, switch to [verify-existing-fix.md](verify-existing-fix.md).

An artifact may come from the thread, tracker issue, repository history, or pull request search. A claim without a commit or pull request is not a fix artifact.

If a person owns the work but has not produced an artifact, stop. Do not race them.

## 4. Load and check the control adapter

Read [control-adapter.md](control-adapter.md) and the feature map from AGENTS.md or the user, then invoke the control skill named in AGENTS.md or by the user.

Find the feature-map section that matches the reported user path. Read it before driving the app. If no section covers the feature, ask the user or mark the run `Blocked` instead of inventing a path or selector.

Require all seven capabilities:

1. Bring up the target app and test environment named in AGENTS.md or agreed with the user.
2. Navigate the mapped feature and exercise its documented states.
3. Drive the real UI with clicks, typing, keys, scrolling, drag, resize, or navigation.
4. Inspect state without mutating it.
5. Capture screenshots.
6. Start and stop a screen recording.
7. Clean up processes, sessions, profiles, and temporary data.

If the adapter is absent or any required capability is missing, report `Blocked` to the user and stop. Do not pretend a screenshot, unit test, state mutation, or source reading is a UI repro.

## 5. Study the report

Read the full source issue/thread and tracker issue when present.

Collect:

- Exact action path
- Expected behavior
- Observed behavior
- Discriminating state where they diverge
- Frequency
- Version, environment, and platform
- Attachments and error signatures
- Candidate code area

Inspect screenshots and video. Use read-only parallel workers for code history, test ideas, blast-radius mapping, and media review when useful. Each worker gets a narrow question and the source-write prohibition.

Use the **how** skill to trace the action through the repository. Use the **why** skill for regression history and defensive code. Form competing cause hypotheses and identify evidence that would separate them.

## 6. Reproduce

Bring up the target app through the control adapter.

Confirm the correct app, workspace, account, data set, and feature state before acting. Use stable app markers. Do not rely on window order or a familiar title alone.

Drive the reported path through real UI actions.

Before calling it reproduced:

1. Name the correct final state.
2. Name the broken final state.
3. Reach the point where they diverge.
4. Observe the broken state.
5. Reset enough state to make the second attempt independent.
6. Repeat the same path and observe the same broken state again.
7. Cross-check a real state value when possible.

An expected dialog, loading state, or setup step is not the bug. Capture the final state that distinguishes correct from broken behavior.

Use the repro budget. If the symptom does not reproduce within it, report a clean `Could not reproduce` outcome. If the environment cannot provide a required capability, report `Blocked` and state what was missing.

## 7. Capture and review evidence

For a successful repro:

- Record the full path through the symptom.
- Capture a screenshot of the broken final state.
- Save a short note with the exact steps and observed state.
- Keep artifacts in a temporary artifact directory named in AGENTS.md or agreed with the user.

Have a read-only media reviewer answer one question: does the evidence visibly show the discriminating broken state?

If the answer is no or uncertain, the repro is not confirmed. Capture better evidence or use `Could not reproduce`.

Show the detailed evidence to the user. Keep any source update concise.

## 8. Report the repro outcome

Report the outcome to the user first.

For `Could not reproduce` or `Blocked`, post nothing in the source issue/thread. Report the result to the user.

When the user asks for a source reply, run the source preflight and post one reply:

- Say the issue reproduced.
- Include at most three short findings.
- Link the tracker issue when one exists.
- Do not ping an owner by default.

Attach evidence to that reply only when the source action keeps it inside the same source issue/thread and the organization's retention policy allows it.

Show the repro evidence and get the user's go-ahead before the fix phase. If the user shows that the setup or interpretation was wrong, correct the repro once.

## 9. Verify an existing fix

When a fix artifact exists, follow [verify-existing-fix.md](verify-existing-fix.md).

Verification must show the symptom on the baseline and its absence on the patched build. Both paths use the real UI twice.

Do not edit the existing fix, add a competing patch, or open a replacement pull request.

## 10. Qualify a bounded fix

Attempt a fix only when all of these hold:

- The outcome is a plain confirmed repro.
- Media review confirmed the broken final state.
- No existing fix artifact appeared.
- The user gave the go-ahead for the fix phase.
- Runtime evidence identifies the root cause.
- The likely change fits the fix budget and the repository scope named in AGENTS.md or agreed with the user.
- The control adapter can run both baseline and patched builds.

If any condition fails, keep the repro report and stop without a pull request.

When the gate passes, report `Attempting bounded fix` to the user.

## 11. Root-cause and implement

The coordinator owns every source post, the final diff review, commits, and the pull request.

Read-only workers may:

- Trace code and history
- Propose tests
- Map blast radius
- Review a diff
- Review media

They do not edit, run external writes, post status, or own the fix.

A tightly scoped code edit may be delegated during this phase only when tool isolation removes source credentials and every source write action from that worker. Its prompt must still carry the explicit source-write ban. The coordinator reviews the edit and runs or verifies the required tests. If tool isolation is uncertain, keep the edit in the coordinator.

Confirm the mechanism with runtime evidence. Eliminate competing hypotheses before editing.

Fix the root cause with the smallest justified change.

- Invoke the **tdd** skill when there is a cheap local test target, and write the failing test before the fix.
- State why TDD was skipped when the path is expensive, unclear, or integration-heavy.
- Keep unrelated cleanup out.
- Stop if the change grows beyond the effort or risk budget named in AGENTS.md or agreed with the user.

## 12. Prove the fix

Keep the original baseline evidence.

On the patched build:

1. Run the same real UI path.
2. Repeat it twice.
3. Show that the broken state is gone.
4. Show the expected state in its place.
5. Capture an after recording and screenshot.
6. Cross-check the same real state value used for the baseline.

A compile, unit test, code review, or plausible diff is not after evidence.

Run focused tests, then smoke the blast radius around the changed behavior. Cover nearby states, inputs, permissions, platforms, and failure paths that the change could affect. Stop without a pull request if a regression remains.

## 13. Open a draft pull request

Only after before-and-after proof:

- Review the final diff for unrelated changes and secrets.
- Run the repository's required checks.
- Create small ordered commits when the repository workflow allows it.
- Open a draft pull request. Never merge or deploy from this workflow.
- Link the tracker issue from the intake verdict, when present, using the tracker's supported pull request syntax.
- Use the repository's own pull request URL form (resolve the forge per [Opening a PR](playbooks/opening-a-pr.md), forge resolution only).
- Include the repro steps, root cause, test result, before and after evidence, and blast-radius checks.
- Run the pull request text and all source updates through the **unslop** skill.

If pull request creation fails, do not claim success. Keep the commit or branch state in the run output and report `Fix did not land` to the user.

On success, report `Draft pull request opened` to the user and give the user the linked pull request. Do not create a second source issue/thread, and post a source reply only when the user asks.

## 14. Follow-ups and cleanup

- Answer a direct question from evidence already gathered.
- Apply one concrete correction and rerun the repro once when it invalidates the setup.
- Stay out of human coordination and side chatter.
- Stop when asked.

Always call the control adapter's cleanup capability. Keep artifacts only as long as the retention policy named in AGENTS.md or agreed with the user allows.
