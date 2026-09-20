# Obsidian CLI

## Overview

"Obsidian CLI" means the **official CLI that ships with Obsidian.app**, documented at [help.obsidian.md/cli](https://help.obsidian.md/cli). Its binary is `obsidian`. It is the default surface for every vault-aware read, inspection, link-graph, and mutation operation in this package.

The community Yakitrak [`obsidian-cli`](https://github.com/Yakitrak/obsidian-cli) is a **separate third-party binary with a different and much smaller command surface**. Despite its name it is not "the Obsidian CLI". Use it only as the headless fallback described below, and never assume a command from one binary exists on the other.

Treat `${OBSIDIAN_VAULT_NAME}` and `${OBSIDIAN_VAULT_PATH}` as the source of truth for the vault; never hardcode a host-specific vault root or vault name in skill instructions, scripts, examples, or reports.

## When to Use

- A workflow asks to read, create, search, move, inspect, or link-audit notes in the vault through the Obsidian CLI.
- Another skill requires Obsidian-aware verification after writing a vault note — especially wikilink resolution, backlinks, or unresolved links.
- A workflow reports `Vault not found`, missing nested output, or confusion between the `obsidian` and `obsidian-cli` binaries.
- Use [`doctor.md`](doctor.md) instead when the task is specifically plugin/template/API debugging.
- Use [`sync.md`](sync.md) for the headless `ob` client's pairing and daemon lifecycle; read-only Sync **state** for a vault the desktop app already syncs is owned by this file's `sync:*` commands.

**NOT for:** reading files outside the vault; destructive vault cleanup without explicit current-turn approval; bulk raw asset operations where an Obsidian-aware operation adds no safety.

## Command syntax

The official CLI does not use POSIX flags. Arguments are bare `key=value` pairs and bare switches.

```bash
obsidian <command> [key=value ...] [switch ...]
```

- `vault=<name>` targets a vault other than the active one; it is accepted by every vault-scoped command.
- `file=<name>` resolves **by name, exactly like a wikilink**. This is the correct surface for proving that `[[Some Note]]` resolves.
- `path=<folder/note.md>` is an exact vault-relative path. Prefer it when the target is known and unambiguous.
- Most commands default to the active file when both `file` and `path` are omitted.
- Quote values containing spaces: `file="My Note"`. Use `\n` and `\t` for newline and tab inside `content=`.

## Core Process

1. Resolve runtime prerequisites before touching the vault.

   ```bash
   command -v obsidian
   obsidian version
   ```

Use `obsidian version` for the version. `obsidian --version` prints help on current installations and is not a version probe. The official CLI drives the running desktop app, so it requires the documented app runtime; the community binary does not. Do not silently substitute one for the other.

### Empty output with exit code 0 is not a result

This CLI answers through the running app. When that bridge is momentarily unavailable the command still **exits 0 and prints nothing**. Observed directly: `plugins:enabled filter=core` returned 23 lines, then an empty string minutes later, then 23 lines again, with the app running the whole time; `unresolved total` and `backlinks` behaved the same way.

Treat an empty result as *indeterminate*, never as zero/absent. Before interpreting emptiness, retry until a non-empty answer appears or a bounded number of attempts is exhausted, and report which happened.

```bash
for i in 1 2 3 4 5; do
  out=$(obsidian <command> vault="${OBSIDIAN_VAULT_NAME}" 2>&1)
  [ -n "$out" ] && { printf '%s\n' "$out"; break; }
  sleep 2
done
```

This matters most for the counting and listing switches (`total`, `counts`, `format=json`), where an empty string is easily misread as `0`, and for any check whose whole purpose is to prove an absence, such as `unresolved`.

2. Resolve the vault registry and confirm the name/path mapping before note operations.

   ```bash
   obsidian vaults verbose
   obsidian vault info=path vault="${OBSIDIAN_VAULT_NAME}"
   ```

`vaults verbose` prints every known vault with its root. Match `${OBSIDIAN_VAULT_NAME}` to `${OBSIDIAN_VAULT_PATH}` before proceeding. If the mapping is unresolved, report it rather than guessing; changing the active vault requires task authority.

3. Read and inspect through the official surface.

   ```bash
   obsidian read path="Folder/Note.md" vault="${OBSIDIAN_VAULT_NAME}"
   obsidian file file="Note Name" vault="${OBSIDIAN_VAULT_NAME}"
   obsidian files folder="Folder" vault="${OBSIDIAN_VAULT_NAME}"
   obsidian outline path="Folder/Note.md" format=json vault="${OBSIDIAN_VAULT_NAME}"
   obsidian properties path="Folder/Note.md" format=yaml vault="${OBSIDIAN_VAULT_NAME}"
   obsidian property:read name=type path="Folder/Note.md" vault="${OBSIDIAN_VAULT_NAME}"
   obsidian tags path="Folder/Note.md" counts vault="${OBSIDIAN_VAULT_NAME}"
   ```

4. Audit the link graph with Obsidian's own resolver. This is the authoritative wikilink check; a filesystem title match is not equivalent, because it ignores aliases, shortest-path resolution, and the app index.

   ```bash
   obsidian links   file="Note Name" total   vault="${OBSIDIAN_VAULT_NAME}"
   obsidian backlinks file="Note Name" counts format=json vault="${OBSIDIAN_VAULT_NAME}"
   obsidian unresolved verbose format=tsv vault="${OBSIDIAN_VAULT_NAME}"
   obsidian orphans total vault="${OBSIDIAN_VAULT_NAME}"
   ```

`unresolved` is the single best post-write check after adding wikilinks: a target that fails to resolve appears there, and an empty result for the edited notes is positive evidence rather than an absence of errors.

5. Search through the indexed surface.

   ```bash
   obsidian search query="term" path="Folder" limit=20 format=json vault="${OBSIDIAN_VAULT_NAME}"
   obsidian search:context query="term" format=json vault="${OBSIDIAN_VAULT_NAME}"
   ```

Both commands are part of the official surface, but they returned empty on every attempt on the verification host even during windows when `read`, `backlinks`, `unresolved`, and `tags` all returned data, including for a term known to be present. Search depends on the core search plugin and the app's search index, so confirm it answers on the target install before relying on it, and never report an empty search as proof a term is absent. When search cannot be confirmed, fall back to `links`/`backlinks`/`unresolved` for link questions or an explicit filesystem scan for content questions, and say which surface produced the answer.

6. Mutate with the least destructive command that does the job, then read back.

   ```bash
   obsidian create  name="New Note" path="Folder" content="..." vault="${OBSIDIAN_VAULT_NAME}"
   obsidian append  path="Folder/Note.md" content="..."          vault="${OBSIDIAN_VAULT_NAME}"
   obsidian prepend path="Folder/Note.md" content="..."          vault="${OBSIDIAN_VAULT_NAME}"
   obsidian property:set name=status value=done type=text path="Folder/Note.md" vault="${OBSIDIAN_VAULT_NAME}"
   obsidian move    path="Folder/Note.md" to="Other Folder"      vault="${OBSIDIAN_VAULT_NAME}"
   obsidian rename  path="Folder/Note.md" name="New Title"       vault="${OBSIDIAN_VAULT_NAME}"
   ```

`move` and `rename` are the link-preserving surface; a raw `mv` breaks inbound wikilinks. `create` without `overwrite` will not clobber an existing file.

7. Read back every mutation exactly. A zero exit code is not completion.

   ```bash
   obsidian read path="Folder/Note.md" vault="${OBSIDIAN_VAULT_NAME}"
   test -f "${OBSIDIAN_VAULT_PATH}/Folder/Note.md"
   ```

Compare the CLI output against the filesystem bytes when the write is wikilink- or frontmatter-sensitive. The CLI's `read` output may differ from the file by a single trailing newline; treat only a content difference as a real mismatch. If a frontmatter wikilink scalar is serialized into a list or loses one bracket layer, patch only that exact value back to the canonical scalar form.

8. Read Sync state for a vault the desktop app already syncs. These are read-only; `sync on|off` mutates and needs explicit approval.

   ```bash
   obsidian sync:status  vault="${OBSIDIAN_VAULT_NAME}"
   obsidian sync:history path="Folder/Note.md" vault="${OBSIDIAN_VAULT_NAME}"
   obsidian sync:deleted total vault="${OBSIDIAN_VAULT_NAME}"
   obsidian diff filter=sync path="Folder/Note.md" vault="${OBSIDIAN_VAULT_NAME}"
   ```

An empty `sync:status` with a zero exit code is not proof of a healthy pairing. Report it as indeterminate and corroborate with `plugins:enabled filter=core` or the app UI rather than asserting a state the surface did not return.

9. Avoid deletion, trash, prune, unlink, or cleanup primitives unless the operator explicitly approved the exact target in the current turn. Report the target path and approval source before executing any destructive command.

## Headless fallback: Yakitrak `obsidian-cli`

Use this binary only when the desktop app cannot run — cron, CI, or a headless replica — and the operation is within its small surface. It is not a drop-in substitute.

```bash
: "${OBSIDIAN_CLI_PATH:=obsidian-cli}"
"$OBSIDIAN_CLI_PATH" --version
"$OBSIDIAN_CLI_PATH" --help
```

- Run only commands present in the **installed** binary's help. The surface differs across releases: v0.2.3 exposes `print-default` and has no `list-vaults`, which later versions added.
- Registry lookup on v0.2.3 is `print-default`; it reports only the default vault name and path.
- Useful reads: `print --vault <name> <path-or-name>`, `print -m` for linked mentions, `list --vault <name> <folder>`.
- `search-content` was observed returning `Cannot find note in vault` for terms that exist in the vault on v0.2.3. Do not report a negative search result from this binary as evidence of absence; re-run the query through `obsidian search` or a filesystem scan.
- It has no `backlinks`, `unresolved`, `orphans`, `property:*`, or `sync:*` equivalent. When the task needs those, the official CLI is required; say so instead of substituting a weaker check.

## Requirements

- Obsidian.app providing the `obsidian` binary, with the target commands present in the installed `obsidian help` output.
- `${OBSIDIAN_VAULT_NAME}` resolves to `${OBSIDIAN_VAULT_PATH}` in `obsidian vaults verbose`.
- `${OBSIDIAN_CLI_PATH}` or an `obsidian-cli` binary on `PATH` only when the headless fallback is selected.
- Use the [official CLI documentation](https://help.obsidian.md/cli) for `obsidian` and the [community CLI documentation](https://github.com/Yakitrak/obsidian-cli) for the Yakitrak fallback.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "`obsidian-cli` is the Obsidian CLI." | It is a third-party binary with a different, smaller surface. The official CLI is `obsidian`, documented at help.obsidian.md/cli. |
| "One probe returned nothing, so the tool is not installed." | A single failed `command -v` or `ls \| grep` can come from a flaky shell, not a missing binary. Confirm with a second, different probe before reporting a tool as unavailable. |
| "`obsidian --version` shows the version." | It prints help on current installations. Use `obsidian version`. |
| "The CLI printed success, so the note exists." | Verify the exact filesystem path and read the note back. |
| "The filenames match, so the wikilinks resolve." | Filesystem title matching ignores aliases and the app index. Prove resolution with `backlinks`/`links`/`unresolved`. |
| "Search returned nothing, so the term is absent." | Confirm the search surface actually answers on this install first. The official `search`/`search:context` returned empty for present terms on the verification host, and the community `search-content` returned `Cannot find note in vault` for terms that exist. |
| "Exit code 0 with no output means zero results." | This CLI prints nothing and exits 0 when the app bridge is momentarily unavailable. Retry before interpreting emptiness; an empty result is indeterminate, not a count of zero. |
| "A full path in the example is clearer." | Host-specific paths leak runtime state. Use `${OBSIDIAN_VAULT_PATH}` plus vault-relative paths. |
| "Cleanup is part of the smoke test." | Vault deletion requires explicit current-turn approval for the exact target. |

## Red Flags

- A skill, script, or example treats `obsidian-cli` as the official CLI, or mixes the two command surfaces.
- A tool is declared unavailable on the strength of exactly one probe.
- An empty CLI result with exit code 0 is reported as `0`, `none`, or `clean` without a retry.
- A write made with a raw filesystem tool while the app is running is trusted byte-for-byte; the app can normalize frontmatter afterward, so read the note back through the CLI.
- A skill, script, or example contains a literal home directory or vault root instead of `${OBSIDIAN_VAULT_PATH}`.
- Completion is reported after a write without exact readback evidence.
- Wikilink health is claimed from filename matching instead of `unresolved`/`backlinks`.
- An empty `sync:status` is reported as a healthy pairing.
- Any vault file is deleted, trashed, moved, or unlinked without explicit current-turn approval.

## Verification

- [ ] `obsidian version` reports the installed app version, and the required commands appear in `obsidian help`.
- [ ] Any empty-but-zero-exit result was retried before being interpreted, and the outcome of that retry is stated.
- [ ] `obsidian vaults verbose` resolves `${OBSIDIAN_VAULT_NAME}` to `${OBSIDIAN_VAULT_PATH}`; no default was changed merely for preflight.
- [ ] The target note is verified with `obsidian read` plus filesystem readback after any write.
- [ ] Wikilink claims are backed by `links`, `backlinks`, or `unresolved` output, not filename matching.
- [ ] Any use of the Yakitrak fallback names the binary, its version, and why the official CLI was unavailable.
- [ ] No host-specific path or secret appears in changed package files.
- [ ] Destructive operations have explicit current-turn approval for the exact target, or are skipped.
