# Gajae-Code Lens

GJC-specific orchestration for authoring and refining portable skill packages.
The generated package remains runtime-neutral; this lens never changes the package contract.

## Table of Contents

1. [Sources and support boundary](#1-sources-and-support-boundary)
2. [Ownership boundary](#2-ownership-boundary)
3. [Preflight the built-in profiles](#3-preflight-the-built-in-profiles)
4. [Select one profile](#4-select-one-profile)
5. [Run the complete workflow](#5-run-the-complete-workflow)
6. [Evaluation and evidence](#6-evaluation-and-evidence)
7. [Failure and retry behavior](#7-failure-and-retry-behavior)
8. [Portability boundary](#8-portability-boundary)

## 1. Sources and support boundary

Official sources:

- [SDK application guide](https://github.com/Yeachan-Heo/gajae-code/blob/main/docs/sdk-app-guide.md)
- [SDK contract](https://github.com/Yeachan-Heo/gajae-code/blob/main/docs/sdk.md)
- [SDK session CLI](https://github.com/Yeachan-Heo/gajae-code/blob/main/docs/sdk-session-cli.md)
- [Models and profiles](https://github.com/Yeachan-Heo/gajae-code/blob/main/docs/models.md)
- [Multi-vendor profiles](https://github.com/Yeachan-Heo/gajae-code/blob/main/docs/multi-vendor-profiles.md)

This route requires an installed GJC that exposes:

- the Q27 `models.profiles.list` query as a complete profile catalog with exact profile IDs, `source`, and boolean `available`.
- session-scoped `--mpreset` activation.
- the built-in `opus-codex` and `codex-pro` profiles.
- native `ralplan` and `ultragoal` workflows.

Probe the installed version with `gjc --version`, then verify capabilities rather than inferring them from a version number.
The route was exercised with GJC 0.15.4; that observation is not a claimed minimum version.
Current GJC documentation describes Q27 as the full catalog with explicit availability, although a narrower row example elsewhere in the SDK document omits that field.
The installed response is authoritative for the run: a missing or non-boolean `available` value stops this route and requires re-planning.

## 2. Ownership boundary

GJC owns only orchestration:

- selecting one built-in profile before planning.
- Ralplan consensus and approval.
- Ultragoal execution continuity and evidence tracking.
- native session and workflow state.

Skillify continues to own:

- admission and package planning.
- `evals/evals.json` and `evals/triggers.json`.
- baseline-versus-candidate evaluation.
- package format and deterministic validators.
- versioning, changelog, provenance, and branch-to-PR delivery.

Ralplan references those existing gates instead of defining replacements.
Ultragoal may track their evidence but never waives or duplicates them.

## 3. Preflight the built-in profiles

Run preflight under the same effective agent directory and repository authority that the native authoring session will use.
Use a broker-indexed preflight session and the public SDK session CLI; never inspect endpoint records, bearer tokens, or private WebSockets.

```bash
gjc sdk session list
gjc sdk session inspect <preflight-session-id>
gjc sdk session raw query <preflight-session-id> \
  --query models.profiles.list
```

Follow every continuation cursor until the response reports a complete page set.
A partial page cannot prove that a profile is absent or unavailable.
For each candidate, require one exact effective row with:

- the exact requested ID.
- `source: builtin`.
- a boolean `available` value.

A same-name `source: configured` row is a configured override, not the requested built-in profile.
Treat ambiguous rows, incomplete pagination, registry failure, missing fields, or an authority mismatch as preflight failure.
Record only the session ID, complete-page evidence, profile ID, source, and availability; never record credentials or endpoint data.

Q27 is used only for profile provenance and availability.
Do not expand this route to Q10 selection, activation probing, Q26 turn telemetry, broker-driven authoring, private endpoint access, or an embedding harness.
If the installed Q27 contract cannot establish the required facts, stop and re-plan instead of inventing another surface.

## 4. Select one profile

Apply this deterministic priority before Ralplan starts:

1. Select `opus-codex` when its exact row has `source: builtin` and `available: true`.
2. Otherwise select `codex-pro` when its exact row has `source: builtin` and `available: true`.
3. Otherwise stop before planning or product mutation.

`opus-codex` is the primary whole-workflow profile.
`codex-pro` is only the whole-workflow fallback when the multi-provider primary is unavailable; it is not a mandatory second reviewer.

Start a new, non-resumed native session with the selected profile for this run only:

```bash
gjc --mpreset <selected-profile>
```

Never add `--default`; this workflow does not alter the operator's startup default.
Record the selected profile in the plan and Ultragoal evidence, then keep it fixed through completion.

## 5. Run the complete workflow

Selecting this GJC route makes deliberate Ralplan mandatory before product edits:

```text
/skill:ralplan --deliberate "<skill change and acceptance criteria>"
```

After approval, invoke `/skill:ultragoal` from the same selected live session so the in-process workflow handoff retains that session's profile.
Bind the state-seeding CLI call to the same session identity:

```bash
GJC_SESSION_ID=<selected-session-id> \
  gjc ultragoal create-goals --brief-file <approved-plan>
```

The CLI command seeds durable Ultragoal state; it does not start a second model session.
Never run it from an unbound shell or hand execution to a different GJC session.

The selected profile remains active for:

- Ralplan planning and review.
- Ultragoal execution.
- package authoring and refinement.
- baseline and candidate eval iterations.
- validators and completion evidence.

Do not switch to `codex-pro` after Ralplan because the selected profile later fails.
Stop and preserve the evidence; any retry begins with a new preflight, a new session, and a new complete run.

## 6. Evaluation and evidence

Use the provider-neutral fresh-eyes contract in [`evaluation.md`](evaluation.md).
GJC orchestration does not prescribe a second GJC profile as the judge.
Use a fresh, blind, read-only capable model or human independent from the authoring session, and keep the baseline and candidate arms matched as that methodology requires.

Keep local eval artifacts under the existing gitignored `evals/` directory.
Do not commit GJC session state, workflow IDs, profile receipts, or `.gjc` paths into a generated package.
A useful sanitized run record contains:

- the preflight session ID and completion status.
- selected built-in profile and availability.
- the Ralplan run or approved-plan reference.
- the Ultragoal run and validator/eval evidence references.
- the terminal outcome.

The record never contains endpoint URLs, tokens, credentials, environment values, or private discovery files.

## 7. Failure and retry behavior

| Condition | Required behavior |
|---|---|
| Built-in `opus-codex` is available | Select it for the complete run. |
| Primary is unavailable and built-in `codex-pro` is available | Select `codex-pro` before Ralplan for the complete run. |
| A candidate is configured-shadowed | Disqualify that candidate and evaluate only the next priority candidate. |
| Neither candidate qualifies | Stop before Ralplan and product mutation. |
| Q27 is incomplete, ambiguous, or lacks boolean availability | Stop and re-plan; do not add another query or activation surface ad hoc. |
| Native activation fails after selection | Stop; do not switch profiles in place. |
| The selected profile fails after Ralplan | Preserve evidence and restart from preflight in a new run. |
| Ralplan proposes a second eval or lifecycle owner | Reject that part and link to skillify's existing owner. |
| Ultragoal lacks eval, validator, provenance, or lifecycle evidence | Keep completion open until the existing gate is satisfied. |
| A fresh-eyes judge is unavailable | Use another independent capable model or a human; do not restore a preferred provider. |

GJC owns provider retries inside the selected profile.
Those retries do not authorize changing the workflow profile or weakening a skillify gate.

## 8. Portability boundary

All GJC commands, profile names, Q27 handling, session state, and retry rules belong in this lens.
Never copy them into a universal package's root `SKILL.md`, scripts, templates, or required runtime instructions.

The final skill package must run unchanged wherever its declared portable contract applies, including Claude Code, Codex, Cursor, Hermes, and Grok-native runtimes.
A package may link to this lens as optional authoring guidance; it may not require GJC to execute its reusable craft.
