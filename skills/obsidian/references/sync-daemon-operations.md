# Headless Sync Daemon Operations

Use a process supervisor only after the one-shot pull-only and bidirectional verification gates pass.
The supervisor owns process lifetime; `ob` owns sync configuration.

## Contents

- [Existing installation](#existing-installation)
- [Environment](#environment)
- [pm2](#pm2)
- [Remote inspection](#remote-inspection)
- [Stop and recover](#stop-and-recover)
- [Health evidence](#health-evidence)

## Existing installation

Inspect the registered process definition, binary, vault path, restart settings, logs, and OS boot integration before adapting an existing replica.
Preserve observed behavior and privileges; change only the necessary replica-specific paths, binaries, or approved boot wiring.
Treat the ecosystem snippet below as an example for a missing definition, not permission to overwrite an existing definition or start a duplicate process.
Verify the exact local and remote vault, their contents, expected initial transfer direction, and a usable recovery point using [Sync preflight](sync.md#1-preflight).
An empty remote does not authorize deleting populated local content, and pull-only still propagates remote deletions.
Account authentication, vault pairing, and credential access scope are separate: a distinct remote does not prove the credentials cannot access another vault.
Keep login and encryption secrets in the supported interactive flow, outside shared configuration, command arguments, and evidence logs.

## Environment

Resolve these values on the replica:

```bash
: "${OBSIDIAN_CLI_PATH:=ob}"
: "${OBSIDIAN_VAULT_PATH:?set vault path}"
: "${OBSIDIAN_SYNC_PROCESS_NAME:=ob-sync}"
: "${PM2_LOG_DIR:=${HOME}/.pm2/logs}"
```

Do not copy an ecosystem file between replicas without re-resolving the vault path and binary path.

## pm2

Create an ecosystem file outside the vault:

```javascript
module.exports = {
  apps: [{
    name: process.env.OBSIDIAN_SYNC_PROCESS_NAME || "ob-sync",
    script: process.env.OBSIDIAN_CLI_PATH || "ob",
    args: ["sync", "--path", process.env.OBSIDIAN_VAULT_PATH, "--continuous"],
    autorestart: true,
    restart_delay: 5000,
    max_restarts: 10,
    kill_timeout: 10000,
    time: true,
    env: {
      OBSIDIAN_VAULT_PATH: process.env.OBSIDIAN_VAULT_PATH,
    },
  }],
};
```

Start once from the reviewed file, save the live definition, and inspect it:

```bash
pm2 start "${HOME}/.config/pm2/ob-sync.config.cjs"
pm2 save
pm2 describe "${OBSIDIAN_SYNC_PROCESS_NAME}"
pm2 logs "${OBSIDIAN_SYNC_PROCESS_NAME}" --lines 100 --nostream
```

After registration, restart by process name rather than by an old ecosystem-file path:

```bash
pm2 restart "${OBSIDIAN_SYNC_PROCESS_NAME}" --update-env
pm2 save
```

`pm2 save` updates the boot-time process dump.
Confirm the boot integration separately with the supervisor’s supported startup command for the operating system.

Keep existing Git backup ownership separate from Sync: observe its actual trigger, branch, remote, retention, and failure reporting before making an approved adaptation.
Do not infer a backup cadence from continuous Sync or add a scheduler to fill an unknown; use the Git workflow owner for unresolved backup behavior.

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

## Health evidence

A healthy daemon has:

- Supervisor state is `online` with a stable restart count compared with the observed baseline.
- A recent successful sync heartbeat is present.
- `ob sync-status` points at the exact intended vault path.
- No concurrent Obsidian desktop process uses the same replica vault.
- Git status and file count remain plausible after a controlled one-shot check.
- An authorized test note reaches the user's device, and a controlled edit there returns to the exact replica with content readback in both directions.
- After an authorized process restart, the same pairing and controlled content flow still work without new errors or a rising restart count.

Supervisor health alone does not prove Sync, restart recovery, or backup success.
For the separate Git backup, read the intended content from the actual remote branch and revision after its observed trigger; a local commit is not remote-backup evidence.
Report each unavailable content, restart, or backup check as unverified rather than inferring it from `online`.
