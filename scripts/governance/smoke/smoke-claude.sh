#!/usr/bin/env bash
# Smoke-test Claude Code marketplace installation and installed skill discovery.
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)"

if ! command -v claude >/dev/null; then
  printf 'SKIPPED: claude CLI is not installed\n'
  exit 3
fi

TEMP_HOME="$(mktemp -d)"
trap 'rm -rf "$TEMP_HOME"' EXIT
export HOME="$TEMP_HOME"
export CLAUDE_CONFIG_DIR="$TEMP_HOME/.claude"
unset CLAUDE_HOME
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
mkdir -p "$CLAUDE_CONFIG_DIR" "$XDG_CONFIG_HOME" "$XDG_DATA_HOME" "$XDG_STATE_HOME" "$XDG_CACHE_HOME" "$TEMP_HOME/git-templates" "$TEMP_HOME/git-hooks"
git config --global init.templateDir "$TEMP_HOME/git-templates"
git config --global core.hooksPath "$TEMP_HOME/git-hooks"
git config --global commit.gpgsign false
git config --global url."https://github.com/".insteadOf "git@github.com:"

SNAPSHOT="$TEMP_HOME/snapshot"
mkdir -p "$SNAPSHOT"

# Snapshot current tracked + untracked nonignored distributable source into an
# owned TEMP_HOME tree, then register that snapshot as the marketplace.
if ! python3 - "$ROOT" "$SNAPSHOT" "$TEMP_HOME" <<'PY'
import os
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath

root = Path(sys.argv[1]).resolve()
snapshot = Path(sys.argv[2]).resolve()
temp_home = Path(sys.argv[3]).resolve()
if not snapshot.is_relative_to(temp_home):
    raise SystemExit("snapshot is not owned by TEMP_HOME")


def git_bytes(*args: str) -> bytes:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        detail = os.fsdecode(getattr(exc, "stderr", b"") or b"").strip()
        raise SystemExit(f"git inventory failed: {detail or exc}") from exc


reported = os.fsdecode(git_bytes("rev-parse", "--show-toplevel").removesuffix(b"\n"))
git_root = Path(reported).resolve()
if git_root != root:
    raise SystemExit("requested root must identify the Git worktree root")


def decode_rel(raw: bytes) -> str:
    value = os.fsdecode(raw)
    path = PurePosixPath(value)
    if (not value or "\0" in value or path.is_absolute()
            or ".." in path.parts or path.as_posix() != value):
        raise SystemExit(f"unsafe git path: {value!r}")
    return value


skip_parts = {".git", ".gjc"}
inventory: set[str] = set()
for args in (
    ("ls-files", "-z"),
    ("ls-files", "--others", "--exclude-standard", "-z"),
):
    for raw in git_bytes(*args).split(b"\0"):
        if not raw:
            continue
        rel = decode_rel(raw)
        parts = PurePosixPath(rel).parts
        if parts and parts[0] in skip_parts:
            continue
        inventory.add(rel)

deleted = {
    decode_rel(raw)
    for raw in git_bytes("ls-files", "--deleted", "-z").split(b"\0")
    if raw
}
inventory -= deleted

