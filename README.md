# craft-skills

Work-craft Agent Skills for research and engineering by Beomsu Koh.

![License: MIT](https://img.shields.io/badge/license-MIT-green) [![Release](https://img.shields.io/github/v/release/GoBeromsu/craft-skills)](https://github.com/GoBeromsu/craft-skills/releases/latest)

Own your craft, vendor-neutral: all 49 packages use the plain Agent Skills `SKILL.md` layout.
The portable core contains no runtime-specific behavior; Claude Code, Codex, Hermes, Cursor, and Grok-native integration lives in runtime lenses and generated instruction-file adapters.
This is a task-oriented library for software and research work — kept separate from [`bstack`](https://github.com/GoBeromsu/bstack) (personal / life / second-brain automation) so the two domains never bleed into each other's context.

---

## Features

### Skills

| Skill | Purpose |
|-------|---------|
| `api` | Defines and evolves public HTTP API contracts while preserving published incumbent behavior. Use when asked to design the public REST contract for a resource, document an endpoint contract, choose API pagination or error shapes, standardize a greenfield REST API, or API 계약을 설계할 때. Not for service structure or persistence — use principle-backend; client rendering or state — use principle-frontend; or transport-level test design — use principle-testing. |
| `architect` | Sketches types, signatures, caller usage, and module boundaries before implementation and stays in the loop while code fills in the chosen shape. Use for "/architect", "architect this", "design this", or non-trivial work where jumping to code would lock in the wrong structure. Grounds through how and why, explores alternatives through arena, and applies principle-architecture. Not for explaining existing architecture alone - use how; not for behavior-preserving cleanup - use refactor. |
| `arena` | Runs N candidates at the same task, picks a base, and grafts the strongest parts into one verified artifact. It applies to '/arena', 'arena this', 'throw it in the arena', and design choices where one attempt could lock in the wrong shape. It fans out parallel subagents across model families and has a judge from another family cross-check the pick. Not for partitioning independent work slices - use swarm. |
| `automate-me` | Drafts or updates one personal <handle>-mode skill from the user's working conventions, mined from the active workspace's recent transcripts and asked directly, and runs unslop on its prose. It applies to 'automate me', 'update my mode skill', 'capture my preferences', and 'work in my style'. It updates existing skills in place. Not for reconstructing the current state of past work - use recall. |
| `benchmark-checklist` | Vets performance measurements for the limiter, tuning, physical limits, errors, repeatability, relevance, and proof that timed work happened. It applies to 'check this benchmark', 'report this speedup', measured regressions, and choosing a library or configuration from numbers. It reports spread and gaps before drawing a conclusion. Not for general testing policy or choosing test oracles - use principle-testing. |
| `benny` | Triages an issue report from a pasted message, GitHub or Linear issue, chat thread, or text; dedupes against the tracker and decides whether to file. For confirmed bugs or performance issues, it reproduces the symptom, verifies an existing fix or makes a bounded fix with before/after proof. Use for "triage this issue", "benny", or "reproduce and fix this bug report". Not for a bug already reproduced - use the bug-fix playbook in craft-mode. |
| `issue-triage` | Refines existing issues in one repository with evidence-linked R1–R5 verdicts: duplicates, fixed bugs, repro routing, existing features, and vertical splits. Not for reproduction or fixes — use benny; vague requests — use deep-interview or write-prd. |
| `blast-radius` | Finds what a change could break beyond the diff and proves the safety fact by running real code. It applies to 'blast radius of X', 'what could this break', and small diffs whose callers or wire formats hide risk. It returns evidenced risks, cleared cases, and a proof or an explicit unproven fact. Not for explaining existing behavior alone - use how or why. |
| `bro` | Restates the assistant's last message in plain human language without jargon, keeping its meaning while making it shorter and easier to understand. Use for "/bro", "say that simply", "drop the jargon", "what are you actually saying", or "explain your last message like a human". Applies only to this explicit restatement, not as a global style override. Not for teaching a subsystem with new evidence - use teach; not for a general prose editing pass - use unslop. |
| `browser` | Owns personal composition for live authenticated browser work through Aside as the sole managed route. Use when a request says "Use Aside to inspect my logged-in dashboard", "inspect my signed-in dashboard", "open this in my browser", "click this button", "fill out this form", "continue this Aside session", or "브라우저로 열어줘" and the page needs login, JavaScript, or multi-step interaction. Not for static public extraction — use a standalone extractor — or plain JSON API responses — use an HTTP client. Not for rewriting official Aside product usage. |
| `cicd` | Designs CI/CD changes that preserve the repository's delivery topology and make releases observable and reversible. Use when asked to set up the PR pipeline and deployment for this repo, configure CI/CD, add a deployment pipeline, define required CI checks, design release rollback, or 배포 파이프라인을 설계할 때. Not for service architecture or persistence — use principle-backend; test-suite design — use principle-testing; or commit and PR mechanics — use git. |
| `correct` | Finds repeated mistake classes and changes the repository so agents cannot repeat them. Use for "/correct", "agents keep leaving debug prints", "make this correction stick", or recurring review fixes with two or more observed incidents. Chooses architecture, types, lint/CI, tests, then docs and proves enforcement rejects a real past error. Not for reflecting on session learnings - use reflect; not for diagnosing a single failure - use debug. |
| `craft-help` | Guides users through craft-skills setup, craft-mode, and picking the skill, playbook, or principle for a task, then hands back a prompt they can send and the file the answer came from. Use for "craft-help", "which skill should I use", "how do I use craft-mode", "which playbook fits this", "how do I install craft-skills", or "my craft-mode run went wrong". Answers the question without starting the work. Not for doing the work - use craft-mode. |
| `craft-mode` | Routes multi-step engineering work through a chosen playbook, situational workflows, and domain-owned principles. Use for craft-mode, a rigorous feature or bug fix, a migration, a measured performance problem, or work that needs a clear finish condition and evidence. Keeps replies concise, applies unslop to prose, and delegates to background subagents by default. A named procedure such as how, why, correct, or tdd can run directly; domain policy stays with its principle owner. |
| `db` | Diagnoses database workloads and anti-patterns and makes evidence-backed schema and operating decisions after persistence selection. Use when a slow query needs EXPLAIN review, bulk DML or an online schema change needs a safe plan, keys, FKs, JSON, indexes, partitioning, pooling, replication, cache, or storage tradeoffs need assessment, or asked “DB 병목 원인과 설계 대안을 검토해줘.” Not for engine, provider, ORM, version, roles, destructive target, persistence implementation, or schema retirement—use principle-backend; generic bugs—use debug; public API contracts—use api; typed SQL or code—use principle-programming; injection or authorization—use security; fixtures or test taxonomy—use principle-testing. |
| `debug` | Diagnoses a failing program under a hypothesis-driven loop: reproduce the failure before theorizing, log observed facts separately from inferences, hold competing hypotheses until the cheapest probe discriminates between them, and confirm the mechanism with instrumentation before any fix lands. Use when a test or command fails for an unclear reason, a bug needs bisecting to the commit or input that caused it, a failure only reproduces intermittently, or asked to find out why something is broken ("이거 왜 안 되는지 찾아줘"). Not for restructuring working code (use refactor), suite-level test architecture (use principle-testing), or triaging a vulnerability class (use security). |
| `design` | Owns canonical DESIGN.md artifacts and evidence-first UX/UI judgment for coherent product design roots. Use when requests ask to define interface direction; choose type, color, spacing, or motion; audit a user journey; establish design tokens or state specifications; redesign information hierarchy; review mental models; evaluate rendered states; prioritize bad UX; improve an interaction; turn accessibility and usability findings into an improvement plan; or 디자인 점검해줘. Not for frontend rendering or architecture, product copy, or generic documentation — use principle-frontend, the product or copywriting owner, or document; live-page operation and automated evidence collection remain mechanics-owned. |
| `distil` | Distils transferable rules and conventions from an external source — a well-crafted repo, an engineering article, an AGENTS.md, or a third-party skill — and lands them in the owning package with provenance recorded. Use when the user says "파쿠리", "distil the rules from this repo", "absorb this skill", or "pull the conventions out of this article", or hands over a link worth mining. Not for authoring a skill from your own workflow or shipping the final package; not for open-ended investigation of a question — use research; not for summarizing a source with no intent to land rules in the library. |
| `document` | Scaffolds and authors repository documentation through a six-type ontology and canonical artifacts. Use when asked to scaffold repository docs, "record this decision", "where does this spec go", "draft the project CHANGELOG", or "comment-the-why". Not for READMEs (use readme), conducting research (use research), technical reports (use write-report), API-surface comments, or DESIGN.md, visual direction, UX audits, and design-system work (use design). |
| `figure-it-out` | Designs an auditable playbook when no narrower workflow fits a large migration, multi-part change, or unattended run. It applies to '/figure-it-out', 'figure it out', and work a human reviews after stepping away. It scales rigor, tests hypotheses against real artifacts, and records decisions through show-me-your-work. Not for choosing among several candidates for one settled brief - use arena. |
| `git` | Guides version-control craft: a ground-truth and incumbent-style detection gate before the first git mutation, the atomic-commit `git add -p` split protocol, commit/branch/PR conventions matched to the repo's own history, and non-interactive-safe history surgery (fixup, reword, split, scripted bisect, undo). Use when committing a change ("commit this", "커밋해줘"), rebasing or squashing history, sizing a PR, recovering from a broken rebase, or running "git wt" to create an isolated worktree with the git-guard rails. Not for general runtime-hook or linter configuration; preserve the target repository's enforcement tooling. |
| `gpu` | Applies GPU environment and resource discipline — probe the hardware before choosing any install, budget the host before launching any job — to CUDA/PyTorch setup, attention-backend builds, and GPU job launches. Use when setting up CUDA or PyTorch on a new GPU machine, asked to "install flash attention", debugging "torch.cuda.is_available() returns False", "CUDA out of memory", or "no kernel image is available", sizing VRAM, running a training/inference job on a shared GPU host or HPC, or working on Apple Silicon (MPS, M-series). Not for training methodology, datasets, or evaluation discipline — use `ml` — and not for serving a model behind an API — use `principle-backend`. |
| `how` | Explains how a system or process works by tracing entry points, data flow, boundaries, and ownership in real source evidence. Use for "how does X work", "walk me through this code", "where should this live", "which package owns this", or onboarding to a subsystem before changing it. Scales exploration to the question and reports untraced gaps. Not for historical motivation - use why; not for paced coaching combining both - use teach. |
| `init` | Maps a repository into a maintained hierarchical AGENTS.md knowledge base. Use when asked to "init this repo" for AGENTS, deep-init a codebase, generate or update AGENTS.md, map repository conventions, audit existing AGENTS coverage, or report stale managed AGENTS regions. Not for package-manager or plugin initialization, docs scaffolding or authoring (use `document`), or git-hook installation (use `git`). |
| `interrogate` | Synthesizes an adversarial verdict from independent reviewers available in the runtime without assigning fixed models. It applies to 'interrogate', 'adversarial review', 'challenge this', 'stress test this code', 'find blind spots', and 'tear this apart'. It separates actionable findings from tradeoffs and rejected claims without applying fixes. Not for proving one change's downstream safety fact - use blast-radius. |
| `make-bot-ui` | Builds a small web page whose buttons wake an agent over a webhook: a local server keeps the sender key server-side and POSTs JSON to a webhook-triggered routine, and the page is exposed on the existing Tailscale node. Use for "make a bot UI", "a dashboard with buttons that trigger the agent", "wake the bot from a page", handing a webhook sender key to the server without pasting it in chat, or putting that UI on the tailnet. Not for general frontend work - use principle-frontend; not for tailnet health or reachability - use tailscale. |
| `ml` | Applies ML/DL research engineering discipline — reproducible project layout, leakage-safe dataset construction, and a training-discipline ladder — to classical ML, deep learning, fine-tuning, and vision work. Use when scaffolding a new ML project, asked to "build a dataset" or "데이터셋 구축", running or reviewing a "train a model" experiment, or building a "vision model" pipeline (augmentation, detection, segmentation). Not for per-file Python discipline (typing, TDD loop) — use `principle-programming`. Agent behavior (prompts, tools, agent evals) is outside this package. GPU/CUDA environment setup or shared-host job launch belongs to `gpu`. |
| `orca` | Organizes Orca around low-clutter project identities and preserves running work while diagnosing which local connection layer still needs evidence. Use to "organize Orca", "reduce sidebar clutter", consolidate the "same repo across hosts", clean old branches in Orca, reuse or account for task terminals, resolve selector_not_found or remote_runtime_unavailable, investigate SSH failures to an Orca host, or handle "orca에 연결이 안된다". Not for standalone Git maintenance (use git), vault taxonomy (use obsidian and local policy), network-versus-SSH reachability triage (use tailscale), or executable command mechanics (use the installed orca-cli and orchestration guides). |
| `principle-architecture` | Guides cross-domain structural decisions before implementation. Use when choosing core data structures, integrating a requirement into an existing design, comparing architectures without precedent, planning a rewrite, retiring internal APIs, or isolating concurrent writers to a file or branch. Service structure and persistence belong to principle-backend, published HTTP contracts to api, and rendered UX to design. The architect workflow owns design sketches and implementation coordination; this skill supplies the structural principles it applies. |
| `principle-backend` | Routes backend service architecture and persistence selection, including engine, provider, ORM, production major, roles, destructive-target proof, persistence implementation, schema-ledger retirement, and folder conventions. Use when building a service layer, choosing a persistence stack, adding a repository or use case, setting up production-fidelity local database development, retiring a migration ledger, or reviewing architecture drift (e.g. "백엔드 구조 잡아줘"). After selection, use db for database workload diagnosis, schema/access-path tradeoffs, and operations/configuration. Not for public HTTP API contracts—use api; UI rendering—use principle-frontend. |
| `principle-frontend` | Routes frontend engineering through rendering, ownership, reuse, state, CSS, and performance decisions. Use when building or reorganizing a React/Vue/Svelte UI ("프론트엔드 구조 잡아줘"); choosing a React + Vite or Next.js shell, folder/public-API, or server/client boundary; improving component reuse or state ownership; selecting CSS Modules/Tailwind/CSS-in-JS and token structure; or setting dependency, bundle, and CSS performance strategy. Not for material visual/UX judgment or DESIGN.md — use design; public API/server contracts — use api/principle-backend; TypeScript-only work — use principle-programming/refactor; test suites — use principle-testing. |
| `principle-programming` | Guides correctness-first, type-strict Python and TypeScript implementation. Use when asked to write a `.py` or `.ts` file, scaffold a Python/TypeScript project, add strict types, assess an implementation diff for correctness or type holes, or fix a reproducible defect. Not for smell-only assessment or behavior-preserving restructuring — use refactor; not for suite-level test architecture — use principle-testing. |
| `principle-testing` | Designs, improves, and audits test suites around behavior and risk, independent oracles, counterfactual evidence, deterministic diagnosis, and cost. Use for generated-test review, unit/component/integration/e2e or smoke placement, test-suite health, flaky-test policy, fixtures, and test audits. Not for production-code red-green implementation, which belongs to principle-programming; diagnosis or repair of one currently failing or intermittent test, which belongs to debug; structural-change characterization, which belongs to refactor; ML evaluation methodology, which belongs to ml; or project-specific agent evaluation methodology. |
| `recall` | Reconstructs recent working context from the active workspace's chat history, scoped shared records, and live state. It applies to 'recall my work on X', 'catch me up', 'what have I been working on', and 'where did I leave off'. It returns a cited current-state brief and reads another project's transcripts only when asked. Not for turning working habits into a personal skill - use automate-me. |
| `readme` | Authors or overhauls a repository README as a showcase front page with a hero, tagline, language switch, accurate badges, navigation, previews, features, quick start, and collapsed depth, checks every claim against the repository, and fills the community files it links. Use when asked to "write the README", "update the README", "make the README beautiful", "redesign our README like this repo", "add a license and code of conduct", or "README 예쁘게 작성해줘". Not for docs ontology, ADRs, changelogs, or architecture maps (use document), prose cleanup alone (use unslop), or design systems (use design). |
| `refactor` | Restructures code without changing what it does — extracting functions, renaming, removing duplication, flattening nested conditionals, and other mechanical moves backed by a detection command and threshold. Use when the user says "refactor this", "clean up this code", "리팩토링 해줘", or "this function is a mess", or a named smell (long function, deep nesting, feature envy) surfaces while reading code with no intended behavior change. Gates untested legacy code behind a characterization-test protocol first. Not for diagnosing why something is broken — use debug — or for behavior-changing feature work and bug fixes, which belong to principle-programming's red-green-refactor loop. |
| `reflect` | Reviews durable learnings from the current session through judgment, tooling, and divergent lenses, then routes each accepted learning to an edit on an existing skill. Use for "reflect", "/reflect", "what did this session teach us", or "capture the workflow lessons from this conversation". Reads a current-session source only when the runtime exposes it and presents edits for approval. Not for enforcing repeated repository mistakes - use correct; not for recovering older sessions - use recall. |
| `research` | Researches an open question by reframing it first: rewrites the ask as one problem statement, defines its terms, and splits it into sub-questions tied to established topics, then sweeps trustworthy primary sources, verifies claims by risk, and replies with cited findings, options side by side, and how to check them. Use for "research this before we decide", "what does the evidence say", "compare these options", "dig into whether this is feasible", "조사해줘", or "근거 찾아서 파고들어 봐". Not for making the call; not for how code works - use how; why it has this shape - use why; adversarial review - use interrogate; filing a doc - use document. |
| `security` | Finds and fixes vulnerabilities in code the user owns across web, API, and LLM surfaces, and owns confidentiality for authorized remote credential handoffs. Use for a security review, "is this safe to ship," "check for vulnerabilities," "보안 점검," secrets hygiene, dependency risk, PR security regressions, or "hand a secret to a remote agent." Not for building LLM-agent systems, Orca session operation (use official `orca-cli`), or general hook and gate configuration; this skill never attacks. |
| `show-me-your-work` | Keeps a reviewable TSV decision trail for long-running, autonomous, or multi-phase work, with evidence pointers and outcomes. It applies to '/show-me-your-work', 'keep a decision log', and work a human reviews after stepping away. It audits each run's rows and keeps the file local unless a reviewer needs the trail committed. Not for designing the workflow that produces the decisions - use figure-it-out. |
| `swarm` | Coordinates bounded workers across independent slices or declared races, drains their results, and returns one evidence-backed report. It applies to '/swarm', 'swarm this', parallel coverage, gauntlets, and exploration. It respawns a worker once when its result misses the brief and records a second miss as a gap, never a pass. Not for synthesizing competing candidate artifacts by grafting them - use arena. |
| `tailscale` | Verifies and repairs the Tailscale tailnet that carries cross-host work — SSH, remote process inspection, `scp` — before a dependent workflow runs, and triages failures as network-layer versus service-layer. Use when `tailscale ping` or `ssh <peer>` hangs, when a reachable peer is missing from `tailscale status`, when switching networks between tailnets with `tailscale switch` or listing stored profiles, when the target is a shared-in node or a tailnet you were invited to rather than own, when picking the daemon-restart path for a macOS install variant, or when a browser OAuth popup appears mid-SSH. Not for generic SSH problems unrelated to the tailnet. |
| `tdd` | Executes a focused red-to-green bug fix when the user asks for "TDD", "write a failing test first", "add a regression test", or the defect has an obvious cheap local test target. Writes and runs the regression check for the intended failure before editing production code, then makes the minimum fix and reruns it. Uses the closest executable check instead when a new test would be impractical. Not for suite design - use principle-testing; not for an unclear failure - use debug. |
| `teach` | Teaches a body of work in plain language at the person's pace by composing how and why into one account of what it is, how it works, and why it has that shape. Use for "teach me this", "help me really understand X", or "explain this change or subsystem to me" when understanding, not editing, is the goal. Preserves evidence confidence while adding concrete examples and progressive diagrams. Not for mechanics alone - use how; not for causal investigation alone - use why. |
| `unslop` | Removes AI writing patterns while preserving meaning and the intended tone. It applies to all prose the agent writes, including replies, docs, READMEs, PR descriptions, and commit messages, and to 'remove AI tells', 'rewrite this plainly', or 'unslop this'. It keeps stable numbered rule ids for callers. Code and fixed machine formats are excluded. Not for cleaning up code - use refactor. |
| `why` | Investigates why code or a decision has its current shape through available source history, tickets, documents, chat, telemetry, error records, and analytics. Use for "why does X work this way", "why did we pick Y", design rationale, postmortems, regressions, or "where did this threshold come from". Returns cited findings, calibrated inferences, competing explanations, and source gaps. Not for runtime mechanics - use how; not for repairing a failure - use debug. |
| `write-prd` | Authors product requirements documents by filling a provided or packaged PRD template from product context, with One Pager, scope, metrics, rollout, open issues, and history kept coherent. Use when asked to "write a PRD", "fill this PRD template", "turn this product idea into a PRD", "complete the product requirements document", or "PRD 작성해줘". Not for READMEs (use `readme`), ADRs, changelogs, or docs-ontology artifacts (use `document`), or one-off technical reports (use `write-report`). |
| `write-report` | Scaffolds and authors a project's one-off canonical technical report against a single YAML frame (technical-report.yaml) whose depth is the enforced table of contents — section, then heading, then required must-content. Use when asked to "scaffold a technical report" or "기술 보고서", when writing or restructuring a report section against that frame, or when checking a section's structure and pinned sources for "TOC enforcement" against its source manifest. Not for READMEs (use `readme`), ongoing project documentation, ADRs, or changelogs (use `document`) — write-report owns exactly one canonical, one-off deliverable per project. |

---

## Installation

### Install and discovery

| Runtime | Vendor-native install or documented discovery path |
|---|---|
| Claude Code | Marketplace package |
| Codex | Plugin marketplace package; plain Agent Skills clone is auxiliary development context |
| Hermes | Portable Agent Plugin; packages load as `<namespace>:<name>` |
| GJC (Gajae-Code) | Marketplace plugin; packages load from the installed plugin as `craft-skills:<name>` |
| Cursor | Project or user skills in `.cursor/skills`; plain Agent Skills discovery also supports `.agents/skills` |
| Grok-native | Skills in `.grok/skills` or a configured plugin path |
| Plain Agent Skills | One `SKILL.md` directory per skill under `.agents/skills` |

#### Claude Code — marketplace

Use the Claude Code marketplace channel:

```text
/plugin marketplace add GoBeromsu/craft-skills
/plugin install craft-skills@craft-skills
```

Then invoke a skill above by name, such as `craft-mode`, `correct`, `how`, `tdd`, or `principle-backend`.

---

#### Codex — plugin or plain Agent Skills

The observed Codex plugin marketplace channel is:

```bash
codex plugin marketplace add GoBeromsu/craft-skills
codex plugin add craft-skills@craft-skills --json
```

Marketplace package metadata is tracked in `.codex-plugin/plugin.json`.

For plain Agent Skills development context, clone into a project-root `.agents/skills` directory:

```bash
git clone https://github.com/GoBeromsu/craft-skills.git .agents/skills/craft-skills
```

The clone is optional development context; its skills have the nested layout `.agents/skills/craft-skills/skills/<name>/SKILL.md`.

---

#### Hermes — portable plugin

Install the repository as one portable Agent Plugin (root `plugin.json`) and let Hermes keep it current:

```bash
hermes plugins install GoBeromsu/craft-skills --enable
hermes config set plugins.auto_apply true   # apply git-plugin updates unattended
```

---

#### GJC — marketplace plugin

Register the marketplace once, then install the plugin:

```bash
gjc plugin marketplace add GoBeromsu/craft-skills
gjc plugin install craft-skills@craft-skills
```

GJC scans the installed plugin directly and advertises every package as `craft-skills:<name>`,
so `/skill:craft-skills:git` works with no further configuration.
Refresh the marketplace snapshot before upgrading, or the upgrade stops at the version the snapshot last saw:

```bash
gjc plugin marketplace update craft-skills
gjc plugin upgrade craft-skills@craft-skills
```

`craft-mode` compares its loaded version with `main` as its first step and follows the newer body for the task, but leaves the upgrade to you.

The installed plugin is the only copy; a manual copy alongside it outranks the plugin and freezes.

---

#### Cursor — documented skills directories

Cursor discovers project skills in `.cursor/skills/<name>/SKILL.md`; its Agent Skills compatibility also recognizes `.agents/skills/<name>/SKILL.md`.
Copy or link the individual plain skill directories there using the deployment mechanism appropriate for the project.
No Cursor plugin manifest or CLI command is provided by this repository.

#### Grok-native — documented skills or plugin configuration

Grok-native discovers plain skills at `.grok/skills/<name>/SKILL.md`, or through its configured plugin path.
Use the vendor's configured plugin mechanism for the latter; this repository does not invent a Grok plugin manifest or command.

#### Plain Agent Skills layout

Each package is a self-contained `skills/<name>/SKILL.md`.
For a generic Agent Skills runtime, place the desired package directory at `.agents/skills/<name>/SKILL.md`.
The portable core is the same file used by every runtime; lenses hold runtime-specific guidance.

#### Operational deployment verification

For the approved `m1-pro` deployment, verify the discovered skill directories and runtime behavior only through the approved Tailscale/Orca SSH route.
This is operational verification guidance, not a vendor install command.

---

## Usage

### Craft mode and principle owners

Invoke `craft-mode` for multi-step engineering work. It selects a playbook, composes situational workflows, reads the triggered principles, and reports each applied principle with the decision it changed. Procedures such as `how`, `why`, `correct`, and `tdd` can also run directly.

The `principle-*` packages own broad policy: architecture for cross-domain structure, backend for service structure and persistence, frontend for UI implementation, programming for Python and TypeScript, and testing for test suites and evidence. Narrow principles are reference files under these owners or their existing domain owner, not separate commands.

Steer an active task by naming a principle, for example "apply prove it works" or "apply subtract before you add". The agent reads that principle and changes the relevant decision. See the craft-mode [source catalog](skills/craft-mode/references/catalog.md) for destinations and runtime boundaries.

After installation, skills are discovered by each runtime from their `SKILL.md` packages (GJC exposes them as `craft-skills:<name>`).

`unslop` already runs inside `craft-mode` and as the final prose pass of the writing skills. To make it always-on for everything your agent writes, add this line to your agent's global instructions (for example, your user-level `AGENTS.md` or `CLAUDE.md`); this repository never edits that file for you:

```text
Apply the unslop skill to all prose you write, including replies, docs, PR descriptions, and commit messages; leave code and fixed machine formats unchanged.
```

---

## Development

Each skill lives in `skills/<name>/SKILL.md`. Each package owns its own recipe; repository conventions live in `AGENTS.md`.

### Validation

`scripts/ci-local.sh` mirrors every required CI gate locally (pr-size, both Layer-1 validators, distribution-version, marketplace validation) and is the merge gate whenever GitHub Actions cannot run:

```bash
bash scripts/ci-local.sh
```

Enable the tracked git hooks once per clone — pre-commit runs the fast Layer-1 pair, pre-push runs the full mirror:

```bash
git config core.hooksPath .githooks
```

`SKIP_LOCAL_CI=1` bypasses a hook once; `SKIP_MARKETPLACES=1` skips the claude/codex CLI job.
Individual checks can still be run directly (`claude plugin validate .`, `python3 scripts/governance/tools/validate_skill_format.py`, `python3 scripts/governance/tools/validate_runtime_hygiene.py`).

Codex reads the tracked plugin tree directly.

## License

Third-party credits and the pstack MIT notice are in [ACKNOWLEDGEMENTS.md](ACKNOWLEDGEMENTS.md).

MIT, as declared in `.claude-plugin/plugin.json`. No `LICENSE` file is present in this repository yet.
