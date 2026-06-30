# Changelog

## [Unreleased]

- 2026-06-30 — git-guard scripts were referenced but never bundled, leaving fresh clones with no hooks → shipped [githooks/pre-commit](githooks/pre-commit), [githooks/pre-push](githooks/pre-push), and [scripts/install.sh](scripts/install.sh) as the single first-run installer; [init](../init/SKILL.md) now delegates to it so git-guard installs by default on a fresh clone.
- 2026-06-30 — `deny-assets.sh` was missing from the executable set so pre-commit/pre-push hooks could not invoke it → fixed [scripts/setup-hooks.sh](scripts/setup-hooks.sh) to `chmod +x` [githooks/deny-assets.sh](githooks/deny-assets.sh).
- 2026-06-30 — local fan-out across multiple worktrees had no tmux automation → S5: added [scripts/tmux-fanout.sh](scripts/tmux-fanout.sh) for local tmux fan-out across `git wt <issue#> --slug <slice>` worktrees, with mockable smoke coverage and usage docs.
- 2026-06-30 — worktree creator lacked fan-out support and contained repo-specific symlink assumptions → S4: added `git wt <issue#> --slug <slice-slug>` fan-out flag, required explicit `--type` when an issue has no type label, and removed `ml/data` / `ml/models` symlink assumptions from the portable creator.

- 2026-06-17 — 1.0.1: post-merge cleanup ordering was undocumented, causing failures when merging with `--delete-branch` while a worktree held the branch → documented correct ordering (cleanup from primary checkout, prefer `git branch -d`) and added matching red-flag entries; prose-only, no interface change.
- 2026-06-13 — no standard git worktree workflow or branch-guard automation existed → initial release: vendored 6 git-guard scripts from eldercare-fall-ai; encoded `git wt <issue#>` worktree workflow, idempotent self-install via [scripts/setup-hooks.sh](scripts/setup-hooks.sh), and optional Tailscale remote-execution extension with explicit teardown confirmation gate.
