# Refactor smell catalog

One entry per smell: a one-line definition, a **Detect** command with its threshold, the **Fix** (which move in `catalog.md` resolves it), and a grey-zone note for when the pattern is fine as-is. Every command is copy-pasteable and approximate unless stated otherwise — read the false-positive note before acting on a finding. `scripts/detect-smells.sh <dir>` runs the greppable subset of these checks in one pass; run it first, then read the smell entry for the ones it flags.

## Table of Contents

- [Size](#size) — Long Function, Long Parameter List, God File / God Class, Nested Conditional
- [Duplication](#duplication) — Duplicated Code, Repeated Type-Check Conditional
- [Coupling](#coupling) — Feature Envy, Shotgun Surgery, Inappropriate Intimacy, Message Chain
- [Abstraction](#abstraction) — Data Clumps, Primitive Obsession, Speculative Generality, Dead Code, Magic Literal
- [Change Smells](#change-smells) — Divergent Change
- [Function](#function) — Boolean Flag Parameter, Negative Conditional, Output Argument, Side Effect in a Helper, Mixed Abstraction Levels
- [Naming](#naming) — Mental Mapping, Inconsistent Vocabulary, Redundant Context
- [Comments](#comments) — Comments as Deodorant, Commented-Out Code, Journal Comment, TODO-as-Feature

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

## Function

### Boolean Flag Parameter

A boolean parameter that switches the function's body between two unrelated code paths — the caller can't tell what actually happens without opening the definition.

**Detect** (approximate — flags any bool-typed parameter, not confirming it forks the body; false positives from flags that only toggle a minor detail):

```bash
# Python — bool-typed parameters
grep -rnE 'def [A-Za-z_]+\([^)]*:[[:space:]]*bool' --include='*.py' <dir>

# TypeScript — boolean-typed parameters
grep -rnE '\([^)]*:[[:space:]]*boolean' --include='*.ts' --include='*.tsx' <dir>
```

**Fix:** [Extract Function](catalog.md#1-extract-function) — split into two named functions, one per branch, and delete the flag.

Grey zone: a flag that only toggles a minor detail within one shared path (`includeMeta: boolean` appending one extra field) is a configuration option, not two functions wearing one name — the smell is a flag that sends execution down genuinely different logic.

### Negative Conditional

A predicate named or phrased as a negative (`isNotValid`, `!isNotReady`) that forces the reader to resolve a double negation before knowing the actual state.

**Detect** (approximate — matches `!` applied to an already-negative name, or a `not`-prefixed predicate definition; misses other double-negative phrasings):

```bash
grep -rnE '!\s*(is_?[Nn]ot|has_?[Nn]ot)[A-Za-z_]*' --include='*.py' --include='*.ts' <dir>
grep -rnE '\b(is_?[Nn]ot|has_?[Nn]ot)[A-Za-z_]*\s*\(' --include='*.py' --include='*.ts' <dir>
```

**Fix:** [Rename](catalog.md#4-rename-via-idelsp-not-sed) the predicate to its positive form; [Extract Variable](catalog.md#3-extract-variable) to name the resulting positive condition at the call site.

Grey zone: a single, isolated `!isX` at one call site reads fine — the smell is a predicate *defined* in the negative, forcing every caller to double-negate to reason about it.

### Output Argument

A function that mutates a parameter passed in — a collection, object, or array — instead of returning a new value, hiding a side effect behind what looks like a normal argument.

**Detect:** no cheap command — greppable candidates (a parameter reassigned or mutated in the body) drown in false positives from legitimate in-place APIs; read the flagged function's parameter list against its body.

**Fix:** [Extract Variable](catalog.md#3-extract-variable) at the call site to hold the return value, and change the function to return the new value instead of mutating the input.

Grey zone: a documented in-place API (`list.sort()`, a builder's `.add()`) is fine when mutation is the stated contract — the smell is an *undocumented* mutation the caller didn't expect from the name or the type.

### Side Effect in a Helper

A function named and shaped like a pure query (`get`/`is`/`calculate`) that also writes state or calls out over the network — its name promises no effect and its body delivers one.

**Detect:** no cheap command — read the flagged lines; a `get`/`is`-prefixed function whose body assigns to something outside its own locals, writes, or calls the network is the tell.

**Fix:** [Extract Function](catalog.md#1-extract-function) to split the query from the effect, or [Rename](catalog.md#4-rename-via-idelsp-not-sed) so the name discloses the effect.

Grey zone: lazy-loading and memoizing a value inside a getter (compute once, cache, return) is an accepted exception — the smell is an effect that other callers depend on, not private memoization.

### Mixed Abstraction Levels

One function interleaves high-level orchestration ("do step A, then step B") with low-level detail (byte offsets, regex, index math) in the same body, forcing the reader to switch levels line by line.

**Detect:** no cheap command — read the flagged function; the tell is a call to a well-named helper sitting directly next to a line of raw loop/index/regex manipulation.

**Fix:** [Extract Function](catalog.md#1-extract-function) to pull the low-level detail into its own named step, so the outer function reads as a flat list of verbs.

Grey zone: a short, genuinely single-purpose function (one loop with one obvious index calculation) isn't mixing levels — the smell needs enough length to have more than one level in the first place.

---

## Naming

### Mental Mapping

A variable or parameter named with a single letter or an abbreviation cryptic enough that the reader must hold its meaning in their head rather than read it off the name.

**Detect** (approximate — single-letter identifiers outside the conventional loop-counter/index exception):

```bash
# Python — single-letter assignment outside common loop counters
grep -rnE '^\s*[a-hl-z]\s*=' --include='*.py' <dir>

# TypeScript — single-letter const/let outside common loop counters
grep -rnE '\b(const|let)\s+[a-hl-z]\s*[:=]' --include='*.ts' --include='*.tsx' <dir>
```

**Fix:** [Rename](catalog.md#4-rename-via-idelsp-not-sed) to the concept the value holds.

Grey zone: `i`/`j`/`k` as loop counters, `x`/`y` as coordinate pairs, and `_` as a deliberately-unused binding are conventional, not mental mapping — the smell is a name that forces a lookup of its definition to know what it holds.

### Inconsistent Vocabulary

The same concept goes by several names across the codebase (`fetchUser`, `getUser`, `retrieveUser`), so a reader can never be sure two similarly-named functions aren't secretly different.

**Detect** (approximate — clusters near-synonym verb prefixes on the same noun; still needs a read to confirm they return the same shape):

```bash
grep -rnoE '\b(get|fetch|retrieve|load)[A-Z][A-Za-z0-9_]*' --include='*.py' --include='*.ts' <dir> \
  | sed -E 's/^[^:]+:[^:]+://; s/^(get|fetch|retrieve|load)//' | sort | uniq -c | sort -rn | awk '$1>=2'
```

**Fix:** [Rename](catalog.md#4-rename-via-idelsp-not-sed) every variant to the one term the team has picked for that concept.

Grey zone: `get` (cheap, in-memory) versus `fetch` (network I/O) can be a deliberate, documented distinction — the smell is unexplained variation on functions that do the identical thing.

### Redundant Context

A field or variable repeats the name of its own container (`car.carColor`, `user.userId` inside `class User`), adding characters without adding information.

**Detect:** no cheap command — greppable candidates (a member name sharing its container's name) need the container name confirmed by eye; scan a flagged type's member list for its own name repeated as a prefix.

**Fix:** [Rename](catalog.md#4-rename-via-idelsp-not-sed) to drop the redundant prefix; the container already supplies that context.

Grey zone: a field name that happens to share a word with its type for a good reason (`Order.orderedAt`, distinct from a hypothetical `Order.createdAt`) is fine — the smell is pure repetition that adds zero disambiguating information.

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

### Commented-Out Code

Dead code left behind a comment marker instead of deleted, so the reader has to decide whether it's meaningful or forgotten.

**Detect:** the Dead Code entry's cheap first pass (`ABSTR-DEADCODE`) already flags commented-out blocks as one of its false-positive sources — treat any such hit that turns out to be a comment, not live code, as this smell instead of Dead Code.

**Fix:** no catalog move applies — delete it outright; version control already holds the history.

Grey zone: a one-line comment documenting *why* an approach was rejected is a design note, not this smell — the smell is a code block left behind, not a sentence.

### Journal Comment

A comment block logging dates, authors, or an edit history inline in the source, duplicating what version control already tracks.

**Detect** (approximate — comment lines containing a date or an attribution phrase):

```bash
grep -rnE '^\s*(//|#).*(\b[0-9]{4}-[0-9]{2}-[0-9]{2}\b|changed by|modified by)' --include='*.py' --include='*.ts' <dir>
```

**Fix:** no catalog move applies — delete it; `git log`/`git blame` already carries that history.

Grey zone: none — a journal comment is never load-bearing information the code itself needs; delete on sight.

### TODO-as-Feature

A `TODO` comment standing in for behavior the current task actually requires, shipped as if leaving a note were the same as finishing the work.

**Detect:** no cheap command — a `TODO`/`FIXME` grep mostly finds legitimate deferred work; confirm by reading whether the surrounding function sits on a path the current change is supposed to make work.

**Fix:** implement the behavior now, or file a tracked issue and say so explicitly in the commit or PR — never let the comment substitute for either.

Grey zone: a `TODO` marking a genuinely out-of-scope follow-up (a documented future optimization, not required for correctness now) is fine — the smell is a `TODO` covering for missing behavior the task was supposed to deliver.

