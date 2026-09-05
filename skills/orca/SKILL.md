---
name: orca
description: Verifies and repairs the connection between a shell and an Orca orchestration runtime, triaging a failure as CLI presence, repo registration, remote-runtime liveness, or SSH transport before dependent worktree, terminal, or orchestration work. Use when `orca worktree current` returns `selector_not_found`, when `--worktree active` will not resolve, when an environment answers `remote_runtime_unavailable`, when ssh to an Orca host hangs or exits 255, when Orca processes are visible but the CLI reports no runtime, or when the operator says "orca에 연결이 안된다". Not for driving Orca once the runtime answers — use the bundled orca-cli guide — nor for tailnet reachability, which belongs to tailscale.
metadata:
  version: 1.0.0
---

# orca

Orca is an orchestration platform whose worktrees, managed terminals, dispatched workers, decision gates, and paired remote runtimes all sit behind four connection layers.
Success is a named layer verdict backed by tool output, a repair scoped to that layer alone, and the originally failing command re-run green.

## Output contract

A run reports the failing layer, the evidence that identifies it, the repair applied, and the re-run of the command that first failed.

- The verdict names exactly one layer — CLI presence, repo registration, remote-runtime liveness, or SSH transport — and cites the JSON error code, `orca status` field, or exit status that proves it.
- The repair touches only that layer; a green sibling command is not accepted as proof.
- Verification re-runs the failing command and the checks in `## Verification` that the change could affect, and quotes their real output.
- The summary names the layer, the fix, and any environment left unreachable.

When the run cannot succeed, it reports the last confirmed layer instead of a recovery claim:

- `orca` absent from `PATH` → report the missing CLI and stop, rather than inspecting application internals or guessing an install path.
- `orca open` does not settle to a ready runtime → report the last observed state and stop; do not dispatch dependent work.
- A host is unreachable at the transport layer → hand off to tailnet triage rather than repairing Orca.
- An environment record or its pairing endpoint is missing → report it; pairing carries a credential and is an operator decision.
- Process listings contradict `orca status` → report the runtime as down on the CLI's authority.

## Layer map

Each surface fails with a connection error, not a usage error, when its layer is down.

| Surface | Requires |
|---|---|
| `worktree`, `file`, `terminal` | Layers 1–2, since `--worktree active` resolves through a registered repo |
| `orchestration` runs, dispatch, workers, gates | Layers 1–2 locally, plus Layer 3 for any remote-hosted worker |
| `automations`, `project`, `repo` | Layer 1 locally, plus Layer 3 when scoped by `--environment` |
| Any `--environment` or `--host` command | Layer 3, plus Layer 4 to revive a dead host |
| Embedded browser, computer use, emulator | Layers 1–3 for the runtime that owns the surface |

## Layer 1 — CLI presence

```bash
command -v orca && orca status --json
```

`runtime.state: ready` with `graph.state: ready` means the local runtime is usable.
`not_running` means the application is down, and `orca open` starts it and waits for reachability.
Resolve the executable by discovery rather than a baked-in path, and keep using the same one for every later call.
A second copy on `PATH` from a package manager is equivalent to the bundle launcher and needs no repair.

## Layer 2 — Repo registration

A selector-bearing command failing inside an ordinary git checkout points here.

```
No Orca-managed worktree contains the current directory: <path>
```

`selector_not_found` from `orca worktree current --json` means the repo was never registered, while the CLI and runtime are healthy.
The identifiers Orca exports into a terminal name the workspace that launched it, so a sibling checkout inherits an identity that does not contain it.

```bash
orca repo add --path "<repo-root>" --json
orca worktree current --json
orca terminal list --worktree active --json
```

`worktree current` returns a worktree whose `path` is the repo root once registration takes effect.
Only then do `--worktree active`, file diffs, terminal creation, and worktree-scoped orchestration work from that directory.

## Layer 3 — Remote runtime liveness

`remote_runtime_unavailable` from an `--environment` call is a host verdict, not a network verdict.

```bash
orca environment show --environment "<environment>" --json
```

Read the endpoint host and pairing port from that record, then ask the host itself for the truth.

```bash
ssh -o RemoteCommand=none -o RequestTTY=no -o BatchMode=yes "<host-alias>" \
  'orca status --json' </dev/null
```

`app.running: false` with `runtime.state: not_running` confirms the remote runtime is dead, and an absent listener on the pairing port corroborates it.
Revive it over the same channel with `orca open --json`, which blocks until the runtime answers and reports `graph_not_ready` only while the graph warms.
Re-verify locally with `orca status --environment` and one operational call such as `orca repo list --environment`.
Quote an environment name that contains spaces.
Version drift between the local and remote application is normal and is not a connection fault, so an update is not a reachability repair.

