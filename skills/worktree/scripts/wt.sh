#!/usr/bin/env sh
# git wt — simple worktree maker.
#
#   git wt <name>          Create (or reuse) a worktree named <name> off
#                          origin/<default>; print its path.
#   git wt rm <name>       Remove the worktree (git worktree remove + prune).
#                          Branch is kept — delete after merge with `git branch -d`.
#   git wt ls              List worktrees.
#
# Worktrees live OUTSIDE the repo so they don't dirty `git status`:
#   WORKTREE_ROOT (default: <repo-parent>/<repo>-worktrees) / <name>
#
# Teardown MUST use `git worktree remove` (never rm -rf) + `git worktree prune`,
# or phantom .git/worktrees/ entries block branch checkout and `git branch -d`.
set -eu

_gg_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
# shellcheck source=scripts/git-guard/lib.sh
. "$_gg_dir/lib.sh"

usage() {
  sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

repo_root() { git rev-parse --show-toplevel 2>/dev/null || gg_die "not inside a git repository"; }

repo_name() {
  url=$(git remote get-url origin 2>/dev/null || true)
  if [ -n "$url" ]; then basename "$url" .git; else basename "$(repo_root)"; fi
}

default_branch() {
  # origin/HEAD -> origin/<default>, fall back to main.
  ref=$(git symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null || true)
  if [ -n "$ref" ]; then basename "$ref"; else echo main; fi
}

worktree_root() {
  root=$(repo_root); parent=$(dirname "$root")
  printf '%s' "${WORKTREE_ROOT:-$parent/$(repo_name)-worktrees}"
}

# Make a name safe to use as both a branch and a path segment.
sanitize() {
  printf '%s' "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's#[^a-z0-9._/-]+#-#g; s#^[-/]+##; s#[-/]+$##' \
    | cut -c1-60 \
    | sed -E 's#[-/]+$##'
}

resolve_worktree_path() {
  git worktree list --porcelain | awk -v a="$1" '
    /^worktree /{p=$2}
    /^branch /{b=$2; sub("refs/heads/","",b); if(b==a){print p; exit}}'
}

cmd_create() {
  name=$(sanitize "${1:-}")
  [ -n "$name" ] || gg_die "worktree name required: git wt <name>"

  existing=$(resolve_worktree_path "$name")
  if [ -n "$existing" ]; then printf '%s\n' "$existing"; return 0; fi

  path="$(worktree_root)/$name"
  mkdir -p "$(dirname "$path")"
  if git show-ref --verify --quiet "refs/heads/$name"; then
    git worktree add "$path" "$name" >&2
  else
    base=$(default_branch)
    git fetch --quiet origin "$base" 2>/dev/null || gg_warn "could not fetch origin/$base — branching off local ref"
    git worktree add -b "$name" "$path" "origin/$base" >&2
  fi
  printf '%s\n' "$path"
}

cmd_rm() {
  force=""; arg=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --force|-f) force="--force"; shift ;;
      *) arg="$1"; shift ;;
    esac
  done
  [ -n "$arg" ] || usage 1
  path=$(resolve_worktree_path "$(sanitize "$arg")")
  [ -n "$path" ] || gg_die "no worktree found for '$arg'"
  # shellcheck disable=SC2086
  git worktree remove $force "$path" || gg_die "worktree remove failed (dirty? use: git wt rm $arg --force)"
  git worktree prune
  gg_warn "removed worktree $path (branch kept — delete after merge with: git branch -d)"
}

main() {
  [ $# -gt 0 ] || usage 1
  case "$1" in
    rm|remove) shift; cmd_rm "$@" ;;
    ls|list) git worktree list ;;
    -h|--help) usage 0 ;;
    *) cmd_create "$@" ;;
  esac
}

main "$@"
