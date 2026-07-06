#!/usr/bin/env sh
# git-guard check, registered into hookify's .githooks/guards.d/ convention.
# Blocks model weights, media files, and blobs > 5 MB staged for commit. Logic
# lives in scripts/git-guard/deny-assets.sh; this file only execs it.
set -eu

exec "$(git rev-parse --show-toplevel)/scripts/git-guard/deny-assets.sh" staged
