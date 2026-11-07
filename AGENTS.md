# Repository Guidelines

<!-- init:managed id=init-root sha256=80082c02f19f6197e2d619ffcbf383ea79d24abf1e066112e9eca617911e3e58 -->
## Project Overview

craft-skills is a public library of reusable research and engineering methods, not an application.
Keep the plain Markdown core vendor-neutral; personal accounts, knowledge policy, and private operating context belong in `bstack`.
Discover packages from `skills/*/SKILL.md`, rather than maintaining another inventory here.
`README.md` introduces usage and distribution; each package owns its own recipe, and this file holds the only repository-wide conventions.

## Architecture & Data Flow

A request routes through a package's description to `SKILL.md`, then to its on-demand references, scripts, templates, or assets.
Each package is flat: `skills/<name>/SKILL.md`; no nested skills or grouping directories.
Runtime-specific adapters and optional `agents/` plumbing stay outside the portable core; authoring does not require GJC.
Author source → check the affected contract and behavior → hand off evidence; installation, registration, publication, and effective loading are separate effects.
There is no central authoring, contract, or verification document; a package's `SKILL.md` and support files are its whole contract.
`validate_skill_format.py` and `validate_runtime_hygiene.py` own their deterministic checks, not semantic judgment.

## Key Directories

- `skills/<name>/`: always-read recipe plus only the support resources it actually consumes; history stays in `git log`.
- `scripts/governance/tools/`: repository validators, not a second skill workflow.
- `.github/workflows/`: actual CI and distribution jobs; runtime manifests describe native packaging, not universal loader behavior.
- Gitignored `evals/` scratch: generated transcripts and scores, never committed policy or mandatory quality gates.

## Development Commands

Run from the repository root and select the actual integration branch before resolving one base commit.
These commands come from `.github/workflows/pr-check.yml`; `--diff-base` takes one commit, not a revision range.

```sh
BASE_REF=main # replace with the actual PR target branch
BASE=$(git merge-base "origin/$BASE_REF" HEAD)
python3 -m pip install -r scripts/governance/requirements.txt # official skills-ref linter, Python 3.11+
python3 scripts/governance/tools/validate_skill_format.py
python3 scripts/governance/tools/validate_skill_format.py --diff-base "$BASE"
python3 scripts/governance/tools/validate_runtime_hygiene.py --diff-base "$BASE"
python3 scripts/governance/tools/check_version_bump.py --diff-base "$BASE"
```

Select verification relevant to the changed behavior; the repository ships validators, not test code.
The Layer-1 selectors include committed, staged, unstaged, and untracked changes; shared repository-tool paths select no skill owner, while unknown scoped paths fail closed.
`bash scripts/ci-local.sh` runs the declared local checks, but is not full CI proof: marketplace checks can skip and isolated native-install jobs are CI-only.
Inspect `.github/workflows/test-plugin-install.yml` before claiming marketplace or install coverage; the local runner can register a marketplace in temporary Codex state.
There is no application build/run or root npm/Bun pipeline.

## Code Conventions & Common Patterns

Use `name`, `description`, and `metadata.version` frontmatter; the name matches the kebab-case directory, and version is never a top-level key.
Local semantic versions serve repository consumers, not a native loader requirement; history stays in `git log`, and optional metadata follows the official Agent Skills specification.
Keep judgment in prose and fragile repeatable operations in scripts; reuse existing patterns and prefer standard-library Python.
Declare narrow flags or positional inputs; use placeholders in examples, not host-specific paths or secrets.
A declared non-secret runtime setting may default from one documented environment variable; secrets require declared environment lookup, not ambient environment dumping.
Resolve support paths within the package, including symlinks; reject missing or escaping paths and ambiguous inputs rather than guessing.
Do not use `../` cross-package links: name the sibling skill and file in prose instead.
Keep `.env` private and gitignored; only `.env.example` with placeholders is committed. Never reproduce secret values in reports or logs.
Keep one owner per rule and link to it; tables, rigid heading schemas, wording corpora, provider quorums, and checker-of-checker aggregators are not requirements.
Sentence-per-line is nonblocking taste, not a reflow or formatting gate.
Skills and plugins carry no CHANGELOG; history stays in `git log`.
Source credit and lineage belong in the commit message, preserving upstream attribution and applicable NOTICE/LICENSE obligations.

