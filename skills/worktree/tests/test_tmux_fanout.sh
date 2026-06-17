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
FANOUT_SH=$(CDPATH= cd -- "$SCRIPT_DIR/../scripts" && pwd)/tmux-fanout.sh
TMPDIR=${TMPDIR:-/tmp}
TMP=$(mktemp -d "$TMPDIR/tmux-fanout-test.XXXXXX")
trap 'rm -rf "$TMP"' EXIT INT TERM

sh -n "$FANOUT_SH"

mkdir -p "$TMP/bin"
cat >"$TMP/bin/tmux" <<'TMUX'
#!/usr/bin/env sh
set -eu
printf '%s\n' "$*" >>"$TMUX_TEST_LOG"
case "$1" in
  has-session)
    if [ -f "$TMUX_TEST_SESSION" ]; then exit 0; fi
    exit 1
    ;;
  new-session)
    : >"$TMUX_TEST_SESSION"
    exit 0
    ;;
  list-windows)
    printf '%s\n' api
    exit 0
    ;;
  new-window)
    exit 0
    ;;
  *) exit 0 ;;
esac
TMUX
chmod +x "$TMP/bin/tmux"

set +e
env PATH="/bin:/usr/bin" sh "$FANOUT_SH" 42 api >"$TMP/missing.out" 2>"$TMP/missing.err"
missing_status=$?
set -e
[ "$missing_status" -ne 0 ] || fail 'missing tmux should fail'
missing_err=$(cat "$TMP/missing.err")
assert_contains "$missing_err" 'tmux not found'
assert_contains "$missing_err" 'git wt <issue#> --slug <slice>'

: >"$TMP/log"
SESSION_FILE="$TMP/session"
env PATH="$TMP/bin:$PATH" TMUX_TEST_LOG="$TMP/log" TMUX_TEST_SESSION="$SESSION_FILE" \
  sh "$FANOUT_SH" 42 api ui 'QA Slice' >"$TMP/out" 2>"$TMP/err"

out=$(cat "$TMP/out")
log=$(cat "$TMP/log")
err=$(cat "$TMP/err")
assert_contains "$out" 'tmux attach -t wt-42'
assert_contains "$log" 'has-session -t wt-42'
assert_contains "$log" 'new-session -d -s wt-42 -n api'
assert_contains "$log" "git wt '42' --slug 'api'"
assert_contains "$log" 'new-window -t wt-42 -n ui'
assert_contains "$log" "git wt '42' --slug 'ui'"
assert_contains "$log" 'new-window -t wt-42 -n qa-slice'
assert_contains "$log" "git wt '42' --slug 'QA Slice'"
assert_contains "$err" 'created tmux session wt-42 window api'

: >"$TMP/log"
env PATH="$TMP/bin:$PATH" TMUX_TEST_LOG="$TMP/log" TMUX_TEST_SESSION="$SESSION_FILE" \
  sh "$FANOUT_SH" 42 api ui >"$TMP/idempotent.out" 2>"$TMP/idempotent.err"
idempotent_log=$(cat "$TMP/log")
idempotent_err=$(cat "$TMP/idempotent.err")
assert_contains "$idempotent_err" 'using existing tmux session wt-42'
assert_contains "$idempotent_err" 'window wt-42:api already exists; skipping slice api'
assert_contains "$idempotent_log" 'new-window -t wt-42 -n ui'

set +e
env PATH="$TMP/bin:$PATH" TMUX_TEST_LOG="$TMP/log" TMUX_TEST_SESSION="$SESSION_FILE" \
  sh "$FANOUT_SH" nope api >"$TMP/bad.out" 2>"$TMP/bad.err"
bad_status=$?
set -e
[ "$bad_status" -ne 0 ] || fail 'non-numeric issue should fail'
bad_err=$(cat "$TMP/bad.err")
assert_contains "$bad_err" 'issue number must be numeric'

echo 'ok - tmux local fan-out helper'
