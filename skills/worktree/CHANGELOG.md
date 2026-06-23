# Changelog

## [Unreleased]

- Added shipped `githooks/pre-commit` and `githooks/pre-push` as real files (previously referenced but never bundled), plus `scripts/install.sh` as the single bundled first-run installer that copies the guard scripts + hooks into the target repo and then runs `setup-hooks.sh`. `init` now delegates to this so git-guard installs by default on a fresh clone.
- Fixed `setup-hooks.sh` to `chmod +x` `deny-assets.sh` (it was missing from the executable set, so the pre-commit/pre-push hooks could not invoke it).
- S5: Added `tmux-fanout.sh` for local tmux fan-out across multiple `git wt <issue#> --slug <slice>` worktrees, including mockable smoke coverage and usage docs.
- S4: Added `git wt <issue#> --slug <slice-slug>` for fan-out worktrees, require explicit `--type` when an issue has no type label, and removed repo-specific `ml/data` / `ml/models` symlink assumptions from the portable worktree creator.

- 2026-06-17 — 1.0.1 — Document post-merge cleanup ordering: don't merge with `--delete-branch` (fails while a worktree holds the branch), run cleanup from the primary checkout not inside the target worktree, prefer `git branch -d`. Added matching red-flag entries. Prose-only; no interface change.
- 2026-06-13 — Initial release: vendored 6 git-guard scripts from eldercare-fall-ai; encoded the `git wt <issue#>` worktree workflow, idempotent self-install via `setup-hooks.sh`, and optional Tailscale remote-execution extension with explicit teardown confirmation gate.
