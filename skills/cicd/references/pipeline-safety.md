# Deployment pipeline safety

Treat deployment as a state transition, not a sequence of independent shell commands. Jenkins owns the transition on the deployment server; it builds locally and does not depend on a registry.

## Preconditions

- Restrict the job checkout to `main` and use Jenkins SCM checkout, not an arbitrary user-supplied ref.
- Disable concurrent builds so two jobs cannot overwrite each other's runtime state.
- Set one fixed `COMPOSE_PROJECT_NAME` so inspection and cleanup address the intended stack.
- Require Compose inputs at interpolation time, such as `${DATABASE_URL:?required}`. An absent value must stop the release instead of silently selecting a default.
- Use named volumes for durable state. Do not run `docker compose down -v` in deployment or rollback paths.

## Transition

| State | Action | Exit condition |
|---|---|---|
| Checkout | `checkout scm` at `main` | Workspace commit is known |
| Capture | Read the running application container image tag into optional `PREV_TAG` before build | Missing tag is a greenfield state; an inconsistent running tag stops the job |
| Build | Set `IMAGE_TAG` to the checked-out commit SHA and build once | The resulting digest is recorded for every subsequent service |
| Database ready | Start only database dependencies with `--wait --wait-timeout` | Health checks report ready |
| Migrate | Run the migration deploy service using the built digest | Migration exits successfully |
| Roll out | `up -d --no-build --wait` for application services | Compose health checks report ready |
| Smoke | Exercise the deployed service through its intended smoke endpoint | Expected response succeeds |
| Complete | Mark the release successful | All prior states passed |

Do not rebuild after migration or before application startup. Rebuilding turns a commit identifier into multiple possible images and makes rollback evidence unreliable.

## Failure and recovery

On failure after runtime state may have changed, capture `docker compose ps` and relevant `docker compose logs` best-effort before recovery. Preserve that evidence even when the capture command itself fails.

When `PREV_TAG` exists, switch the application services back to that tag and wait for readiness, without deleting volumes. When there is no prior tag, this is a greenfield failure: do not automatically roll back or tear down state. Report the evidence and require a manual recovery decision because no known-good image exists.

## Compose shape

Pass `IMAGE_TAG` to every service that uses the application image, including the migration deploy service. Keep database startup separate from application rollout so migrations never race a database that has not become healthy. `--no-build` on rollout enforces use of the image already built for the captured SHA.
