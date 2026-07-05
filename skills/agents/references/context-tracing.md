# Context & Tracing Discipline

Every run leaves a trail long enough to replay it — context that entered the model has a known origin, and consumption that could run away has a known ceiling.

## Hard rules

### Context discipline

- **Retrieval budget per turn.** Cap how much retrieved content enters a single turn's context — a token count or a top-k document count, stated as a fixed number in the agent's config, never "however much fits."
- **Provenance of injected context.** Every piece of context entering the prompt is tagged with where it came from — instructions and retrieved data never share a trust level, even when concatenated into the same context window.

| Context source | Trust level | Enters as |
|---|---|---|
| System-authored instruction | Trusted | Instruction channel |
| User message | Semi-trusted (states intent, not a command over the system) | Instruction channel, scoped |
| Retrieved document / tool result | Untrusted | Data channel, delimited |

Enforcing that separation against an injection attempt is `security`'s job — load the `security` skill, whose own PHASE 0 gate routes to `references/llm.md` ("Prompt injection"); this skill's job is keeping the provenance tag present in the first place so there is something for that rule to check.

### Tracing law

Log the full model input and output for every run, tagged with a run id and the prompt/config hash that produced it — a run that can't be replayed is a run that can't be debugged.

Minimum trace record:

```json
{"run_id": "r_8f2a", "prompt_hash": "sha256:...", "config_hash": "sha256:...",
 "input": "...", "output": "...", "tool_calls": [], "timestamp": "..."}
```

A thin wrapper is enough to make this automatic instead of a per-call afterthought:

```python
def traced_call(agent: Agent, run_id: str, prompt: str, **kwargs) -> Output:
    record = {"run_id": run_id, "prompt_hash": sha256_of(prompt), "config_hash": sha256_of(agent.config)}
    output = agent.call(prompt, **kwargs)
    record.update(input=prompt, output=output.text, tool_calls=output.tool_calls)
    trace_sink.write(record)  # a call site can't "forget" the log — it's inside the wrapper
    return output
```

**Detect** — an agent entrypoint with no trace-id plumbing:

```bash
grep -rnL -E 'run_id|trace_id' --include='*.py' --include='*.ts' <agent-entrypoint-dir>
```

Pass: no output, or every listed file is confirmed not to be an entrypoint. Fail: an entrypoint file with no `run_id`/`trace_id` anywhere in it — its runs cannot be correlated back to the prompt/config version that produced them.

**Retention and redaction.** A trace sink that outlives the run holds real user input and model output, so it inherits the same PII-handling rules as any other data store — redact or hash fields the wider team reading traces shouldn't see in plaintext, and set a retention window instead of keeping every run forever "just in case." This is a data-handling decision this skill's tracing law creates a need for, not a substitute for `security`'s guidance on what counts as sensitive.

### Unbounded-consumption guards — what to log

Every agent run logs its running consumption alongside the trace record: iteration count so far, token count so far, and recursion depth so far. This is a logging/budget-declaration convention, not the enforcement itself.

```json
{"run_id": "r_8f2a", "iteration": 4, "max_iterations": 12, "tokens_used": 8200, "token_budget": 20000, "recursion_depth": 1}
```

Declaring the numeric budgets and enforcing the hard stop when one is exhausted — the loop-break logic itself and its detection command — is owned by `security`. Load the `security` skill before shipping any agent loop; its own PHASE 0 gate routes to `references/llm.md` section "Unbounded-consumption guards" for the loop-break rule and its detection command. This skill's job ends at making sure the counters exist for that rule to check.

### Memory hygiene

| Kind | Lives | Persists across | Cleared |
|---|---|---|---|
| Per-run scratch | In-process, a single run's context | Nothing — one run only | Automatically at run end |
| Session memory | A session store keyed by session id | Turns within one session | On session end/timeout |
| Long-term memory | A persistent store (DB, vector index) keyed by user/tenant | Sessions, explicitly | Only by an explicit deletion path |

