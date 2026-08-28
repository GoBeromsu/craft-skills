# Untrusted CI

A continuous-integration workflow triggered by a pull request executes code the fork author wrote, on this repository's runner, with this repository's cache and token.
Everything that workflow *writes* — a cache entry, an image tag, an artifact, a digest — can be read by a later trusted run on the default branch, so every write path is a supply-chain path.
This reference owns the rules for that boundary and the mutation tests that keep them from decaying into decoration.

## Contents

- [Rules](#rules)
- [Prove every policy bites](#prove-every-policy-bites)
- [Pitfalls](#pitfalls)
- [Verification](#verification)

## Rules

1. **No dependency cache on a pull-request-triggered workflow.**
   A fork can poison a cache key that a later trusted run restores.
   This contradicts the generic "cache dependencies first" advice on purpose: when the economics were measured, dependency sync was 21 s and the model fetch 1 s of a 19m37s job, so a cache was worth under 30 s against a permanent fork-write path into trusted runs.
   Measure the saving before accepting the trade; never accept it by default.
2. **Pin every action reference to a 40-hex commit SHA.**
   A tag is mutable and repointable by the upstream action owner at any time.
3. **Grant `contents: read` at workflow level**, and write only on the single job that needs it.
   A `permissions:` block accepts no expression, so a grant cannot be narrowed by event — the narrowing has to happen at the token's consumers instead (rule 4).
4. **Never gate a required job behind a job-level `if:` — a skipped required check reports success to branch protection.**
   Put the gating on the token's *consumers* inside the job: registry login, image push, cache export, artifact upload.
   Drive them from one env flag such as `PUSH_IMAGES: ${{ github.event_name != 'pull_request' }}`, and assert both the flag and each consumer in a test — including a **count**, so a gate cannot be "fixed" by deleting the step it guards.
5. **Do not interpolate `${{ }}` into a `run:` body** — untrusted or trusted alike.
   Pass the value through `env:` and reference `$VAR`.
   A matrix value inlined into a shell script is the canonical template-injection shape, and it is the version people copy.
6. **Give every job an explicit timeout.**
   The platform default is 360 minutes, so a hung fork pull request burns six hours times the shard count of the runner budget.
7. **Publish artifacts and digests only from runs that actually pushed.**
   A digest that was never pushed cannot be pulled, and publishing one from a pull-request run invites someone to deploy a fork's build.

A dependency resolved at CI time inside an untrusted workflow is itself a supply-chain surface.
This is why a test sharder is safer written as a dependency-free round-robin over sorted tracked files than as an installed splitting plugin.

## Prove every policy bites

A policy with no failing case is a comment.
For a workflow allowlist, a shard cover, or SHA pinning, add mutation tests that fail when the property is removed:

- an unpinned tag in an action reference.
- a non-hex ref.
- an ungated cache export.
- a widened `permissions:` value.
- a dropped gating step, caught by the count assertion.
- an extra job appearing in the workflow.
- an injected `${{ secrets.` inside a `run:` block.

For a new lint or boundary rule, introduce a deliberate violation once, capture the failure output with the rule name, then revert.
Adding a policy test with no mutation case produces a green suite that proves nothing: when this discipline was applied to one repository, the policy suite grew from 79 assertions to 96 and then by 23 more for an image workflow, and every addition arrived with its violation case.

## Pitfalls

- **A security policy test can pin the whole workflow.**
  One such test asserted the exact job set, the exact ordered steps, the exact trigger shape, and the exact top-level key set — so a job split, a concurrency block, and a duplicate-run fix were all rejected until its allowlist was deliberately extended, keeping every guarantee but expressing it per job.
  Read the policy test before designing the change, and do not delete an assertion to make room.
- **Escalate a policy conflict instead of resolving it alone.**
  A cache ban whose rationale is written into its commit message is a recorded decision, not a stale pin; it goes back to the owner rather than being quietly relaxed.
- A count that lives in a commit message rots.
  Put the assertion count in a test, not in prose.

## Verification

- [ ] Every action reference is a 40-hex SHA, and `contents: read` is the workflow default.
- [ ] No dependency cache is restored or exported on any pull-request-triggered workflow.
- [ ] No required job carries a job-level `if:`; each token consumer is gated individually and asserted with a count.
- [ ] No `${{ }}` appears inside any `run:` body.
- [ ] Every job declares a timeout.
- [ ] Each policy has a mutation test that fails when the property is violated, and the policy count is asserted rather than narrated.
- [ ] The workflow linter exits zero on every workflow file.
