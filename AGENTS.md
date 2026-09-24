# craft-skills — Agent Operating Guide

Engineering and research work-craft skills for any coding agent — Claude Code, Codex, Hermes, or a generic instruction-following agent.
This is the operator's own accumulated craft, kept vendor-agnostic on purpose: every skill is a plain Markdown recipe, portable across runtimes with no lock-in to one tool's frontmatter or plugin format.
Keep reusable work methods here, including personal preferences that generalize without private context.
Keep personal accounts, knowledge policy, and private operating context in `bstack`; compose distinct responsibilities rather than duplicating them.

## Layout

A package is one flat directory: `skills/<name>/SKILL.md` plus whichever of `references/`, `templates/`, `scripts/`, `assets/`, and `CHANGELOG.md` it needs; tests live at repo-root `tests/<name>/`.
Runtime-owned `agents/` directories are optional plumbing, not part of the portable core.
No nested `SKILL.md` files — every skill is one level deep.
`tests/<name>/` holds focused functional, security, and data-integrity fixtures; optional reusable scenarios may live under `tests/<name>/evals/`.
Generated run transcripts and scores stay in gitignored `evals/` scratch and are never quality gates.
Do not require a wording- or procedure-locking corpus.

Discover available packages from `skills/*/SKILL.md`; do not maintain a second package inventory here.
`browser` is a thin personal-boundary package: Aside is the sole managed route, official aside-browser and current aside guide own product usage, and this library records only uncovered identity, existing-app protection, same-session continuation, and observed-result composition.
`obsidian` composes unchanged official native owners `obsidian-markdown`, `obsidian-bases`, `json-canvas`, and `obsidian-cli` for format and CLI mechanics, keeping only uncovered local app/Sync coordination and live-vault/OMS policy.
`design` owns root `DESIGN.md`, UX/UI judgment, bad-UX audits, and rendered evidence.

The authoring contract — frontmatter shape, naming, description rules, body limits, CHANGELOG format, upstream-first create/update, and focused outcome verification — lives at `skills/skillify/references/contract.md`.
The `skillify` skill owns create/update/move/retire work at the user-chosen destination and completes with the package plus its evaluation evidence; this library's admission and branch → PR delivery are destination policy applied when the destination is this library, and bstack registration belongs to bstack `promote`. It keeps the portable core neutral across Claude Code, Codex, Hermes, Cursor, Grok, and GJC; it accommodates optional `agents/` and `assets/` without admitting runtime-specific fields to the core, and it needs no GJC to author.
Official vendor skills stay unmodified on their official distribution and update channels; local packages hold only uncovered context.

## Install matrix

| Runtime | How skills are loaded |
|---------|------------------------|
| **Claude Code** | Claude marketplace commands: `/plugin marketplace add Xia-Ataraxia/craft-skills` then `/plugin install craft-skills@craft-skills`. |
| **Codex** | Canonical channel: vendor-native plugin install with `codex plugin marketplace add Xia-Ataraxia/craft-skills` then `codex plugin add craft-skills@craft-skills --json`; marketplace metadata lives in `.codex-plugin/plugin.json`. Codex auxiliary clone path: `.agents/skills/craft-skills` is optional development context from the user project's root; skills are nested at `.agents/skills/craft-skills/skills/<name>/SKILL.md`. |
| **Hermes** | Custom tap: `hermes skills tap add Xia-Ataraxia/craft-skills`, then `hermes skills install Xia-Ataraxia/craft-skills/skills/<name>` per skill and `hermes skills update` for upstream changes. The tap copies and scans the whole unit, so packages stay scanner-clean (`safe`). |
| **GJC** (Gajae-Code) | For authorized installation, use the marketplace plugin: `gjc plugin marketplace add Xia-Ataraxia/craft-skills` then `gjc plugin install craft-skills@craft-skills`. GJC advertises installed plugin packages as `craft-skills:<name>`. Select the native update command, target, and scope from installed help; do not widen to unrelated plugins. Preserve identifiable native field experiments separately from the official cache and retain unique changes before normalization. Do not author the official cache or point `skills.customDirectories` at a version-pinned cache. Verify updated content and fresh effective loading separately. |
| **Generic agents** (Cursor, Gemini, Copilot, etc.) | Point the instruction-file import at `skills/<name>/SKILL.md`; each file is self-contained. |

