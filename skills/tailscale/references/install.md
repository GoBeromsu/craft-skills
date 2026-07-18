# Tailscale Install Reference

## Goal
Provide a public-safe installation baseline for Tailscale without embedding private machine assumptions.

## Public-Safe Principles
- Use the official Tailscale install flow for the target operating system.
- Prefer the documented CLI path for automation instead of personal shell aliases.
- Verify installation with a version or status command before continuing.

## Minimal Flow
1. Install Tailscale using the official package or installer for the target platform.
2. Confirm the CLI is available.
3. Authenticate through the supported login flow.
4. Verify that the node appears in the tailnet before continuing to SSH, Serve, or Funnel tasks.

## macOS Install Variants
Three install layouts coexist in the wild. Identify which one a host is on before troubleshooting or migrating.

- **macsys (Tailscale.app, standalone `.pkg`)** — GUI app, menu-bar item, daemon embedded in the app process. Suitable for laptops driven interactively.
- **Homebrew + per-user LaunchAgent** — `brew install tailscale` and `brew services start tailscale`. Daemon runs as the login user, stops when the user logs out. Suitable for workstations where the user is always logged in.
- **Homebrew + system LaunchDaemon (headless)** — `brew install tailscale` and `sudo tailscaled install-system-daemon`. Daemon runs as root via `launchd`, survives logout. Suitable for headless servers and for always-on workstations where no GUI is wanted.

Identification commands (use the host's own out-of-band shell, not over the tailnet you are trying to diagnose):
- `ls /Applications | grep -i Tailscale` — presence of `Tailscale.app` implies macsys is at least installed.
- `launchctl print system/com.tailscale.tailscaled` — exit 0 implies the system LaunchDaemon is loaded.
- `brew services list | grep tailscale` — `started` implies the per-user LaunchAgent is running.
- `file "$(command -v tailscale)"` — a shell-wrapper script under `/Applications/Tailscale.app/...` means the CLI on `PATH` belongs to the macsys app, not to Homebrew.

## macsys → Headless System Daemon Migration
For an always-on host that no longer needs the GUI, migrate to the system daemon. Run from the host itself with admin rights.

1. Snapshot pre-migration state (`tailscale status`, tailnet IPv4, exit-node and subnet-route settings) to a local file outside the vault. Do not commit this snapshot.
2. Quit the GUI: `osascript -e 'quit app "Tailscale"'`.
3. Install the Homebrew formula (CLI + daemon binaries): `brew install tailscale`.
4. Register the system daemon: `sudo tailscaled install-system-daemon`. This writes `/Library/LaunchDaemons/com.tailscale.tailscaled.plist` and starts the daemon as root.
5. Re-authenticate: `tailscale up` (add `--operator=<user>` if a non-root user should be allowed to run `tailscale` without `sudo`; re-apply exit-node and route flags captured in step 1).
6. Confirm the node appears connected with `tailscale status`.
7. Delete or rename the now-obsolete node entry in the Tailscale admin console — the host will otherwise re-register with a `-N` hostname suffix on next auth.
8. Move `/Applications/Tailscale.app` to the Trash. The Network System Extension that the macsys app loaded auto-unloads on next reboot for non-SIP-disabled hosts; do not attempt `systemextensionsctl uninstall` without SIP-disable, it will fail.

The migration creates a new tailnet node identity (new node key). ACL tags, exit-node permissions, and subnet-route advertisements must be re-applied either through `tailscale up` flags or the admin console.

## Hostname Reconciliation
`tailscale set --hostname <name>` rewrites local prefs only. The control-plane machine name is server-side and is set at the moment of (re-)authentication. If the previous node is still present in the admin console at auth time, the new node registers with a `-1` / `-2` / `-N` suffix. Delete (or rename) the stale node in the admin console before re-auth, or rename the new node after auth.
