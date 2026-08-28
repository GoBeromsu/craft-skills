# Jenkins-on-server Docker Compose recipe

Use this recipe only when the selected topology is Jenkins running on the deployment server, building local Docker images for Docker Compose without a registry. It is not a general CI/CD default.

## Preconditions

- Preserve the incumbent immutable release resolver, such as a validated release tag mapped to a commit. Resolve the accepted release input to an exact commit SHA, record it, and use detached checkout; do not replace release semantics with a moving `main` checkout. A bounded greenfield pipeline may select a branch only when that topology is explicitly chosen and documented.
- Disable concurrent builds so two jobs cannot overwrite each other's runtime state.
- Set one fixed `COMPOSE_PROJECT_NAME` so inspection and cleanup address the intended stack.
- Require Compose inputs at interpolation time, such as `${DATABASE_URL:?required}`. An absent value stops the release instead of silently selecting a default.
- Use named volumes for durable state. Do not run `docker compose down -v` in deployment or rollback paths.

## CI status gate

When the incumbent or newly selected topology includes an upstream CI provider, assert that provider's already-recorded status for the exact release SHA before deployment touches runtime state. Do not re-run lint, test, or build inside the deployment pipeline for a commit the CI provider already validated — the deployment pipeline confirms release readiness, it does not re-prove code correctness.

- Query the CI provider for the run associated with the exact release SHA, filtered to the CI workflow's own triggering event, for example `event=push` on GitHub Actions. A workflow that also triggers on `issues` or `issue_comment` events stamps a same-named check run on the default branch head SHA for those triggers too, and that run's overall conclusion can read `success` while the relevant job never ran for the deploy-relevant event.
- Assert the specific job's conclusion inside that run, not the run-level conclusion. A run can report `success` while an individual job was skipped by an `if:` condition; job-level assertion catches a broken condition that a run-level check would miss.
- The workflow being asserted must not use `paths` or `paths-ignore` on its push trigger. A paths-filtered push run creates a false green by absence: a commit that only touches one application merges and deploys without validating the others. Reserve `paths` filters for pull-request-triggered workflows, where a skipped run is visibly skipped rather than silently green.
- Treat a missing run, an unresolved job, or any conclusion other than the asserted job's success as a stop condition, not a warning — the gate fails closed.

## Transition

| State | Action | Exit condition |
|---|---|---|
| Verify | Assert the exact release SHA's CI job conclusion per the CI status gate above | The asserted job's conclusion is success for that exact SHA |
| Checkout | Resolve the validated release input and detach at its exact commit SHA | Workspace commit equals the recorded release SHA |
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

Before migrations run, switching application services to a known-good prior image may be an automatic recovery path when runtime state is unchanged. After a migration succeeds, the default is to capture evidence, fail stopped, and require an explicit manual recovery decision.

Automatic application rollback after migration is allowed only when the release was pre-classified as having no schema change or backward compatibility between the migrated schema and prior application was proven and recorded. A code rollback is not database recovery: switching to `PREV_TAG` neither reverses schema/data changes nor proves the prior application can read them. Never delete volumes or improvise reverse migrations during automated recovery.

When there is no prior tag, report a greenfield failure with the retained evidence and require a manual recovery decision because no known-good image exists.
