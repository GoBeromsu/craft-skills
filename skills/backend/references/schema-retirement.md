# Schema retirement

When one schema version is declared canonical, the migration ledger that reached it stops being an asset and becomes dead weight that still runs on every deployment.
Retire it by replacing the migrator with a create-only bootstrap that creates, verifies, or refuses — and never upgrades.
This is a behavior change, not a restructuring: the system loses the ability to upgrade an older database on purpose, so the refusal path is the feature.

## Contents

- [Inputs](#inputs)
- [Ordered steps](#ordered-steps)
- [The bootstrap contract](#the-bootstrap-contract)
- [Judgment calls to flag explicitly](#judgment-calls-to-flag-explicitly)
- [Pitfalls](#pitfalls)
- [Success criteria](#success-criteria)

## Inputs

- The canonical schema-definition module and its runtime guards.
- How a fresh database is actually created today — a one-shot container service, a module entrypoint, an application-startup hook — traced before anything is deleted.

## Ordered steps

1. **Map the modules read-only first**, into two lists.
   Runtime: connection handling, path resolution, query functions, ownership and permissions, configuration, the canonical schema definition, and the guards.
   Ledger: versioned schema modules, the migrator, backfills, cutover machinery, legacy import, drain and recovery paths, and inventory gates.
   For every module you are unsure about, grep its callers and keep only what a runtime path imports.
   One drain module survived every reading of the code and turned out to be reachable only from an operations script, so it went.
2. **Replace the creation path; do not delete it.**
   Write the bootstrap below before removing anything it supersedes.
3. **Keep the operator-facing names.**
   The service name and the module entrypoint stay identical so runbooks and muscle memory keep working, even though what they run is now a bootstrap.
   Drop only the services and volumes that existed to feed the ledger.
4. Delete the ledger modules, their tests, the cutover runbooks, and the operations scripts.
   Fold still-valid operational rules — digest pinning, never destroying state volumes — into the architecture document; do not mint a decision record unless the repository's own convention asks for one.
5. **Update the import contracts that name deleted modules** in the same commit, because a contract checker errors on an unknown module rather than ignoring it.
6. Fix the topology and container-composition contract tests that pinned the old services.

A worked scale for this shape of change: 10,492 lines across 41 modules, 33 test modules, and 3 runbooks reduced to 3,140 lines across 13 modules, landing as 141 files at +910/−15,894.

## The bootstrap contract

Three outcomes, and exactly three:

- **Absent or empty** — create the canonical schema in one transaction, write one ledger row and the schema version marker, and report success with a created flag set true.
- **Already canonical** — verify the ledger row, the expected tables, and the manifest; mutate nothing; report success with the created flag false.
- **Any other version**, including a zero version marker on a database that already has tables — refuse loudly, leave the file byte-identical, and exit non-zero.

Take the exclusive deployment lock for the duration, and refuse while the application holds it.
Sequence the change as bootstrap first, ledger deletion second, documentation and contracts third, so each commit is independently revertible.

## Judgment calls to flag explicitly

These are decisions, not derivations — name each one in the change description.

- A ledger checksum was frozen into a constant so that databases already in the field, which reached the canonical version through the old ledger, keep validating. Tightening it to "exactly one row" waits until no such database exists.
- The engine version-floor module was deleted, leaving the floor asserted only in the container image, because the development host's engine is older than the floor.
- A runbook that four documents linked to as "the rollback procedure" was removed and those links repointed.
- A chunked test run hides dependency-ladder breakage when an ignore line in the contracts is wrong; run that test file on its own after editing contracts.

## Pitfalls

- **The one-shot service that "migrates" is also the only thing that creates a fresh database.**
  Deleting it without a replacement bricks every new installation while leaving existing ones healthy, so the failure appears only at the next deployment.
- **The dead ledger tests were the majority of the suite's database coverage.**
  Add the bootstrap smoke as a real test rather than a manual check, or the deletion trades dead coverage for none.

## Success criteria

- Smoke on a throwaway path: first run reports created, second run reports not-created, the schema version marker matches the canonical value, the expected tables exist, write-ahead logging is on, and the directory and file permissions are the intended restrictive ones.
- A foreign schema version marker produces the loud failure and a byte-identical file.
- The container-composition configuration still validates.
- The suite has no real failures, the linter is clean, and every import contract is kept.
- The change description lists the lines removed and states the bootstrap contract.
