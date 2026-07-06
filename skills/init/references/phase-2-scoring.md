# Phase 2 — Scoring & Location Decision

Phase 2 turns the merged project model from Phase 1 into a concrete list of directories that
warrant their own `AGENTS.md`. It is pure decision logic — no files are written here.

## Scoring matrix

Score each candidate directory by summing `weight × (1 if the factor clears its high threshold else
partial/0)`. The weights are load-bearing — centrality and file count dominate by design.

| Factor | Weight | High threshold | Source |
|--------|--------|----------------|--------|
| File count | 3× | >20 | bash |
| Subdir count | 2× | >5 | bash |
| Code ratio | 2× | >70% | bash |
| Unique patterns | 1× | Has own config | explore |
| Module boundary | 2× | Has `index.ts` / `__init__.py` | bash |
| Symbol density | 2× | >30 symbols | LSP / codegraph |
| Export count | 2× | >10 exports | LSP / codegraph |
| Reference centrality | 3× | >20 refs | LSP / codegraph |

When centrality is **unmeasured** (no LSP/codegraph — see phase-1 fallback), score the three
LSP/codegraph rows (symbol density, export count, reference centrality) from the `ast-grep`/explore
inventory where possible, and otherwise treat them as 0 — never invent a centrality number. Record
that the score was computed on the degraded path so the report can flag it.

## Decision rules

| Score | Action |
|-------|--------|
| **Root (`.`)** | **Always create** |
| **>15** | Create `AGENTS.md` |
| **8–15** | Create **if** it is a distinct domain (own conventions/boundary the parent does not cover) |
| **<8** | Skip — the parent `AGENTS.md` covers it |

The root is unconditional; this is what keeps the engine useful even on a shallow/fresh repo, where
every subdir scores <8 and the run collapses to a single root map. That degraded-but-valid outcome
is expected on the bootstrap path, not a failure.

## Output

Emit an explicit location list for Phase 3 to consume:

```
AGENTS_LOCATIONS = [
  { path: ".",         type: "root" },
  { path: "src/hooks", score: 18, reason: "high complexity" },
  { path: "src/api",   score: 12, reason: "distinct domain" }
]
```

**Cartography scope:** exclude the `docs/` ontology scaffold that Phase 0 just seeded — the code
map describes code directories, not the documentation rails. Mapping `docs/` back onto itself is
circular and adds no signal.
