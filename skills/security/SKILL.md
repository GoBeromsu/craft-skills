---
name: security
description: Finds and fixes vulnerabilities in code the user owns across web, API, and LLM surfaces, mapping every trust boundary first and triaging by production reachability and severity second. Use when asked for a security review, "is this safe to ship," "check for vulnerabilities," or "보안 점검," when auditing secrets hygiene or dependency risk, or when reviewing a PR or feature for security regressions before release. Not for building or changing LLM-agent systems themselves (use `agents`) or for installing the enforcement hook, lint, or pre-commit that closes a finding permanently (use `hookify`); this skill finds and fixes, it never attacks.
metadata:
  version: 2.1.0
---

# security

Find and fix vulnerabilities in your own systems under one discipline: **map every trust boundary first, triage by real-world reachability and severity second, fix at the source third.** A review is done when every ingress channel has a parse/validate/limit decision, every finding carries a reachability-and-severity verdict backed by `file:line` evidence, and every applied fix is proven closed by a test or a re-run of the detection command that surfaced it.

## PHASE 0 — trust-boundary mapping (run first, every time)

Do not propose a fix before this gate.

1. Enumerate every ingress channel the feature or codebase under review exposes: user input (forms, query params, headers), webhooks, file uploads, LLM output (tool-call arguments, model completions, retrieved documents), and third-party API responses.
2. Give each ingress point a parse / validate / limit decision — parse it into a typed value at the boundary, validate it against a schema, and cap its size/rate. An ingress point with none of the three is a gap.
3. Name the assets at risk: credentials, personal data, payment data, availability, another tenant's data.
4. Write a one-line abuse case for each top flow — "attacker submits X through channel Y to achieve Z." This turns severity triage into something concrete instead of abstract.
5. Route to the surface-specific or risk-specific reference(s) that apply before acting:
   | Surface or scope | Read |
   |---|---|
   | Web UI / frontend rendering | `references/web.md` |
   | API / server-side handler | `references/api.md` |
   | LLM-powered feature (agent, prompt, retrieval-augmented generation (RAG), tool use) | `references/llm.md` |
   | Full audit, or dependency, build, credential, or supply-chain reachability | `references/secrets-supply-chain.md` |
   A review can route to more than one reference — a web app with an LLM feature reads `web.md`, `api.md`, and `llm.md`. Read `secrets-supply-chain.md` and run its relevant audit commands only when its routing row applies.
Preserve trust-boundary validation and error handling; remove either only when an adversarial regression test proves it redundant.

Quick surface-identification heuristics — approximate, confirm by reading the code, not the grep alone:

```bash
# web rendering surface present
grep -rnE 'dangerouslySetInnerHTML|v-html|\.innerHTML\s*=' \
  --include="*.tsx" --include="*.jsx" --include="*.vue" --include="*.ts" --include="*.js" . \
  | grep -v node_modules | head -5

# server/API surface present
find . -maxdepth 3 \( -iname "*controller*" -o -iname "routes*" -o -iname "*views.py" -o -iname "main.py" \) \
  -not -path "*/node_modules/*"

# LLM feature present
grep -rnE "anthropic|openai|langchain" --include="*.py" --include="*.ts" --include="*.js" . \
  | grep -v node_modules | head -5
```

## Action boundary

| Tier | Actions |
|---|---|
| Review-only request | Read code and configs; run the detection commands that match the routed surfaces; report every finding with `file:line` evidence and the command that surfaced it. Do not apply fixes. |
| Explicit fix request | Fix confirmed vulnerabilities at their source in code the user owns, subject to the Ask first boundary below, and add or update a test or re-run the detection command to prove each fix stays closed. |
| Ask first | Propose the change and apply it only once explicitly accepted: authentication/session/authorization model changes; rotating or revoking a live credential; a major-version dependency bump taken as the fix; modifying a CI/CD security gate; deleting or overwriting data discovered during the audit; disclosing a finding to anyone outside the immediate team. |
| Never do | Write or run exploit code beyond the minimal local proof needed to confirm a fix works; probe, access, or scan any system, account, or endpoint outside what the user explicitly owns or authorized; paste, log, or otherwise expose a real secret found during the audit — redact it in every report; leave a known exploitable path live "to see if it gets hit." |

## Severity triage

Every finding runs through this tree before it gets a fix-now / next-release / backlog verdict:

```
Is the flaw reachable by an unauthenticated or low-privilege actor in production?
├─ NO (needs prod-admin access, or the actor is already at the target's privilege level)
│    → BACKLOG — harden opportunistically, no release blocked.
└─ YES
     ├─ Severity: auth bypass, remote code execution, data loss, secret exposure, cross-tenant leak
     │    ├─ Fix is a patch/config/one-line change → FIX NOW.
     │    └─ Fix needs design or migration work → FIX NOW anyway: ship a mitigation today
     │         (disable the route, rotate the secret, add a gateway rule); track the real
     │         fix as the next release's first item, not a backlog entry.
     ├─ Severity: single-tenant or precondition-gated (needs a specific role, a narrow input
     │   shape, or denial of a non-critical feature)
     │    ├─ Fix available now → NEXT RELEASE.
     │    └─ Fix needs design work → BACKLOG, with a named owner and a date.
     └─ Severity: cosmetic / defense-in-depth (missing security header, verbose error
         message, minor non-sensitive info leak)
          → BACKLOG.
```