## Important Files

- `.github/workflows/pr-check.yml`, `.github/workflows/test-plugin-install.yml`, and `scripts/ci-local.sh`: inspect actual jobs rather than assuming README coverage claims.
- `README.md` and native manifests such as `.codex-plugin/plugin.json`: distribution entry points; check affected manifest compatibility rather than inventing native support.
- `skills/init/SKILL.md` and `skills/init/scripts/agents_region.py`: hierarchical guidance ownership and hash-checked managed-region editing.
Maintain this payload through `python3 skills/init/scripts/agents_region.py AGENTS.md --id init-root --payload-file -`; supply UTF-8 text ending in LF through stdin.
Keep the title outside the single `init-root` region; resolve hand-edited marker content rather than bypassing its hash check.
Leave existing adapters unchanged unless selected; add child `AGENTS.md` only for a distinct configured entry scope, not directory size.

## Runtime/Tooling Preferences

Official vendor skills and manuals stay unmodified on upstream channels; local packages hold uncovered context, not copied product manuals or harnesses.
Consult current official guidance and installed help only for APIs and tools the task uses; distinguish compatibility requirements, recommendations, and local policy.
`README.md` documents runtime distribution routes; GJC installed packages use `craft-skills:<name>`, while portable frontmatter keeps the bare name.
Select authorized native update commands and scope from installed help; never author official caches or point `skills.customDirectories` at a version-pinned cache.
Preserve unique field experiments separately; harvest only on request, recording owner, privacy, provenance, and admission for `canonical_package`, `proposed_pr`, `field_package`, or `reference_evidence`.
Do not harvest whole memory/conversation stores, add automatic harvesting, or turn field learning into an automatic canonical edit or version bump.
`browser` keeps Aside as the sole managed route and delegates product usage upstream; `design` owns root `DESIGN.md` and rendered UX evidence.
Optional environment names remain task-bound: `CRAFT_WT_REMOTE_HOST` is used only by the git worktree recipe.
Preserve unrelated dirty work; never stash, discard, or publish it to make a task look clean.
Reuse unchanged approvals bound to target, command, and effect; new install, removal, restart, publication, or expanded delivery effects require their own authorization.
A plan or passing test grants no external effect; do not upgrade unrelated tools or publish out-of-scope issues automatically.

## Testing & QA

Choose evidence by observable behavior and risk: exercise real scripts, error paths, security boundaries, and data integrity; use independent judgment for subjective output and routing positives/near-misses.
A prose correction may use focused contract review; do not require generated scores, fixed case counts, a wording-locked corpus, or repeated admission committees.
Keep checks only with a current consumer or independent safety obligation; structural and lexical passes do not prove deployed behavior.
Record source base and current recursive content digest, evaluated resources, actual checks, independent findings, and unverified effects in the existing handoff.
Label results executed or reviewed; name unrun checks and reasons. Release commit, installed content, discovery, and effective load are separate facts.
Reuse exact task- and content-bound evidence across coherent batches; do not restart a workflow per package.

### Repository-aware PR review

When assigned a repository PR, read root and applicable nested `AGENTS.md`, then inspect the actual base, head, and diff, including callers and support resources.
Judge each changed package against its own `SKILL.md` and the conventions here.
Check affected routes, manifests, privacy, containment, and retirement references; approved retirement removes obsolete paths rather than leaving aliases or loadable stubs.
Select the actual affected checks; report material findings with path and line, separating observed execution from reviewed evidence and unrun limitations.
This is assigned-review guidance, not an automatic PR detector, bot, or webhook; review does not authorize fixes, installation, merge, release, or restart.
<!-- /init:managed id=init-root -->
