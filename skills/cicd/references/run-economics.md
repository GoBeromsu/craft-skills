# Run economics

How to make a pipeline faster without losing the gate.
Every rule here is a correction to generic advice that measurement contradicted; the measurements are kept so the reasoning can be re-derived rather than trusted.

## Contents

- [What measurement changes about the generic advice](#what-measurement-changes-about-the-generic-advice)
- [Ordered steps](#ordered-steps)
- [Pitfalls](#pitfalls)
- [Verification](#verification)

## What measurement changes about the generic advice

| Generic advice | What measurement showed |
|---|---|
| "Slow pipeline? Cache dependencies first." | Dependency sync was 21 s and the model fetch 1 s of a 19m37s job; the test suite was 18m27s, or 94 %. Cache-first optimises the wrong 3 %. |
| Cache with the platform's cache action | On a pull-request-triggered workflow the cache is a fork-write supply-chain path into later trusted runs. Owned by `security`'s untrusted-CI reference. |
| Trigger on both push and pull request | That runs every pull request twice. Fixing it alone halved the bill before any parallelism. |
| Use path filters to skip unrelated jobs | A path filter on a **required** check means it never reports, so the pull request is blocked forever. Only safe on non-required workflows. |
| Split into parallel jobs | Correct — but branch protection's required contexts are job names. Split without updating them and the default branch silently loses its gate. |

## Ordered steps

0. **Read the security policy test before designing anything.**
   A policy test can pin the exact job set, ordered steps, trigger shape, and top-level key set, and will reject a job split, a concurrency block, and a duplicate-run fix until its allowlist is deliberately extended.
   Skipping this step means designing the whole change twice.
   Rules for extending it live in `security`'s untrusted-CI reference.

1. **Measure first, per step, from a real run.**
   Pull the run log and attribute wall-clock per step before touching anything.
   Also count *runs per pull request* — duplicates are invisible inside a single run's timing.

2. **Kill duplicate runs.**
   A bare push trigger alongside a pull-request trigger fires twice for every same-repository branch:

   ```yaml
   on:
     push: { branches: [main] }
     pull_request:
   concurrency:
     group: ci-${{ github.workflow }}-${{ github.ref }}
     cancel-in-progress: ${{ github.event_name == 'pull_request' }}
   ```

   A pull request's ref is its own merge ref, so it can never cancel the default-branch run; gate `cancel-in-progress` on the event anyway, explicitly.

3. **Split into independent jobs** — secrets scan, lint, test, gate — and give each only what it needs.
   A lint job needs neither media codecs, nor system packages, nor a model fetch.
   Measured after the split: secrets 10 s, lint 44 s.

4. **Shard the slow job only after establishing two invariants.**
   - *Stable test ids across processes.* A distributed-execution plugin aborted in about 5 s with `Different tests were collected between gw0 and gw1`, root-caused to a `uuid4()` call inside a parametrize decorator; a splitting plugin needs the same stable ids. A dependency-free round-robin over sorted tracked files sidesteps this, because each shard is its own process and cross-process id agreement is moot.
   - *An asserted exact cover.* A glob of `tests/test_*.py` silently drops `*_test.py` and nested directories that the runner's own defaults **do** collect; those files then run in no shard while the gate stays green. Mirror the runner's globs, and add a test that recomputes the partition from the tracked tree **and executes the workflow's own shell pipeline**, so shell and model cannot drift.

   Measured: serial 802.93 s became shards of 146/265/323/188 s on four cores with identical counts (3977 passed, 9 skipped, 43 deselected); on the hosted runner 1107 s became 374 s.

5. **Add one aggregate gate job** so branch protection has a single stable context:

   ```yaml
   ci-ok:
     needs: [secrets, lint, test]
     if: always()
     steps: [ run: for r in ...; do [ "$r" != "success" ] && failed=1; done; exit $failed ]
   ```

   Compare against the literal `success`, so `failure`, `skipped`, `cancelled`, and an empty result all fail.
   Set the matrix to not fail fast, so one bad shard reports a failure rather than a cancellation.

6. **Update branch protection in the same change.**
   Required contexts are job names, so renaming or splitting orphans them.
   Swap old for new and say so in the pull-request body — an administrator has to do it, and doing it in the wrong order either blocks every pull request or leaves the default branch ungated.

7. **Set a timeout on every job.**
   The platform default is 360 minutes.
   Values used after the split: secrets 10, lint 15, test 30, gate 5.

Result of applying all seven to one repository: 19m37s twice per pull request became 7m47s once.

## Pitfalls

- **Administrators may not bypass.**
  With admin enforcement on, an admin merge and the REST merge both return HTTP 405 while required checks are in progress.
  With strict mode on, every merge makes the other pull requests out of date and costs each another full cycle — plan the merge order, or batch.
- **A flake in a required check costs a full rerun cycle.**
  Sharding raises contention, so deadline-sensitive tests lose races more often.
  Assert the invariant, not which racer won.
- **Numbers in a commit message rot.**
  A recorded shard split of "104+103+103+103 = 413" was already 103 × 4 = 412 a day later.
  Put the count in a test, not in prose.
- **A lint script nobody runs is prose with extra steps.**
  Wire it into the workflow in the same change.

## Verification

- [ ] Per-step timing was captured *before* the change.
- [ ] One run per pull request; superseded pull-request runs cancel, and default-branch runs never do.
- [ ] Every job declares a timeout.
- [ ] Required contexts match the actual job names, and the aggregate gate fails on a skipped or cancelled dependency.
- [ ] The shard partition is asserted as an exact cover by a test that runs the workflow's own pipeline.
- [ ] `security`'s untrusted-CI checklist was run over the same diff.
