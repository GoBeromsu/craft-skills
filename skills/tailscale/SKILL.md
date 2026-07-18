---
name: tailscale
description: Verifies and repairs the Tailscale tailnet that carries cross-host work — SSH, remote process inspection, `scp` — before a dependent workflow runs, and triages failures as network-layer versus service-layer. Use when `tailscale ping` or `ssh <peer>` hangs, when a peer that should be reachable is missing from `tailscale status`, when choosing the daemon-restart path for a macOS install variant (macsys `.pkg`, Homebrew LaunchAgent, system LaunchDaemon), when a browser OAuth popup appears mid-SSH, or when switching and verifying the active tailnet profile with `tailscale switch`. Not for generic SSH problems unrelated to the tailnet.
metadata:
  version: 1.0.0
---

# tailscale

Tailscale is the transport layer between a source-of-truth host (where work is authored) and a replica host (where it is executed). Any cross-host workflow — `ssh <replica>`, remote process inspection, `scp` of tracked config — assumes the tailnet is healthy. Verify that assumption and triage when it doesn't hold **before** invoking any dependent workflow; success is "tailnet healthy enough for the dependent workflow to proceed."

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

Not for generic SSH problems that do not involve the tailnet, or public-facing Funnel design beyond the dependent workflow. Never reveal Tailscale IPs (`100.x.x.x`), tailnet domains, or real hostnames in output — use neutral role labels (`source`, `replica`, `peer`) and MagicDNS names.

## Process

### 1. Check local status first

```bash
which tailscale || echo "tailscale CLI missing"
tailscale status | head -20
```

Expect the CLI present, the local node `connected`, and the target peer in the list with `idle` or `active` status (not `offline`).

### 2. Verify remote reachability before dispatching

```bash
tailscale ping <peer> | head -3
```

Expect a `pong from <peer>` under a few hundred ms. If ping fails, do not proceed to `ssh <peer>` — the dependent workflow will hang and waste attempts.

### 3. Separate network state from service state

If `tailscale ping <peer>` fails, the fault is at the tailnet layer. Triage on the relevant daemon using whatever out-of-band access exists (physical or screen share), and pick the restart path per install variant: quit/relaunch the app (macsys), `brew services restart tailscale` (per-user LaunchAgent), or `sudo launchctl kickstart -k system/com.tailscale.tailscaled` (system LaunchDaemon). A `sudo tailscale down && sudo tailscale up` cycle is a logical reconnect on any variant but does not restart the daemon process — use it only to renegotiate a running session, not to revive a wedged daemon.

If `tailscale ping <peer>` succeeds but `ssh <peer>` fails, the fault is at the service layer (sshd, keys, agent forwarding). Do not restart tailscale — fix ssh instead.

### 4. Hand off to the dependent workflow

Only after both checks pass, invoke the downstream skill or command. The dependent workflow owns its own success criteria.

### 5. Serve or Funnel only after baseline connectivity is proven

Never open a Serve or Funnel workflow before a fresh `tailscale status` + `tailscale ping <peer>` pass. Confirm the exposed service actually responds, and give every Funnel workflow an explicit teardown step plus a verification that the exposure is closed.

### 6. OAuth popup triage: classify the owner before touching Tailscale state

When a browser OAuth popup appears during Tailscale SSH or remote-agent work, determine whether it is Tailscale auth or an application launched through the Tailscale session. Inspect the URL and owning process before running `tailscale up`, deleting state, or restarting auth. App-layer OAuth residue (stale `claude.ai/oauth/authorize`, `localhost:<port>/callback` tabs) can look like a Tailscale problem when the transport is healthy — close only stale app-layer tabs and terminate only orphaned process trees; leave active terminal/tmux/agent sessions untouched (`references/oauth-popup-triage.md`).

If the popup appears specifically when initiating Tailscale SSH, check whether the SSH ACL rule uses `"action": "check"`: check mode requires periodic reauth per `checkPeriod` (12h default), while `accept` admits already-authenticated tailnet users (`references/tailscale-ssh-check-mode-oauth-popup.md`). If it is the device itself needing reauth, inspect node-key expiry — trusted or hard-to-reach devices should have key expiry disabled or be authenticated as tagged devices.

### 7. Reconcile profile, identity, and reachability drift before trusting a cached target

When a target that should be reachable is not — or the host holds more than one tailnet login — do not jump to `ssh` or a daemon restart. Branch through three checks in order, then return to the steps above:

1. **Profile** — confirm the intended tailnet is active (`tailscale switch --list`, `CurrentTailnet.Name` from `tailscale status --json`). A peer missing from `tailscale status` is most often the wrong active profile, not an offline peer. When several logins exist and it is unclear which tailnet owns the node, use `tailscale switch` as a search tool: hop across the stored profiles (`tailscale switch <profile>`) and re-run `tailscale status` until the node appears, before concluding the peer is offline; switch back once it is found.
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
- `references/tailnet-profile-and-identity-changes.md` — switch/verify the active tailnet profile, reconcile node identity and reachability drift.
