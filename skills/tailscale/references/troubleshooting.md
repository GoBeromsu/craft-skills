# Tailscale Troubleshooting Reference

## Goal
Provide a public-safe troubleshooting sequence for common Tailscale failures.

## Triage Order
1. Check whether the local client is installed and running.
2. Check whether the node is authenticated.
3. Check whether the remote node is reachable.
4. Only then test SSH or exposed services.

## Common Failure Classes
- CLI missing or not on PATH
- Client installed but disconnected
- Auth expired or login required
- Remote node offline or asleep
- Network healthy but service-layer problem still unresolved

## Daemon-Variant Pitfalls
- **Wrong restart path**: `brew services restart tailscale` only restarts a per-user LaunchAgent. On a host running the system LaunchDaemon (`/Library/LaunchDaemons/com.tailscale.tailscaled.plist`), use `sudo launchctl kickstart -k system/com.tailscale.tailscaled` instead. The two are not interchangeable.
- **CLI is a wrapper from a previous install**: a `tailscale` shimmed by a now-removed macsys app remains on `PATH` until the app is fully trashed and the shell session restarts. Run `file "$(command -v tailscale)"` — a path under `/Applications/Tailscale.app/...` means you are talking to the macsys IPC, not to the headless daemon.
- **Two daemons fighting over the socket**: during a macsys → headless migration, the app and the new system daemon can both try to own `${TAILSCALED_SOCKET}`. Quit the app fully (`osascript -e 'quit app "Tailscale"'`) before starting the system daemon, and during the transition pin the CLI to the headless socket with `tailscale --socket=${TAILSCALED_SOCKET} status`.
- **Stale Network System Extension**: macsys installs a Network System Extension at the kernel boundary. End users without SIP disabled cannot remove it via `systemextensionsctl uninstall`. The supported path is "delete the app and reboot" — macOS will then garbage-collect the extension. Do not attempt to force-remove it on a SIP-enforced machine.

## Hostname / Node-Identity Pitfalls
- After re-authentication, a host can appear in the admin console with a `-1` / `-2` / `-N` suffix because the previous node entry was still present at auth time. `tailscale set --hostname` only changes local prefs; the server-side machine name must be renamed or deleted in the admin console.
- A migrated host has a brand-new node key, so any ACL tags or exit-node permissions tied to the old node identity must be reapplied.

## Rule
Do not publish real hostnames, private IPs, tailnet domains, or personal SSH targets in examples.
