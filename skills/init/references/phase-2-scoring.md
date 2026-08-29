# Phase 2 — Scoring and Placement

Phase 2 is pure deterministic decision logic.
It consumes the Phase 1 inventory and produces eligible AGENTS placement decisions without writing files, changing ownership, or reducing complete coverage.

## Candidate facts

Score each inventoried directory in stable normalized-path order.
Use only recorded evidence for file count, subdirectory count, code ratio, local configuration, module boundary, symbol density, export count, and reference centrality.
An unavailable or unmeasured fact contributes zero and remains explicitly marked unmeasured.
Do not infer counts from naming, placement depth, fan-out class, or loader class.

| Factor | Weight | High threshold | Evidence |
|---|---:|---|---|
| File count | 3 | More than 20 | Structural inventory |
| Subdirectory count | 2 | More than 5 | Structural inventory |
| Code ratio | 2 | More than 70% | Structural inventory |
| Unique patterns | 1 | Own configuration | Direct repository evidence |
| Module boundary | 2 | Entry boundary such as `index.ts` or `__init__.py` | Structural inventory |
| Symbol density | 2 | More than 30 symbols | LSP, codegraph, or recorded fallback |
| Export count | 2 | More than 10 exports | LSP, codegraph, or recorded fallback |
| Reference centrality | 3 | More than 20 references | LSP, codegraph, or recorded fallback |

For each factor, add its full weight when its high threshold is met.
Otherwise add zero unless the state contract defines an evidence-backed partial value.
Record every contributing fact and any degraded centrality evidence with the candidate.

## Placement rules

The repository root is always a placement.
For every other directory, apply these rules after complete inventory:

| Score | Decision |
|---|---|
| More than 15 | Place AGENTS.md. |
| 8 through 15 | Place only when direct evidence shows a distinct domain or local convention the parent cannot cover. |
| Less than 8 | No placement; inherited instructions remain available through the chain. |

`max_depth` defaults to 3 and bounds scoring and placement eligibility only.
It does not bound discovery, inventory, root-to-directory instruction chains, coverage counters, existing instruction inspection, ownership observation, or audit findings.
An arbitrarily deep target can therefore be covered by inherited instructions even when it is not eligible for a local placement.

## Output

Emit a stable `AGENTS_LOCATIONS` decision list containing the root and each approved local placement.
Each entry records normalized path, score, decision reason, direct evidence, inherited instruction chain, and whether centrality was measured or unmeasured.
Emit the independent complete-coverage inventory and counters for reconciliation and verification.
Do not represent absence of a local placement as absence of coverage.
