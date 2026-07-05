# Backend Folder Conventions

The folder tree is the architecture made visible — pick the tree that matches the chosen pattern (see `layered.md`, `vertical-slice.md`, `hexagonal.md`) and keep tests, migrations, and config in the place that tree implies.

## Layered — FastAPI

```
src/
  api/              # controllers — routers, request/response DTOs
  services/         # business logic, orchestration, transaction boundary
  repositories/     # persistence — queries, ORM-row to domain mapping
  domain/           # shared domain types
  db/
    migrations/     # alembic revisions
    session.py
tests/
  api/
  services/
  repositories/
configs/
  base.yaml
  production.yaml
```

## Layered — Express/Nest

```
src/
  controllers/
  services/
  repositories/
  models/           # domain / DTO types
  db/
    migrations/
    client.ts
test/
  controllers/
  services/
  repositories/
config/
  base.json
  production.json
```

## Vertical-slice — FastAPI

```
src/
  features/
    create_order/
      handler.py
      validation.py
      repository.py
      test_create_order.py
    cancel_order/
      handler.py
      validation.py
      repository.py
      test_cancel_order.py
  shared/           # admitted only past the rule of three (vertical-slice.md)
  db/
    migrations/
configs/
```

## Vertical-slice — Express/Nest

```
src/
  features/
    create-order/
      handler.ts
      validation.ts
      repository.ts
      create-order.test.ts
    cancel-order/
      handler.ts
      validation.ts
      repository.ts
      cancel-order.test.ts
  shared/
  db/
    migrations/
config/
```

## Hexagonal — FastAPI

```
src/
  domain/            # entities, value objects — zero framework imports
  ports/             # Protocols the domain depends on
  use_cases/         # orchestrates ports for one use case
  adapters/
    http/            # inbound — FastAPI routers
    persistence/     # outbound — SQLAlchemy repository implementations
      migrations/    # migrations belong to the adapter, not the domain
    notifications/
tests/
  domain/
  use_cases/         # tested against in-memory fake adapters
  adapters/
configs/
```

## Hexagonal — Express/Nest

```
src/
  domain/
  ports/             # TS interfaces the domain depends on
  use-cases/
  adapters/
    http/            # inbound — Express/Nest controllers
    persistence/     # outbound — Prisma/TypeORM repository implementations
      migrations/
    notifications/
test/
  domain/
  use-cases/
  adapters/
config/
```

## Where tests, migrations, and config live

| Concern | Layered | Vertical-slice | Hexagonal |
|---|---|---|---|
| Tests | mirrored `tests/` tree, one dir per layer (or colocated — see the `testing` skill for the placement decision) | colocated inside each feature slice | colocated per component; use-case tests run against in-memory fakes of each port, not a real database |
| Migrations | `db/migrations/` at the repo root, shared across layers | `db/migrations/` at the repo root, shared across slices | `adapters/persistence/migrations/` — the adapter owns them, never the domain |
| Config | `configs/` (or `config/`) at the repo root, one file per environment | same | same, but the domain never reads config directly; an adapter reads it and passes a typed value through a port |

## Mixed-pattern drift — detect across all three at once

```bash
have_layered=$(find ./src -maxdepth 2 -type d \( -iname controllers -o -iname services -o -iname repositories \) | wc -l)
have_slice=$(find ./src -maxdepth 1 -type d -iname features | wc -l)
have_hex=$(find ./src -maxdepth 2 -type d \( -iname domain -o -iname ports -o -iname adapters \) | wc -l)
echo "layered=$have_layered slice=$have_slice hexagonal=$have_hex"
```

Two or more of the three counts nonzero means the service is straddling two architectures. Fix: pick the one the service is closer to, and migrate the minority folders into it as a dedicated, scoped change — never silently while doing an unrelated feature edit.

## Repo topology in a GitOps split

When application source and cluster manifests live in separate repositories (a manifests/GitOps repo plus one or more app-source repos), each repo carries only its own concern:

- A manifests repo carries zero application source — only Kubernetes/Kustomize YAML (`base/`, `overlays/`), Helm charts, and the thin scripts that render them.
- An app repo never embeds cluster manifests beyond its own `deploy/` directory (a base overlay reference or a chart values file scoped to that one service) — the manifests repo is the sole owner of cross-cutting cluster topology (per-environment overlays, ingress rules, cluster-wide policy).

```bash
# Manifests repo: application source must not exist outside a thin scripts/ dir
find . -name '*.py' -o -name '*.ts' -o -name '*.go' | grep -v -E '^\./scripts/'
```

Any hit is application source leaked into a manifests-only repo. Move it to the owning app repo.

```bash
# App repo: cluster manifests must stay inside deploy/
find . -maxdepth 2 -iname 'kustomization.yaml' -not -path './deploy/*'
```

Any hit outside `deploy/` is a cluster manifest creeping into the app repo. Move it to the manifests repo, or into `deploy/` if it is genuinely scoped to this one service.

## Incumbent-respect clause

Detect the tree already in place (the mixed-pattern-drift command above doubles as the detector) and match it for new files. Introduce a new top-level folder only when it matches the chosen architecture's shape — not as a one-off convenience.
