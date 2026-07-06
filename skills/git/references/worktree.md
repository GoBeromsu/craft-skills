# Git Worktree Workflow

Make a named worktree off the default branch with one command, and never work directly on a protected branch.

## Contents

- [Purpose](#purpose)
- [Core rule](#core-rule)
- [Step 1 — propose install](#step-1--propose-install-checked-on-first-invocation)
- [Step 2 — create a worktree](#step-2--create-a-worktree)
- [Step 3 — day-to-day commands](#step-3--day-to-day-commands)
- [Step 4 — freshness](#step-4--freshness)
- [Step 5 — escape hatch](#step-5--escape-hatch)
- [Optional Tailscale extension](#optional-tailscale-extension)
- [Requirements / environment](#requirements--environment)
- [Guard scripts reference](#guard-scripts-reference)
- [Rationalizations / red flags](#rationalizations--red-flags)

## Purpose

`git wt <name>` is a plain worktree maker — no issue numbers, no type labels. Prefer picking a short name from a small fixed pool (e.g. `lane-1`~`lane-3`) and reusing it; a dedicated worktree per parallel work lane is also fine when isolation is needed. Install the git-guard checks in the target repo on first run (idempotent).

## Core rule

```
git wt <name>  →  branch <name>  →  worktree at $WORKTREE_ROOT/<name>
```

`hookify` blocks the default branch (`main`) at pre-commit using the checks this skill registers — never work directly on it.

## Step 1 — Propose install (checked on first invocation)

Check whether the git-guard checks are registered in the target repo:

```bash
git config alias.wt                            # must be set
ls scripts/git-guard/setup-hooks.sh             # must exist
ls .githooks/guards.d/10-assert-not-main.sh     # must exist
```

If any check fails, propose the install to the user in one line before running it — state what it does: copies the guard scripts to `scripts/git-guard/`, registers three checks into `.githooks/guards.d/` (assert-not-main, deny-assets, check-freshness), copies the `pre-push` hook to `.githooks/`, and wires the `git wt` alias. Only after the user accepts, run the bundled installer from the target repo root:

```bash
sh skills/git/scripts/install.sh
```

`install.sh` is the single entry point. It never clobbers existing files:

1. Copies the guard scripts into the repo at `scripts/git-guard/` (skip per-file if present).
2. Copies three guard entries into `.githooks/guards.d/` (skip per-file if present) — real files in the skill, not improvised stubs.
3. Copies the shipped `githooks/pre-push` into `.githooks/` (skip if present).
4. Runs `scripts/git-guard/setup-hooks.sh` to register `alias.wt` and `chmod +x` the scripts and hooks.

**Hand-off — `core.hooksPath` belongs to `hookify`.** This installer never writes `.githooks/pre-commit` and never sets `git config core.hooksPath`. That mechanism — and the dispatcher that runs every executable in `.githooks/guards.d/` in lexical order — is owned exclusively by the `hookify` skill; two owners pointing `core.hooksPath` at the same directory is how installs collide. The three checks registered here sit inert until `core.hooksPath` points at `.githooks`; wire that by installing `hookify` in the target repo, or set it by hand in a repo that doesn't use `hookify`:

```bash
git config core.hooksPath .githooks
```

Both installers are idempotent — safe to re-run once accepted. After install, confirm:

```
[git-guard] alias.wt        = ...
[git-guard] guards.d        : .githooks/guards.d/{10-assert-not-main,20-deny-assets,30-check-freshness}.sh
[git-guard] pre-push hook   : .githooks/pre-push
[git-guard] setup complete  — run `git wt <name>` to create a worktree.
```

## Step 2 — Create a worktree

```bash
git wt <name>          # e.g. git wt lane-1
```

`git wt <name>` creates (or reuses) a worktree named `<name>` off `origin/<default>` and prints its path. The worktree lives **outside** the repo root (`$WORKTREE_ROOT`, default `<repo-parent>/<repo>-worktrees/<name>`) so `git status` stays clean. Running it again with the same name returns the existing path — no duplicate. `cd` to the printed path to begin work.

The name is sanitized to be safe as both a branch and a path segment (lowercased; non-`[a-z0-9._/-]` → `-`). If a branch of that name already exists, the worktree checks it out; otherwise it branches off `origin/<default>`.

## Step 3 — Day-to-day commands

```bash
git wt ls                  # list all worktrees
git wt rm <name>           # remove a worktree (preferred over rm -rf)
git wt rm <name> --force   # force-remove a dirty worktree
```

Use `git wt rm` — never `rm -rf`. Manual deletion leaves phantom `.git/worktrees/` entries that block `git branch -d` and `git checkout` until `git worktree prune` runs. `git wt rm` calls `git worktree remove` + `git worktree prune` automatically. The branch is **kept** — delete it after merge with `git branch -d`.

### After the PR is merged — cleanup order matters

The branch is **held by its worktree**. Delete the branch only after the worktree is gone, and run the cleanup from the primary checkout, not from inside the worktree being removed:

1. **Don't merge with `--delete-branch`.** `gh pr merge --squash --delete-branch` fails with `cannot delete branch '<branch>' used by worktree` whenever a worktree still holds it. Merge plain, then clean up locally.
2. **`cd` to the primary checkout first**, then:

```bash
git wt rm <name>          # remove worktree + prune (run from primary checkout)
git branch -d <name>      # branch is now free to delete
```

Use `git branch -d` (not `-D`) — a merged branch deletes cleanly, and the safe form catches the "not actually merged" case.

## Step 4 — Freshness

- `pre-push` and session start warn (exit 0) if the branch is behind `origin` — never blocks. Pre-commit freshness is the `.githooks/guards.d/30-check-freshness.sh` entry, active once `core.hooksPath` points at `.githooks` (Step 1).

To sync: `git pull --rebase`.

## Step 5 — Escape hatch

For rare deliberate maintenance directly on a protected branch:

```bash
GIT_GUARD_PROTECTED= git <cmd>
```

Setting `GIT_GUARD_PROTECTED` to empty disables enforcement for that invocation only. Document the reason in the commit message.

To bypass the asset guard for an intentional large-file exception:

```bash
GIT_GUARD_ALLOW_ASSETS=1 git <cmd>
```

## Optional Tailscale extension

This extension activates only when the environment variable `${CRAFT_WT_REMOTE_HOST}` is set.

1. Verify reachability: `ping -c 1 ${CRAFT_WT_REMOTE_HOST}` (or `tailscale ping`). Abort with a clear message if unreachable.
2. SSH to the host: `ssh ${CRAFT_WT_REMOTE_HOST}`.
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

## Requirements / environment

| Variable | Purpose | Required |
|---|---|---|
| `${WORKTREE_ROOT}` | Where worktrees are created | No — defaults to `<repo-parent>/<repo>-worktrees` |
| `${CRAFT_WT_REMOTE_HOST}` | Tailscale hostname or `user@host` for remote execution | No — omit to use local-only mode |

Set in `.env` (gitignored). See `../.env.example` for the placeholder.

Dependencies: `git` >= 2.5 (worktree support); `tmux` + `tailscale` (or equivalent) only for the optional Tailscale remote extension.

## Guard scripts reference

| Script | Role |
|---|---|
| `../scripts/install.sh` | Bundled first-run installer: copies guard scripts into the repo, registers them into `.githooks/guards.d/`, installs `.githooks/pre-push`, then runs `setup-hooks.sh`. The single entry point `worktree`/`init` delegate to. |
| `../githooks/guards.d/10-assert-not-main.sh` | Shipped guards.d entry — execs `assert-not-main.sh`. Registered by `install.sh`; dispatched by `hookify`'s pre-commit mechanism. |
| `../githooks/guards.d/20-deny-assets.sh` | Shipped guards.d entry — execs `deny-assets.sh staged`. |
| `../githooks/guards.d/30-check-freshness.sh` | Shipped guards.d entry — execs `check-freshness.sh warn`. |
| `../githooks/pre-push` | Shipped hook, installed directly — not via guards.d, since `hookify` has no push-time surface: assert-not-main + check-freshness (warn) + deny-assets (push). |
| `../scripts/lib.sh` | Shared helpers: `gg_warn`, `gg_die`, protected-branch list. |
| `../scripts/assert-not-main.sh` | Exits 1 when HEAD is on a protected branch. |
| `../scripts/check-freshness.sh` | Compares HEAD to upstream; `block` (exit 1) or `warn` mode. |
| `../scripts/wt.sh` | Simple worktree maker/manager (`<name>`, `rm`, `ls`). |
| `../scripts/setup-hooks.sh` | Idempotent post-clone setup: registers `alias.wt`, `chmod +x`s the scripts and hooks — does not touch `core.hooksPath` (see Step 1 hand-off). |
| `../scripts/deny-assets.sh` | Blocks model weights, media files, and blobs > 5 MB at commit/push. |

## Rationalizations / Red flags

- `gh pr merge --delete-branch` exiting with `cannot delete branch '<branch>' used by worktree` is expected, not a fault — the worktree still holds it. Merge without `--delete-branch`, then `git wt rm <name>` + `git branch -d <name>`.
- Cleanup commands failing with `... already used by worktree` usually means they're running *inside* the worktree being removed. `cd` to the primary checkout and retry.
- A phantom `git worktree list` entry after a manual `rm -rf` clears with `git worktree prune` — then the branch can be deleted or checked out.
- Spawning a fresh worktree for every trivial task when a small reused pool (`lane-N`) would do — reuse the pool for sequential solo work; a dedicated worktree per parallel work lane is fine when isolation is genuinely needed.
- Never set `GIT_GUARD_PROTECTED=` in shell startup files — it disables enforcement globally and permanently.
- Assuming the checks fire right after `install.sh` runs — they stay inert until `core.hooksPath` points at `.githooks`, which is `hookify`'s install, not this one (Step 1).
