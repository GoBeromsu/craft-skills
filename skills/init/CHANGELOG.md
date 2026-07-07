# Changelog

- 2026-06-13 — v1.0.0: no docs/ bootstrap existed → scaffolds docs/ ontology + ADR index, delegates architecture/README to document, wires git-guard.
- 2026-06-17 — v1.1.0: governance lacked shared config resolution → added a governance-config resolver + GitHub label installer/verifier scripts.
- 2026-06-17 — v1.1.0: issue triage lacked a Type label + auto-label enforcement → added an issue Type template + fail-closed auto-label workflow.
- 2026-06-17 — v1.1.0: no PR size gate existed → added an S3 PR size-check workflow with churn thresholds, base guards, verifier drift checks.
- 2026-06-17 — v1.1.0: Development Flow had no GitHub-governance wiring → added an S6 scaffold wired into the governance installer/verifier rails.
- 2026-06-30 — v2.0.0: governance/audit machinery was overkill → rebuilt init as dual-entry: docs/ ontology graft + AGENTS.md cartography engine. BREAKING.
- 2026-06-30 — v2.0.0: a 4-phase engine would break triage-depth if inlined → split into references/phase-0..4.md; SKILL.md stays triage-only.
- 2026-06-30 — v2.0.0: the graft needed document's new layout → phase-0-ontology.md seeds docs/ + ADR index from document/templates/*.md.
- 2026-06-30 — v2.0.0: the engine assumed agent fan-out only → added a sequential single-agent fallback for Hermes/generic; centrality now optional/unmeasured.
- 2026-06-30 — v2.0.0: degraded runs could pass silently → every run ends with an observability report; root AGENTS.md gains a DOCS & DECISIONS section.
- 2026-06-30 — v2.0.0: governance/audit machinery was tombstoned → removed scripts/ + tests/ trees; git-guard moved to git; block now convention-only.
- 2026-06-30 — v2.1.0: no rail caught scope creep mid-change → Development Flow block gained an out-of-scope routing convention: open a new issue instead (#21).
- 2026-07-06 — v3.0.0: realign to vendor-official authoring contract → spec-minimal frontmatter, what+when description, naming fixed, phase refs gain ToCs.
- 2026-07-06 — v3.0.1: contract adopted a single anti-patterns registry → Red Flags reshaped into ## Anti-patterns with behavior → fix entries.
- 2026-07-07 — v3.0.2: operator correction rejected implicit ADR pressure → init now scaffolds only craft-owned docs folders/files, keeps `docs/decisions/README.md` explicit-only, stops README seeding, and records an anti-pattern against creating or requiring ADRs without an explicit ask. Provenance: delegated team instruction in `eldercare-fall-ai/.omo/teams/team-e61e6580/guide.md`.
