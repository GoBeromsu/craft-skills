# Vendor Absorption Protocol

How to absorb a frontier lab's skill-creator (or skill-authoring guide) into this library when a new one ships.
Every lab distills how skills are best made *for its models* into its skill-creator; the labs converge on direction but each illuminates a different part of the craft.
This protocol harvests the universal lessons into core and quarantines the runtime-specific plumbing into a lens — so the library compounds with every release instead of chasing any single vendor.

## 1. Fetch the whole package

Blog posts and READMEs describe intent; the package is the evidence.
Sparse-clone the real thing — `SKILL.md`, scripts, agent prompts, schemas, references — into scratch:

```bash
git clone --depth 1 --filter=blob:none --sparse <upstream-repo-url> <scratch-dir>
cd <scratch-dir> && git sparse-checkout set <path/to/skill-creator>
```

Read the tooling, not just the prose: validators reveal the hard limits a lab actually enforces; scaffolds reveal what it considers a complete package; eval harnesses reveal what it means by quality.

## 2. Inventory the mechanisms

List every distinct mechanism: each principle, process step, script behavior, numeric limit, metadata field, and agent-prompt rubric.
Small things count — a validator's exact character bound or a "run baselines in the same turn" instruction is often where the real opinion lives.

## 3. Classify with the portability test

For each mechanism ask: **would this still be true for a skill running on a runtime this vendor does not control?**

- **Yes → universal craft.** Candidate for core (`contract.md`, `evaluation.md`, `lifecycle.md` — whichever owns the topic, §9 MECE).
- **No → vendor plumbing.** Metadata files only one runtime reads, CLI invocations only one runtime exposes, packaging formats, UI-surface fields. These go in the lens, never core.

When unsure, hold it in the lens; promotion to core is cheap later, and un-polluting core is not.

## 4. Merge universal lessons into core

Fold each universal lesson into the file that owns its topic, compressed to reference voice.
Rules:

- One owner per rule (§9 MECE) — extend the owning section, never restate elsewhere.
- A lesson core already holds in different words is a confirmation, not an addition — leave core as written.
- **Conflicts change core only by deliberate decision.** When upstream contradicts the contract (e.g. a lab forbids per-skill CHANGELOGs where this library mandates them), record the disagreement in the lens with both positions and why the library keeps its choice. Silent import of a conflicting rule is the failure mode this step exists to stop.

## 5. Write or extend the lens

One flat file per vendor: `references/vendor-<name>.md`, shaped as:

1. **Source** — the upstream repo/docs path absorbed, so the next absorption diffs cleanly.
2. **What this lab illuminates** — the distinctive philosophy, in a few tight paragraphs.
3. **Runtime plumbing** — exact fields, commands, limits, packaging needed when targeting that runtime.
4. **Divergences from this library** — the recorded disagreements from step 4.
5. **Absorbed into core** — pointer list of what was taken and where it now lives.

Section 5 makes re-absorption idempotent: when the vendor ships an update, diff the new package against sections 3–5 and only the genuinely new mechanisms need classifying.

## 6. Record and deliver

- `CHANGELOG.md` bullet with a `Provenance:` clause linking the upstream (contract §6).
- Update the skill's row in `skills/PROVENANCE.md`.
- Update `skills-manifest.yaml`: the package `version` and `provenance.absorbed_from`.
- Register the new vendor's repo namespace (e.g. `openai`, `NousResearch`) in `external_repos` of `scripts/governance/fixtures/repos.portable.json` and the cross-repo fixture — the provenance checker blocks any `absorbed_from` entry whose namespace it cannot resolve.
- Bump per contract §8 — an absorption that adds lenses or capabilities is MINOR.
- Re-run the scenario and trigger evals (contract §7): absorbed rules must not shift existing behavior or routing. Then the standard delivery flow (`lifecycle.md` §6).
