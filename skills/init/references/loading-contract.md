# Loading contract

Loading is an observable runtime property, not a claim inferred from a runtime name, documentation, installation source, or a successful command fan-out.
`AGENTS.md` is canonical.
A sibling `CLAUDE.md` is an adapter only when its raw bytes are exactly `@AGENTS.md\n`.

## Evidence record

A loading observation records the normalized repository-relative root, runtime identifier, runtime version, probe fixture hash, source/version probe outputs, raw sentinel observations, and the resulting status.
The only statuses are `verified`, `unknown`, `conflicted`, `unavailable`, and `version-mismatch`.
Persist a loading class only for `verified`; every other status has class `unknown`.

A source probe establishes where a runtime was obtained.
A version probe establishes the executable or API version which ran the sentinel.
Neither establishes loading behavior.
Missing, unparsable, conflicting, or different-version evidence is `unknown`, `conflicted`, `unavailable`, or `version-mismatch` as applicable.

## Runtime evidence registry

Review the matching official source before changing a probe, support boundary, or classification rule.
The safe version probe identifies the installed target only; the sentinel still decides loading behavior.

| Runtime | Official source | Safe version probe | Support boundary |
| --- | --- | --- | --- |
| Claude Code | <https://code.claude.com/docs/en/memory> | `claude --version` | Native `CLAUDE.md`; `AGENTS.md` requires the exact sibling import adapter. |
| OpenAI Codex | <https://learn.chatgpt.com/docs/agent-configuration/agents-md> | `codex --version` | `AGENTS.md` chain assembled at run/session start. |
| OpenCode | <https://opencode.ai/docs/rules/> | `opencode --version` | Core rules discovery only; extensions such as OMO require their own probe evidence. |
| Gajae Code | <https://github.com/Yeachan-Heo/gajae-code> | `gjc --version` | Installed GJC runtime matching the probed executable. |
| Gemini CLI | <https://google-gemini.github.io/gemini-cli/docs/cli/gemini-md.html> | `gemini --version` | Native `GEMINI.md`; `AGENTS.md` only when configured as a context filename. |
| Cursor | <https://cursor.com/docs/rules> | `cursor --version` when available | Editor/CLI build that exposes the documented nested `AGENTS.md` behavior. |
| GitHub Copilot | <https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot> | No universal local probe | Mark unavailable unless the active Copilot surface can run the sentinel and report references. |
| Windsurf / Devin Desktop | <https://docs.devin.ai/desktop/cascade/memories> | No universal local probe | Mark unavailable unless the active desktop agent can run the sentinel. |

A selected runtime release, changed official rule, changed version probe, or changed loading surface triggers official-documentation review and rerunning the applicable sentinel cases.
Never copy this registry into the snapshot; snapshots retain only the generic evidence status, source category, version string, fixture hash, observations, and resulting class.

## Sentinel matrix

Run a fresh, applicable sentinel fixture with distinct root, child, and sibling markers.
Record startup and read observations, including precedence.

| Observed behavior | Verified class | Coverage consequence |
| --- | --- | --- |
| Each selected file receives only its own marker | `file-scoped` | A unit is covered only when its expected file is selected. |
| A selected directory receives its marker and descendant markers | `recursive` | The expected root-to-nearest chain must be observed without sibling leakage. |
| A selected descendant receives the root-to-nearest ancestor chain, with nearest precedence | `ancestor-only` | The expected root-to-nearest chain must be observed without sibling leakage. |
| No applicable complete sentinel result | `unknown` | Every affected unit is unverified. |

A runtime may execute a command or expose a skill without proving any class.
Source inspection, help text, version text, a manually supplied file, or an unrelated fixture are not sentinel evidence.

## Conservative classification

The probe must run against the same applicable loading mechanism, supported version, and fixture hash that the report names.
A missing source probe, missing version probe, unavailable executable, changed fixture, partial observations, inconsistent repeated observations, sibling leakage, or unresolved precedence prevents a verified class.
Conflicting verified-looking observations are `conflicted`, never a tie-breaker.

For each coverage unit, compare the observed chain to the expected ordered root-to-nearest `AGENTS.md` chain.
Exact applicable behavior is `covered`; verified omission is `gap`; sibling leakage or unresolved precedence is `ambiguous`; unknown evidence is `unverified`.

The root fallback is advisory text, not native loading evidence:

> Before working on a path, read every `AGENTS.md` from the repository root through the target's directory in order; the nearest file's instruction wins on conflict.

Its presence never upgrades `unknown` to `covered`.
It can be recorded as `root-fallback` basis only alongside the native evidence result; it cannot manufacture a verified loading class.
