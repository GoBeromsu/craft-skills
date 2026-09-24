# Gajae-Code Lens

Local context for using GJC as the selected authoring runtime.
Official GJC skills, orca-cli, and orchestration originals stay unmodified on their official channels; native GJC currently discovers official `orca-cli` and orchestration as symlinks to those updated originals — do not copy their docs into this library.
This file records uncovered library boundaries and source links, not a product command manual.
Consult current official docs and installed help when a runtime form is unknown; apply [contract §10](contract.md#10-external-facts-and-dependencies) on create/update.
A version or help check is not compatibility or deployment proof.

## 1. Source

Official surfaces to consult first:

- Installed `gjc --help`, `gjc --version`, `gjc plugin list --json`, and `gjc skills discover --json`
- [Skills doc](https://github.com/Yeachan-Heo/gajae-code/blob/main/docs/skills.md), [marketplace loader](https://github.com/Yeachan-Heo/gajae-code/blob/main/packages/coding-agent/src/discovery/claude-plugins.ts), [scanner](https://github.com/Yeachan-Heo/gajae-code/blob/main/packages/coding-agent/src/discovery/helpers.ts), and [skill tool](https://github.com/Yeachan-Heo/gajae-code/blob/main/packages/coding-agent/src/tools/skill.ts)
- [SDK application guide](https://github.com/Yeachan-Heo/gajae-code/blob/main/docs/sdk-app-guide.md) and [models and profiles](https://github.com/Yeachan-Heo/gajae-code/blob/main/docs/models.md)
- Current official orca-cli and orchestration documentation via the native discovery surface, not a local copy

Shared reference check (consumed by this library's packaging and by bstack `promote`): installed `gjc/0.17.4` at `~/.local/bin/gjc`, a compiled binary; release tag `v0.17.4` resolves to `e87c91927b78c01c250a124ed2890488ac8bcb64`, which was also `main` at inspection.
The four sources above were read at that revision (`docs/skills.md` sha256 `11581bb8…`, `claude-plugins.ts` `c76864fb…`, `helpers.ts` `21447099…`, `skill.ts` `cd9c8517…`).
Parity between the installed binary and that source revision is asserted only by the matching version string; it is not verified by build provenance and stays unknown.
This is a read-only source and CLI check, not multi-runtime compatibility evidence; re-probe per [contract §10](contract.md#10-external-facts-and-dependencies) when GJC is actually selected.

## 2. Portable lesson

Use GJC for authoring orchestration and durable execution when the operator selects it.
Keep the resulting skill portable; a consumer does not need GJC merely because GJC authored the package.

Skillify owns the package contract, useful authoring evidence, and local refinement.
The destination admission gate owns formal acceptance, routing, packaging, and release delivery.
GJC owns the selected session, orchestration, execution continuity, and durable workflow state.
Reuse task-bound authoring evidence at admission instead of creating a second evaluator for the same behavior.

Use an existing approved plan when it covers the requested change.
For a coordinated library reform, review the common policy once and implement domain batches within that contract.
Do not start a full interview, consensus plan, or execution workflow for every package.
A small, concrete change can use direct repository tools and focused verification; use a planning workflow only when selected by the operator or required by the active runtime contract.
Never dispatch from a terminal blocked plan or relabel an unreviewed draft as approved.

## 3. Runtime plumbing (GJC-only)

Package-side contract observed at `e87c919` for a library installed through the GJC marketplace (`gjc plugin install craft-skills@craft-skills`):

- **Namespace.** The loader reads the plugin id from the installed-plugins registry (`<plugin>@<marketplace>`) and advertises every skill as `${plugin}:${frontmatter name}` — `craft-skills:skillify`. Frontmatter keeps the bare `name: skillify`; never prefix it by hand, and never document the qualified handle as the frontmatter name. The `skill_discovery` tool and `gjc skills discover --json` returned `craft-skills:skillify` from the installed `0.24.0` cache, not from any source checkout.
- **Root and nesting.** The skills root is `.claude-plugin/plugin.json` `skills` when set and inside the plugin root, else `skills/`. Only `<root>/<dir>/SKILL.md` immediate children are scanned; dotfile entries are skipped; a symlinked entry is followed but its real path must stay inside the root; the file must be a regular file with a single link; nested `SKILL.md` files are never discovered.
- **Frontmatter.** A leading `---` YAML block is required and read within a bounded byte cap; marketplace skills additionally require `description`; `enabled: false` hides the skill; a blank `name` falls back to the directory name.
- **Trust and filters.** Plugin roots come from the user registry and a project-scoped registry (project entries shadow user entries by plugin id); `skills.enabled`, `skills.trustProjectSkills`, `skills.trustUserSkills`, `skills.includeSkills`, `skills.ignoredSkills`, and `disabledExtensions` filter discovery; bundled workflow names (`autoresearch`, `deep-interview`, `ralplan`, `ultragoal`) always win and collisions are diagnosed.
- **Explicit invocation.** The `skill` tool requires the exact discovered name (`craft-skills:skillify`); glob or wildcard names are rejected; chaining into the currently active skill is refused; an unknown name is re-discovered at runtime before failing with the available list.
- **Internal calls.** Chaining out of a canonical GJC workflow (`ralplan`, `ultragoal`) is refused in live phases until that workflow writes its handoff phase; runtime skills such as this library's have no phase state and dispatch directly.
- **Failure classes stay distinct.** Discovery success (the name appears), body load (the file reads inside the root), explicit invocation (exact name accepted), and workflow-phase permission are separate facts; a prior invocation failure whose cause was not reproduced remains unresolved and is not fixed by a passing discovery listing.
- Profile names, marketplace/plugin commands, namespace handles, discovery precedence, and update flags belong to installed help and official docs. Do not copy them into portable `SKILL.md`.
- Do not require named profiles, a provider family count, or a new session for a package edit.
- When selecting a different route is necessary, inspect the runtime's real catalog and record the actual provider/model reported by the completed run. Do not alter the operator's startup default or inspect private endpoint credentials to discover a route.
- Official orca-cli and orchestration stay canonical originals. Native symlink discovery is not a reason to re-host their instructions here.
- Keep GJC-specific namespace, profile, and installation details in this lens rather than in portable core instructions.

## 4. Divergences from this library

- **Official originals.** GJC product usage stays on official channels. This library does not fork, patch, or republish those skills or CLI manuals.
- **Evidence.** Actual script regressions, relevant scenarios, and negative cases for routing or external effects remain the local policy ([evaluation.md](evaluation.md)). Generated workflow transcripts are not tracked SSOT. A version/help probe is not deployed-behavior proof.
- **Approval.** An approval for the same target, command, and effect is reusable. Commit, push, merge, install, unregister, removal, and restart are distinct effects; do not infer them from a successful test or plan.
- **Failure.** Preserve useful work and the real error. Unavailable verification remains explicitly unverified, not passed.

## 5. Absorbed into core

- Task-bound evidence reuse instead of a second committee → `contract.md` §7, `lifecycle.md` §6.
- Explicit irreversible-effect authorization, no generic repeated consent → `contract.md` §4 and §10.
- Inspectable conclusions rather than reasoning-transcription requests → `contract.md` §4.
