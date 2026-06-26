# Changelog

- 2026-06-26 — v0.1.1 warn against tool-private YAML placement (#18). `SKILL.md` Setup and
  `.env.example` now state the `technical-report.yaml` SSOT must live at a tool-neutral path
  (repo root or `docs/`), never under a single tool's private dir (`.claude/`, `.codex/`,
  `.gjc/`, `.hermes/`, `.cursor/`) where other runtimes cannot discover it. Docs-only; no
  validator or runtime change.
- 2026-06-25 — Harvest-stage draft (v0.1.0). Promoted from a project-local skill into a
  portable engine: split into a reusable empty frame (`technical-report.template.yaml`) and
  a two-mode engine (Scaffold depth-1 interview + Author/Validate). Generalized both
  validators to resolve paths via `$TECHNICAL_REPORT_YAML` / `$TECHNICAL_REPORT_BOOK` (and
  `--yaml`/`--book` flags) instead of skill-relative constants; stripped project-specific
  content, paths, and named-individual governance. Layer-1 (format/hygiene/routing) green;
  Layer-2 consensus converged round 3 — all live providers (codex, claude) APPROVE, gemini
  environmentally unavailable (free-tier ineligible). Registered in README/AGENTS.
