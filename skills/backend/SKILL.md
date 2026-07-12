---
name: backend
description: Routes backend service engineering through an architecture-detection gate — layered, vertical-slice, or hexagonal — then applies dependency-direction rules, persistence choices, and folder conventions. Use when building a backend service or designing the service layer for a new endpoint, setting up production-fidelity local database development, deciding whether a service should be layered or hexagonal, choosing Prisma or preserving an incumbent ORM, adding a repository or use case to an existing service, or reviewing folder structure for architecture drift (e.g. "백엔드 구조 잡아줘"). Not for public HTTP API contracts — use api; not for UI rendering work — use frontend.
metadata:
  version: 3.1.0
---

# backend

Engineer backend services under one discipline: preserve the incumbent architecture and dependency direction, and make persistence choices explicit. Done means structural changes follow manifest and import-direction evidence rather than folder names alone, and database decisions fit the existing service or an explicitly greenfield one.

## Architecture gate

Use this gate before choosing an architecture or creating service folders. Small changes follow the established imports and conventions they touch.

1. Work from the service root — the directory holding that service's `pyproject.toml` or `package.json`. Inspect its manifest, entrypoint, and imports first; they identify the service boundary and dependency direction more reliably than folder labels. Use these folder shapes as candidate signals, not a classification:

   ```bash
   # Layered signal — controller/service/repository names
   find . -type d \( -iname controllers -o -iname services -o -iname repositories \) \
     -not -path '*/node_modules/*' -not -path '*/.venv/*' | sed 's|.*/||' | sort -u

   # Vertical-slice signal — features/<use-case> grouping
   find . -maxdepth 5 -type d -path '*/features/*' -not -path '*/node_modules/*'

   # Hexagonal signal — domain/ports/adapters names
   find . -type d \( -iname domain -o -iname ports -o -iname adapters \) \
     -not -path '*/node_modules/*' | sed 's|.*/||' | sort -u
   ```

   Confirm a candidate by import direction: controller → service → repository supports layered; feature-local imports support vertical slices; domain/use case → port with adapters at the edge supports hexagonal. A lone folder or multiple triads is inconclusive evidence, not permission to add a pattern.

2. An existing service keeps its architecture, framework, validation, package-manager, and folder conventions in every language. When manifest or import evidence is incomplete, preserve the nearest local convention and avoid new architecture scaffolding. A whole-service migration needs explicit scope; it is never a feature side effect.

3. Only a service with no incumbent source is greenfield. Choose from the table, then load the matching reference:

   | Signal | Choose | Why |
   |---|---|---|
   | Small team (1-3), CRUD-heavy, low domain complexity | Layered | Fastest to build, lowest ceremony, easiest onboarding. |
   | Multiple feature teams need independent change/deploy cadence; high feature count and velocity | Vertical-slice | Each feature slice ships and changes without touching siblings. |
   | Complex domain logic, multiple delivery mechanisms (HTTP + CLI + queue), domain must outlive the framework | Hexagonal | Framework-agnostic core, swappable adapters, protects a long-lived domain investment. |

   A genuinely ambiguous greenfield service defaults to layered because it is the cheapest architecture to migrate away from later.

4. Route to the matching reference:

   | Scope | Read |
   |---|---|
   | Layered service (detected or chosen) | `references/layered.md` |
   | Vertical-slice service | `references/vertical-slice.md` |
   | Hexagonal service | `references/hexagonal.md` |
   | Any service choosing a database engine or ORM | `references/persistence.md` |
   | Any service creating folders | `references/folders.md` |

## Requirements

- `grep`, `find`: POSIX; used by every detection command in this skill and its references.
- Greenfield Python services may start with FastAPI + Pydantic v2 + `uv`; greenfield TypeScript services may start with Express or Nest + zod + strict `tsc`. These are defaults, not migration directives; `programming` owns per-file discipline for both.
- Every incumbent service, in any language, keeps its observed framework, validation library, package manager, and stack conventions unless an explicit migration scope says otherwise.

## Boundaries

Not for: public HTTP API contracts, response shapes, or REST conventions (`api` skill); per-file type/style discipline or parse-don't-validate input handling at the boundary (`programming` skill); test suite design (`testing` skill); authz/injection/rate-limiting hardening (`security` skill); frontend rendering architecture (`frontend` skill).

## Anti-patterns

- Calling the repository directly from the controller as a one-off shortcut → keep the dependency-direction rule with zero exceptions in a layered service; one skip normalizes the next.
- Picking hexagonal for a CRUD-only service because it looks more professional → use layered; ports/adapters ceremony only pays off with a real second delivery mechanism or a domain that must outlive the framework.
- Adding a `shared/` helper because repeated code merely looks similar → extract only when a named owner accepts it, its semantic identity is shared, its changes are coupled, and the incumbent convention supports the boundary.
- Adding a third architecture pattern because the project already mixes patterns → report existing drift as a bug to flag, not a precedent to extend.
- A controller importing a repository or ORM session directly → route data access through the service layer instead.
- A service function taking or returning an HTTP framework type (`Request`, `Response`) → keep HTTP types confined to controllers; pass plain domain types to services.
- Domain code (`domain/`) importing a web framework or ORM → keep domain code framework-agnostic; put such calls behind a port/adapter.
- A feature slice importing another slice's internals outside `shared/` → import only through `shared/` or a public interface, never another slice's internals.
- Two or more architecture-triad folders (`controllers/`+`services/`+`repositories/` alongside `domain/`+`ports/`+`adapters/`) coexisting in one service → keep exactly one pattern per service; flag mixed-pattern drift instead of layering a third pattern on top.

## Verification

- [ ] Manifest, entrypoint, and import-direction evidence were inspected before folder names; any folder triad was treated as a candidate signal.
- [ ] Existing services retained their architecture and stack conventions; a greenfield choice was made only where no incumbent source exists.
- [ ] The matching reference file was read before structural changes.
- [ ] No dependency-direction violation — the grep commands in the loaded reference return no unexplained hits.
- [ ] Database engine and ORM decisions follow `references/persistence.md`; public API contracts were defined through the `api` skill.
- [ ] Folder shape matches `references/folders.md` for the established or chosen architecture.
