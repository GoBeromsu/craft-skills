---
name: obsidian-cli
description: Operate an Obsidian vault through the `obsidian-cli` binary — note reads, writes, searches, moves, and property edits — when an Obsidian-aware command is safer than raw filesystem access. Use when a workflow must read, create, search, or inspect vault notes via the CLI, verify a note materialized after a write, or triage `Vault not found` and `obsidian` vs `obsidian-cli` wrapper confusion. Not for reading files outside the vault or destructive vault cleanup without explicit current-turn approval.
metadata:
  version: 1.0.0
---

# obsidian-cli

## Overview

Use the installed `obsidian-cli` binary to operate an Obsidian vault when an Obsidian-aware command is safer than raw filesystem access. Treat `${OBSIDIAN_VAULT_PATH}`, `${OBSIDIAN_VAULT_NAME}`, and `${OBSIDIAN_CLI_PATH}` as the source of truth for the vault; never hardcode a host-specific vault root or vault name in skill instructions, scripts, examples, or reports.

## When to Use

- A workflow asks to read, create, search, move, open, or inspect notes in the vault through the Obsidian CLI.
- Another skill requires Obsidian-aware verification after writing a vault note.
- A workflow reports `Vault not found`, missing nested output, stale Obsidian wrapper behavior, or confusing `obsidian` versus `obsidian-cli` command results.
- Use the `obsidian-doctor` skill instead when the task is specifically plugin/template/API debugging.

**NOT for:** reading files outside the vault; destructive vault cleanup without explicit current-turn approval; bulk raw asset operations where an Obsidian-aware operation adds no safety.

## Core Process

1. Resolve runtime prerequisites before touching the vault.
   ```bash
   : "${OBSIDIAN_VAULT_PATH:?set OBSIDIAN_VAULT_PATH}"
   : "${OBSIDIAN_VAULT_NAME:?set OBSIDIAN_VAULT_NAME}"
   : "${OBSIDIAN_CLI_PATH:=obsidian-cli}"
   "$OBSIDIAN_CLI_PATH" --version
   "$OBSIDIAN_CLI_PATH" print-default
   ```
   Pass only when the command reports the expected default vault and the path matches `${OBSIDIAN_VAULT_PATH}`.

2. Use the current `obsidian-cli` command surface.
   ```bash
   "$OBSIDIAN_CLI_PATH" print-default
   "$OBSIDIAN_CLI_PATH" list --vault "${OBSIDIAN_VAULT_NAME}" "Daily Notes"
   "$OBSIDIAN_CLI_PATH" print --vault "${OBSIDIAN_VAULT_NAME}" "Daily Notes/2024-01-15.md"
   "$OBSIDIAN_CLI_PATH" search-content --vault "${OBSIDIAN_VAULT_NAME}" "query text"
   ```
   Treat legacy `obsidian vault-info/read/eval/files/property:*` examples as invalid for this skill unless the installed `obsidian-cli` binary explicitly documents those commands in `--help` output.

3. Prefer exact vault-relative paths when the target is known. Use name-based lookup only when the note title is intentionally ambiguous and the command supports that mode.

4. For generated notes or nested paths, verify materialization with a filesystem readback under `${OBSIDIAN_VAULT_PATH}` after the CLI command returns success.
   ```bash
   test -f "${OBSIDIAN_VAULT_PATH}/Roundup/2024-01-15 - GDR.md"
   "$OBSIDIAN_CLI_PATH" print --vault "${OBSIDIAN_VAULT_NAME}" "Roundup/2024-01-15 - GDR.md"
   ```
   If `create` returns success but the nested file is absent, use a bounded direct write to the already-verified exact path, then repeat the readback.

5. For frontmatter or wikilink-sensitive edits, verify both CLI output and exact filesystem content. If a wikilink scalar is serialized into a list or loses one bracket layer, patch only that exact frontmatter value back to the canonical scalar form.

6. For `Vault not found` or wrapper confusion, distinguish binaries before changing anything.
   ```bash
   command -v obsidian-cli
   command -v obsidian || true
   "$OBSIDIAN_CLI_PATH" print-default
   ```
   Do not use the Obsidian.app wrapper as a substitute for `obsidian-cli` in cron or headless workflows.

7. Avoid deletion, trash, prune, unlink, or cleanup primitives unless the operator explicitly approved the exact target in the current turn. Report the target path and approval source before executing any destructive command.

## Requirements

- `obsidian-cli` v0.2.3 or newer, available through `${OBSIDIAN_CLI_PATH}` or `PATH`.
- `${OBSIDIAN_VAULT_PATH}` points to the vault root; `${OBSIDIAN_VAULT_NAME}` is the registered vault name.
- The target vault is registered as the default vault for `obsidian-cli print-default`.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The CLI printed success, so the note exists." | Nested `create` calls can report success without materializing the file. Verify the exact filesystem path and print the note back. |
| "The `obsidian` binary is close enough." | The Obsidian.app wrapper and `obsidian-cli` expose different command surfaces. Use the binary verified by `obsidian-cli --version` and `print-default`. |
| "A full path in the example is clearer." | Host-specific paths leak runtime state. Use `${OBSIDIAN_VAULT_PATH}` plus vault-relative paths. |
| "Search output is enough to identify the note." | Search can be broad or stale. Verify the final candidate with `print` or exact readback before editing. |
| "Cleanup is part of the smoke test." | Vault deletion requires explicit current-turn approval for the exact target. Leave smoke artifacts in place or ask for approval when interactive. |

## Red Flags

- A skill, script, or example contains a literal home directory or vault root instead of `${OBSIDIAN_VAULT_PATH}`.
- A cron/headless workflow invokes `obsidian` when the verified runtime command is `obsidian-cli`.
- Completion is reported after a write without exact readback evidence.
- A wikilink frontmatter edit is trusted from stdout alone.
- Any vault file is deleted, trashed, moved, or unlinked without explicit current-turn approval.

## Verification

- [ ] `"$OBSIDIAN_CLI_PATH" --version` reports the expected installed CLI version.
- [ ] `"$OBSIDIAN_CLI_PATH" print-default` reports the expected vault and matches `${OBSIDIAN_VAULT_PATH}`.
- [ ] The target note is verified with `print` or exact filesystem readback after any write.
- [ ] No host-specific path or secret appears in changed package files.
- [ ] Destructive operations have explicit current-turn approval for the exact target, or are skipped.
