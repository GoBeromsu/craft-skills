---
name: cicd
description: "Designs CI/CD so pull requests receive inexpensive, reliable feedback and deployment servers own image build and release state. Use when configuring CI/CD 구성, doing 배포 파이프라인 설계, asking to set up CI/CD, defining a deployment pipeline, adding GitHub Actions checks, or writing a Jenkins Docker deployment. Not for application architecture or persistence choices — use backend; not for UI rendering or client state — use frontend; not for commit history or PR mechanics — use git; not for test-suite design — use testing."
metadata:
  version: 1.0.0
---

# cicd

Make every change cheap to validate and every deployment reversible from evidence. A pipeline is complete when PR checks run without cost-heavy image builds, the required check cannot deadlock on changed paths, and a failed release either returns to its known previous image or leaves a greenfield system intact for manual recovery.

## Ownership boundary

Use GitHub Actions for lint, typecheck, test, and application build only. Do not build Docker images there: the deployment server's Jenkins job owns Docker build and deployment, using its local build context rather than a registry.

Keep the split explicit:

| Surface | Owns | Does not own |
|---|---|---|
| GitHub Actions | Fast PR validation and one stable required check | Docker image build, release, server mutation |
| Jenkins on the deployment server | Docker build, migrations, rollout, rollback | PR-required status |

## CI gate

Trigger the workflow for every pull request. Do not put `paths` filters on the workflow event because skipped workflows leave required checks pending. Instead, use an internal path gate that exits successfully when no relevant application path changed; a change under `.github/workflows/**` always selects the full check path.

Expose one job with the fixed required-check name. Put path selection and all lightweight checks beneath that job so branch protection never depends on conditionally absent job names. Load [ci-gating.md](references/ci-gating.md) before editing a workflow.

Run the project-native lint, typecheck, tests, and application build in that order. Fail on the first broken command; do not turn a failed check into a warning-only result.

## Deployment gate

Use a Jenkins job restricted to `main`, with `disableConcurrentBuilds()` and a fixed `COMPOSE_PROJECT_NAME`. Validate deployment inputs with Compose fail-closed substitutions such as `${DATABASE_URL:?required}` before changing runtime state. Preserve named volumes; never use `down -v` in this pipeline.

Follow this state transition exactly:

1. Check out Jenkins SCM at `main`.
2. Capture the running container's tag as optional `PREV_TAG` before building, and stop if observed runtime state is inconsistent.
3. Build once with `IMAGE_TAG` equal to the commit SHA; reuse that image digest for migration and application services.
4. Start the database dependencies with `--wait --wait-timeout`, then run migrations as a one-shot deploy service.
5. Roll out with `up -d --no-build --wait`, then run a smoke check.
6. On failure, retain `ps` and logs best-effort. Roll back only when `PREV_TAG` exists; on a greenfield deployment, preserve evidence and require manual recovery.

Read [pipeline-safety.md](references/pipeline-safety.md) before creating or changing the Jenkinsfile or Compose deployment services.

## Verification

- [ ] The PR workflow has no event-level `paths` filter and includes `.github/workflows/**` in its internal full-check condition.
- [ ] The same fixed job name reports success for both no-op and full-check PR paths.
- [ ] GitHub Actions runs no Docker build or registry push.
- [ ] Jenkins builds exactly one SHA-tagged image and migration plus application services use it.
- [ ] Database readiness, migration completion, application readiness, and smoke success precede release success.
- [ ] Failure output retains container state and logs; rollback occurs only from an observed `PREV_TAG`.

## Boundaries

Route service decomposition, APIs, persistence, and migrations' application semantics to `backend`. Route test selection and fixture strategy to `testing`; this skill only sequences the commands that already prove the service. Route commits, branches, and pull-request operations to `git`.
