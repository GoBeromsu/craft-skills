# Phase 4 — Review & Deduplicate

## Per-file review

For each generated `AGENTS.md`:

- Remove generic advice (anything that would apply to *any* project).
- Remove content duplicated from the parent file (**dedup-vs-parent**).
- Trim to the size budget: **root 50–150 lines, subdir 30–80 lines.**
- Verify telegraphic style — terse, scannable, no prose padding.

## Quality anti-patterns (reject on sight)

- **Static agent count** — agent count must scale with project size/depth (phase-1 table).
- **Sequential when fan-out was available** — on agent-spawn runtimes, explore + LSP + codegraph run
  concurrently. (Sequential is correct *only* on single-agent runtimes.)
- **Ignoring existing** — always read existing AGENTS.md first, even under `--create-new`.
- **Over-documenting** — not every directory needs an `AGENTS.md`; respect the Phase 2 cutoffs.
- **Redundancy** — a child never repeats its parent.
- **Generic content** — remove anything true of all projects.
- **Verbose style** — telegraphic or die.

## Final report (observability — hard requirement)

Every run ends with an explicit report. A degraded or fallback run must be **visible**, never silent.
Enumerate:

```
=== init Complete ===

Mode: {bootstrap | cartography | update | create-new}
Path taken: {concurrent fan-out | sequential single-agent}
Centrality: {measured via LSP/codegraph | unmeasured (explore/ast-grep fallback)}

Docs/ ontology (Phase 0):
  {created | already present | n/a}  — dirs seeded: {N}, anchors seeded: {N}
Managed block: {replaced legacy hard-rail block | none found | n/a}

Cartography (Phases 1–4):
  [OK] ./AGENTS.md (root, {N} lines)
  [OK] ./src/hooks/AGENTS.md ({N} lines)

Dirs analyzed: {N}
AGENTS.md created: {N}   updated: {N}

Hierarchy:
  ./AGENTS.md
  └── src/hooks/AGENTS.md
```

The report must state: files created/updated, dirs analyzed, the path taken (concurrent vs
sequential), whether centrality was measured or unmeasured, and the managed-block action. Any run
that cannot fill one of these lines names the gap explicitly rather than omitting it.
