# VNC Input: Wake Protocol and KEYMAP Pitfalls

The mechanics of driving a VMware Fusion guest through VNC keystrokes and mouse input, once [the SKILL.md body](../SKILL.md) has established that VNC is the only available channel.

## Table of Contents

1. [Channel setup](#1-channel-setup)
2. [Wake before every burst](#2-wake-before-every-burst)
3. [KEYMAP pitfalls](#3-keymap-pitfalls)
4. [Timing and partial-key recovery](#4-timing-and-partial-key-recovery)
5. [Host-side capture](#5-host-side-capture)

---

## 1. Channel setup

Enable VNC in the `.vmx` (edit only while Fusion is fully quit — see `vmx-lifecycle.md`):

```
RemoteDisplay.vnc.enabled = "TRUE"
RemoteDisplay.vnc.port = "5901"
RemoteDisplay.vnc.password = "${VNC_PASSWORD}"
```

Drive it with `vncdotool` (`vncdo -s 127.0.0.1::5901 -p "${VNC_PASSWORD}" <command>`).
Each invocation opens a fresh connection and closes it, which is why the wake step in §2 must run inside the same invocation as the real action, not as a separate prior call.

## 2. Wake before every burst

A guest display that has gone to sleep returns a solid black frame on capture — this looks identical to a dead renderer but is not one.
Diagnose display-sleep first, always: send a wake burst immediately before any capture or interaction, in the same command chain, then act.

```bash
vncdo -s 127.0.0.1::5901 -p "${VNC_PASSWORD}" move 512 400 key shift pause 2 capture out.png
```

Only treat a still-black capture *taken right after a fresh wake* as evidence of a real renderer fault worth a cold boot.
Skipping the wake and concluding the renderer died from a single black frame is the single most common false alarm in this workflow.

## 3. KEYMAP pitfalls

`vncdotool`'s `KEYMAP` table (in its `client.py`) is incomplete and has at least one wrong entry.
Sending an unmapped or misparsed key name doesn't just fail that keystroke — the argument parser throws, which hangs or drops the whole Twisted-reactor connection, killing every queued command in that invocation.

| Symptom | Root cause | Fix |
|---|---|---|
| `key semicolon` (or bare `key ;`) hangs, then "Connection lost" | `"semicolon"` is not a registered `KEYMAP` name | Send `;` as a quoted single character resolved via its ordinal: `key ';'`, or `key 'shift-;'` if the layout needs shift for it |
| Typed `/` comes out as `\` | `KEYMAP`'s `"slash"` entry is mismapped to backslash | Never send `/` via `key` — use `type '/'` (or embed it in a larger `type` string) instead |
| An uppercase letter or shifted symbol lands lowercase/unshifted | The VNC server does not synthesize shift on its own for a bare `key X` | Compose the shift explicitly: `key 'shift-x'` for a capital, or `key 'shift-;'`/`key 'shift-1'` etc. for a shifted symbol |

General rule: prefer `type '<literal string>'` for plain alphanumeric and common punctuation — it goes through a different code path than single-key `key` sequences and sidesteps most `KEYMAP` gaps.
Reserve `key` for modifiers, function keys, and navigation (`enter`, `esc`, `tab`, `ctrl-a`, `alt-y`) where `type` doesn't apply.

## 4. Timing and partial-key recovery

- A long `vncdo` chain that runs past a shell timeout leaves the connection killed mid-sequence and can leave a modifier key logically "held" on the guest side. After any killed or timed-out chain, wait a few seconds, then send `key ctrl-a` (select-all) before retyping into a text field — it clears both stray held-key state and whatever partial text was typed, giving a known-clean starting point.
- Verify a text field's actual content with a capture before trusting that a `type`/`key` sequence landed correctly — a guest that dropped a keystroke silently produces a plausible but wrong string.
- After stopping a backgrounded `vncdo` process, confirm it actually exited (`pgrep -fl vncdo`, `lsof -nP -iTCP:5901`) before assuming a second concurrent client might be corrupting the session — a shell-timeout backgrounding a command can outlive the wrapper that started it, but it still exits on its own once the connection drops.

## 5. Host-side capture

For a second, VNC-independent view of the guest console (e.g. to cross-check a suspicious VNC capture), use the host's own screen capture against the Fusion console window, and keep the host awake for the duration of a long unattended run:

```bash
caffeinate -i -w $$ &
screencapture -l"$(osascript -e 'tell app "System Events" to id of window 1 of process "VMware Fusion"')" host_view.png
```
