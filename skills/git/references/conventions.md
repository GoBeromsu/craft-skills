# Git Conventions Reference

A commit-message, scope, or merge-strategy convention only has authority when it matches what the repo's own history already does — detect before conforming.

## Hard rules

| Concern | Do / Use | Never |
|---|---|---|
| Choosing a commit-message convention | Detect the repo's actual prefix ratio first (see `SKILL.md` PHASE 0) | Import conventional commits into a repo that doesn't already use them because "it's the standard" |
| Choosing a merge strategy for a new PR | Detect the repo's merge-commit ratio, match it | Introduce a different merge strategy mid-project without team agreement |
| Naming a scope in a commit subject | Derive it from the directories/packages actually touched | Invent a scope name that doesn't correspond to any real path in the repo |
| A repo's prefix word isn't in the canonical type list | Match it if it appears with meaningful frequency (see Type-vocabulary drift) | Silently normalize a repeated non-canonical word to the nearest canonical type |

## Conventional-commit type reference

Use this table only after PHASE 0's prefix-ratio check confirms the repo already uses conventional commits.

| Type | When |
|---|---|
| `feat` | A new user-facing capability |
| `fix` | A bug fix |
| `chore` | Maintenance with no production behavior change (deps, tooling, config) |
| `docs` | Documentation only |
| `refactor` | Restructuring with no behavior change |
| `test` | Adding or adjusting tests only |
| `style` | Formatting only, no logic change |
| `perf` | A performance improvement with no behavior change |
| `build` | Build system or packaging changes |
| `ci` | CI configuration changes |
| `revert` | Reverts a previous commit |

A breaking change adds `!` after the type/scope (`feat(auth)!: ...`) in addition to the footer below — the two signals are independent and both are expected together.

## Type-vocabulary drift

A repo can pass the PHASE 0 prefix-ratio check (≥ 2/3 prefixed) while using a type vocabulary that diverges from the canonical 11 types above. Surface the repo's actual words before assuming the canonical list applies verbatim:

```bash
git log --format=%s -30 | grep -oE '^[a-z]+' | sort | uniq -c | sort -rn
```

Reading: this ranks every prefix word the repo actually uses by frequency. A word like `hotfix`, `release`, or `wip` appearing with meaningful frequency (roughly ≥ 3 of the 30) means the repo's real vocabulary includes types the canonical list doesn't — use the repo's own words for those cases rather than forcing them into the nearest canonical type. A prefix appearing once or twice is noise (a typo or an outlier commit), not a vocabulary addition.

## Scopes from repo directories

Derive the parenthetical scope from what the staged diff actually touches, never from a generic guess:

```bash
git diff --staged --name-only | sed -E 's#^([^/]+)/.*#\1#' | sort -u
```

Exactly one top-level directory touched → use it as the scope: `fix(auth): ...`. More than one → omit the scope, or use the smallest shared ancestor directory if one exists and is meaningful. Grey zone — in a monorepo, the package name (from `package.json` `"name"` or `pyproject.toml` `[project].name`) is often more meaningful to readers than the raw directory name; check it when the directory name alone would be ambiguous (e.g. `packages/core` vs. a scope of `core`).

SMELL / CLEAN, same diff:

```
SMELL: fix(stuff): correct token refresh bug
CLEAN: fix(auth): correct token refresh bug
```

`stuff` names nothing on disk; `auth` is what the detection command above actually printed for this diff. A scope that doesn't correspond to a real path forces the next reader to go check the diff anyway — it adds a lookup step instead of removing one.

## Breaking-change footer

```
BREAKING CHANGE: <what breaks and the migration path>
```

A footer paragraph, separated from the body by a blank line. Reading precedent already in the repo:

```bash
git log --grep='BREAKING CHANGE' --oneline
```

Empty output on a repo that otherwise uses conventional commits doesn't mean breaking changes never happened — it means they weren't flagged. Flag every one from here forward regardless of history.

## Worked example — a full breaking-change commit message

```
feat(auth)!: require refresh-token rotation on every login

Rotating the refresh token on each login closes a replay window where
a leaked long-lived token stayed valid indefinitely. Sessions issued
before this change are invalidated on next refresh.

BREAKING CHANGE: clients that cache the refresh token across restarts
must re-authenticate once; store the new token from every login
response instead of only the first.

Closes: #482
```

Reading, rule by rule: `feat` + `(auth)` come from the type table and the scope-detection command above; `!` marks the breaking change independently of the footer; the subject stays under 72 chars and imperative; the body explains *why*, not a restatement of the diff; `BREAKING CHANGE:` gives the migration path a caller needs; `Closes:` links the tracked issue per the parent `SKILL.md`'s footer contract. Every line traces to a rule stated above it.

## Changelog-generation compatibility

Conventional-commit prefixes are machine-readable: `feat:` implies a minor version bump, `fix:` a patch, any `BREAKING CHANGE:` footer (or `!`) a major bump. A changelog generator or release-automation tool derives both the version number and the release notes text directly from this prefix stream — which is the practical reason to adopt the convention at all, and why PHASE 0's ratio check gates it: a repo that hasn't adopted it gets no benefit from a few prefixed commits mixed into free-form ones, only inconsistency.

## Merge strategy table

Detect the repo's actual practice before choosing how to land a PR:

```bash
git log --merges --oneline -30 | wc -l
```

This counts true two-parent merge commits in the last 30 commits on the current branch's history. Confirm the reading with a parent count, which distinguishes a merge commit (2 parents) from a squash or rebase landing (1 parent):

```bash
git log --oneline -30 --first-parent | awk '{print $1}' | while read -r sha; do git log -1 --format=%P "$sha" | wc -w; done
```

| Strategy | Detection reading | Choose-when | Absolute rule |
|---|---|---|---|
| Merge commit (`--no-ff`) | Merge-commit count is a meaningful fraction (roughly ≥ 20%) of the last 30 | The repo already preserves branch topology in its history | Never rebase a branch that has already been merged into a shared branch's history |
| Squash merge | Merge-commit count near 0; PR platform's squash button used | The repo keeps exactly one commit per PR/feature in `main`'s history | Squash locally only pre-push; never squash commits that have already been pushed and reviewed without the reviewer's agreement |
| Rebase merge | Merge-commit count near 0; multiple small commits per feature survive intact in `main`'s linear history | The repo values a granular, linear per-commit history | Rebase only unpushed commits, or commits on a branch confirmed not shared (see `history-surgery.md`'s safety rules) |

Grey zone: a ratio landing between roughly 10% and 20%, or a repo younger than ~20 commits, doesn't give a clean reading either way — default to whatever the remote PR platform's configured default merge button does (check the repo/org settings if reachable), or ask before choosing.

A one-line pointer, not a dependency: on a GitHub-hosted repo, `gh repo view --json squashMergeAllowed,mergeCommitAllowed,rebaseMergeAllowed` reads the platform's allowed strategies directly, which resolves the grey zone above without needing the ratio heuristic at all.
