# Anthropic Lens (Claude Code / claude.ai)

## 1. Source

`anthropics/skills` → `skills/skill-creator` — SKILL.md, `scripts/` (`run_loop.py`, `run_eval.py`, `improve_description.py`, `generate_report.py`, `package_skill.py`, `aggregate_benchmark.py`, `quick_validate.py`, `eval-viewer/`), `agents/` (`grader.md`, `comparator.md`, `analyzer.md`), `references/schemas.md`.

## 2. What this lab illuminates

**Quality is measured behavior.**
Structural lint is table stakes; what matters is the delta between the with-skill and without-skill arms on real runs.
A skill nobody measured is a skill nobody knows works.

**The description is an optimizable artifact.**
A closed loop — measure trigger rate on labeled should/should-not queries, propose a structurally different description, repeat — treats triggering as an empirical property, not a writing style.
False triggers and missed triggers are both scored.

**Overfitting is the expected failure mode, so the harness blinds itself.**
Queries are split train/test (stratified, seeded); the improver only ever sees train results; the best iteration is picked by held-out test score.
The improvement prompt explicitly forbids repeating prior attempts.

**Distrust the judge and the eval alike.**
The grader puts the burden of proof on the expectation — uncertain means FAIL — rejects superficial passes (right filename, wrong content), and doubles as an eval critic that flags gameable assertions ("a hallucinated document that happens to mention the right name would also pass").
The comparator judges A/B blind, never told which skill produced which output.
The analyzer separates "fix the skill" findings from "fix the eval" findings.

## 3. Runtime plumbing (targeting Claude Code)

- Trigger testing shells out to `claude -p <query> --output-format stream-json --include-partial-messages`, injects the description under test as a throwaway uniquely-named `.claude/commands/*.md`, and watches the stream for a `Skill`/`Read` tool-use naming it. Reuses the calling session's Claude Code auth (strips the `CLAUDECODE` env var to permit nesting).
- Loop knobs — Anthropic's own calibration, configurable rather than law: trigger threshold 0.5, 3 runs per query, 0.4 holdout, max 5 iterations, ~10 parallel workers.
- `improve_description.py` baked-in craft: imperative voice ("Use this skill for…"), user intent over implementation, distinctive against sibling skills, ~100–200 words, ≤ 1024 chars with an auto-shorten safety net.
- `quick_validate.py`: same limits as OpenAI's fork plus one extra allowed frontmatter key, `compatibility` (optional, ≤ 500 chars).
- `package_skill.py` zips a skill into a `.skill` file — validates first, refuses on failure, strips `evals/`, `__pycache__`, `.DS_Store` from the distributable.
- `agents/*.md` are subagent prompt files (grader / blind comparator / analyzer); `schemas.md` locks the artifact formats (`grading.json`, `benchmark.json`, `history.json` version lineage, `comparison.json`, `analysis.json`); `eval-viewer/` is a zero-dependency local HTML review server for human-in-the-loop passes.

## 4. Divergences from this library

- **Eval artifacts as durable citizens.** Anthropic persists schema'd eval history (version lineage, benchmark aggregates) alongside the skill; this library keeps `evals/` as gitignored local scratch (contract §7). The methodology — measure, hold out, blind — is kept; the artifact bureaucracy is not, at this library's scale.
- **Frontmatter surface.** Anthropic admits `license`, `allowed-tools`, `compatibility`; the contract fixes exactly three keys (contract §1).
- **Executor coupling.** The whole harness assumes the Claude Code CLI as the eval runner; this library's [`evaluation.md`](evaluation.md) states the same loop runner-agnostically so evals run on any runtime.

## 5. Absorbed into core

- Baseline-delta arms, fresh sessions, snapshot-before-update → `evaluation.md` §1.
- Assertion discipline — objective script checks, gameable and both-arms-pass assertions discriminate nothing, flaky verdicts signal under-specification → `evaluation.md` §2.
- Trigger-eval mechanics — messy realistic queries, near-miss negatives, undertriggering asymmetry, fresh-eyes judging, held-out re-judging → `evaluation.md` §3 and `contract.md` §3.
- Transcript reading (repeated work → bundle a script; wasted detours → cut prose) → `evaluation.md` §4.
- Anti-overfitting (generalize from feedback; held-out prompts judge the result) → `evaluation.md` §5.
- Imperative, user-intent-first description craft was already `contract.md` §3 — confirmed, not re-added.
