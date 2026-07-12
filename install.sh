#!/usr/bin/env sh
# install.sh — craft-skills multi-runtime convenience installer
#
# Usage:
#   ./install.sh claude    Print the Claude Code marketplace install commands
#   ./install.sh codex     Install the Codex plugin and optionally clone skills for project context
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

  # Codex canonical channel: .codex-plugin/plugin.json.
  note "Canonical channel: install the plugin defined by ${REPO_DIR}/.codex-plugin/plugin.json."
  printf '\n'
  printf '    codex plugin marketplace add %s\n' "${REPO_DIR}"
  printf '    codex plugin add craft-skills@craft-skills --json\n'
  printf '\n'

  # Codex auxiliary clone path: .agents/skills/craft-skills.
  CLONE_DIR="${PWD}/.agents/skills/craft-skills"
  REPO_URL="https://github.com/GoBeromsu/craft-skills.git"
  note "Optional discovery clone target: ${CLONE_DIR}."

  if [ -d "${CLONE_DIR}/.git" ]; then
    ok "Already cloned at ${CLONE_DIR} — skipping clone."
  else
    step "Cloning ${REPO_URL} → ${CLONE_DIR}"
    mkdir -p "${PWD}/.agents/skills"
    git clone "${REPO_URL}" "${CLONE_DIR}"
    ok "Cloned to ${CLONE_DIR}"
  fi

  note "The auxiliary clone has a nested layout: skills live at ${CLONE_DIR}/skills/<name>/SKILL.md."
  ok "Codex setup complete."
}

# ── Hermes ─────────────────────────────────────────────────────────────────────

install_hermes() {
  header "Hermes"

  # Hermes mount path: ~/dev/GoBeromsu/craft-skills/skills.
  SKILLS_PATH="${HOME}/dev/GoBeromsu/craft-skills/skills"

  note "ASSUMPTION: Hermes config.yaml uses 'skills.external_dirs'. Verify with: hermes --help | grep -i external"
  note "Automatic config.yaml editing is NOT performed — paste the snippet below manually."

  if [ -n "${HERMES_HOME}" ] && [ -f "${HERMES_HOME}/config.yaml" ]; then
    if grep -q "craft-skills" "${HERMES_HOME}/config.yaml" 2>/dev/null; then
      ok "craft-skills already referenced in ${HERMES_HOME}/config.yaml — no action needed."
      return 0
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
  ok "Hermes config snippet printed — paste it into config.yaml and restart."
}

# ── Dispatch ───────────────────────────────────────────────────────────────────

TARGET="${1:-}"

case "${TARGET}" in
  claude)
    install_claude
    ;;
  codex)
    install_codex
    ;;
  hermes)
    install_hermes
    ;;
  all)
    install_claude
    hr
    install_codex
    hr
    install_hermes
    ;;
  ""|--help|-h)
    printf 'Usage: %s [claude|codex|hermes|all]\n' "$0"
    printf '\n'
    printf '  claude   Print Claude Code marketplace install commands\n'
    printf '  codex    Clone craft-skills for Codex skill context\n'
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
