# VM Lifecycle: vmx Edits, Locked State, ARM Guests

State and configuration rules for the VM itself, separate from the in-guest input mechanics in `vnc-input.md`.

## Table of Contents

1. [vmx edits only survive while Fusion is quit](#1-vmx-edits-only-survive-while-fusion-is-quit)
2. [Locked VM: open the bundle, don't vmrun start it](#2-locked-vm-open-the-bundle-dont-vmrun-start-it)
3. [Closing the console window suspends, it doesn't stop](#3-closing-the-console-window-suspends-it-doesnt-stop)
4. [ARM guest vmx: PCIe slots and MAC checks](#4-arm-guest-vmx-pcie-slots-and-mac-checks)

---

## 1. vmx edits only survive while Fusion is quit

Fusion holds the running VM's configuration in memory and rewrites the entire `.vmx` from that in-memory copy whenever a Settings window closes or the app quits.
An edit made to the `.vmx` file while Fusion is open — even with the VM powered off — is silently overwritten the next time any Settings window for that VM closes.

- Fully quit `Fusion.app` (not just close the VM window) before hand-editing a `.vmx`.
- Reopen Fusion only after the edit; do not open the VM's Settings window until confirming the edit took (`grep` the line back out of the file).
- Never touch `encryption.*`, `vtpm.*`, or `managedVM.*` keys by hand on an encrypted VM — they are cryptographic state tied to the Mac's keychain and Fusion's own bookkeeping; a manual edit can make the VM unbootable. Change encryption/vTPM settings only through Fusion's UI.

## 2. Locked VM: open the bundle, don't vmrun start it

A VM can come back from a Fusion relaunch (0 windows open) in a "locked" state.
Running `vmrun start` against a locked VM does not recover it correctly.
Instead, open the `.vmwarevm` bundle itself:

```bash
open "${VM_BUNDLE_PATH}/VM Name.vmwarevm"
```

This routes through Fusion's GUI, which restores the vTPM key from the keychain (required for an encrypted VM to boot at all) and resumes the VM automatically.
`vmrun start` bypasses that keychain step.

## 3. Closing the console window suspends, it doesn't stop

Closing a Fusion VM's console window while it's running triggers a suspend, not a power-off — the VM resumes from that suspended state on next open rather than cold-booting.
This matters for two downstream effects to expect and handle, not treat as new failures:

- A CD/DVD device that was connected pre-suspend can come back disconnected after resume (see `troubleshooting.md` for the `installTools` reconnection pattern this causes).
- `vmrun getGuestIPAddress` and other guestinfo-based queries can return `unknown` for a short window after resume while the Tools guestinfo channel re-establishes.

## 4. ARM guest vmx: PCIe slots and MAC checks

- An ARM64 guest's `.vmx` uses `pcieRootPort` slot assignments for its virtual PCIe topology; don't copy device-slot numbering from an x86 vmx template — assign the next free `pciBridgeN.pciSlotNumber` / `pcieRootPortN.pciSlotNumber` a device actually needs instead of reusing an occupied slot.
- Setting a custom static MAC address (`ethernet0.address`) outside VMware's registered OUI range requires `ethernet0.checkMACAddress = "FALSE"` in the same `.vmx`, or Fusion refuses the non-VMware-OUI address at power-on.
