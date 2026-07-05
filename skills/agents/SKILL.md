---
name: agents
description: '"build an agent", "에이전트 만들어줘", "prompt engineering", "add a tool to my agent", "LLM eval" — LLM-agent engineering discipline: eval-first law, prompts-as-code, tool design, and context/tracing discipline for building and changing agent behavior. Routes through a PHASE 0 work-type gate to references/evals.md, references/prompts-tools.md, references/context-tracing.md.'
version: 1.0.0
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob]
compatibility: claude-code, codex
---

# agents

Build and change LLM-agent behavior under one discipline: **prove it with an eval first, version the prompt as code second, bound the context third.**

## Overview

This skill is an index for LLM-agent engineering: building an agent, changing what it does, designing its tools, and wiring the context/memory/observability around it. Shared laws live here; the per-topic iron list lives in `references/`. Load the matching reference before writing a prompt, adding a tool, or shipping a behavior change. Examples stay framework-light: a plain Python client plus typed dataclasses/pydantic models exercises every rule here; LangGraph, CrewAI, and similar frameworks are named only as "applies to" notes where their abstractions map onto a rule.

## When to Use

- Building a new agent, or changing what an existing one does — a new capability, a rewritten prompt, a changed tool set, a different routing decision.
- Writing or editing a system prompt, a tool schema, or a few-shot example set — "prompt engineering."
- Adding, removing, or re-scoping a tool an agent can call — "add a tool to my agent."
- Setting up or auditing an LLM eval — golden set, pass criteria, regression case.
- Wiring retrieval, session memory, or trace logging around an agent.

**Not for:** training or fine-tuning a model — `ml` owns this. Deterministic business logic with no model in the loop — unit/integration tests are `testing`'s job. Hosting or serving the model API itself — `backend` owns this. Enforcing prompt-injection, output-execution, or tool-permission defenses — `security` owns the enforcement catalog; this skill states the design principle and hands off.

## PHASE 0 — work-type gate (run first, every time)

Do not change agent behavior, write a prompt, or wire a tool before this gate.

