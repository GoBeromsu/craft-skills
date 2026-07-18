# Tailscale SSH check-mode OAuth popup

Use this when Tailscale SSH or remote-agent access to a tailnet node repeatedly opens a browser/OAuth confirmation prompt even though local daemon state looks healthy. The repeated prompt may be ACL policy, not local daemon/login state.

## Symptom

- SSH or remote-agent access to a Tailscale node repeatedly opens a browser/OAuth confirmation popup.
- Local `tailscale debug prefs` can still show healthy state such as `RunSSH: true`, `WantRunning: true`, and `LoggedOut: false`.
- The local CLI can show the node as connected, but the control-plane SSH policy can still require periodic browser checks.

## Fast diagnosis in Admin Console

1. Open the Tailscale Admin Console SSH access-control editor.
2. Check the Tailscale SSH rule table.
3. If a rule shows check mode enabled, or the rule JSON contains:

```json
"action": "check"
```

then that rule is explicitly configured to require periodic reauthentication.

## Browser fix path

1. Admin Console → **Access controls** → **Tailscale SSH**.
2. Open the SSH rule → **Edit**.
3. Either:
   - set **Check mode** from `On` to `Off`, which changes the rule to `"action": "accept"`; or
   - keep check mode enabled but set an explicit `checkPeriod` appropriate for the trust boundary.
4. Save the SSH rule.
5. Verify with a fresh Tailscale SSH attempt from the intended source to the intended destination.

## Notes and pitfalls

- Do not infer this from local CLI alone. Local CLI can enable/disable Tailscale SSH (`tailscale set --ssh=true`), but repeated popups may be governed by the tailnet ACL's SSH `action`.
- Tailscale CLI is not enough for this fix: ACL edits and machine key-expiry toggles are Admin Console/API concerns. Use CLI for local evidence (`tailscale debug prefs`, `tailscale set --ssh=true`), then move to Admin Console or the policy API for persistent policy changes.
- `check` is not a bug by itself. It is the intentional mode for access paths that should require periodic user presence. Use `accept` only when that trust boundary is appropriate.
- Tailscale docs define `check` as periodic reauthentication controlled by `checkPeriod`; when omitted, the default is currently 12 hours. If the desired policy is still check mode, set `checkPeriod` explicitly so the intended interval is visible in code review.
- A control-plane bug reported in tailscale/tailscale#16541 (Jul 2025) caused check-mode SSH to ask for auth on every connection; the observed workaround was adding/changing `checkPeriod` to force netmap propagation, and the issue was later fixed server-side. If symptoms match "every SSH request asks auth," inspect ACL `ssh` rules before blaming node key expiry.
- If the popup continues after policy changes, next suspects are machine key expiry, device login/session expiry, or an app-owned OAuth popup misclassified as Tailscale-owned.
- In the JSON editor, avoid accidental edits from browser find/key events; the visual editor is safer for a simple check-mode toggle.
- Machine key expiry is checked separately under **Machines → node → key expiry**; it is not the same as SSH check mode.

## Preserve the local lesson before pruning

If this workflow was extracted from a private/local skill, keep the old source until the public-safe skill has absorbed the durable pieces:

- local evidence can look healthy while ACL check mode is the real cause;
- Admin Console or policy API owns the persistent `action` / `checkPeriod` change;
- `accept` vs `check` is a trust-boundary decision, not a universal fix;
- key expiry is a separate fallback branch;
- record post-fix evidence somewhere durable when the policy change affects an operational environment.

After those lessons are present in the public skill, archive the old private note instead of leaving an active duplicate that can drift.

## Useful links

- Tailscale SSH docs: `https://tailscale.com/kb/1193/tailscale-ssh`
- Auth/key-expiry docs: `https://tailscale.com/kb/1085/auth-keys`
- Tags docs: `https://tailscale.com/kb/1068/tags`
