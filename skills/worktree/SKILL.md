---
name: worktree
description: '"git wt", "make a worktree", "new worktree", "/worktree" — create (or reuse) a named git worktree off the default branch and install the git-guard rails in the target repo.'
version: 2.0.0
allowed-tools: [Bash, Read, Write, Edit, Grep, Glob]
compatibility: claude-code, codex
---

# Worktree Workflow Skill

## Purpose

Make a named worktree off the default branch with one command, and never work directly on a protected branch. Install the git-guard enforcement layer on first run (idempotent).

`git wt <name>` is a plain worktree maker — no issue numbers, no type labels. Pick a short name (e.g. a small fixed pool `lane-1`~`lane-3`) and reuse it; don't spawn a new worktree per task.

---

## Core Rule

```
git wt <name>  →  branch <name>  →  worktree at $WORKTREE_ROOT/<name>
```

The default branch (`main`) is blocked at pre-commit and pre-push by the git-guard hooks. Never work directly on it.

---

## Step 1 — Self-Install (idempotent, run on first invocation)

Check whether the git-guard rails are installed in the target repo:

```bash
git config core.hooksPath           # must equal ".githooks"
git config alias.wt                 # must be set
ls scripts/git-guard/setup-hooks.sh # must exist
```

If any check fails, run the bundled installer from the target repo root:

```bash
sh skills/worktree/scripts/install.sh
```

`install.sh` is the single entry point. It never clobbers existing files:

1. Copies the guard scripts into the repo at `scripts/git-guard/` (skip per-file if present).
2. Copies the shipped `githooks/pre-commit` and `githooks/pre-push` into `.githooks/` (skip if present) — real files in the skill, not improvised stubs.
3. Runs `scripts/git-guard/setup-hooks.sh` to wire `core.hooksPath`, register `alias.wt`, and `chmod +x` the scripts and hooks.

Both installers are idempotent. After install, confirm:

```
[git-guard] core.hooksPath  = .githooks
[git-guard] alias.wt        = ...
[git-guard] setup complete  — run `git wt <name>` to create a worktree.
```

---

## Step 2 — Create a Worktree

```bash
git wt <name>          # e.g. git wt lane-1
```

`git wt <name>` creates (or reuses) a worktree named `<name>` off `origin/<default>` and prints its path. The worktree lives **outside** the repo root (`$WORKTREE_ROOT`, default `<repo-parent>/<repo>-worktrees/<name>`) so `git status` stays clean. Running it again with the same name returns the existing path — no duplicate. `cd` to the printed path to begin work.

The name is sanitized to be safe as both a branch and a path segment (lowercased; non-`[a-z0-9._/-]` → `-`). If a branch of that name already exists, the worktree checks it out; otherwise it branches off `origin/<default>`.

---

## Step 3 — Day-to-Day Commands

```bash
git wt ls                  # list all worktrees
git wt rm <name>           # remove a worktree (preferred over rm -rf)
git wt rm <name> --force   # force-remove a dirty worktree
```

Use `git wt rm` — never `rm -rf`. Manual deletion leaves phantom `.git/worktrees/` entries that block `git branch -d` and `git checkout` until `git worktree prune` runs. `git wt rm` calls `git worktree remove` + `git worktree prune` automatically. The branch is **kept** — delete it after merge with `git branch -d`.

### After the PR is merged — cleanup order matters

The branch is **held by its worktree**. You cannot delete the branch while the worktree exists, and you cannot run the cleanup *from inside* the worktree being removed:

1. **Don't merge with `--delete-branch`.** `gh pr merge --squash --delete-branch` fails with `cannot delete branch '<branch>' used by worktree` whenever a worktree still holds it. Merge plain, then clean up locally.
2. **`cd` to the primary checkout first**, then:

```bash
git wt rm <name>          # remove worktree + prune (run from primary checkout)
git branch -d <name>      # branch is now free to delete
```

Use `git branch -d` (not `-D`) — a merged branch deletes cleanly, and the safe form catches the "not actually merged" case.

---

## Step 4 — Freshness

