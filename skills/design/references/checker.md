# Offline checker contract (v1)

`python3 skills/design/scripts/check-design.py [--root PATH] [--evidence PATH] [--format text|json]` is offline, read-only, and uses only the Python standard library. `--root` is exactly one supplied ownership root; it never discovers app roots. It checks one uppercase `DESIGN.md`; missing, legacy-only `docs/design.md`, and dual paths are distinct errors.

## Document grammar

The eleven ordered H2 headings are: Product Intent; Principles; Tokens; Typography; Layout and Responsive; Primitives; Interaction and Feedback; Motion; Accessibility; Verification; Accepted Debt. An H2 is `## ` with at most three leading spaces, NFC/Unicode-trimmed, ASCII-whitespace-collapsed, casefolded, and optional closing hashes removed. Fenced code and HTML comments are ignored. Each canonical section is unique and substantive.

Section-scope fields are `- field: value`, exact lowercase snake case. Primitives are unique `### id` blocks with exactly one `data_bearing: true|false`, and a `state|specification|same_as|non_color_cue` table. Required states are default, hover, active, focus, disabled, loading; data-bearing primitives also require empty and error. Product-specific states such as selected, read-only, warning, success, permission-limited, offline, or destructive confirmation may extend that floor. State/primitive keys use NFC, trim, ASCII whitespace collapse, casefold. A substantive value is not empty, `...`, `TBD`, `TODO`, or `-`. `same_as` is `-` or another state, cannot self/cycle/miss, and requires specification `-`. `non_color_cue` is substantive or exact `not_applicable`; exact table-cell `none` emits `UX_DOC_NON_COLOR_CUE_NONE`. Prose, quotations, examples, negations, and values outside that cell do not.

Motion has `motion_present: true|false` and `reduced_motion`; true requires substantive text other than none/not_applicable and false requires exact not_applicable. Accepted Debt has one `id|decision|date|upgrade_path` table; dates are real `YYYY-MM-DD` Gregorian dates and upgrade paths are substantive.

## Evidence manifest

Schema v1 has exactly `schema_version`, `producer`, `checks`, `sources`, `accessibility_nodes`, `focus_expectations`, `captures`, and `artifacts`. Producer requires nonempty name/version and an optional nonempty string `run_id`. Requested checks are only `UX_SRC_ICON_CONTROL_NAME_MISSING`, `UX_SRC_REDUCED_MOTION_MISSING`, `UX_RENDER_CONTROL_NAME_MISSING`, and `UX_RENDER_FOCUS_EVIDENCE_MISSING`; each declares applicability `applicable|not_applicable|unknown`, coverage `complete|partial|none`, and a reason for unknown/not-applicable. Unknown/partial/none is insufficiency; absence findings require complete coverage.

Interpret outcomes as four disjoint states: an omitted check is `not_requested`; malformed schema, containment, relation, or integrity is `invalid` with exit 2; missing/partial/ambiguous evidence is `insufficient` and cannot support a defect or pass claim; an error diagnostic is an observed bounded `violation` with exit 1. A performed `passed` check means only that no listed violation was detected in its declared complete scope, never that UX, accessibility, or conformance passed.

IDs in sources, nodes, captures, artifacts match `[A-Za-z0-9][A-Za-z0-9._-]{0,127}` and are globally unique. Paths are POSIX-relative regular files within resolved root; absolute, traversal, missing, directory, backslash, and symlink escapes are invalid. Sources are exact HTML/HTM or CSS suffixes. Nodes require `id`, `role`, `name`, and locator exactly `{kind,value}`; kinds are test_id, dom_id, accessibility_path. Locator pair uniqueness is `(kind,value)`, so equal values with distinct kinds are valid. Accessibility node `id` is the only identity: expectation/capture `control_ref` must exactly reference an eligible allowlisted node; locators are anchor evidence only. Expectations are unique `(control_ref,viewport_id)`. Captures require focus-visible, keyboard, and a verified SHA-256 artifact whose `kind` is exactly `image`. Applicable complete render checks with no eligible nodes, or complete focus coverage that omits an eligible node or all expectations, are insufficient rather than clean.

Minimal schema-v1 focus-evidence example:

```json
{
  "schema_version": 1,
  "producer": {
    "name": "project-browser-adapter",
    "version": "1"
  },
  "checks": {
    "UX_RENDER_FOCUS_EVIDENCE_MISSING": {
      "applicability": "applicable",
      "coverage": "complete"
    }
  },
  "sources": [],
  "accessibility_nodes": [
    {
      "id": "ax-save",
      "role": "button",
      "name": "Save",
      "locator": {
        "kind": "dom_id",
        "value": "save"
      }
    }
  ],
  "focus_expectations": [
    {
      "control_ref": "ax-save",
      "viewport_id": "mobile"
    }
  ],
  "captures": [
    {
      "id": "capture-save-focus",
      "control_ref": "ax-save",
      "state": "focus-visible",
      "input": "keyboard",
      "viewport_id": "mobile",
      "artifact_id": "shot-save-focus"
    }
  ],
  "artifacts": [
    {
      "id": "shot-save-focus",
      "kind": "image",
      "path": "evidence/save-focus.png",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    }
  ]
}
```

The hash must match the real artifact bytes; the value above is the standard SHA-256 of an empty fixture and is illustrative, not rendered proof.

## Closed diagnostics and output

Document errors: `DESIGN_PATH_MISSING`, `DESIGN_PATH_LEGACY`, `DESIGN_PATH_CONFLICT`, `DESIGN_SECTION_MISSING`, `DESIGN_SECTION_DUPLICATE`, `DESIGN_SECTION_ORDER`, `DESIGN_SECTION_EMPTY`, `DESIGN_FIELD_INVALID`, `DESIGN_FIELD_DUPLICATE`, `DESIGN_TABLE_INVALID`, `DESIGN_PRIMITIVE_DUPLICATE`, `DESIGN_STATE_MISSING`, `DESIGN_STATE_DUPLICATE`, `DESIGN_STATE_REFERENCE_INVALID`, `DESIGN_DEBT_DATE_MISSING`, `DESIGN_DEBT_UPGRADE_MISSING`, `UX_DOC_REDUCED_MOTION_MISSING`, `UX_DOC_NON_COLOR_CUE_NONE`. Evidence errors are the four requested codes; `UX_EVIDENCE_INSUFFICIENT` is info. Every diagnostic has code, level, evidence kind/domain, path, location, observed evidence, and limitation; optional evidence_id is node ID. They sort by code/path/location/evidence_id.

JSON top-level keys are `schema_version`, `status`, `checks_performed`, `evidence_coverage`, `diagnostics`; status is clean, violations, invalid. Exit 0 means no performed error, 1 bounded document/evidence violation, 2 invalid invocation/schema/containment/integrity/internal error. This never rates aesthetics, severity, intent, task fitness, usability, or WCAG conformance.

## Conservative source scope

Static HTML is limited to literal button or href-bearing anchor tokenization and literal names; dynamic, malformed, custom, hidden, or ambiguous markup is insufficiency. CSS is limited to literal nonzero animation-duration/transition-duration and a balanced qualifying `@media (prefers-reduced-motion: reduce)` block; imports, shorthand-only, variables/functions, malformed syntax, or cascade uncertainty are insufficiency. A shorthand may coexist with an independently parseable nonzero longhand but never supplies motion evidence itself. No source result is a complete accessibility audit.