Promoting something from session memory to long-term memory is an explicit, opt-in write — never an automatic side effect of "the conversation mentioned it." A user or an operator can name what got persisted and why.

**Detect** — a long-term memory write with no visible opt-in check nearby:

```bash
grep -rn -B2 -E '\.(save|persist|upsert)\(.*(memory|profile)' --include='*.py' --include='*.ts' <agent-dir>
```

Read: confirm each hit is preceded by an explicit consent/opt-in check (a flag, a user-confirmed action) in the surrounding lines. A save call with no such check nearby is writing to long-term memory unconditionally — grey zone if the check lives in a caller several frames away; trace the call path by hand before flagging.

## Debugging with a trace record

Once tracing is in place, a misbehaving run is diagnosed from its record instead of guesswork:

1. Get the reported `run_id` (from a support ticket, an alert, or a log line).
2. Query the trace sink for that `run_id` and pull the full record — input, output, `prompt_hash`, `config_hash`, and the consumption counters.
3. Resolve `prompt_hash` back to the exact prompt file version that produced it, so the diagnosis starts from the real prompt text, not the current one on disk.
4. Reproduce locally by replaying the same input against the resolved prompt/config version before changing anything.

```bash
git log --oneline -S "$(jq -r .prompt_hash trace_record.json)" -- prompts/
```

## Worked example — one turn end to end

A support agent handles "What's the status of my order?" by retrieving order records and answering:

1. **Retrieval budget:** top-3 documents, 2,000 tokens max — configured once in the agent's config, not computed ad hoc per call.
2. **Provenance:** the user's message enters the instruction channel; the 3 retrieved order records enter a delimited data block (`<context>...</context>`) with an explicit system-prompt note that content inside the block is data, never a command.
3. **Trace:** the `traced_call` wrapper above writes `run_id`, `prompt_hash`, and `config_hash` alongside the full input/output to the trace sink before returning — the call site cannot forget this step.
4. **Consumption:** the same trace record carries `iteration: 1, max_iterations: 6, tokens_used: 1400, token_budget: 8000` — nowhere near its ceiling, and visible without opening a log viewer's raw text.
5. **Memory:** the user does not ask the agent to remember anything, so nothing gets written to long-term memory; the turn's context is discarded once the response is sent — per-run scratch only.

```json
{"run_id": "r_92c1", "prompt_hash": "sha256:9f2a...", "config_hash": "sha256:11bd...",
 "input": "What's the status of my order?", "output": "Order #4821 shipped yesterday.",
 "iteration": 1, "max_iterations": 6, "tokens_used": 1400, "token_budget": 8000}
```

## Grey zones

- **Deterministic tool results still get a provenance tag.** A calculator tool's return value is fully trustworthy content-wise, but it is still tagged as data, not an instruction — the model must not treat any tool result as a new command just because the content itself is correct and non-adversarial.
- **Session-vs-long-term boundary.** "Remember my name for this chat" stays in session memory; "remember my name for next time" is the explicit promotion event. Judge by whether the user's phrasing names a persistence horizon beyond the current session — absent that, default to session-scoped, never silently promote.
- **Retrieval budget sizing** is genuinely task-dependent (a code-search agent needs a larger top-k than a FAQ bot) — the absolute rule is that the number is fixed and stated in config, not that any particular number is universally correct.
- **Trace retention windows** are also task-dependent (regulated data may require a shorter window than an internal tool) — the absolute rule is that some window is set and enforced, not that every agent shares one duration.

## Framework notes

Applies to: LangGraph's checkpointer persists full graph state automatically — once checkpoints survive across sessions, treat the checkpoint store as long-term memory and apply the same opt-in-promotion rule to what gets carried forward. CrewAI's built-in memory backends need the identical trace-tagging discipline layered on top, since neither framework ships prompt/config hashing or a provenance tag by default — both are conveniences for state management, not a substitute for the tracing law above.

None of the rules above require adopting either framework — a plain structured-logging call wrapped around a plain API client satisfies the tracing law and the consumption-logging convention with zero framework dependency.
