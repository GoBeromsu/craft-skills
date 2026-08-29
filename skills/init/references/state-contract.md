# Init Lifecycle State Contract

This document is the normative byte- and filesystem-level contract for the AGENTS lifecycle.
Reconcile computes this state purely; only private map/prune effects may apply it.
Audit validates and reports it without importing an effect-capable module.

## Table of Contents

- [Paths, files, and canonical serialization](#paths-files-and-canonical-serialization)
- [Managed envelope and canonical shim](#managed-envelope-and-canonical-shim)
- [Snapshot ownership state](#snapshot-ownership-state)
- [Transaction identity and journal](#transaction-identity-and-journal)
- [Artifact roles and modes](#artifact-roles-and-modes)
- [Durable application order](#durable-application-order)
- [Restart, rollback, and cleanup](#restart-rollback-and-cleanup)
- [Stable diagnostics](#stable-diagnostics)

---

## Paths, files, and canonical serialization

All stored paths are normalized repository-relative POSIX paths.
They are non-empty, are never absolute, contain no backslash, NUL, `.` or `..` component, and resolve within the repository without following symlinks.
Before a path is read, written, renamed, or unlinked, verify its containment and regular-file type using no-follow operations.
Symlinks, special files, case ambiguity, path escape, unreadable data, and unsupported filesystem behavior are blocks.

Raw hashes are SHA-256 lowercase hexadecimal hashes of complete raw bytes.
Text content is UTF-8 with LF behavior preserved by the observed/prepared bytes; there is no semantic reformatting before hashing.
Hash comparisons are byte comparisons, not normalized-text comparisons.

The repository-root snapshot is `.agents-map.json`.
The only journal is the repository-root `.agents-map.transaction.json`.
Both names are fixed; neither is searched for by glob.
New AGENTS files, exact shims, and snapshots have mode `0644` (decimal 420).
Existing regular-file modes are recorded and preserved as `S_IMODE(st_mode)`, an integer from `0` through `4095`; inability to read, set, or verify such a mode blocks before journal creation.

Canonical identity serialization is compact, sorted-key UTF-8 JSON with no trailing LF.
Schema serialization must reject unknown fields where its schema specifies `additionalProperties: false`.
Array order is significant wherever this contract says ordered.

## Managed envelope and canonical shim

A managed region has exactly this paired envelope, with literal ASCII marker syntax:

```md
<!-- init:managed id=<ID> sha256=<64-lowercase-hex> -->
<payload>
<!-- /init:managed id=<ID> -->
```

`<ID>` is non-empty, unique within its file, and stable for the same managed region.
The opening marker's `sha256` is the SHA-256 of the exact UTF-8 payload bytes strictly between the marker lines; it does not include either marker line.
The closing marker must contain the identical ID.
Marker-like text that does not satisfy this complete paired grammar is unmanaged data.
Duplicate IDs, unmatched markers, invalid hash spelling, mismatched IDs, or payload hash mismatch block ownership-sensitive work.

`AGENTS.md` is canonical.
A `CLAUDE.md` sibling is an adapter only when it is a regular file whose complete bytes are exactly `b"@AGENTS.md\n"`; its hash is SHA-256 of those eleven bytes.
No other CLAUDE content is a shim or a canonical peer.
Substantive CLAUDE content requires a current, evidence-bound accepted consolidation proposal before replacement.
The shim policy is `keep`, `on`, or `off`; `keep` uses the last valid snapshot policy or resolves to `off` when no valid snapshot exists.

## Snapshot ownership state

The snapshot schema requires `schema_version`, `repository_root`, `owned_artifacts`, and `last_applied_topology`.
It separates the last-applied desired topology from ownership.
Mapping may mark an owned artifact stale, but it does not erase stale ownership; only guarded accepted prune can remove stale owned content.

Each owned artifact records `path`, `artifact_type`, `managed_id`, `status`, `payload_sha256`, `file_sha256`, and `mode`.
Artifact types are `agents-region`, `agents-file`, or `claude-shim`; status is `active` or `stale`.
A region binds its exact payload hash; a full AGENTS file or shim binds its full-file hash.
Ownership requires agreement among the schema record, normalized path, regular-file observation, marker grammar when applicable, hash, and mode.
A matching filename, desired topology, or marker fragment does not establish ownership.

`last_applied_topology` records `max_depth`, resolved `shim_policy`, `coverage_units`, and exclusions.
A coverage unit records `directory`, ordered `expected_chain`, `status_at_apply`, and `basis_at_apply`.
Snapshot topology is historical evidence, not permission to adopt present data.
A new snapshot replaces the old snapshot only after all product postimages verify.

## Transaction identity and journal

Only map/prune through private `_transaction.py` may create, update, recover, or clean the fixed journal.
Audit only inventories it.
A valid existing journal resolves before ordinary mutation; an invalid one blocks and is never overwritten.

The identity is acyclic.
`TransactionBasis` contains only `operation` and normalized ordered `products` plus `snapshot` entries.
Each basis entry contains `path`, `action`, `pre_exists`, `pre_sha256`, `pre_mode`, `post_exists`, `post_sha256`, and `post_mode`.
Hash the canonical basis serialization once with SHA-256 to obtain the transaction ID.

The ID input excludes all derived paths, phase, target state, recovery fields, an intended-snapshot duplicate, clocks, process data, and report data.
Only after ID creation derive every `pre_recovery_path`, `post_recovery_path`, `apply_path`, and `.next` path from authenticated ID, target path, and artifact role.
Recompute and validate those names on every journal read; never trust stored names merely because they appear in the journal.

A transaction target has the immutable basis fields plus derived `pre_recovery_path`, `post_recovery_path`, `apply_path`, and state.
States are exactly `pending`, `applying`, `applied`, `rolling-back`, and `rolled-back`.
Journal phases are exactly `preparing`, `prepared`, `applying-products`, `products-applied`, `committing-snapshot`, `snapshot-committed`, `cleaning`, and `recovery-required`.
No additional phase, state, or rename-before-mode classifier exists.

## Artifact roles and modes

A pre- or post-recovery file is immutable authoritative evidence: it is regular, mode `0600`, hash-valid for its bound preimage/postimage, and never writable after creation, renamed, truncated, or consumed as a rename source.
It remains available until verified whole prestate or poststate allows cleaning.

An apply temp is a distinct same-directory, derived, regular, consumable transaction file.
Its bytes and mode are selected from the direction, not copied from recovery-file mode:

- Forward product/snapshot create or replace: postimage bytes at `post_mode`.
- Prepared forward-delete rollback temp: preimage bytes at `pre_mode`; forward delete does not consume it.
- Automatic or accepted rollback: preimage bytes at `pre_mode`.
- Accepted completion: postimage bytes at `post_mode`.
- An absent image has no replacement temp for that direction; deletion uses unlink and parent fsync.

To create or recreate an apply temp: validate journal identity, derived path, direction, and the immutable source; exclusively create with no symlink following; copy the selected bytes; `fchmod` the open descriptor to the selected destination mode; verify `fstat` mode and raw hash while open; fsync the file; close; fsync its parent; then reopen/lstat and reverify containment, regular type, derived name, hash, and mode.
Only that verified temp may be atomically renamed.

The rename installs complete bytes and complete destination mode in one namespace transition.
After rename, fsync the target file, fsync its parent, and verify normalized target path, regular type, raw hash, and mode before state advance.
No `chmod` or `fchmod` occurs after rename.
A mode-0600 apply temp is valid only when its selected destination mode is itself 0600.

## Durable application order

1. Exclusively create and fsync the fixed mode-0600 journal, then fsync repository root.
2. Exclusively create every mode-0600 immutable recovery copy, hash-verify and fsync it, then fsync its parent.
3. Create every forward apply temp using the destination-mode procedure above; file fsync and parent fsync each one.
4. Enter `prepared` only after all recovery copies and forward apply temps are durable.
5. Enter `applying-products`. For each product, set `applying`; rename only its verified apply temp for create/replace or unlink for delete; fsync target when present and parent; verify complete postimage; set `applied`.
6. Enter `products-applied`, then `committing-snapshot`. Consume only the verified destination-mode snapshot apply temp; fsync snapshot and root; verify complete snapshot postimage.
7. Enter `snapshot-committed`; verify all product and snapshot postimages and recovery copies; enter `cleaning`.
8. Delete only validated, recomputed same-transaction `.next`, apply, and recovery artifacts with parent fsyncs. Remove the fixed journal last, then fsync root. Report success only afterward.

This is journal-first and snapshot-last.
No target mutation is permitted while `preparing` is incomplete.
Recovery copies are never deletion candidates before whole-state verification.

## Restart, rollback, and cleanup

On restart validate journal schema, identity, derived names, containment, target/snapshot hashes and modes, immutable-copy hashes/mode 0600, and any apply temp's direction-derived hash/mode.
Apply temps are non-authoritative and disposable; recreate them only from validated immutable evidence after selecting recovery direction.

`preparing` with no product deviation aborts and cleans only validated transaction artifacts.
Before snapshot commit, a complete preimage snapshot plus products each at complete preimage or postimage selects automatic reverse rollback.
During `committing-snapshot`, complete snapshot preimage selects rollback; complete postimage with all complete product postimages selects committed cleanup.
`snapshot-committed` or `cleaning` with complete poststate resumes idempotent cleanup.

Unexpected targets with a preimage snapshot may expose accepted rollback only with valid immutable preimages.
Unexpected targets with a postimage snapshot may expose accepted completion only with valid immutable postimages.
A snapshot matching neither complete bound image, missing/mismatched immutable evidence, invalid identity/name, path escape, symlink, or special file blocks and preserves all evidence.
Rerunning is never recovery consent.

## Stable diagnostics

Diagnostics use a stable catalog and deterministically ordered payloads.
They distinguish usage, unsafe inspection, schema/identity/name/path failure, ownership/marker/hash/mode drift, missing acceptance, recovery-artifact mismatch, coverage/loader gap, and apply/recovery failure.
IDs do not contain clock, process, temporary-path, host, or incidental exception text.

Usage, preflight, proposal, and recovery blocks exit 2 before target temps or a new journal.
Apply or recovery failures exit 3 and retain evidence.
Map/prune success exits 0 only after verified poststate and journal-last cleanup.
Audit exits 0 clean, 1 with findings, and 2 when safe inspection is impossible.
The old blanket-0600 apply-temp mode for a non-0600 destination is an existing apply-artifact mismatch: it is never authoritative and never creates a new classifier state.
