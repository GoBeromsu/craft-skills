# Phase 3 — Reconcile Proposed Lifecycle State

Reconcile computes the complete proposed AGENTS lifecycle state before an effect path can run.
It owns map and prune proposal formation; it does not own project discovery or post-apply verification.
The public route normalizes omitted operation and explicit `map` to the same `map` request before flag validation, preflight, proposal calculation, journal inspection, or effects.
`audit` and `prune` remain explicit operations.

## Table of Contents

- [Pure proposed-state pipeline](#pure-proposed-state-pipeline)
- [Canonical content and managed regions](#canonical-content-and-managed-regions)
- [Proposal and acceptance boundary](#proposal-and-acceptance-boundary)
- [Audit isolation](#audit-isolation)
- [Map and prune effect boundary](#map-and-prune-effect-boundary)
- [Transaction and snapshot handoff](#transaction-and-snapshot-handoff)

---

## Pure proposed-state pipeline

Run this deterministic pipeline with no repository mutation:

1. Normalize invocation: no operation token and `map` both become `operation: "map"`; reject invalid, duplicate, legacy, and cross-operation flags before creating a temp or journal.
2. Read and validate the repository state, prior snapshot, active journal, paths, file types, UTF-8/LF content, modes, existing instructions, coverage inventory, loader evidence, and shim policy. An invalid or unsafe input is a block, not a repair opportunity.
3. Compute complete first-party coverage independently of `max_depth`. Depth `1..32` limits only scoring and placement; it cannot omit a target or ancestor instruction chain.
4. Compute desired topology, root fallback, candidate placements, rendered AGENTS payloads, managed-region changes, exact shim changes, ownership changes, stale ownership, findings, and proposal actions from the validated observations.
5. Bind each mutation to raw pre/post bytes, existence, `S_IMODE` values, normalized path, and ordered action. Compute the transaction basis and its acyclic ID before deriving artifact names.
6. Emit one proposed state: clean/no-op, blocked with stable diagnostics, or an acceptance-gated map/prune transaction request. The result is pure data and is the sole input to effects.

Do not derive another proposal during application.
Re-read observations only to prove that the proposal's bound evidence is still current; changed evidence invalidates acceptance and blocks.

## Canonical content and managed regions

`AGENTS.md` is the canonical instruction source.
A substantive `CLAUDE.md` is never co-canonical.
The only allowed native adapter is a sibling regular file whose bytes are exactly `b"@AGENTS.md\n"`; this is a ten-character ASCII reference plus one LF, and its hash is the hash of those eleven bytes.
Any other CLAUDE content is user-owned and requires the applicable accepted consolidation proposal before replacement.

A shim policy is always one of `keep`, `on`, or `off`:

- `keep` resolves to the last valid snapshot policy, otherwise `off`.
- `on` proposes the exact shim only where AGENTS is canonical and a safe sibling shim can exist.
- `off` proposes removal only for an owned exact shim; it never deletes substantive user content.

Managed payloads use the state-contract marker grammar.
Reconciliation replaces or removes only a validated managed region that is owned by the snapshot and whose observed bytes and hash bind to the proposal.
It must not overwrite an unmanaged `AGENTS.md`, adopt a partial marker, normalize user text, follow a symlink, or treat a matching filename as ownership.

New AGENTS, exact shims, and snapshots use mode `0644` (decimal 420).
Existing regular-file modes are preserved exactly as `S_IMODE` in the range `0..4095`; unsupported mode read, set, or verify behavior blocks before journal creation.

## Proposal and acceptance boundary

A proposal is required for every user-owned ambiguity or destructive change.
Its stable ID binds operation, target identity, observed evidence, requested action, and the proposed result.
Accepted IDs are supplied only through repeated `--accept=ID`; rerunning, matching a path, or accepting a prior ID after evidence changes is never consent.

Ordinary actions are exactly:

- `adopt-exact-shim`
- `restore-managed-payload`
- `adopt-managed-payload`
- `merge-claude-and-replace-shim`
- `remove-stale-region`
- `remove-stale-file`
- `remove-stale-shim`

Recovery actions are exactly `recover-rollback-transaction` and `recover-complete-transaction`.
They bind the journal hash and ID, observed target and snapshot hashes/modes, and selected immutable recovery images.
Unknown action IDs, duplicate conflicts, missing acceptance, or changed evidence block without effects.

Map preserves stale ownership in the snapshot; it may report and propose but must not delete stale content merely because the current desired topology omits it.
Prune is the only deletion path and fails closed: it starts with no deletion accepted, permits only accepted stale artifacts whose ownership, marker/hash, path, regular-file type, and preimage remain valid, and blocks rather than rebasing unrelated observation into ownership.

## Audit isolation

Audit runs the same read/validate/classify computations needed for findings, but is structurally read-only.
Its module must not import the apply or transaction-effect module and has no code path that can create, chmod, rename, unlink, fsync, or clean target or transaction artifacts.
It may write JSON only to stdout and may use temporary state only outside the inspected repository.

Audit inventories a journal and reports it as a finding; it never resolves, cleans, creates, updates, or overwrites a journal.
It reports exit 0 when clean, 1 when findings exist (including an active journal), and 2 when safe inspection is impossible.
Audit never emits an executable effects plan as an implicit side effect.

## Map and prune effect boundary

Only `map` and `prune` may invoke the package-private transaction helper.
They consume the one pure proposed-state result after acceptance and preflight revalidation.
No bare-init effects adapter exists: bare init and `init map` share the same normalized request, proposals, transaction basis, effects, report, diagnostics, and exit class.

Effects may mutate only the proposal's validated managed products, exact owned shims, snapshot, and bounded same-transaction artifacts.
They must not glob for cleanup, discover new targets, change desired state, modify unowned content, or turn a failed revalidation into adoption.
An existing valid journal is resolved first; an invalid journal is preserved and blocks ordinary work.

## Transaction and snapshot handoff

The pure result supplies `operation`, ordered `products`, and `snapshot`.
Each target binds `path`, `action`, `pre_exists`, `pre_sha256`, `pre_mode`, `post_exists`, `post_sha256`, and `post_mode`; the transaction layer adds only derived recovery/apply paths and state.
State details, identity, artifact modes, restart classification, and durability order are normative in [state-contract.md](state-contract.md).

Map/prune effects create a bounded journal before product mutation and commit the snapshot last.
A successful completion verifies every bound target and snapshot, then removes only validated same-transaction artifacts and the fixed journal last.
A proposal block, invalid journal, unsafe path, unsupported mode, or failed evidence check creates no target temporary file or journal.
