# Consensus Receipt — technical-report — round 3 — 2026-06-25

status: degraded
scope: whole-file
providers_requested: codex, gemini, claude
providers_live: codex, claude

## Degraded Providers

- **gemini**: CLI auth failed — `IneligibleTierError: UNSUPPORTED_CLIENT` (Gemini Code Assist
  free-tier no longer supported for this client). Environmental, independent of the package;
  host-specific stack-trace frames elided. The other two providers carried the round.

## codex verdict

VERDICT: APPROVE

## claude verdict

VERDICT: APPROVE

## Result

Partial convergence (degraded: 2/3 models live). All live models APPROVE. Re-run with all providers available to confirm.
