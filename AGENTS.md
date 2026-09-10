# craft-skills — Agent Operating Guide

Engineering and research work-craft skills for any coding agent — Claude Code, Codex, Hermes, or a generic instruction-following agent.
This is the operator's own accumulated craft, kept vendor-agnostic on purpose: every skill is a plain Markdown recipe, portable across runtimes with no lock-in to one tool's frontmatter or plugin format.
Keep reusable work methods here, including personal preferences that generalize without private context.
Keep personal accounts, knowledge policy, and private operating context in `bstack`; compose distinct responsibilities rather than duplicating them.

## Layout

A package is one flat directory: `skills/<name>/SKILL.md` plus whichever of `references/`, `templates/`, `scripts/`, `assets/`, and `CHANGELOG.md` it needs; tests live at repo-root `tests/<name>/`.
Runtime-owned `agents/` directories are optional plumbing, not part of the portable core.
No nested `SKILL.md` files — every skill is one level deep.
`tests/<name>/evals/` holds a supplied reusable corpus (`evals.json` and/or `triggers.json`); corpus presence and counts are not universal quality gates.
`evals/` directories are local, gitignored scratch for private transcripts and are never committed.

The 30 packages (alphabetical): `agents`, `api`, `ast-grep`, `backend`, `browser`, `cicd`, `db`, `debug`, `defuddle`, `design`, `distil`, `document`, `frontend`, `git`, `gpu`, `guardrails`, `init`, `ml`, `obsidian`, `orca`, `programming`, `refactor`, `research`, `security`, `skillify`, `tailscale`, `testing`, `vmware`, `write-prd`, `write-report`.
`browser` is one flat package: it owns one router and exactly three references for Aside, agent-browser, and existing-session.
`obsidian` is one thick package whose sub-recipes live under `references/`.
`design` owns root `DESIGN.md`, UX/UI judgment, bad-UX audits, and rendered evidence.

The authoring contract — frontmatter shape, naming, description rules, body limits, CHANGELOG format, and the eval-first loop — lives at `skills/skillify/references/contract.md`.
The `skillify` skill owns create/update/move/retire work and keeps the portable core neutral across Claude Code, Codex, Hermes, Cursor, and Grok; it accommodates optional `agents/` and `assets/` without admitting runtime-specific fields to the core.

## Install matrix

| Runtime | How skills are loaded |
|---------|------------------------|
| **Claude Code** | Claude marketplace commands: `/plugin marketplace add GoBeromsu/craft-skills` then `/plugin install craft-skills@craft-skills`. |
| **Codex** | Canonical channel: vendor-native plugin install with `codex plugin marketplace add GoBeromsu/craft-skills` then `codex plugin add craft-skills@craft-skills --json`; marketplace metadata lives in `.codex-plugin/plugin.json`. Codex auxiliary clone path: `.agents/skills/craft-skills` is optional development context from the user project's root; skills are nested at `.agents/skills/craft-skills/skills/<name>/SKILL.md`. |
| **Hermes** | Custom tap: `hermes skills tap add GoBeromsu/craft-skills`, then `hermes skills install GoBeromsu/craft-skills/skills/<name>` per skill and `hermes skills update` for upstream changes. The tap copies and scans the whole unit, so packages stay scanner-clean (`safe`). |
| **GJC** (Gajae-Code) | For authorized installation, use the marketplace plugin: `gjc plugin marketplace add GoBeromsu/craft-skills` then `gjc plugin install craft-skills@craft-skills`. GJC advertises installed plugin packages as `craft-skills:<name>`. Select the native update command, target, and scope from installed help; do not widen to unrelated plugins. Preserve identifiable native field experiments separately from the official cache and retain unique changes before normalization. Do not author the official cache or point `skills.customDirectories` at a version-pinned cache. Verify updated content and fresh effective loading separately. |
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
- Preserve native local field learning without immediate canonical edits or version bumps. Harvest only on request, distinguishing `canonical_package`, `proposed_pr`, `field_package`, and `reference_evidence` with owner, privacy, provenance, and admission state.
- Do not harvest all MEMORY/USER/conversation files, edit official installed caches as an authoring shortcut, or add an automatic harvesting service.
- Choose verification by behavior and risk: real script/error/effect tests, independent judgment for subjective output, and relevant routing positives/near-misses. Supplied corpus structure is checked, but no fixed case count, provider quorum, universal baseline improvement, or full model/runtime matrix establishes quality.
- Structural and lexical checks are not semantic or deployed-behavior proof. Distinguish official compatibility requirements, upstream recommendations, and local repository policy.
- Reuse a common approved policy and exact authoring evidence across coherent domain batches; do not restart a full GJC workflow per package or duplicate admission committees.
- Reuse an unchanged task-bound approval tuple (target, command, effect). New publication, install, removal, or restart effects require their own authorization; a plan or passing test alone grants none.
- Record source base plus current recursive content digest, actual checks, independent findings, and unverified effects. A release commit, installed content, and effective load are separate facts.
- Keep out-of-scope findings separate without automatically expanding the change or publishing an issue. Publish a concrete issue only within the operator's authorization.
- CHANGELOG bullets are one compact line: `- YYYY-MM-DD — [vX.Y.Z: ]why → what.`
- Provenance is two-tier: per-change credit lives in the package's own `CHANGELOG.md`; the current cross-skill lineage snapshot lives in `skills/PROVENANCE.md`.
- Governance harness: `python3 scripts/governance/harness.py --config <repos.json>` where `repos.json` is `{"repos":[{"name":"craft-skills","path":"<repo root>"}]}`.
