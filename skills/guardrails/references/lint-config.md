# Linter and formatter configuration

Owning the tier-2 surface: which linter rules are enabled, where they are ignored, who owns whitespace, and how a change to any of that reaches the repository without burying the work it was meant to protect.
Configuration is the deliverable, not a script — it runs inside the checks that already exist, and the next person edits one file instead of learning a private tool.

## Contents

- [Stage rule sets by measured hit count](#stage-rule-sets-by-measured-hit-count)
- [Read the autofix before trusting it](#read-the-autofix-before-trusting-it)
- [Split the commits](#split-the-commits)
- [Ignore policy](#ignore-policy)
- [Formatter ownership](#formatter-ownership)
- [Adopting a formatter onto an unformatted repository](#adopting-a-formatter-onto-an-unformatted-repository)

## Stage rule sets by measured hit count

Switching on a linter's full recommended selection in one commit produces a diff nobody reads and a rule set nobody chose.
Enable in stages, and let the measurement decide the stages.

1. Count each candidate rule set's hits against the target scope alone, and record the number before deciding anything.

   ```bash
   <linter> check --select <RULESET> <target>/ | tail -1
   ```

2. Read the distribution, not the total.
   A set whose hits concentrate in a single rule is a different decision from a set spread evenly across many — the first is one judgment call, the second is a policy change.
   A set dominated by one rule that turns out to be unwanted is enabled with that rule excluded, not dropped whole.
3. Enable only the sets whose hits are genuine improvements at the current hit count.
   A set that would pay off later, once the code has moved, is recorded as a follow-up rather than enabled with a wall of ignores holding it back.
4. Re-count after each stage lands, so the next decision is made against the new baseline rather than the original one.

The recorded before-and-after counts are the evidence that the rule set earned its place; a change description that names the enabled sets without them is asserting, not showing.

## Read the autofix before trusting it

Apply the safe autofix first, then read its diff.
Apply the unsafe or opt-in fixes one rule at a time, reading each rule's diff separately — a wholesale unsafe-fix run mixes a rewrite that is obviously correct with one that quietly changes meaning, and the reviewer cannot tell them apart.
Every class in [`autofix-failure-classes.md`](autofix-failure-classes.md) is invisible in the diff until the suite runs, so run the suite after the autofix and before the hand pass.
An autofix that flips a test is reverted and recorded as a scoped ignore with its reason — not argued with, and not fixed by editing the test to match.

## Split the commits

Configuration plus mechanical autofix output lands in one commit; the hand pass that follows lands in another.
The reason is reviewability, not tidiness: judgment edits reviewed inside a diff of hundreds of mechanically rewritten files are not reviewed at all, and a revert of the mechanical change drags the judgment with it.

The mechanical commit is large and boring by construction, and that is the signal it is safe.
The hand commit is small and interesting, and that is where review attention belongs.
When a formatter is being adopted in the same campaign, its sweep is a third commit — never folded into either of the other two.

## Ignore policy

Prefer the narrowest scope that works, in this order: an inline suppression on the one line, a per-file or per-directory ignore, then a global disable as the last resort.
A global disable is a decision about the whole repository made to solve a problem in one corner of it.

Every ignore records its reason next to the ignore itself, in the configuration or the suppression comment.
An ignore whose reason lives only in a commit message is invisible at the moment someone is deciding whether to delete it, and gets deleted.

Scope tests, generated code, vendored trees, and fixtures out with per-file ignores rather than narrowing the global selection — the global selection is what the production code is held to, and weakening it to accommodate a fixture weakens it everywhere.
When a repository-wide rule floods a scope that is not the target, ignore it there and record it as follow-up rather than stalling the current change.

## Formatter ownership

Once a formatter is adopted, it owns whitespace, line breaks, and quoting in the files it covers, and nobody hand-edits those.
This is the whole value: the formatter's output is not a preference to be negotiated per diff, and a repository where some files are hand-tuned has a formatter that fights its own contributors.

Two consequences follow.
Disagreement about the output is resolved by changing the formatter's configuration, never by editing the formatted result — an edit the formatter did not produce is reverted on the next run, and the churn recurs in every diff that touches the file.
Stylistic rules in the linter that overlap the formatter's territory are disabled, so the two tools cannot produce contradictory fixes on the same line.

## Adopting a formatter onto an unformatted repository

A repository with a large pre-existing unformatted surface cannot absorb a big-bang reformat: the sweep buries every other change in its blast radius, invalidates in-flight branches, and rewrites the blame of files nobody was working on.

Adopt with a ratchet instead:

1. Add the formatter's configuration and wire the **check** — not the write — into the local surface and the required checks, scoped to the set of files already conformant (often empty at the start).
2. Format one coherent scope at a time — a directory, a package, a layer — each as its own commit containing nothing else, and widen the checked scope to include it in the same commit.
3. Order the scopes by how little in-flight work touches them, so the rewritten files and the open branches overlap as little as possible.
4. Record the sweep commits so history tooling can skip them; a formatting-only commit that is invisible to blame keeps the ratchet cheap for everyone reading the file afterwards.

The end state is the same as a big-bang adoption, reached without a single commit that touches everything.
Until the ratchet completes, the check covers only the conformant scopes, so it is a real gate on new work rather than a permanently failing job everyone learns to ignore.
