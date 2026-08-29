# Phase 4 — Verify Lifecycle State

Verify proves that a proposed or applied lifecycle state is specific to this repository, complete, owned, loadable where evidence permits, and accounted for without hidden mutation.
It does not repair drift or create artifacts.
Transaction mechanics are defined in [state-contract.md](state-contract.md).

## Table of Contents

- [Verification inputs and invariants](#verification-inputs-and-invariants)
- [Project-specific AGENTS quality](#project-specific-agents-quality)
- [Schema ownership and hashes](#schema-ownership-and-hashes)
- [Coverage and loader evidence](#coverage-and-loader-evidence)
- [Mutation accounting and reports](#mutation-accounting-and-reports)
- [Operation-specific outcomes](#operation-specific-outcomes)

---

## Verification inputs and invariants

Verify consumes only the normalized operation, pure proposed state, observed filesystem state, valid snapshot/journal data, and the transaction receipt when effects ran.
It rechecks raw bytes, regular-file type, containment, normalized paths, modes, markers, hashes, and evidence binding.
It never treats a semantic approximation, rendered similarity, filename match, or a rerun as proof.

The root fallback is exact: before working on a path, read every `AGENTS.md` from repository root through that path's directory in order; the nearest file wins on conflict.
Fallback presence does not turn unknown loader behavior into covered behavior.

A clean result means every required invariant below is observed.
An unreadable, truncated, symlinked, special, escaped, malformed, or otherwise unsafe artifact is non-clean and receives a stable diagnostic.
Verification must preserve evidence rather than attempting a repair.

## Project-specific AGENTS quality

Each managed payload must be repository-specific: retain factual structure, entry points, conventions, commands, constraints, and non-obvious relationships established by discovery.
Reject generic advice that could describe arbitrary projects, invented claims, stale references, and instructions unsupported by the repository evidence.

Deduplicate a child against its parent chain.
A child may refine local ownership, commands, conventions, or exceptions; it must not repeat inherited content merely for completeness.
The nearest applicable AGENTS instruction wins, so conflicting duplicated guidance is a defect even when both claims are true.

Line budgets are enforced after deduplication: root `AGENTS.md` is 50–150 lines; each child is 30–80 lines.
A project too small to support the minimum must not receive padded generic prose; record the placement/quality finding and omit or revise the candidate according to the pure selection result.
The budget does not authorize omission of required project-specific evidence.

Verify UTF-8 and LF behavior required by the marker contract.
Do not silently rewrite user line endings or invalid text during verification.
Managed content may be compared byte-for-byte using its bound raw hash.

## Schema ownership and hashes

Validate the snapshot and transaction against their schemas before using any field.
The snapshot partitions owned artifacts from last-applied topology; desired topology is not evidence of current ownership.
For every owned artifact, validate normalized contained path, kind, raw hash, marker metadata where applicable, and recorded `S_IMODE` integer `0..4095`.

A managed region is owned only when its marker grammar, byte boundaries, raw hash, and snapshot record agree.
A full managed file is owned only when the recorded full-file identity agrees.
An exact CLAUDE shim is owned only when its raw bytes equal `b"@AGENTS.md\n"`, its hash is the corresponding eleven-byte hash, and snapshot ownership agrees.
Never infer ownership from the path, a marker-like substring, or current desired state.

Check preimage and postimage hashes and modes for every proposed mutation.
Before applying an accepted proposal, observed state must equal its preimage; after application, it must equal its postimage.
A mismatched hash, mode, existence bit, schema version, marker, or ownership partition invalidates the proposal and blocks instead of updating the snapshot.

## Coverage and loader evidence

Coverage is complete at arbitrary depth.
Inventory every non-excluded first-party regular-file target and every AGENTS file on its root-to-directory chain without following symlinks.
Unreadable, truncated, excluded-without-rule, or unclassified subtrees are visible non-clean findings.
The `max_depth` placement limit cannot hide coverage gaps.

Loader classification is evidence-based and independent of execution fan-out.
A package-local sentinel probe records root, child, and sibling startup/read observations, precedence, runtime version, fixture hash, and raw result.
Only an applicable probe with matching evidence persists a non-unknown loader class.
Source-only, conflicted, unavailable, version-mismatched, and non-automatable observations remain `unknown`.

Probe reports expose observable `root`, `child`, and `sibling` results.
They prove loader behavior only; they do not prove AGENTS quality, complete coverage, or transaction correctness.
Root fallback is separately verified from the instruction chain and never substitutes for probe evidence.

## Mutation accounting and reports

For map and prune, account for every proposed product and snapshot mutation before effects and every observed result after effects.
The deterministic transaction report includes `operation`, transaction identity/state where applicable, `effects`, proposals, stable diagnostics, and counters.
Each effect identifies its normalized path, action, expected/observed hashes and modes, and final disposition; the snapshot result is reported separately and is committed last.

For audit, emit JSON stdout with `findings` and `counters` plus observed state sufficient to explain each finding.
Audit accounting includes an active journal, ownership/hash/mode drift, coverage and loader gaps, exact-shim status, and unsafe inspection conditions.
It contains no effect list that can be executed, no mutation receipt, and no write-capable import path.

Counters must reconcile exactly with enumerated findings/effects: no unreported mutation, skipped target, duplicate target, or snapshot write is permitted.
A no-op map still reports its verified basis and zero target effects; it does not fabricate a transaction.
Prune must separately account for each stale candidate, rejection, accepted deletion, and preserved unowned artifact.

Diagnostics are stable identifiers with deterministic payload ordering.
Do not embed clocks, process IDs, temporary paths, or host-dependent prose in identifiers or acceptance evidence.
Report details may include bounded observed values needed to diagnose the result.

## Operation-specific outcomes

**Map.**
Bare `init` and `init map` must produce the same normalized request and observable result for equivalent repository state and flags: proposals, acceptance requirements, diagnostics, mutation basis, transaction identity, effects, target bytes/modes, snapshot, report, and exit class.
Verify journal-last cleanup and snapshot-last commit after an applied map.

**Audit.**
Verify audit has no target, transaction, or snapshot mutation and no imported effect path.
It exits 0 when clean, 1 with findings (including an active journal), and 2 when inspection cannot be performed safely.
It may report a defect but must not resolve it.

**Prune.**
Verify prune begins with no deletion accepted and fails closed.
Every deletion requires its matching accepted proposal plus current stale ownership, marker/hash, path/type, and preimage evidence.
It preserves unowned, ambiguous, mismatched, or unsafe content and reports why.
Its accepted effects use the same bounded transaction and snapshot-last rules as map.

**Failures and recovery.**
Usage, preflight, proposal, and recovery blocks exit 2 before target temps or a new journal.
Apply or recovery failures exit 3 while preserving evidence for deterministic restart.
Successful map/prune exits 0 only after complete poststate verification and journal-last cleanup.
Unexpected observations never become an implicit recovery or acceptance.