for rel in sorted(inventory):
    src = root / rel
    dest = snapshot / rel
    if src.is_symlink() or dest.is_symlink():
        raise SystemExit(f"refusing symlink in snapshot: {rel}")
    try:
        if not src.exists():
            raise SystemExit(f"missing inventoried path: {rel}")
        resolved = src.resolve()
        if not resolved.is_relative_to(root):
            raise SystemExit(f"source path escapes checkout: {rel}")
        if resolved.is_dir():
            raise SystemExit(f"inventoried directory/submodule is not a regular file: {rel}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(resolved, dest, follow_symlinks=False)
    except OSError as exc:
        raise SystemExit(f"unreadable snapshot source {rel}: {exc}") from exc
PY
then
  printf 'FAILED: current-source snapshot failed\n' >&2
  exit 1
fi

if [ ! -f "$SNAPSHOT/.claude-plugin/marketplace.json" ]; then
  printf 'FAILED: snapshot is missing copied public marketplace.json\n' >&2
  exit 1
fi
if [ ! -f "$SNAPSHOT/.claude-plugin/plugin.json" ]; then
  printf 'FAILED: snapshot is missing .claude-plugin/plugin.json\n' >&2
  exit 1
fi

cd "$TEMP_HOME"
if ! claude plugin marketplace add "$SNAPSHOT" </dev/null; then
  printf 'FAILED: claude marketplace add failed\n' >&2
  exit 1
fi
if ! claude plugin install craft-skills@craft-skills --scope user </dev/null; then
  printf 'FAILED: claude plugin install failed\n' >&2
  exit 1
fi

if ! PLUGIN_LISTING="$(claude plugin list --json </dev/null)"; then
  printf 'FAILED: claude plugin list failed\n' >&2
  exit 1
fi
export PLUGIN_LISTING
if ! python3 - "$SNAPSHOT" "$TEMP_HOME" "$ROOT" <<'PY'
import json
import os
import sys
from pathlib import Path

snapshot = Path(sys.argv[1]).resolve()
temp_home = Path(sys.argv[2]).resolve()
original = Path(sys.argv[3]).resolve()
plugins = json.loads(os.environ["PLUGIN_LISTING"])
if not isinstance(plugins, list):
    raise SystemExit("plugin listing is not an array")
catalog = json.loads((snapshot / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
entries = catalog.get("plugins") if isinstance(catalog, dict) else None
if not isinstance(entries, list) or not any(
    isinstance(entry, dict) and entry.get("name") == "craft-skills" and entry.get("source") == "./"
    for entry in entries
):
    raise SystemExit("snapshot marketplace.json does not use relative source ./")
source_plugin = json.loads((snapshot / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
expected_version = source_plugin.get("version")
if not isinstance(expected_version, str) or not expected_version:
    raise SystemExit("snapshot .claude-plugin/plugin.json has no version")
expected = {path.parent.name for path in (snapshot / "skills").glob("*/SKILL.md")}
if not expected:
    raise SystemExit("snapshot has no skills/*/SKILL.md packages")

for plugin in plugins:
    if not isinstance(plugin, dict):
        raise SystemExit("plugin listing contains a non-object entry")
    if plugin.get("id") != "craft-skills@craft-skills":
        continue
    install_path = plugin.get("installPath")
    if not isinstance(install_path, str) or not install_path.strip():
        raise SystemExit("plugin listing has empty installPath")
    if not Path(install_path).is_absolute():
        raise SystemExit("installPath is not an absolute path")
    resolved = Path(install_path).resolve()
    if not str(resolved).startswith(str(temp_home) + os.sep):
        raise SystemExit("installedPath is not an isolated absolute path")
    if resolved == original or str(resolved).startswith(str(original) + os.sep):
        raise SystemExit("installedPath points at the original checkout")
    installed_manifest = (resolved / ".claude-plugin" / "plugin.json").resolve()
    if not installed_manifest.is_relative_to(resolved):
        raise SystemExit("installed manifest escapes the plugin directory")
    installed_plugin = json.loads(installed_manifest.read_text(encoding="utf-8"))
    if installed_plugin.get("name") != "craft-skills" or installed_plugin.get("version") != expected_version:
        raise SystemExit("installed plugin identity/version does not match current-source snapshot")
    installed = {path.parent.name for path in (resolved / "skills").glob("*/SKILL.md")}
    if installed != expected:
        raise SystemExit(
            "installed skills do not match snapshot skills/*/SKILL.md "
            f"(expected={sorted(expected)}, found={sorted(installed)})"
        )
    raise SystemExit(0)
raise SystemExit("plugin listing has no installed craft-skills package")
PY
then
  printf 'FAILED: installed skill discovery did not match current-source snapshot\n' >&2
  exit 1
fi

printf 'PASSED: Claude marketplace install and skill listing.\n'