- `pre-push`: blocks the push if the branch is behind `origin` (exit 1).
- `pre-commit` and session start: warn if behind, do not block (exit 0).

To sync: `git pull --rebase`.

---

## Step 5 — Escape Hatch

For rare deliberate maintenance directly on a protected branch:

```bash
GIT_GUARD_PROTECTED= git <cmd>
```

Setting `GIT_GUARD_PROTECTED` to empty disables enforcement for that invocation only. Document the reason in the commit message.

To bypass the asset guard for an intentional large-file exception:

```bash
GIT_GUARD_ALLOW_ASSETS=1 git <cmd>
```

---

## Optional Tailscale Extension

This extension activates only when the environment variable `CRAFT_WT_REMOTE_HOST` is set.

### Flow

1. Verify reachability: `ping -c 1 $CRAFT_WT_REMOTE_HOST` (or `tailscale ping`). Abort with a clear message if unreachable.
2. SSH to the host: `ssh $CRAFT_WT_REMOTE_HOST`.
3. Open (or attach to) a named tmux session: `tmux new-session -As wt-<name>` on the remote.
4. Run `git wt <name>` inside the tmux session to create a dedicated remote worktree.
5. Work inside the remote worktree via the tmux session.

### Teardown (explicit — do not auto-detect)

Ask the user to confirm before tearing down:

> "Work complete. Confirm teardown? (y/N)"

On confirmation:
1. Commit and push all changes, or open a PR (`gh pr create`).
2. Close the tmux session: `tmux kill-session -t wt-<name>`.
3. Remove the remote worktree: `git wt rm <name>` on the remote.

Never auto-detect completion and never tear down without explicit user confirmation.

---

## Requirements / Environment

| Variable | Purpose | Required |
|---|---|---|
| `WORKTREE_ROOT` | Where worktrees are created | No — defaults to `<repo-parent>/<repo>-worktrees` |
| `CRAFT_WT_REMOTE_HOST` | Tailscale hostname or `user@host` for remote execution | No — omit to use local-only mode |

Set in `.env` (gitignored). See `.env.example` for the placeholder.

Dependencies:
- `git` >= 2.5 (worktree support).
- `tmux` + `tailscale` (or equivalent) — required only for the optional Tailscale remote extension.

---

## Guard Scripts Reference

| Script | Role |
|---|---|
| `scripts/install.sh` | Bundled first-run installer: copies guard scripts + hooks into the repo, then runs `setup-hooks.sh`. The single entry point `worktree`/`init` delegate to |
| `githooks/pre-commit` | Shipped hook: assert-not-main + deny-assets (staged) + check-freshness (warn) |
| `githooks/pre-push` | Shipped hook: assert-not-main + check-freshness (block) + deny-assets (push) |
| `scripts/lib.sh` | Shared helpers: `gg_warn`, `gg_die`, protected-branch list |
| `scripts/assert-not-main.sh` | Exits 1 when HEAD is on a protected branch |
| `scripts/check-freshness.sh` | Compares HEAD to upstream; `block` (exit 1) or `warn` mode |
| `scripts/wt.sh` | Simple worktree maker/manager (`<name>`, `rm`, `ls`) |
| `scripts/setup-hooks.sh` | Idempotent post-clone setup: `core.hooksPath`, `alias.wt`, `chmod +x` |
| `scripts/deny-assets.sh` | Blocks model weights, media files, and blobs > 5 MB at commit/push |

---

## Rationalizations / Red Flags

- `gh pr merge --delete-branch` exiting with `cannot delete branch '<branch>' used by worktree` is expected, not a fault — the worktree still holds it. Merge without `--delete-branch`, then `git wt rm <name>` + `git branch -d <name>`.
- Cleanup commands failing with `... already used by worktree` usually means you are running them *inside* the worktree you are removing. `cd` to the primary checkout and retry.
- A phantom `git worktree list` entry after a manual `rm -rf` clears with `git worktree prune` — then the branch can be deleted or checked out.
- Spawning a fresh worktree per task instead of reusing a small fixed pool — pick a `lane-N` and reuse it.
- Never set `GIT_GUARD_PROTECTED=` in shell startup files — it disables enforcement globally and permanently.
