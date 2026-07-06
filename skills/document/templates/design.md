# Design System

<!--
PURPOSE: The single source of truth for this project's design system — principles,
tokens, typography, primitive states, motion, responsive rules, and accepted debt.
A change that introduces or changes a token, primitive, or pattern updates this file
in the same commit. See the `design` skill for the full contract and lifecycle rules.
-->

## 1. Principles

<!-- ≤5 principles. Each pairs the rule with a concrete "so we never {counter-example}". -->

1. **{Principle}** — so we never {concrete anti-pattern this principle rules out}.
2. **{Principle}** — so we never {concrete anti-pattern this principle rules out}.

## 2. Tokens

<!-- Literal values with names. Every later section references these names, never a raw literal. -->

### Color

| Token | Value | Usage |
|---|---|---|
| `color-bg-default` | `#{hex}` | Page and surface background |
| `color-fg-default` | `#{hex}` | Primary text |
| `color-accent` | `#{hex}` | Primary actions, active state |
| `color-danger` | `#{hex}` | Destructive actions, error state |

### Spacing

| Token | Value |
|---|---|
| `space-1` | `{value}` |
| `space-2` | `{value}` |
| `space-3` | `{value}` |

### Type scale

| Token | Value |
|---|---|
| `text-sm` | `{value}` |
| `text-base` | `{value}` |
| `text-lg` | `{value}` |

## 3. Typography

<!-- Roles, not fonts: when to use each role. -->

| Role | Token | Use for |
|---|---|---|
| Heading | `text-lg` / `{weight}` | Page and section titles |
| Body | `text-base` / `{weight}` | Paragraph and UI copy |
| Mono | `{mono-token}` | Code, IDs, numeric tables |

## 4. Primitives inventory

<!--
One entry per primitive. Each entry is a state table covering, at minimum:
default / hover / active / focus / disabled / loading.
A primitive that renders or displays data additionally covers: empty / error.
A primitive without its state table is not done — fill the table before coding it.
-->

### Button

| State | Visual |
|---|---|
| `default` | `color-accent` background, `color-bg-default` text, `space-2` horizontal padding |
| `hover` | Background darkened one step from `color-accent` |
| `active` | Background darkened two steps from `color-accent`; no elevation |
| `focus` | 2px `color-accent` outline, 2px offset (keyboard focus only) |
| `disabled` | 40% opacity; pointer-events none; no hover/active response |
| `loading` | Label replaced by a spinner; width held fixed to prevent layout shift |

### {DataListItem}

<!-- Example naming for a data-bearing primitive — it adds empty/error to the standard six. -->

| State | Visual |
|---|---|
| `default` | {resting visual} |
| `hover` | {hover visual} |
| `active` | {active visual} |
| `focus` | {focus visual} |
| `disabled` | {disabled visual} |
| `loading` | Skeleton placeholder at the item's resting height |
| `empty` | Placeholder row with a call-to-action, not a blank space |
| `error` | Inline retry affordance, not a silent disappearance |

## 5. Motion

<!-- Durations/easings as tokens. The reduced-motion rule is mandatory. -->

| Token | Value | Use for |
|---|---|---|
| `duration-fast` | `{ms}` | Micro-interactions (hover, focus ring) |
| `duration-base` | `{ms}` | Standard transitions (modal open, panel slide) |
| `easing-standard` | `{cubic-bezier}` | Default easing for all transitions |

**Reduced motion:** when the user's OS signals a reduced-motion preference, replace transitions with instant state changes — never disable the state change itself, only its animation.

## 6. Responsive

| Breakpoint token | Width | Layout behavior |
|---|---|---|
| `bp-sm` | `{value}` | {behavior, e.g. single column, nav collapses to a menu} |
| `bp-md` | `{value}` | {behavior} |
| `bp-lg` | `{value}` | {behavior} |

## 7. Accepted debt

<!-- Dated deviations from this system, each with an upgrade path. -->

- **{YYYY-MM-DD}** — {what was skipped, e.g. "Button has no dark-mode token yet"}. Upgrade path: {what closes the gap and when}.
