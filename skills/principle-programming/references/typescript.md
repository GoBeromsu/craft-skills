# TypeScript reference

Modern TypeScript: strictly typed, built on the project's canonical libraries and toolchain, and correct under async. The compiler is your first line of defense — encode invariants as types, parse untrusted input at boundaries, and give every function a contract the types enforce.

Load this file in full before writing or editing TypeScript. The rules below are deliberate project choices — violations are wrong, not stylistic. Naming, function shape, and structural craft live in `typescript/clean-code.md` — load it alongside this file for green-field code and reviews.

## Contents

- [Tooling](#tooling)
- [Upstream rules](#upstream-rules)
- [The iron list](#the-iron-list)
- [Data modeling — which construct, when](#data-modeling--which-construct-when)
- [Exhaustive switch — the canonical shape](#exhaustive-switch--the-canonical-shape)
- [Error handling — narrow with instanceof](#error-handling--narrow-with-instanceof)
- [tsconfig — beyond `strict: true`](#tsconfig--beyond-strict-true)
- [No-excuse audit (run before declaring done)](#no-excuse-audit-run-before-declaring-done)
- [In tests](#in-tests)
- [Editing an existing file](#editing-an-existing-file)

## Tooling

| Category | Use | Never |
|---|---|---|
| Runtime | Bun (native TS, single binary) | ts-node, tsx |
| Package manager | `pnpm` | npm, yarn (unless a workspace forces it) |
| Linter + formatter | Biome | ESLint, Prettier |
| Type checker | `tsc --noEmit` with strict config | skipping type checking |
| Web framework | Hono | Express |
| Validation | Zod | joi, yup, class-validator |
| ORM | Drizzle | TypeORM, Prisma (unless already in the project) |
| HTTP client | `ky` (default) / `undici` (Node perf) | bare `fetch` in prod, axios, node-fetch |
| Testing | `bun test` / vitest | jest |
| Logging | `pino` | console.log in prod |

Override a default only when the project manifest explicitly picks something else.

## Upstream rules

Apply the [type-system-discipline](type-system-discipline.md) principle skill first.

| Rule | Summary |
|------|---------|
| Discriminated unions | Model variants with a `kind` literal discriminant so impossible states can't be represented. No optional-field bags. |
| Branded types | Brand primitives with `& { readonly __brand: "X" }` so they can't be mixed up. Validate once at the boundary. A brand comes from a verifying type guard (`input is AgentId`), never from `as`. |
| Constructive modeling | Build the shape so the illegal value can't be constructed. `[T, ...T[]]` for non-empty, `[T, T][]` for even length, `start` plus `duration` for a range. Not a runtime guard, not a wish for refinement types. |
| Simplest total type | Keep `T[]` while every operation on it stays total. Strengthen to `NonEmpty<T>` only where the loose type forces `!`, a cast, or a "should never happen" throw. |
| `unknown` over `any` | External data is `unknown`. |
| Schemas before guards | Before hand-writing a property-by-property type guard, use the repository's runtime schema library and infer the type from the schema, such as `z.infer`. |
| No `as` casts | Every `as` is a runtime crash waiting. Cast only after validation. |
| Narrowing hierarchy | Discriminant switch > `in` operator > `typeof`/`instanceof` > user-defined type guard > `as`. |
| Type guards | Must verify the claim. A lying guard is worse than `as` because the bug hides behind a name that says it's safe. Name them `isX` or `hasX`. |
| Exhaustiveness | Inline `const _exhaustive: never = x;` in default arms so the compiler errors when a new variant is added. |
| `satisfies` over `as` | Validates the value without widening literal types. |
| Boundary validation | Parse where data crosses in, into a named domain type. `Record<string, unknown>` (however spelled) stops at that parse. Trust types inside. See the **boundary-discipline** principle skill (`principle-backend/references/boundary-discipline.md`). |
| Schema-derived types | Reach for `Pick`/`Omit`/`Parameters`/`ReturnType`/`Awaited`/`typeof` before declaring a new interface. |
| Object args | Pass objects, not positional, so argument order is self-documenting. Skip on hot paths (per-frame render, tokenizers, parsers). |
| Real tests | Don't mock what you can run. Prefer the framework's real test primitives with leak/disposable checks, and verify UI in a running build. Mock only what you can't run locally. |
| Structured telemetry | Prefer structured logger diagnostics with enough context to debug from an id. No `console.log` in shipped code. |

Examples: [`typescript/patterns.md`](typescript/patterns.md).

## The iron list

1. **Readonly by default** — all `type` / `interface` properties are `readonly`; arrays are `readonly T[]`. Mutable only when mutation is the documented purpose.
2. **Branded types for distinct primitives** — Brand primitives with `& { readonly __brand: "X" }` so they can't be mixed up. Validate once at the boundary.
3. **Exhaustive switch** — Inline `const _exhaustive: never = x;` in default arms so the compiler errors when a new variant is added.
4. **No `any`** — banned in annotations, returns, and parameters. Use `unknown` and narrow.
5. **No `as` casts** — Every `as` is a runtime crash waiting. Cast only after validation.
6. **No non-null assertion** — `x!` is banned. Narrow, or use optional chaining (`x?.y`).
7. **No `@ts-ignore` / `@ts-expect-error`** — fix the type.
8. **No `enum`** — use an `as const` object plus a literal union type.
9. **Zod at boundaries** — external input (API, user, file) → Zod schema + `z.infer`. Internal → plain types.
10. **Typed errors** — `Error` subclasses with typed fields, never `throw new Error("bare string")` for a domain error. Use a `Result` for expected failures within 1–2 call levels; throw for propagation across many layers.
11. **`as const` for constants** — module-level constant objects and arrays use `as const`.
12. **`import type`** — type-only imports use `import type` (enforced by `verbatimModuleSyntax`).
13. **Named exports only** — no `export default` except where a framework requires it (e.g. Next.js pages).
14. **No empty catch, no catch-and-swallow** — every `catch` receives `unknown`; earn type safety with `instanceof`. A block must either narrow and handle each case, or re-throw. `catch (e) { console.error(e) }` without narrowing or re-throw is banned. A genuine top-level boundary (CLI entry, HTTP handler) may catch broadly only to log and exit.

## Data modeling — which construct, when

| Situation | Use |
|---|---|
| User input, API request/response | Zod schema + `z.infer` |
| Internal value object | `type` with `readonly` properties |
| Function with multiple outcomes | discriminated union (`kind` field) |
| Contract for implementations | `interface` |
| Fixed constants | `as const` + literal union |
| Distinct primitive (`UserId` vs `OrderId`) | branded type |
| Key-value map | `Record<K, V>` or an index signature |

The one rule: data crosses a trust boundary → Zod. Everything else → plain `type` with `readonly`.

`readonly` does not apply to framework state (React `useState`, signals), deliberate builder/accumulator objects, and ORM insert/update objects — document why each is mutable.

## Exhaustive switch — the canonical shape

```typescript
type Event =
  | { kind: "click"; x: number; y: number }
  | { kind: "scroll"; delta: number };

function handle(event: Event): void {
  switch (event.kind) {
    case "click":
      handleClick(event.x, event.y);
      return;
    case "scroll":
      handleScroll(event.delta);
      return;
    default: {
      const _exhaustive: never = event;
      void _exhaustive;
    }
  }
}
```

## Error handling — narrow with instanceof

```typescript
// BANNED — swallows TypeError, RangeError, and domain errors identically
try {
  const data = await api.get("/users");
} catch (e) {
  console.error("failed", e);
}

// GOOD — narrow, handle the known case, let the unknown propagate
try {
  const data = await api.get("/users");
} catch (e) {
  if (e instanceof HttpError) {
    logger.warn(`API ${e.status}: ${e.message}`);
    return fallback;
  }
  throw e;
}
```

## tsconfig — beyond `strict: true`

`"strict": true` alone is not strict.
The reusable compiler configuration owner is this package's `assets/tsconfig.strict.json`.
It enables `strict` plus `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `verbatimModuleSyntax`, `noFallthroughCasesInSwitch`, `noPropertyAccessFromIndexSignature`, and `noUnusedLocals`.
It does not enable `noUnusedParameters`.
Do not add project-specific `module`, `target`, or build choices to that portable baseline.

| Flag | Catches |
|---|---|
| `noUncheckedIndexedAccess` | `arr[0]` is `T \| undefined` — forces a check |
| `exactOptionalPropertyTypes` | `{ x?: string }` is not `{ x: string \| undefined }` |
| `verbatimModuleSyntax` | forces `import type` for type-only imports |
| `noFallthroughCasesInSwitch` | a forgotten `break` / `return` |
| `noPropertyAccessFromIndexSignature` | `.key` on an index signature → bracket notation |
| `noUnusedLocals` | unused locals and unused imports fail the type check |

When `tsc` reports unused locals or unused imports, remove the genuinely unused code.
Do not suppress the diagnostic with a compiler escape.
Unused parameters stay permitted under this baseline.

HTTP rule: production code never uses bare `fetch()` — it has no retry, timeout, or error policy. Use `ky` by default; use the `undici` direct API when a Node backend needs pooling, HTTP/2, or pipelining.

## No-excuse audit (run before declaring done)

`tsc` (strict) + Biome catch most of this; the rest is a manual scan of the diff. None of these has a silent opt-out — fix the cause or add a one-line comment naming why.

| Catches | Resolution |
|---|---|
| an `as` cast before validation | Every `as` is a runtime crash waiting. Cast only after validation. |
| `@ts-ignore` / `@ts-expect-error` | fix the type |
| `enum` declaration | use `as const` + literal union |
| `x!` non-null assertion | narrow or `?.` |
| `throw "string"` / `throw 123` | throw an `Error` subclass |
| `export let` / `export var` | use `export const` |
| `: any` annotation or `(): Promise<any>` return | type it precisely |
| `catch {}` / `catch (e) {}` empty | narrow with `instanceof` or re-throw |
| `catch (e)` without narrowing or re-throw | handle each case or re-throw |
| `switch` without an inline `const _exhaustive: never` default | add the exhaustive default |
| bare `fetch()` in prod | use `ky` / `undici` |
| file > 250 pure LOC | split by responsibility |

## In tests

Tests follow the iron list — branded types, typed errors, exhaustive switch. They may use `expect()`, magic numbers as test data, bracket-notation access to internals, and mutable fixtures. Don't mock what you can run. Prefer the framework's real test primitives with leak/disposable checks, and verify UI in a running build. Mock only what you can't run locally.

## Editing an existing file

When a file does not follow these rules, write new code in strict style; do not refactor the surrounding code in the same change.
