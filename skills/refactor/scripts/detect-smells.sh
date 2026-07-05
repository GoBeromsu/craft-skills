#!/usr/bin/env bash
# detect-smells.sh — mechanical code-smell reporter for skills/refactor.
#
# Usage: detect-smells.sh [target-dir]   (defaults to .)
# Output: one finding per line, format "RULE-ID file:line  detail".
# This is a REPORTER, not a gate — it always exits 0. Every rule is a cheap,
# approximate grep/awk/find heuristic (no interpreters, no git, no third-party
# binaries beyond the coreutils that ship with any POSIX shell: grep, awk,
# find, sort, uniq, wc, cut). Read the false-positive comment on each rule
# before acting on a finding — every rule trades recall for zero setup cost.
set -u

target="${1:-.}"
files() {
  find "$target" \( -name '*.py' -o -name '*.ts' -o -name '*.tsx' -o -name '*.js' \) \
    -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/dist/*' \
    -not -path '*/build/*' -not -path '*/.venv/*' 2>/dev/null
}

# SIZE-LONGFN: function body > 40 lines, measured from a def/function line to
# the next def/function/class at the same-or-lower indentation.
# False-positive profile: indentation-based, not AST-based — decorators,
# multi-line signatures, and brace-only nesting (dense one-liner TS) skew the
# count; misses functions nested deeper than one level of indentation drift.
check_long_function() {
  local f
  for f in $(files); do
    awk -v FN="$f" '
      match($0, /^[ \t]*/) { indent = RLENGTH }
      /^[ \t]*(def |async def |function |export function |export default function )/ {
        if (start && (NR - start) > 40) print FN":"start"  SIZE-LONGFN ("(NR-start)" lines)"
        start = NR; base = indent; next
      }
      start && indent <= base && NR > start + 1 && !/^[ \t]*$/ {
        if ((NR - start) > 40) print FN":"start"  SIZE-LONGFN ("(NR-start)" lines)"
        start = 0
      }
      END { if (start && (NR - start) > 40) print FN":"start"  SIZE-LONGFN ("(NR-start)" lines)" }
    ' "$f"
  done
}

# SIZE-PARAMS: 4+ comma-separated params on a single-line def/function signature.
# False-positive profile: misses multi-line signatures entirely; a tuple or
# dict literal used as a default value inflates the comma count.
check_long_param_list() {
  local f
  for f in $(files); do
    grep -nE '^[ \t]*(def |function |async function |export function )[A-Za-z_]' "$f" 2>/dev/null \
      | while IFS=: read -r ln rest; do
          inner=$(printf '%s' "$rest" | sed -n 's/^[^(]*(\(.*\)).*/\1/p')
          commas=$(printf '%s' "$inner" | tr -cd ',' | wc -c)
          [ "$commas" -ge 3 ] && echo "$f:$ln  SIZE-PARAMS ($((commas + 1)) params)"
        done
  done
}

