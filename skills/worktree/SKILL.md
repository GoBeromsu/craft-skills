---
name: worktree
description: '"git wt", "make a worktree", "work on issue #N", "/worktree" — create an isolated worktree off a <type>/<issue#>-<slug> branch and install the git-guard rails in the target repo.'
version: 1.0.0
allowed-tools: [Bash, Read, Write, Edit, Grep, Glob]
compatibility: claude-code, codex
---

# Worktree Workflow Skill

## Purpose

Enforce one task per dedicated worktree off a `<type>/<issue#>-<slug>` branch. Never branch directly from a protected branch. Install the git-guard enforcement layer on first run (idempotent).

---

## Core Rule

Every task maps to a GitHub Issue, which maps to a branch, which maps to a worktree outside the repo root.

```
GitHub Issue  →  branch <type>/<issue#>-<slug>  →  worktree at $WORKTREE_ROOT/<branch>
```

Protected branch (`main` by default) is blocked at pre-commit and pre-push by the git-guard hooks. Never work directly on it.

---

## Step 1 — Self-Install (idempotent, run on first invocation)

Check whether the git-guard rails are installed in the target repo. If any of the three conditions below are missing, run the bundled installer:

```bash
# Check installation state
git config core.hooksPath           # must equal ".githooks"
git config alias.wt                 # must be set
ls scripts/git-guard/setup-hooks.sh # must exist
```

If any check fails, install by running the bundled `setup-hooks.sh` from the skill's `scripts/` directory into the repo:

1. Copy `skills/worktree/scripts/` into the repo at `scripts/git-guard/` (skip if already present).
2. Ensure `.githooks/pre-commit` and `.githooks/pre-push` exist (create stubs that call the guard scripts if absent).
3. Run `sh scripts/git-guard/setup-hooks.sh` from the repo root.

`setup-hooks.sh` is idempotent — re-running when already installed is a no-op. After install, confirm output shows:

```
[git-guard] core.hooksPath  = .githooks
[git-guard] alias.wt        = ...
[git-guard] setup complete  — run `git wt <issue#>` to start work on an issue.
```

---

## Step 2 — Create a Worktree

```bash
git wt <issue#>                         # e.g. git wt 17
git wt <issue#> --type fix              # explicit type override
git wt <issue#> --slug api --type feat  # fan-out slice branch
```

`git wt` reads the issue's `type:` label (`feat|fix|chore|docs|refactor|test`) and title via `gh`, derives the branch name `<type>/<issue#>-<slug>`, fetches `origin/<default>`, and creates the worktree **outside** the repo root so `git status` stays clean.

If the issue has no `type: *` label, `git wt` stops and requires `--type`. This keeps governed repositories from silently creating `feat/*` branches. Manual or offline cases are still allowed by passing `--type` explicitly.

Branch naming:
- `<type>`: from the issue's `type: *` label, or explicit `--type`
- `<issue#>`: GitHub issue number
- `<slug>`: title lowercased, non-alphanumeric chars → `-`, capped at 50 chars; explicit `--slug <slice-slug>` overrides the title slug for fan-out PR slices

Examples: `feat/17-add-inference-endpoint`, `fix/23-rtsp-timeout`, `chore/31-update-deps`

Fan-out example for multiple PRs from the same issue: `git wt 17 --type feat --slug api`, `git wt 17 --type feat --slug ui`, and `git wt 17 --type test --slug coverage` create separate branches/worktrees under the same issue number.
For local fan-out orchestration, run the bundled tmux helper from the target repo after self-install:

```bash
scripts/git-guard/tmux-fanout.sh 17 api ui coverage
```

The helper creates or reuses a local tmux session named `wt-17`, creates one window per slice, and runs `git wt 17 --slug <slice>` in that window. Existing windows with the same normalized slice name are skipped, so re-running the command is safe. The printed `tmux attach -t wt-17` command attaches to the fan-out session.

Local tmux fan-out is intentionally lightweight: it only creates local tmux windows and invokes `git wt`; it does not introduce team mailbox, dispatch, lifecycle, or remote-worker governance. The optional Tailscale flow below remains remote-only and is not the default.

The worktree path is printed on success. `cd` to it to begin work.

---

## Step 3 — Day-to-Day Commands

```bash
git wt ls                  # list all worktrees
git wt rm <issue#>         # remove a worktree (preferred over rm -rf)
git wt rm <issue#> --force # force-remove a dirty worktree
```

Use `git wt rm` — never `rm -rf`. Manual deletion leaves phantom `.git/worktrees/` entries that block `git branch -d` and `git checkout` until `git worktree prune` is run manually. `git wt rm` calls `git worktree remove` + `git worktree prune` automatically.

After the PR is merged, delete the local branch:

```bash
git branch -d <branch>
```

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
3. Open (or attach to) a named tmux session: `tmux new-session -As wt-<issue#>` on the remote.
4. Run `git wt <issue#>` inside the tmux session to create a dedicated remote worktree.
5. Work inside the remote worktree via the tmux session.

### Teardown (explicit — do not auto-detect)

Ask the user to confirm before tearing down:

> "Work complete on issue #N. Confirm teardown? (y/N)"

On confirmation:
1. Commit and push all changes, or open a PR (`gh pr create`).
2. Close the tmux session: `tmux kill-session -t wt-<issue#>`.
3. Remove the remote worktree: `git wt rm <issue#>` on the remote.

Never auto-detect completion and never tear down without explicit user confirmation.

---

## Requirements / Environment

| Variable | Purpose | Required |
|---|---|---|
| `CRAFT_WT_REMOTE_HOST` | Tailscale hostname or `user@host` for remote execution | No — omit to use local-only mode |

Set in `.env` (gitignored). See `.env.example` for the placeholder.

Dependencies:
- `gh` CLI authenticated (`gh auth status`) — required for `git wt` to read issue metadata.
- `git` >= 2.5 (worktree support).
- `tmux` locally — required only for `tmux-fanout.sh` local fan-out helper; also required on the remote host for the Tailscale extension.
- `tailscale` CLI or equivalent — required for Tailscale extension reachability check only.

---

## Guard Scripts Reference

| Script | Role |
|---|---|
| `scripts/lib.sh` | Shared helpers: `gg_warn`, `gg_die`, protected-branch list |
| `scripts/assert-not-main.sh` | Exits 1 when HEAD is on a protected branch |
| `scripts/check-freshness.sh` | Compares HEAD to upstream; `block` (exit 1) or `warn` mode |
| `scripts/wt.sh` | Issue → worktree creator and manager (`create`, `rm`, `ls`) |
| `scripts/tmux-fanout.sh` | Local tmux fan-out helper: one `git wt <issue#> --slug <slice>` window per slice |
| `scripts/setup-hooks.sh` | Idempotent post-clone setup: `core.hooksPath`, `alias.wt`, `chmod +x` |
| `scripts/deny-assets.sh` | Blocks model weights, media files, and blobs > 5 MB at commit/push |

---

## Rationalizations / Red Flags

- If `git worktree list` shows a phantom entry for a branch after a manual `rm -rf`, run `git worktree prune` to clear it — then the branch can be deleted or checked out.
- If `git wt` reports "branch already exists", use `git wt ls` to find the existing worktree path instead of creating a duplicate.
- If the freshness check warns but you are certain the upstream has no relevant changes, run `git fetch` then re-check with `git rev-list --count HEAD..@{upstream}` before suppressing.
- Never set `GIT_GUARD_PROTECTED=` in shell startup files — it disables enforcement globally and permanently for all sessions.
