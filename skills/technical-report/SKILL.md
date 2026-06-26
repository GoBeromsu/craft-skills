---
name: technical-report
description: '"technical-report", "기술 문서 써줘", "정본 문서", "TOC 강제", "기술 보고서 골격", "scaffold a technical report", "/technical-report" — build and enforce a project''s canonical technical report. Scaffold mode interviews you depth-by-depth (sections → ## headings → required content) to fill a per-project technical-report.yaml frame; Author/Validate mode writes or reviews section markdown against that YAML as the single source of truth and gates structure + source coverage with two validators.'
version: 0.1.1
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob]
compatibility: claude-code, codex
---

# Technical Report

Build and enforce a project's **canonical technical report** against one definition
file: `technical-report.yaml`. That YAML's depth *is* the table of contents
(section → `##` heading → required `must` content), and it is the single source of
truth (SSOT). Section facts are pinned by the source model in
[references/source-model.md](./references/source-model.md) and per-section source
manifests. The author never grows or shrinks structure freely, and stands up current
claims only on a manifest's `source_of_truth`.

The same skill produces different reports in different projects: the YAML is an empty
**frame** that gets filled per project. Completion bar: a reader can start the work by
reading this document alone.

## When to Use

- Standing up a technical report for a new project — interview to fill the YAML frame.
- Writing, expanding, or restructuring a section against an existing YAML.
- Reviewing whether a section keeps its tone, structure, and required `must` content.
- Citing system facts (architecture, paths, contracts) with sources pinned, no guessing.
- Trigger phrases: "technical-report", "기술 문서 써줘", "정본 문서", "TOC 강제",
  "기술 보고서 골격", "scaffold a technical report", "/technical-report".

Do not use for free-form raw notes or daily logs — those are not bound by this enforced frame.

## Two Modes

Pick the mode first:

- **Scaffold** — no `technical-report.yaml` exists yet, or the structure (sections /
  headings / must) must change. Build the frame through a depth-ordered interview.
  Structure changes always happen here first, then the document follows.
- **Author/Validate** — the YAML already defines the structure. Write or review section
  markdown against it, then pass both validators.

## Setup

Paths are per-project and injected, never hardcoded:

- `TECHNICAL_REPORT_YAML` — path to this project's filled YAML (SSOT). Default
  `./technical-report.yaml`. **Do not place this file under a tool-private directory**
  (`.claude/`, `.codex/`, `.gjc/`, `.hermes/`, `.cursor/`, etc.) — the YAML is the SSOT for
  *all* agents, and tool-private dirs are invisible to other runtimes. Keep it at a
  tool-neutral path: repo root (`./technical-report.yaml`) or `docs/technical-report.yaml`.
- `TECHNICAL_REPORT_BOOK` — directory holding the canonical markdown (Index + section
  files). Default `./book`.

Copy `.env.example` to `.env` and set both, or export them in the shell. To start a new
project's frame, copy [technical-report.template.yaml](./technical-report.template.yaml)
to the `TECHNICAL_REPORT_YAML` location and fill it through Scaffold mode.

## Mode A — Scaffold (depth-1 interview)

The default entry is **depth-1**. Build the YAML from the template frame one depth at a
time; do not jump ahead to `must` before the section list is settled.

1. **depth-1 — sections.** Interview for the section list: each section is one markdown
   file under `TECHNICAL_REPORT_BOOK`. Fix the order (numeric prefix = document order),
   the `title`, the `file` name, and a one-line `intent`. An abstract-style section with
   no `##` headings carries `headings: []`.
2. **depth-2 — headings.** For each section, interview for its `##` headings. Each heading
   gets a one-line `intent`. The heading name is exactly the markdown `## ` text.
3. **depth-3 — must.** For each heading (and abstract section), interview for the `must`
   items: the facts or claims that heading must contain, one bullet each. A heading with
   no `must` is unfinished.
4. **governance + background.** Capture the project's `governance` (approval authority by
   role, document-vs-log separation, house style) and any optional `background` knowledge
   the author should cite from. Keep all of this inside the YAML, not in this skill.
5. **Sensitivity.** Never write hostnames, ports, tokens, private IPs, tailnet domains, or
   raw filesystem paths into the YAML — use `REDACTED` or a reference key per
   [references/source-model.md](./references/source-model.md).

Write the result to `TECHNICAL_REPORT_YAML`. Then run `validate.py` to confirm the frame
parses and to see which section files are still missing.

## Core Mechanism — depth is the TOC (enforced)

Structure truth is `technical-report.yaml` alone. Depth is the document skeleton.

- **depth-1** `document.<section>` → one `.md` file under `TECHNICAL_REPORT_BOOK`.
- **depth-2** `<section>.headings.<## heading>` → that file's `##` headings.
- **depth-3** `.must` → what the heading must contain. One empty `must` means the section
  is unfinished.

Rules:

1. Before writing, read the target section's `intent`, every `heading`, and every `must`.
2. After writing, check each `must` off as a checklist. An unmet `must` means not done.
3. Never add, delete, or reorder sections or headings ad hoc. To change structure, edit
   the YAML first (with approval), then conform the document — YAML is SSOT, document is
   the dependent.
