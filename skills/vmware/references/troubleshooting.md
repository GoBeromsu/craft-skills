# Troubleshooting: VIX Noise, Tools Install, Network Verification, UAC

Failure modes that look alarming but have a known, benign explanation, plus the recipes for the recurring tasks around them.

## Table of Contents

1. [DecryptWithPadding noise on an encrypted VM](#1-decryptwithpadding-noise-on-an-encrypted-vm)
2. [Empty guest password blocks all VIX guest-exec](#2-empty-guest-password-blocks-all-vix-guest-exec)
3. [installTools and the Tools CD reconnection](#3-installtools-and-the-tools-cd-reconnection)
4. [Guestinfo lag: fall back to the DHCP lease file](#4-guestinfo-lag-fall-back-to-the-dhcp-lease-file)
5. [Network verification recipe](#5-network-verification-recipe)
6. [UAC approval over VNC](#6-uac-approval-over-vnc)
7. [Typing characters cmd can't accept directly](#7-typing-characters-cmd-cant-accept-directly)

---

## 1. DecryptWithPadding noise on an encrypted VM

Every `vmrun` call against an encrypted, vTPM-backed VM (`list`, `checkToolsState`, `getGuestIPAddress`, …) logs a `DecryptWithPadding: Failed because padding is too short or too long` line to `vmware.log` on each VIX connection attempt.
This is benign per-call noise from the VIX auth handshake against the encrypted config, not evidence of a second process or an intrusion attempt.

The real trap is self-inflicted: a background watcher script that polls `vmrun list` / `checkToolsState` every few seconds produces a steady stream of this noise that reads exactly like a problem.
Prefer a **passive** watcher — one that only tails `vmware.log` for the state transition lines it actually needs (boot, reboot, Tools-status-changed) and checks for expected output/artifact files — over one that re-polls `vmrun` on a timer.
Reserve direct `vmrun` calls for the one-shot checks a human step actually needs.

## 2. Empty guest password blocks all VIX guest-exec

`vmrun -gu <user> -gp "" runProgramInGuest|typeKeystrokesInGuest|...` fails outright with `Error: The guest OS does not support empty passwords` when the guest's local account has no password set.
This is not a flag or retry problem — VIX guest-exec is categorically unavailable for that guest.
Route all in-guest interaction (typing, clicking, running commands) through VNC (`vnc-input.md`) instead; `vmrun` stays limited to VM-lifecycle operations that don't need guest auth (`start`, `stop`, `suspend`, `list`, `installTools`, `getGuestIPAddress`).

## 3. installTools and the Tools CD reconnection

`vmrun -T fusion installTools "${VMX_PATH}"` blocks until the guest's silent Tools install finishes — run it in the background and treat its return as the completion signal.
It also reconnects the Tools ISO to a CD device, which is the fix for the specific case where a suspend/resume cycle (see `vmx-lifecycle.md` §3) left the D: drive backing image disconnected and a command like `D:/setup.exe /S /v/qn` typed into a Run dialog fails with a "insert disk" style error even though the typed command itself is correct.
Re-run the command after `installTools` reconnects the device, not before.

A silent Tools install (`/S /v/qn`) typically triggers an automatic guest reboot on completion — expect a `CPU hard reset` line in `vmware.log` and a `Tools: Changing running status` transition around it, not a hang.

## 4. Guestinfo lag: fall back to the DHCP lease file

Right after a Tools install/reboot, `vmrun getGuestIPAddress -wait` can return `unknown` for a stretch while the guestinfo channel re-propagates.
Rather than waiting longer, read the NAT DHCP lease file directly for a faster, equally authoritative answer:

```bash
grep -B2 -A2 -i "${GUEST_MAC}" /var/db/vmware/vmnet-dhcpd-vmnet<N>.leases
```

`<N>` is the NAT adapter's vmnet number — `8` is Fusion's conventional default, but confirm it against the guest's actual configured network adapter rather than assuming.

Cross-check the leased IP against the guest's own `ipconfig /all` (or `ip addr`) once reachable, as the final confirmation step in §5.

## 5. Network verification recipe

Confirm guest networking end-to-end rather than assuming it from a lease alone: type the check commands into the guest via VNC, capture the console output, and read the captures back.

```bash
vncdo -s 127.0.0.1::5901 -p "${VNC_PASSWORD}" \
  move 512 400 key shift pause 1 \
  key 'super' type 'cmd' key enter pause 2 \
  type 'ping 8.8.8.8' key enter pause 5 \
  capture ping_check.png \
  type 'ipconfig /all' key enter pause 2 \
  capture ipconfig_check.png
```

Confirm: 0% packet loss on the ping, and the adapter's `Physical Address` in `ipconfig /all` matches the `ethernet0.address` configured in the `.vmx` — a mismatch there means the guest is using a different adapter than the one being configured.

## 6. UAC approval over VNC

A Korean-locale UAC prompt ("이 앱이 디바이스를 변경할 수 있도록 허용하시겠어요?") accepts `key alt-y` as the fast path (Y is the underlined accelerator for 예/Yes).
If focus is uncertain or the accelerator doesn't register, fall back to `key left` then `key enter` to select the left-hand (Yes/예) button explicitly rather than retrying the same accelerator blind.

## 7. Typing characters cmd can't accept directly

When a target field or shell rejects a character sent via `key` (a `KEYMAP` gap, see `vnc-input.md` §3) and `type` also misbehaves for it in context, use the guest shell's own completion instead of fighting the input layer — e.g. in `cmd`, type a distinguishing prefix and press `Tab` to let the guest complete a path segment containing an underscore or other awkward character, rather than trying to type that character directly.
