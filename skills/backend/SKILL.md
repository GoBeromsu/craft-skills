---
name: backend
description: Routes backend service engineering through an architecture-detection gate — layered, vertical-slice, or hexagonal — then applies dependency-direction rules, persistence choices, and per-framework folder conventions. Use when building a backend service, setting up production-fidelity local database development, deciding whether a service should be layered or hexagonal, choosing Prisma or preserving an incumbent ORM, adding a repository or use case to an existing service, or reviewing folder structure for architecture drift (e.g. "백엔드 구조 잡아줘"). Not for public HTTP API contracts — use api; not for UI rendering work — use frontend.
metadata:
  version: 2.2.0
---

# backend

Engineer backend services under one discipline: one architecture per service, one dependency direction, and production-fidelity persistence. Done means the incumbent architecture is respected, the loaded reference's dependency-direction greps return no unexplained hits, and database engine plus ORM choices are explicit before persistence code is written.

## PHASE 0 — architecture gate (run first, every time)

Do not write or edit service code before this gate.

1. Detect the existing architecture from folder shape. Run every command below from the service's own root — the directory holding that service's `pyproject.toml` or `package.json` — never from a monorepo root, which mixes multiple services' folders into one reading and manufactures false mixed-pattern-drift flags.

```bash
# Layered signal — controller/service/repository triad
find . -type d \( -iname controllers -o -iname services -o -iname repositories \) \
  -not -path '*/node_modules/*' -not -path '*/.venv/*' | sed 's|.*/||' | sort -u

# Vertical-slice signal — features/<use-case> grouping
find . -maxdepth 5 -type d -path '*/features/*' -not -path '*/node_modules/*'

# Hexagonal signal — domain/ports/adapters triad
find . -type d \( -iname domain -o -iname ports -o -iname adapters \) \
  -not -path '*/node_modules/*' | sed 's|.*/||' | sort -u
```

A triad needs **≥2 of its 3 names present** to classify the incumbent architecture — layered needs 2 of {`controllers`, `services`, `repositories`}; hexagonal needs 2 of {`domain`, `ports`, `adapters`}. Exactly one name present is a grey zone: judge by import direction instead (does that lone folder reach straight into an ORM/session, layered-style, or sit behind a port/interface, hexagonal-style?). Both triads clearing the threshold at once means mixed-pattern drift already exists (see `references/folders.md`) — flag it; do not layer a third pattern on top.

2. Respect the incumbent. An existing service keeps its detected architecture for every edit — a controller calling a repository directly in an otherwise-layered service, or a use-case importing framework code in an otherwise-hexagonal service, are both violations. Migrating a whole service's architecture is a separate, explicitly-scoped change, never a side effect of a feature edit.

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
| Any service choosing a database engine or ORM | `references/persistence.md` |
| Any service, before creating folders | `references/folders.md` |

## Requirements

- `grep`, `find`: POSIX; used by every detection command in this skill and its references.
- Python services: FastAPI + Pydantic v2 + `uv`. TypeScript services: Express or Nest + zod + strict `tsc` — the `programming` skill owns per-file discipline for both.
- Any other language: the architecture and dependency-direction rules apply regardless of language; stack conventions (framework, validation library, package manager) come from the incumbent codebase, not from this list.

## Boundaries

Not for: public HTTP API contracts, response shapes, or REST conventions (`api` skill); per-file type/style discipline or parse-don't-validate input handling at the boundary (`programming` skill); test suite design (`testing` skill); authz/injection/rate-limiting hardening (`security` skill); frontend rendering architecture (`frontend` skill).

## Anti-patterns

- Calling the repository directly from the controller as a one-off shortcut → keep the dependency-direction rule with zero exceptions in a layered service; one skip normalizes the next.
- Picking hexagonal for a CRUD-only service because it looks more professional → use layered; ports/adapters ceremony only pays off with a real second delivery mechanism or a domain that must outlive the framework.
- Adding a `shared/` helper for a single slice because it's convenient → wait for a rule of three (identical logic in ≥3 slices) before admitting `shared/`; one occurrence is coincidence, not a pattern.
- Adding a third architecture pattern because the project already mixes patterns → report existing drift as a bug to flag, not a precedent to extend.
- A controller importing a repository or ORM session directly → route data access through the service layer instead.
- A service function taking or returning an HTTP framework type (`Request`, `Response`) → keep HTTP types confined to controllers; pass plain domain types to services.
- Domain code (`domain/`) importing a web framework or ORM → keep domain code framework-agnostic; put such calls behind a port/adapter.
- A feature slice importing another slice's internals outside `shared/` → import only through `shared/` or a public interface, never another slice's internals.
- Two or more architecture-triad folders (`controllers/`+`services/`+`repositories/` alongside `domain/`+`ports/`+`adapters/`) coexisting in one service → keep exactly one pattern per service; flag mixed-pattern drift instead of layering a third pattern on top.

## Verification

- [ ] PHASE 0 detection commands were run and the incumbent architecture (or its absence) was confirmed before writing code.
- [ ] The matching reference file was read in full before structural changes.
- [ ] No dependency-direction violation — the grep commands in the loaded reference return no unexplained hits.
- [ ] No architecture mixing — exactly one pattern's folder shape is present per service, confirmed by running PHASE 0 detection from that service's own root (never a monorepo root).
- [ ] Database engine and ORM decisions follow `references/persistence.md`; public API contracts were defined through the `api` skill.
- [ ] Folder shape matches `references/folders.md` for the chosen architecture and framework.
