#!/usr/bin/env bash
# Smoke-test Hermes external skill directory discovery.
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)"
OUT_DIR="${SMOKE_OUT:-/tmp/craft-smokes}"
ARTIFACT="${OUT_DIR}/hermes.json"
CHECKS="external_dirs_config|skills_list"
mkdir -p "$OUT_DIR"

write_artifact() {
  python3 - "$ARTIFACT" "${1}" "${2}" "$CHECKS" <<'PY'
import json
import sys
from pathlib import Path

Path(sys.argv[1]).write_text(json.dumps({
    "runtime": "hermes",
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

if ! command -v hermes >/dev/null; then
  skip "hermes CLI is not installed"
fi

TEMP_HOME="$(mktemp -d)"
trap 'rm -rf "$TEMP_HOME"' EXIT
export HOME="$TEMP_HOME"
export HERMES_HOME="$TEMP_HOME/hermes"
mkdir -p "$HERMES_HOME"
printf 'skills:\n  external_dirs:\n    - %s/skills\n' "$ROOT" > "$HERMES_HOME/config.yaml"

if ! SKILL_LISTING="$(hermes skills list)"; then
  fail "hermes skills list failed"
fi
export SKILL_LISTING
if ! python3 - "$ROOT" <<'PY'
import json
import os
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
manifest = json.loads("\n".join(
    line for line in (root / "skills-manifest.yaml").read_text(encoding="utf-8").splitlines()
    if not line.lstrip().startswith("#")
))
listing = os.environ["SKILL_LISTING"]
missing = [
    package["name"]
    for package in manifest["packages"]
    if not re.search(rf"(?<![A-Za-z0-9_-]){re.escape(package['name'])}(?![A-Za-z0-9_-])", listing)
]
if missing:
    raise SystemExit(f"hermes skills list is missing: {', '.join(missing)}")
PY
then
  fail "hermes did not discover every manifest skill"
fi

write_artifact "passed" "external_dirs mount exposed every manifest skill"
printf 'PASSED: Hermes external skill directory discovery.\n'
