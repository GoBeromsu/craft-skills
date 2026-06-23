#!/usr/bin/env sh
# tmux-fanout — local tmux fan-out for git wt slice worktrees.
#
#   tmux-fanout.sh <issue#> <slice-slug> [slice-slug ...]
#
# Creates/uses a local tmux session named wt-<issue#>. For each slice slug, creates
# one tmux window and runs: git wt <issue#> --slug <slice-slug>
set -eu

_script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
# shellcheck source=scripts/git-guard/lib.sh
. "$_script_dir/lib.sh"

usage() {
  sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

quote_sq() {
  # POSIX single-quote escaping for embedding one argument in a shell command.
  printf "'%s'" "$(printf '%s' "$1" | sed "s/'/'\\''/g")"
}

window_name() {
  name=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9_.-]+/-/g; s/^-+//; s/-+$//')
  [ -n "$name" ] || name=slice
  printf '%s' "$name" | cut -c1-50
}

require_tmux() {
  command -v tmux >/dev/null 2>&1 || gg_die "tmux not found — install tmux or run git wt <issue#> --slug <slice> manually for each slice"
}

window_exists() {
  session=$1
  win=$2
  tmux list-windows -t "$session" -F '#W' 2>/dev/null | awk -v w="$win" 'BEGIN{found=1} $0==w{found=0; exit} END{exit found}'
}

run_command_for() {
  issue=$1
  slice=$2
  printf 'git wt %s --slug %s; printf '\''\\n[tmux-fanout] git wt finished for slice %s. Press Enter to close this shell. '\''; read _; exit' \
    "$(quote_sq "$issue")" "$(quote_sq "$slice")" "$(printf '%s' "$slice" | sed "s/'/'\\''/g")"
}

main() {
  [ $# -ge 2 ] || usage 1
  case "$1" in
    -h|--help) usage 0 ;;
  esac
  issue=$1
  shift
  case "$issue" in *[!0-9]*|'') gg_die "issue number must be numeric: $issue" ;; esac
  require_tmux

  session="wt-$issue"
  if tmux has-session -t "$session" 2>/dev/null; then
    gg_warn "using existing tmux session $session"
  else
    first_slice=$1
    first_window=$(window_name "$first_slice")
    first_command=$(run_command_for "$issue" "$first_slice")
    tmux new-session -d -s "$session" -n "$first_window" "$first_command"
    gg_warn "created tmux session $session window $first_window"
    shift
  fi

  for slice in "$@"; do
    win=$(window_name "$slice")
    if window_exists "$session" "$win"; then
      gg_warn "window $session:$win already exists; skipping slice $slice"
      continue
    fi
    command=$(run_command_for "$issue" "$slice")
    tmux new-window -t "$session" -n "$win" "$command"
    gg_warn "created tmux window $session:$win"
  done

  printf '%s\n' "tmux attach -t $session"
}

main "$@"
