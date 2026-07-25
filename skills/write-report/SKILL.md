---
name: write-report
description: 'Scaffolds and authors a project''s one-off canonical technical report against a single YAML frame (technical-report.yaml) whose depth is the enforced table of contents — section, then heading, then required must-content. Use when asked to "scaffold a technical report" or "기술 보고서", when writing or restructuring a report section against that frame, or when checking a section''s structure and pinned sources for "TOC enforcement" against its source manifest. Not for ongoing project documentation, READMEs, ADRs, or changelogs (use `document`) — write-report owns exactly one canonical, one-off deliverable per project.'
metadata:
  version: 1.0.1
---

# write-report

Scaffold and enforce a project's one-off canonical technical report against a single YAML
frame, `technical-report.yaml`, whose depth *is* the table of contents (section → `##`
heading → required `must` content) and single source of truth (SSOT). Success: the frame is
filled through a depth-ordered interview, every section's draft passes both validators, and
a reader can start the work by reading the report alone.

## Setup

- `TECHNICAL_REPORT_YAML` — path to the project's filled frame (SSOT). Default
  `./technical-report.yaml`. Keep it at a tool-neutral path (repo root or `docs/`) — never
  under `.claude/`, `.codex/`, `.gjc/`, `.hermes/`, or any tool-private dir, since every
  agent runtime must be able to read it.
- `TECHNICAL_REPORT_BOOK` — directory holding the canonical markdown (Index + section
  files). Default `./book`.

Copy `.env.example` to `.env` and set both, or export them in the shell. New project: copy
`templates/technical-report.template.yaml` to `$TECHNICAL_REPORT_YAML` and fill it via
Scaffold mode.

## Two modes

Pick first:

- **Scaffold** — no frame exists yet, or its structure (sections/headings/must) must
  change. Structure changes always happen here first; the document follows.
- **Author/Validate** — the frame already defines structure. Write or review section
  markdown against it, then pass both validators.

## Scaffold — depth-ordered interview

Depth order matters; do not jump ahead to `must` before the section list is settled.

1. **depth-1 — sections.** Interview the section list: one markdown file per section under
   `TECHNICAL_REPORT_BOOK`, numeric-prefix order, `title`, `file`, one-line `intent`. An
   abstract section with no `##` headings carries `headings: []`.
2. **depth-2 — headings.** Per section, interview its `##` headings, each with a one-line
   `intent`. The heading name is exactly the markdown `## ` text.
3. **depth-3 — must.** Per heading (and abstract section), interview the `must` items — the
   facts or claims that heading has to contain. An empty `must` means unfinished.
4. **governance + background.** Capture approval authority by role, document-vs-log
   separation, house style, and any optional background knowledge — all inside the YAML.
5. **Sensitivity.** Never write hostnames, ports, tokens, private IPs, tailnet domains, or
   raw filesystem paths into the frame — use `REDACTED` or a reference key per
   `references/source-model.md`.

Write the result to `$TECHNICAL_REPORT_YAML`, then run `scripts/validate.py` to confirm it
parses and see which section files are still missing.

## Depth is the TOC (enforced)

- **depth-1** `document.<section>` → one `.md` file under `TECHNICAL_REPORT_BOOK`.
- **depth-2** `<section>.headings.<## heading>` → that file's `##` headings.
- **depth-3** `.must` → required content; one empty `must` means unfinished.

Never add, delete, or reorder sections or headings ad hoc — edit the YAML first (with
approval), then conform the document. Fact truth is the per-section source manifest
(`references/source-model.md`); apply the frame's `governance` and house style to every
section equally.

## House style

Defaults, unless the frame's `governance` overrides them:

- Prose-first; bullets only for section summaries or atomic enumeration.
- MECE — state a fact once, cite it elsewhere.
- `[[wikilinks]]` for internal/section citations; `[title](url)` for external sources.
- Hierarchical Mermaid — high-level diagram first, component detail in a separate one.
- Section intros and the TOC live only in the Index file; each section file is
  self-contained.
- Truth comes from reading actual code/specs and a manifest's `source_of_truth`; never
  guess a fact.
- The canonical document changes only under the approver named (by role) in `governance` —
  agents propose, humans approve.
- **Korean body prose uses formal polite speech (합쇼체 / ~습니다·~입니다).** Declarative
  plain style (`~다` / `~한다` / `~이다` as the default sentence ender) is not the house
  default when the report is written in Korean. Technical nouns (ArgoCD, namespace, env)
  stay in English; sentence endings stay 경어. Record the same rule under
  `governance.must` house-style so the project frame does not silently drop it.

When drafting or reviewing a Korean section, rewrite endings before submit:
`~한다` → `~합니다`, `~이다` → `~입니다`, `~있다` → `~있습니다`, `~없다` → `~없습니다`.
Keep headings and table cells terse if needed; full sentences in body paragraphs use 경어.

## Author/Validate workflow

1. Read the target section's `intent`, headings, and `must` from `$TECHNICAL_REPORT_YAML`.
2. Read `references/source-model.md` for source status and sensitivity rules.
3. Pin facts on the section's source manifest (`source_of_truth`, `must_coverage`) — fix
   the source first rather than inventing a fact.
4. Draft the section as a proposal, not a direct write into the canonical book, honoring
   house style.
5. Review every `must` and `must_coverage` entry as a checklist; move duplicated narrative
   to one place and wikilink the rest.
6. Validate against a draft directory (`--book <draft-dir>`) until both validators exit 0.
7. Submit for approval; only the `governance`-named approver's acceptance moves the draft
   into `TECHNICAL_REPORT_BOOK`, including any Index status line or TOC update.

## Validators

`scripts/validate.py` treats the YAML `document` depth as truth and parses the real
markdown heading structure against it — missing/undefined `##`, reordering, `# title`
mismatch, empty headings (frontmatter and fenced code ignored):

```bash
python3 scripts/validate.py --yaml "$TECHNICAL_REPORT_YAML" --book "$TECHNICAL_REPORT_BOOK"
python3 scripts/validate.py --json
```

`scripts/validate_sources.py` checks per-section source manifests against the YAML's
`must` — a current claim needs a current source; stale/deferred alone does not pass; it
also rejects sensitive/private values:

```bash
python3 scripts/validate_sources.py --yaml "$TECHNICAL_REPORT_YAML" --book "$TECHNICAL_REPORT_BOOK"
python3 scripts/validate_sources.py --fixture missing-must
```

Both exit 0 before a section counts as done. When an external editor mechanically rewrites
a heading (Obsidian normalizing `vs`→`Vs`), reconcile by submitting a YAML update for
approval first — never by hand-editing the document around the drift. The YAML, not the
rendered markdown, is always what becomes canonical.

## Files

- `templates/technical-report.template.yaml` — the empty frame; copy to
  `$TECHNICAL_REPORT_YAML` and fill via Scaffold mode.
- `references/source-model.md` — source manifest format, `source_of_truth` status,
  `must_coverage`, sensitivity rules.
- `scripts/validate.py` / `scripts/validate_sources.py` — structure + source validators.
- `.env.example` — per-project path template.

## Requirements

- `python3` with PyYAML (`pip install pyyaml`) for both validators.

## Anti-patterns

- Korean report body written in plain declarative endings (`~다`/`~한다`/`~이다`) → rewrite to formal polite 합쇼체 (`~습니다`/`~입니다`) before approval.
- Treating English-only house style as complete for a Korean deliverable → add the 경어 rule to `governance` house style and apply it in Author mode.
- Softening 경어 only in the Index while sections stay plain → every section file follows the same ending style.
