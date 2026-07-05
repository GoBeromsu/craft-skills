# Refactor smell catalog

One entry per smell: a one-line definition, a **Detect** command with its threshold, the **Fix** (which move in `catalog.md` resolves it), and a grey-zone note for when the pattern is fine as-is. Every command is copy-pasteable and approximate unless stated otherwise — read the false-positive note before acting on a finding. `scripts/detect-smells.sh <dir>` runs the greppable subset of these checks in one pass; run it first, then read the smell entry for the ones it flags.

## Table of Contents

- [Size](#size) — Long Function, Long Parameter List, God File / God Class, Nested Conditional
- [Duplication](#duplication) — Duplicated Code, Repeated Type-Check Conditional
- [Coupling](#coupling) — Feature Envy, Shotgun Surgery, Inappropriate Intimacy, Message Chain
- [Abstraction](#abstraction) — Data Clumps, Primitive Obsession, Speculative Generality, Dead Code, Magic Literal
- [Change Smells](#change-smells) — Divergent Change
- [Comments](#comments) — Comments as Deodorant

---

## Size

### Long Function

A function whose body is long enough that a reader must hold too much unrelated state in working memory to follow it in one pass.

**Detect** (approximate — indentation-boundary heuristic; threshold 40 lines from a def/function line to the next one at the same-or-lower indentation):

```bash
scripts/detect-smells.sh <dir> | grep SIZE-LONGFN
```

**Fix:** [Extract Function](catalog.md#1-extract-function) — or [Replace Loop with Pipeline](catalog.md#12-replace-loop-with-pipeline) when the bulk of the body is one imperative iteration.

Grey zone: a long function that is a flat, no-branching sequence of independent steps (a data pipeline, a migration script) can be more readable whole than split — judge by branching and reuse, not line count alone.

### Long Parameter List

A signature with enough parameters that callers can no longer track which value goes where.

**Detect** (approximate — single-line signatures only; threshold ≥4 params):

```bash
scripts/detect-smells.sh <dir> | grep SIZE-PARAMS
```

**Fix:** [Introduce Parameter Object](catalog.md#8-introduce-parameter-object).

Grey zone: 4 parameters that vary fully independently of one another are just a wide function — the smell is specifically when a *subset* travels together across call sites (see Data Clumps).

### God File / God Class

A single file or class that has grown past the point a reviewer can hold in working memory.

**Detect:** the file-size ceiling is owned by `programming` — reuse its command directly rather than duplicating a threshold here:

```bash
awk '!/^[[:space:]]*$/ && !/^[[:space:]]*(\/\/|#)/' <file> | wc -l   # >250 pure LOC = defect
```

A God Class is the object-shaped version of the same ceiling: one class whose method count or pure LOC crosses the same 250-line threshold.

**Fix:** [Extract Class](catalog.md#11-extract-class).

Grey zone: a generated file (schema bindings, a single state machine table) may justify crossing the ceiling with a one-line comment explaining why it is genuinely indivisible.

### Nested Conditional / Arrow Code

Control flow nested deep enough that the reader must track several simultaneous conditions to reach the line that matters.

**Detect** (approximate — indentation depth, not true AST nesting; threshold 4+ levels):

```bash
scripts/detect-smells.sh <dir> | grep SIZE-NESTING
```

**Fix:** [Replace Nested Conditional with Guard Clauses](catalog.md#7-replace-nested-conditional-with-guard-clauses).

Grey zone: two levels of nesting for two genuinely independent conditions is normal control flow — the smell is three-plus levels, or the same guard repeated at every level.

---

## Duplication

### Duplicated Code

The same logic, copy-pasted rather than shared, so a bug fix or business-rule change has to be applied more than once to take effect.

**Detect** (approximate — exact-line floor, not a semantic diff; threshold: a normalized line of 20+ characters repeated 3+ times across the tree):

```bash
scripts/detect-smells.sh <dir> | grep DUP-BLOCK
```

A real near-duplicate detector (renamed variables, reordered statements, same shape different tokens) needs a proper AST-diff tool — this command is a cheap floor, not a ceiling.

**Fix:** [Extract Function](catalog.md#1-extract-function) (same object) or [Extract Class](catalog.md#11-extract-class) (duplicated across two related objects).

Grey zone: two blocks that *look* similar but encode different business rules are coincidental duplication — forcing a shared abstraction over them couples two things that change for different reasons. Only unify duplication that shares a reason to change.

### Repeated Type-Check Conditional

The same `isinstance`/`typeof`/tag-switch conditional, copy-pasted at every call site that needs to branch on a variant — every new variant means finding and updating all of them.

**Detect** (approximate — counts occurrences per file; does not confirm the *same* conditional recurs at multiple call sites, which still needs a read):

```bash
# Python — 3+ isinstance checks in one file
grep -rnE '\bisinstance\(' --include='*.py' <dir> | cut -d: -f1 | sort | uniq -c | awk '$1>=3'

# TypeScript — 3+ typeof/tag discriminations in one file
grep -rnE '\btypeof\b.*===|\.kind ===|\.type ===' --include='*.ts' --include='*.tsx' <dir> \
  | cut -d: -f1 | sort | uniq -c | awk '$1>=3'
```

**Fix:** [Replace Conditional with Polymorphism](catalog.md#6-replace-conditional-with-polymorphism).

Grey zone: a single, isolated type check (a boundary parser distinguishing two input shapes) is fine — the smell is the *same* discrimination repeated across independent call sites.

---

## Coupling

### Feature Envy

A function that reaches into another object's data more than it uses its own — it is doing that object's job from the outside.

**Detect** (approximate — per-function ratio of foreign-attribute access to `self`/`this` access; flag when foreign access exceeds self access by 3+):

```bash
awk '
  /^[ \t]*(def |function |async def )/ {
    if (fn && other - self >= 3) print fname":"start"  COUPLING-ENVY ("other" foreign refs vs "self" self refs)"
    fn = 1; start = NR; self = 0; other = 0; fname = FILENAME
  }
  fn && /(^|[^A-Za-z0-9_])(self|this)\.[A-Za-z_]/ { self++ }
  fn && /(^|[^A-Za-z0-9_])[a-z_][A-Za-z0-9_]*\.[A-Za-z_]/ && !/(^|[^A-Za-z0-9_])(self|this)\./ { other++ }
  END { if (fn && other - self >= 3) print fname":"start"  COUPLING-ENVY" }
' <file>
```

**Fix:** [Move Function](catalog.md#5-move-function) — relocate the method next to the data it actually uses.

Grey zone: calling a couple of fields off another object to compute a purely local value isn't envy; fluent utility calls (`math.floor(x)`, a logger) inflate the "foreign" count without being envy at all — read the flagged function before moving anything.

### Shotgun Surgery

One conceptual change (add a field, rename a concept) requires touching many unrelated files — the responsibility for that concept is scattered instead of owned in one place.

**Detect** (approximate — commit co-change frequency; judged by reading the list, not a hard cutoff):

```bash
git log --format= --name-only -- <path-or-dir> | sort | uniq -c | sort -rn | head -20
```

Look for a cluster of files whose co-change counts move together across many commits (a rough floor: 5+ shared commits).

**Fix:** [Move Function](catalog.md#5-move-function) or [Extract Class](catalog.md#11-extract-class) to consolidate the scattered responsibility into one owner.

Grey zone: files that legitimately share a public-interface migration (a rename that touches every caller once) are normal — the smell is the *same kind* of change recurring across unrelated modules every time the concept evolves.

### Inappropriate Intimacy

Code outside a class/module reaches into its private internals instead of going through its public surface.

**Detect** (approximate — Python-convention-specific; TypeScript's `private`/`#field` is already compiler-enforced, so this smell matters far more in Python and duck-typed JS):

```bash
grep -rnE '[A-Za-z_][A-Za-z0-9_]*\._[A-Za-z][A-Za-z0-9_]*' --include='*.py' <dir> \
  | grep -vE '/tests?/'
```

**Fix:** [Move Function](catalog.md#5-move-function) or [Extract Class](catalog.md#11-extract-class) to relocate the logic next to the data it reaches into.

Grey zone: a test file reaching into internals to verify state is an accepted exception (the command above already excludes `tests/`/`test/` paths) — the smell is production code doing it.

### Message Chain

A line that walks through a chain of objects to reach the one it actually needs — any of those intermediate objects changing breaks every caller in the chain.

**Detect** (approximate — 4+ chained `.` accesses on one line):

```bash
scripts/detect-smells.sh <dir> | grep COUPLING-CHAIN
```

**Fix:** [Extract Function](catalog.md#1-extract-function) (or [Move Function](catalog.md#5-move-function)) to hide the delegation behind one call on the object the caller actually needs.

Grey zone: a chain through a fluent builder API designed for chaining (a query builder, an assertion library) is idiomatic, not a Law-of-Demeter violation — judge by whether the chain traverses object *internals* versus a public interface built for exactly this.

---

## Abstraction

### Data Clumps

The same group of 3+ parameters (or fields) shows up together across multiple signatures — the group is really one concept that has never been named.

**Detect** (approximate — order-sensitive; misses a reordered clump):

```bash
grep -rnoE '\(([a-z_]+, ){2,}[a-z_]+' --include='*.py' --include='*.ts' <dir> \
  | sed -E 's/^[^:]+:[^:]+://' | sort | uniq -c | sort -rn | awk '$1>=2'
```

**Fix:** [Introduce Parameter Object](catalog.md#8-introduce-parameter-object).

Grey zone: two parameters that merely share a type (two independent counts) aren't a clump unless the *same group* recurs across 3+ signatures.

### Primitive Obsession

A domain concept (an email, a currency amount, an ID) represented as a bare `str`/`int`/`string` everywhere instead of its own type — every call site re-invents its own validation.

**Detect** (approximate — illustrative concept list; swap in the domain's own vocabulary; threshold 3+ occurrences of the same concept typed as a bare primitive):

```bash
grep -rnE '(email|user_id|currency|amount)[[:space:]]*:[[:space:]]*(str|string)\b' \
  --include='*.py' --include='*.ts' <dir> | wc -l
```

**Fix:** [Introduce Parameter Object](catalog.md#8-introduce-parameter-object) for a group, or hand off to `programming`'s `NewType`/branded-type rule for a single recurring value.

Grey zone: a primitive used once, locally, with no repeated validation logic is not obsession yet — the smell is the *same* concept's validation duplicated at every site that touches it.

### Speculative Generality

An interface, abstract base, or plugin seam built for flexibility no caller has asked for yet.

**Detect** (approximate, two-step — no single grep counts implementers reliably):

```bash
# Step 1: list candidate interfaces/protocols
grep -rnE 'class .*\(Protocol\)|^interface [A-Za-z_]+' --include='*.py' --include='*.ts' <dir>

# Step 2: for each candidate name, count concrete implementers/usages
grep -rc '<CandidateName>' --include='*.py' --include='*.ts' <dir>
```

≤1 concrete implementer beyond the interface declaration itself is the signal.

**Fix:** [Inline Function](catalog.md#2-inline-function) — collapse the seam back to the concrete type until a second real implementation exists.

Grey zone: an interface with one implementation *and* a concrete, scheduled second implementation (a payment provider due next milestone) is a plan, not a smell yet — judge by whether a second caller exists within the current milestone, not "might exist someday."

### Dead Code

Code that no live path ever reaches or calls — it costs reading time and blast-radius risk for zero behavior.

**Detect** (two-tier — cheap first pass, then an authoritative per-language check):

```bash
# Cheap first pass (approximate — flags commented-out code, not true dead code)
scripts/detect-smells.sh <dir> | grep ABSTR-DEADCODE

# Authoritative
uv run vulture <dir>            # Python — unused functions/vars
npx ts-prune -p tsconfig.json    # TypeScript — unused exports
```

A 0%-coverage function from a full test-suite run is also a dead-code candidate — confirm it is truly unreachable before deleting; a coverage gap can mean untested-but-live code instead.

**Fix:** no catalog move applies — delete it outright. See `programming`'s rule to remove obsolete code rather than leaving a dead alias behind.

Grey zone: code behind a feature flag that is currently off is not dead — judge reachability across every live configuration, not just today's default.

### Magic Literal

An unexplained numeric or string constant embedded inline, where the reader has to reverse-engineer what it represents.

**Detect** (approximate — array indices, loop counters, and 0/1/-1/100 are common, usually-fine false positives):

```bash
scripts/detect-smells.sh <dir> | grep ABSTR-MAGIC
```

**Fix:** [Replace Magic Literal](catalog.md#9-replace-magic-literal).

Grey zone: `0`, `1`, `-1`, and well-known idioms (HTTP `200`, a zero-based array index) don't need a name — the smell is a domain-specific threshold or business constant with no name anywhere.

---

## Change Smells

### Divergent Change

One file changes for many unrelated reasons — a change to pricing and a change to logging both land in the same file because it has grown more than one responsibility.

**Detect** (approximate — commit-subject-prefix diversity as a proxy for "how many different reasons this file changes"; judge by reading the list, not a hard count):

```bash
git log --format='%s' -- <file> | awk '{print $1}' | sort | uniq -c | sort -rn
```

Many distinct leading words/types across commits touching one file is the signal — a wide spread means many different reasons to change land in the same place.

**Fix:** [Split Phase](catalog.md#10-split-phase) or [Extract Class](catalog.md#11-extract-class) to separate the independent reasons to change into their own units.

Grey zone: a file that changes often *for the same reason* (a router registering new routes) is not divergent change — the smell is unrelated reasons converging on one file, not high churn alone.

---

## Comments

### Comments as Deodorant

A comment explaining *what* a confusing block of code does, standing in for code that should have been made clear enough to read on its own.

**Detect** (approximate — comment-to-code line ratio; grey-zone-heavy, see below):

```bash
scripts/detect-smells.sh <dir> | grep COMMENT-DEODORANT
```

Threshold: ratio > 0.3 in a file with 20+ non-blank lines.

**Fix:** [Extract Variable](catalog.md#3-extract-variable) or [Extract Function](catalog.md#1-extract-function) to name the thing instead of describing it; [Rename](catalog.md#4-rename-via-idelsp-not-sed) often removes the need for the comment entirely.

Grey zone: a comment stating *why* — a non-obvious constraint, a trade-off, a `craft:` ceiling — is documentation, never this smell. The smell is specifically a comment narrating *what* the very next line already says.

