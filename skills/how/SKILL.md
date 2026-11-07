---
name: how
description: "Explains how a system or process works by tracing entry points, data flow, boundaries, and ownership in real source evidence. Use for \"how does X work\", \"walk me through this code\", \"where should this live\", \"which package owns this\", or onboarding to a subsystem before changing it. Scales exploration to the question and reports untraced gaps. Not for historical motivation - use why; not for paced coaching combining both - use teach."
metadata:
  version: 1.0.2
---

# How

Explore the codebase to answer "how does X work?" questions. Produce architectural explanations at the level of a senior engineer onboarding onto a subsystem, enough to build a working mental model, not so much that it reads like annotated source code.

Every spawn is a read-only general-purpose subagent. Explorers use the fastest, cheapest setting that still reads and reports accurately, because that role runs many times over broad material. Every explainer uses the most capable setting available, because that role runs once and weighs evidence. Pick each subagent's reasoning level and fast or standard speed for the job, per the Subagents section of the **craft-mode** skill.

## 1. Assess complexity

If the scope is ambiguous, state your interpretation and explore. The user can redirect.

- **Simple** (a single module, a small utility, a narrow question such as "how does function X work"): no explorers. Spawn one explainer that explores and explains in one pass, built from `references/explainer-prompt.md` without the explorer-findings section. Go to step 4.
- **Complex** (a subsystem spanning multiple files or services, a cross-cutting feature, a full architectural overview): go to step 2.

When in doubt, take the simple path.

## 2. Explore (complex only)

Decompose the question into 2 to 4 angles, each a distinct slice of the subsystem. Spawn all explorers in a single message, each with `references/explorer-prompt.md` and its angle filled in.

## 3. Synthesize (complex only)

Once all explorers have returned, spawn one explainer with `references/explainer-prompt.md` and every explorer's findings filled in.

## 4. Present

Present the explainer's output. Light edits for clarity or context from the conversation are fine. Do not substantially rewrite it.

## Output format

The explanation uses the sections defined in `references/explainer-prompt.md`, dropping any that do not apply: Overview, Key Concepts, How It Works, Where Things Live, Gotchas.
