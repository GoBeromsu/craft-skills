# Jenkins-on-server Docker Compose recipe

Use this recipe only when the selected topology is Jenkins running on the deployment server, building local Docker images for Docker Compose without a registry. It is not a general CI/CD default.

## Preconditions

- Restrict the job checkout to `main` and use Jenkins SCM checkout, not an arbitrary user-supplied ref.
- Disable concurrent builds so two jobs cannot overwrite each other's runtime state.
- Set one fixed `COMPOSE_PROJECT_NAME` so inspection and cleanup address the intended stack.
- Require Compose inputs at interpolation time, such as `${DATABASE_URL:?required}`. An absent value stops the release instead of silently selecting a default.
- Use named volumes for durable state. Do not run `docker compose down -v` in deployment or rollback paths.

## Transition

| State | Action | Exit condition |
|---|---|---|
| Checkout | `checkout scm` at `main` | Workspace commit is known |
| Capture | Read the running application container image tag into optional `PREV_TAG` before build | Missing tag is greenfield; an inconsistent running tag stops the job |
| Build | Set `IMAGE_TAG` to the checked-out commit SHA and build each application image once | Every application image has the same SHA tag and its digest is recorded |
| Database ready | Start only database dependencies with `--wait --wait-timeout` | Health checks report ready |
| Migrate | Run the migration deploy service with the recorded backend image digest | Migration exits successfully |
| Roll out | `up -d --no-build --wait` for the full application stack | Compose health checks report ready |
| Smoke | Exercise the deployed service through its intended smoke endpoint | Expected response succeeds |
| Complete | Mark the release successful | All prior states passed |

Do not rebuild an application image after its SHA build, migration, or before application startup. Build each application image once per SHA, tag every image with that SHA, and preserve the recorded backend digest for migrations.

## Failure and recovery

On failure after runtime state may have changed, capture `docker compose ps` and relevant `docker compose logs` best-effort before recovery. Preserve that evidence even when capture itself fails.

When `PREV_TAG` exists, switch application services back to that tag and wait for readiness without deleting volumes. When there is no prior tag, this is a greenfield failure: do not automatically roll back or tear down state. Report the evidence and require a manual recovery decision because no known-good image exists.
