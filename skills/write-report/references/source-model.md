# Technical Report Source Model

This reference defines the source manifest contract used beside the split
technical report book. The project's `technical-report.yaml` (resolved through
`$TECHNICAL_REPORT_YAML`) remains the structure source of truth for section
files, headings, and required `must` items. Source manifests explain which
admissible material supports each section without turning the skill prompt or
structure YAML into a source catalog.

## Contents

- [Concepts](#concepts)
- [Source Statuses](#source-statuses)
- [Source Fields](#source-fields)
- [Sensitivity Rules](#sensitivity-rules)
- [Coverage Keys](#coverage-keys)
- [Example Manifest](#example-manifest)

## Concepts

- `source_of_truth`: current, authoritative project material that may support
  current claims. Admissible current statuses are `present`, `accepted-adr`,
  `current-code`, and `current-plan`.
- `source_material`: supporting material that helps explain or contextualize a
  claim. It may be current or non-current, but non-current material cannot be
  the only support for a current claim.
- `stale_exclusions`: historical, deferred, stale, or background material that
  must not be used as current proof. These entries document why a tempting
  source was excluded or downgraded.
- `must_coverage`: a mapping from every structure-YAML section-level and
  heading-level `must` item to source ids that support the item.

## Source Statuses

Current-claim statuses:

- `present`: current project state or approved human-provided context.
- `accepted-adr`: an accepted Architecture Decision Record.
- `current-code`: current repository implementation or tests.
- `current-plan`: current approved project plan or active proposal state.

Non-current statuses:

- `historical`: archive, superseded design, or older implementation note.
- `external-background`: public external reference used only for context.
- `deferred`: future work or not-yet-implemented target.
- `stale-exclusion`: material intentionally excluded from current claims.

`historical`, `external-background`, `deferred`, and `stale-exclusion` sources
may appear in manifests, but a `must_coverage` entry is invalid when all of its
supporting sources have only those statuses.

## Source Fields

Every source entry in `source_of_truth`, `source_material`, and
`stale_exclusions` uses the same human-editable fields:

- `id`: unique source id inside the section manifest.
- `kind`: source type, such as `repo-file`, `repo-dir`, `adr`, `plan`,
  `book-section`, `external-url`, or `excluded`.
- `status`: one of the statuses above.
- `path_or_url`: repo-relative path, section file path, or public URL. Do not
  use private operational paths or private endpoints.
- `role`: short description of how the source is used.
- `supports`: list of claim keys or short claim labels supported by the source.

Repo-local `path_or_url` values must exist. Non-local sources must carry a
non-current status label such as `external-background`, `historical`, or
`deferred`.

## Sensitivity Rules

These sensitivity rules apply to every manifest field before a report section is
treated as source-backed.

Manifests must not contain hostnames, ports, tokens, passwords, API keys,
private IP addresses, tailnet domains, raw live filesystem paths, credentials,
or unmasked operational payloads. Use public repo-relative paths, environment
variable names, and sanitized descriptions instead.

When an operator needs the real local values for implementation or handover,
the technical-report book may name a `private operational annex` reference key
and the approved storage class. The actual value still stays outside the
canonical book, manifests, repo docs, reports, fixtures, and agent-visible
source catalogs. Acceptable examples are a password-manager item name, a local
note excluded from AI access, or an encrypted/private runbook path. The manifest
may cite only the reference key, owner, and freshness date, never the secret
value.

## Coverage Keys

`must_coverage` keys map to the structure YAML:

- Section-level must: `section.must.<zero_based_index>`
- Heading-level must:
  `heading.<exact_heading_text>.must.<zero_based_index>`

The validator requires every configured `must` item for the section to appear
exactly by key and to cite at least one known source id.

## Example Manifest

The example uses neutral placeholder ids and paths. Replace section id, file
name, paths, and heading text with your project's own values from the structure
YAML.

```yaml
section_id: 1_introduction
section_file: <PROJECT> 1 Introduction.md
source_material_concept: Current introduction claims are backed by the structure
  YAML, accepted ADRs, and current code; future targets stay labelled as
  deferred.
source_of_truth:
  - id: structure_yaml
    kind: repo-file
    status: present
    path_or_url: technical-report.yaml
    role: Section and must-item structure source of truth.
    supports:
      - section identity
source_material:
  - id: adr_0001
    kind: adr
    status: accepted-adr
    path_or_url: docs/decisions/ADR-0001-example-decision.md
    role: Decision that backs the introduction claim.
    supports:
      - design decision
  - id: future_milestone
    kind: plan
    status: deferred
    path_or_url: docs/plans/next-milestone.md
    role: Future target referenced as not-yet-implemented.
    supports:
      - future work
stale_exclusions:
  - id: archived_design
    kind: excluded
    status: stale-exclusion
    path_or_url: docs/archive/
    role: Archived references are not current proof.
    supports:
      - do not use as current state
must_coverage:
  section.must.0:
    - structure_yaml
  heading.Context and motivation.must.0:
    - adr_0001
  heading.Context and motivation.must.1:
    - adr_0001
    - future_milestone
```
