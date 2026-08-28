# Changelog

- 2026-07-19 — v1.0.0: Automating a VMware Fusion guest on Apple Silicon through an empty-password VM repeatedly hit VIX guest-exec refusals, black VNC captures misdiagnosed as renderer failure, `vncdotool` KEYMAP hangs on `;`/`/`, a reverting `.vmx` edit, and a "locked" VM that wouldn't `vmrun start` → packaged the VNC-as-primary-channel workflow, the wake-before-capture protocol, the KEYMAP pitfall table, and the vmx/lifecycle rules into a new skill.
- 2026-08-28 — mutable VMware, VNC, and guest-runtime facts can invalidate general guidance → v1.1.0 adds official-docs-first evidence handling, conflict disclosure, scoped overrides, and unknown-safe stops.
- 2026-08-28 — the deleted `aside` package remained in VMware's active browser-automation hand-offs → v1.1.1 routes those requests to the active `browser` package without adding browser automation to VMware.
