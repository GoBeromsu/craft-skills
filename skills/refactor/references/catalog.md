# Refactor move catalog

Twelve mechanical moves. Each move: numbered micro-steps, a safety check, and a compact SMELL/CLEAN
example. Run every step with tests green before and after — a move that cannot stay green at every
step is too big; split it into smaller moves from this same list.

## Table of Contents

1. [Extract Function](#1-extract-function)
2. [Inline Function](#2-inline-function)
3. [Extract Variable](#3-extract-variable)
4. [Rename (via IDE/LSP, not sed)](#4-rename-via-idelsp-not-sed)
5. [Move Function](#5-move-function)
6. [Replace Conditional with Polymorphism](#6-replace-conditional-with-polymorphism)
7. [Replace Nested Conditional with Guard Clauses](#7-replace-nested-conditional-with-guard-clauses)
8. [Introduce Parameter Object](#8-introduce-parameter-object)
9. [Replace Magic Literal](#9-replace-magic-literal)
10. [Split Phase](#10-split-phase)
11. [Extract Class](#11-extract-class)
12. [Replace Loop with Pipeline](#12-replace-loop-with-pipeline)

---

## 1. Extract Function

1. Select the code fragment that computes one identifiable thing.
2. List every variable the fragment reads (each becomes a parameter) and every variable it writes
   back for the caller (each becomes a return value — bundle 2+ into one typed return).
3. Create a new function named for *what* it does, not *how*.
4. Replace the fragment at the call site with a call to the new function.
5. Run the tests. A missed read/write shows up immediately as an undefined-name or wrong-result
   failure.

**Safety check:** behavior must be provably unchanged — only *where* the code lives changed. If the
extraction also fixes a bug, that is a second, separately committed change.

```python
# SMELL
def render_invoice(items, tax_rate):
    subtotal = sum(i.price * i.qty for i in items)
    total = subtotal + subtotal * tax_rate
    return f"Total: {total:.2f}"

# CLEAN
def compute_total(items, tax_rate):
    subtotal = sum(i.price * i.qty for i in items)
    return subtotal + subtotal * tax_rate

def render_invoice(items, tax_rate):
    return f"Total: {compute_total(items, tax_rate):.2f}"
```

## 2. Inline Function

1. Confirm the function body is now as clear as its name (or clearer) — the indirection no longer
   earns its keep.
2. Find every call site (this is the blast radius for step 4).
3. Replace each call site with the function body, substituting actual arguments for parameters.
4. Delete the now-unused function.
5. Run the tests after each call-site replacement, not only at the end.

**Safety check:** watch for recursive calls or multiple return points inside the body — inline one
return path at a time rather than all at once.

```typescript
// SMELL
function isEligible(order: Order): boolean {
  return moreThanFive(order.items.length);
}
function moreThanFive(n: number): boolean {
  return n > 5;
}

// CLEAN
function isEligible(order: Order): boolean {
  return order.items.length > 5;
}
```

## 3. Extract Variable

1. Identify a sub-expression whose purpose isn't obvious from reading it.
2. Introduce a well-named local holding that sub-expression's value.
3. Replace every occurrence of the *same* sub-expression within scope with the new name.
4. Run the tests — this move is purely local, so no interface changes to verify.

**Safety check:** only replace occurrences that are provably the same expression over the same
inputs; a look-alike expression with a different meaning stays separate.

```python
# SMELL
if platform.lower().startswith("ios") and platform.lower().endswith("18"):
    ...

# CLEAN
normalized_platform = platform.lower()
if normalized_platform.startswith("ios") and normalized_platform.endswith("18"):
    ...
```

## 4. Rename (via IDE/LSP, not sed)

1. Confirm the current name lies or under-communicates — a comment explaining a name is a rename
   waiting to happen.
2. Trigger the editor's symbol-aware "rename symbol" command, never a text search-and-replace.
3. Review every file the rename tool reports as touched before confirming.
4. Run tests plus the type-check/build step.

**Safety check:** a text-based find-and-replace matches string literals, comments, and unrelated
identically-spelled symbols in other scopes with no warning. A symbol-aware rename respects scope
boundaries and reference resolution — it is table stakes for this move, not an optional nicety.

## 5. Move Function

1. Identify the function's actual center of gravity — which object/module it references the most
   (see the Feature Envy smell).
2. Note what the function currently pulls from its old home; carry those references along or pass
   them in explicitly.
3. Copy the function to the target location, adjusting for the new context (`self`/`this`, imports).
4. Turn the original into a thin delegator, or update call sites directly if a delegator adds no
   value.
5. Run tests; once every call site uses the new location, delete the delegator.

**Safety check:** do copy → delegate → delete as three separate, independently revertible steps —
never collapse them into one commit.

```typescript
// SMELL — shippingCost lives on Order but only ever reads warehouse fields
class Order {
  shippingCost(warehouse: Warehouse): number {
    return warehouse.baseRate * warehouse.distanceFactor;
  }
}

// CLEAN
class Warehouse {
  shippingCostFor(order: Order): number {
    return this.baseRate * this.distanceFactor;
  }
}
```

## 6. Replace Conditional with Polymorphism

1. Identify the discriminant — the field or type the conditional switches on.
2. Create one type/subclass/variant handler per branch.
3. Move each branch's logic into its corresponding variant.
4. Replace the call site's conditional with a single polymorphic dispatch (a virtual call, or an
   exhaustive match that delegates to the variant).
5. Migrate one branch at a time, running tests after each — never migrate all branches in one step.

**Safety check:** worth the indirection only when new variants get added over time; a two-branch
conditional that never grows may not need it (a judgment call — see `programming`'s exhaustive-match
rule for the type-system-enforced version of this same idea).

```python
# SMELL
def shipping_cost(order):
    if order.method == "standard":
        return order.weight * 0.5
    elif order.method == "express":
        return order.weight * 1.5 + 10

# CLEAN
class StandardShipping:
    def cost(self, order): return order.weight * 0.5
class ExpressShipping:
    def cost(self, order): return order.weight * 1.5 + 10
# dispatch table replaces the if/elif chain; each new method adds one class, zero edits elsewhere
```

## 7. Replace Nested Conditional with Guard Clauses

1. Find the exceptional or early-exit cases nested inside the main logic.
2. Flip each one to a top-level early return (a guard clause) that handles the exceptional case and
   exits immediately.
3. Remove the now-unnecessary `else` — the code after a guard clause is implicitly the normal path.
4. Repeat until the main logic is flat, nesting only for genuine two-way branches.

**Safety check:** a guard clause must be a true early exit (`return`/`raise`/`continue`) — flipping a
nested `if` into a branch that still falls through afterward is not this move.

```typescript
// SMELL
function discount(customer: Customer): number {
  if (customer)
    if (customer.active)
      if (customer.years > 2) return 0.1;
  return 0;
}

// CLEAN
function discount(customer: Customer): number {
  if (!customer) return 0;
  if (!customer.active) return 0;
  if (customer.years <= 2) return 0;
  return 0.1;
}
```

## 8. Introduce Parameter Object

1. Identify the group of parameters that always travel together (the Data Clumps smell).
2. Define a single typed value for the group — a frozen dataclass or Pydantic model in Python, a
   `type`/interface in TypeScript.
3. Change the signature to accept the new object instead of the individual parameters.
4. Update every call site to construct or pass through the object.
5. Run tests; the type checker flags every missed call site immediately.

**Safety check:** only group parameters that are conceptually one thing — bundling unrelated
parameters merely to shorten a signature relocates the smell instead of fixing it.

```python
# SMELL
def create_shipment(street, city, postal_code, country): ...

# CLEAN
@dataclass(frozen=True, slots=True)
class Address:
    street: str
    city: str
    postal_code: str
    country: str

def create_shipment(address: Address): ...
```

```typescript
// SMELL
function createShipment(street: string, city: string, postalCode: string, country: string) {}

// CLEAN
type Address = { street: string; city: string; postalCode: string; country: string };
function createShipment(address: Address) {}
```

## 9. Replace Magic Literal

1. Find the unexplained literal and determine what it represents.
2. Declare a named constant (`Final` / `UPPER_SNAKE_CASE` in Python, `const UPPER_SNAKE_CASE` in
   TypeScript) at the narrowest scope that makes sense — module-level if shared, function-local
   otherwise.
3. Replace every occurrence that shares this *meaning* with the named constant — two literals that
   happen to equal the same number but mean different things stay separate.
4. Run tests.

**Safety check:** name the constant after what it *means*, not what it equals — `MAX_RETRY_ATTEMPTS`,
never `SEVEN`.

```python
# SMELL
if attempts > 7:
    raise TooManyAttempts()

# CLEAN
MAX_RETRY_ATTEMPTS: Final = 7
if attempts > MAX_RETRY_ATTEMPTS:
    raise TooManyAttempts()
```

## 10. Split Phase

1. Identify a function doing two things in sequence (parse-then-compute, fetch-then-render) where
   phase one's output is the sole input to phase two.
2. Extract phase two first ([Extract Function](#1-extract-function)), taking the intermediate value
   as a parameter.
3. Extract phase one, returning the intermediate value.
4. Have the now-thin original call phase one, then phase two, passing the intermediate value
   explicitly.

**Safety check:** the intermediate value should be one well-typed object or tuple, never a loose bag
of variables carried across the boundary.

```typescript
// SMELL
function handleOrder(raw: string) {
  const data = JSON.parse(raw);
  const total = data.items.reduce((sum: number, i: Item) => sum + i.price * i.qty, 0);
  return { orderId: data.id, total };
}

// CLEAN
function parseOrder(raw: string): OrderData { return JSON.parse(raw); }
function computeTotal(order: OrderData): OrderSummary {
  const total = order.items.reduce((sum, i) => sum + i.price * i.qty, 0);
  return { orderId: order.id, total };
}
function handleOrder(raw: string) { return computeTotal(parseOrder(raw)); }
```

## 11. Extract Class

1. Identify the subset of fields and methods that change together and are used together, separately
   from the rest of the class (the Divergent Change / God Class signal).
2. Create the new class holding that subset.
3. Move the fields, then move the methods that use them one at a time ([Move
   Function](#5-move-function) per method).
4. Leave a reference from the old class to the new one (composition) for callers that still need
   the old shape; update callers to the new class where it is cleaner.
5. Run tests after each field/method move, not in one large step.

**Safety check:** each resulting half should be nameable in one noun phrase without "and" (see
`programming`'s single-responsibility check) — if either half still needs "and," split again.

```python
# SMELL — one class owns both account data and notification delivery
class Account:
    def __init__(self, balance, email, phone):
        self.balance, self.email, self.phone = balance, email, phone
    def notify(self, message): ...  # sends email or SMS

# CLEAN
@dataclass
class NotificationPreferences:
    email: str
    phone: str
    def notify(self, message): ...
class Account:
    def __init__(self, balance, prefs: NotificationPreferences):
        self.balance, self.prefs = balance, prefs
```

## 12. Replace Loop with Pipeline

1. Identify a loop that filters, transforms, and/or aggregates a collection.
2. Convert it to the language's collection-pipeline operations — `map`/`filter`/`reduce` in
   TypeScript, comprehensions or generator expressions in Python — one pipeline stage per logical
   operation the loop performed.
3. Name an intermediate stage with [Extract Variable](#3-extract-variable) if the chain gets hard to
   read as one expression.
4. Run tests, including the loop's exact edge cases (empty input, off-by-one, any early
   `break`/`continue`).

**Safety check:** a loop with an early `break`/`return` mid-iteration, or complex side effects per
element, usually does not collapse cleanly into a pipeline — keep the loop and apply [Extract
Function](#1-extract-function) instead of forcing this move.

```python
# SMELL
active_emails = []
for user in users:
    if user.active:
        active_emails.append(user.email.lower())

# CLEAN
active_emails = [u.email.lower() for u in users if u.active]
```
