#!/usr/bin/env sh
set -eu

fail() {
  printf 'not ok - %s\n' "$*" >&2
  exit 1
}

assert_contains() {
  haystack=$1
  needle=$2
  case "$haystack" in
    *"$needle"*) ;;
    *) fail "expected output to contain: $needle\nactual: $haystack" ;;
  esac
}

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
WT_SH=$(CDPATH= cd -- "$SCRIPT_DIR/../scripts" && pwd)/wt.sh
TMPDIR=${TMPDIR:-/tmp}
TMP=$(mktemp -d "$TMPDIR/wt-test.XXXXXX")
trap 'rm -rf "$TMP"' EXIT INT TERM

mkdir -p "$TMP/bin"
cat >"$TMP/bin/gh" <<'GH'
#!/usr/bin/env sh
set -eu
case " $* " in
  *" --json title "*) printf '%s\n' "${WT_TEST_TITLE:-Implement Default Title}" ;;
  *" --json labels "*) printf '%s' "${WT_TEST_TYPE:-}" ;;
  *) exit 1 ;;
esac
GH
chmod +x "$TMP/bin/gh"

mkdir -p "$TMP/origin.git" "$TMP/seed"
git init --bare --quiet "$TMP/origin.git"
git -C "$TMP/seed" init --quiet -b main
git -C "$TMP/seed" config user.email test@example.com
git -C "$TMP/seed" config user.name 'Test User'
printf 'root\n' >"$TMP/seed/README.md"
git -C "$TMP/seed" add README.md
git -C "$TMP/seed" commit --quiet -m initial
git -C "$TMP/seed" remote add origin "$TMP/origin.git"
git -C "$TMP/seed" push --quiet -u origin main
git --git-dir="$TMP/origin.git" symbolic-ref HEAD refs/heads/main
git clone --quiet "$TMP/origin.git" "$TMP/repo"

(
  cd "$TMP/repo"
  env PATH="$TMP/bin:$PATH" WORKTREE_ROOT="$TMP/worktrees" WT_TEST_TITLE='Ignored Title' WT_TEST_TYPE='' \
    sh "$WT_SH" 77 --type fix --slug 'API v2 Slice!' >"$TMP/out" 2>"$TMP/err"
)
created=$(cat "$TMP/out")
[ "$created" = "$TMP/worktrees/fix/77-api-v2-slice" ] || fail "unexpected worktree path: $created"
git -C "$TMP/repo" show-ref --verify --quiet refs/heads/fix/77-api-v2-slice || fail 'slug branch was not created'
[ ! -e "$created/ml/data" ] || fail 'repo-specific ml/data symlink should not be created'
[ ! -e "$created/ml/models" ] || fail 'repo-specific ml/models symlink should not be created'

set +e
(
  cd "$TMP/repo"
  env PATH="$TMP/bin:$PATH" WORKTREE_ROOT="$TMP/worktrees" WT_TEST_TITLE='Needs Explicit Type' WT_TEST_TYPE='' \
    sh "$WT_SH" 78 >"$TMP/fallback.out" 2>"$TMP/fallback.err"
)
status=$?
set -e
[ "$status" -ne 0 ] || fail 'missing type label should fail without --type'
fallback_err=$(cat "$TMP/fallback.err")
assert_contains "$fallback_err" "pass --type explicitly"
assert_contains "$fallback_err" "missing issue type label"

echo 'ok - wt --slug and explicit type guard'
