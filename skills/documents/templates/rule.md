---
slug: {kebab-description}         # must match the filename (without .md)
date: YYYY-MM-DD
author: {name or agent}
governing-adr: ADR-NNN            # the ADR whose decision this rule operationalizes, or "none"
status: active                     # active | deprecated
---

# Rule: {Convention Title}

<!--
PURPOSE: Specify a standing convention — an ongoing constraint that applies to all
work in this area, not scoped to a single feature or decision event.

A rule answers "what must we always do?" — the operational guidance.
The WHY behind the rule belongs in the governing ADR (see frontmatter).
If no ADR exists for a non-trivial rule, consider writing one.

This file is alive as long as the convention holds. Deprecate (do not delete)
when the convention is retired.
-->

## Rule

<!-- State the convention as a present-tense imperative. Be specific enough that
     compliance is unambiguous. -->

## Rationale

<!-- Brief explanation of why this rule exists. For a full decision record,
     link to the governing ADR rather than restating it here. -->

<!-- Governing ADR: docs/decisions/{governing-adr}.md -->

## Scope

<!-- Which parts of the codebase, team, or workflow this rule applies to. -->

## Examples

### Compliant

```
{show a concrete compliant example}
```

### Non-compliant

```
{show a concrete violation and explain why it fails}
```

## Exceptions

<!-- Conditions under which the rule does not apply, if any. "None" is a valid answer. -->

## Enforcement

<!-- How compliance is verified: CI check, code review, hook, convention-only, etc. -->
