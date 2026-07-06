#!/usr/bin/env bash
# Smoke tests for the technical-report engine. No project data required —
# parses the template frame and runs the validators' built-in negative fixtures.
set -u

SKILL_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
YAML="$SKILL_DIR/technical-report.template.yaml"
fail=0

note() { printf '%s\n' "$*"; }
expect_exit() { # <expected> <label> <cmd...>
  local want="$1" label="$2"; shift 2
  "$@" >/dev/null 2>&1; local got=$?
  if [ "$got" = "$want" ]; then
    note "  ok    $label (exit $got)"
  else
    note "  FAIL  $label (want exit $want, got $got)"; fail=1
  fi
}

note "[1] frame parses + validate.py runs (missing book files => exit 1)"
emptybook="$(mktemp -d)"
expect_exit 1 "validate.py on empty book" \
  python3 "$SKILL_DIR/validate.py" --yaml "$YAML" --book "$emptybook"
rmdir "$emptybook" 2>/dev/null || true

note "[2] validate_sources.py negative fixtures each fail (exit 1)"
for fx in missing-must missing-local stale-current duplicate-section secret-leak; do
  expect_exit 1 "fixture:$fx" \
    python3 "$SKILL_DIR/validate_sources.py" --yaml "$YAML" --fixture "$fx"
done

if [ "$fail" = 0 ]; then note "ALL PASS"; else note "FAILURES"; fi
exit "$fail"
