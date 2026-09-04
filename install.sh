#!/usr/bin/env sh
# install.sh — craft-skills multi-runtime convenience installer
#
# Usage:
#   ./install.sh claude    Print the Claude Code marketplace install commands
#   ./install.sh codex [--clone [PROJECT_ROOT]]
#                       Print Codex plugin commands; optionally clone development context
#   ./install.sh hermes    Print the Hermes tap commands and verify the tap is registered
#   ./install.sh gjc       Print the GJC plugin commands and verify the plugin is installed
#   ./install.sh all       Run all four targets
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

  TAP_REPO="GoBeromsu/craft-skills"

  note "Hermes installs craft-skills through a custom tap; each skill is one install unit."
  printf '\n'
  printf '    hermes skills tap add %s\n' "${TAP_REPO}"
  printf '    hermes skills install %s/skills/<name>\n' "${TAP_REPO}"
  printf '    hermes skills update            # pull upstream changes for every tap-installed skill\n'
  printf '\n'
  note "The tap scans every file in the unit; only a safe verdict installs without --force."

  TAPS_FILE="${HERMES_HOME:-${HOME}/.hermes}/skills/.hub/taps.json"
  if [ -f "${TAPS_FILE}" ] && grep -q "\"${TAP_REPO}\"" "${TAPS_FILE}"; then
    ok "tap ${TAP_REPO} is registered in ${TAPS_FILE}."
    return 0
  fi
  note "tap ${TAP_REPO} is not registered yet (checked ${TAPS_FILE})."
  return 1
}

# ── GJC ───────────────────────────────────────────────────────────────────────────

install_gjc() {
  header "GJC"

  note "GJC installs craft-skills as a marketplace plugin and loads packages straight from it."
  printf '\n'
  printf '    gjc plugin marketplace add GoBeromsu/craft-skills\n'
  printf '    gjc plugin install craft-skills@craft-skills\n'
  printf '    gjc plugin upgrade              # the whole update path\n'
  printf '\n'
  note "Packages are advertised as craft-skills:<name>; no further configuration is required."
  note "The installed plugin is the only copy; see the GJC row of the install matrix in AGENTS.md."

  if ! command -v gjc >/dev/null 2>&1; then
    note "gjc is not on PATH; nothing to verify."
    return 1
  fi
  if gjc plugin list 2>/dev/null | grep -q 'craft-skills@craft-skills'; then
    ok "craft-skills@craft-skills is installed."
    return 0
  fi
  note "craft-skills@craft-skills is not installed yet."
  return 1
}

# ── Dispatch ───────────────────────────────────────────────────────────────────────

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
  gjc)
    [ "$#" -eq 0 ] || {
      printf 'Usage: %s gjc\n' "$0" >&2
      exit 2
    }
    install_gjc
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
    hr
    install_gjc
    ;;
  ""|--help|-h)
    printf 'Usage: %s [claude|codex [--clone [PROJECT_ROOT]]|hermes|gjc|all]\n' "$0"
    printf '\n'
    printf '  claude   Print Claude Code marketplace install commands\n'
    printf '  codex    Print Codex plugin commands; --clone optionally adds development context\n'
    printf '  hermes   Print the Hermes tap commands and verify the tap is registered\n'
    printf '  gjc      Print the GJC plugin commands and verify the plugin is installed\n'
    printf '  all      Run all four targets\n'
    exit 0
    ;;
  *)
    printf 'Unknown target: %s\n' "${TARGET}" >&2
    printf 'Run %s --help for usage.\n' "$0" >&2
    exit 1
    ;;
esac

printf '\n'
