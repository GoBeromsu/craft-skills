# Changelog

- 2026-06-26 — v0.1.1: YAML SSOT could be placed under a tool-private dir (`.claude/`, `.codex/`, `.gjc/`, `.hermes/`, `.cursor/`) invisible to other runtimes → `SKILL.md` Setup + `.env.example` now warn to keep `technical-report.yaml` at a tool-neutral path (repo root or `docs/`); docs-only, no validator/runtime change (#18).
- 2026-06-25 — v0.1.0: technical-report was a project-local skill with hardcoded paths and project-specific content → promoted to portable engine: split into a reusable empty frame (`technical-report.template.yaml`) and a two-mode engine (Scaffold depth-1 interview + Author/Validate), validators now resolve paths via `$TECHNICAL_REPORT_YAML` / `$TECHNICAL_REPORT_BOOK` (and `--yaml`/`--book` flags); stripped project-specific content, paths, and named-individual governance; registered in [README](../../README.md)/[AGENTS.md](../../AGENTS.md).
</content>
</invoke>
