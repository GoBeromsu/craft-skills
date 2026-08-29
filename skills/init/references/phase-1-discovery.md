# Phase 1 — Discovery

Discovery builds one deterministic, evidence-grounded repository inventory for scoring, reconciliation, coverage, audit findings, and state validation.
It does not write targets, select mutations, infer loader behavior, or let placement depth limit coverage.

## Inputs and exclusions

Start at the repository root and apply the state contract's normalized-path, containment, symlink, special-file, UTF-8/LF, and exclusion rules.
Record the repository root, all non-excluded first-party directories, and every non-excluded first-party regular-file target at arbitrary depth without following symlinks.
Record unreadable, truncated, special, symlinked, or unclassified paths as non-clean evidence.
Do not use a directory's depth to omit it from inventory.

For each target directory, read every `AGENTS.md` from repository root through that directory in order.
Preserve the complete chain, raw bytes, hashes, modes, and applicable instruction context.
The nearest AGENTS instruction wins on conflict.
This root fallback is an instruction rule only; it does not prove loading behavior.

Inventory incumbent `CLAUDE.md` files separately.
Only the exact bytes `b"@AGENTS.md\n"` are shim candidates.
Any other CLAUDE content is substantive evidence for reconciliation and requires the appropriate proposal; never silently treat it as canonical or managed.

## Evidence collection

Collect reproducible facts for directory topology, files and languages, entry points, build and test commands, configurations, generated/vendor boundaries, symbols, exports, references, and local conventions.
Attach each conclusion to its file, command, tool result, or incumbent instruction source.
Prefer direct repository evidence over directory-name conventions.
When evidence is unavailable or contradictory, record the unknown or conflict rather than guessing.

Use LSP and codegraph as complementary sources when available.
When neither is available, use available structural and syntax evidence, mark centrality unmeasured, and preserve the missing-evidence reason for scoring and reporting.
Do not invent symbol, export, or reference counts.

## Execution scheduling

Classify execution scheduling independently from loader behavior.
An agent-spawn runtime may fan out independent, evidence-bounded investigations after the structural pass.
A single-agent runtime performs the same selected investigations sequentially.
Choose investigations for unresolved high-impact questions, cross-boundary risk, unfamiliar languages, generated code, security or migration sensitivity, and high-centrality evidence gaps.
Do not increase fan-out merely for file count, repository depth, or workspace count.

Merge all observations in stable normalized-path order.
Resolve duplicates by retaining the raw evidence and recording conflicts, not by averaging or selecting the most convenient claim.
The result is one inventory with explicit evidence, unknowns, and coverage status for Phase 2.

## Loader evidence handoff

Use [loading contract](loading-contract.md) for loader probes, classifications, and persistence rules.
Record only probe-backed loader evidence in the inventory.
Source-only, unavailable, conflicted, version-mismatched, or non-automatable observations remain unknown.
Never derive a loader class from execution fan-out, AGENTS placement, root fallback, or a successful map.
