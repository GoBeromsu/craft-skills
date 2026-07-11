---
name: api
description: "Defines contract-first HTTP APIs with stable resource URLs, DTO-only success payloads, and diagnosable sanitized failures. Use when doing API 설계, setting REST 규격, asking to design the API, defining REST conventions, documenting an endpoint contract, or standardizing pagination and errors. Not for service architecture, ORM choice, or persistence implementation — use backend; not for client rendering or component state — use frontend; not for version-control history or PR mechanics — use git; not for transport-level test-suite design — use testing."
metadata:
  version: 1.0.0
---

# api

Define an HTTP contract before handlers, schemas, or client calls. A surface is complete when its resource URL, request and response DTOs, pagination behavior, and failure shapes are written and the client reaches it through one version-prefix boundary.

## Contract gate

Write the resource contract first: method, URL, authorization rule, request DTO, success DTO, error codes, pagination inputs and outputs, and examples of expected failures. Keep the public URL base as `/api/v1` in one server bootstrap/global-prefix location and one client base-URL configuration. Handlers and clients own only resource-local paths.

Model collection resources with plural kebab-case nouns and express containment as hierarchy, for example `/api/v1/team-members` and `/api/v1/teams/{teamId}/members`. Use verbs only when an operation cannot be modeled as a resource.

Read [conventions.md](references/conventions.md) before naming routes or DTO fields, and [error-contract.md](references/error-contract.md) before implementing exception mapping.

## Success contract

Return the DTO itself as the success payload; do not add a generic `data`, `result`, or `message` envelope. Serialize JSON keys in camelCase. Name boolean fields with `is`, `has`, or `can`; serialize enum values as `UPPER_SNAKE`.

Every list endpoint paginates. Choose the repository's incumbent pagination model; for a new API default to cursor pagination when a stable sort key exists, otherwise use bounded offset pagination. Include the input cursor or page parameters and enough response metadata for the client to request the next page without inferring hidden state.

Validate inputs at the DTO boundary, where malformed transport data first enters the application. Keep domain and persistence layers on typed values rather than duplicating request validation downstream.

## Failure contract

Map application failures to RFC 7807 `ProblemDetail` with `type`, `title`, `status`, `detail`, and `instance`, plus one domain `code`. Define errors in a domain-owned `ErrorCode` enum using `DDD_001`-style values, and reserve `SYS_xxx` codes for system taxonomy. Do not claim transport-layer failures such as HTTP 431 as application API contract errors.

Log diagnostics for unknown exceptions and 5xx failures, then return a sanitized problem response. Do not expose stack traces, query text, credentials, or internal implementation details.

## Verification

- [ ] The endpoint contract names one `/api/v1` base owner on server and one base URL owner in the client.
- [ ] Resource paths use plural kebab-case nouns and hierarchy only for actual containment.
- [ ] Every success response is the documented DTO without a wrapper envelope.
- [ ] Every list contract includes pagination request fields and a navigable next-page response shape.
- [ ] Expected failures map to `ProblemDetail` plus an owned `ErrorCode`; unknown failures are logged and sanitized.
- [ ] Boundary DTOs validate transport input once, and sample responses use camelCase plus boolean and enum conventions.

## Boundaries

Route backend service structure, database migration strategy, ORM selection, and persistence implementation to `backend`. Route UI data fetching, rendering, and client state to `frontend`. Route test taxonomy and fixture strategy to `testing`; this skill owns the contract that those tests exercise.

## References

- [Pullit API Design Guide](https://pullit-docs-server.vercel.app/index.html#02-api-design)
- [addyosmani/agent-skills API and interface design](https://github.com/addyosmani/agent-skills/tree/main/skills/api-and-interface-design)
