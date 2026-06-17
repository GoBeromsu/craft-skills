# Changelog

## [Unreleased]

- S5: Added `tmux-fanout.sh` for local tmux fan-out across multiple `git wt <issue#> --slug <slice>` worktrees, including mockable smoke coverage and usage docs.
- S4: Added `git wt <issue#> --slug <slice-slug>` for fan-out worktrees, require explicit `--type` when an issue has no type label, and removed repo-specific `ml/data` / `ml/models` symlink assumptions from the portable worktree creator.

- 2026-06-13 — Initial release: vendored 6 git-guard scripts from eldercare-fall-ai; encoded the `git wt <issue#>` worktree workflow, idempotent self-install via `setup-hooks.sh`, and optional Tailscale remote-execution extension with explicit teardown confirmation gate.
