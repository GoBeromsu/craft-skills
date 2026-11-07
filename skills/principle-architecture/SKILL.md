---
name: principle-architecture
description: "Guides cross-domain structural decisions before implementation. Use when choosing core data structures, integrating a requirement into an existing design, comparing architectures without precedent, planning a rewrite, retiring internal APIs, or isolating concurrent writers to a file or branch. Service structure and persistence belong to principle-backend, published HTTP contracts to api, and rendered UX to design. The architect workflow owns design sketches and implementation coordination; this skill supplies the structural principles it applies."
metadata:
  version: 1.0.0
---

# principle-architecture

Choose structures that make the intended end state verifiable without duplicating domain policy.
Record the structural decision, affected callers or writers, and verification boundaries in the target project's existing plan or design artifact.
If the constraints do not settle the design, compare concrete alternatives before implementation.

## When it applies

Load the matching principle before changing core data shapes, integrating requirements, coordinating an internal migration, or deciding what concurrent actors share.
For two parallel agents writing to one branch, load [Separate Before Serializing Shared State](references/separate-before-serializing-shared-state.md) before choosing coordination.
Keep service architecture and persistence with the principle-backend skill, published-contract changes with api, and rendered UX decisions with design.
Use the architect workflow for sketches and implementation coordination, and cicd for deployment repeats.

## Principles

- [Foundational Thinking](references/foundational-thinking.md) chooses the core data structures before writing logic.
- [Redesign from First Principles](references/redesign-from-first-principles.md) integrates a new requirement as if it had been a foundational assumption from the start.
- [Exhaust the Design Space](references/exhaust-the-design-space.md) builds two or three competing prototypes when there's no precedent.
- [Outcome-Oriented Execution](references/outcome-oriented-execution.md) converges rewrites on the target design instead of preserving throwaway compatibility states.
- [Migrate Callers Then Delete Legacy APIs](references/migrate-callers-then-delete-legacy-apis.md) migrates and deletes in one wave.
- [Separate Before Serializing Shared State](references/separate-before-serializing-shared-state.md) removes the sharing before adding coordination.
