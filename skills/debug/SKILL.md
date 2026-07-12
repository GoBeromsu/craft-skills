---
name: debug
description: 'Diagnoses a failing program under a hypothesis-driven loop: reproduce the failure before theorizing, log observed facts separately from inferences, hold competing hypotheses until the cheapest probe discriminates between them, and confirm the mechanism with instrumentation before any fix lands. Use when a test or command fails for an unclear reason, a bug needs bisecting to the commit or input that caused it, a failure only reproduces intermittently, or asked to find out why something is broken ("이거 왜 안 되는지 찾아줘"). Not for restructuring working code (use refactor), suite-level test architecture (use testing), or triaging a vulnerability class (use security).'
metadata:
  version: 1.1.0
---

# debug

Diagnose why code is broken under one loop: establish observed evidence, log fact separately from inference, hold competing hypotheses only while evidence is ambiguous, and instrument only when existing evidence cannot confirm the mechanism. Done means the failure is reproducible on command or directly established by deterministic evidence, the fix is proven by a failing-then-passing regression test and real user scenario, and every temporary artifact is removed.

## The loop

1. **Establish evidence.** Reproduce the failure on demand and capture the exact invocation and output. A deterministic failing test, stack trace, or static contract violation may seed the first hypothesis when it directly establishes the failure. If it only fails sometimes, run it N times and record the failure rate instead of guessing — an unreproduced bug is a report, not yet a debugging target.
2. **Log evidence, not conclusions.** Runtime evidence outranks plausible code reading. Keep two columns as you go: `Observed` (a command, a stack-trace line, a log entry — verbatim) and `Inferred` (what it's believed to mean). Never write an inference into the observed column; a hypothesis that turns out wrong should trace back to the specific inference that produced it, not get tangled into the facts.
3. **Hold competing hypotheses when evidence is ambiguous.** Write down at least two candidate explanations only when the observed facts leave more than one plausible mechanism. For the next step, ask "which probe kills one hypothesis but not the other?" and run that one — not the one that would merely confirm the favorite. When direct evidence isolates a mechanism, follow it rather than inventing alternatives.
4. **Bisect the search space.** Pick the axis that fits the failure:
   - **Temporal** — a regression between a known-good and known-bad commit: `git bisect start`, `git bisect bad`, `git bisect good <sha>`, then `git bisect run <cmd>` with a script that exits 0/1 against the reproduction command, non-interactive end to end.
   - **Input** — a large or complex failing input: halve it, keep whichever half still reproduces, repeat until the input is minimal.
   - **Layer** — a multi-hop pipeline (client → gateway → service → DB): probe the midpoint first to learn which half owns the fault, then recurse into that half only.
5. **Instrument only when evidence cannot discriminate.** When the existing evidence cannot prove or disprove the leading hypothesis, add the smallest probe that can — a log line, an assertion, or a debugger breakpoint — and run it. Touch source once the mechanism is confirmed by observed evidence, not merely suspected from reading the code.
6. **Fix, prove, clean up.** Write the fix once the mechanism is confirmed. Per `testing`'s prove-it law, add a regression test that fails against the pre-fix code and passes against the post-fix code (red, then green) in the same change as the fix. After that test passes, exercise the real user-facing scenario too. Inventory every temporary artifact before creating it — files, processes, ports, environment changes, and debugger sessions — then remove each one before the diff lands; instrumentation is disposable, the regression test is not.

Escape hatch: reproduction is genuinely too expensive or too flaky to pin down (a rare race, a third-party outage) — timebox the search, act on the best-evidenced hypothesis, and say explicitly in the report which assumption stands unconfirmed.

## Hand-offs

- The fix needs restructuring beyond the minimal patch (extract, rename, deduplicate) → `refactor`.
- The regression test's placement in the suite (unit vs. integration, fixture scope) → `testing`.
- The root cause is a vulnerability class (injection, auth bypass, secret exposure), not a defect → `security`.

## Requirements

- `git` — bisect (step 4, temporal axis).
- The project's incumbent test runner for the regression test in step 6 (`pytest`, `vitest`, or equivalent).
