---
name: agents
description: 'Builds and changes LLM-agent systems — the prompts, tool schemas, and context/tracing wiring around them — under an eval-first discipline: prove a behavior change against a versioned eval set before shipping, version prompts as code, and bound retrieval/memory/consumption. Use when building a new agent ("에이전트 만들어줘"), writing or editing a system prompt ("prompt engineering"), adding or re-scoping a tool an agent can call ("add a tool to my agent"), setting up an LLM eval or golden set, or wiring RAG/session memory/trace logging. Not for authoring or managing skills in this library (use `skillify`) or for tool-permission and consumption enforcement (use `security`).'
metadata:
  version: 2.0.0
---

# agents

Build and change LLM-agent behavior under one discipline: prove it with an eval first, version the prompt as code second, bound the context third. A change is done when its eval case passes, its prompt lives in a diffable file, and its run is traceable by a `run_id`.

## PHASE 0 — work-type gate

Read the matching reference in full before writing a prompt, adding a tool, or shipping any behavior change.

| Work type | Read (in order) |
|---|---|
| Agent/LLM-feature behavior change — new agent, prompt edit, tool-logic change, routing change | `references/evals.md` |
| Prompt or tool authoring — itself a behavior change, not a separate lane | `references/evals.md`, then `references/prompts-tools.md` |
| Retrieval, memory, or observability wiring | `references/context-tracing.md` |
| Model training or fine-tuning | stop — load `ml` instead |

Apply the three core laws below plus the matching reference's iron list.

## Core laws

### Eval-first

No agent-behavior change ships without an eval set and stated pass criteria — a prompt edit, a tool-logic change, and a routing change are all behavior changes. Evals are versioned data files committed alongside the code they gate, never a notebook run once and discarded.

**Detect** — a diff touching prompts or agent code with no corresponding eval change:

```bash
git diff --name-only <base>...HEAD | grep -qE '(^|/)(prompts?|agents?)/.*\.(py|ts|md|txt|jinja)$' \
  && { git diff --name-only <base>...HEAD | grep -qE '(^|/)evals?/' || echo "FLAG: behavior change with no evals/ touched"; }
```

Pass: no `FLAG` line. Fail: `FLAG` printed — the change is blocked until an eval case covers it (see `references/evals.md`). This command is a floor, not a ceiling: it only greps `prompts?/`/`agents?/` paths and misses a behavior change landing in `src/` or a framework module — judge by whether the diff alters agent behavior, not by path alone.

### Prompts are code

A prompt is source code: it lives in a dedicated `prompts/` directory, gets a diff, and gets reviewed — never only inside a vendor dashboard where changes are unversioned and unreviewable.

**Detect** — an inline prompt string over 10 lines living outside `prompts/`:

```bash
find . -path '*/node_modules/*' -prune -o -path '*/prompts/*' -prune -o \
  \( -name '*.py' -o -name '*.ts' -o -name '*.tsx' \) -print \
  | while read -r f; do
      awk -v f="$f" '/"""/{c++; if (c%2==1) start=FNR; else if (FNR-start>10) print f":"start"-"FNR}' "$f"
    done
```

Pass: no output. Fail: any `file:start-end` line — a prompt long enough to need its own diffable file is instead buried inline. TypeScript template literals follow the identical pattern with a backtick delimiter.

### LLM output is untrusted input

A completion, a tool-call argument, a generated query — whatever the model produces carries no more trust than the least-trusted content that fed into generating it. This skill states the principle; it does not own the enforcement catalog. Before shipping code that acts on a model completion or tool-call argument, load the `security` skill for the parse/validate pattern (its own PHASE 0 gate routes to `references/llm.md`).

## Hand-offs

- Prompt-injection defense, output-execution hardening, tool-permission allowlists, and unbounded-consumption loop-breaks (plus their detection commands) → `security` — this skill states the design-time principle, `security` owns enforcement.
- Model training or fine-tuning → `ml`.
- Serving the model or agent behind an API → `backend`.
- Deterministic, model-free business logic (unit/integration tests) → `testing`.
- Creating, updating, renaming, or retiring a skill in this library, including this one → `skillify`.

## Requirements

- A plain Python or TypeScript client for the model API under test — no framework required to exercise any rule in this skill.
- `git`, `grep`, `awk`, `find` for the detection commands above and in `references/`.
- An eval runner that can replay a golden set against pass criteria — a plain script is sufficient.

## Verification

- [ ] PHASE 0 routed to the matching reference before the change was written.
- [ ] The behavior change has a corresponding eval case (golden-set diff or new case) in the same change.
- [ ] Every prompt over 10 lines lives in a dedicated `prompts/` file, not inline.
- [ ] Every tool handler validates its arguments against a typed schema before acting.
- [ ] The agent entrypoint logs a `run_id`/`trace_id` alongside the prompt/config hash it used.
- [ ] Prompt-injection, output-execution, and tool-permission enforcement were reviewed via the `security` skill, not re-implemented here.
