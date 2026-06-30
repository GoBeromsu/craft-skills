---
name: api-docs
description: '"document this API", "write JSDoc", "add doc comments", "document the endpoint", "OpenAPI spec", "document the function" — document a public API surface (function/method doc comments or REST endpoints) by its contract. Loaded on demand by the documents waypoint.'
---

# api-docs

Document a public API surface so a caller can use it without reading the implementation. Template: `template.md` (beside this file) — a doc-comment skeleton and an OpenAPI fragment.

Document the **contract, not the implementation**: what goes in, what comes out, what errors are raised, and one real example. The implementation is free to change; the contract is the promise.

## Pick the surface

```
in-code function / method / class   →  doc-comment block (JSDoc / TSDoc / docstring / Javadoc)
REST HTTP endpoint (external API)   →  OpenAPI / Swagger fragment
```

## Doc comments (functions / methods)

Every public function, method, or class carries a doc comment with four contract facts:

- **Parameters** — each name, its type, meaning, whether required, and valid range/units.
- **Return** — the type and what it represents, including the empty/zero case.
- **Errors** — each error/exception type and the condition that triggers it.
- **One example** — a single real call and its result.

Use the language's native convention — JSDoc/TSDoc `@param`/`@returns`/`@throws`/`@example`, Python docstring `Args:`/`Returns:`/`Raises:`, Javadoc, Go doc comments. The vocabulary changes; the four facts do not. Document only the **public** surface — internal helpers are documented by clear naming and inline why-comments (see the `inline-comments` sub-recipe), not by full contract blocks.

## REST endpoints (OpenAPI)

For an HTTP API consumed by external clients, document each endpoint as an OpenAPI fragment: path + method, parameters (name/in/required/schema), request body schema, and every response status with its meaning — success and the error cases. Reference shared models via `$ref` to `components/schemas/` rather than inlining the same shape twice.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "The function name says what it does." | A name hints at intent; it does not state the valid input range, the error conditions, or the empty-result case. The contract does. |
| "I'll document the happy path; errors are obvious." | The error contract is the half callers most need — undocumented throws become production surprises. List every error and its trigger. |
| "I'll add the example later." | One real call is the fastest way a caller learns the surface, and writing it is the first test that the signature is usable. Add it now. |
| "Internal helpers need full doc blocks too." | Document the public surface. Over-documenting internals is noise that goes stale; name them well and explain the why inline. |

## Red flags

- A public function with no documented error conditions
- A doc comment that narrates the implementation instead of the contract
- An OpenAPI endpoint missing its error responses
- The same model shape inlined in multiple endpoints instead of a shared `$ref`
- Full contract blocks on private helpers (noise)

## Verification

- [ ] Every public function/method/class has a doc comment with params, return, errors, and one example
- [ ] The empty/zero/error cases are documented, not only the happy path
- [ ] REST endpoints list every response status with its meaning
- [ ] Shared models are referenced via `$ref`, not duplicated
- [ ] Comments state the contract, not the implementation
