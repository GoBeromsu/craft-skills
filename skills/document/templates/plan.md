---
slug: {kebab-description}
date: YYYY-MM-DD
author: {name or agent}
spec: {slug of the corresponding spec, or "none"}
status: active
superseded-by:
finalized: false
---

# Plan: {Feature or Task Title}

## Approach

{Core strategy and rationale}

## Steps

| # | Implementation step | Concrete paths | Acceptance conditions | Agent-executable QA (happy + failure) |
|---:|---|---|---|---|
| 1 | {Imperative implementation step} | `{path/to/file}` | {Observable completed behavior} | Happy: `{command or scenario}` → {expected result}; Failure: `{command or scenario}` → {expected rejection or error} |
| 2 | {Imperative implementation step} | `{path/to/file}` | {Observable completed behavior} | Happy: `{command or scenario}` → {expected result}; Failure: `{command or scenario}` → {expected rejection or error} |

## Files affected

| File | Change type | Notes |
|------|-------------|-------|
| `{path}` | create / modify / delete | {Planned change} |

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| {Risk} | {Mitigation} |

## Verification

| Check | Command or scenario | Expected result |
|-------|---------------------|-----------------|
| {Check} | `{command or scenario}` | {Result} |

## Decision notes

| Decision or trade-off | Rationale | ADR |
|-----------------------|-----------|-----|
| {Note} | {Rationale} | {Link or none} |
