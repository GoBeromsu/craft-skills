#!/usr/bin/env sh
# git-guard check, registered into hookify's .githooks/guards.d/ convention.
# Warns (never blocks) when the branch is behind its upstream. Logic lives in
# scripts/git-guard/check-freshness.sh; this file only execs it.
set -eu

exec "$(git rev-parse --show-toplevel)/scripts/git-guard/check-freshness.sh" warn
