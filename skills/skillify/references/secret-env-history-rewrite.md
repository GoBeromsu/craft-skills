# Secret / `.env` Hygiene and History Rewrite

Use this when a craft-skills skill, script, reference, or example accidentally commits real runtime configuration, API keys, OAuth tokens, credentials, or `.env` content.

## Rules

- Commit only `.env.example` files with placeholders. Never commit real `.env`, `.env.*`, tokens, account IDs that grant access, private keys, session tokens, or machine-specific config values.
- `.gitignore` should ignore real env files while explicitly allowing examples:

```gitignore
.env
.env.*
!.env.example
!**/.env.example
```

- If a secret reached GitHub, history cleanup is not enough. Rotate/revoke the exposed secret immediately.
- Do not paste secret values into chat, commit messages, PR bodies, logs, summaries, or skill notes. Report only path names, commit ids, and redacted labels.

## Emergency Cleanup Sequence

1. Stop normal feature work and preserve the current repo state.

```bash
git status --short --branch
git fetch --all --prune
```

2. Identify tracked/current/history env paths without printing values.

```bash
git ls-files | grep -E '(^|/)\.env($|\.)|\.env\.example$|env\.example$' || true
git rev-list --objects --all | awk '{print $2}' | grep -E '(^|/)\.env($|\.)|\.env\.example$|env\.example$' | sort -u || true
```

3. Rewrite local history to remove real env files. Keep `.env.example` only if it contains placeholders; if in doubt, remove env examples from history too and recreate a clean placeholder example afterward.

```bash
REMOTE_URL=$(git remote get-url origin)
printf '%s\n' "$REMOTE_URL" > /tmp/craft-skills-origin-url.txt

git filter-repo --force \
  --invert-paths \
  --path .env \
  --path-glob '*/.env' \
  --path-glob '.env.*' \
  --path-glob '*/.env.*'

git remote add origin "$(cat /tmp/craft-skills-origin-url.txt)" 2>/dev/null || \
  git remote set-url origin "$(cat /tmp/craft-skills-origin-url.txt)"
```

4. Recreate safe ignore/example policy if needed.

```bash
# Ensure .gitignore ignores real env files and allows examples.
# Then commit the .gitignore / clean .env.example changes.
git diff --check
git add .gitignore '**/.env.example'
git commit -m "chore: keep env examples while ignoring real env files"
```

5. Verify history again without printing values.

```bash
git rev-list --objects --all | awk '{print $2}' | grep -E '(^|/)\.env($|\.)|\.env\.example$|env\.example$' | sort -u || true
```

6. Force-push rewritten refs only with explicit current-turn approval. State the exact refs being rewritten and why.

```bash
git push --force-with-lease origin main
# Include other published branches only if they also contain the leaked path.
```

7. After force-push, verify remote refs and tell the user to rotate/revoke any exposed secrets. Do not claim GitHub/cache/clone copies are clean unless separately verified.

## Pitfalls

- A PR after the leak does not remove leaked history. The cleanup requires history rewrite + force push.
- `.env.example` is allowed only when it contains placeholders. A file named `.env.example` can still leak secrets.
- `git filter-repo` removes the `origin` remote by design; restore it before pushing.
- Force push is destructive. Get explicit approval and prefer `--force-with-lease` when possible.
