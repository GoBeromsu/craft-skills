#!/usr/bin/env bash
# Smoke-test the Codex plugin install and installed skill discovery.
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)"

if ! command -v codex >/dev/null; then
  printf 'SKIPPED: codex CLI is not installed\n'
  exit 3
fi

TEMP_HOME="$(mktemp -d)"
trap 'rm -rf "$TEMP_HOME"' EXIT
export HOME="$TEMP_HOME"
export CODEX_HOME="$TEMP_HOME/.codex"
export XDG_CONFIG_HOME="$TEMP_HOME/.config"
export XDG_DATA_HOME="$TEMP_HOME/.local/share"
export XDG_STATE_HOME="$TEMP_HOME/.local/state"
export XDG_CACHE_HOME="$TEMP_HOME/.cache"
for git_var in "${!GIT_@}"; do
  unset "$git_var"
done
export GIT_CONFIG_NOSYSTEM=1
export GIT_CONFIG_SYSTEM=/dev/null
export GIT_CONFIG_GLOBAL="$TEMP_HOME/git-config"
export GIT_TERMINAL_PROMPT=0
mkdir -p "$CODEX_HOME" "$XDG_CONFIG_HOME" "$XDG_DATA_HOME" "$XDG_STATE_HOME" "$XDG_CACHE_HOME" "$TEMP_HOME/git-templates" "$TEMP_HOME/git-hooks"
git config --global init.templateDir "$TEMP_HOME/git-templates"
git config --global core.hooksPath "$TEMP_HOME/git-hooks"
git config --global commit.gpgsign false
git config --global --add safe.directory "$ROOT"

cd "$ROOT"
if ! codex plugin marketplace add ./ </dev/null; then
  printf 'FAILED: codex marketplace add failed\n' >&2
  exit 1
fi
if ! INSTALL_OUTPUT="$(codex plugin add craft-skills@craft-skills --json </dev/null)"; then
  printf 'FAILED: codex plugin add failed\n' >&2
  exit 1
fi
export INSTALL_OUTPUT
if ! python3 - "$ROOT" "$TEMP_HOME" <<'PY'
import json
import os
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
temp_home = Path(sys.argv[2]).resolve()
try:
    payload = json.loads(os.environ["INSTALL_OUTPUT"])
except json.JSONDecodeError as error:
    raise SystemExit(f"plugin install did not return JSON: {error}")
if not isinstance(payload, dict):
    raise SystemExit("plugin install JSON is not an object")

source_plugin = json.loads((root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
expected_version = source_plugin.get("version")
if not isinstance(expected_version, str) or not expected_version:
    raise SystemExit("source .codex-plugin/plugin.json has no version")

plugin_id = payload.get("pluginId")
name = payload.get("name")
marketplace = payload.get("marketplaceName")
version = payload.get("version")
if plugin_id != "craft-skills@craft-skills" or name != "craft-skills":
    raise SystemExit("plugin install JSON is not craft-skills@craft-skills")
if marketplace != "craft-skills":
    raise SystemExit(f"plugin install JSON marketplaceName is {marketplace!r}")
if version != expected_version:
    raise SystemExit(f"plugin version {version!r} does not match source {expected_version!r}")

installed_path = payload.get("installedPath")
if not isinstance(installed_path, str) or not installed_path.strip():
    raise SystemExit("plugin install JSON has empty installedPath")
if not Path(installed_path).is_absolute():
    raise SystemExit("installedPath is not an absolute path")
resolved = Path(installed_path).resolve()
if not str(resolved).startswith(str(temp_home) + os.sep):
    raise SystemExit("installedPath is not contained in TEMP_HOME")
if resolved == root or str(resolved).startswith(str(root) + os.sep):
    raise SystemExit("installedPath points at the source checkout")

expected = {path.parent.name for path in (root / "skills").glob("*/SKILL.md")}
if not expected:
    raise SystemExit("source checkout has no skills/*/SKILL.md packages")
installed = {path.parent.name for path in (resolved / "skills").glob("*/SKILL.md")}
if installed != expected:
    raise SystemExit(
        "installed skills do not match source skills/*/SKILL.md "
        f"(expected={sorted(expected)}, found={sorted(installed)})"
    )
PY
then
  printf 'FAILED: plugin install readback or installed skill discovery failed\n' >&2
  exit 1
fi

printf 'PASSED: Codex plugin install and discovery.\n'
