# Sources and provenance

## Immutable upstream receipt

- Google Labs `design.md`: https://github.com/google-labs-code/design.md
- Pin: `9bf8eae67128b6cc55ad9bf86665767deb4c11cd` (release 0.4.0)
- License: Apache License 2.0, `LICENSE` at that commit.
- Update-review paths: `README.md`, `PHILOSOPHY.md`, `docs/spec.md`, `LICENSE`, `packages/cli/package.json`, `packages/cli/src/commands/{lint,diff,export}.ts`, `packages/cli/src/linter/`, and associated linter tests/fixtures.

Adopted concepts: uppercase root artifact, structured named values paired with human-readable rationale, unknown-content preservation, deterministic lint findings, stable versioned formats, and bounded source-informed validation. Local deviations: the body token vocabulary, eleven H2 contract, and table/list grammar are authoritative instead of the upstream frontmatter/token schema; primitive states, debt, reduced-motion, and non-color declarations are mandatory; roots are explicit per product/app; checker is optional Python stdlib; no npm/npx, runtime installer, diff/export/search, contrast test, or compliance claim is copied.

## Legacy ownership transfer ledger

The transferred source files were `skills/document/references/design.md` at SHA-256 `8813f71702c1be68e231470c851d9e5a01de803d1f7867c81aaf24607aeb9d6a` and `skills/document/templates/design.md` at SHA-256 `b6b8bce93d93ce0cfe610c4dcaebc0505d99e1dae7c98aa33c58edebb1fe16fe`.
The row-level execution ledger in local eval scratch records exact source ranges and hashes, target locations, dispositions, rationale, contradiction resolution, checks, and stale-callsite result.
No row required owner-approved removal.

| Legacy identity | Target owner | Disposition and rationale |
|---|---|---|
| Principles and project intent | `templates/DESIGN.md` Product Intent and Principles | Transformed into explicit product/user/task/context and evidence-grounded principles. |
| Color, spacing, and type-scale tokens | `templates/DESIGN.md` Tokens and Typography | Preserved as named literal decisions; no stock defaults or aliases are retained. |
| Primitive inventory and required states | Template Primitives; `references/checker.md` | Preserved and strengthened with `data_bearing`, `same_as`, `non_color_cue`, and optional product-semantic states. |
| Motion and reduced-motion rule | Template Motion; checker contract | Preserved as exact declarations with bounded structural validation. |
| Responsive behavior | Template Layout and Responsive | Preserved with viewport and reflow expectations. |
| Accepted debt, date, and upgrade path | Template Accepted Debt; checker contract | Preserved as a deterministic table with real-date and substantive-path checks. |
| Same-change lifecycle | `SKILL.md` Artifact lifecycle | Preserved for material design decisions without recreating a universal frontend gate. |
| Primitive staleness audit | `SKILL.md` Artifact lifecycle; checker tests | Transformed into an explicit implementation-to-artifact inventory review because component locations are framework-specific. |
| Anti-generic literal/default check | `SKILL.md` Anti-patterns | Preserved as a judgment boundary: register a deliberate token or use the incumbent token. |
| Per-app placement | `SKILL.md` Routing | Preserved as one ownership root per coherent product system, including divergent deployable apps. |
| Former shell snippets and lowercase path | `references/checker.md`; `scripts/check-design.py` | Transformed into portable read-only checks; the lowercase path remains only a diagnostic and never an alias. |

## Other foundations

- UI UX Pro Max, https://github.com/nextlevelbuilder/ui-ux-pro-max-skill — design pattern/reference concepts only; inspect its current license and revision before updating any adoption.
- Agentic Design System, https://github.com/aa-on-ai/agentic-design-system — structured design-governance workflow concepts only; inspect license/revision before update.
- W3C WCAG 2.2, https://www.w3.org/TR/WCAG22/ — accessibility vocabulary and adaptation prompts, not checker conformance.
- W3C WAI-ARIA, https://www.w3.org/TR/wai-aria-1.2/ — normalized role/name evidence vocabulary, not computed-name implementation.
- Apple Human Interface Guidelines, https://developer.apple.com/design/human-interface-guidelines/ — platform interaction guidance.
- ISO 9241-210, Human-centred design for interactive systems — user/context framing; licensed standard, not reproduced.
- Nielsen Norman Group usability heuristics, https://www.nngroup.com/articles/ten-usability-heuristics/ — feedback, control, recovery, consistency prompts.

Update triggers: an explicit approved manual review of a pinned upstream release, material template/schema/checker change, license change, or a source correction. Review the immutable diff, license, paths, adoption/deviation list, probes, tests, checker/reference/template/skill/provenance/version/changelog impacts. Never fetch a moving branch/tag or install/call an upstream runtime during normal checking.

Probe before adopting external mechanics: confirm the source still supports the cited concept, that its license permits the intended reference, and that a conservative local test can distinguish evidence from inference. Runtime installers and browser automation remain out of scope.
