---
name: skillify
description: Owns the full lifecycle of craft-skills skill packages — creating, updating, moving/renaming, and retiring them — through an eval-first authoring loop and deterministic format validation. Use when a user says things like "make a skill", "skillify this workflow", "turn this into a skill", "update this skill", "move this skill", or "스킬 만들자", or when a recurring workflow correction needs to be encoded into a governing skill instead of staying in chat memory. Not for one-off project scripts or prompts with no reuse intent — those stay local to the originating project.
metadata:
  version: 4.2.0
---

# skillify

Turns a repeated workflow into a well-formed craft-skills package — `SKILL.md` +
`CHANGELOG.md`, plus whatever `references/`, `scripts/`, `templates/`, or `tests/` it needs
— and owns that package's lifecycle afterward. Success looks like: the package passes both
Layer-1 validators, its description triggers correctly and only on the intended prompts,
and it ships as branch → commit → PR.

## Admission check

Before authoring anything, answer three questions. All three "yes" → proceed. Any "no" →
keep the candidate project-local, or point at the upstream harness that already owns it,
instead of authoring here.

1. **Reusable craft?** True and useful on a next project whose stack is unrelated to the
   one it came from — not a one-off artifact bound to this project's paths or data.
2. **Owned by this library?** No mature upstream harness already performs this workflow.
3. **Vendor-agnostic?** Runs as plain Markdown instructions with `${ENV_VAR}` indirection —
   no call that only one runtime exposes.

## Detect mode

```bash
SKILL_DIR="skills/<skill-name>"
test -f "$SKILL_DIR/SKILL.md" && mode=update || mode=create
```

## Eval-first authoring loop (the quality gate)

Before writing `SKILL.md`, draft the eval scenarios that will judge it — evals are the
quality bar, not a manual sign-off round:

1. Draft `evals/evals.json` — about 3 realistic scenarios (prompt + expected behavior).
2. Draft `evals/triggers.json` — 8 should-trigger + 8 near-miss should-NOT-trigger prompts
   pulled from sibling skills' domains.
3. Run each scenario without the skill, then with the drafted body; iterate until behavior
   matches. Run the 16 trigger prompts against the drafted description; tighten the "Not
   for X" boundary sentence wherever a near-miss would plausibly match.

`evals/` is local scratch — gitignored, never committed. Full contract: `references/contract.md §7`.

## Author the package

Frontmatter is exactly `name`, `description`, `metadata.version` — nothing else. Name is
kebab-case and equals the directory: verb-first for a skill the user explicitly triggers,
a plain noun for a skill that supplies ambient domain context. Description is third
person, states what + when, weaves in 3–6 real trigger phrases, and adds a "Not for X" line
when a sibling overlaps. Body targets 150 lines, hard-caps at 500; move depth to
`references/*.md`. Keep package content MECE: each rule has one owning section or
reference, and nearby locations link to it instead of restating it. Full rules:
`references/contract.md`.

## Lifecycle

- **Create:** clear the admission check, draft evals, author the package, validate, PR.
- **Update:** patch `SKILL.md`/references, bump `metadata.version`, append one `CHANGELOG.md`
  bullet, validate, PR. When the operator corrects unwanted behavior mid-session, record it
  via the three-way split — workflow step + `## Anti-patterns` entry + CHANGELOG bullet
  (`references/lifecycle.md §3`).
- **Move/rename:** `git mv` the whole directory, fix every path reference across the repo,
  verify by loading. `references/lifecycle.md §4`.
- **Retire:** add a `## Deprecated` section at the top of the body pointing at the
  replacement, bump MAJOR, PR; delete the directory only once nothing still routes to it.
  `references/lifecycle.md §5`.

Before any change: `git status`, stash unrelated work, `git fetch origin --prune`, switch
to `main`, `git pull --ff-only`, branch. Never stack edits on a dirty branch.

## Validate (Layer 1 — deterministic, CI-enforced)

```bash
python3 skills/skillify/scripts/validate-skill-format.py --diff-base origin/main...HEAD
python3 skills/skillify/scripts/validate-runtime-hygiene.py --diff-base origin/main...HEAD
```

Both gate CI on changed packages only; drop `--diff-base` for a full inventory.

## Secrets

Every credential, token, or host-specific value lives in `$SKILL_DIR/.env` (gitignored);
commit only `.env.example` with placeholders. Remediation for an already-committed secret:
`references/runtime-hygiene.md §4`.

## Deliver

Every change ships branch → commit → PR unless the operator explicitly asks for
local-only. A patched file with no PR is not done. Mechanics: `references/lifecycle.md §6`.

## Requirements

- `python3` — both Layer-1 validators
- `gh` — PR creation and branch flow

## Anti-patterns

- Skipping branch → PR because "it's a small edit" → the deliverable is reviewable repo state; open the PR.
- Deferring the CHANGELOG bullet to "later" → Layer-1 CI fails a changed package with no dated bullet; add it in the same commit.
- Authoring before `evals/evals.json` + `evals/triggers.json` exist → evals judge behavior and trigger-fit first; tests lock in behavior only once proven.
- A longer, descriptive skill name "for clarity" → the name is a compact handle; discoverability lives in the description's trigger phrases.
- An API key or real path inline "for now" → secrets live in the per-skill `.env`; a committed secret means history rewrite + rotation.
- A `## Change Log` section inside `SKILL.md` → history lives only in `CHANGELOG.md`.
- A description written as an abstract capability blurb → weave in real user trigger phrases.
- A nested `SKILL.md` anywhere inside a package → every skill is one flat directory.
- An operator correction left in chat memory → record it via the three-way split before the session ends (`references/lifecycle.md §3`).
- Operator-supplied source material left in chat history → land the excerpt as `references/*.md` and add a `Provenance:` clause to the CHANGELOG bullet.
- Duplicated overlapping guidance inside one package → apply `references/contract.md` §9; link to the owner instead of restating the rule.

## Verification

- [ ] `validate-skill-format.py --diff-base origin/main...HEAD` passes
- [ ] `validate-runtime-hygiene.py --diff-base origin/main...HEAD` passes
- [ ] `evals/` scenarios ran clean and the 16 trigger prompts route correctly
- [ ] `CHANGELOG.md` has a new dated bullet; `metadata.version` bumped
- [ ] Secrets only in per-skill `.env`; `.env.example` committed with placeholders
- [ ] Branch → commit → PR opened (unless explicitly local-only)
