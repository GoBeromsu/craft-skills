# Boundary lint

Encoding an architectural boundary — who may import whom — as linter configuration rather than prose or a bespoke script.
A boundary is only real when something mechanical fails when it drifts, and configuration is the right surface because it is native to the checks that already run and the next person edits one file instead of a private tool.

## Contents

- [Prove the current state first](#prove-the-current-state-first)
- [Encode the layering](#encode-the-layering)
- [Prove the rule bites](#prove-the-rule-bites)
- [Break real cycles minimally](#break-real-cycles-minimally)
- [Pitfalls](#pitfalls)

## Prove the current state first

Evidence before tooling: grep for the actual cross-package imports and count them.

```bash
grep -rn "^from <pkg-a>\|^import <pkg-a>" <pkg-b> <shared>
grep -rn "<pkg-a>/\|<pkg-b>/" <ui-src> --include=*.ts --include=*.tsx
```

Doc comments and fixture string literals are false positives; re-grep for import statements only before calling anything a violation.
An audit script written to count cross-slice imports is a stopgap, not the deliverable — replace it with configuration the same day, and keep it afterwards only as an audit reporter.

## Encode the layering

Choose contract kinds by the shape of the rule, and name each contract after the rule rather than the modules it happens to list:

- **independence** between peers that must never import each other in either direction.
- **forbidden** for a leaf that may import nothing internal, and for a package that imports only one specific leaf.
- **forbidden** again for a sole composition root — the module nothing else may import.

For a front-end with flat feature slices, a flat lint config carrying boundary rules *only* — no stylistic rules — needs three blocks:

- global: forbid importing the server packages' paths at all.
- the shared layer: forbid importing features or the app shell, because shared is the bottom of the stack.
- each feature slice: forbid every *other* slice except the documented seams, plus any parent-relative path, since with flat slices any `../` leaves the slice.

Expose it as a package script so it is one command, and wire that command into CI in the same change.

## Prove the rule bites

A rule that has never failed is not evidence.
Temporarily add a forbidden import, run the lint, capture the failing output including the rule name, then revert.
In one such probe the deliberate violation produced 6 restricted-import errors naming the slice, against a clean tree that reported 0 problems.

For the import-contract side, the durable equivalent is a test that runs the contract checker against synthetic fixture packages, so a contract that silently stops matching anything is caught rather than reported as passing.
That check is what turns "11 contracts kept" from a number into a guarantee.

## Break real cycles minimally

A mutual pair between two slices, created by one importing the other's hook, is fixed by moving the shared thing down into the shared layer — not by reversing a documented one-way seam.
Doing that took one repository's cross-slice import count from 7 to 6 with zero reverse edges, and the seam list in the contributor guide was updated in the same commit.
Then update the prose to point at the config file as the enforcement point, so the document stops being the rule and starts being the explanation.

## Pitfalls

- A restricted-import negation cannot re-include a path under an already-excluded parent, so a pattern-plus-exception list flags every slice's own imports.
  Compute an explicit per-slice denylist instead — all slices minus the allowed ones.
- A linter that reports suppression comments for rules it has not loaded turns stale suppressions into errors.
  Delete the stale comments rather than disabling inline-config handling wholesale.
- Deleting a module that a `forbidden` contract names makes the contract checker error on an unknown module; update the contracts in the same commit as the deletion.
- A suppression comment for a rule the linter does not enable is decorative — check the enabled rule set before trusting it.
- No CI step ran the front-end checks at all in one repository, so every rule there was advisory by accident.
  A lint script nobody runs is prose with extra steps; wire it into the workflow in the same change that adds it.
