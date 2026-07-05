---
name: security
description: '"security review", "보안 점검", "is this safe", "check for vulnerabilities" — defensive security triage across web, API, and LLM surfaces: trust-boundary mapping, vulnerability-class detection commands, severity triage, and secrets/dependency hygiene. Finds and fixes vulnerabilities in code the user owns; does not perform offensive or exploit work.'
version: 1.0.0
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob]
compatibility: claude-code, codex
---

# security

Find and fix vulnerabilities in your own systems under one discipline: **map every trust boundary first, triage by real-world reachability and severity second, fix at the source third.**

## Overview

This skill is an index for defensive security work: locating and closing vulnerabilities in code you own, hardening secrets and dependency hygiene, and triaging findings by actual production risk. Shared judgment — trust-boundary mapping, the action boundary, the severity tree — lives here; the per-surface vulnerability classes and their detection commands live in `references/`. Load the matching reference before proposing a fix.

## When to Use

- A user asks for a security review, "is this safe to ship," or "check for vulnerabilities" — in any phrasing, including "보안 점검."
- Auditing secrets hygiene, dependency risk, or a specific vulnerability class (unsafe rendering, injection, unchecked outbound fetches, prompt injection) in the user's own codebase.
- Reviewing a PR, a new feature, or an existing service for security regressions before release.

**Not for:** offensive tooling, exploit development, penetration-testing infrastructure, or probing systems the user does not own or hold written authorization to test. This skill finds and fixes; it does not attack.

## PHASE 0 — trust-boundary mapping (run first, every time)

Do not propose a fix before this gate.

1. **Enumerate every ingress channel** the feature or codebase under review exposes: user input (forms, query params, headers), webhooks, file uploads, LLM output (tool-call arguments, model completions, retrieved documents), and third-party API responses.
2. **Give each ingress point a parse / validate / limit decision** — parse it into a typed value at the boundary, validate it against a schema, and cap its size/rate. An ingress point with none of the three is a gap.
3. **Name the assets at risk**: credentials, personal data, payment data, availability, another tenant's data.
4. **Write a one-line abuse case for each top flow** — "attacker submits X through channel Y to achieve Z." This is what turns severity triage into something concrete instead of abstract.
5. **Route to the surface-specific reference(s)** and read the matching file in full before acting:

   | Surface | Read |
   |---|---|
   | Web UI / frontend rendering | `references/web.md` |
   | API / server-side handler | `references/api.md` |
   | LLM-powered feature (agent, prompt, retrieval-augmented generation (RAG), tool use) | `references/llm.md` |
   | Secrets, dependencies, CI, install scripts | `references/secrets-supply-chain.md` |

   A single review often routes to more than one reference — a web app with an LLM feature reads `web.md`, `api.md`, and `llm.md`. Every review reads `secrets-supply-chain.md` at least once; it applies regardless of surface.

Quick surface-identification heuristics — approximate, confirm by reading the code, not by the grep alone:

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

## Three-tier action boundary

| Tier | Actions |
|---|---|
| **Always do** | Read code and configs; run detection commands and dependency audits; report every finding with `file:line` evidence and the command that surfaced it; propose and, once accepted, apply source-level fixes; add or update a test that proves a closed vulnerability stays closed. |
| **Ask first** | Rotate or revoke a live credential; change authentication/session/authorization logic; modify a CI/CD security gate; delete or overwrite data discovered during the audit; disclose a finding to anyone outside the immediate team. |
| **Never do** | Write or run exploit code beyond the minimal local proof needed to confirm a fix works; probe, access, or scan any system, account, or endpoint outside what the user explicitly owns or authorized; paste, log, or otherwise expose a real secret found during the audit — redact it in every report; leave a known exploitable path live "to see if it gets hit." |

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

- Turning a finding into enforced prevention — a pre-commit hook, a CI lint gate, a runtime guard — is owned by the `hookify` skill.
- The parse-don't-validate typed-boundary idiom referenced in PHASE 0 step 2 is owned by the `programming` skill; this skill states the security requirement, `programming` owns the implementation pattern.

## Requirements

- POSIX `grep`, `find`, `awk` for the detection commands in every reference file.
- `git` for tracked-file and history secret scans.
- `npm audit` / `pnpm audit` (Node) or `pip-audit` / `uv` (Python) for dependency audits — see `references/secrets-supply-chain.md`.
- Optional: `ast-grep` for structural matches where a plain regex produces too many false positives — an optional extra, not a substitute for the commands shipped in the references.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It's an internal tool, nobody external can reach it." | Internal tools get exposed by a VPN misconfiguration, a compromised laptop, or a partner integration — network position is not a stable trust boundary. |
| "We'll fix it after launch." | Ship dates slip and the flaw goes live with exactly the reachability the severity tree flags as fix-now. Ship a mitigation now; track the real fix, don't defer the whole thing. |
| "The model would never actually generate that." | Model output is untrusted input by definition — a jailbreak or one poisoned retrieved document is the only precondition. Validate the output, never the model's good behavior. |
| "It's just a prototype." | Prototype code and demo credentials both get copy-pasted into production. Apply the same input-validation and secrets discipline regardless of the label. |
| "Nobody will find this endpoint, it's not linked anywhere." | Obscurity fails against scanners, `robots.txt` leaks, and bundled JS inspection. Any endpoint a request can reach, an attacker can eventually find. |
| "The framework already handles that by default." | Confirm with the detection command; a config flag left off, or a default changed between versions, silently reopens the exact hole the framework claims to close. |
| "There's no working exploit shown, so it's not real yet." | Reachability plus severity is sufficient to triage — demanding a proof-of-concept before acting is how known, reachable bugs sit unfixed. |

## Red Flags

- A user-controlled or model-generated string reaching `exec`/`eval`/a shell call/a raw SQL string/an HTML-rendering sink with no parse step in between.
- A secret-shaped string (`AKIA…`, `ghp_…`, `sk-…`, `BEGIN PRIVATE KEY`) present in a tracked file or anywhere in `git log -p`.
- A `.env` file tracked by git with no `.env.example` sibling.
- No dependency lockfile committed while the audit command reports unresolved high/critical findings.
- Authorization implemented as "is authenticated" instead of "is authenticated AND permitted for this specific object."
- A finding reported with the real secret value pasted in instead of redacted.
- A known exploitable path left live "to see what happens" instead of mitigated immediately.

## Verification

- [ ] Every ingress channel for the reviewed feature is enumerated with a parse/validate/limit decision.
- [ ] PHASE 0 routed to every matching reference before any fix was proposed.
- [ ] Each finding carries a fix-now / next-release / backlog verdict from the severity tree, with the reachability and severity reasoning stated.
- [ ] Every finding cites `file:line` evidence and the detection command that surfaced it.
- [ ] No real secret value appears anywhere in the report — redacted placeholders only.
- [ ] A dependency audit (`npm audit` / `pip-audit` / `uv`) has been run and its output reviewed.
- [ ] Every applied fix is proven closed by a test or a re-run of the same detection command showing a pass.
