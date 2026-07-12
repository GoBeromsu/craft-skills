#!/usr/bin/env bash
# Smoke-test the Codex plugin install and installed skill discovery.
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)"
OUT_DIR="${SMOKE_OUT:-/tmp/craft-smokes}"
ARTIFACT="${OUT_DIR}/codex.json"
CHECKS="plugin_install|installed_skill_discovery"
mkdir -p "$OUT_DIR"

write_artifact() {
  python3 - "$ARTIFACT" "${1}" "${2}" "$CHECKS" <<'PY'
import json
import sys
from pathlib import Path

Path(sys.argv[1]).write_text(json.dumps({
    "runtime": "codex",
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

if ! command -v codex >/dev/null; then
  skip "codex CLI is not installed"
fi

TEMP_HOME="$(mktemp -d)"
trap 'rm -rf "$TEMP_HOME"' EXIT
export HOME="$TEMP_HOME"
export CODEX_HOME="$TEMP_HOME/.codex"
mkdir -p "$CODEX_HOME"

cd "$ROOT"
if ! codex plugin marketplace add ./; then
  fail "codex marketplace add failed"
fi
if ! INSTALL_OUTPUT="$(codex plugin add craft-skills@craft-skills --json)"; then
  fail "codex plugin add failed"
fi
export INSTALL_OUTPUT
if ! python3 - <<'PY'
import json
import os


def contains_name(value):
    if isinstance(value, dict):
        return value.get("name") == "craft-skills" or any(contains_name(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_name(item) for item in value)
    return False

try:
    payload = json.loads(os.environ["INSTALL_OUTPUT"])
except json.JSONDecodeError as error:
    raise SystemExit(f"plugin install did not return JSON: {error}")
if not contains_name(payload):
    raise SystemExit("plugin install JSON does not contain name=craft-skills")
PY
then
  fail "plugin install readback did not identify craft-skills"
fi

if ! python3 - "$ROOT" <<'PY'
import json
import os
import sys
from pathlib import Path

root = Path(sys.argv[1])
payload = json.loads(os.environ["INSTALL_OUTPUT"])
installed_path = payload.get("installedPath")
if not isinstance(installed_path, str):
    raise SystemExit("plugin install JSON has no installedPath")
manifest = json.loads("\n".join(
    line for line in (root / "skills-manifest.yaml").read_text(encoding="utf-8").splitlines()
    if not line.lstrip().startswith("#")
))
expected = {package["name"] for package in manifest["packages"]}
installed = {path.parent.name for path in (Path(installed_path) / "skills").glob("*/SKILL.md")}
if installed != expected:
    raise SystemExit(
        "installed skills do not match skills-manifest.yaml "
        f"(expected={sorted(expected)}, found={sorted(installed)})"
    )
PY
then
  fail "installed skill discovery differs from skills-manifest.yaml"
fi

write_artifact "passed" "plugin readback and installed skill discovery matched"
printf 'PASSED: Codex plugin install and discovery.\n'
