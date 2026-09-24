# Vendor Absorption Protocol

How to learn from a frontier lab's skill-creator or skill-authoring guide when a new one ships.
Every lab distills how skills are best made *for its models* into its skill-creator; the labs converge on direction but each illuminates a different part of the craft.
This protocol harvests portable lessons into core and records runtime-specific plumbing in a lens.
It is comparison and local-gap extraction, not re-hosting upstream product commands, scripts, or evaluator harnesses as a local SSOT.
Official vendor skills stay unmodified on their official distribution and update channels.

## 1. Fetch the whole package

Blog posts and READMEs describe intent; the package is the evidence.
Sparse-clone the real thing into scratch — do not copy it into this library as the product-usage original:

```bash
git clone --depth 1 --filter=blob:none --sparse <upstream-repo-url> <scratch-dir>
cd <scratch-dir> && git sparse-checkout set <path/to/skill-creator>
```

Read the tooling, not just the prose: validators reveal the hard limits a lab actually enforces; scaffolds reveal what it considers a complete package; eval harnesses reveal what that vendor means by quality on its own runtime.
Apply [contract §10](contract.md#10-external-facts-and-dependencies) to related official skills and CLIs on the working host before treating versions as current.
Check-only detection is incomplete.

## 2. Inventory the mechanisms

List every distinct mechanism: each principle, process step, script behavior, numeric limit, metadata field, and agent-prompt rubric.
Small things count — a validator's exact character bound or a "run baselines in the same turn" instruction is often where the real opinion lives.
Label each item as native compatibility, upstream recommendation, or local repository policy.

## 3. Classify with the portability test

For each mechanism ask: **would this still be true for a skill running on a runtime this vendor does not control?**

A runner's example count, generated-eval requirement, or prompting recommendation is not automatically a universal admission requirement.
Distinguish model/API guidance from that vendor's skill loader, plugin packaging, permission semantics, and evaluator harness.

- **Yes → universal craft.** Candidate for core (`contract.md`, `evaluation.md`, `lifecycle.md` — whichever owns the topic, §9 MECE).
- **No → vendor plumbing.** Metadata files only one runtime reads, CLI invocations only one runtime exposes, packaging formats, UI-surface fields, and vendor evaluator machinery. These go in the lens as links and boundaries, never as copied product instructions or a local harness SSOT.

When unsure, hold it in the lens; promotion to core is cheap later, and un-polluting core is not.
Do not import wording-locked corpora, generated run outputs, or a checker-of-checker as this library's pass condition.

## 4. Merge universal lessons into core

Fold each universal lesson into the file that owns its topic, compressed to reference voice.
Rules:

- One owner per rule (§9 MECE) — extend the owning section, never restate elsewhere.
- A lesson core already holds in different words is a confirmation, not an addition — leave core as written.
- **Conflicts change core only by deliberate decision.** When upstream contradicts the contract (e.g. a lab forbids per-skill CHANGELOGs where this library mandates them), record the disagreement in the lens with both positions and why the library keeps its choice. Silent import of a conflicting rule is the failure mode this step exists to stop.
- Official product-usage text stays upstream. Local files record uncovered context, boundaries, and source links.

## 5. Write or extend the lens

One flat file per vendor: `references/vendor-<name>.md`, shaped as:

1. **Source** — the official repo/docs path consulted, so the next absorption diffs cleanly. Prefer current official docs over a pinned historical tree when the product still ships.
2. **What this lab illuminates** — the distinctive philosophy, in a few tight paragraphs.
3. **Runtime plumbing** — fields, commands, limits, and packaging needed when targeting that runtime, as links and boundaries rather than copied command sheets.
4. **Divergences from this library** — the recorded disagreements from step 4, including evaluator machinery this repository will not re-host.
5. **Absorbed into core** — pointer list of what was taken and where it now lives.

Section 5 makes re-absorption idempotent: when the vendor ships an update, diff the new package against sections 3–5 and only the genuinely new mechanisms need classifying.

## 6. Record and deliver

- `CHANGELOG.md` bullet with a `Provenance:` clause linking the upstream (contract §6). If the file would exceed 100 lines, drop oldest whole entries; do not grow an archive.
- Update the skill's row in `skills/PROVENANCE.md` when its primary source changes.
- Bump per contract §8 — an absorption that adds lenses or capabilities is MINOR; a re-comparison that changes nothing records the verified no-op in the lens and needs no bump.
- Run the relevant script, scenario, and routing checks from contract §7, with a rationale for the selected evidence. Do not require generated vendor-harness outputs or all corpus/runtime combinations.
- Reuse the existing approved common-policy/domain boundary and exact evidence at destination admission, then use only authorized delivery effects (`lifecycle.md` §6). Delivery is not live publication or deployment.
