---
name: vmware
description: Automates a VMware Fusion VM on Apple Silicon through VNC keystroke and mouse input when vmrun's guest-exec is unavailable — an empty guest password, an encrypted vTPM VM, or any headless GUI task in the guest console. Use when a VNC capture keeps coming back black, vncdotool hangs or drops the connection on a key like `;`, a vmx edit reverts after Fusion restarts, a VM shows as "locked" and won't start, VMware Tools install needs a UAC prompt driven through, or vmrun/VIX fails with "guest OS does not support empty passwords". Not for browser-based web automation — use `aside` — and not for tailnet/SSH connectivity between hosts — use `tailscale`.
metadata:
  version: 1.0.0
---

# vmware

Drives a VMware Fusion guest on Apple Silicon when `vmrun`'s guest-exec calls (`runProgramInGuest`, `typeKeystrokesInGuest`, …) are unavailable — most commonly because the guest account has an empty password, which VIX refuses outright regardless of retries.
The fallback channel is VNC: mouse and keystroke input plus screen capture, driven through `vncdotool`.
Success looks like a guest reliably clicked, typed into, and verified through VNC, with `vmrun` reserved for VM-lifecycle operations (start, suspend, `installTools`, `getGuestIPAddress`) that don't need guest auth.

## Task gate

Load the reference that matches the task before acting — each owns one slice of the failure space:

| Task | Read |
|---|---|
| Typing/clicking in the guest, a black capture, a hung or dropped `vncdo` connection | [`references/vnc-input.md`](references/vnc-input.md) |
| Editing the `.vmx`, a VM stuck "locked", suspend/resume behavior, ARM guest PCIe/MAC config | [`references/vmx-lifecycle.md`](references/vmx-lifecycle.md) |
| `DecryptWithPadding` log noise, Tools install/reboot, network verification, UAC, guestinfo lag | [`references/troubleshooting.md`](references/troubleshooting.md) |

## Core rules

- **VIX guest-exec is not the channel here.** Confirm early whether `vmrun -gu <user> -gp "<pass>" runProgramInGuest` (or similar) is even reachable. An empty guest password makes it categorically unavailable, not flaky — stop retrying flags and switch to VNC for every in-guest action. `vmrun` still owns lifecycle calls that don't need guest auth: `start`, `stop`, `suspend`, `list`, `installTools`, `getGuestIPAddress`. Detail: `troubleshooting.md` §2.
- **A black VNC capture means the display slept, not that the renderer died.** Send a wake burst (mouse move + a keypress) in the same command as the capture, every time, before drawing any conclusion about renderer health. Detail: `vnc-input.md` §2.
- **`vncdotool`'s KEYMAP has real gaps.** `key semicolon`/`key ;` hangs the connection because the name isn't registered; `key slash` sends a backslash because that entry is mismapped. Prefer `type '<string>'` for literal text and punctuation; reserve `key` for modifiers and navigation, quoting single punctuation characters (`key ';'`, `key 'shift-;'`) when `key` is unavoidable. Detail: `vnc-input.md` §3.
- **A `.vmx` edit only survives while Fusion is fully quit.** Any Settings window closing, or the app itself closing, rewrites the whole file from memory — an edit made while Fusion is running is silently lost. Never hand-edit `encryption.*`/`vtpm.*`/`managedVM.*` on an encrypted VM. Detail: `vmx-lifecycle.md` §1.
- **A "locked" VM is unlocked by opening the bundle, not `vmrun start`.** `open "<name>.vmwarevm"` routes through Fusion's GUI, which restores the vTPM key from the keychain; `vmrun start` skips that step and can leave an encrypted VM unable to boot. Detail: `vmx-lifecycle.md` §2.
- **Closing the console window suspends the VM, it doesn't power it off.** Expect a CD device to come back disconnected and `getGuestIPAddress` to lag after the next resume — both have known fixes, not new bugs. Detail: `vmx-lifecycle.md` §3, `troubleshooting.md` §3–§4.
- **`DecryptWithPadding` noise on every VIX call against an encrypted VM is benign.** Before treating a steady stream of it as an intrusion or concurrency bug, check whether a background watcher is polling `vmrun` on a timer — that's almost always the actual source. Prefer a passive, log-tailing watcher over one that re-polls `vmrun`. Detail: `troubleshooting.md` §1.
- **Verify guest state by reading it back, not by assuming the command landed.** After typing a command or a credential-adjacent field, capture and read the result — a dropped keystroke from a `KEYMAP` gap produces plausible-looking but wrong output. Cross-check network state against the host's own DHCP lease file when `vmrun` guestinfo lags. Detail: `troubleshooting.md` §4–§5.

## Requirements

- `vmrun` (ships with VMware Fusion) — VM lifecycle calls.
- `vncdotool` (`vncdo`) — guest keystroke/mouse input and screen capture over VNC.
- `hdiutil` — host-side inspection of an ISO's contents without touching the guest.

## Anti-patterns

- Concluding the renderer crashed from one black capture → wake the guest first, in the same command, and re-capture before escalating.
- Sending `key semicolon` or `key slash` and treating the resulting hang as a network/VM problem → both are known `vncdotool` `KEYMAP` gaps; use `type` or a quoted single-character `key`.
- Retrying `vmrun ... -gp ""` guest-exec calls with different flags → an empty guest password blocks VIX guest-exec entirely; switch to VNC for all guest interaction instead.
- Editing a running VM's `.vmx` without fully quitting Fusion first → the edit is silently overwritten on the next Settings-window close.
- Hand-editing `encryption.*`/`vtpm.*`/`managedVM.*` keys on an encrypted VM → change these only through Fusion's UI; a manual edit can make the VM unbootable.
- `vmrun start` on a VM reported "locked" → open the `.vmwarevm` bundle instead so Fusion restores the vTPM key from the keychain.
- A background watcher polling `vmrun list`/`checkToolsState` every few seconds → prefer a passive watcher that tails `vmware.log` for the specific transition it's waiting on.
- Trusting a typed command or field landed correctly without a capture to confirm it → verify by reading the guest state back, especially right after a killed or timed-out `vncdo` chain.

## Boundaries

This skill owns getting input into, and state out of, a VMware Fusion guest console on Apple Silicon.
It does not cover browser automation inside a guest or on the host (`aside`), or cross-host connectivity used to reach a remote hypervisor (`tailscale`) — load those instead once the target is a web page or a different machine rather than this guest's own console.

## Verification

- [ ] Every in-guest action went through VNC, not a `vmrun` guest-exec call, once an empty guest password or another VIX block was confirmed.
- [ ] Any black capture was re-taken after an explicit wake burst before being called a renderer fault.
- [ ] No punctuation was sent via a bare unquoted `key <name>` that isn't a real `KEYMAP` entry.
- [ ] Any `.vmx` edit was made with Fusion fully quit, and re-read afterward to confirm it held.
- [ ] A typed command or credential field was verified by capture, not assumed from the command that sent it.
