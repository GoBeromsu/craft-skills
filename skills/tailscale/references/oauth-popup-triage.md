# OAuth popup triage on Tailscale-mediated hosts

Use this when a browser OAuth popup appears during or after Tailscale SSH / remote-agent work and the user describes it as a "Tailscale OAuth popup". The durable lesson: first prove whether the popup belongs to Tailscale or to an application launched through the Tailscale session.

## Symptom pattern

- A browser shows OAuth tabs for an application, not Tailscale. Common examples from agent workflows:
  - `https://claude.ai/oauth/authorize?...redirect_uri=http://localhost:<port>/callback...`
  - `https://platform.claude.com/oauth/code/callback?...`
  - `http://localhost:<port>/callback?...`
- No Tailscale-owned OAuth or login tab is present.
- No listener is active on the OAuth callback port.
- Old agent process trees launched from a Tailscale SSH context are still alive long after the original session ended.
- Tailscale ping and SSH transport are healthy; the popup is app-layer OAuth residue, not a tailnet auth failure.

## Safe triage sequence

1. Inspect browser tabs for ownership before touching Tailscale auth/state.
   - Tailscale-owned auth URLs generally use Tailscale's login/admin domains and device-login flow.
   - App-owned OAuth URLs use that app's domain plus a localhost callback.
2. Check whether the callback listener is alive:
   - `lsof -nP -iTCP -sTCP:LISTEN | egrep '<port>|oauth|agent|tailscale|tsnet'`
3. List long-lived agent processes:
   - `ps -axo pid,ppid,lstart,etime,command | egrep 'agent|claude|codex|opencode|mcp-server|oauth|tailscale'`
4. If stale app processes are clearly orphaned, close only their stale OAuth tabs and terminate only that process tree.
   - Do not kill the current active terminal/tmux/agent session unless it is confirmed to be the offender.
5. Re-check that OAuth tabs are gone and no callback listener remains.

## Preserve the local lesson before pruning

If this triage came from a local/private runtime skill or session note, do not delete that source immediately after adding this public-safe reference. First confirm that the reusable parts were carried forward:

- browser URL ownership check before any Tailscale auth reset;
- callback-port listener check;
- long-lived/orphaned agent process check;
- warning not to kill active terminal/tmux/agent sessions;
- final verification that stale OAuth tabs and listeners are gone.

Only archive or prune the old local note after the public skill contains those reusable lessons and any private hostnames, file paths, or user-specific process labels have been generalized.

## Pitfall

Do not run `tailscale logout`, `tailscale up`, delete `tailscaled.state`, or reinstall Tailscale merely because the user calls it a Tailscale OAuth popup. First classify the URL and process owner. If Tailscale connectivity is already healthy, prefer cleaning the application-layer OAuth residue.