4. Fact truth is the per-section source manifest; its format and status rules follow
   [references/source-model.md](./references/source-model.md).
5. Apply the YAML's `governance` and house-style rules to every section equally.

## Tone & House Style

Defaults, unless the project's YAML `governance` overrides them:

- **Prose-first.** Paragraphs by default. Bullets only for section summaries or atomic
  enumeration — do not chop explanation into bullets.
- **MECE.** No cross-section duplication. State a fact once and cite it elsewhere.
- **Links.** Internal/section citations use `[[wikilinks]]`; external sources (code, repo,
  URL) use `[title](url)` markdown links.
- **Diagrams.** Mermaid is hierarchical: high-level first, component detail in a separate
  diagram. Not everything in one chart.
- **Cohesion.** Section intros and the table of contents live in the Index file only; each
  section file holds self-contained content.
- **Sources.** Truth comes from reading actual code/specs and a manifest's
  `source_of_truth`. Secondary docs may be stale. Do not guess facts.
- **Governance.** The canonical document changes only under the approver named (by role)
  in the YAML `governance`. Agents propose drafts; humans approve before the canonical
  document changes. Curated document and raw notes stay separate and are not auto-synced.

## Mode B — Author/Validate workflow

1. **Read the frame.** Pull the target section's `intent`, headings, and `must` from
   `TECHNICAL_REPORT_YAML`.
2. **Check the source model.** Read [references/source-model.md](./references/source-model.md)
   for current vs non-current source status and the sensitivity rules.
3. **Pin facts.** Read the section's source manifest; stand up current claims on
   `source_of_truth` and `must_coverage`. Do not invent facts not in a manifest — fix the
   source first.
4. **Draft.** Produce the section as a *draft proposal*, not a direct write into the canonical
   book. Prose-first, honoring the house style; cite with wikilinks/markdown links; use
   hierarchical mermaid where a heading calls for a diagram.
5. **Review.** Check every `must` and the manifest's `must_coverage` as a checklist; move
   any duplicated narrative to one place and wikilink the rest.
6. **Validate.** Run both validators against the draft until they exit 0 — point `--book` at
   the draft directory while drafting (the `TECHNICAL_REPORT_BOOK` default stays aimed at the
   canonical book, which only changes at step 7). Heading-structure gate + source-manifest gate.
7. **Govern.** Submit the validated draft for approval. Only after the approver named in the
   YAML `governance` accepts it do the canonical book files under `TECHNICAL_REPORT_BOOK`
   change — including any Index status line / TOC update. Agents propose; humans promote.

## Code Enforcement — structure + source validators

Declaration is not enforcement. [validate.py](./validate.py) treats the YAML `document`
depth as truth and parses the real markdown heading structure to compare — catching missing
required `##`, undefined `##`, reordering, `# title` mismatch, and empty headings, exiting 1
on violation (frontmatter and fenced `#` ignored).

```
python3 validate.py --yaml "$TECHNICAL_REPORT_YAML" --book "$TECHNICAL_REPORT_BOOK"
python3 validate.py --json    # machine-readable for CI/hook
```

[validate_sources.py](./validate_sources.py) reads per-section source manifests and checks
that `source_of_truth`, `source_material`, `stale_exclusions`, and `must_coverage` match the
YAML's `must`. Current claims need a current source; stale/deferred/historical alone do not
pass. It also rejects sensitive/private values.

```
python3 validate_sources.py --yaml "$TECHNICAL_REPORT_YAML" --book "$TECHNICAL_REPORT_BOOK"
python3 validate_sources.py --fixture missing-must    # built-in negative fixtures
```

After writing or editing a section, pass **both validators (exit 0)**. The YAML stays
authoritative and the document conforms to it. When an external editor mechanically rewrites a
heading — for example Obsidian normalizing `vs`→`Vs` — `validate.py` fails on the mismatch.
That failure is never resolved by silently hand-editing the document: reconcile by submitting a
YAML update for approval first, and validation only goes green once the **approved** YAML
matches the heading. The validator never passes on unreconciled drift, so the YAML — not the
rendered markdown — is always the thing that becomes canonical. A genuine structure change
follows the same order: edit the YAML first, then the document.

## Files

- **[technical-report.template.yaml](./technical-report.template.yaml)** — the empty frame.
  Copy to `TECHNICAL_REPORT_YAML` and fill via Scaffold mode.
- **[references/source-model.md](./references/source-model.md)** — section source manifest
  format, `source_of_truth` status, `must_coverage`, sensitivity rules. Never put a
  per-section source catalog in this SKILL.md or the YAML.
- **[validate.py](./validate.py)** — heading-structure validator. Compares YAML `document`
  to real `.md` headings; exit 1 on violation.
- **[validate_sources.py](./validate_sources.py)** — source-manifest validator. Checks
  per-section coverage, stale-only claims, repo-local source existence, and sensitive leaks.
- **[.env.example](./.env.example)** — per-project path template. Copy to `.env` and set
  `TECHNICAL_REPORT_YAML` / `TECHNICAL_REPORT_BOOK`.

## Requirements

- `python3` with PyYAML (`pip install pyyaml`) for both validators.
