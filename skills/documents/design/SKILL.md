---
name: design
description: '"design.md", "design system doc", "design tokens", "디자인 시스템 문서" — author or update a project design.md: the single source of truth for a design system''s principles, tokens, typography, primitive interaction states, motion, responsive rules, and accepted debt. Loaded on demand by the documents waypoint.'
---

# design

Author or update `design.md`: the single, self-complete source of truth for a project's design system. Template: `template.md` (beside this file). Canonical location: `docs/design.md` (per-app in a monorepo — see Placement).

A **token** is a named, literal design value — a color hex, a spacing unit, a type-scale step — referenced by name instead of a raw literal repeated ad hoc across components. A **primitive** is the smallest reusable UI building block a design system ships (button, input, checkbox) that composed components and features are built from.

Frontend engineering work gates on `design.md` existing before UI code is written; that gate and its enforcement belong to the frontend skill. This skill owns `design.md`'s structure and lifecycle only — not component-coding rules.

## The 7-section contract

Every `design.md` carries exactly these sections, in this order.

| # | Section | Holds |
|---|---------|-------|
| 1 | Principles | ≤5 principles; each pairs the rule with a concrete "so we never {counter-example}" |
| 2 | Tokens | Color, spacing, and type-scale tokens as literal values with names — the vocabulary every other section references |
| 3 | Typography | Roles, not fonts — heading/body/mono usage rules (when to use each role, not which font file backs it) |
| 4 | Primitives inventory | One `### {PrimitiveName}` entry per primitive; each entry is a state table (see below) |
| 5 | Motion | Durations and easings as named tokens; the reduced-motion rule |
| 6 | Responsive | Breakpoint tokens and the layout behavior at each breakpoint |
| 7 | Accepted debt | Dated deviations from the system, each with an upgrade path |

## Primitives inventory — states before code

Every primitive's entry is a state table covering, at minimum: `default`, `hover`, `active`, `focus`, `disabled`, `loading`. A primitive that renders or displays data (a list item, a card, a table row) additionally covers `empty` and `error`.

**A primitive without its state table is not done.** Fill the table before writing the component's code, not after. If a state's visual is genuinely identical to another state's, write "= {other state}" rather than omitting the row — an omitted row reads as "not designed," not "same as."

## Authoring steps

1. Copy `template.md` to `docs/design.md` (or the per-app path in a monorepo).
2. Fill Principles and Tokens first — every later section references token names, so tokens must exist before typography, primitives, motion, or responsive rules are written.
3. For each primitive the project ships, write its state table before any component code exists for it.
4. Seed Accepted debt with any known gap the team is knowingly shipping without (for example, a primitive with no dark-mode value yet) — date it and name the upgrade path.

## Lifecycle

### Same-commit law

A commit that introduces or changes a token, primitive, or pattern updates `design.md` in that same commit. Detect a commit that touched components without touching `design.md`:

```bash
git diff --name-only HEAD~1 | grep -q '^{components-dir}/' && \
  ! git diff --name-only HEAD~1 | grep -q 'design\.md$'
```

Exit `0` (the `&&` chain succeeds) → components changed and `design.md` did not → flag the commit. Any other exit code → pass.

### Staleness audit

Compare the components directory against the primitives inventory (contract §4) to find primitives that exist in code but were never entered:

```bash
comm -23 \
  <(ls {components-dir} | sed -E 's/\.[jt]sx?$//' | sort) \
  <(grep '^### ' docs/design.md | sed 's/^### //' | sort)
```

Any line printed is an orphan — a component with no `design.md` entry. Empty output → pass.

### Anti-generic rule

Tokens used in a component come from this project's `design.md`, never a UI framework's stock visual defaults (default theme grays, default border-radius scale, default gradient utilities). Approximate detection — a literal color value in component source with no matching token in `design.md`:

```bash
grep -rnE '#[0-9a-fA-F]{3,6}\b' {components-dir} \
  | grep -vFf <(grep -oE '#[0-9a-fA-F]{3,6}\b' docs/design.md)
```

Any match is a color used in code that is not a registered token — add it to Tokens or replace it with an existing token. Approximate: a one-off illustrative color (in a comment or a test fixture) can false-positive; judge by whether the match sits in shipped component code.

## Placement

`design.md` lives at `docs/design.md` by default. In a monorepo with multiple deployable apps, each app carries its own `docs/design.md` — do not centralize one shared file across apps whose design systems have diverged.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "I'll code the button first and document its states after." | The states-before-code rule exists because writing the table first is what surfaces missed states (focus-visible, loading, disabled+hover) before they ship undesigned. |
| "This component is simple, it only has one state." | Every primitive has at least default/hover/active/focus/disabled; a one-row table is a red flag, not a shortcut. |
| "I'll update design.md in a follow-up commit." | The same-commit law exists because a follow-up commit is exactly where the update gets forgotten; the detection command flags the gap immediately, not the follow-up's absence. |
| "This shade of blue is just for this one component." | A literal value outside the token table is exactly what the anti-generic detection flags — either it is a real design decision (add the token) or it should not exist. |

## Red flags

- A primitive with no state table, or a state table missing `disabled` or `focus`
- A commit that adds a component without a matching `design.md` update
- Component code with literal color or spacing values that duplicate an existing token under another name
- Accepted debt with no date or no upgrade path
- A monorepo with one `design.md` covering apps whose design systems have diverged

## Verification

- [ ] All 7 sections present, in order, each non-empty
- [ ] Every primitive in the components directory has a matching state table (staleness audit clean)
- [ ] Every state table covers at minimum default/hover/active/focus/disabled/loading; empty/error added for data-bearing components
- [ ] No component change landed without a same-commit `design.md` update
- [ ] Accepted debt entries are dated and each names an upgrade path
