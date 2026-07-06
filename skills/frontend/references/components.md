# Frontend Component Reuse

A component earns reuse by its position in a strict dependency hierarchy, not by how many props it accepts. Dependencies point downward only — a lower layer never imports from a higher one.

## Contents

- [Hard rules](#hard-rules)
- [The 3-layer hierarchy](#the-3-layer-hierarchy)
- [Props-API rules](#props-api-rules)
- [Colocation rule](#colocation-rule)
- [Incumbent-respect clause](#incumbent-respect-clause)
- [Hand-offs](#hand-offs)

## Hard rules

| Concern | Do | Never |
|---|---|---|
| Dependency direction | Import only from your own layer or a layer below it | Import from a higher layer (a primitive importing a feature component) |
| Boolean props | Collapse ≥3 related booleans into one variant enum | Let a component grow a fourth independent boolean prop |
| Extraction timing | Extract a shared component on the third duplication (rule of three) | Extract on the first or second occurrence "in case it's needed again" |
| Test/story colocation | Keep a component's test and story file next to its source file | Centralize all tests in a separate mirror tree disconnected from the component |

## The 3-layer hierarchy

| Layer | Owns | Depends on | Example |
|---|---|---|---|
| Primitives / design system | The smallest visual building blocks; every visual variant traces to a `design.md` token | Nothing project-specific — only the design system's own tokens | `Button`, `Input`, `Checkbox`, `Card` |
| Composed / patterns | Combinations of primitives into a reusable interaction shape, still content-agnostic | Primitives only | `FormField` (label + input + error), `Modal`, `DataTable` |
| Feature-bound | Business-specific composition wired to real data and routes | Primitives and composed components | `CheckoutSummary`, `UserProfileCard` |

**Detect: an upward or sideways dependency violation — a primitive or composed component importing from `features/`.**

```bash
grep -rlE "from ['\"](\.\./)*features/" src/components/ui src/components/patterns 2>/dev/null
```

Any file printed → a lower layer depends on a higher one → the dependency direction is inverted; move the feature-specific logic out of the primitive/composed component, or move the component itself down to `features/` if it was never actually generic.

**Detect: the same check, generalized (adjust the higher-layer glob to the project's actual feature directory name).**

```bash
grep -rlE "from ['\"](\.\./)*(features|pages|routes)/" src/components/{ui,primitives,patterns,composed} 2>/dev/null
```

## Props-API rules

- **Boolean explosion → variant enum.** A component with 3 or more independent boolean props is really encoding a small set of variants; collapse them into one `variant` (or `size`, `state`) enum prop instead.

  **Detect:**

  ```bash
  find src/components -name '*.tsx' -print0 2>/dev/null \
    | xargs -0 grep -HoE '^\s*(is|has|show|use)[A-Z][A-Za-z]*\??:\s*boolean' \
    | awk -F: '{print $1}' | sort | uniq -c | awk '$1>=3'
  ```

  Reading: 3+ boolean-shaped props on one component signature (grouped by file, approximate — the command scans per-line, cross-check by file manually) → collapse to an enum.

  **SMELL:**

  ```tsx
  function Button({ isPrimary, isSecondary, isDanger, isGhost }: ButtonProps) { /* … */ }
  ```

  **CLEAN:**

  ```tsx
  type ButtonVariant = "primary" | "secondary" | "danger" | "ghost";
  function Button({ variant }: { variant: ButtonVariant }) { /* … */ }
  ```

- **Children over render-prop, unless the child genuinely needs arguments.** Default to passing `children` for static composition. Reach for a render-prop (`children: (arg: T) => ReactNode`) only when the parent must hand the child computed data it cannot otherwise access (a list item's index, a measured dimension).

  ```tsx
  // children — no argument needed, prefer this shape
  <Card><CardTitle>Plan</CardTitle></Card>

  // render-prop — justified only because the parent owns `index`
  <VirtualList items={rows}>{(row, index) => <Row data={row} pos={index} />}</VirtualList>
  ```

- **No premature extraction — rule of three applies to components too.** The first time a JSX shape repeats, leave it inline. The second time, note the duplication. The third time, extract to a shared component. Extracting after one occurrence produces an abstraction shaped around a single caller's needs, which the second caller then has to fight.

  **Detect (approximate — near-duplicate JSX blocks worth a manual look):**

  ```bash
  grep -rhoE '<[A-Z][A-Za-z]*' src/pages src/features 2>/dev/null | sort | uniq -c | sort -rn | awk '$1>=3'
  ```

  A JSX tag name appearing 3+ times across different feature files is a candidate for promotion to a composed component — confirm by hand that the usages are structurally similar, not just the same primitive used differently each time.

Grey zone — judge by whether the three occurrences share the *same reason to change*. Three components that happen to look alike today but serve unrelated features are coincidental duplication, not a shared abstraction; extracting them couples features that should stay independent. Only extract when a future change to one occurrence would legitimately need to change all three.

## Colocation rule

A component's test file and story file (if the project uses a story format) live next to its source file, not in a separate mirror tree:

```
components/patterns/FormField/
├── FormField.tsx
├── FormField.test.tsx
└── FormField.stories.tsx
```

**Detect: a test file living outside its component's directory.**

```bash
find src/components -name '*.test.tsx' -o -name '*.test.ts' | while read -r f; do
  comp="$(dirname "$f")/$(basename "$f" | sed 's/\.test\././')"
  test -f "$comp" || echo "orphan test: $f"
done
```

Any line printed → the test has no colocated component source at the same path → either the component moved and the test did not, or the test was placed in a mirror tree; move it beside its component.

## Incumbent-respect clause

Detect the project's existing component layering (its folder names for primitives/composed/feature layers vary: `ui/` vs `primitives/`, `patterns/` vs `composed/`) and follow that naming for edits. Apply the 3-layer hierarchy strictly to new components; never relabel or move an existing codebase's component tree into this shape as a side effect of an unrelated feature change — propose that reorganization separately.

A codebase with no layering at all (every component in one flat `components/` directory) is not an incumbent convention to preserve — it is the absence of one. Apply the 3-layer hierarchy to new components added to that codebase even while the existing flat directory stays untouched.

Note the drift in the work notes or final report rather than silently reorganizing the existing tree.

## Hand-offs

- Which rendering model a component belongs to (server vs. client leaf) → `architectures.md` in this skill.
- Where a component's data comes from (props vs. store vs. server cache) → `state.md` in this skill.
- Per-file TypeScript discipline (prop typing, exhaustiveness) → `programming`.
- Component-level test structure and coverage → `testing`.
- Rendering untrusted content inside a component (raw HTML injection, XSS escape hatches) → `security`.
- New token, primitive, or pattern introduced by a component change → update `design.md` in the same commit (gate + detection command owned by `document`, stated in this skill's `SKILL.md`).
