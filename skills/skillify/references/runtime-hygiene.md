# Runtime Hygiene: Validators & Secrets Remediation

The Layer-1 validator playbook, plus the emergency sequence for a real secret or `.env` value that reached a commit.

## Table of Contents

1. [Per-skill secrets rule](#1-per-skill-secrets-rule)
2. [Validator playbook](#2-validator-playbook)
3. [Diff-mode pitfall](#3-diff-mode-pitfall)
4. [Emergency cleanup: a secret was committed](#4-emergency-cleanup-a-secret-was-committed)

---

## 1. Per-skill secrets rule

Every access path, API key, OAuth token, and host-specific value lives in a per-skill `.env` at `$SKILL_DIR/.env` (gitignored).
Commit only `$SKILL_DIR/.env.example` with placeholder values; document required variable names in `SKILL.md`.
Never hardcode real values in `SKILL.md`, references, scripts, tests, evals, or examples.

```gitignore
.env
.env.*
!.env.example
!**/.env.example
```

Do not paste secret values into chat, commit messages, PR bodies, logs, summaries, or skill notes — report only path names, commit ids, and redacted labels.

## 2. Validator playbook

Run the relevant checks on the actual authoring snapshot before admission or an authorized commit.
Resolve and record one intended base commit:

```bash
set -e
BASE=$(git merge-base origin/main HEAD)

# Format selection unions committed, staged, unstaged and untracked changes.
python3 skills/skillify/scripts/validate-skill-format.py --diff-base "$BASE"

# Select an additional existing owner explicitly; repeat --package to add owners.
python3 skills/skillify/scripts/validate-skill-format.py --diff-base "$BASE" --package skills/skillify

# Secret / real-path leakage on newly changed lines.
python3 skills/skillify/scripts/validate-runtime-hygiene.py --diff-base "$BASE"

# Sentence-boundary line breaks (contract §4) on the changed package's Markdown; --fix reflows.
python3 skills/skillify/scripts/reflow-sentences.py skills/<skill-name>
```

The format validator maps body, references, scripts, assets and repo-root test changes to actual owners.
Every mode requires Git and the actual worktree root; `--root` is not a standalone non-Git package directory.
It rejects repeated base flags, revision ranges, noncanonical or escaping paths, nonexistent package selectors, and unresolved support ownership; input/Git failures still fail in advisory mode.
Deleted owners receive tombstone and concrete inbound-path checks; independent review still owns semantic routing and retirement adequacy.
Without either selector it scans all packages.
Add `--advisory` only for an explicitly non-blocking format inventory.
Neither lexical validation nor a supplied corpus count demonstrates behavioral quality; preserve relevant script tests and scenario evidence.

**Guard-first sequencing.**
When a hygiene gap is discovered in already-committed content, add or update the guard before broad cleanup and keep changed-line hygiene scoped to the recorded base so unrelated legacy debt does not block a different package.
For a large cleanup, prefer two separate PRs: one adds the guard + tests + CI step, the next externalizes the legacy paths/secrets it now catches.
In cleanup PRs, keep prose examples as placeholders (`<VAR>`, `${VAR}`), and make executable scripts declare inputs with argparse flags or shell positional or flag arguments; a runtime-owned non-secret setting may default from a `getenv`-style read of one documented variable, and secrets use `getenv` after declaration in the runtime's secret manifest.

Avoid ambient configuration / implicit inputs and language-in-language heredocs.
The runtime's security scanner cannot distinguish a script that dumps the environment from one that passes arguments through it, and neither can a reader of `--help`.

After an authorized merge/update, verify the actual resulting revision and rerun the relevant checks.
Report unrelated work without stashing or changing the operator's branch implicitly.

## 3. Diff-mode pitfall

`--diff-base` must validate the content that would be committed, not a stale `HEAD` snapshot.
A three-dot range like `origin/main...HEAD` passed directly to `git diff` can miss uncommitted cleanup.
Resolve the intended base explicitly; do not pass a range to the format selector.
Package selection unions the four Git states even when a staged change and an unstaged reversal cancel in a net diff; format checks then read current content.
Changed-line secret checks have a different purpose from package selection; do not claim identical coverage merely because both scripts accept `--diff-base`.
Regression-test shape when changing either script: a clean base commit; a next commit that adds a leaked value; a worktree that replaces it with a placeholder; `--diff-base <base>` must PASS against the worktree state, and a negative case with an uncommitted leak must FAIL.

A line containing an env placeholder can still contain a second hardcoded value on the same line — do not exempt a whole line just because `${VAR}` appears somewhere in it.

## 4. Emergency cleanup: a secret was committed

Use this sequence the moment a real secret, token, or `.env` value reaches a commit.
A PR opened after the leak does not remove it from history — cleanup requires a history rewrite plus a force push.

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

3. Obtain approval for the exact local history rewrite and preserve unrelated work before using a destructive history command. Revoke or rotate the exposed credential through the authorized provider procedure; history cleanup does not invalidate it. Remove only approved real env paths, and retain safe examples or recreate them afterward.

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

6. Force-push the rewritten refs only with explicit current-turn approval. State the exact refs being rewritten and why; prefer `--force-with-lease`:

   ```bash
   git push --force-with-lease origin main
   # Include other published branches only if they also contain the leaked path.
   ```

7. After force-push, verify remote refs and tell the user to rotate/revoke the exposed secret immediately — a history rewrite alone does not invalidate a leaked credential. Do not claim GitHub caches or clones are clean unless separately verified.
