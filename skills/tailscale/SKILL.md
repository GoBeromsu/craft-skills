---
name: tailscale
description: Verifies and repairs the Tailscale tailnet that carries cross-host work — SSH, remote process inspection, `scp` — before a dependent workflow runs, and triages failures as network-layer versus service-layer. Use when `tailscale ping` or `ssh <peer>` hangs, when a reachable peer is missing from `tailscale status`, when switching networks between tailnets with `tailscale switch` or listing stored profiles, when the target is a shared-in node or a tailnet you were invited to rather than own, when picking the daemon-restart path for a macOS install variant, or when a browser OAuth popup appears mid-SSH. Not for generic SSH problems unrelated to the tailnet.
metadata:
  version: 1.2.1
---

# tailscale

Tailscale is the transport layer between a source-of-truth host (where work is authored) and a replica host (where it is executed). Any cross-host workflow — `ssh <replica>`, remote process inspection, `scp` of tracked config — assumes the tailnet is healthy. Verify that assumption and triage when it doesn't hold **before** invoking any dependent workflow; success is "tailnet healthy enough for the dependent workflow to proceed."

One host can hold several tailnet logins at once, and `tailscale switch` is how the active network changes — `tailscale switch --list` enumerates the stored profiles, `tailscale switch <profile>` activates a different one. Only one is active at a time, and the active profile decides which peers, addresses, and MagicDNS suffix exist. A peer "missing" from `tailscale status` is far more often the wrong active profile than an offline peer.

Not every reachable tailnet is the operator's to act on. Nodes shared in from another account, and tailnets the operator was *invited* to rather than owns, are **external** — see the consent gate in step 2, which is a hard stop, not a preference.

## Mutable CLI and daemon facts

For Tailscale CLI syntax, daemon behavior, install layout, and control-plane state, consult official Tailscale documentation first. Disclose conflicts with observed behavior or other sources; a more-specific repository-local contract or reproducible evidence for the installed version and platform overrides general or stale documentation. Keep an unresolved fact unknown and fail safely: stop before state-changing or peer-reaching work rather than guessing. Never invent a Tailscale command, flag, daemon behavior, or capability.

## Dependency maintenance

