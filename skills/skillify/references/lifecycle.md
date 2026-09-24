# Skill Lifecycle

The full create / update / move-rename / retire mechanics skillify owns, plus the branch-then-PR delivery flow and plugin-root relocation.
This file sequences those operations; it does not restate the authoring contract.
Official vendor skills stay unmodified on their official channels; local packages hold only uncovered library or personal context.
Create and update apply [contract §10](contract.md#10-external-facts-and-dependencies) rather than a second dependency procedure.
A package plus its usable evidence handoff at the chosen location completes an authoring run only when its required authoring checks pass (contract §7).
Clean start (§1) and branch → commit → PR (§6) apply only when the destination is a Git repository; a non-Git destination — a vault, a project directory without version control — skips them.
A reviewable source package is not publication, install, or deployment.

## Table of Contents

1. [Clean start](#1-clean-start)
2. [Create](#2-create)
3. [Update](#3-update)
4. [Move or rename](#4-move-or-rename)
5. [Retire](#5-retire)
6. [Branch → commit → PR](#6-branch--commit--pr)
7. [Plugin-root relocation](#7-plugin-root-relocation)

---

## 1. Clean start

Use this section when the destination is a Git repository; skip it otherwise.
Before a formal package change, inspect the actual worktree and selected canonical base:

```bash
git status --short --branch
git rev-parse HEAD
```

Use the destination's approved workspace arrangement; this library normally uses a topic branch from the recorded approved base when the tree is clean.
Reuse a task-approved branch rather than creating another, and do not implicitly repurpose the operator's checked-out branch:

```bash
git switch -c <topic-branch> <approved-base>
```

When unrelated work is present, leave it in place and create an authorized isolated worktree from the pinned canonical base instead:

```bash
git worktree add -b <topic-branch> <new-worktree-path> <approved-base>
```

Do not stash, discard, or carry unrelated work into the lifecycle change.
Fetch the specific canonical revision when it is missing locally; a fetch does not authorize a pull, reset, or deletion.
Record the workspace, base commit, current content identity, and task approval before authoring.

## 2. Create

```bash
SKILL_DIR="<destination>/<skill-name>"   # this library: skills/<skill-name>
mkdir -p "$SKILL_DIR"
```

1. State the artifact, location, relevant format, and cannot-succeed behavior before writing the rest of `SKILL.md` (contract §4). Heading names, procedural phrases, section order, description wording, and ~150-line body length are authoring guidance, not format gates.
2. Choose focused functional, security, and data-integrity evidence for the requested effects (contract §7). Optional authored scenarios are allowed; generated run outputs, wording-locked corpora, and exact evals/triggers schema or counts are not required.
3. Author `SKILL.md` (contract §1–§4) and record history/version under the destination's policy (contract §5; this library seeds `CHANGELOG.md` per §6).
4. Add `references/`, `scripts/`, `assets/`, optional `agents/`, `templates/`, tests where the destination keeps them (this library: repo-root `tests/<skill-name>/`), and `.env.example` only as the package-parts table (contract §5) calls for them; keep generated `evals/` scratch local and gitignored.
5. Apply [contract §10](contract.md#10-external-facts-and-dependencies) for the related official skills and CLI/agent runtimes the task actually uses: current is a verified no-op; stale requires an actual official-channel update on the working host, resulting-version verification, and sibling repair; check-only or failed update leaves the run incomplete. Other devices update when that skill is deployed. Unused optional runtimes are unrelated.
6. Run the checks the destination consumes (this library: the [validator playbook](runtime-hygiene.md#2-validator-playbook)), then hand off the evidence receipt (contract §7) with the package. Passing required checks and handing off usable evidence completes authoring; otherwise retain an incomplete draft. Branch/PR delivery (§6), install, registration, and publication are separate authorized effects.

## 3. Update

Patch `SKILL.md` and/or its support resources, record the destination's history/version change (contract §5), apply [contract §10](contract.md#10-external-facts-and-dependencies) to the dependencies actually used, validate with the destination's checks, and hand off the evidence receipt (contract §7); follow the delivery flow (§6) only when repository delivery is requested and authorized.
In this library, bump `metadata.version` per contract §8 and append one `CHANGELOG.md` bullet; if it would exceed 100 lines, drop the oldest whole entries without rewriting retained bullets or growing a sidecar archive (contract §6).
Git is the history store only for Git-managed destinations.

### Maintain declared dependencies

Every create or update uses the current/stale/failed-update outcomes already owned by [contract §10](contract.md#10-external-facts-and-dependencies).
Do not duplicate that procedure here, treat a version check as success, bulk-update unrelated tools, or invent an unsupported fallback.

### Record a correction

Keep native field experiments separate from official packages; local correction does not itself require a canonical mutation, version bump, or publication.
When the operator requests a harvest or an authorized formal correction, assign the lesson to its actual owner and use the three-way split:

1. **The corrected behavior** → an imperative step in the skill's workflow, only when the fix is a repeatable step rather than a one-off.
2. **The failure it prevents** → one recorded-mistake entry: `- <unwanted behavior> → <what to do instead>.` Exact registry heading text is not a format gate (contract §4, §9).
3. **The event, date, and any operator-supplied source** → the destination's history record (contract §5). In this library, append a `CHANGELOG.md` bullet with `Provenance: <source>` when applicable and trim to 100 lines (contract §6); bump PATCH, or MINOR if the workflow gained a step.

Retain useful field learning until a requested harvest rather than scanning or rewriting all memory.

### Requested field and PR harvest

Classify each input before reusing it:

| Class | Meaning | Required handling |
|---|---|---|
| `canonical_package` | Recorded official package revision | Record base commit and recursive content identity; a new draft is not that old revision |
| `proposed_pr` | Bound PR base/head and diff | Judge the contents and privacy; do not infer admission or merge permission |
| `field_package` | Native local experiment or unique installed delta | Preserve the private original and provenance; select a formal owner only on request |
| `reference_evidence` | Official docs/help, source, manifest, lock or observation | Record version, location and limitations; evidence is not an admitted package |

Record owner, privacy, provenance, unique delta, disposition, and admission state.
Keep private account values and personal source text out of public packages and PRs.
Use a narrow linked provenance source only when necessary for the requested package; never expand the harvest into all MEMORY/USER files or conversations.
Do not add a harvesting cron, daemon, or separate distribution service.
Reuse the common approved policy and task-bound evidence across domain batches rather than invoking a full GJC workflow for every skill.

## 4. Move or rename

Move the actual selected package and repair its active references; this library has no routing-index file.

1. Resolve the source and destination under their applicable permissions, preserve unique contents, and stop on a conflicting destination or escaping symlink rather than overwriting unrelated work.
2. Use the destination's move mechanism: `git mv <source> <destination>` for a tracked package, or a filesystem move for a non-Git package. In this library the paths are `skills/<old-name>` and `skills/<new-name>`; update frontmatter `name` when the package is renamed.
3. Repair active references in the affected destination scope, including script paths, links, verification blocks, and registrations; do not rewrite historical records or unrelated projects.
4. Run the destination's checks and assess affected trigger/path behavior. This library uses its format validator; other destinations do not acquire that validator's Git requirement. Reuse evidence for provably identical content, but refresh evidence for changed names, body, or required resources (contract §7).
5. Runtime loading or registration cleanup runs only when selected and separately authorized; otherwise report it as unverified without blocking completed source work. Preserve unique cache contents and never claim a successful load from static inspection.

## 5. Retire

Retire only an explicitly approved target after preserving unique knowledge and resolving live references and dependencies.
Remove obsolete registration and package paths instead of leaving compatibility aliases or a loadable stub.
Keep retirement history in the destination CHANGELOG or retained repository history, not an invented frontmatter status.
Where this library's CHANGELOG convention applies, drop oldest whole entries if it would exceed 100 lines (contract §6).
Record the removed trigger and output contract as a breaking change and require the corresponding approval before publication.
Source retirement and installed cleanup are different effects; neither authorizes deletion of projects, worktrees, or personal data.

### Abort an in-flight promotion

When authoring is abandoned or blocked, retain the draft and its real status without presenting it as admitted or deployed.
Preserve unrelated work; branch deletion, PR closure, and runtime removal require their own authorized effects.
Do not merge or discard work merely to make the lifecycle appear complete.

## 6. Branch → commit → PR

Prepare reviewable repository state when the destination is a Git repository and the operator requests delivery there.
Authoring is already complete before this flow; it is an additional effect, not a completion condition.
This flow does not authorize live publication, install, reload, or deployment.
bstack registration, merge, and version publication belong to the bstack `promote` skill, which consumes the contract §7 evidence receipt and does not re-author or re-evaluate.

1. Start from the clean-state route (§1).
2. Make the change on the topic branch; do not carry unrelated old-branch state into it.
3. Run `references/runtime-hygiene.md`'s relevant checks and independent review on the frozen base-plus-content snapshot. Preserve functional, security, and data-integrity fixtures; do not require generated eval outputs.
4. Record authoring and destination admission evidence bound to that snapshot. Reuse evidence only while it covers the current task and effect.
5. When commit/push/PR permission exists, publish one logical change and record its actual commit and PR; otherwise report publication pending without fabricating either.
6. Apply admitted releases through the destination's supported native lifecycle only after the specific install/update/reload effects are separately approved.

An existing approval for the same target, command, and effect remains valid; do not ask again for an unchanged candidate.
New targets or expanded irreversible effects require a new decision, not every reversible authoring correction.
Installed content and the current effective load need separate proof; a source commit, manifest version, or receipt `ok` alone does not prove deployment.

## 7. Plugin-root relocation

Use when the plugin root path, repository remote, or a runtime's plugin registration changes.
Claude Code marketplace files are one runtime surface, not the portable package contract.

1. Treat the repository as the single source of truth, not any derived cache or symlink.
2. Update that runtime's marketplace or plugin metadata if the plugin root moved.
3. Search active surfaces for the old path/name: marketplace/plugin manifests, CI workflow files, and any `SKILL.md`/`CHANGELOG.md` with a hardcoded path. Historical mentions in old `CHANGELOG.md` bullets are not blockers once active config is clean.
4. Remove stale bytecode/cache files that preserve the old path.
5. Verify skill discovery on the selected runtime and confirm the affected skills appear.
6. Run `python3 skills/skillify/scripts/validate-skill-format.py` and `python3 skills/skillify/scripts/validate-runtime-hygiene.py` to confirm no format or hygiene violations were introduced.
7. Report status only from real tool output; list unresolved caveats separately rather than burying them in a success summary.
