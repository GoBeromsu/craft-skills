---
name: changelog
description: '"write a changelog", "update the changelog", "release notes", "what changed in this version", "keep a changelog" — author the project-level CHANGELOG.md grouped by Added/Changed/Fixed per release. Loaded on demand by the documents waypoint.'
---

# changelog

Author the project-level `CHANGELOG.md`: a human-facing record of notable changes per release, written for the people who **use** the project. Template: `template.md` (beside this file). Canonical location: repo root `CHANGELOG.md`.

This is the user-facing project changelog, distinct from a per-skill or per-package internal changelog. It answers "what changed for me between versions?" — group entries by change type, newest release on top.

## Structure

- An **`[Unreleased]`** section stays open at the top; new entries land there as work merges.
- When a release is cut, rename `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD` and open a fresh `[Unreleased]` above it.
- Within each release, group entries under the change types that apply:

| Type | Use for |
|------|---------|
| Added | New features |
| Changed | Changes to existing behavior |
| Deprecated | Features soon to be removed |
| Removed | Features removed in this release |
| Fixed | Bug fixes |
| Security | Vulnerability fixes |

## Writing entries

- Write each entry from the **user's** point of view — the visible change, not the internal commit. "Fixed crash when importing an empty file" beats "fixed null check in parser."
- One change per bullet. A bullet that needs "and" is usually two entries.
- Note any migration the user must perform under **Changed** or **Removed**.
- Version numbers follow semver: `MAJOR` breaks the contract, `MINOR` adds backward-compatible behavior, `PATCH` fixes bugs.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "The git log is the changelog." | Commits are for developers and record how; the changelog is for users and records what changed for them. They are different audiences. |
| "I'll paste the commit subjects." | Commit subjects describe internals. Rewrite each as the user-visible effect. |
| "I'll write it all at release time." | Entries written months later lose the user-facing framing. Add to `[Unreleased]` as you go. |
| "Group by file, not by change type." | Users scan by Added/Changed/Fixed, not by which file moved. Group by type. |

## Red flags

- Changelog entries that are raw commit subjects
- A flat list with no Added/Changed/Fixed grouping
- A breaking change filed without a migration note
- No `[Unreleased]` section to collect in-flight changes

## Verification

- [ ] Newest release is on top; an `[Unreleased]` section is open
- [ ] Entries are grouped by change type (Added/Changed/Fixed/…)
- [ ] Each entry is written from the user's point of view, one change per bullet
- [ ] Breaking changes carry a migration note
- [ ] Version numbers follow semver
