# Skill Lifecycle

The full create / update / move-rename / retire mechanics skillify owns, plus the
branch-then-PR delivery flow and plugin-root relocation.

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

Before any lifecycle change: run `git status` first and stash or set aside unrelated
uncommitted work — never discard user-owned changes to reach a clean tree. Then:

```bash
git fetch origin --prune
git checkout main
git pull --ff-only origin main
git checkout -b <topic-branch>
```

Do not stack a skill change on a dirty or unrelated branch.

## 2. Create

```bash
SKILL_DIR="skills/<skill-name>"
mkdir -p "$SKILL_DIR"
```

1. Draft `evals/evals.json` + `evals/triggers.json` (contract §7) before writing `SKILL.md`.
2. Author `SKILL.md` (contract §1–§4) and seed `CHANGELOG.md` with the first dated bullet.
3. Add `references/`, `scripts/`, `templates/`, `tests/`, `.env.example` only as the
   package-parts table (contract §5) calls for them.
4. Validate (see `references/runtime-hygiene.md` for the script invocations), then branch →
   commit → PR (§6).

## 3. Update

Patch `SKILL.md` and/or `references/`, bump `metadata.version` per the version-bump rubric
(contract §8), append one `CHANGELOG.md` bullet, validate, PR.

## 4. Move or rename

There is no routing-index file to update in this library's model — moving a skill means
moving the real directory and fixing every path that names it.

1. `git mv skills/<old-name> skills/<new-name>` so history survives.
2. Search the repo for the old path and rewrite every hit: script paths, reference links,
   verification blocks, CI workflow steps, other skills' cross-references.
3. Verify by loading, not by reading a routing index — open Claude Code and confirm the moved
   skill still appears under its trigger phrases; run
   `python3 skills/skillify/scripts/validate-skill-format.py` to confirm the moved package
   is still well-formed.
4. Delete any stale bytecode/cache under the old path.

## 5. Retire

Mark deprecation in the **body**, never in frontmatter — the frontmatter contract is fixed
and admits no `status` key. Add a `## Deprecated` section at the top of `SKILL.md` pointing
to the replacement skill, bump **MAJOR** (a trigger phrase is leaving the contract), append
a `CHANGELOG.md` bullet, and PR. Prefer a deprecated stub over physical deletion whenever
another skill takes over the same trigger phrases. Delete the directory only after
confirming no other skill or scheduled job still references it.

### Abort an in-flight promotion

When a promotion is abandoned — the workflow proves too narrow, or the user cancels —
unwind it instead of leaving half-registered state. Confirm the abandonment with the user
before any destructive step.

- **No PR yet:** delete the working branch; the scaffolded directory dies with it.
- **PR opened:** close the PR and delete the branch — nothing merges to `main`.
- An abandoned promotion records nothing in `main` — the branch is the only artifact, and
  it is gone once deleted.

## 6. Branch → commit → PR

Every skill change ships as branch → commit → PR unless the operator explicitly requests
local-only. A patched file is not the deliverable; reviewable repo state is.

1. Clean start (§1).
2. Make the change on the topic branch; do not drag unrelated old-branch state into the PR.
3. Validate (`references/runtime-hygiene.md`), commit, push.
4. Open a PR unless local-only was explicitly requested.

## 7. Plugin-root relocation

Use when the plugin root path, repository remote, or Claude Code plugin registration
changes.

1. Treat the repository as the single source of truth, not any derived cache or symlink.
2. Update `.claude-plugin/marketplace.json` and `plugin.json` if the plugin root moved.
3. Search active surfaces for the old path/name: marketplace/plugin manifests, CI workflow
   files, and any `SKILL.md`/`CHANGELOG.md` with a hardcoded path. Historical mentions in
   old `CHANGELOG.md` bullets are not blockers once active config is clean.
4. Remove stale bytecode/cache files that preserve the old path.
5. Verify skill discovery by opening Claude Code and confirming the affected skills appear
   under the plugin.
6. Run `python3 skills/skillify/scripts/validate-skill-format.py` and
   `python3 skills/skillify/scripts/validate-runtime-hygiene.py` to confirm no format or
   hygiene violations were introduced.
7. Report status only from real tool output; list unresolved caveats separately rather than
   burying them in a success summary.
