#!/usr/bin/env bash
# Local mirror of the required CI gates (.github/workflows/pr-check.yml plus the
# marketplace validation job of test-plugin-install.yml). Use it as the merge gate
# whenever GitHub Actions cannot run; .githooks/pre-push runs it automatically.
#
# Usage:
#   bash scripts/ci-local.sh                 # run every gate against origin/main
#   DIFF_BASE=origin/release/x bash ...      # compare against a different base
#   SKIP_MARKETPLACES=1 bash ...             # skip the claude/codex CLI job
#   PR_SIZE_OVERRIDE=1 bash ...              # accept churn over the threshold
#
# The two Layer-1 validators run with a single-ref base so uncommitted worktree
# changes are validated too (see skills/skillify/references/runtime-hygiene.md §3);
# the remaining jobs run CI-exact. Label-gated Codex install/replacement jobs are
# CI-only and intentionally not mirrored.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
DIFF_BASE="${DIFF_BASE:-origin/main}"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT

FAILED=""
run_job() {
  local name="$1"; shift
  echo ""
  echo "=== ${name} ==="
  if "$@"; then
    echo "--- ${name}: PASS"
  else
    echo "--- ${name}: FAIL"
    FAILED="${FAILED} ${name}"
  fi
}

job_pr_size() {
  python3 - "$DIFF_BASE" <<'PY'
import os, re, subprocess, sys

THRESHOLD = 1000
NON_LOGIC_GLOBS = ["**/test/**", "**/tests/**", "*_test.*", "test_*.*", "test_*.py",
                   "*.spec.*", "*.test.*", "docs/**", "*.md", "pnpm-lock.yaml",
                   "uv.lock", "package-lock.json", "yarn.lock", "Cargo.lock",
                   "go.sum", "poetry.lock", "**/migrations/**", "**/generated/**",
                   "**/data/**"]

def glob_to_regex(glob):  # mirrors SIZE-CHECK-LOGIC in pr-check.yml
    regex, i = "^", 0
    while i < len(glob):
        ch = glob[i]
        if ch == "*":
            if i + 1 < len(glob) and glob[i + 1] == "*":
                i += 1
                if i + 1 < len(glob) and glob[i + 1] == "/":
                    i += 1
                    regex += "(?:.*/)?"
                else:
                    regex += ".*"
            else:
                regex += "[^/]*"
        elif ch == "?":
            regex += "[^/]"
        else:
            regex += re.escape(ch)
        i += 1
    return re.compile(regex + "$")

matchers = [glob_to_regex(g) for g in NON_LOGIC_GLOBS]

def non_logic(path):
    base = path.split("/")[-1]
    return any(m.match(path) or m.match(base) for m in matchers)

base = subprocess.run(["git", "merge-base", sys.argv[1], "HEAD"],
                      capture_output=True, text=True, check=True).stdout.strip()
numstat = subprocess.run(["git", "diff", "--numstat", base],
                         capture_output=True, text=True, check=True).stdout
churn = 0
for line in numstat.splitlines():
    added, deleted, path = line.split("\t", 2)
    if added == "-" or non_logic(path):
        continue
    churn += int(added) + int(deleted)

bucket = "size/S" if churn <= 100 else "size/M" if churn <= 300 else \
         "size/L" if churn <= THRESHOLD else "size/XL"
print(f"logic churn {churn} classified as {bucket}")
if churn > THRESHOLD and os.environ.get("PR_SIZE_OVERRIDE") != "1":
    print(f"churn exceeds {THRESHOLD}; split the PR or rerun with PR_SIZE_OVERRIDE=1")
    sys.exit(1)
PY
}

job_layer1_format() {
  python3 skills/skillify/scripts/validate-skill-format.py --diff-base "$DIFF_BASE"
}

job_layer1_hygiene() {
  python3 skills/skillify/scripts/validate-runtime-hygiene.py --diff-base "$DIFF_BASE"
}

job_distribution_version() {
  python3 scripts/governance/tools/check_version_bump.py --diff-base "${DIFF_BASE}...HEAD" &&
  python3 -m unittest \
    scripts.governance.tests.test_check_version_bump \
    scripts.governance.tests.test_verify_plugin_install \
    scripts.governance.tests.test_resolve_plugin_revision
}

job_harness_portable() {
  python3 scripts/governance/harness.py --profile portable \
    --config scripts/governance/fixtures/repos.portable.json \
    --json-out "$SCRATCH/governance-report.json" \
    --text-out "$SCRATCH/governance-report.txt"
}

job_marketplaces() {
  if [ "${SKIP_MARKETPLACES:-0}" = "1" ]; then
    echo "skipped (SKIP_MARKETPLACES=1)"
    return 0
  fi
  if ! command -v claude >/dev/null 2>&1; then
    echo "skipped (claude CLI not installed)"
    return 0
  fi
  claude plugin validate . || return 1
  if ! command -v codex >/dev/null 2>&1; then
    echo "codex CLI not installed; codex half skipped"
    return 0
  fi
  local codex_home="$SCRATCH/codex-home"
  mkdir -p "$codex_home"
  CODEX_HOME="$codex_home" codex plugin marketplace add ./ || return 1
  CODEX_HOME="$codex_home" codex plugin list --marketplace craft-skills --available --json \
    > "$SCRATCH/codex-available.json" || return 1
  python3 - "$SCRATCH/codex-available.json" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as fh:
    data = json.load(fh)
names = {plugin.get("name") for plugin in data.get("available", [])}
if "craft-skills" not in names:
    raise SystemExit("craft-skills was not listed as an available Codex plugin")
print("codex marketplace lists craft-skills")
PY
}

run_job "pr-size"              job_pr_size
run_job "layer1-format"        job_layer1_format
run_job "layer1-hygiene"       job_layer1_hygiene
run_job "distribution-version" job_distribution_version
run_job "harness-portable"     job_harness_portable
run_job "marketplaces"         job_marketplaces

echo ""
if [ -n "$FAILED" ]; then
  echo "ci-local: FAIL —${FAILED}"
  exit 1
fi
echo "ci-local: all gates PASS"
