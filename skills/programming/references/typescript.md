# TypeScript reference

Modern TypeScript: strictly typed, built on the project's canonical libraries and toolchain, and correct under async. The compiler is your first line of defense — encode invariants as types, parse untrusted input at boundaries, and give every function a contract the types enforce.

Load this file in full before writing or editing TypeScript. The rules below are deliberate project choices — violations are wrong, not stylistic.

## Contents

- [Tooling](#tooling)
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

## The iron list

1. **Readonly by default** — all `type` / `interface` properties are `readonly`; arrays are `readonly T[]`. Mutable only when mutation is the documented purpose.
2. **Branded types for distinct primitives** — `type UserId = Brand<string, "UserId">`. Never pass a raw `string`/`number` where a branded type exists.
3. **Exhaustive switch** — every `switch` on a discriminated union ends with `default: assertNever(x)`. No fall-through.
4. **No `any`** — banned in annotations, returns, and parameters. Use `unknown` and narrow.
5. **No type assertions** — `as T` is banned; it overrides the checker. The only allowed forms are `as const` and `satisfies`. To change a type, narrow with a type guard or re-parse — never assert.
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

function assertNever(x: never): never {
  throw new Error(`unreachable: ${JSON.stringify(x)}`);
}

function handle(event: Event): void {
  switch (event.kind) {
    case "click":
      handleClick(event.x, event.y);
      return;
    case "scroll":
      handleScroll(event.delta);
      return;
    default:
      assertNever(event); // build fails when a new variant is added
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

`"strict": true` alone is not strict. Add:

| Flag | Catches |
|---|---|
| `noUncheckedIndexedAccess` | `arr[0]` is `T \| undefined` — forces a check |
| `exactOptionalPropertyTypes` | `{ x?: string }` is not `{ x: string \| undefined }` |
| `verbatimModuleSyntax` | forces `import type` for type-only imports |
| `noFallthroughCasesInSwitch` | a forgotten `break` / `return` |
| `noPropertyAccessFromIndexSignature` | `.key` on an index signature → bracket notation |

HTTP rule: production code never uses bare `fetch()` — it has no retry, timeout, or error policy. Use `ky` by default; use the `undici` direct API when a Node backend needs pooling, HTTP/2, or pipelining.

## No-excuse audit (run before declaring done)

`tsc` (strict) + Biome catch most of this; the rest is a manual scan of the diff. None of these has a silent opt-out — fix the cause or add a one-line comment naming why.

| Catches | Resolution |
|---|---|
| an `as` assertion other than `as const` / `satisfies` | redesign the types or narrow with a guard |
| `@ts-ignore` / `@ts-expect-error` | fix the type |
| `enum` declaration | use `as const` + literal union |
| `x!` non-null assertion | narrow or `?.` |
| `throw "string"` / `throw 123` | throw an `Error` subclass |
| `export let` / `export var` | use `export const` |
| `: any` annotation or `(): Promise<any>` return | type it precisely |
| `catch {}` / `catch (e) {}` empty | narrow with `instanceof` or re-throw |
| `catch (e)` without narrowing or re-throw | handle each case or re-throw |
| `switch` without `default: assertNever` | add the exhaustive default |
| bare `fetch()` in prod | use `ky` / `undici` |
| file > 250 pure LOC | split by responsibility |

## In tests

Tests follow the iron list — branded types, typed errors, exhaustive switch. They may use `expect()`, magic numbers as test data, bracket-notation access to internals, and mutable fixtures. Prefer real objects and in-memory fakes over mocks; mock only the unmockable (clock, randomness) at the narrowest seam.

## Editing an existing file

When a file does not follow these rules, write new code in strict style; do not refactor the surrounding code in the same change.
