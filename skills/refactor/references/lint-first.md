# Lint-first simplification

Making an existing package smaller and clearer by moving as much of the work as possible into linter configuration, and reserving hand judgment for what the linter cannot express.
Configuration beats a bespoke script: it runs in CI already, and the next person edits one file rather than learning a private tool.
The rule codes below come from one Python linter and are illustrative — consult the incumbent linter's official documentation for what each rule means and fixes in the installed version before enabling it.

## Contents

- [Inputs](#inputs)
- [Ordered steps](#ordered-steps)
- [Autofix pitfalls](#autofix-pitfalls)
- [Success criteria](#success-criteria)

## Inputs

- The linter's currently selected rule sets.
- The target package; the rest of the repository is scoped out with per-file ignores rather than by narrowing the global selection.
- A green suite and a clean contract check before starting, per the safety protocol in `../SKILL.md`.

## Ordered steps

1. **Measure before enabling.**
   For each candidate rule set, count its hits on the target package alone and record the number.

   ```bash
   <linter> check --select <RULESET> <package>/ | tail -1
   ```

   A worked measurement across one package: `SIM` 15, `C4` 3, `PIE` 1, `RET` 3, `PERF` 6, `RUF` 154 of which 106 were unused-suppression findings, `FURB` 4, `ISC` 11.
   The distribution is the point — one set dominated the count and most of that set was a single rule, which changes what is worth enabling.
2. Enable only the sets whose hits are genuine improvements.
   Prefer per-file ignores for tests, scripts, and other packages over dropping a rule globally, and write the reason next to each ignore.
3. Apply the autofixes and commit them **alone**: configuration plus mechanical rewrites, nothing else.
   Read the unsafe-fix diff before applying any of it, and apply unsafe fixes per rule rather than wholesale.
4. Run the suite.
   Revert any autofix that flips a test and record it as a per-file ignore or an inline suppression with its reason.
5. Do the hand pass for what lint cannot express — duplicate helpers, dead code, recomputation inside a loop, copy-pasted blocks — strictly behavior-preserving, and commit it separately.
6. State explicitly what was *skipped* and why: cross-package deduplication that would breach an import contract, arithmetic that changes rendered output, metric semantics.

Two commits, not one: mechanical and judgment changes reviewed together means the judgment changes are not reviewed.
A worked split ran 165 files at +579/−537 for the mechanical commit and 20 files at +147/−244 for the hand commit.

## Autofix pitfalls

Each of these cost a revert in one pass, and each is invisible until the suite runs.

- An unused-suppression autofix stripped the *reason text* from suppression comments the repository relied on, so it was ignored globally instead.
- An implicit-string-concatenation fix joined two adjacent literals into exactly the string a privacy scan test searched for, turning a passing scan into a failing one; keep the literal split with an inline suppression.
- The multi-line variant of that rule flags deliberate SQL and fixture literals; scope it out per file.
- A sorting fix reordered an export list inside a vendored, byte-pinned module and broke its mirror test; ignore that rule for vendored files.
- A redundant-alias fix turned deliberate re-export aliases in test fixtures into unused imports; drop that rule.
- A return-refactor fix left a dead variable behind, and a branch-merge fix produced a 155-character line — read the autofix output rather than trusting it.
- Formatting is a separate concern: one repository had roughly 300 pre-existing unformatted files while CI ran only the checker, so a format sweep bundled into a simplification change would have buried it.
- Do not stack unrelated packages.
  When a repository-wide rule floods a package that is not the target, scope it with per-file ignores and record it as follow-up.

## Success criteria

- The linter passes across the whole repository, not just the target package.
- The suite has no real failures, and every import contract is still kept.
- Exactly two commits: configuration plus autofix, then hand edits.
- The change description names the enabled rule sets and the before-and-after hit counts.
  A worked result: 307 findings repository-wide reduced to 0 by configuration and autofix, then a small hand pass, ending with 3971 tests passing, a clean linter, and 11 of 11 contracts kept.
