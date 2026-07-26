# Tailnet profile, identity, and reachability changes

A cross-host workflow assumes the target peer is the node you think it is, on the
tailnet you think you are on, and reachable right now. When any of those three
assumptions shifts, `ssh <peer>` either hits the wrong box, fails to resolve, or
hangs. This reference is the branch to take when a target that *should* be
reachable is not — before blaming the daemon or the dependent workflow.

Use neutral role labels (`source`, `replica`, `peer`) and MagicDNS names in all
output. Never paste a 100.x address, a tailnet domain, or a real hostname.

## A. Tailnet profile switching (multiple logins on one host)

One host can hold more than one tailnet identity (multiple login accounts). Only
one profile is active at a time, and the active profile decides which peers,
which 100.x addresses, and which MagicDNS suffix exist.

```bash
tailscale switch --list          # list stored profiles; the active one is marked
tailscale switch <profile>       # activate a different tailnet identity
tailscale status --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["CurrentTailnet"]["Name"])'
```

- Before any cross-host operation, confirm the active tailnet matches the one the
  target lives on. A peer "missing" from `tailscale status` is most often the
  **wrong active profile**, not an offline peer — check the profile before
  declaring the peer gone.
- When the host holds several logins and you are unsure which tailnet the node is
  on, use `tailscale switch` as a search tool: hop to each stored profile in turn
  (`tailscale switch <profile>`) and re-run `tailscale status` until the node
  appears. This finds the right tailnet faster than guessing and distinguishes
  "wrong profile" from "genuinely offline." Switch back to the profile your
  workflow runs on once the node is found.
- The MagicDNS suffix differs per tailnet. A name that resolved under one profile
  fails under another. Re-resolve the peer name after every switch.
- Switching profiles changes this host's own 100.x address too; do not carry an
  address learned under one profile into work done under another.
- `tailscale switch` changes the active network for **every** process on the host,
  not just the current workflow. A hop taken to find a node must be undone —
  switch back to the profile the workflow runs on before continuing.

### A1. Ownership classification — own tailnet vs external

Reachability is not authorization. Before the first command that reaches a peer,
place the target in one of two classes:

- **Own** — a node on the operator's own personal tailnet, owned by the operator's
  own account.
- **External** — a node **shared in** from another account (Tailscale node
  sharing), or any node on a tailnet the operator was **invited** to rather than
  owns. An organization or another person's tailnet the operator holds a login for
  is external, however routine the access feels.

Two signals settle it:

```bash
# 1. Which tailnet is active, and which account is Self?
tailscale status --json | python3 -c 'import json,sys; d=json.load(sys.stdin); \
print("TAILNET", d["CurrentTailnet"]["Name"]); print("SELF-USER", d["User"][str(d["Self"]["UserID"])]["LoginName"])'

# 2. Which account owns the target peer? A different LoginName than Self's means shared in.
tailscale status --json | python3 -c 'import json,sys; d=json.load(sys.stdin); \
[print(p["HostName"], d["User"][str(p["UserID"])]["LoginName"]) for p in d["Peer"].values()]'
```

The plain `tailscale status` output carries the same owner in its per-peer account
column — the JSON form is for when the text output is ambiguous.

**The gate.** On an external target, stop and get the operator's explicit approval
before running anything that reaches the peer or changes state on it: `ssh`, `scp`,
remote process control, `serve`, `funnel`, ACL or admin-console edits, or
`tailscale up`/`down` under that profile. State what the approval covers — the
tailnet, the peer, the owning account, and the exact command. Approval is per-task:
it does not carry to the next peer, the next command, or the next session.

Always permitted without asking, because they are how the classification is made:
`tailscale status`, `tailscale switch --list`, `tailscale ping`, and a discovery hop
that switches profiles, reads status, and switches back.

When the owning account cannot be established — an unparseable status, a peer the
JSON does not attribute — the target is external for gating purposes. Ambiguity
resolves toward asking.

## B. Reachability drift — peer offline, asleep, or just returned

A peer that was reachable can power off, sleep, or roam off the network.
`tailscale status` then shows `offline, last seen ...` and `tailscale ping <peer>`
times out.

- Do **not** `ssh` into an offline or asleep peer — the dependent workflow hangs
  and wastes attempts. Treat "unreachable now" as a **defer** condition, not a
  failure.
- For an action that must run on a currently-offline peer — for example repairing
  a machine-local symlink that a synced vault cannot fix, because the symlink is
  host-local state — queue the exact one-shot command and run it as
  `ssh <peer> '<cmd>'` the next time the peer is online. Verify the side effect,
  then consider it done. **Until the command actually runs and is verified, the
  action is pending, not complete — report it as pending.**
- A peer that just returned may report `online` in the control plane before its
  sshd is accepting connections. If `tailscale ping <peer>` passes but `ssh`
  refuses, wait and retry — this is a service-layer warm-up, not a tailnet fault,
  so do not restart tailscale.

## C. Identity drift — IP, hostname, and self-vs-peer confusion

- Never hardcode or cache a 100.x address across sessions. A node's address is
  stable while the node lives, but a re-auth or re-register issues a **new** node
  and a new address. Address peers by MagicDNS name and re-resolve each session.
- When a node re-registers while an old node of the same name still exists, the
  control plane appends a numeric suffix (`<name>-1`). Reconcile in the admin
  console — delete the stale node or rename it — so the canonical name resolves;
  do not chase the suffixed name in scripts.
- Two nodes with near-identical names (for example, one being this host and one a
  remote peer) are an identity trap. Confirm which address is **`Self`** and which
  is the **`Peer`** before issuing `ssh`:

  ```bash
  tailscale status --json | python3 -c 'import json,sys; d=json.load(sys.stdin); s=d["Self"]; print("SELF", s["HostName"], s["TailscaleIPs"][0])'
  ```

  Issuing `ssh` against `Self`'s own address connects to the local box (and is
  refused outright if local Remote Login is off), not the intended remote. A
  "connection refused" against what you believe is the remote is the signature of
  this mistake — re-check Self vs Peer before retrying.
- `tailscale set --hostname` only rewrites local prefs; the control-plane machine
  name is server-side. Rename in the admin console (or delete the old node before
  re-auth) to make the new name resolve tailnet-wide — otherwise the host
  re-registers with a `-N` suffix.

## Decision order when a target is unexpectedly unreachable

1. **Profile** — is the intended tailnet the active profile?
   (`tailscale switch --list`, `CurrentTailnet.Name`)
2. **Ownership** — is the target on the operator's own tailnet, or external? If
   external, ask before acting (§A1). Reachable is not authorized.
3. **Identity** — is the address you are about to use the `Peer`, not `Self`?
   (`tailscale status --json` → `Self` vs `Peer`)
4. **Reachability** — does `tailscale ping <peer>` return pong? If not, defer the
   action and re-attempt on reconnect; do not SSH into an unreachable peer.

Only after all three hold does the network-vs-service triage in
`troubleshooting.md` apply.
