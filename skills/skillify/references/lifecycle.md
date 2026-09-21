# Skill Lifecycle

The full create / update / move-rename / retire mechanics skillify owns, plus the branch-then-PR delivery flow and plugin-root relocation.
This file sequences those operations; it does not restate the authoring contract.
Official vendor skills stay unmodified on their official channels; local packages hold only uncovered library or personal context.
Create and update apply [contract §10](contract.md#10-external-facts-and-dependencies) rather than a second dependency procedure.
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

Before a formal package change, inspect the actual worktree and selected canonical base:

```bash
git status --short --branch
git rev-parse HEAD
```

Choose a topic branch from the recorded approved base when the tree is clean; do not implicitly repurpose the operator's checked-out branch:

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
SKILL_DIR="skills/<skill-name>"
mkdir -p "$SKILL_DIR"
```

1. State the artifact, location, relevant format, and cannot-succeed behavior before writing the rest of `SKILL.md` (contract §4). Heading names, procedural phrases, section order, description wording, and ~150-line body length are authoring guidance, not format gates.
2. Choose focused functional, security, and data-integrity evidence for the requested effects (contract §7). Optional authored scenarios are allowed; generated run outputs, wording-locked corpora, and exact evals/triggers schema or counts are not required.
3. Author `SKILL.md` (contract §1–§4) and seed `CHANGELOG.md` with the first dated bullet (contract §6).
4. Add `references/`, `scripts/`, `assets/`, optional `agents/`, `templates/`, repo-root tests, and `.env.example` only as the package-parts table (contract §5) calls for them; keep generated `evals/` scratch local and gitignored.
5. Apply [contract §10](contract.md#10-external-facts-and-dependencies) for related official skills and CLI/agent runtimes: current is a verified no-op; stale requires an actual official-channel update on the working host, resulting-version verification, and sibling repair; check-only or failed update leaves the run incomplete. Other devices update when that skill is deployed.
6. Run the relevant [validator playbook](runtime-hygiene.md#2-validator-playbook) checks, then follow the delivery flow (§6). Delivery is not install or live publication.

## 3. Update

Patch `SKILL.md` and/or `references/`, bump `metadata.version` per the version-bump rubric (contract §8), add one `CHANGELOG.md` bullet, apply [contract §10](contract.md#10-external-facts-and-dependencies), validate, then follow the delivery flow (§6).
If the CHANGELOG would exceed 100 lines, drop the oldest whole entries until it fits; do not cut an entry in the middle, rewrite retained bullets, or grow a sidecar archive (contract §6).
Git remains the history store.

### Maintain declared dependencies

Every create or update uses the current/stale/failed-update outcomes already owned by [contract §10](contract.md#10-external-facts-and-dependencies).
Do not duplicate that procedure here, treat a version check as success, bulk-update unrelated tools, or invent an unsupported fallback.

### Record a correction

Keep native field experiments separate from official packages; local correction does not itself require a canonical mutation, version bump, or publication.
When the operator requests a harvest or an authorized formal correction, assign the lesson to its actual owner and use the three-way split:

1. **The corrected behavior** → an imperative step in the skill's workflow, only when the fix is a repeatable step rather than a one-off.
2. **The failure it prevents** → one recorded-mistake entry: `- <unwanted behavior> → <what to do instead>.` Exact registry heading text is not a format gate (contract §4, §9).
3. **The event, date, and any operator-supplied source** → the `CHANGELOG.md` bullet, with a `Provenance: <source>` clause when material was handed over, then trim to 100 lines if needed (contract §6). Bump PATCH — MINOR if the workflow gained a step.

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

There is no routing-index file to update in this library's model — moving a skill means moving the real directory and fixing every path that names it.

1. `git mv skills/<old-name> skills/<new-name>` so history survives.
2. Search the repo for the old path and rewrite every hit: script paths, reference links, verification blocks, CI workflow steps, other skills' cross-references.
3. Verify by loading on the selected runtime, not by reading a routing index — confirm the moved skill still appears under its trigger phrases; run `python3 skills/skillify/scripts/validate-skill-format.py` to confirm the moved package is still well-formed.
4. Record stale runtime registrations and caches as effect candidates; preserve unique content and use approved native cleanup rather than unilateral cache deletion.

## 5. Retire

Retire only an explicitly approved target after preserving unique knowledge and resolving live references and dependencies.
Remove obsolete registration and package paths instead of leaving compatibility aliases or a loadable stub.
Keep retirement history in the destination CHANGELOG or retained repository history, not an invented frontmatter status.
If the CHANGELOG would exceed 100 lines, drop oldest whole entries (contract §6).
Record the removed trigger and output contract as a breaking change and require the corresponding approval before publication.
Source retirement and installed cleanup are different effects; neither authorizes deletion of projects, worktrees, or personal data.

### Abort an in-flight promotion

When authoring is abandoned or blocked, retain the draft and its real status without presenting it as admitted or deployed.
Preserve unrelated work; branch deletion, PR closure, and runtime removal require their own authorized effects.
Do not merge or discard work merely to make the lifecycle appear complete.

## 6. Branch → commit → PR

Prepare reviewable repository state.
This flow does not authorize live publication, install, reload, or deployment.

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
