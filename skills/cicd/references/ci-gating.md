# CI required-check gating

Keep branch protection observable even when a pull request does not touch application code. The required check is a stable interface: its workflow and job must exist for every PR.

## Pattern

Trigger on all pull requests. Calculate relevance inside the job, then choose either the no-op success path or the full validation path. Treat workflow changes as relevant so edits to the checker cannot bypass the checker.

| Changed path class | Internal gate | Result |
|---|---|---|
| Application, dependency, test, or build configuration | Full validation | lint → typecheck → test → application build |
| `.github/workflows/**` | Full validation | Same full validation; protects the workflow itself |
| Documentation-only or unrelated paths | No-op | The fixed required job exits 0 with an explicit reason |

Do not use event-level `paths` or `paths-ignore` when this workflow's job is required. GitHub does not create a skipped workflow run, which leaves branch protection waiting for a status that cannot arrive.

## Fixed status contract

Set one job identifier and display name for the branch-protection requirement, for example `pr-validate`. Do not make that job conditional. Place conditional steps inside it, or make it a non-conditional aggregator whose selected child path always reports into the same job.

When branch protection already names a check, preserve that name. Renaming it is a coordinated repository-policy change, not a workflow cleanup.

## Selection implementation

Use the repository's existing changed-file mechanism. It must compare the PR base and head, emit one boolean output, and match `.github/workflows/**` before any no-op decision. Keep the no-op path visible in logs, but do not invoke lint, test, build, Docker, or external deployment work from it.

Validate the two observable cases after changing the gate:

1. A docs-only PR produces the fixed required job and a successful no-op.
2. A workflow-file PR produces the same job and runs every lightweight check.
