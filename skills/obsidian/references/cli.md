# Obsidian CLI coordination

## Native owner

Discover the official `obsidian-cli` skill by package identity before selecting a vault-aware command. Its executable is `obsidian`; the native skill owns the command catalog, syntax, app prerequisite, and CLI-specific format details. This local reference does not copy those mechanics or designate a second CLI.

If the native skill, executable, app bridge, or requested command is unavailable, report that capability gap. Do not invent a generic writer or substitute an unrelated binary.

## Local composition

- Resolve the exact vault, authorized effect, and native Obsidian mutation surface before any write. Use [target-vault and native-surface authorization](markdown.md#target-vault-and-native-surface-authorization) and [exact non-Markdown destination readback](markdown.md#non-markdown-targets-and-destination-readback) for those boundaries.
- Compose the native CLI with `obsidian-markdown` for note format decisions and the applicable target-vault/OMS or personal policy owner; a command surface does not grant write authority.
- Use [`doctor.md`](doctor.md) for plugin, template, and API diagnostics. Use [`sync.md`](sync.md) for headless `ob` pairing, lifecycle, supervisor, and backup evidence. Desktop-app Sync state remains an operation of the native CLI skill.

## Result evidence

The app bridge can return empty output with exit code 0. Treat an empty result as indeterminate, never as zero or absence; retry a bounded number of times and report the outcome. Do not declare a capability unavailable after one failed probe; confirm with a second, different probe.

After a mutation, exact source and destination readback remains required. A successful exit code or a filesystem title match is not materialized content or proof of the intended destination; use the readback owner above and disclose unavailable app/index evidence.

## Verification

- [ ] The native `obsidian-cli` skill was discovered by identity and the executable is `obsidian`.
- [ ] The target vault, authorized effect, and native surface were resolved.
- [ ] Empty output was retried before interpretation, or the result was reported as indeterminate.
- [ ] Exact readback and any app/index or renderer gap were reported.
