---
name: git
description: 'Guides version-control craft: a ground-truth and incumbent-style detection gate before the first git mutation, the atomic-commit `git add -p` split protocol, commit/branch/PR conventions matched to the repo''s own history, and non-interactive-safe history surgery (fixup, reword, split, scripted bisect, undo). Use when committing a change ("commit this", "커밋해줘"), rebasing or squashing history, sizing a PR, recovering from a broken rebase, or running "git wt" to create an isolated worktree with the git-guard rails. Not for hook-enforcement mechanics (runtime/lint/pre-commit guard authoring) — that belongs to hookify.'
metadata:
  version: 2.1.0
---

# git

Version-control craft, in order: **truth over memory, one logical change per commit, incumbent style over personal preference.** A commit is done right when it traces to one logical change, matches the repo's own detected conventions rather than an imported standard, and never rewrites shared history without the safe path. Deep recipes live in `references/`: `conventions.md` (commit-type/scope/merge-strategy tables), `history-surgery.md` (non-interactive fixup/reword/split/bisect/undo), `worktree.md` (`git wt` isolated-worktree workflow + guard install). Detection-by-code runs throughout — every rule ships a copy-pasteable command with a threshold, because the repo's actual history always outranks a general convention.
## Request mode

For a commit, rebase, or staging request, run the ground-truth gate before the first Git mutation. For an investigation-shaped request — history, blame, why, or status — collect and report evidence without changing the worktree, index, or history. Investigation findings do not authorize a follow-on mutation.


## Ground truth (run first, every time)

```bash
BASE=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || true)
if ! git rev-parse --verify --quiet "${BASE}^{commit}" >/dev/null; then
  BASE=
  for remote in $(git remote); do
    candidate=$(git symbolic-ref --quiet --short "refs/remotes/$remote/HEAD" 2>/dev/null || true)
    if git rev-parse --verify --quiet "${candidate}^{commit}" >/dev/null; then
      BASE=$candidate
      break
    fi
  done
fi
git status --short
git diff --stat
git diff --staged --stat
git branch --show-current
git log -15 --oneline
git rev-parse --abbrev-ref @{upstream} 2>/dev/null || echo "no upstream — first push"
if [ -n "$BASE" ]; then
  git merge-base HEAD "$BASE"
else
  echo "no comparison base — record PR size without a merge-base"
fi
```

`BASE` uses `origin/HEAD` when it resolves to a commit, then the first existing remote default branch. If neither exists, record `no comparison base` and do not call `merge-base` or a base-relative PR diff. The two `diff --stat` calls separate staged from unstaged; `log -15` samples local style; a missing `@{upstream}` means an unpushed branch, not a failure; `merge-base` anchors the PR-sizing diff below.

## Repo-style detection

```bash
total=$(git log --oneline -30 | wc -l | tr -d ' ')
git log --oneline -30 | grep -ciE '^[0-9a-f]+ (feat|fix|chore|docs|refactor|test|style|perf|build|ci|revert)(\([a-z0-9_-]+\))?!?:'
git log -30 --format=%s | perl -CSD -ne 'print if /[\x{AC00}-\x{D7A3}]/' | wc -l
git log -30 --format=%s | awk '{ s += length($0); n++ } END { if (n) print s/n }'
```

Divide every count by `total`, not a hardcoded 30 — a young repo samples fewer. First ratio ≥ 2/3 → use conventional-commit prefixes (`references/conventions.md`); below that → plain imperative subjects, never import the standard onto an unprefixed repo. Second command's Hangul ratio over half → write subjects in Korean. Third gives the actual average subject length — target that, not a ≤72 ceiling as a goal in itself. **Incumbent style always wins.**

## Atomic commit law

One commit = one requested logical change; a message needing "and" is two commits.

```bash
git status --short
git diff <file>
git add -p <file>          # stage one hunk at a time: y/n/s/e/q
git diff --staged
git commit -m "<subject>"
git status --short
```

Repeat `add -p` → `diff --staged` → `commit` for each requested logical change. Leave unrelated staged or unstaged work untouched: stage only the user-requested files or hunks, never use `git add -A` / `git add .`, and do not require an empty `status --short` as completion. Detect a mixed diff:

```bash
git diff --staged --name-only | sed -E 's#/[^/]+$##' | sort -u | wc -l
```

More than one top-level directory touched for **unrelated** reasons is a split signal — judgment, not a hard gate: a rename across the codebase is one commit even at a high count. The test is whether the message needs "and", not the file count.

## Commit message contract

