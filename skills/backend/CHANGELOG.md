# Changelog

- 2026-07-05 — v1.0.0: no detection or folder convention → architecture gate, dependency rules, API contract, folder trees. Provenance: addyosmani/agent-skills.
- 2026-07-06 — v2.0.0: realign to vendor-official authoring contract → spec-minimal frontmatter, what+when description, body compressed, references deduped.
- 2026-07-06 — v2.0.1: contract adopted a single anti-patterns registry → merged Red Flags + Common Rationalizations into ## Anti-patterns.
- 2026-07-08 — v2.1.0: API base guidance risked per-router prefix duplication → centralized base/prefix/version ownership at app/bootstrap/router composition. Provenance: API boundary rule from [api-boundary-correction](references/api-boundary-correction.md).
- 2026-07-11 — v2.2.0: local persistence could diverge from production and ORM choice lacked a default → real-engine development parity and Prisma-first selection guidance; API contracts moved to `api`. Provenance: operator-supplied persistence rationale.
