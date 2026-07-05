# Secrets and Supply-Chain Hygiene

A secret is compromised the moment it touches a tracked file, a log line, or a git commit — treat leak prevention and dependency provenance as one discipline, because both answer the same question: what do you trust to run with access to your systems.

## Hard rules

| Concern | Do / Use | Never |
|---|---|---|
| Secret storage | Environment variable injected at runtime, or a secrets manager | Hardcoded in source, committed in a tracked `.env` |
| Dependency versions | Committed lockfile, pinned exact versions for security-sensitive packages | Unpinned ranges with no lockfile in a deployed artifact |
| YAML/pickle loading | `yaml.safe_load()` / a schema-validated parser | `yaml.load()` default loader, `pickle.load()` on untrusted data |
| Install-time scripts from unknown packages | Reviewed before allowing, or installed with `--ignore-scripts` | Blind install of a new dependency in CI with scripts enabled |

## Secret scanning

A leaked credential (API key, private key, access token) grants whatever access that credential holds to anyone who finds it — in a tracked file, a build log, or git history that was supposedly "removed" later.

**Detect** — common secret shapes across currently tracked files:

```bash
grep -rnE "AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|sk-[A-Za-z0-9]{20,}|-----BEGIN (RSA |EC )?PRIVATE KEY-----" \
  $(git ls-files) 2>/dev/null
```

**Detect** — the same shapes anywhere in git history, including commits later "fixed":

```bash
git log -p --all | grep -nE "AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|sk-[A-Za-z0-9]{20,}"
```

Reading: zero hits on both commands is a pass. Any hit is a live leak, not a historical curiosity — assume the repository (or its history) has already been cloned or cached somewhere outside your control, and rotate the credential regardless of whether you also rewrite history. Heuristic: this pattern list is illustrative, not exhaustive — extend it with the prefix formats of whatever credential providers the project actually uses.

**Fix**: rotate first (see the protocol below); do not treat a history rewrite as sufficient on its own.

## `.env` law

An environment file holding real secrets must never be tracked by git; a checked-in `.env.example` with placeholder values documents the required variables without exposing any of them.

**Detect**:

```bash
git ls-files | grep -E '\.env$'
```

Reading: any output is a fail — a real `.env` is tracked. Confirm `.gitignore` excludes `.env` and that `.env.example` exists as its documented, secret-free sibling:

```bash
test -f .env.example || echo "FAIL: no .env.example for onboarding"
```

```bash
# SMELL — real credentials tracked in a committed .env
DATABASE_URL=postgres://admin:hunter2@prod-db:5432/app

# CLEAN — .env.example ships placeholders; real values live only in the untracked .env
DATABASE_URL=postgres://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:5432/app
```

Grey zone: a monorepo often carries one `.env` per package — run the tracked-file check from the repository root so a nested `.env` several directories deep isn't missed.

## Rotation-on-leak protocol

1. Revoke the leaked credential at its issuer (cloud console, package registry, API provider) — this is the actual fix; everything else is cleanup.
2. Issue a new credential and update it wherever it's consumed (deploy configs, secrets manager, CI variables).
3. Redeploy so the new credential is live everywhere the old one was.
4. Confirm the old credential is rejected — attempt an authenticated call with it; expect a 401/403.
5. Only then scrub the leaked value from git history and any logs — a secondary cleanup step, not a substitute for rotation.

## Dependency audit

An unaudited dependency tree can carry a known-vulnerable transitive package, or a floating version range that resolves to a different — and possibly compromised — release between two installs.

**Detect** — vulnerability scan:

```bash
npm audit --omit=dev
pip-audit
# uv projects — export the resolved lockfile and audit it without needing a pip/venv build:
uv export --format requirements-txt | uvx pip-audit -r /dev/stdin --disable-pip --no-deps
```

**Detect** — lockfile presence:

```bash
test -f package-lock.json -o -f pnpm-lock.yaml -o -f uv.lock -o -f poetry.lock \
  || echo "FAIL: no dependency lockfile committed"
```

Reading: any high/critical finding from the audit command with a fix version available is fix-now; no lockfile at all is a fail regardless of audit output — reproducible installs are a prerequisite for a meaningful audit. Pin exact versions (not floating ranges) for security-sensitive packages (auth, crypto, serialization libraries) even when a lockfile exists, so a lockfile regeneration can't silently pull in a newer major version.

Grey zone: a finding in a dev-only dependency (test runner, linter, local tooling) that never ships to production carries lower urgency than the same CVE score in a runtime dependency — weight the severity tree's reachability question by whether the package executes in production, not by CVE score alone.

## CI secret hygiene

A secret printed to a CI log is exposed to everyone with log read access, indefinitely — most CI providers do not retroactively redact.

**Detect**:

```bash
grep -rnE 'echo\s+\$\{?(SECRET|TOKEN|KEY|PASSWORD)' --include="*.yml" --include="*.yaml" .
```

Reading: any hit is a finding — remove the direct print; rely on the CI provider's built-in secret masking, and never pass a secret as a plain command-line argument that would appear in a process list or log line.

## Install-script caution

A package's install-time script (`postinstall`, a Python build hook) runs arbitrary code on your machine or CI runner the moment the package is installed, before any of your code executes.

**Detect** — which installed packages carry a lifecycle script worth reviewing:

```bash
find node_modules -maxdepth 2 -name package.json -exec grep -l '"postinstall"' {} \; 2>/dev/null | head -20
```

Reading: each hit is a package whose install step runs custom code — review the script before trusting it, especially for a recently-added or low-reputation dependency. Zero hits, or every hit reviewed and accepted, is a pass.

**Fix / evaluation rule**: for a new dependency from an unfamiliar or low-reputation source, review its install scripts before allowing them, or install with scripts disabled and enable only after review:

```bash
npm install --ignore-scripts
```

Grey zone: some legitimate packages need install scripts to build native bindings — blanket-disabling in CI can break real builds. Evaluate case by case: a widely-used package with a documented native-build step is lower risk than an obscure package published days ago with a build hook.
