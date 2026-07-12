# Backend Vertical-Slice Architecture

One feature is one slice, and a slice carries its own handler, validation, and persistence calls end to end — nothing reaches into a sibling slice's internals.

## Contents

- [Hard rules](#hard-rules)
  - [Slice definition](#slice-definition)
  - [Cross-slice import ban](#cross-slice-import-ban)
  - [Shared kernel — minimal and explicit](#shared-kernel--minimal-and-explicit)
  - [Mixed-pattern drift back into layered](#mixed-pattern-drift-back-into-layered)
  - [Testing stays inside the slice](#testing-stays-inside-the-slice)
  - [`shared/` junk-drawer detection](#shared-junk-drawer-detection)
- [Incumbent-respect clause](#incumbent-respect-clause)
- [Grey zones](#grey-zones)
- [Folder shape (see `folders.md` for full framework-specific trees)](#folder-shape-see-foldersmd-for-full-framework-specific-trees)

## Hard rules

### Slice definition

A slice is one use case, structured as a single folder that owns everything needed to execute it: the request handler, its input validation, and its persistence calls. A slice does not split its own logic across `controllers/`, `services/`, `repositories/` folders shared with other slices — that split is the layered pattern, and mixing it into a vertical-slice service is the #1 drift.

```
src/features/create_order/
  handler.py        # entry point — receives the request, calls validation then persistence
  validation.py      # input parsing/validation for this use case only
  repository.py      # persistence calls this slice needs
  test_create_order.py
```

### Cross-slice import ban

```bash
# Python
grep -rEn "from features\.[a-zA-Z_]+\." --include='*.py' -r ./src/features 2>/dev/null \
  | grep -vE "from features\.shared\."

# TypeScript
grep -rEn "from ['\"]\.\./\.\./features/" --include='*.ts' -r ./src/features 2>/dev/null
```

Any hit that names a different feature folder — and is not importing from `features/shared/` — is a cross-slice import. Fix: either the logic meets the shared-admission judgment below, or keep the logic in the slice; a slice's independence is worth more than avoiding a few repeated lines.

**SMELL — a slice reaches into a sibling's repository:**

```python
# features/cancel_order/handler.py
from features.create_order.repository import OrderRepository  # cross-slice import
```

**CLEAN — the slice owns its own persistence call:**

```python
# features/cancel_order/repository.py
class CancelOrderRepository:
    def mark_cancelled(self, order_id: OrderId) -> None: ...
```

**SMELL — a slice imports a sibling's validation logic (TypeScript):**

```typescript
// features/cancel-order/handler.ts
import { validateOrderId } from "../create-order/validation"; // cross-slice import
```

**CLEAN — duplicate the small check, or promote it when shared admission is justified:**

```typescript
// features/cancel-order/validation.ts
export function validateOrderId(id: string): OrderId { /* ... */ }
```

### Shared kernel — minimal and explicit

`shared/` holds behavior that has a named owner, the same semantic identity across its consumers, coupled changes, and a boundary that matches the incumbent convention. Repetition count is evidence to inspect, not an admission threshold:

| Evidence | Action |
|---|---|
| One local use | Keep it in the slice. |
| Similar uses in multiple slices | Compare semantics and whether future changes must move together. |
| Shared semantics, coupled changes, and an owner | Extract a narrow shared module under that owner's review. |

Cross-cutting infrastructure (authentication middleware, request logging, error-envelope formatting) may live in `shared/` (or `platform/`) from the start when that is the incumbent's owned platform boundary, not feature logic that merely repeats.

### Mixed-pattern drift back into layered

```bash
find ./src -maxdepth 1 -type d \( -iname controllers -o -iname services -o -iname repositories \)
```

Any hit at the top level of a vertical-slice service means the layered pattern is creeping back in — a shared services/repositories folder splits the very thing vertical-slice exists to keep together. Dissolve the folder back into the owning feature slice(s), or flag the drift if the split spans many slices (a structural regression, not a quick fix).

### Testing stays inside the slice

A slice's test file lives beside the slice, not in a shared top-level test tree, and exercises the slice through its own handler — never through a sibling slice's fixtures. A test importing another slice's test helpers is the same cross-slice violation as production code importing across slices.

```bash
grep -rEn "from features\.[a-zA-Z_]+\.test|from ['\"]\.\./\.\./features/.*test" \
  --include='*.py' --include='*.ts' -r ./src/features 2>/dev/null
```

Any hit is a test-level cross-slice import. Apply the same fix as production code: admit the fixture to `shared/` only when it has shared semantics, coupled changes, a named owner, and matches the incumbent convention; otherwise duplicate it.

### `shared/` junk-drawer detection

`shared/` is a kernel of proven-common logic, not a place to put code that does not obviously belong to one slice. A `shared/` directory that grows without bound is usually absorbing one-off code that was never actually shared.

```bash
find ./src/shared -maxdepth 1 -type f | wc -l
```

A count climbing past what the owner can name a reason for (roughly a dozen files for a small service) is a signal to audit: for each file, confirm its shared semantic identity, coupled consumers, named owner, and fit with the incumbent boundary rather than parking it there to avoid duplicating two lines.

## Incumbent-respect clause

Detect the slice boundaries and shared-admission convention already used in this service, then match them for every edit. Migrating an established slice boundary is its own scoped change, never a side effect of adding one feature.

## Grey zones

- A value object needed by more than one slice (`Money`, `EmailAddress`) with no behavior beyond validation is infrastructure-like and belongs in an owned shared boundary when that matches incumbent convention; a value object that encodes feature-specific policy stays in its slice.
- A handler that is nearly identical across two slices except for one branch usually stays separate; extract only when its semantics and future changes are genuinely coupled, not because it crosses a repetition count.

## Folder shape (see `folders.md` for full framework-specific trees)

```
src/
  features/
    create_order/
      handler.py
      validation.py
      repository.py
      test_create_order.py
    cancel_order/
      ...
  shared/          # admitted through the shared-ownership judgment above
```