# SIZE-NESTING: 4+ levels of leading-indentation depth on a control line.
# False-positive profile: indentation ≠ true nesting depth for brace languages
# that allow single-line `if (x) return;`; tab/space mixing skews the count.
check_deep_nesting() {
  local f
  for f in $(files); do
    awk -v FN="$f" '
      /^[ \t]*(if|elif|else if|for|while|switch)[ \t(:]/ {
        line = $0
        gsub(/\t/, "    ", line)
        match(line, /^[ ]*/)
        depth = int(RLENGTH / 4)
        if (depth >= 4) print FN":"NR"  SIZE-NESTING (depth "depth")"
      }
    ' "$f"
  done
}

# ABSTR-MAGIC: a bare numeric literal other than 0/1/-1/100 used inline,
# outside a constant declaration.
# False-positive profile: array indices, loop counters, and version numbers
# in comments/strings are frequent false positives — read before renaming.
check_magic_literal() {
  local f
  for f in $(files); do
    grep -nE '[^A-Za-z0-9_.]([2-9]|[1-9][0-9]+)[^A-Za-z0-9_.]' "$f" 2>/dev/null \
      | grep -vE '^[^:]*:[0-9]+:[ \t]*(const|let|final|[A-Z_]+[ \t]*[:=])' \
      | grep -vE '^\s*#|^\s*//' \
      | head -50 | while IFS=: read -r ln rest; do
          echo "$f:$ln  ABSTR-MAGIC"
        done
  done
}

# ABSTR-DEADCODE: commented-out code — a comment line whose remainder still
# parses as a statement (def/function/if/return/assignment).
# False-positive profile: this is a cheap first pass only; a genuinely dead
# (unreachable, never-called) LIVE function is NOT caught here — pair with
# vulture/ts-prune/coverage per references/code-smells.md.
check_dead_code_marker() {
  local f
  for f in $(files); do
    grep -nE '^[ \t]*(#|//)[ \t]*(def |function |if |return |[A-Za-z_]+[ \t]*=[^=])' "$f" 2>/dev/null \
      | while IFS=: read -r ln rest; do
          echo "$f:$ln  ABSTR-DEADCODE (commented-out code)"
        done
  done
}

# COUPLING-CHAIN: 4+ chained `.` member/method accesses on one line.
# False-positive profile: fluent builder APIs (query builders, test
# assertion chains) are idiomatic chains, not Law-of-Demeter violations.
check_message_chain() {
  local f
  for f in $(files); do
    grep -noE '([A-Za-z_][A-Za-z0-9_]*\.){4,}[A-Za-z_][A-Za-z0-9_]*' "$f" 2>/dev/null \
      | while IFS=: read -r ln rest; do
          echo "$f:$ln  COUPLING-CHAIN"
        done
  done
}

# DUP-BLOCK: an exact, whitespace-normalized line of 20+ chars repeated 3+
# times across the tree (blank/comment-only lines excluded).
# False-positive profile: floor only — catches literal repetition, not
# renamed-variable near-duplicates; boilerplate (license headers, imports)
# is a frequent, usually-fine false positive.
check_duplicate_lines() {
  local flist
  flist=$(files)
  [ -z "$flist" ] && return
  # shellcheck disable=SC2086
  awk '
    /^[ \t]*(#|\/\/)/ { next }
    /^[ \t]*$/ { next }
    {
      line = $0
      gsub(/^[ \t]+|[ \t]+$/, "", line)
      if (length(line) < 20) next
      count[line]++
      if (!(line in firstfile)) { firstfile[line] = FILENAME; firstln[line] = FNR }
    }
    END {
      for (line in count) if (count[line] >= 3) print firstfile[line]":"firstln[line]"  DUP-BLOCK (repeated "count[line]"x)"
    }
  ' $flist
}

# COMMENT-DEODORANT: comment-line-to-code-line ratio > 0.3 in a file.
# False-positive profile: heavily-documented public APIs legitimately exceed
# this ratio — grey zone, judge by whether comments explain WHY or narrate
# WHAT the next line already says.
check_comment_ratio() {
  local f total comments ratio
  for f in $(files); do
    total=$(grep -vc '^[[:space:]]*$' "$f" 2>/dev/null)
    [ "${total:-0}" -lt 20 ] && continue
    comments=$(grep -cE '^[[:space:]]*(#|//)' "$f" 2>/dev/null)
    ratio=$(awk -v c="$comments" -v t="$total" 'BEGIN { printf "%.2f", (t > 0 ? c / t : 0) }')
    awk -v r="$ratio" -v f="$f" 'BEGIN { if (r + 0 > 0.3) print f":1  COMMENT-DEODORANT (ratio "r")" }'
  done
}

check_long_function
check_long_param_list
check_deep_nesting
check_magic_literal
check_dead_code_marker
check_message_chain
check_duplicate_lines
check_comment_ratio

exit 0
