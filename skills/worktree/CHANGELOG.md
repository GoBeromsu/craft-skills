# Changelog

- 2026-06-17 — 1.0.1 — Document post-merge cleanup ordering: don't merge with `--delete-branch` (fails while a worktree holds the branch), run cleanup from the primary checkout not inside the target worktree, prefer `git branch -d`. Added matching red-flag entries. Prose-only; no interface change.
- 2026-06-13 — Initial release: vendored 6 git-guard scripts from eldercare-fall-ai; encoded the `git wt <issue#>` worktree workflow, idempotent self-install via `setup-hooks.sh`, and optional Tailscale remote-execution extension with explicit teardown confirmation gate.
