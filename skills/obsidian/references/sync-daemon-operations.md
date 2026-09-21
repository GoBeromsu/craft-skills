# Headless Sync Daemon Operations

Use a process supervisor only after the one-shot pull-only and bidirectional verification gates pass.
The supervisor owns process lifetime; `ob` owns sync configuration.
Inspect the registered supervisor, process identity, executable, arguments, working directory, relevant environment, restart policy, and boot integration before changing anything.
Preserve observed settings unless their exact change is authorized; do not replace an existing supervisor with the example surface below.

## Environment

Resolve these values on the replica:

```bash
: "${OBSIDIAN_VAULT_PATH:?set vault path}"
: "${OBSIDIAN_SYNC_PROCESS_NAME:?set observed supervisor process name}"
```

Resolve the binary and log locations from the observed process definition rather than assigning defaults or repurposing the third-party CLI path.
Do not copy an ecosystem file between replicas without re-resolving the vault path and binary path.

## pm2

When the observed supervisor is pm2, inspect the registered process:

```bash
pm2 describe "${OBSIDIAN_SYNC_PROCESS_NAME}"
pm2 logs "${OBSIDIAN_SYNC_PROCESS_NAME}" --lines 100 --nostream
```

For an authorized restart, target only that registered process, retaining its environment and settings:

```bash
pm2 restart "${OBSIDIAN_SYNC_PROCESS_NAME}"
```

Do not reload a stale ecosystem file, refresh the environment, or rewrite the boot-time process dump for a restart-only task.
For initial provisioning or an approved definition change, use the actual supervisor's official guidance and inspect the resulting live definition and persistence separately.
Do not invent a restart delay, retry limit, boot integration, or backup schedule.

## Remote inspection

Keep inspection read-only until the failure mechanism is known:

```bash
: "${OBSIDIAN_SYNC_REMOTE_HOST:?set replica host}"
ssh "${OBSIDIAN_SYNC_REMOTE_HOST}" \
  'pm2 describe "$OBSIDIAN_SYNC_PROCESS_NAME"; pm2 logs "$OBSIDIAN_SYNC_PROCESS_NAME" --lines 100 --nostream'
```

Run `ob sync-setup` through an interactive terminal, not as a non-interactive remote command, because encryption setup prompts for a secret.

## Stop and recover

Contain a suspected deletion or crash loop before changing configuration:

```bash
pm2 stop "${OBSIDIAN_SYNC_PROCESS_NAME}"
```

Read the earliest relevant error, verify the local path and remote vault, and follow `sync-recovery.md`.
Do not restart repeatedly: each restart may replay the same destructive or failing state.

## Separate Git backup

Treat an existing Git backup job as a separate mechanism, not as part of Obsidian Sync.
Read its actual owner, command, schedule or trigger, repository, branch, remote destination, and push/readback behavior without replacing them.
Preserve existing include/exclude rules and protected content; do not stage unrelated files, add a schedule, push, or repair backup configuration without matching authority.
For an authorized backup check, read the expected revision and scoped content from the actual remote backup destination and compare them with the intended backup.
A local commit, successful Sync, or scheduler status does not prove remote backup content; missing remote access or revision evidence leaves backup verification incomplete.

## Health evidence

Report these independently, without upgrading liveness to content proof:

- Supervisor state is `online` with a low stable restart count.
- A recent successful sync heartbeat is present.
- `ob sync-status` points at the exact intended vault path.
- No concurrent Obsidian desktop process uses the same replica vault.
- Git status and file count remain plausible after a controlled one-shot check.
- An authorized [content roundtrip](sync.md#content-roundtrip-evidence) has source and receiving-replica readback for each tested direction.
- A scoped restart preserves the registered definition and resumes actual synchronization, demonstrated by authorized post-restart content readback rather than process status alone.
- The separate backup has [remote revision and content readback](#separate-git-backup), not merely a local commit or successful job exit.

If restart authority, native capability, note authority, or remote access is missing, name the unverified result and stop short of that effect.
