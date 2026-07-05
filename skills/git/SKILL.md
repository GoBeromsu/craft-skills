---
name: git
description: '"commit this", "커밋해줘", "rebase", "squash", "커밋 정리" — atomic-commit discipline, incumbent repo-style detection, commit/branch/PR conventions, and non-interactive-safe history surgery (fixup/autosquash, scripted bisect, undo recovery).'
version: 1.0.0
allowed-tools: [Read, Bash, Grep, Glob]
compatibility: claude-code, codex
---

# git

Version-control craft, in order: **truth over memory, one logical change per commit, incumbent style over personal preference.**

## Overview

This skill is an index. Shared rules live here; the deep recipe catalogs live in `references/` — load the matching reference before acting on history. Detection-by-code is the method throughout: every rule ships a copy-pasteable command with a threshold and a pass/fail reading, because a repo's actual history is always more authoritative than a general convention.

## When to Use

- Committing any change — "commit this", "커밋해줘", "커밋 정리".
- Rebasing, squashing, or otherwise rewriting local or remote-tracked history.
- Naming a branch, sizing a PR, or deciding a merge strategy.
- Recovering from a rebase gone wrong or undoing a commit.

Not for: git worktree lifecycle (branch/worktree creation and cleanup — load the `worktree` skill instead), PR review process or issue routing (the repo's own `AGENTS.md` development-flow section owns that).

## PHASE 0 — ground truth + repo-style detection (run first, every time)

Do not write a commit message, rebase, or push before this gate. Stale mental models of "what's on this branch" cause the two most common failures in this domain: committing the wrong thing, and rewriting history that's no longer what you think it is.

### Ground truth

```bash
git status --short
git diff --stat
git diff --staged --stat
git branch --show-current
git log -15 --oneline
git rev-parse --abbrev-ref @{upstream}
git merge-base HEAD origin/main
```

Read every line before acting: `status --short` shows what's changed and whether staged/unstaged are mixed; the two `diff --stat` calls separate "about to be committed" from "not yet staged"; `branch --show-current` confirms you're not on a protected branch (hand off to `worktree` if you are); `log -15` is the local style sample; `@{upstream}` confirms a remote-tracking branch exists before any push-safety command matters; `merge-base HEAD origin/main` is the divergence point the PR-sizing diff below measures from.

### Repo-style detection

```bash
git log --oneline -30 | grep -ciE '^[0-9a-f]+ (feat|fix|chore|docs|refactor|test|style|perf|build|ci|revert)(\([a-z0-9_-]+\))?!?:'
git log -30 --format=%s | perl -CSD -ne 'print if /[\x{AC00}-\x{D7A3}]/' | wc -l
git log -30 --format=%s | awk '{ s += length($0); n++ } END { if (n) print s/n }'
```

Reading: first count ÷ 30 ≥ 2/3 → the repo uses conventional-commit prefixes; use them (type table in `references/conventions.md`). Below 2/3 → do not import conventional commits onto an unprefixed repo; match its plain imperative-subject style. Second command counts commits containing Hangul; count ÷ 30 > half → write commit subjects in Korean, keeping whichever prefix convention the first check found. Third command gives the repo's actual average subject length — target that norm, not the ≤72 ceiling as a goal in itself. **Incumbent style always wins over personal preference or an outside standard.**

## Atomic commit law

One commit = one logical change. A commit whose message needs "and" to describe it is two commits.

```bash
git status --short                  # every changed file
git diff <file>                     # read the full diff before staging anything
git add -p <file>                   # stage one hunk at a time: y/n/s/e/q
git diff --staged                   # confirm only the intended change is staged
git commit -m "<subject per contract below>"
git status --short                  # confirm remaining hunks await the next commit
```

Repeat the `add -p` → `diff --staged` → `commit` loop once per logical change until `git status --short` is empty.

Detect a diff that spans unrelated concerns:

```bash
git diff --staged --name-only | sed -E 's#/[^/]+$##' | sort -u | wc -l
```

More than one top-level directory touched for **unrelated** reasons is a split signal. Grey zone — this is judgment, not a hard gate: a single cohesive change that happens to touch many files (a rename across the codebase, a type propagated through its callers) is one commit even at a high count; the test is whether the commit message needs "and", not the file count.

## Commit message contract

- **Subject**: imperative mood ("Fix", never "Fixed"/"Fixes"), matches the repo's detected length norm, hard ceiling 72 chars.
- **Body**: why the change was made and what was traded off — never a restatement of the diff.
- **Footer**: `Refs: #<issue>` / `Closes: #<issue>` when it resolves a tracked issue; `BREAKING CHANGE: <description>` when applicable (see `references/conventions.md`).
- Blank line between subject, body, and footer — the subject alone is what `git log --oneline` and most UIs show.

```bash
git log -1 --format=%s | awk '{print length}'
```

Over 72 → rewrite the subject before pushing (or use the reword recipe in `references/history-surgery.md` if already committed).

## Pre-commit self-review

```bash
git diff --staged
```

Read every hunk top to bottom before writing the commit message — this is the last checkpoint before the change becomes permanent history, and a message written from memory drifts from what's actually staged.

```bash
git diff --staged | grep -nE '^\+.*(console\.log\(|print\(|pdb\.set_trace|debugger;|TODO: remove|FIXME: remove)'
```

Any hit → unstage or fix before committing.

## Branch naming from incumbent

```bash
git branch -a --format='%(refname:short)' | grep -vE 'HEAD|->|(^|/)(main|master|develop)$'
git branch -a --format='%(refname:short)' | grep -cE '^(origin/)?(feat|feature|fix|bugfix|chore|hotfix)/[a-z0-9._-]+$'
```

Ratio ≥ 2/3 of listed branches matching one shape → follow it, matching the exact type spelling found (`feat/` and `feature/` are different conventions — copy the one observed, don't guess). No dominant shape found (fresh repo, or ticket-based names) → default to `<type>/<slug>` using the type list in `references/conventions.md`. Tool-managed branch names (e.g. the `worktree` skill's lane branches) are outside this rule — the managing skill owns them; apply incumbent detection only to branches you name yourself.

## PR sizing rule

```bash
git diff origin/main...HEAD --shortstat
```

Insertions + deletions over ~400 → the diff is large enough to slow review meaningfully; split before opening the PR. When the work must land as one deployable unit, stack branches instead of collapsing it into one PR:

```bash
git checkout -b <slug>-2 <slug>-1     # second slice branches off the first, not off main
```

Open one PR per slice, each targeting the previous branch. When the base branch's PR updates, rebase the next slice onto its new tip:

```bash
git log <slug>-1..<slug>-2 --oneline  # confirm only the intended delta shows
```

## Safety rules

| Concern | Do / Use | Never |
|---|---|---|
| Update a pushed branch after rewriting history | `git push --force-with-lease` | `git push --force` |
| Mid-rebase gets tangled or conflicts you don't understand | `git rebase --abort`, reassess, retry | Force-push a half-finished rebase to "fix" it forward |
| Undo a change on a branch others have pulled | `git revert <sha>` | `git reset --hard` on a branch anyone else has fetched |
| Uncertain whether a branch is shared | `git branch -r --contains <sha>`, or ask before rewriting | Assume "probably just me" and rewrite anyway |

`git rebase --abort` is always the first recovery move for a rebase in trouble — it returns to the exact pre-rebase state in one command, before any manual conflict-resolution attempt.

## Requirements

- `git` >= 2.23 (for `git restore` and the default `--force-with-lease` behavior used throughout).
- POSIX `grep`, `awk`, `sed` — commands in this package and `references/history-surgery.md` use `sed -i.bak` (portable across BSD and GNU sed; delete the `.bak` file after).
- `perl` (present by default on macOS and virtually all Linux distributions) — used for the Unicode-aware language check in the repo-style detection block, since the platform's default `grep` may lack `-P`/PCRE support.
- A project-specific test/lint command to pass to `git bisect run` when using `references/history-surgery.md`'s scripted bisect recipe.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It's a couple of small fixes, one commit is fine." | A mixed diff makes `git revert` and `git bisect` useless for either change on its own. `git add -p` splits it — same edits, one extra commit call. |
| "This repo has no obvious convention, I'll just use conventional commits — they're better." | Detect first (repo-style prefix ratio above). A repo with no prefix history gets plain imperative subjects, not an imported outside standard. |
| "Force-pushing is faster than untangling this." | `--force` overwrites whatever a collaborator pushed in between with no warning. `--force-with-lease` refuses when the remote moved — that's the entire point of using it. |
| "The rebase got messy, I'll reset --hard and redo the edits." | `git rebase --abort` restores the exact pre-rebase state in one command; no reconstruction needed. |
| "I'll write the commit message after I see what changed." | Read `git diff --staged` before writing the message — a message composed from memory drifts from what's actually staged. |
| "This PR is 900 lines but it's all one feature." | Reviewability doesn't track conceptual unity. Split via stacked branches; each PR still reviews independently. |
| "I already know branch-naming conventions from my last project." | Conventions are per-repo. Scan `git branch -a` for this repo's actual shape before naming anything. |

## Red Flags

- A commit message that needed "and" to describe it in one sentence.
- `git push --force` in shell history instead of `--force-with-lease`.
- A PR diff stat over ~400 changed lines with no stacked-branch split plan.
- `git diff --staged` never read before `git commit` — message doesn't match what's staged.
- A rebase abandoned mid-way without `git rebase --abort` — leftover `<<<<<<<` conflict markers or a lingering `.git/rebase-merge` directory.
- A new commit introducing a prefix or naming style the last 30 commits don't use.

## Verification

- [ ] Ground-truth block ran before the first edit, commit, or rebase this session.
- [ ] Repo-style detection ran before the first commit (prefix ratio, language, subject-length norm).
- [ ] Staged diff is one logical change (`git add -p` used to split any mixed diff).
- [ ] `git diff --staged` was read in full before writing the commit message.
- [ ] Commit subject is imperative, matches the repo's observed length norm, ≤72 chars.
- [ ] Branch name matches the incumbent shape, or the `<type>/<slug>` default on a fresh repo.
- [ ] PR diff is ≤~400 changed lines, or a stacked-branch split plan exists.
- [ ] No `--force` in history for this change — only `--force-with-lease`, only on branches confirmed not shared.
