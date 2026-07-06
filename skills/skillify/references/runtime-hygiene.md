# Runtime Hygiene: Validators & Secrets Remediation

The Layer-1 validator playbook, plus the emergency sequence for a real secret or `.env`
value that reached a commit.

## Table of Contents

1. [Per-skill secrets rule](#1-per-skill-secrets-rule)
2. [Validator playbook](#2-validator-playbook)
3. [Diff-mode pitfall](#3-diff-mode-pitfall)
4. [Emergency cleanup: a secret was committed](#4-emergency-cleanup-a-secret-was-committed)

---

## 1. Per-skill secrets rule

Every access path, API key, OAuth token, and host-specific value lives in a per-skill
`.env` at `$SKILL_DIR/.env` (gitignored). Commit only `$SKILL_DIR/.env.example` with
placeholder values; document required variable names in `SKILL.md`. Never hardcode real
values in `SKILL.md`, references, scripts, tests, evals, or examples.

```gitignore
.env
.env.*
!.env.example
!**/.env.example
```

Do not paste secret values into chat, commit messages, PR bodies, logs, summaries, or skill
notes — report only path names, commit ids, and redacted labels.

## 2. Validator playbook

Run both scripts before every commit that touches a skill package:

```bash
# Package format: frontmatter shape, name==dir, semver, CHANGELOG presence, no nested SKILL.md.
python3 skills/skillify/scripts/validate-skill-format.py --diff-base origin/main...HEAD

# Secret / real-path leakage on newly changed lines.
python3 skills/skillify/scripts/validate-runtime-hygiene.py --diff-base origin/main...HEAD
```

Both run in CI in `--diff-base` mode: only packages changed in the PR are enforced. Run
either script without `--diff-base` for a full non-blocking inventory of legacy gaps
(`validate-skill-format.py --advisory`).

**Guard-first sequencing.** When a hygiene gap is discovered in already-committed content,
add or update the guard before doing broad cleanup, and keep the guard scoped to newly
changed lines (`--diff-base origin/main...HEAD`) so old debt never blocks an unrelated PR.
For a large cleanup, prefer two separate PRs: one adds the guard + tests + CI step, the
next externalizes the legacy paths/secrets it now catches. In cleanup PRs, keep prose
examples as placeholders (`<VAR>`, `${VAR}`) and executable code as environment lookups
(`os.environ[...]`, shell `${VAR:?message}`).

Post-merge, re-sync `main` and rerun both scripts against it; confirm `git status --short
--branch` is clean or explicitly report a remaining stash.

## 3. Diff-mode pitfall

`--diff-base` must validate the content that would be committed, not a stale `HEAD`
snapshot. A three-dot range like `origin/main...HEAD` passed directly to `git diff` can
miss uncommitted cleanup. Resolve the range to its merge base first, then diff that base
against the current worktree — both validators already implement this via
`diff_compare_base()`. Regression-test shape when changing either script: a clean base
commit; a next commit that adds a leaked value; a worktree that replaces it with a
placeholder; `--diff-base <base>` must PASS against the worktree state, and a negative
case with an uncommitted leak must FAIL.

A line containing an env placeholder can still contain a second hardcoded value on the
same line — do not exempt a whole line just because `${VAR}` appears somewhere in it.

## 4. Emergency cleanup: a secret was committed

Use this sequence the moment a real secret, token, or `.env` value reaches a commit. A PR
opened after the leak does not remove it from history — cleanup requires a history rewrite
plus a force push.

1. Stop other work on the repo and preserve current state:

   ```bash
   git status --short --branch
   git fetch --all --prune
   ```

2. Identify tracked/current/history env paths without printing values:

   ```bash
   git ls-files | grep -E '(^|/)\.env($|\.)|\.env\.example$|env\.example$' || true
   git rev-list --objects --all | awk '{print $2}' | grep -E '(^|/)\.env($|\.)|\.env\.example$|env\.example$' | sort -u || true
   ```

3. Rewrite local history to remove the real env file(s). Keep `.env.example` only if it
   holds placeholders; if in doubt, strip it from history too and recreate a clean example
   afterward.

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

   `git filter-repo` removes the `origin` remote by design — restore it before pushing.

4. Recreate the safe ignore/example policy if needed, then commit it:

   ```bash
   git diff --check
   git add .gitignore '**/.env.example'
   git commit -m "chore: keep env examples while ignoring real env files"
   ```

5. Verify history again without printing values (rerun the step-2 commands).

6. Force-push the rewritten refs only with explicit current-turn approval. State the exact
   refs being rewritten and why; prefer `--force-with-lease`:

   ```bash
   git push --force-with-lease origin main
   # Include other published branches only if they also contain the leaked path.
   ```

7. After force-push, verify remote refs and tell the user to rotate/revoke the exposed
   secret immediately — a history rewrite alone does not invalidate a leaked credential. Do
   not claim GitHub caches or clones are clean unless separately verified.
