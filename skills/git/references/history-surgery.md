# Git History-Surgery Recipes

Every rewrite here runs without an interactive editor and leaves `git rebase --abort` or `git reflog` as a way back — never trade a small mess for a bigger one.

## Contents

- [Hard rules](#hard-rules)
- [Pre-flight — is this commit safe to rewrite?](#pre-flight--is-this-commit-safe-to-rewrite)
- [Fixup flow (non-interactive-safe)](#fixup-flow-non-interactive-safe)
- [Reword a commit](#reword-a-commit)
- [Split a commit](#split-a-commit)
- [Undo decision table](#undo-decision-table)
- [Scripted bisect](#scripted-bisect)
  - [Custom bisect terms](#custom-bisect-terms)
- [Recovering from mid-rebase mess](#recovering-from-mid-rebase-mess)

## Hard rules

| Concern | Do / Use | Never |
|---|---|---|
| Rewording or squashing a commit already pushed to a shared branch | Open a new commit, or `git revert` | Force-push a rewritten history without team agreement first |
| A rebase hits conflicts that don't make sense | `git rebase --abort` immediately, reassess | Keep resolving blindly and hope it converges |
| A commit seems to have disappeared after reset/rebase | `git reflog`, then recover it | Assume it's gone and redo the work from memory |
| Interactive rebase in a non-interactive environment | Script it via `GIT_SEQUENCE_EDITOR` / `GIT_EDITOR` (recipes below) | Skip the rewrite because there's no TTY for `$EDITOR` |

## Pre-flight — is this commit safe to rewrite?

Run this before any recipe below that touches an existing commit (reword, split, fixup target, or interactive rebase):

```bash
git branch -r --contains <sha>
```

Empty output → `<sha>` isn't on any remote-tracking branch; rewrite it freely with the recipes in this file. Non-empty output → treat it as shared: prefer the revert-based rows in the undo table over any rewrite, and never force-push over it without confirming with whoever else has it.

## Fixup flow (non-interactive-safe)

Use this to fold a small correction into an earlier commit without hand-editing a rebase todo list.

```bash
git commit --fixup=<sha>                                    # marks this commit as a fixup for <sha>
GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash <sha>~1  # reorders + squashes with no editor prompt
```

`GIT_SEQUENCE_EDITOR=true` replaces the interactive todo-list edit step with the no-op `true` command, so the todo list `autosquash` already generated is accepted as-is — no editor, no TTY required. Confirm the result:

```bash
git log --oneline -10
```

The fixup commit is gone; its changes are folded into `<sha>`.

## Reword a commit

**Last commit (HEAD)** — fully non-interactive, no sequence editor needed:

```bash
git commit --amend -m "<new subject>"
```

Only amend a commit that is unpushed, or pushed to a branch nobody else has fetched (confirm with `git branch -r --contains HEAD` — empty output means safe).

**An older commit** — non-interactive via the two editor environment variables git already supports:

```bash
short=$(git rev-parse --short <sha>)
GIT_SEQUENCE_EDITOR="sed -i.bak 's/^pick $short/reword $short/'" \
GIT_EDITOR='printf "%s\n" "<new subject>" >' \
git rebase -i <sha>~1
```

`GIT_SEQUENCE_EDITOR` flips that one line's action from `pick` to `reword` in the rebase todo list — but the todo always lists commits by their abbreviated SHA, so resolve `<sha>` through `git rev-parse --short` first and match on `$short`, not on `<sha>` itself; matching on a full 40-char SHA never hits (the `pick` line never contains it), so the rebase silently completes with nothing reworded. `GIT_EDITOR` then receives the commit-message file as its argument; because git invokes the editor command through the shell, a command ending in `>` redirects into that file — `printf` writes the new subject, no editor UI involved. `sed -i.bak` is the portable in-place form (both BSD/macOS and GNU sed accept an attached backup suffix with no space); the backup lands inside `.git/rebase-merge/`, which git deletes itself once the rebase finishes (whether it completes or is aborted) — there is no `.bak` file left in the working tree to clean up, and running `rm -f *.bak` from the repo root finds nothing (and errors under zsh's default glob behavior when it doesn't).

## Split a commit

Turn one commit into two or more, non-interactively:

```bash
GIT_SEQUENCE_EDITOR="sed -i.bak 's/^pick <sha>/edit <sha>/'" git rebase -i <sha>~1
rm -f *.bak
git reset HEAD~1                # uncommit, keep the changes in the working tree
git add -p                      # stage the first logical chunk
git commit -m "<first message>"
git add -A
git commit -m "<second message>"
git rebase --continue
```

`edit` pauses the rebase at `<sha>` with its changes applied but not yet re-committed; `git reset HEAD~1` un-commits them into the working tree so the atomic-commit `add -p` loop (see the parent `SKILL.md`) applies exactly as it would for any other mixed diff.

## Undo decision table

Pick the row by whether the commit is pushed and whether the branch is shared — the two facts that determine whether a rewrite is safe.

| Situation | Pushed? | Shared? | Command | Why |
|---|---|---|---|---|
| Undo the last local commit, keep the changes staged | No | No | `git reset --soft HEAD~1` | Only local history moves; nothing else has seen this commit |
| Undo the last local commit, discard the changes | No | No | `git reset --hard HEAD~1` | Nothing shared depends on it |
| Undo a commit already on a shared/pushed branch | Yes | Yes | `git revert <sha>` | Adds a new commit undoing the change; preserves the history others already pulled |
| Restore one file to its committed state | either | either | `git restore --staged --worktree <file>` | File-scoped; no history rewrite at all |
| Recover a commit lost to a reset or rebase | either | either | `git reflog` → `git reset --hard <reflog-sha>` or `git cherry-pick <reflog-sha>` | The reflog retains unreachable commits for roughly 90 days by default |
| Undo a merge commit on a shared branch | Yes | Yes | `git revert -m 1 <merge-sha>` | Reverting a merge requires naming which parent is "mainline" via `-m` |

Grey zone: a commit pushed only to your own remote fork, with no PR opened and no collaborator confirmed to have fetched it, behaves like the unpushed case — `git branch -r --contains <sha>` on the shared remote is the check that resolves the ambiguity.

## Scripted bisect

```bash
git bisect start <bad-sha> <good-sha>
git bisect run <test-cmd>            # e.g. ./run-tests.sh, `pytest -x`, `npm test`
git bisect reset
```

`<test-cmd>` must exit `0` on a good commit and a nonzero code (1–127) on a bad one; exit code `125` tells bisect the commit is untestable and to skip it — use that for commits where the build itself doesn't compile. Wrap any setup the test needs (dependency install, env vars) inside `<test-cmd>` itself so each checked-out commit is self-contained; a bisect run that assumes state left over from the previous commit produces false results.

### Custom bisect terms

When the property being isolated isn't naturally "bad"/"good" — a performance regression, a UI layout break — relabel the endpoints so the bisect log reads correctly:

```bash
git bisect start --term-old=fast --term-new=slow
git bisect fast <sha>
git bisect slow <sha>
git bisect run <test-cmd>
```

`--term-old`/`--term-new` rename the two states everywhere (including the marking commands); pick names that match the property under test so the eventual `git bisect log` output reads as a sentence, not a translation exercise.

## Recovering from mid-rebase mess

`git rebase --abort` is the first move, always — before any manual conflict edit, before `rm -rf .git/rebase-merge`, before anything else:

```bash
git rebase --abort
git status --short          # confirm it's back to the pre-rebase state
```

If `--abort` itself fails (rare — typically an interrupted process left `.git/rebase-merge` in an inconsistent state), fall back to:

```bash
git rebase --quit
git reflog                  # find the commit HEAD pointed to before the rebase started
git reset --hard <reflog-sha>
```

`rebase --quit` stops the rebase machinery without trying to restore the working tree, then the reflog gives back the exact pre-rebase `HEAD` to reset onto.
