#!/usr/bin/env sh
# install.sh — craft-skills multi-runtime convenience installer
#
# Usage:
#   ./install.sh claude    Print the Claude Code marketplace install commands
#   ./install.sh codex [--clone [PROJECT_ROOT]]
#                       Print Codex plugin commands; optionally clone development context
#   ./install.sh hermes    Print the Hermes skills.external_dirs config snippet
#   ./install.sh all       Run all three targets
#
# Idempotent — safe to re-run. Never hardcodes secrets or user paths beyond $HOME.
# Does not write git commits or push to remotes.
#
# NOTE: Runtime install channels and paths are kept in the install matrix in AGENTS.md.

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── Helpers ────────────────────────────────────────────────────────────────────

step()  { printf '\n  -> %s\n' "$1"; }
ok()    { printf '  [ok] %s\n' "$1"; }
note()  { printf '  NOTE: %s\n' "$1"; }
header(){ printf '\n=== %s ===\n' "$1"; }
hr()    { printf -- '----------------------------------------------------------------------\n'; }

# ── Claude Code ────────────────────────────────────────────────────────────────

install_claude() {
  header "Claude Code"
  note "Claude Code uses the plugin marketplace — these commands run inside Claude Code, not the shell."
  printf '\n'
  printf '    /plugin marketplace add GoBeromsu/craft-skills\n'
  printf '    /plugin install craft-skills@craft-skills\n'
  printf '\n'
  ok "Paste those two lines into any Claude Code session to install craft-skills."
}

# ── Codex ──────────────────────────────────────────────────────────────────────

install_codex() {
  header "Codex"

  note "Canonical channel: install craft-skills from the Codex plugin marketplace."
  printf '\n'
  printf '    codex plugin marketplace add GoBeromsu/craft-skills\n'
  printf '    codex plugin add craft-skills@craft-skills --json\n'
  printf '\n'

  if [ "$#" -eq 0 ]; then
    note "Optional development clone: ./install.sh codex --clone [PROJECT_ROOT]"
    return 0
  fi
  if [ "$#" -eq 1 ] && [ "$1" = "--clone" ]; then
    PROJECT_ROOT="${PWD}"
  elif [ "$#" -eq 2 ] && [ "$1" = "--clone" ]; then
    PROJECT_ROOT="$2"
  else
    printf 'Usage: %s codex [--clone [PROJECT_ROOT]]\n' "$0" >&2
    return 2
  fi

  if [ ! -d "${PROJECT_ROOT}" ]; then
    printf 'REFUSED: Codex clone project root is not a directory: %s\n' "${PROJECT_ROOT}" >&2
    return 1
  fi
  # Physical normalization: resolve symlinks so a link pointing into the
  # repository cannot bypass the prefix check or the marker-pair walk.
  PROJECT_ROOT="$(cd -P "${PROJECT_ROOT}" && pwd -P)"
  REPO_DIR_P="$(cd -P "${REPO_DIR}" && pwd -P)"
  case "${PROJECT_ROOT}/" in
    "${REPO_DIR_P}/"*|"${REPO_DIR_P}")
      printf 'REFUSED: --clone must target a consumer project, not the craft-skills repository (or a path inside it).\n' >&2
      return 1
      ;;
  esac
  # Walk ancestors: a marker pair anywhere above also means we are inside a craft-skills checkout.
  ANCESTOR="${PROJECT_ROOT}"
  while [ "${ANCESTOR}" != "/" ]; do
    if [ -f "${ANCESTOR}/.codex-plugin/plugin.json" ] && [ -f "${ANCESTOR}/skills-manifest.yaml" ]; then
      printf 'REFUSED: --clone must target a consumer project, not the craft-skills repository (marker pair at %s).\n' "${ANCESTOR}" >&2
      return 1
    fi
    ANCESTOR="$(dirname "${ANCESTOR}")"
  done

  (
    cd "${PROJECT_ROOT}"
    # Codex auxiliary clone path: .agents/skills/craft-skills.
    CLONE_DIR="${PWD}/.agents/skills/craft-skills"
    REPO_URL="https://github.com/GoBeromsu/craft-skills.git"
    note "Optional development clone target: ${CLONE_DIR}."

    if [ -d "${CLONE_DIR}/.git" ]; then
      ok "Already cloned at ${CLONE_DIR} — skipping clone."
    else
      step "Cloning ${REPO_URL} → ${CLONE_DIR}"
      mkdir -p "${PWD}/.agents/skills"
      git clone "${REPO_URL}" "${CLONE_DIR}"
      ok "Cloned to ${CLONE_DIR}"
    fi

    note "The auxiliary development clone has a nested layout: skills live at ${CLONE_DIR}/skills/<name>/SKILL.md."
    ok "Codex setup complete."
  )
}

# ── Hermes ─────────────────────────────────────────────────────────────────────

