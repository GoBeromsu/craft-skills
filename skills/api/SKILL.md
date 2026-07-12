---
name: api
description: "Defines and evolves public HTTP API contracts while preserving published incumbent behavior. Use when asked to design the public REST contract for a resource, document an endpoint contract, choose API pagination or error shapes, standardize a greenfield REST API, or API 계약을 설계할 때. Not for service structure or persistence — use backend; client rendering or state — use frontend; or transport-level test design — use testing."
metadata:
  version: 1.1.0
---

# api

Define a public HTTP contract before handlers, schemas, or client calls. A contract is complete when its published behavior is preserved or its versioned migration is explicit, and the documented requests and responses can be exercised by clients.

## Contract gate

Inspect the repository's published API before choosing a convention. Record its URL base, success envelope, pagination model, field naming, and error shape from routes, clients, API descriptions, and deployed examples. Preserve that incumbent contract for existing APIs.

Change a published contract only in an explicitly scoped version or migration. State the affected clients, compatibility behavior, rollout or deprecation path, and how clients verify the transition. Do not call an undocumented or unobserved surface greenfield.

For a greenfield API or an explicitly new version, apply the defaults in [conventions.md](references/conventions.md). That reference owns URL, DTO, naming, and pagination rules. Apply [error-contract.md](references/error-contract.md) for failure behavior; it owns the greenfield problem shape, codes, mapping, and sanitization.

## Verification

- [ ] Repository evidence identifies the incumbent contract, or explains why the API is genuinely greenfield.
- [ ] Existing endpoints preserve their published URL, envelope, pagination, naming, and error behavior.
- [ ] Any public-contract change names its version or migration scope and client-compatibility note.
- [ ] New or explicitly versioned surfaces follow the relevant convention and error references.
- [ ] Exercise representative success, empty or next-page, expected-failure, and sanitized unexpected-failure scenarios through the contract boundary.

## Boundaries

Route service structure, database migration strategy, ORM selection, and persistence implementation to `backend`. Route UI data fetching, rendering, and client state to `frontend`. Route test taxonomy and fixture strategy to `testing`; this skill owns the contract those tests exercise.