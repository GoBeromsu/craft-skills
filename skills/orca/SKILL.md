---
name: orca
description: Organizes Orca around low-clutter project identities and preserves running work while diagnosing which local connection layer still needs evidence. Use to "organize Orca", "reduce sidebar clutter", consolidate the "same repo across hosts", clean old branches in Orca, reuse or account for task terminals, resolve selector_not_found or remote_runtime_unavailable, investigate SSH failures to an Orca host, or handle "orca에 연결이 안된다". Not for standalone Git maintenance (use git), vault taxonomy (use local policy), or executable command mechanics (use the installed orca-cli and orchestration guides).
metadata:
  version: 1.4.2
---

# orca

A thin router. Orca's official skills own the mechanics; this package adds the operator's judgment about grouping, preserving running work, and naming where a connection failed.

## Route

- Commands, flags, retries, terminals, worktrees, and supervised workers → the official skills. Read the version-matched guide bundled with the selected executable (`orca skills list`, `orca skills get <name>`), or install them with `npx skills add https://github.com/stablyai/orca --skill <name>`. Use the installed guide rather than memory, and do not copy it here.
- Grouping, cross-host identity, naming, task terminals, and old-branch cleanup → [operations](references/operations.md).
- Git mechanics → the `git` skill.

## Boundaries

Informational questions stay read-only. A request authorizes only its own effect. Pairing, application or remote upgrades, restarts, installed-skill changes, GUI interference, setup removal, and terminal closure each need their own authorization. A skill install is not an application upgrade, and an update is not a reachability repair. Unknown identity, an unsupported operation, an unreachable host, or missing evidence means preserve the item and report partial coverage.

## Report

- **Connection diagnosis.** Exactly one layer, the evidence that identifies it, and what remains unproven. Do not invent a repair command. Re-run the failing command only through the official guide and quote real output.
- **Organization or cleanup.** The groups and identities actually changed, host coverage, and branches deleted or retained with reasons, read back from runtime state. If the sidebar was not inspected, say UI evidence is unavailable. No report file unless requested.
- **Terminals.** Per task, the actual retain, sleep, close, or release outcome and its reason. No creation and no effect is a valid outcome.

## Connection layers

Name the layer the evidence identifies and stop there.

| Layer | Symptom | What the evidence supports | What it does not authorize |
|---|---|---|---|
| 1 CLI presence | `orca` absent from `PATH` | The CLI is missing; report it and stop | Inspecting application internals or guessing an install path |
| 1 | Processes visible while status says not running | Crash-handler helpers outlive the runtime; `orca status --json` is the verdict | Reading the process list as the runtime verdict |
| 2 Repo registration | `selector_not_found` from the current-worktree query | The selector missed; registration is still a question | Registering without a current official miss for this root and operator approval |
| 2 | An active workspace selector fails in a sibling checkout | The launching terminal's identity may not contain this checkout | Assuming the sibling repo is unregistered |
| 3 Remote runtime | `remote_runtime_unavailable` | The named host's runtime did not answer; ask the host itself over SSH | A network repair, re-pair, or automatic restart |
| 3 | Remote answers but the graph is not ready | The graph may still be warming; re-poll | Restarting the application |
| 3 | A requested revive does not settle to ready | Report the last observed state and stop | Dispatching dependent work |
| 3 | Environment record or pairing endpoint missing | Pairing carries a credential and is an operator decision | Re-pairing on your own |
| 4 SSH transport | `Cannot execute command-line and remote command.` at 255 | The alias carries a remote command; override `RemoteCommand` and `RequestTTY` for that one call | Editing the operator's alias |
| 4 | A piped SSH call never returns | A persistent control master is holding stdout | Treating the host as down |
| 4 | Host unreachable at the transport layer | Hand off to tailnet triage | Repairing Orca |

A non-interactive host probe reads the effective alias with `ssh -G <host-alias>`, detaches stdin, keeps batch mode and a 10-second connection timeout, and redirects both streams to files in a unique private temporary directory. Bound it with a 20-second caller deadline, record the exit status, read the files, then remove only that probe's files. On timeout, mark the host unverified and continue without reconnecting.

## Anti-patterns

- Guessing why an operation silently failed, or re-registering to test the guess → search official docs and upstream issues first, update only for a shipped fix, then compare with a setup that works.
- Sorting repositories into PARA lifecycle groups, or repeating project and tab prefixes → group by the domain or large project and verify actual sidebar membership.
- Matching repos by name, or treating a folder registration as non-Git → inspect real roots and provider identities.
- Deleting a live setup to remove a duplicate-looking card → preserve it and resolve verified identity or grouping metadata.
- Reporting a successful API response as visible organization → require persisted read-back.
- Deleting old-looking branches or forcing a refused deletion → apply the evidence gates in operations and retain uncertain work.
- Closing a terminal because it looks old, idle, orphaned, or unverifiable, or closing a supervised worker instead of releasing it → follow the disposition rules in operations and the orchestration guide.
- Restarting the app, driving the GUI, or bulk-closing terminals to finish a task → preserve the current state and report the missing evidence.
