# Changelog

- 2026-07-12 — v1.0.0: ported obsidian-plugin-doctor into craft-skills as `obsidian-doctor` → six-step Inspect→Diagnose→Consult→Patch→Verify→Learn pipeline over a package-local `references/plugins.yaml` seed registry; genericized the worked example and dropped vault-specific registry/log paths. Provenance: bstack obsidian-tools/obsidian-plugin-doctor.
- 2026-08-27 — v2.0.0: moved from GoBeromsu/craft-skills@ca9eb6c8 skills/obsidian-doctor, converted frontmatter to the bstack 5-key contract (name/description/version/allowed-tools/compatibility), and renamed to `obsidian/doctor` as part of the domain-topology reorganization.
- 2026-08-27 — v2.0.1: hermes skills_guard compatibility (round 2, leaf-accurate scan): detached the `[[...]]` YAML bracket-path notation in SKILL.md from the adjacent `references/plugins.yaml` file path so it no longer parses as a suspicious local-reference traversal; no behaviour change.
- 2026-08-28 — v3.0.0: moved the active Obsidian doctor skill from GoBeromsu/bstack@3e0672c into craft-skills as `obsidian-doctor`, replacing the deprecated stub and restoring craft-skills as the reusable Obsidian-craft owner.
