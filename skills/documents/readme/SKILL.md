---
name: readme
description: '"write a README", "update the readme", "project entry point doc", "how do I document the repo root" — author the repository README as a one-minute entry point that links out to docs/. Loaded on demand by the documents waypoint.'
---

# readme

Author the repository `README.md`: the entry point that answers "what is this and how do I start?" in under a minute. Template: `template.md` (beside this file). Canonical location: repo root `README.md`.

The README is a **map, not a manual**. It orients a newcomer and links out to `docs/` for depth. It never duplicates an ADR body, the architecture map, or rule text — it points at them.

## Sections

| Section | Holds |
|---------|-------|
| Title + one-liner | What the project is and who it is for, in one sentence. |
| Overview | 2–4 sentences: the problem solved and the high-level approach. |
| Quick start | The shortest path to a working state — clone, install, run, as runnable commands. |
| Commands | A small table of the handful of commands a contributor actually runs daily. |
| Architecture | A few sentences on how the system fits together, then links to `docs/architecture.md` and the key ADRs in `docs/decisions/`. |
| Layout | The `docs/` ontology and the few top-level dirs that matter. |
| Contributing | The shortest path from "I want to change this" to a reviewable PR, including the ADR rule for cross-cutting decisions. |
| License | The license name / link. |

## Authoring steps

1. Copy `template.md` to the repo-root `README.md`.
2. Fill the one-liner and Overview first — if you cannot state the project in one sentence, the README is not ready.
3. Make Quick start **runnable**: real clone/install/run commands a newcomer can paste, not prose.
4. In Architecture, write 2–3 orienting sentences, then **link** to `docs/architecture.md` and the relevant `docs/decisions/ADR-NNN-*.md` files. Do not restate their bodies.
5. Keep the Commands table to the commands that are actually used; delete the rest.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "I'll explain the whole architecture here so it's all in one place." | The README is a map. Architecture depth lives in `docs/architecture.md` and ADRs; duplicating it creates two sources that drift. Link out. |
| "The quick start can just describe the steps in prose." | A newcomer pastes commands. Prose forces them to translate; give runnable commands. |
| "I'll list every command the project has." | The README lists the daily-driver commands. An exhaustive dump buries the three that matter. |

## Red flags

- A README that restates an ADR or `architecture.md` body instead of linking to it
- A Quick start with no runnable commands
- A Commands table that has grown into an exhaustive CLI reference
- Architecture prose with no link out to `docs/`

## Verification

- [ ] The project is stated in one sentence before any depth
- [ ] Quick start is runnable commands, not prose
- [ ] Architecture links to `docs/architecture.md` and ADRs rather than restating them
- [ ] Commands table holds only the commands actually used
- [ ] Contributing names the ADR rule for cross-cutting decisions
