# Runtime hygiene PR playbook

Use when a skill-library task touches hardcoded runtime values, credential patterns, `.env` files, or host-specific paths.

## Sequence

1. **Stop new leakage first**
   - Add or update the runtime hygiene guard before doing broad cleanup.
   - CI should scan only newly changed lines with `--diff-base origin/main...HEAD` so old debt does not block unrelated PRs.
   - Keep a full-scan mode available for dedicated cleanup PRs.

2. **If a real secret or `.env` was committed**
   - Do not treat this as normal cleanup.
   - Follow `references/secret-env-history-rewrite.md` immediately: rewrite history, force-push with explicit approval, then rotate/revoke the exposed secret.

3. **Branch and PR shape**
   - Prefer separate PRs:
     - guard PR: adds detection + tests + CI step
     - legacy cleanup PR: externalizes existing paths/secrets after the guard exists
   - For broad cleanup, keep examples as placeholders (`<VAR>`, `${VAR}`) and executable code as environment lookups (`os.environ[...]`, shell `${VAR:?message}`).

4. **Validation before PR / merge**
   - Run the guard both ways when relevant:
     - `python3 skills/skillify/scripts/validate-runtime-hygiene.py`
     - `python3 skills/skillify/scripts/validate-runtime-hygiene.py --diff-base origin/main...HEAD`
   - Run deterministic tests for the guard.
   - Compile changed Python scripts and syntax-check changed shell scripts.
   - Run marketplace/plugin validation if the repo exposes a Claude Code plugin surface.
   - Run `git diff --check` before committing.

5. **Post-merge verification**
   - Sync `main` and rerun the core guard/test/plugin validation on `main`.
   - Verify PR state and merge commit with `gh pr view <n> --json state,mergedAt,mergeCommit,url`.
   - Confirm `git status --short --branch` is clean or explicitly report remaining stashes.

## Diff-mode pitfall (local checks)

`validate-runtime-hygiene.py --diff-base ...` must validate the content that would be
committed, not a stale `HEAD` snapshot. A three-dot range like `origin/main...HEAD` passed
directly to `git diff` can miss uncommitted cleanup. Resolve the range to its merge base
first, then diff that base against the current worktree:

```python
def diff_compare_base(root: Path, diff_base: str) -> str:
    if "..." in diff_base:
        left, right = diff_base.split("...", 1)
        right = right or "HEAD"
        return subprocess.check_output(
            ["git", "merge-base", left, right], cwd=root, text=True).strip()
    return diff_base
```

Regression test shape: (1) clean base commit; (2) next commit adds a host path
`/Users/<user>/...`; (3) worktree replaces it with `${VAR}`/`<OS_HOME>`; (4) `--diff-base <base>`
must PASS, proving the validator sees the worktree. Keep the negative test where an
uncommitted added host path must FAIL. Real runtime locations belong in env vars, profile
config, approved credential files, or placeholders — never committed into a skill package.

## Pitfalls

- A line containing an env placeholder can still contain a second hardcoded absolute path; do not globally exempt lines just because `${VAR}` appears.
- Tests for the guard must avoid containing raw forbidden strings in their own source unless split/constructed safely.
- If local dirty edits exist during merge/pull, stash with a descriptive message, finish the merge, then inspect the stash and restore useful changes on a follow-up branch instead of dropping them blindly.