- **Subject**: imperative ("Fix", never "Fixed"), matches the repo's detected length norm, ≤72 chars.
- **Body**: why and what was traded off — never a restatement of the diff.
- **Footer**: `Refs: #<issue>` / `Closes: #<issue>`; `BREAKING CHANGE: <description>` when applicable (`references/conventions.md`).
- Blank line between subject, body, footer.

```bash
git log -1 --format=%s | awk '{print length}'
```

Over 72 → reword before pushing (`references/history-surgery.md` if already committed).

## Pre-commit self-review

```bash
git diff --staged
git diff --staged | grep -nE '^\+.*(console\.log\(|print\(|pdb\.set_trace|debugger;|TODO: remove|FIXME: remove)'
```

Read every hunk before writing the message — memory drifts from what's actually staged. Any grep hit → unstage or fix first.

## Branch naming from incumbent

```bash
total=$(git branch -a --format='%(refname:short)' | grep -vE 'HEAD|->|(^|/)(main|master|develop)$' | wc -l | tr -d ' ')
matching=$(git branch -a --format='%(refname:short)' | grep -vE 'HEAD|->|(^|/)(main|master|develop)$' | grep -cE '^(origin/)?(feat|feature|fix|bugfix|chore|hotfix)/[a-z0-9._-]+$')
echo "$matching / $total"
```

Ratio ≥ 2/3 → follow the exact shape observed (`feat/` and `feature/` are different conventions — copy, don't guess). Below 2/3, or `total` is 0 → default to `<type>/<slug>` (`references/conventions.md`). `git wt`'s own lane branches are outside this rule.

## PR sizing

```bash
if [ -n "$BASE" ]; then
  git diff "$BASE"...HEAD --shortstat
else
  echo "no comparison base — PR size requires an explicit comparison target"
fi
```

Over ~400 insertions+deletions → split. When there is no comparison base, record that fact and choose an explicit comparison target before sizing. When the work must land as one deployable unit, stack branches instead:

```bash
git checkout -b <slug>-2 <slug>-1   # second slice branches off the first, not main
```

One PR per slice, each targeting the previous branch; rebase the next slice when the base PR updates.

## Safety rules

| Concern | Do | Never |
|---|---|---|
| Update a pushed branch after rewriting history | `git push --force-with-lease` | `git push --force` |
| Rebase gets tangled | `git rebase --abort`, reassess | Force-push a half-finished rebase |
| Undo a change others have pulled | `git revert <sha>` | `git reset --hard` on a shared branch |
| Uncertain whether a branch is shared | `git branch -r --contains <sha>`, or ask | Assume "probably just me" |

## Worktrees

`git wt <name>` creates or reuses an isolated worktree off the default branch — never work directly on a protected branch. Full workflow and guard install live in `references/worktree.md`. Guard scripts register into `.githooks/guards.d/`; `core.hooksPath` itself is owned by `hookify`, not this skill.

## Requirements

- `git` >= 2.23 (`git restore`, default `--force-with-lease`).
- POSIX `grep`, `awk`, `sed` (`sed -i.bak`, portable across BSD and GNU).
- `perl` — Unicode-aware Hangul check in repo-style detection.
- A project test/lint command for `git bisect run` (`references/history-surgery.md`).

## Anti-patterns

- Committing a couple of small fixes together, or writing a message that needs "and" → split with `git add -p`, one commit per logical change; a mixed diff breaks `git revert`/`git bisect` for either change alone.
- Defaulting to conventional-commit prefixes because there's no obvious convention → detect first (`references/conventions.md`); no prefix history means plain imperative subjects, not an imported standard.
- Force-pushing to save time, or `git push --force` sitting in shell history → use `--force-with-lease`, which refuses when the remote moved; `--force` silently overwrites a collaborator's push.
- A PR diff over ~400 changed lines with no stacked-branch plan → split the PR, or stack branches (`git checkout -b <slug>-2 <slug>-1`), one PR per slice.
- Writing the commit message before reading `git diff --staged` in full → read every hunk first; memory drifts from what's actually staged.
- Abandoning a rebase without `git rebase --abort`, leaving conflict markers or a lingering `.git/rebase-merge` → run `git rebase --abort` and reassess.

## Verification

- [ ] Ground-truth block ran before the first Git mutation (staging, commit, or rebase) this session.
- [ ] Repo-style detection ran before the first commit.
- [ ] Staged diff is one logical change.
- [ ] `git diff --staged` was read in full before the commit message was written.
- [ ] Commit subject is imperative, matches the repo's norm, ≤72 chars.
- [ ] Branch name matches the incumbent shape, or `<type>/<slug>` on a fresh repo.
- [ ] PR diff is ≤~400 changed lines, or a stacked-branch plan exists.
- [ ] No `--force` in history for this change — only `--force-with-lease` on confirmed-unshared branches.
