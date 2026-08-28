# Changelog

- 2026-07-05 — v1.0.0: no unified security recipe → trust-boundary + severity triage for web/api/llm/secrets. Provenance: addyosmani/agent-skills, OWASP.
- 2026-07-05 — v1.0.1: allowed-tools missing Write/Edit despite the action boundary applying fixes directly → added; expanded the RAG acronym at first use.
- 2026-07-06 — v2.0.0: realign to vendor-official authoring contract → spec-minimal frontmatter, what+when description, boundaries in Hand-offs, refs get ToCs.
- 2026-07-06 — v2.0.1: contract adopted a single anti-patterns registry → merged Red Flags + Common Rationalizations into ## Anti-patterns.
- 2026-07-12 — v2.1.0: reachability-scoped supply-chain review, evidence-only review boundaries, and adversarial guard-retention principles needed explicit ownership → scoped routing, review/fix separation, and regression-proven removal of trust-boundary guards. Provenance: remove-ai-slops transfer from docs/research/omo-analysis.md.
- 2026-08-28 — v2.2.0: mutable audit-tool and framework facts need runtime evidence handling → official-docs-first conflict disclosure, specific-evidence precedence, and safe unknowns without invented commands or capabilities.
- 2026-08-28 — v2.3.0: a pull-request CI workflow runs fork-authored code but was not treated as an ingress channel → added the untrusted-CI trust boundary to trust-boundary mapping, with SHA pinning, consumer-level token gating, no-cache-on-fork-trigger, template-injection, and job-timeout rules proven by mutation tests. Provenance: measured fork-trust rules absorbed from the operator-supplied `security-and-hardening` skill (~/seeon-backups/omc-learned-backup-20260828T105212Z/security-and-hardening.md), grounded in a SeeON-edge CI restructure.
- 2026-08-28 — v2.3.1: the skill that owns turning a finding into enforced prevention was renamed → the description boundary and the routing line now name `guardrails`.
