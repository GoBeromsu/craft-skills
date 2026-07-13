---
name: cicd
description: "Designs CI/CD changes that preserve the repository's delivery topology and make releases observable and reversible. Use when asked to set up the PR pipeline and deployment for this repo, configure CI/CD, add a deployment pipeline, define required CI checks, design release rollback, or 배포 파이프라인을 설계할 때. Not for service architecture or persistence — use backend; test-suite design — use testing; or commit and PR mechanics — use git."
metadata:
  version: 1.1.1
---

# cicd

Design delivery changes from repository evidence, not a preferred stack. A pipeline is complete when it preserves the selected topology, gives cheap PR feedback, rejects invalid release inputs, retains evidence, and has a reversible recovery path.

## Incumbent topology gate

Before editing workflows or deployment files, identify the CI provider and required-check names, image distribution path, orchestrator and deployment target, immutable release resolver, and the owner that performs deployment. Inspect existing configuration, branch protection or equivalent policy, runtime manifests, and recent successful release evidence. Preserve those incumbents unless the task explicitly migrates them.

For a greenfield repository, select and document those five topology decisions before writing pipeline files. Keep stable required checks available for every PR when the hosting provider supports them; make their no-op and full-check paths observable. Fail closed on release inputs, retain build and runtime evidence, and use a recovery action that does not destroy durable state.

## Selected-topology recipes

Use [ci-gating.md](references/ci-gating.md) only when the selected CI provider is GitHub Actions and a required PR check is in scope. Use [pipeline-safety.md](references/pipeline-safety.md) only when the selected topology is Jenkins on the deployment server with local Docker Compose builds and no registry. Do not transfer either recipe's provider or runtime specifics to another topology.

## Verification

- [ ] Evidence records the incumbent or newly selected CI provider, image path, orchestrator, deployment target, and deployment owner.
- [ ] PR feedback is cheap, and any required check remains stable across both selected paths.
- [ ] A documentation-only change demonstrates the visible no-op path; a workflow or pipeline change demonstrates the full-check path.
- [ ] Missing or malformed release inputs fail before runtime mutation, and build or runtime evidence is retained.
- [ ] An exact release input resolves to a recorded commit SHA rather than a moving branch.
- [ ] Exercise failures before and after migration; automatic application rollback after migration is enabled only with compatibility proof, and the manual-recovery path preserves durable state.

## Anti-patterns

- Replacing an incumbent tag, release, or immutable commit resolver with `checkout main` → preserve the repository's release semantics and deploy the exact resolved SHA in detached state.
- Automatically switching to `PREV_TAG` after a migration succeeds but health or smoke checks fail → capture evidence and fail stopped unless no schema change or backward compatibility was proven before deployment; code rollback is not database recovery.

## Boundaries

Route service decomposition, public HTTP API contracts, persistence, and migration semantics to `api` or `backend` as appropriate. Route test selection and fixture strategy to `testing`; this skill sequences existing proof commands. Route commits, branches, and pull-request operations to `git`.
