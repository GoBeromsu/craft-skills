# Release cutover

Turning a verified commit into a named, reproducible artefact, getting that exact artefact running, and proving from durable evidence that it is what runs.
A release is not real because a tag exists; it is real once the live stack resolves to the released digest.

## Contents

- [The shape](#the-shape)
- [Cut the release](#cut-the-release)
- [Swap the live stack](#swap-the-live-stack)
- [Measure the deployed result](#measure-the-deployed-result)
- [Pitfalls](#pitfalls)
- [Verification](#verification)

## The shape

```
push tag <product>-v<semver>
        │
        ▼
  guard job: tag == version in EVERY version carrier   ──fail──▶ prints each carrier + value
        │ pass
        ▼
  workflow creates the release (non-prerelease)
        │
        ▼
  image workflow triggers on the release-published event
        │
        ▼
  images pushed, tagged by full commit SHA; digests in job outputs + artifact
        │
        ▼
  live stack redeployed by digest   ──▶ the release is real
```

## Cut the release

1. **Write the guard first.**
   Find every **version carrier** by grep; never assume there is one.
   A package manifest and a front-end manifest each carrying `0.1.0` are two carriers.
   Beware look-alikes: a constant such as a database-format identity is not the product version and must never be bumped to match a tag.
   The guard reads each carrier, asserts the tag equals `<product>-v$VERSION` for all of them, and echoes tag and carrier for every one before failing.
   The point is that a mismatch is impossible to merge past, not that the check is clever.
2. **Provide a rehearsal path** — a manual dispatch with a rehearsal boolean defaulting to true that runs the whole pipeline and creates no release.
   Rehearse before the first real tag.
3. **The workflow creates the release, not a human.**
   Grant release-creation write permission on that job only, with the workflow default at read.
   A real release is not a prerelease: an image workflow conditioned on the release not being a prerelease publishes nothing for one.
4. **Let the release event do the publishing**, and keep the event-to-push mapping explicit:

   | Event | Pushes | Tags |
   |---|---|---|
   | pull request | never | none |
   | push to the default branch | yes | full SHA, plus a staging tag |
   | release published | yes | full SHA |
   | manual dispatch | yes | full SHA |

5. **Reference images by digest, never by tag.**
   A branch-or-staging tag is not a deployment reference.
   Take digests from the run's job outputs or its image-refs artifact — which is uploaded only by runs that actually pushed, because a digest that was never pushed cannot be pulled.
6. **Keep models and other large assets out of the images** and pin them as external artefacts instead.
   A manifest names each file, its upstream at a 40-hex revision, its size, and its checksum; a one-shot service fills a named volume on every start and the consumer starts only after it exits zero, so a bad pin holds the consumer back instead of loading an unverified asset.
   Changing an asset means changing the manifest inside the released commit, never editing the volume.

## Swap the live stack

7. **Record the pre-swap baseline before touching anything** — it is the evidence the swap is about to overwrite.
   Capture the image reference and image id, the data-volume mount source, the work-queue depth, the restart count, the start timestamp, the input-source count, and whatever domain counters exist.
   Save it outside the deployment tree.
8. **Swap one service at a time with the shell scrubbed.**
   Exported variables override an env file, so unset them explicitly for the call; on one cutover a polluted project name and image variables took the stack down twice.

   ```bash
   env -u COMPOSE_PROJECT_NAME -u CLIP_STORE_HOST_DIR -u ML_WORKER_IMAGE -u ML_API_IMAGE \
     docker compose --env-file "${ENV_FILE}" -f compose.yaml -f compose.gpu.yaml \
     -p "${PROJECT}" up -d --pull never --no-deps --force-recreate "${SERVICE}"
   ```

   Back up the env file before editing an image reference in it.
   After a restart, transient states are normal: an input-source count read 2 of 13 eight seconds after a restart and 13 of 13 a minute later, so wait before calling it an outage.
9. **Rollback rule.** Keep the previous released digest pullable, restore the env backup, and re-run the same command.
   Never bring the stack down with its volumes removed — the state volumes are the only copy.

## Measure the deployed result

A claim that a fix works is only as good as the preconditions pinned around it.
One prior measurement session was wrong seven times: it measured the wrong mount, counted a backlog drain as new events, and credited a fix for what a restart's flag reset had done.

1. Build from the branch that actually contains the fix, never from the base checkout; an earlier session shipped an image that silently reverted the branch's changes.
   Record the built image id, and require the source-revision build argument to be 40-hex lowercase so an empty value fails the build.
2. **Pin the preconditions immediately and record them verbatim:** the container's configured image and resolved image id; the mount source for the data directory, which must be the expected one — a wrong mount once measured a three-day-old directory as "0 items"; the work-queue backlog and dead-letter depth, since a draining backlog looks like new traffic; the restart count and start timestamp; and the input-source health.
3. **Watch the first minutes for storms.** One build produced 265 rebuilds per minute and was rolled back after four minutes with the same command and the previous tag.
   Rolling back is cheap; a storm left running is not.
4. **Window:** start at least 10 minutes after the start timestamp and run at least an hour, with interim counts about every 15 minutes so a regression shows early.
5. **Count from durable artefacts, not logs.** Successful operations frequently emit no log line at all, so absence in the log means nothing.
   Count the artefacts themselves, break the result down by reason code, and cross-check the failure subset against both the log and the service's own counter.
6. **Re-check the restart count at the end.** If it moved, the window is invalid — a restart resets in-memory state and masks the bug.

Report a table of window, new items, successful items, failures, ratio, threshold, and result, plus the reason breakdown, the log cross-check, and a final restart count of zero.
A worked result in this shape: a one-hour window, 314 of 314 items complete, zero warnings, zero restarts, an empty queue, and full input-source health, against a pre-fix store holding 3,405 incomplete records.

## Pitfalls

- **Running unmerged code in production is the default failure mode.**
  Before one such cutover the live stack ran two branch builds from unmerged pull requests, despite a runbook warning against exactly that, because a locally built tag is the path of least resistance.
  A release exists to make the pinned digest easier than a rebuild.
- **A tag is mutable; a digest is not.** Deployment references are digests, and a latest-or-branch tag or a hand-typed digest is refused.
- **Pruning too aggressively removes the rollback.** Keep at least the current and previous released digests locally and in the registry.
- **Version-carrier drift is silent** until the guard exists; that is why the guard fails the release rather than warning.
- **Branch protection can block the merge that precedes the tag.** Sequence the merges, then tag.
- **The first release has no previous tag**, so its notes are assembled by hand from the merge list; every later one can use the tag range.
- An agent that "waits for a notification" stops and never resumes; waiting has to be an active loop that ends in the final count.
- Load tests run against the same host during a measurement window distort it — do not run them then.

## Verification

- [ ] The guard job fails loudly on a deliberate carrier mismatch, exercised once.
- [ ] A rehearsal run creates no release.
- [ ] The release is not a prerelease, so the image workflow actually publishes.
- [ ] Digests came from job outputs or the refs artifact, not typed by hand.
- [ ] Live containers report the released image and digest — the only proof the system runs from the release rather than from someone's local build.
- [ ] The pre-swap baseline is saved and the previous digest is still pullable.
- [ ] No step brings the stack down with its volumes removed.
- [ ] Post-swap: restart count zero, expected mount, queue drained, inputs healthy, no tracebacks in a recent log window.
