#!/usr/bin/env sh
set -eu

fail() {
  printf 'not ok - %s\n' "$*" >&2
  exit 1
}

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
WT_SH=$(CDPATH= cd -- "$SCRIPT_DIR/../scripts" && pwd)/wt.sh
TMPDIR=${TMPDIR:-/tmp}
TMP=$(mktemp -d "$TMPDIR/wt-test.XXXXXX")
trap 'rm -rf "$TMP"' EXIT INT TERM

# Minimal origin + clone so origin/HEAD -> main resolves.
git init --bare --quiet "$TMP/origin.git"
git --git-dir="$TMP/origin.git" symbolic-ref HEAD refs/heads/main
git -C "$TMP" init --quiet -b main seed
git -C "$TMP/seed" config user.email test@example.com
git -C "$TMP/seed" config user.name 'Test User'
printf 'root\n' >"$TMP/seed/README.md"
git -C "$TMP/seed" add README.md
git -C "$TMP/seed" commit --quiet -m initial
git -C "$TMP/seed" remote add origin "$TMP/origin.git"
git -C "$TMP/seed" push --quiet -u origin main
git clone --quiet "$TMP/origin.git" "$TMP/repo"
git -C "$TMP/repo" remote set-head origin main

run() { ( cd "$TMP/repo" && env WORKTREE_ROOT="$TMP/worktrees" sh "$WT_SH" "$@" ); }

# create
created=$(run lane-1)
[ "$created" = "$TMP/worktrees/lane-1" ] || fail "unexpected worktree path: $created"
[ -d "$created" ] || fail 'worktree dir was not created'
git -C "$TMP/repo" show-ref --verify --quiet refs/heads/lane-1 || fail 'branch lane-1 was not created'

# reuse: same name returns the same worktree, no duplicate
# (-ef compares the resolved file, tolerating /var vs /private/var on macOS)
reused=$(run lane-1)
[ "$reused" -ef "$created" ] || fail "reuse should return same path: $reused"
count=$(git -C "$TMP/repo" worktree list --porcelain | grep -c '^worktree ')
[ "$count" -eq 2 ] || fail "expected primary + 1 worktree, got $count"

# rm: worktree gone, branch kept
run rm lane-1 >/dev/null 2>&1 || fail 'wt rm failed'
[ ! -e "$created" ] || fail 'worktree dir should be removed'
git -C "$TMP/repo" show-ref --verify --quiet refs/heads/lane-1 || fail 'branch should be kept after rm'

echo 'ok - wt create / reuse / rm'
