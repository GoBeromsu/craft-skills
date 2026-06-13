# Skill PR Branch Hygiene

Use this when a skill-library change is already sitting on an unrelated dirty branch, or when the operator requests a clean branch and PR for a skill change.

## Required sequence

1. Inspect current repo state and stash unrelated local edits if needed.
2. `git fetch origin --prune`.
3. Switch to `main`.
4. `git pull --ff-only origin main`.
5. Create a fresh topic branch for the skill change.
6. Restore only the relevant skill diff; do not drag unrelated old branch state into the PR.
7. Validate, commit, push, and open a PR unless the operator explicitly requested local-only.

## Pitfall

Do not treat "I patched the skill file" as completion. For craft-skills skill changes, the durable deliverable is reviewable repo state: branch + commit + PR, or an explicit blocker with the exact uncompleted step.
