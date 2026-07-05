---
name: backend
description: '"build an API endpoint", "백엔드 구조 잡아줘", "should this be layered or hexagonal", "set up a new backend service" — architecture-gated backend engineering. Routes through a PHASE 0 gate that detects layered / vertical-slice / hexagonal from folder shape, then loads the matching reference (references/layered.md, vertical-slice.md, hexagonal.md) plus always-on API design and folder-convention references.'
version: 1.0.0
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob]
compatibility: claude-code, codex
---

# backend

Engineer backend services under one discipline: **one architecture per service, one dependency direction, contract before code.**

## Overview

This skill is an index. Shared rules live here; the per-architecture iron list lives in `references/`. Load the matching reference before writing a line of service code.

## When to Use

- Building or reviewing a backend service, API, or persistence layer, in any language.
- Deciding how to structure a new service (layered vs vertical-slice vs hexagonal).
- Adding an endpoint, use case, or repository to an existing service.
- Reviewing folder structure or dependency direction for architecture drift.

Do not use for: per-file type/style discipline or parse-don't-validate input handling at the boundary (the `programming` skill owns that), test suite design (`testing` skill), authz/injection/rate-limiting hardening (`security` skill), frontend rendering architecture (`frontend` skill).

## PHASE 0 — architecture gate (run first, every time)

Do not write or edit service code before this gate.

1. Detect the existing architecture from folder shape:

```bash
# Layered signal — controller/service/repository triad
find . -type d \( -iname controllers -o -iname services -o -iname repositories \) \
  -not -path '*/node_modules/*' -not -path '*/.venv/*'

# Vertical-slice signal — features/<use-case> grouping
find . -maxdepth 3 -type d -path '*/features/*' -not -path '*/node_modules/*'

# Hexagonal signal — domain/ports/adapters triad
find . -type d \( -iname domain -o -iname ports -o -iname adapters \) \
  -not -path '*/node_modules/*'
```

Read: whichever triad returns the most non-empty hits is the incumbent architecture. Two triads both hitting strongly means mixed-pattern drift already exists (see `folders.md`) — flag it; do not layer a third pattern on top.

2. **Respect the incumbent — the #1 absolute rule.** An existing service keeps its detected architecture for every edit. Never mix patterns in one service: a controller calling a repository directly in an otherwise-layered service, or a use-case importing framework code in an otherwise-hexagonal service, are both violations. Migrating a whole service's architecture is a separate, explicitly-scoped change — never a side effect of a feature edit.

3. No incumbent detected (greenfield service) → choose from the table, then load the matching reference:

| Signal | Choose | Why |
|---|---|---|
| Small team (1-3), CRUD-heavy, low domain complexity | Layered | Fastest to build, lowest ceremony, easiest onboarding. |
| Multiple feature teams need independent change/deploy cadence; high feature count and velocity | Vertical-slice | Each feature slice ships and changes without touching siblings. |
| Complex domain logic, multiple delivery mechanisms (HTTP + CLI + queue), domain must outlive the framework | Hexagonal | Framework-agnostic core, swappable adapters, protects a long-lived domain investment. |

Grey zone — genuinely ambiguous (mid-size team, moderate complexity, no clear second delivery mechanism) → default to layered; it is the cheapest architecture to migrate away from later.

4. Route to the matching reference:

| Scope | Read |
|---|---|
| Layered service (detected or chosen) | `references/layered.md` |
| Vertical-slice service | `references/vertical-slice.md` |
| Hexagonal service | `references/hexagonal.md` |
| Any service exposing an API (always) | `references/api-design.md` |
| Any service, before creating folders | `references/folders.md` |

## Requirements

- `grep`, `find`: POSIX; used for every detection command in this skill and its references.
- Python services: FastAPI + Pydantic v2 + `uv` (see the `programming` skill for per-file discipline).
- TypeScript services: Express or Nest + zod + strict `tsc` (see the `programming` skill for per-file discipline).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It's one small endpoint, I'll just call the repository from the controller this once." | One skip normalizes the next; the dependency-direction rule has zero exceptions inside a layered service. |
| "This service is CRUD-only but hexagonal looks more professional." | Ports/adapters ceremony earns its cost only with a real second delivery mechanism or a domain that must outlive the framework. A CRUD app pays the cost with no return — use layered. |
| "I'll just add a `shared/` helper for this one slice, it's convenient." | `shared/` is admitted only after a rule of three (identical logic in ≥3 slices). One occurrence is coincidence, not a pattern. |
| "The API field's meaning changed slightly, docs will explain it." | Every observed behavior is a contract whether documented or not. A silent field-meaning change breaks whoever already parses it the old way. |
| "I'll add a v2 API alongside v1 and migrate later." | Long-lived parallel versions rarely get retired. Evolve v1 additively; version only when a break is unavoidable, and set a deprecation date immediately. |
| "This project already mixes patterns, adding one more won't matter." | Existing drift is a bug to flag, not a precedent to extend. Report it; do not add a third pattern on top. |

## Red Flags

- A controller importing a repository or ORM session directly.
- A service function taking or returning an HTTP framework type (`Request`, `Response`).
- Domain code (`domain/`) importing a web framework or ORM.
- A feature slice importing another slice's internals outside `shared/`.
- Two or more architecture-triad folders (`controllers/`+`services/`+`repositories/` alongside `domain/`+`ports/`+`adapters/`) coexisting in one service.
- An API response reusing a repurposed field's old name for a new meaning.
- More than one API version directory alive with no deprecation date set on the older one.

## Verification

- [ ] PHASE 0 detection commands were run and the incumbent architecture (or its absence) was confirmed before writing code.
- [ ] The matching reference file was read in full before structural changes.
- [ ] No dependency-direction violation — the grep commands in the loaded reference return no unexplained hits.
- [ ] No architecture mixing — exactly one pattern's folder shape is present per service.
- [ ] New API surface followed the contract-first and observed-behavior rules in `api-design.md`.
- [ ] Folder shape matches `folders.md` for the chosen architecture and framework.
