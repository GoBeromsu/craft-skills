# Changelog

- 2026-07-12 — v1.0.0: ported the Obsidian CLI skill into craft-skills → vendor-agnostic `obsidian-cli` operating surface (prereq resolution, write-then-readback verification, wrapper-confusion triage, destructive-op guard) with vault name/path fully env-indirected. Provenance: bstack obsidian-tools/obsidian-cli.
- 2026-08-27 — v2.0.0: moved from GoBeromsu/craft-skills@ca9eb6c8 skills/obsidian-cli, converted frontmatter to the bstack 5-key contract (name/description/version/allowed-tools/compatibility), and renamed to `obsidian/cli` as part of the domain-topology reorganization.
- 2026-08-28 — v3.0.0: moved the active Obsidian cli skill from GoBeromsu/bstack@3e0672c into craft-skills as `obsidian-cli`, replacing the deprecated stub and restoring craft-skills as the reusable Obsidian-craft owner.