## Layer 4 — SSH transport

Two configuration patterns break non-interactive access while interactive use stays healthy.

```bash
ssh -G "<host-alias>" | grep -iE '^(hostname|user|requesttty|remotecommand|controlpath)'
```

An alias carrying `RequestTTY yes` with a `RemoteCommand` that attaches a multiplexer serves humans, and any command argument fails with `Cannot execute command-line and remote command.` at exit 255.
That alias is working as intended, so override it per invocation instead of editing it.

```bash
ssh -o RemoteCommand=none -o RequestTTY=no "<host-alias>" '<command>'
```

With `ControlMaster auto` and `ControlPersist`, the first connection forks a background master that inherits stdout, so a piped call waits for the persist window rather than the ssh timeout.
An outer timeout on the foreground process does not release it, because the master holds the pipe.

```bash
ssh -o BatchMode=yes "<host-alias>" '<command>' </dev/null >"${TMPDIR:-/tmp}/ssh-out.txt" 2>&1
echo "exit=$?"; cat "${TMPDIR:-/tmp}/ssh-out.txt"
```

Detaching stdin also turns a silent credential prompt into a fast failure.

## Verification

| Check | Command | Pass condition |
|---|---|---|
| Local runtime | `orca status --json` | `runtime.state` and `graph.state` both `ready` |
| Repo registration | `orca worktree current --json` | returns a worktree whose `path` is the repo root |
| Selector usability | `orca terminal list --worktree active --json` | `ok: true`, where an empty terminal list still passes |
| Remote runtime | `orca status --environment "<environment>" --json` | `runtime.state` and `graph.state` both `ready` |
| Remote operability | `orca repo list --environment "<environment>" --json` | `ok: true` with the host's repos |
| SSH non-interactive | `ssh -o RemoteCommand=none -o RequestTTY=no "<host-alias>" 'echo OK' </dev/null` | prints `OK` at exit 0 |

Sweep every saved environment after reviving a host, because one dead host hides others and a dispatch aimed at an unreachable one fails long after the run is created.

## Symptom index

| Symptom | Layer | Verdict | Repair |
|---|---|---|---|
| `selector_not_found` from `worktree current` | 2 | Repo unregistered, runtime healthy | `orca repo add --path <repo-root>` |
| `--worktree active` fails in a sibling checkout | 2 | Workspace identity inherited from the launching terminal | register the sibling repo root |
| `remote_runtime_unavailable` | 3 | Remote application down, local CLI healthy | `orca open` on the host over ssh |
| Remote reachable but `graph_not_ready` | 3 | Graph still warming | re-poll instead of restarting |
| `Cannot execute command-line and remote command.` at 255 | 4 | Alias carries a `RemoteCommand` | `-o RemoteCommand=none -o RequestTTY=no` |
| A piped `ssh` never returns | 4 | Persistent master holds stdout | `</dev/null` with output redirected to a file |
| Processes visible while the CLI reports `not_running` | 1 | Stale helper processes, no runtime | trust `orca status --json`, then `orca open` |

## Requirements

- `orca` — official source: the installed application's `orca --help` and `orca agent-context --json`, which carry the machine-readable command schema; safe probe: `orca status --json`; support boundary: a runtime advertising `runtime.status.compat.v1` and `runtime.environments.v1`.
- `ssh` — official source: https://man.openbsd.org/ssh_config; safe probe: `ssh -G <host-alias>`; support boundary: an OpenSSH client supporting `ControlPersist` and `RemoteCommand`.
- Dependency trigger — a change to the Orca CLI's status schema, error codes, or environment record shape requires rechecking `orca agent-context --json` and rerunning the affected eval cases before the recipe is trusted.

## Anti-patterns

- Reading a process listing as proof that a runtime is up → crash-handler helpers outlive the application, so take the verdict from `orca status --json`.
- Treating `remote_runtime_unavailable` as a network fault → confirm runtime state on the host before touching transport or pairing.
- Editing an interactive ssh alias so an agent call succeeds → override `RemoteCommand` and `RequestTTY` per invocation and leave the operator's alias intact.
- Piping the first ssh call to a host that uses a persistent control master → redirect to a file, since the master holds the pipe past any outer timeout.
- Re-pairing an environment or upgrading an application to chase reachability → repair the layer the evidence names, and leave credential-bearing pairing to the operator.
- Reporting a connection restored from the repair command's own exit code → re-run the command that originally failed and quote its output.
