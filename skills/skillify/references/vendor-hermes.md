# Hermes Lens (Hermes Agent)

## 1. Source

`NousResearch/hermes-agent` — `website/docs/developer-guide/creating-skills.md`, `website/docs/user-guide/skills/`, `website/docs/guides/work-with-skills.md`, `AGENTS.md` skill-authoring HARDLINE, `tools/skill_manager_tool.py`, `agent/` (`learn_prompt.py`, `prompt_builder.py`, `background_review.py`, `curator.py`), and the in-repo meta-skill `skills/software-development/hermes-agent-skill-authoring`.

## 2. What this lab illuminates

**Experience capture as a standing behavior.**
A nudge injected every session tells the agent: after a complex task (5+ tool calls), a tricky error, or a non-trivial workflow, save the approach as a skill; when a skill proves stale mid-use, patch it immediately — "skills that aren't maintained become liabilities."
Capture is self-initiated, not requested.

**Capture is continuous; curation is separate and conservative.**
A per-turn background review asks "should any skill be saved or updated?", while a slower inactivity-triggered curator consolidates and archives — never deletes, never touches human-authored skills, never overrides pinned ones.
Fast capture, slow conservative maintenance.

**`/learn` is a prompt, not a pipeline.**
Distillation is one large prompt handed to the live agent using its ordinary tools — read the sources, treat prose after a link as a requirement, author exactly one SKILL.md to the same standards a maintainer would.

**Skills versus memory.**
Procedural how-to knowledge is a skill: loaded on demand, may be long.
Declarative facts are memory: injected every turn, must stay compact.

**Hard limits versus attention budgets.**
The validator allows 1024-char descriptions, but the house HARDLINE caps them at 60 because the always-loaded skill index truncates there.
The binding constraint is what gets read every turn, not what the parser accepts.

**Named failure modes for skill prose.**
Its in-repo authoring meta-skill names the ways skill text rots: *premature completion* (declaring done before the checkable criterion), *sediment* (stale lines kept because deleting felt risky), *sprawl* (too much always-visible material), and *no-op prose* ("be careful", "use best practices").
Its positive rules: co-locate rule + caveat + example + verification, and end every step with a checkable completion criterion.

**Absorptive interchange posture.**
Hermes treats SKILL.md as a cross-vendor interchange format — it installs directly from `openai/skills` and `anthropics/skills` — and layers all vendor behavior additively under a `metadata.hermes.*` namespace.

## 3. Runtime plumbing (targeting Hermes)

- Mount: `~/.hermes/skills/<category>/<name>/SKILL.md` (plus `skills.external_dirs` in `~/.hermes/config.yaml`; local wins on name conflict). Every installed skill becomes a slash command automatically; up to 5 stack in one line.
- Validator limits: name lowercase/numbers/hyphens ≤ 64 chars; description ≤ 1024 chars; whole file ≤ 100k chars; supporting files ≤ 1 MiB. House HARDLINE: description ≤ 60 chars, one sentence, ends with a period.
- `metadata.hermes.*` fields: `tags`, `related_skills`, `requires_toolsets`/`requires_tools` (hide skill when tools missing), `fallback_for_*` (hide when tools present), `config` (persisted settings), `blueprint` (cron schedule → scheduled automation); plus top-level `required_environment_variables` / `required_credential_files`.
- Body templating: `${HERMES_SKILL_DIR}` and `${HERMES_SESSION_ID}` substitution, and `` !`command` `` inline shell execution at load time (4000-char output cap).
- `skill_manage` tool (create / edit / patch / delete / write_file / remove_file); `skills.write_approval: true` stages agent writes for human approval.
- Hub: `hermes skills browse|search|inspect|install|check|update`; trust tiers `builtin > official > trusted > community` (community needs `--force` past caution findings); hub installs are security-scanned. Smoke test: `hermes chat --toolsets skills -q "Use the X skill to do Y"`.
- House style: prose names Hermes's own tools (`read_file`, `search_files`, `patch`) instead of raw shell utilities.

## 4. Divergences from this library

- **Description length points the opposite way.** Hermes HARDLINEs ≤ 60 chars because its index truncates there; this library warns *under* 200 (contract §3) because the description is the sole triggering surface and must carry trigger phrases. Each answers its own runtime's routing surface — recorded, not averaged.
- **Frontmatter surface.** House style carries `version`, `author`, `license`, `platforms`, `metadata.hermes.*`; the contract fixes exactly three keys (contract §1).
- **Runtime-owned tool naming.** Hermes deliberately frames prose through its own tool surface; this library's admission check requires vendor-agnostic plain-Markdown instructions.
- **Dynamic skill bodies.** Inline shell execution makes SKILL.md dynamic at load; this library's skills stay static Markdown with `${ENV_VAR}` indirection.
- **Skills as scheduled jobs.** The `blueprint` field conflates a skill with a cron automation; this library keeps scheduling outside the package.

## 5. Absorbed into core

- Experience capture — corrections leave chat memory before the session ends → confirms and sharpens `lifecycle.md` §3 (record-a-correction) and the standing anti-pattern in `SKILL.md`; Hermes's contribution is making it a standing behavior, not a request.
- Conservative curation (archive/deprecate, never silent delete; human-authored content protected) → confirms `lifecycle.md` §5 retire path.
- Hard-limit vs attention-budget distinction → confirms `contract.md` §3's warn band (200–700) inside the hard bounds (1..1024) as two different kinds of constraint.
- Skills-vs-memory boundary → confirms the admission check (reusable procedural craft, not project-local declarative facts).
