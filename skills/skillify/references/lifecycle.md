# Skill Lifecycle

The full create / update / move-rename / retire mechanics skillify owns, plus the branch-then-PR delivery flow and plugin-root relocation.

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

1. Draft `## Output contract` (contract §4) and choose relevant tests/scenario evidence (contract §7) before writing the rest of `SKILL.md`.
2. Author `SKILL.md` (contract §1–§4) and seed `CHANGELOG.md` with the first dated bullet.
3. Add `references/`, `scripts/`, `assets/`, optional `agents/`, `templates/`, `tests/`, and `.env.example` only as the package-parts table (contract §5) calls for them; keep `evals/` local and gitignored.
4. For each mutable external dependency, record its official source, installed-version probe, support boundary, and update trigger beside this package (contract §10).
5. Validate (see `references/runtime-hygiene.md` for the script invocations), then follow the delivery flow (§6).

## 3. Update

Patch `SKILL.md` and/or `references/`, bump `metadata.version` per the version-bump rubric (contract §8), append one `CHANGELOG.md` bullet, validate, then follow the delivery flow (§6).

### Maintain declared dependencies

For each mutable dependency declared under the contract's [external-facts and dependencies rules](contract.md#10-external-facts-and-dependencies), run its installed-version probe when its release or update trigger fires.
On a detected update, recheck the linked official documentation before trusting the prior recipe.
Rerun the eval cases affected by that dependency, update the recipe and its support boundary when needed, then bump the package version and append the CHANGELOG entry.
Keep this loop in the dependent package; do not centralize it in an inventory, daemon, or framework.

### Record a correction

Keep native field experiments separate from official packages; local correction does not itself require a canonical mutation, version bump, or publication.
When the operator requests a harvest or an authorized formal correction, assign the lesson to its actual owner and use the three-way split:

1. **The corrected behavior** → an imperative step in the skill's workflow, only when the fix is a repeatable step rather than a one-off.
2. **The failure it prevents** → one `## Anti-patterns` entry: `- <unwanted behavior> → <what to do instead>.`
3. **The event, date, and any operator-supplied source** → the `CHANGELOG.md` bullet, with a `Provenance: <source>` clause when material was handed over (contract §6). Bump PATCH — MINOR if the workflow gained a step.

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
3. Verify by loading, not by reading a routing index — open Claude Code and confirm the moved skill still appears under its trigger phrases; run `python3 skills/skillify/scripts/validate-skill-format.py` to confirm the moved package is still well-formed.
4. Record stale runtime registrations and caches as effect candidates; preserve unique content and use approved native cleanup rather than unilateral cache deletion.

## 5. Retire

Retire only an explicitly approved target after preserving unique knowledge and resolving live references and dependencies.
Remove obsolete registration and package paths instead of leaving compatibility aliases or a loadable stub.
Keep retirement history in the destination CHANGELOG or retained repository history, not an invented frontmatter status.
Record the removed trigger/output contract as a breaking change and require the corresponding approval before publication.
Source retirement and installed cleanup are different effects; neither authorizes deletion of projects, worktrees, or personal data.

### Abort an in-flight promotion

When authoring is abandoned or blocked, retain the draft and its real status without presenting it as admitted or deployed.
Preserve unrelated work; branch deletion, PR closure, and runtime removal require their own authorized effects.
Do not merge or discard work merely to make the lifecycle appear complete.

## 6. Branch → commit → PR

Prepare reviewable repository state, then publish only within the operator's authorization.

1. Start from the clean-state route (§1).
2. Make the change on the topic branch; do not carry unrelated old-branch state into it.
3. Run `references/runtime-hygiene.md`'s relevant checks and independent review on the frozen base-plus-content snapshot.
4. Record authoring and destination admission evidence bound to that snapshot. Reuse evidence only while it covers the current task and effect.
5. When commit/push/PR permission exists, publish one logical change and record its actual commit and PR; otherwise report publication pending without fabricating either.
6. Apply admitted releases through the destination's supported native lifecycle only after the specific install/update/reload effects are approved.

An existing approval for the same target, command, and effect remains valid; do not ask again for an unchanged candidate.
New targets or expanded effects require a new decision, not every reversible authoring correction.
Installed content and the current effective load need separate proof; a source commit, manifest version, or receipt `ok` alone does not prove deployment.

## 7. Plugin-root relocation

Use when the plugin root path, repository remote, or Claude Code plugin registration changes.

1. Treat the repository as the single source of truth, not any derived cache or symlink.
2. Update `.claude-plugin/marketplace.json` and `plugin.json` if the plugin root moved.
3. Search active surfaces for the old path/name: marketplace/plugin manifests, CI workflow files, and any `SKILL.md`/`CHANGELOG.md` with a hardcoded path. Historical mentions in old `CHANGELOG.md` bullets are not blockers once active config is clean.
4. Remove stale bytecode/cache files that preserve the old path.
5. Verify skill discovery by opening Claude Code and confirming the affected skills appear under the plugin.
6. Run `python3 skills/skillify/scripts/validate-skill-format.py` and `python3 skills/skillify/scripts/validate-runtime-hygiene.py` to confirm no format or hygiene violations were introduced.
7. Report status only from real tool output; list unresolved caveats separately rather than burying them in a success summary.
