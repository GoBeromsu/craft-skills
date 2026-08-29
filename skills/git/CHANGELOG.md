# Changelog

- 2026-06-13 — no worktree workflow or branch-guard automation existed → initial release: git-guard scripts, git wt <issue#>, self-install, Tailscale extension.
- 2026-06-17 — v1.0.1: post-merge cleanup ordering undocumented → documented correct ordering + red-flag entries.
- 2026-06-30 — v2.0.0 BREAKING: git wt simplified to a plain worktree maker → dropped gh/issue coupling and --type/--slug.
- 2026-06-30 — git-guard scripts referenced but unbundled → shipped githooks/pre-commit, pre-push, scripts/install.sh; init delegates to it.
- 2026-06-30 — deny-assets.sh missing from executable set → fixed setup-hooks.sh to chmod +x it.
- 2026-07-05 — worktree skill duplicated git craft → absorbed as nested sub-recipe; install proposes first, pre-push freshness warns not blocks.
- 2026-07-05 — v1.0.0: no git craft discipline existed → ground-truth gate, atomic-commit split, commit/branch/PR rules. Provenance: lazycodex.
- 2026-07-06 — v2.0.0: realign to authoring contract + resolve #29 → spec-minimal frontmatter, compressed body, guards.d owned by hookify.
- 2026-07-06 — v2.0.1: contract adopted a single anti-patterns registry → merged Red Flags + Common Rationalizations into ## Anti-patterns.
- 2026-07-12 — v2.1.0: audit applied truth over memory and one logical, reversible change boundaries → resolves only real comparison bases, preserves unrelated dirty work, and keeps history/blame requests read-only. Provenance: docs/research/omo-analysis.md (git-master).
- 2026-08-28 — mutable Git and forge behavior needs grounded runtime handling → v2.2.0 official-docs-first evidence rule with conflict disclosure and safe unknown outcomes.
- 2026-08-28 — v2.2.1: Git dependency maintenance lacked an explicit support boundary → adds official docs, `git --version`, incumbent repo/version/platform/remote scope, and release-or-capability-probe worktree/history-safety re-evaluation.
- 2026-08-28 — v2.2.2: the owner of `core.hooksPath` was renamed → every hand-off in the description, `references/worktree.md`, the installer scripts, and the guards.d headers now names `guardrails`.
- 2026-08-29 — v2.2.2: an installer comment's executable-list wording looked like a set-id permission command to Hermes Guard → describe the synchronized executable-file list without the false dangerous pattern.
- 2026-08-30 — v2.2.3: concurrent v2.2.2 releases both apply → preserves `guardrails` ownership of `core.hooksPath` and the safe installer wording.
