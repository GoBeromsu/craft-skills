# OpenAI Lens (Codex)

## 1. Source

`openai/skills` → `skills/.system/skill-creator` — SKILL.md, `references/openai_yaml.md`, `scripts/init_skill.py`, `scripts/generate_openai_yaml.py`, `scripts/quick_validate.py`, `agents/openai.yaml`.

## 2. What this lab illuminates

**Scaffold-first discipline.**
OpenAI treats package structure as too important to improvise: a new skill always starts from `init_skill.py`, which emits the complete canonical shape with TODO placeholders, and editing begins from there.
The structure is deterministic; only the content is creative.

**The context window as a public good.**
The skill shares context with the system prompt, history, every other skill's metadata, and the user's actual request.
Default assumption: the model is already very smart — challenge every paragraph with "does the model really need this explanation?" and "does this justify its token cost?"
Concise examples beat verbose explanations.

**Analysis-driven planning.**
Before authoring, walk each concrete usage example and ask what a from-scratch run would redo — repeated code, re-derived schemas, re-typed boilerplate — and let that analysis dictate which package parts exist.
Resources are derived from evidence, not enthusiasm.

**Structure follows load order.**
Three loading levels (metadata always; body on trigger; resources on demand) drive every layout rule: variant-specific detail is split per variant so only the chosen one loads; references stay one level deep; files over ~10k words get grep patterns listed in SKILL.md so they can be searched instead of read.

## 3. Runtime plumbing (targeting Codex)

- `agents/openai.yaml` — product config read by the harness, not the agent. Generate deterministically with `scripts/generate_openai_yaml.py <skill-dir> --interface key=value`; regenerate when SKILL.md changes so it never goes stale.
  - `interface.display_name` — human-facing title for skill lists and chips.
  - `interface.short_description` — UI blurb, 25–64 chars.
  - `interface.default_prompt` — one-sentence starter that names the skill as `$skill-name`.
  - `interface.icon_small` / `icon_large` — asset paths relative to the skill dir (default `./assets/`); `interface.brand_color` — hex accent.
  - `dependencies.tools[]` — declared tool deps; only `type: "mcp"` is supported (`value`, `description`, `transport`, `url`).
  - Quote all string values; keep keys unquoted.
- `scripts/init_skill.py <name> --path <dir> [--resources scripts,references,assets] [--examples]` scaffolds the package: a TODO-driven SKILL.md walking four structuring patterns (workflow, task, reference, capabilities) plus `agents/openai.yaml` — the yaml is a non-optional part of init.
- `quick_validate.py` limits: name is hyphen-case, ≤ 64 chars, no leading/trailing/double hyphen; description ≤ 1024 chars and may not contain angle brackets; frontmatter allows `name`, `description`, `license`, `allowed-tools`, `metadata`.
- Codex reads only `name` + `description` for triggering; the body loads after.
- Naming style: verb-led, namespaced by tool when it aids routing (`gh-address-comments`, `linear-address-issue`).

## 4. Divergences from this library

- **Auxiliary files.** OpenAI forbids README/CHANGELOG/quick-reference files inside a package — the skill should hold only what the executing agent needs. This library keeps its mandatory per-package `CHANGELOG.md` (contract §6): recorded corrections and provenance are how the library learns, and that governance value outweighs the clutter cost of one file the agent never loads.
- **Frontmatter surface.** OpenAI admits `license` and `allowed-tools`; this library's contract fixes exactly `name`/`description`/`metadata` (contract §1) to stay portable across runtimes that ignore vendor keys.
- **Name length.** OpenAI allows up to 64 chars with tool-prefix namespacing; this library caps names at two tokens (contract §2) and pushes discoverability into the description.
- **Templates.** OpenAI folds fixed-shape artifacts into `assets/`; this library keeps a separate `templates/` for canonical artifact shapes and reserves `assets/` for output-consumed files (contract §5).

## 5. Absorbed into core

- Degrees-of-freedom rule (high/medium/low specificity matched to fragility) → `contract.md` §4.
- Plan-parts-from-concrete-examples walk → `contract.md` §5 preamble.
- `assets/` as a package part → `contract.md` §5 table.
- "The description is the only triggering surface; when-to-use prose in the body is dead weight" → `contract.md` §3.
- Context-window frugality ("only add what the model doesn't have") was already core (`contract.md` §4 "restated-obvious practice") — confirmed, not re-added.