Treat Tailscale as a package-local dependency. Consult [the official Tailscale knowledge base](https://tailscale.com/kb) before changing guidance, and record the installed client safely with:

```bash
tailscale version
```

Support only behavior verified for the selected tailnet, installed client version, and platform; do not promote a newly documented command or daemon behavior beyond that boundary. When the client, daemon, or CLI updates, re-run the switch, status, and SSH-consent evaluations before releasing the package update.

Three macOS install layouts coexist, and the daemon-restart path differs across them:
- **macsys (Tailscale.app, standalone `.pkg`)** — GUI app with the daemon embedded in the app process. Restart by quitting and relaunching the app (`osascript -e 'quit app "Tailscale"'`, then launch again).
- **Homebrew + per-user `LaunchAgent`** — `brew install tailscale` + `brew services start tailscale`. Daemon runs as the login user, stops on logout. Restart via `brew services restart tailscale`.
- **Homebrew + system `LaunchDaemon` (headless)** — `brew install tailscale` + `sudo tailscaled install-system-daemon`. Daemon runs as root via `launchd`, survives logout. Restart via `sudo launchctl kickstart -k system/com.tailscale.tailscaled`. Do not use `brew services` here — it manages the per-user agent, not the root system daemon.

## When to use

- Before any `ssh <replica>` issued from a source-of-truth host, or when a workflow depends on a peer being reachable through the tailnet.
- When a peer appears offline, asleep, or `ssh` hangs against it.
- When SSH over Tailscale fails and the fault must be placed at the network layer or the service layer.
- When migrating a host from Tailscale.app macsys to a headless `tailscaled` system daemon.
- When documenting Serve/Funnel workflows that must not leak private tailnet topology.
- When the active tailnet profile, a node's identity (IP/hostname), or a peer's reachability has changed since the target was last addressed.
- When switching networks between tailnets, listing stored profiles, or deciding which of several logins owns a given node.
- When the target is a shared-in node or lives on a tailnet the operator was invited to rather than owns.

Not for generic SSH problems that do not involve the tailnet, or public-facing Funnel design beyond the dependent workflow. Never reveal Tailscale IPs (`100.x.x.x`), tailnet domains, or real hostnames in output — use neutral role labels (`source`, `replica`, `peer`) and MagicDNS names.

## Process

### 1. Check local status first

```bash
which tailscale || echo "tailscale CLI missing"
tailscale status | head -20
```

Expect the CLI present, the local node `connected`, and the target peer in the list with `idle` or `active` status (not `offline`).

### 2. Classify tailnet ownership — ask before acting on a network that is not the operator's

Before the first command that reaches a peer, establish who owns the target: the operator's own personal tailnet, or an **external** network — a node shared in from another account, or a tailnet the operator was invited to.

```bash
tailscale switch --list          # stored profiles; the active one is marked
tailscale status                 # the per-peer account column names the owner
```

Compare the peer's owning account against `Self`'s, and the active tailnet against the operator's own (`references/tailnet-profile-and-identity-changes.md` §A). Then branch:

- **Own personal tailnet** — proceed through the remaining steps without asking.
- **External tailnet** — **stop and get the operator's explicit approval before running anything that reaches the peer or changes state on it** (`ssh`, `scp`, `serve`, `funnel`, remote process control, ACL or admin-console changes, `tailscale up/down` under that profile). Present what the approval covers: which tailnet, which peer, whose account owns it, and the exact command. Approval is per-task, not standing — a second task against the same external node needs a fresh ask.
- **Cannot tell** — treat as external and ask. Ambiguity resolves toward asking, never toward proceeding.

Read-only local inspection (`tailscale status`, `switch --list`, `ping`) is always allowed; it is how the classification is made. Discovery hops (`tailscale switch <profile>` → `status` → switch back) are allowed for locating a node, but must return to the profile the workflow runs on and must not be used as a way to start operating on the external tailnet.

### 3. Verify remote reachability before dispatching

```bash
tailscale ping <peer> | head -3
```

Expect a `pong from <peer>` under a few hundred ms. If ping fails, do not proceed to `ssh <peer>` — the dependent workflow will hang and waste attempts.

### 4. Separate network state from service state

If `tailscale ping <peer>` fails, the fault is at the tailnet layer. Triage on the relevant daemon using whatever out-of-band access exists (physical or screen share), and pick the restart path per install variant: quit/relaunch the app (macsys), `brew services restart tailscale` (per-user LaunchAgent), or `sudo launchctl kickstart -k system/com.tailscale.tailscaled` (system LaunchDaemon). A `sudo tailscale down && sudo tailscale up` cycle is a logical reconnect on any variant but does not restart the daemon process — use it only to renegotiate a running session, not to revive a wedged daemon.

If `tailscale ping <peer>` succeeds but `ssh <peer>` fails, the fault is at the service layer (sshd, keys, agent forwarding). Do not restart tailscale — fix ssh instead.

### 5. Hand off to the dependent workflow

Only after status, ownership, and reachability all pass, invoke the downstream skill or command. The dependent workflow owns its own success criteria — but it does **not** inherit permission to act on an external tailnet; that approval is granted in step 2 or not at all.

### 6. Serve or Funnel only after baseline connectivity is proven

Never open a Serve or Funnel workflow before a fresh `tailscale status` + `tailscale ping <peer>` pass. Confirm the exposed service actually responds, and give every Funnel workflow an explicit teardown step plus a verification that the exposure is closed.

### 7. OAuth popup triage: classify the owner before touching Tailscale state

When a browser OAuth popup appears during Tailscale SSH or remote-agent work, determine whether it is Tailscale auth or an application launched through the Tailscale session. Inspect the URL and owning process before running `tailscale up`, deleting state, or restarting auth. App-layer OAuth residue (stale `claude.ai/oauth/authorize`, `localhost:<port>/callback` tabs) can look like a Tailscale problem when the transport is healthy — close only stale app-layer tabs and terminate only orphaned process trees; leave active terminal/tmux/agent sessions untouched (`references/oauth-popup-triage.md`).

If the popup appears specifically when initiating Tailscale SSH, check whether the SSH ACL rule uses `"action": "check"`: check mode requires periodic reauth per `checkPeriod` (12h default), while `accept` admits already-authenticated tailnet users (`references/tailscale-ssh-check-mode-oauth-popup.md`). If it is the device itself needing reauth, inspect node-key expiry — trusted or hard-to-reach devices should have key expiry disabled or be authenticated as tagged devices.

### 8. Reconcile profile, identity, and reachability drift before trusting a cached target

When a target that should be reachable is not — or the host holds more than one tailnet login — do not jump to `ssh` or a daemon restart. Branch through three checks in order, then return to the steps above:

1. **Profile** — confirm the intended tailnet is active (`tailscale switch --list`, `CurrentTailnet.Name` from `tailscale status --json`). A peer missing from `tailscale status` is most often the wrong active profile, not an offline peer. When several logins exist and it is unclear which tailnet owns the node, use `tailscale switch` as a search tool: hop across the stored profiles (`tailscale switch <profile>`) and re-run `tailscale status` until the node appears, before concluding the peer is offline; switch back once it is found. If the node turns up under an external profile, the search ends there — return to step 2 and ask before acting on it.
2. **Identity** — confirm the address is the `Peer`, not `Self` (`tailscale status --json` → compare `Self` vs `Peer`). Addressing `Self` SSHes into the local box. Address peers by MagicDNS name and re-resolve each session; never cache a 100.x address.
3. **Reachability** — if `tailscale ping <peer>` does not return pong, treat the peer as a **defer** condition: queue the one-shot command and run it on reconnect rather than SSHing into an unreachable node. An action against an offline peer is pending until it actually runs and is verified — never reported complete.

Full procedure: `references/tailnet-profile-and-identity-changes.md`.

## Source-of-truth host discipline

In a two-host setup, every meaningful change is authored on the source-of-truth host and executed over `ssh <replica>`:
- Prefer one-shot `ssh <replica> '<command>'` invocations so every remote action lands in the source-of-truth host's transcript. Interactive ad-hoc sessions on the replica leave no audit trail.
- Config files that govern the replica live in tracked directories on the source-of-truth host and are pushed via `scp`. Never edit them in place on the replica.
- The only legitimate interactive session on the replica is when a real TTY is required (e.g. a password prompt that cannot be piped). Capture any state it produced back to the source-of-truth host immediately.

## Anti-patterns

- Pasting Tailscale IPs (`100.x.x.x`), tailnet domains, or real hostnames into output → use neutral role labels (`source`, `replica`, `peer`) and MagicDNS names in every example.
- Concluding "SSH fails, so Tailscale is broken" → run `tailscale ping <peer>` first; SSH failure can be network-layer or service-layer, and only a failed ping implicates the daemon.
- Treating all Tailscale installs the same during a restart → identify the macOS variant first and use its matching restart path (`references/install.md`).
- Running `brew services restart tailscale` on a host using the system `LaunchDaemon` → use `sudo launchctl kickstart -k system/com.tailscale.tailscaled`; `brew services` manages only the per-user agent.
- Assuming Tailscale.app still owns the tailnet after a headless migration → verify with `launchctl print system/com.tailscale.tailscaled` and `file "$(command -v tailscale)"`; the system daemon owns the session once migrated.
- Leaving both the macsys app and the headless daemon running → quit the app fully before starting the system daemon so only one client owns the socket.
- Treating `tailscale set --hostname` as the final rename → reconcile the control-plane name in the admin console (delete or rename the old node), or the host re-registers with a `-N` suffix.
- SSHing into the replica to make a config change interactively → author it on the source-of-truth host and run `ssh <replica> '<cmd>'` so the transcript carries the change.
- Opening a Serve/Funnel and forgetting it → every Funnel workflow needs an explicit teardown step and a verification that the exposure is closed.
- Resetting Tailscale auth (`tailscale up`, logout, state deletion, reinstall) on any browser OAuth popup → classify the URL and owning process first; if ping is healthy and the URL is an app OAuth flow, clean the app-layer residue instead.
- Declaring a peer offline because it is missing from `tailscale status` → confirm the active profile first: `tailscale switch --list`, hop through stored profiles with `tailscale switch <profile>` until the node appears, and check `CurrentTailnet.Name`.
- SSHing into a shared-in node, or one on a tailnet the operator was invited to, because it answered `tailscale ping` → reachable is not the same as authorized; classify ownership in step 2 and get explicit approval before the first command that reaches an external peer.
- Reading "the operator has a profile for that tailnet" as permission to operate on it → a stored login proves access, not consent; the profile exists so the network can be reached when asked for, not on the agent's initiative.
- Carrying one approval across tasks, peers, or sessions on an external tailnet → approval is per-task and names its peer and command; the next task asks again.
- Using a discovery hop as a foothold — switching into an external profile to look for a node, then continuing to work there → switch back to the workflow's profile and ask before acting.
- Guessing at ownership when `tailscale status` is unclear about which account owns a peer → ambiguity resolves toward asking; treat an unclassifiable target as external.
- Leaving the host parked on a profile a discovery hop switched into → `tailscale switch` changes the active network for everything on the host, so restore the original profile once the node is found.
- Reusing a cached 100.x address across sessions → address peers by MagicDNS name and re-resolve each session; a re-registered node gets a new address and a `-N` suffix.
- Choosing an `ssh` target from two similarly-named nodes without checking → confirm `Self` vs `Peer` in `tailscale status --json`; `Self`'s address hits the local box.
- Reporting an action against an offline peer as complete → offline is a defer condition; queue the one-shot command, run it when a fresh ping returns pong, verify the side effect, and report it pending until then.
- Mixing network-layer and service-layer debugging without branching → fix the daemon only when ping fails, fix ssh/keys only when ping passes but ssh fails.

## Requirements

- `tailscale` CLI on the diagnosing host, plus out-of-band shell access to any peer that is unreachable over the tailnet.
- `python3` for the `tailscale status --json` parsing snippets in `references/tailnet-profile-and-identity-changes.md`.

## Related

- `references/install.md` — install variants, identification commands, macsys → headless system-daemon migration.
- `references/troubleshooting.md` — failure-class triage and daemon-variant pitfalls.
- `references/oauth-popup-triage.md` — distinguish Tailscale-owned auth from stale app-layer OAuth residue.
- `references/tailscale-ssh-check-mode-oauth-popup.md` — repeated Tailscale SSH browser prompts from ACL check mode.
- `references/tailnet-profile-and-identity-changes.md` — switch networks between tailnet profiles, classify own-vs-external ownership and gate on consent, reconcile node identity and reachability drift.
