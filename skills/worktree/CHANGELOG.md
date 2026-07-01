# Changelog

## [2.0.0] - 2026-06-30

- 2026-06-30 — 2.0.0: `git wt` was an issue-driven manager coupling every worktree to `gh`/issue/type-label/slug → **BREAKING** simplified to a plain worktree maker: `git wt <name>` creates (or reuses) a worktree off `origin/<default>` with no `gh` dependency; removed `tmux-fanout.sh`, dropped the `--type`/`--slug` interface, and rewrote `SKILL.md` to the simple-name flow (cleanup ordering, freshness, escape hatch, optional Tailscale extension retained). The `work on issue #N` trigger and the `<type>/<issue#>-<slug>` branch contract are gone.
- 2026-06-30 — git-guard scripts were referenced but never bundled, leaving fresh clones with no hooks → shipped [githooks/pre-commit](githooks/pre-commit), [githooks/pre-push](githooks/pre-push), and [scripts/install.sh](scripts/install.sh) as the single first-run installer; [init](../init/SKILL.md) now delegates to it so git-guard installs by default on a fresh clone.
- 2026-06-30 — `deny-assets.sh` was missing from the executable set so pre-commit/pre-push hooks could not invoke it → fixed [scripts/setup-hooks.sh](scripts/setup-hooks.sh) to `chmod +x` [githooks/deny-assets.sh](githooks/deny-assets.sh).

- 2026-06-17 — 1.0.1: post-merge cleanup ordering was undocumented, causing failures when merging with `--delete-branch` while a worktree held the branch → documented correct ordering (cleanup from primary checkout, prefer `git branch -d`) and added matching red-flag entries; prose-only, no interface change.
- 2026-06-13 — no standard git worktree workflow or branch-guard automation existed → initial release: vendored 6 git-guard scripts from eldercare-fall-ai; encoded `git wt <issue#>` worktree workflow, idempotent self-install via [scripts/setup-hooks.sh](scripts/setup-hooks.sh), and optional Tailscale remote-execution extension with explicit teardown confirmation gate.
</content>