Reachability, not a demonstrated exploit, drives the tree — a finding with clear production reachability and real severity is fix-now even with no working proof-of-concept; demanding one before triaging is itself a red flag (see below).

## Hand-offs

- Building or changing an LLM-agent system itself — a new agent, prompt authoring, eval sets — is owned by `agents`; this skill finds and fixes vulnerabilities in what's already built, including prompt injection, tool-permission scope, and consumption guards in agent/LLM code (`references/llm.md`).
- Turning a finding into enforced prevention — a pre-commit hook, a CI lint gate, a runtime guard — is owned by `hookify`.
- The parse-don't-validate typed-boundary idiom referenced in PHASE 0 step 2 is owned by `programming`; this skill states the security requirement, `programming` owns the implementation pattern.
- Offensive tooling, exploit development, penetration-testing infrastructure, and probing systems the user does not own or hold written authorization to test are out of scope entirely — this skill finds and fixes, it never attacks.

## Requirements

- POSIX `grep`, `find`, `awk` for the detection commands in every reference file.
- `git` for tracked-file and history secret scans.
- `npm audit` / `pnpm audit` (Node) or `pip-audit` / the uv-native audit command (Python/uv) when the dependency/build/credential/supply-chain routing row applies — see `references/secrets-supply-chain.md` for the exact commands.
- Optional: `ast-grep` for structural matches where a plain regex produces too many false positives — an optional extra, not a substitute for the commands shipped in the references.

## Anti-patterns

- Skipping trust-boundary mapping because "it's an internal tool, nobody external can reach it" → map every ingress channel regardless of network position; VPN misconfigurations, compromised laptops, and partner integrations all expose "internal" tools.
- Deferring a fix-now finding with "we'll fix it after launch" → ship a mitigation immediately and track the real fix as the next release's first item; ship dates slip and the flaw goes live with fix-now reachability.
- Trusting "the model would never actually generate that" → validate model output like any other untrusted input; a jailbreak or one poisoned retrieved document is the only precondition needed.
- Skipping input-validation and secrets discipline because "it's just a prototype" → apply the same discipline regardless of label; prototype code and demo credentials both get copy-pasted into production.
- Relying on "nobody will find this endpoint, it's not linked anywhere" → treat every reachable endpoint as discoverable; obscurity fails against scanners, `robots.txt` leaks, and bundled JS inspection.
- Assuming "the framework already handles that by default" without confirming → confirm with the detection command; a config flag left off or a default changed between versions silently reopens the hole.
- Waiting for a proof-of-concept before acting because "there's no working exploit shown, so it's not real yet" → triage on reachability plus severity alone; demanding a PoC first is how known, reachable bugs sit unfixed.
- Letting a user-controlled or model-generated string reach `exec`/`eval`/a shell call/a raw SQL string/an HTML-rendering sink with no parse step in between → add a parse/validate step at the boundary before the value reaches the sink.
- Leaving a secret-shaped string (`AKIA…`, `ghp_…`, `sk-…`, `BEGIN PRIVATE KEY`) in a tracked file or anywhere in `git log -p` → rotate the credential immediately and scrub it from history.
- Tracking a `.env` file in git with no `.env.example` sibling → untrack the `.env` file, add it to `.gitignore`, and commit a `.env.example` template instead.
- Leaving no dependency lockfile committed while the audit command reports unresolved high/critical findings → commit the lockfile and resolve the reported high/critical findings before shipping.
- Implementing authorization as "is authenticated" instead of "is authenticated AND permitted for this specific object" → check both authentication and object-level permission on every access.
- Reporting a finding with the real secret value pasted in instead of redacted → redact every secret value before it appears in a report.
- Leaving a known exploitable path live "to see what happens" instead of mitigating it immediately → mitigate the path immediately (disable the route, rotate the secret, add a gateway rule).

## Verification

- [ ] Every ingress channel for the reviewed feature is enumerated with a parse/validate/limit decision.
- [ ] PHASE 0 routed to every matching reference before any fix was proposed; `references/secrets-supply-chain.md` was read only when its routing row applied.
- [ ] Each finding carries a fix-now / next-release / backlog verdict from the severity tree, with the reachability and severity reasoning stated.
- [ ] Every finding cites `file:line` evidence and the detection command that surfaced it.
- [ ] No real secret value appears anywhere in the report — redacted placeholders only.
- [ ] A dependency audit (`npm audit` / `pip-audit` / the uv-native command in `references/secrets-supply-chain.md`) ran and its output was reviewed when dependency, build, credential, or supply-chain reachability was in scope.
- [ ] Every applied fix is proven closed by a test or a re-run of the same detection command showing a pass.
