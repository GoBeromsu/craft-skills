#!/usr/bin/env bash
# Smoke-test Claude Code marketplace installation and skill loading.
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)"
OUT_DIR="${SMOKE_OUT:-/tmp/craft-smokes}"
ARTIFACT="${OUT_DIR}/claude.json"
CHECKS="marketplace_install|plugin_or_skill_listing"
mkdir -p "$OUT_DIR"

write_artifact() {
  python3 - "$ARTIFACT" "${1}" "${2}" "$CHECKS" <<'PY'
import json
import sys
from pathlib import Path

Path(sys.argv[1]).write_text(json.dumps({
    "runtime": "claude",
    "status": sys.argv[2],
    "reason": sys.argv[3],
    "checks": [item for item in sys.argv[4].split("|") if item],
}, indent=2) + "\n", encoding="utf-8")
PY
}

skip() {
  write_artifact "skipped" "$1"
  printf 'SKIPPED: %s\n' "$1"
  exit 3
}

fail() {
  write_artifact "failed" "$1"
  printf 'FAILED: %s\n' "$1" >&2
  exit 1
}

if ! command -v claude >/dev/null; then
  skip "claude CLI is not installed"
fi

TEMP_HOME="$(mktemp -d)"
trap 'rm -rf "$TEMP_HOME"' EXIT
export HOME="$TEMP_HOME"
git config --global url."https://github.com/".insteadOf "git@github.com:"

if ! claude plugin marketplace add "$ROOT"; then
  fail "claude marketplace add failed"
fi
if ! claude plugin install craft-skills@craft-skills; then
  fail "claude plugin install failed"
fi

if ! PLUGIN_LISTING="$(claude plugin list --json)"; then
  fail "claude plugin list failed"
fi
export PLUGIN_LISTING
if ! python3 - "$ROOT" <<'PY'
import json
import os
import sys
from pathlib import Path

root = Path(sys.argv[1])
plugins = json.loads(os.environ["PLUGIN_LISTING"])
for plugin in plugins:
    if plugin.get("id") == "craft-skills@craft-skills":
        install_path = plugin.get("installPath")
        if not isinstance(install_path, str):
            raise SystemExit("plugin listing has no installed craft-skills path")
        manifest = json.loads("\n".join(
            line for line in (root / "skills-manifest.yaml").read_text(encoding="utf-8").splitlines()
            if not line.lstrip().startswith("#")
        ))
        expected = {package["name"] for package in manifest["packages"]}
        installed = {
            path.parent.name for path in (Path(install_path) / "skills").glob("*/SKILL.md")
        }
        if installed != expected:
            raise SystemExit(
                "installed skills do not match skills-manifest.yaml "
                f"(expected={sorted(expected)}, found={sorted(installed)})"
            )
        raise SystemExit(0)
raise SystemExit("plugin listing has no installed craft-skills package")
PY
then
  fail "installed skill discovery differs from skills-manifest.yaml"
fi

write_artifact "passed" "marketplace install and installed skill discovery matched"
printf 'PASSED: Claude marketplace install and skill listing.\n'
