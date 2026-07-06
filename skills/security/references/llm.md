# LLM Feature Security

A model's output and anything it retrieves are untrusted input, never instructions — the trust boundary sits between your system prompt and everything the model reads or produces afterward.

## Contents

- [Hard rules](#hard-rules)
- [Prompt injection](#prompt-injection)
- [Model output is untrusted input](#model-output-is-untrusted-input)
- [Tool-permission scoping](#tool-permission-scoping)
- [Unbounded-consumption guards](#unbounded-consumption-guards)
- [RAG (Retrieval-Augmented Generation) isolation](#rag-retrieval-augmented-generation-isolation)

## Hard rules

| Concern | Do / Use | Never |
|---|---|---|
| Retrieved/tool content in the prompt | Wrapped in a clearly delimited data block, referenced as data | Concatenated into the system prompt as if it were an instruction |
| Model output used downstream | Parsed/validated against a schema before use | Passed raw into `exec`/`eval`/a shell call/a raw SQL string/an HTML sink |
| Tool access per agent | Least-privilege allowlist scoped to the task | A single tool set shared by every agent regardless of need |
| Retrieval scope | Query filtered by the caller's tenant/user ID | A shared index queried with no tenant predicate |

## Prompt injection

Prompt injection is an attacker's instructions taking effect because the model can't distinguish "trusted system instruction" from "untrusted data it's processing." **Direct** injection: the attacker types the adversarial instruction straight into the chat. **Indirect** injection: the adversarial instruction hides inside a document, web page, email, or tool result the model retrieves and reads as part of its context — the user never sees the injected text.

**Detect** — user- or retrieval-sourced content concatenated straight into a system/instruction string:

```bash
grep -rnE '(system_prompt|SYSTEM_PROMPT|instructions)\s*(\+=|=.*\+)' --include="*.py" --include="*.ts" .
```

Reading: any hit builds the instruction channel by string concatenation — trace whether the concatenated value is user- or retrieval-sourced. If so, it's a finding. Zero hits, or every hit passing retrieved content only inside a clearly labeled data section (e.g. `<document>{content}</document>` with an explicit system rule that content inside the delimiter is data, never a command), is a pass. Heuristic: string-building spread across several lines/functions won't match a single grep — trace the prompt-assembly function by hand too.

**Fix**: keep instructions and data in separate, explicitly labeled sections; state once, at the system level, that content inside data delimiters is never to be treated as a command; never let a tool result or retrieved document be appended to the instruction channel itself.

Grey zone: few-shot examples you wrote and committed to the prompt are trusted content, not data needing quarantine — the rule applies to content that entered the context at request time from a user, a retrieval call, or a tool result, not to instructions you authored yourself.

## Model output is untrusted input

Whatever the model produces — a completion, a tool-call argument, a generated SQL string — carries no more trust than the least-trusted content that fed into generating it. Treat it exactly like user input: parse and validate before acting on it.

**Detect** — a model-response variable flowing into a dangerous sink:

```bash
grep -rnE '(response|completion|llm_output|model_output)\.[a-zA-Z_]*.*(exec\(|eval\(|subprocess|dangerouslySetInnerHTML)' \
  --include="*.py" --include="*.ts" --include="*.tsx" .
```

Reading: this is a coarse heuristic — most real cases won't be a single grep-matchable line. Manually trace every place a model's text or tool-call arguments reach `exec`/`eval`/a shell call/a raw SQL string/an HTML-rendering sink; each needs a parse step (schema validation, an allowlist, an escaping function) between the model and the sink.

**Fix**: validate tool-call arguments against a typed schema before executing the tool; never let a model-generated string become a shell command, SQL query, or raw HTML directly.

```python
class SendEmailArgs(BaseModel):
    to: EmailStr
    subject: str = Field(max_length=200)
    body: str = Field(max_length=5000)

def handle_tool_call(name: str, raw_args: dict) -> None:
    match name:
        case "send_email":
            args = SendEmailArgs.model_validate(raw_args)  # parses or raises
            send_email(args.to, args.subject, args.body)
```

```ts
const SendEmailArgs = z.object({
  to: z.string().email(),
  subject: z.string().max(200),
  body: z.string().max(5000),
});

function handleToolCall(name: string, rawArgs: unknown): void {
  if (name === "send_email") {
    const args = SendEmailArgs.parse(rawArgs); // parses or throws
    sendEmail(args.to, args.subject, args.body);
  }
}
```

## Tool-permission scoping

Every tool an agent can call is a capability an attacker gains if they manage to steer the agent — scope tools to exactly what the task needs, per agent, not globally.

**Detect**: list each agent's tool grant and confirm no agent holds a tool it never uses in its own task.

```bash
grep -rnE "allowed[-_]tools|tools\s*=\s*\[" --include="*.py" --include="*.ts" --include="*.yaml" --include="*.yml" .
```

Reading: a broad grant — for example, a research agent holding a delete-data or send-payment tool — is a finding regardless of whether it's ever invoked in practice. Least privilege means the grant itself is narrow.

**Fix**: define tool sets per agent role; a file-read agent gets read tools only, a support agent gets read + reply tools, never write/delete/payment tools unless the task specifically requires them.

Grey zone: a general-purpose assistant genuinely needs a broad tool set to do its job. Scope least privilege there by task-scoped session and per-call authorization checks, not by permanently stripping tools an agent's role actually requires.

## Unbounded-consumption guards

An agent loop with no cap on iterations, tokens, or recursive tool calls turns a single adversarial nudge — or an ordinary bug — into a runaway cost or denial-of-service.

**Detect**: confirm every agent loop has an explicit max-iteration/max-token/max-depth guard.

```bash
grep -rnE 'while True:|for\s*\(;;\)|while\s*\(true\)' --include="*.py" --include="*.ts" --include="*.js" . \
  | grep -v node_modules
```

Reading: any unbounded loop in agent-orchestration code is a finding unless a budget check (`if iterations >= MAX_ITERATIONS: break`) sits inside it.

**Fix**: hard cap on loop iterations, total tokens per run, and recursive tool-call depth; fail closed (stop and report) when the budget is exhausted, never silently retry forever.

Grey zone: a legitimately long-running batch job needs a higher budget than an interactive chat turn — set the cap per use case and document why, rather than reusing one global constant everywhere.

## RAG (Retrieval-Augmented Generation) isolation

A shared retrieval index queried without a tenant or user filter lets one tenant's agent retrieve another tenant's private documents through an ordinary similarity search — no injection required.

**Detect**: confirm every vector-search/retrieval call includes a tenant or owner filter predicate.

```bash
grep -rnE '\.(similarity_search|query|search)\(' --include="*.py" . | grep -v node_modules
```

Reading: for each hit, confirm the call passes a `filter={"tenant_id": ...}` (or equivalent) argument scoped to the current caller. A retrieval call with no filter argument at all, in a multi-tenant system, is a finding.

**Fix**: enforce the tenant filter at the retrieval layer itself, not only in application code that might forget to pass it, so a missing filter fails the query rather than silently returning cross-tenant results.

```python
# SMELL — no tenant filter; can return another tenant's private documents
results = vector_store.similarity_search(query, k=5)

# CLEAN — tenant filter enforced at the call site
results = vector_store.similarity_search(query, k=5, filter={"tenant_id": caller.tenant_id})
```