install_hermes() {
  header "Hermes"

  # Hermes mount path: ~/dev/GoBeromsu/craft-skills/skills.
  SKILLS_PATH="${HOME}/dev/GoBeromsu/craft-skills/skills"

  note "ASSUMPTION: Hermes config.yaml uses 'skills.external_dirs'. Verify with: hermes --help | grep -i external"
  note "Automatic config.yaml editing is NOT performed — paste the snippet below manually."

  if [ -n "${HERMES_HOME}" ] && [ -f "${HERMES_HOME}/config.yaml" ]; then
    if HERMES_REFERENCES="$(python3 -c '
import re
import sys
from pathlib import Path

config_path = Path(sys.argv[1])
expected_path = sys.argv[2]
external_dirs_indent = None
key_stack = []  # list of (indent, key) tracking real mapping ancestry
has_expected_entry = False
unexpected_references = []

for raw_line in config_path.read_text(encoding="utf-8").splitlines():
    line = raw_line.rstrip()
    key_match = re.match(r"^(\s*)([A-Za-z0-9_-]+)\s*:\s*(?:#.*)?$", line)
    if key_match:
        indent = len(key_match.group(1))
        key = key_match.group(2)
        while key_stack and key_stack[-1][0] >= indent:
            key_stack.pop()
        # The canonical list is exactly top-level `skills` -> direct child
        # `external_dirs`: the ancestry stack must be [] for skills and
        # [skills] for external_dirs.
        if key == "external_dirs" and [entry[1] for entry in key_stack] == ["skills"]:
            external_dirs_indent = indent
        else:
            external_dirs_indent = None
        key_stack.append((indent, key))
        continue

    if external_dirs_indent is not None:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if stripped and indent <= external_dirs_indent:
            external_dirs_indent = None
        else:
            entry_match = re.match(r"^\s*-\s*(.*?)\s*(?:#.*)?$", line)
            if entry_match:
                entry = entry_match.group(1).strip()
                if entry == expected_path:
                    has_expected_entry = True
                    continue
                if "craft-skills" in entry:
                    unexpected_references.append(entry)
                    continue

    if "craft-skills" in line:
        unexpected_references.append(line.strip())

if has_expected_entry and not unexpected_references:
    raise SystemExit(0)
print("\n".join(unexpected_references))
raise SystemExit(1)
' "${HERMES_HOME}/config.yaml" "${SKILLS_PATH}"
    )"; then
      ok "config.yaml has the canonical skills.external_dirs entry."
      return 0
    fi
    if [ -n "${HERMES_REFERENCES}" ]; then
      note "Found noncanonical craft-skills reference: ${HERMES_REFERENCES}"
    fi
    printf '\n  Merge this block into %s/config.yaml under the skills: key:\n' "${HERMES_HOME}"
  else
    printf '\n  HERMES_HOME is not set or config.yaml not found.\n'
    note "Set HERMES_HOME to your Hermes installation root, then re-run to get a targeted path."
    printf '  Add this block to your Hermes config.yaml under the skills: key:\n'
  fi

  printf '\n'
  printf '  ┌──────────────────────────────────────────────────────────────┐\n'
  printf '  │  skills:                                                     │\n'
  printf '  │    external_dirs:                                            │\n'
  printf '  │      - %s\n' "${SKILLS_PATH}"
  printf '  └──────────────────────────────────────────────────────────────┘\n'
  printf '\n'
  note "Use a literal absolute path — Hermes expands ~ but NOT \${VARS} in config paths."
  printf '\n'
  step "After editing config.yaml, restart the gateway:"
  printf '\n'
  printf '    hermes gateway restart\n'
  printf '\n'
  step "Verify skills are visible:"
  printf '\n'
  printf '    hermes skills list | grep -E '"'"'document|git|init|skillify|write-prd'"'"'\n'
  printf '\n'
  note "Hermes config snippet printed; config.yaml is not yet verified."
  return 1
}

# ── Dispatch ───────────────────────────────────────────────────────────────────

TARGET="${1:-}"
if [ "$#" -gt 0 ]; then
  shift
fi

case "${TARGET}" in
  claude)
    [ "$#" -eq 0 ] || {
      printf 'Usage: %s claude\n' "$0" >&2
      exit 2
    }
    install_claude
    ;;
  codex)
    install_codex "$@"
    ;;
  hermes)
    [ "$#" -eq 0 ] || {
      printf 'Usage: %s hermes\n' "$0" >&2
      exit 2
    }
    install_hermes
    ;;
  all)
    [ "$#" -eq 0 ] || {
      printf 'Usage: %s all\n' "$0" >&2
      exit 2
    }
    install_claude
    hr
    install_codex
    hr
    install_hermes
    ;;
  ""|--help|-h)
    printf 'Usage: %s [claude|codex [--clone [PROJECT_ROOT]]|hermes|all]\n' "$0"
    printf '\n'
    printf '  claude   Print Claude Code marketplace install commands\n'
    printf '  codex    Print Codex plugin commands; --clone optionally adds development context\n'
    printf '  hermes   Print Hermes skills.external_dirs config snippet\n'
    printf '  all      Run all three targets\n'
    exit 0
    ;;
  *)
    printf 'Unknown target: %s\n' "${TARGET}" >&2
    printf 'Run %s --help for usage.\n' "$0" >&2
    exit 1
    ;;
esac

printf '\n'
