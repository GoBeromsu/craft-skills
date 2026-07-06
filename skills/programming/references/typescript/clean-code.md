# Clean code reference

Naming, function shape, and structural discipline that make TypeScript readable by the next person, not just the compiler.

The iron list (`../typescript.md`) owns type discipline; this file owns naming, function shape, and structure.

## Contents

- [Naming](#naming)
- [Functions](#functions)
- [Classes and structure](#classes-and-structure)
- [SOLID, compressed](#solid-compressed)
- [Concurrency](#concurrency)
- [Comments and formatting](#comments-and-formatting)

## Naming

- **Meaningful and pronounceable.** A name should say what it holds and be sayable out loud — `generationTimestamp`, not `genymdhms`.
- **Searchable over short.** No unexplained magic numbers or strings; name the constant so a search finds every use.
- **One vocabulary per concept.** Pick one verb for one operation across the codebase — `getUser`, not `getUser`/`getUserInfo`/`getUserData` side by side for the same thing.
- **Explanatory variables over inline access.** Destructure so the name carries the meaning, not the index or the map lookup.
- **No mental mapping.** Full words the reader doesn't have to decode — `user`, `subscription` — never a single letter standing in for a concept.
- **No unneeded context.** Drop the type name from the field name — `Car.make`, not `Car.carMake`.
- **Default parameters over short-circuiting.** `function loadPages(count: number = 10)` states the default once; `count !== undefined ? count : 10` restates it at every call site.

```typescript
// BAD — magic number, mental mapping
const u = getUser();
setTimeout(restart, 86400000);

// GOOD — searchable, explanatory
const MILLISECONDS_PER_DAY = 24 * 60 * 60 * 1000;
const user = getUser();
setTimeout(restart, MILLISECONDS_PER_DAY);
```

## Functions

- **Two parameters, ideally; beyond that, one object with destructuring.** Destructuring documents the call site and lets the compiler flag an unused field.
- **One thing per function.** A function doing two things is two functions that haven't been split yet.
- **The name says what it does.** `addMonthToDate(date, 1)`, not `addToDate(date, 1)` — the reader shouldn't need the body to know what the `1` means.
- **One level of abstraction per function.** Don't mix tokenizing, parsing, and walking the result in one body; give each phase its own function.
- **No boolean flag parameters.** A flag means the function does two things under one name — split `createFile(name, temp)` into `createFile` and `createTempFile`.
- **Side effects at the edge, pure logic in the core.** A function that only turns input into output is trivial to test; centralize writes (file, DB, global state) behind one narrow seam instead of scattering them.
- **Encapsulate conditionals.** Name the condition (`canActivateService(...)`) instead of inlining the boolean expression at every call site.
- **Avoid negative conditionals.** Name and implement the positive check (`isEmailUsed`); negate at the call site, not in the definition.
- **Prefer immutability.** Return a new array or object; never mutate a parameter in place.
- **Favor `map`/`filter`/`reduce` over imperative loops.** An accumulator built with a `for` loop hides the operation inside control flow; `reduce` names it.
- **Remove duplicate code and dead code.** Two call sites doing the same thing are one abstraction away from a single source of truth; unused code is noise — version control already remembers it.
- **Use generators for on-demand streams.** A generator yields lazily; a function that materializes a large or infinite sequence into an array pays for items nobody asked for.
- **Avoid type-checking conditionals.** An `instanceof`/`typeof` chain branching on a variant is the same smell the iron list already bans for tagged unions — model the variants as a discriminated union and match exhaustively with `assertNever` (see `../typescript.md`), never reintroduce a manual chain to "simplify" it.

```typescript
// BAD — flag parameter, imperative accumulation, instanceof chain
function createFile(name: string, temp: boolean) {
  fs.create(temp ? `./temp/${name}` : name);
}
let total = 0;
for (let i = 0; i < items.length; i++) total += items[i].amount;
function travel(vehicle: Bicycle | Car) {
  if (vehicle instanceof Bicycle) pedal(vehicle);
  else if (vehicle instanceof Car) drive(vehicle);
}

// GOOD — split by intent, functional, exhaustive match
function createTempFile(name: string) { fs.create(`./temp/${name}`); }
function createFile(name: string) { fs.create(name); }
const total = items.reduce((sum, item) => sum + item.amount, 0);

type Vehicle = { readonly kind: "bicycle" } | { readonly kind: "car" };
function travel(vehicle: Vehicle): void {
  switch (vehicle.kind) {
    case "bicycle": return pedal(vehicle);
    case "car": return drive(vehicle);
    default: return assertNever(vehicle);
  }
}
```

```typescript
// BAD — inlined condition, negative check, mutates the input
if (subscription.isTrial || account.balance > 0) { /* ... */ }
function isEmailNotUsed(email: string): boolean { /* ... */ }
function addItemToCart(cart: CartItem[], item: Item): void {
  cart.push(item);
}

// GOOD — named condition, positive check, returns a new array
function canActivateService(subscription: Subscription, account: Account): boolean {
  return subscription.isTrial || account.balance > 0;
}
function isEmailUsed(email: string): boolean { /* ... */ }
function addItemToCart(cart: readonly CartItem[], item: Item): CartItem[] {
  return [...cart, item];
}
```

## Classes and structure

- **Small classes, one responsibility.** A method list that reads like a grab-bag (settings, progress, subscriptions, navigation) is several classes wearing one name; split by responsibility.
- **High cohesion, low coupling.** Most methods should use most fields; a constructor dependency touched by only one method's slice of the class belongs in its own class.
- **Composition over inheritance.** Reach for `extends` only for a genuine is-a relationship where the subtype substitutes the parent everywhere (Liskov); a has-a relationship (`Employee` has `TaxData`) is composition, not inheritance.

```typescript
// BAD — EmployeeTaxData is-a Employee? No, it's data Employee has.
class EmployeeTaxData extends Employee { /* ... */ }

// GOOD — composition
class Employee {
  constructor(private readonly taxData: EmployeeTaxData) {}
}
```

## SOLID, compressed

| Principle | Rule | Prevents |
|---|---|---|
| Single Responsibility | One reason to change per class | God classes that ripple on every edit |
| Open/Closed | Extend by adding a new type, not by branching on the ones that already exist | Call sites that grow an `if`/`instanceof` chain with every new case |
| Liskov Substitution | Any subtype must work everywhere the parent does, with no surprises | Callers that special-case a subtype because it silently breaks the parent's contract |
| Interface Segregation | No client depends on a method it doesn't use | Fat interfaces that force no-op or throwing stub implementations |
| Dependency Inversion | Depend on an abstraction, not a concrete class | High-level code rewritten every time a low-level detail changes |

Don't over-optimize past this: modern engines already optimize simple loops and property access, so spend effort on structure and correctness, not micro-tuning code the compiler already handles.

## Concurrency

`async`/`await` over a chained `.then()` over a nested callback — each step removes a layer of nesting and reads top-to-bottom.

```typescript
// BAD — callback nesting
get(url, (err, res) => { if (err) cb(err); else writeFile(path, res, cb); });

// GOOD — async/await
async function downloadPage(url: string, path: string): Promise<void> {
  const response = await get(url);
  await write(path, response);
}
```

## Comments and formatting

- **Code self-documents.** A comment that restates what the next line does is an apology for a bad name; fix the name instead.
- **Comments earn their place on business-logic complexity only** — the "why", not the "what".
- **No journal comments, no positional banners, no commented-out code.** Version control already keeps that history; delete it rather than leaving it as noise.

```typescript
// BAD — restates the code, no business reason given
// Check if subscription is active.
if (subscription.endDate > Date.now()) { /* ... */ }

// GOOD — the name is the comment
const isSubscriptionActive = subscription.endDate > Date.now();
if (isSubscriptionActive) { /* ... */ }
```