1. Identify the work type:
   - **Agent or LLM-feature behavior change** (new agent, prompt edit, tool logic change, routing change) → `references/evals.md` FIRST, always. Eval-first is the entry law, not a step you get to after the change already looks good.
   - **Prompt or tool authoring** (writing a system prompt, designing a tool's argument schema) is itself a behavior change, not a separate lane — read `references/evals.md` first like every behavior change, then `references/prompts-tools.md` for the authoring rules.
   - **Retrieval, memory, or observability work** (RAG wiring, session memory, trace/logging setup) → `references/context-tracing.md`.
   - **Model training or fine-tuning** → STOP. This skill does not cover it — load `ml` instead.
2. STOP and read the matching reference(s) in full, in this order:

   | Scope | Read |
   |---|---|
   | Every behavior change, including prompt/tool authoring (always, first) | `references/evals.md` |
   | Prompt/tool authoring (after evals.md) | `references/prompts-tools.md` |
   | Retrieval/memory/observability | `references/context-tracing.md` |
   | Model training/fine-tuning | STOP — load `ml` |

3. Apply the three core laws below plus the matching reference's iron list.

## Core laws

### Eval-first

No agent-behavior change ships without an eval set and stated pass criteria — a prompt edit, a tool-logic change, and a routing change are all behavior changes. Evals are versioned data files committed alongside the code they gate, not a notebook run once and discarded.

**Detect** — a diff touching prompts or agent code with no corresponding eval change:

```bash
git diff --name-only <base>...HEAD | grep -qE '(^|/)(prompts?|agents?)/.*\.(py|ts|md|txt|jinja)$' \
  && { git diff --name-only <base>...HEAD | grep -qE '(^|/)evals?/' || echo "FLAG: behavior change with no evals/ touched"; }
```

Pass: no `FLAG` line — either nothing behavior-relevant changed, or the eval set changed alongside it. Fail: `FLAG` printed — the change is blocked until an eval case covers it; see `references/evals.md` for what "covers" means.

Grey zone — the command above is a floor, not a ceiling: it only greps `prompts?/` and `agents?/` paths, so it misses a behavior change landing in `src/`, `app/`, or a framework module. Judge by whether the diff alters agent behavior (tool logic, routing, system prompts), not by path — a change that meets that test still needs an eval case even when the command above stays silent.

### Prompts are code

A prompt is source code: it lives in a dedicated `prompts/` directory (or module), gets a diff, and gets reviewed — never only inside a vendor dashboard where changes are unversioned and unreviewable.

**Detect** — an inline prompt string longer than 10 lines living outside a `prompts/` directory:

```bash
find . -path '*/node_modules/*' -prune -o -path '*/prompts/*' -prune -o \
  \( -name '*.py' -o -name '*.ts' -o -name '*.tsx' \) -print \
  | while read -r f; do
      awk -v f="$f" '/"""/{c++; if (c%2==1) start=FNR; else if (FNR-start>10) print f":"start"-"FNR}' "$f"
    done
```

Pass: no output. Fail: any `file:start-end` line — a prompt long enough to need its own diffable file is instead buried inline. TypeScript template literals follow the identical `awk` pattern with the backtick as the delimiter.

### LLM output is untrusted input

Whatever the model produces — a completion, a tool-call argument, a generated query — carries no more trust than the least-trusted content that fed into generating it. This skill states the principle; it does not own the enforcement catalog. Before shipping any code that acts on a model completion or tool-call argument, load the `security` skill — its own PHASE 0 gate routes an LLM-powered feature to `references/llm.md`, section "Model output is untrusted input," for the parse/validate pattern and its detection command.

## Hand-offs

- Prompt-injection defense, output-execution hardening, and tool-permission enforcement (least-privilege allowlists, plus the detection command for both) → load the `security` skill; its own PHASE 0 gate routes to `references/llm.md` for the LLM surface. This skill states the design-time principle for each; `security` owns the enforcement/detection catalog.
- Model training or fine-tuning → `ml`.
- Serving the model or agent behind an API → `backend`.
- Deterministic, model-free business logic — unit and integration tests → `testing`.

## Requirements

- A plain Python (or TypeScript) client for the model API under test — no framework required to exercise any rule in this skill.
- `git`, `grep`, `awk`, `find` for the detection commands above and in the references.
- An eval runner capable of replaying a golden set against pass criteria — a plain script is sufficient; a framework's eval harness is optional.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It's a one-line prompt tweak, no eval needed." | A one-line tweak changes behavior exactly as much as a rewrite — the eval set is what proves the tweak didn't regress a case that used to pass. |
| "The prompt is short enough to keep inline." | Short today, ten edits from now it's 40 lines with no diff history. Start it in `prompts/` before it needs to move. |
| "I'll trust the model's tool-call arguments, it's a well-tested prompt." | A well-behaved prompt in testing is not a guarantee against a jailbreak, an indirect-injection document, or an ordinary model mistake in production. Parse every argument. |
| "The framework's built-in tracing is enough." | Confirm it actually persists a run id and a prompt/config hash, not just a console log that vanishes on redeploy. |
| "This is just a prototype agent, skip the eval set." | Prototype prompts get promoted to production without anyone deciding to redo the discipline. Start the golden set at one case per behavior and grow it — never skip it. |

## Red Flags

- A merged diff that changes a prompt or agent-routing code with zero corresponding change under `evals/`.
- A prompt string over 10 lines defined inline in application code instead of a `prompts/` file.
- A tool handler that acts on a raw model completion or tool-call argument with no schema validation in between.
- An agent entrypoint with no `run_id`/`trace_id` argument or plumbing.
- A "temporary" agent or prompt in production with no eval set, still there a quarter later.

## Verification

- [ ] PHASE 0 routed to the matching reference before the change was written.
- [ ] The behavior change has a corresponding eval case (golden-set diff or new case) in the same change.
- [ ] Every prompt over 10 lines lives in a dedicated `prompts/` file, not inline (detection command clean).
- [ ] Every tool handler validates its arguments against a typed schema before acting.
- [ ] The agent entrypoint logs a `run_id`/`trace_id` alongside the prompt/config hash it used.
- [ ] Prompt-injection, output-execution, and tool-permission enforcement were reviewed by loading the `security` skill (its PHASE 0 gate routes to `references/llm.md`), not re-implemented here.