## Environment variables

| Variable | Meaning |
|----------|---------|
| `CRAFT_WT_REMOTE_HOST` | Tailscale hostname for remote worktree exec (the worktree recipe now lives in the `git` skill's `references/worktree.md`; optional). |
| `OBSIDIAN_VAULT_PATH` | Obsidian vault root resolved independently on each machine. |
| `OBSIDIAN_CLI_PATH` | Optional path to the `obsidian-cli` or `ob` binary required by the invoking skill. |
| `OBSIDIAN_SYNC_REMOTE_HOST` | Optional SSH host for a headless Obsidian Sync replica. |
| `OBSIDIAN_SYNC_PROCESS_NAME` | Optional process-supervisor name for the headless Sync daemon. |
| `PM2_LOG_DIR` | Optional pm2 log directory used by the headless Sync daemon recipe. |

## Rails

- Formal changes use `skillify` authoring, task- and content-bound destination admission, and authorized branch → PR delivery. Edits under `skills/skillify/` require explicit task approval; a prior unrelated approval is not reusable.
- Official tool skills remain unmodified originals; install and update them through their official channels. Local skills hold only context those originals do not cover. Do not fork, copy, or rewrite official product usage into this library.
- Every `skillify` create or update checks related official skills and CLI/agent runtimes against the official latest stable, including major. A dependency is related only when the package recipe invokes it or the selected destination or runtime requires it for that task; an installed but unused runtime such as GJC is unrelated. Current matching versions are a verified no-op. Stale relevant dependencies are actually updated on the working host, then resulting versions are verified and impacted siblings are repaired and verified before the run can succeed. Check-only detection or a failed update/verification leaves the run incomplete. Other devices perform the same update when that skill is deployed. Do not bulk-update unrelated tools.
- Preserve native local field learning without immediate canonical edits or version bumps. Harvest only on request, distinguishing `canonical_package`, `proposed_pr`, `field_package`, and `reference_evidence` with owner, privacy, provenance, and admission state.
- Do not harvest all MEMORY/USER/conversation files, edit official installed caches as an authoring shortcut, or add an automatic harvesting service.
- Choose verification by observable behavior and risk: real script, error, effect, security, and data-integrity fixtures, plus independent judgment for subjective output and relevant routing positives/near-misses. Do not require generated eval/run outputs, wording- or procedure-locking corpora, or a replacement checker-of-checker. The agent chooses method and recovery. Do not add generic repeated consent for reversible in-scope work.
- Keep a schema field, check, gate, or receipt only when it has a current consumer or an independent safety obligation. Structural and lexical checks are not semantic or deployed-behavior proof. Distinguish official compatibility requirements, upstream recommendations, and local repository policy.
- Reuse a common approved policy and exact authoring evidence across coherent domain batches; do not restart a full GJC workflow per package or duplicate admission committees.
- Reuse an unchanged task-bound approval tuple (target, command, effect). New publication, install, removal, or restart effects require their own authorization; a plan or passing test alone grants none.
- Record source base plus current recursive content digest, actual checks, independent findings, and unverified effects. A release commit, installed content, and effective load are separate facts.
- Keep out-of-scope findings separate without automatically expanding the change or publishing an issue. Publish a concrete issue only within the operator's authorization.
- CHANGELOG bullets are one compact line: `- YYYY-MM-DD — [vX.Y.Z: ]why → what.` Keep each package CHANGELOG at or under 100 lines by dropping oldest whole entries; do not grow a sidecar archive.
- Provenance is two-tier: per-change credit lives in the package's own `CHANGELOG.md`; the current cross-skill lineage snapshot lives in `skills/PROVENANCE.md`.
- Root policy owners are this file, `skills/skillify/references/contract.md`, Layer-1 format and runtime-hygiene validators, native distribution/version checks, and NOTICE/LICENSE/upstream attribution. Keep private operating context out of public packages. Optional authored examples are not a forced evals/triggers schema; compact bodies are guidance; CHANGELOG files stay at or under 100 lines.
- Do not require a manifest-driven governance aggregator or checker-of-checker. Keep or drop an individual check only with a current consumer or independent safety owner.
