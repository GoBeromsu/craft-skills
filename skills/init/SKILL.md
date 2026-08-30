---
name: init
description: Maps a repository into a maintained hierarchical AGENTS.md knowledge base. Use when asked to "init this repo" for AGENTS, deep-init a codebase, generate or update AGENTS.md, map repository conventions, audit an existing AGENTS lifecycle, or prune accepted stale managed AGENTS artifacts. Not for package-manager or plugin initialization, docs scaffolding or authoring (use `document`), or git-hook installation (use `git`).
metadata:
  version: 4.0.0
---

# init

`init` owns the AGENTS lifecycle only: map, read-only audit, and guarded prune.
AGENTS.md is canonical.
CLAUDE.md may be an adapter only when its bytes are exactly `b"@AGENTS.md\n"`.
Do not scaffold documentation, author document content, initialize packages, or install git hooks.

Read the linked procedure when its phase is reached.
The lifecycle state and transaction rules are owned by [state contract](references/state-contract.md).
Loader classification evidence is owned by [loading contract](references/loading-contract.md).
Those contracts are linked here, not restated or weakened.

## Invocation

| Invocation | Valid flags | Behavior |
|---|---|---|
| `init` or `init [map flags]` | `--max-depth=N`, `--claude-shim=keep\|on\|off`, `--loading-evidence=JSON`, repeated `--accept=ID` | Map/deep-init. |
| `init map` or `init map [map flags]` | Exactly the same map flags | Exact equivalent of bare init. |
| `init audit` | none | Read-only JSON inspection. |
| `init prune` | repeated `--accept=ID` | Remove only accepted stale managed artifacts. |

Normalize an omitted operation to `map` before flag validation, preflight, proposals, journal handling, or effects.
Bare and explicit map must use one normalized request and one map path.
They have identical defaults, diagnostics, proposals, reports, transaction behavior, target results, snapshots, and exit classes.
`audit` and `prune` always require their explicit tokens.

`--max-depth` is an integer from 1 through 32 and defaults to 3.
It limits scoring and placement only, never discovery, coverage, existing-instruction chains, or journal inspection.
`--claude-shim=keep` uses the last valid snapshot policy, or `off` when no valid snapshot exists.
`--loading-evidence` consumes the provenance-bound receipt emitted by the package loader probe; unbound marker arrays remain unknown.
Legacy `--create-new`, unknown operations, malformed values, duplicate or conflicting operations, and cross-operation flags exit 2 before target temporary files or journal creation.
Bare init is valid and never selects a bootstrap outcome, audit, or prune.

The dispatcher is the executable form of that table and passes every remaining argument through unchanged:

```sh
python3 skills/init/scripts/init.py [map|audit|prune] [repository] [flags ...]
```

## Route

1. Run map for bare `init`, map flags without an operation, or explicit `init map`.
2. Run audit only for explicit `init audit`.
3. Run prune only for explicit `init prune`.

Map and prune preserve the state contract's preflight, ownership, proposal, transaction, recovery, durability, and snapshot-last rules.
Audit structurally reads state without importing map or prune effects and writes only JSON stdout.
Map and prune must not create a journal until validation, preflight, and required evidence-bound acceptances succeed.

## Map procedure

Run these phases in order:

| Phase | Procedure | Responsibility |
|---|---|---|
| 1 — Discovery | [phase-1-discovery.md](references/phase-1-discovery.md) | Build deterministic, evidence-grounded repository inventory. |
| 2 — Scoring | [phase-2-scoring.md](references/phase-2-scoring.md) | Choose root and eligible placements from the inventory. |
| 3 — Reconcile | [phase-3-reconcile.md](references/phase-3-reconcile.md) | Compute canonical managed content, ownership, proposals, and mutations. |
| 4 — Verify | [phase-4-verify.md](references/phase-4-verify.md) | Verify applied state, coverage, snapshot, and completion. |

The shared core computes normalization, inventory, scoring, topology, findings, proposals, mutation bases, and transaction identity before effects.
Map/prune effects are isolated from that pure core.
The execution fan-out class controls only how independent discovery work is scheduled.
The loader class is separate evidence about runtime instruction loading and remains unknown without an applicable sentinel probe.
Never infer loader behavior from fan-out capability, source inspection, directory placement, or a root fallback.

## Safety and canonicality

Before working on a path, read every `AGENTS.md` from repository root through that path's directory in order.
The nearest instruction wins on conflict.
Every non-excluded first-party regular-file target and every AGENTS file on each root-to-directory chain is inventoried at any depth without following symlinks.
Unreadable, truncated, special, symlinked, or unclassified paths are non-clean.
Root fallback is an instruction rule, not loader evidence.
Complete coverage is independent from placement depth.

Existing content is never silently adopted, overwritten, or deleted.
Map retains stale owned artifacts until prune receives the required evidence-bound acceptance.
Prune never adopts unrelated content while re-baselining observation.
Only exact CLAUDE shim content may be adopted without a substantive consolidation proposal.

## Completion report

Report the normalized operation, runtime execution class, loader evidence class, coverage and placement results, proposals or acceptances, state/snapshot result, and unavailable evidence.
For map, identify bare or explicit spelling only as input syntax; do not imply distinct behavior.
For audit, report findings without target writes.
For prune, report only accepted removals.

## Boundaries

| Responsibility | Owner |
|---|---|
| AGENTS map, audit, prune, canonicality, snapshots, and lifecycle state | **init** |
| Documentation scaffolding, README, ADRs, and substantive docs content | `document` |
| Git hooks and enforcement rails | `git` |
| Package, plugin, or ecosystem initialization | Outside init |

## Requirements

- `python3` — official source: <https://docs.python.org/3/>; safe probe: `python3 --version`; support boundary: Python 3.10+ for the dispatcher, lifecycle scripts, and package tests.
- Dependency trigger — a selected Python release or a changed probe result requires official-documentation review and rerunning `python3 -m unittest discover -s skills/init/tests -p 'test_*.py'` before trusting the prior recipe.

## Anti-patterns

- Treating bare init as a selector or requiring `init map` for ordinary mapping → normalize bare init to map.
- Adding a second map implementation for explicit syntax → use the single normalized map path.
- Restoring docs bootstrap, Phase 0, or `--create-new` → keep those routes removed.
- Letting placement depth hide first-party coverage or instruction discovery → inventory independently at all depths.
- Using fan-out, source inspection, or root fallback as loader proof → retain unknown without probe evidence.
- Writing from audit or importing apply effects into audit → preserve structural read-only inspection.
