# Gajae-Code Lens

Local context for using GJC as the selected authoring runtime.
Official GJC skills, orca-cli, and orchestration originals stay unmodified on their official channels; native GJC currently discovers official `orca-cli` and orchestration as symlinks to those updated originals — do not copy their docs into this library.
This file records uncovered library boundaries and source links, not a product command manual.
Consult current official docs and installed help when a runtime form is unknown; apply [contract §10](contract.md#10-external-facts-and-dependencies) on create/update.
A version or help check is not compatibility or deployment proof.

## 1. Source

Official surfaces to consult first:

- Installed `gjc --help` and `gjc --version`
- [SDK application guide](https://github.com/Yeachan-Heo/gajae-code/blob/main/docs/sdk-app-guide.md)
- [Models and profiles](https://github.com/Yeachan-Heo/gajae-code/blob/main/docs/models.md)
- Current official orca-cli and orchestration documentation via the native discovery surface, not a local copy

A coordinator-verified working-host fact at authoring time was GJC `0.17.2`; that is not multi-runtime compatibility evidence and must be re-probed per [contract §10](contract.md#10-external-facts-and-dependencies).

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
