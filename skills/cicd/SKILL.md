---
name: cicd
description: "Designs CI/CD changes that preserve the repository's delivery topology and make releases observable and reversible. Use when asked to set up the PR pipeline and deployment for this repo, configure CI/CD, add a deployment pipeline, define required CI checks, design release rollback, or 배포 파이프라인을 설계할 때. Not for service architecture or persistence — use backend; test-suite design — use testing; or commit and PR mechanics — use git."
metadata:
  version: 1.4.0
---

# cicd

Design delivery changes from repository evidence, not a preferred stack. A pipeline is complete when it preserves the selected topology, gives cheap PR feedback, rejects invalid release inputs, retains evidence, and has a reversible recovery path.

## Incumbent topology gate

Before editing workflows or deployment files, identify the CI provider and required-check names, image distribution path, orchestrator and deployment target, immutable release resolver, and the owner that performs deployment. Inspect existing configuration, branch protection or equivalent policy, runtime manifests, and recent successful release evidence. Preserve those incumbents unless the task explicitly migrates them.

For mutable CI-provider, deployment-platform, orchestrator, or runtime facts, consult official primary docs first and disclose conflicts; only more-specific repo-local contracts or matching-version/platform reproducible evidence may override general or stale docs. Otherwise the fact is unknown: do not invent behavior.

For a greenfield repository, select and document those five topology decisions before writing pipeline files. Keep stable required checks available for every PR when the hosting provider supports them; make their no-op and full-check paths observable. Fail closed on release inputs, retain build and runtime evidence, and use a recovery action that does not destroy durable state.

## Selected-topology recipes

Use [ci-gating.md](references/ci-gating.md) only when the selected CI provider is GitHub Actions and a required PR check is in scope. Use [pipeline-safety.md](references/pipeline-safety.md) only when the selected topology is Jenkins on the deployment server with local Docker Compose builds and no registry. Do not transfer either recipe's provider or runtime specifics to another topology.

Use [run-economics.md](references/run-economics.md) when a pipeline is too slow, or when splitting, sharding, or adding a required check — it owns measure-before-optimising, duplicate-run removal, shard exact-cover assertions, the aggregate gate job, and moving branch-protection contexts in the same change. Use [release-cutover.md](references/release-cutover.md) when cutting a tagged release, swapping the running artefact, or proving from durable evidence that the live stack runs the released digest. Fork-trust, action pinning, workflow permissions, and policy mutation tests belong to `security`; this skill sequences the pipeline those rules constrain.

## Verification

- [ ] Evidence records the incumbent or newly selected CI provider, image path, orchestrator, deployment target, and deployment owner.
- [ ] PR feedback is cheap, and any required check remains stable across both selected paths.
- [ ] A documentation-only change demonstrates the visible no-op path; a workflow or pipeline change demonstrates the full-check path.
- [ ] Missing or malformed release inputs fail before runtime mutation, and build or runtime evidence is retained.
- [ ] An exact release input resolves to a recorded commit SHA rather than a moving branch.
- [ ] Exercise failures before and after migration; automatic application rollback after migration is enabled only with compatibility proof, and the manual-recovery path preserves durable state.
- [ ] A deploy-time CI gate asserts the exact release SHA's job-level conclusion — filtered to the CI workflow's own triggering event — rather than re-running proof commands or trusting commit ancestry alone.
- [ ] Per-step timing was captured before any speed change, and each pull request produces one run rather than two.
- [ ] Every version carrier agrees with the release tag through a guard that fails the release, and the deployment reference is a digest rather than a tag.
- [ ] A post-swap measurement pinned its preconditions, counted from durable artefacts rather than logs, and ended with the restart count unchanged.

## Anti-patterns

- Replacing an incumbent tag, release, or immutable commit resolver with `checkout main` → preserve the repository's release semantics and deploy the exact resolved SHA in detached state.
- Automatically switching to `PREV_TAG` after a migration succeeds but health or smoke checks fail → capture evidence and fail stopped unless no schema change or backward compatibility was proven before deployment; code rollback is not database recovery.
- Re-running lint, test, or build inside the deployment pipeline for a commit the CI provider already validated → assert the CI provider's already-recorded conclusion for that exact commit instead; deployment confirms release readiness, it does not re-prove code correctness.
- Trusting `git merge-base --is-ancestor` to prove a release commit passed CI → assert the CI conclusion of the exact release SHA; ancestry only proves lineage, and a commit merged before its required check finished is still an ancestor.
- A second, comment-declared "merge-ready" or "accept" signal running alongside the required check → assert mergeability only from the required check's actual state, and route access control to platform features (ruleset, environment protection, collaborator permissions) instead of a parallel truth source.
- Removing deployment-time re-verification before a new exact-SHA CI gate has proven itself against a real release → land the gate, exercise it against an actual deployment, then remove the redundant check; the reverse order leaves a window where neither layer verifies.
- Adding a date cutoff or bypass switch so pre-existing releases pass a newly fail-closed gate → cut a new release that satisfies the gate instead; the exception outlives the reason for it and the gate around it gets forgotten.
- Caching dependencies first because the pipeline is slow → attribute wall-clock per step from a real run first; the dominant cost is usually the test suite, and a cache on a fork-triggered workflow buys seconds while opening a supply-chain path.
- Adding a path filter to a required check so unrelated changes skip it → a required check that never reports blocks the pull request forever; use path filters only on non-required workflows.
- Splitting or renaming jobs without moving the branch-protection contexts in the same change → required contexts are job names, so the default branch silently loses its gate.
- Sharding a suite on a file glob that does not mirror the runner's own collection defaults → assert the partition as an exact cover with a test that executes the workflow's own pipeline; files in no shard leave the gate green and untested.
- Deploying a locally built or branch-built image because it is at hand → deploy the released digest; running unmerged code in production is the default failure mode a release exists to prevent.
- Calling a fix proven from a live log because no failures appear → count durable artefacts over a pinned window; successful operations often emit no log line, and a restart mid-window invalidates the count.

## Boundaries

Route service decomposition, public HTTP API contracts, persistence, and migration semantics to `api` or `backend` as appropriate. Route test selection and fixture strategy to `testing`; this skill sequences existing proof commands. Route commits, branches, and pull-request operations to `git`.
