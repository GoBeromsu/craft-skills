# Autofix failure classes

A linter's autofix is a code change nobody wrote and nobody reviewed by default.
These are the classes of fix that pass the linter, produce a plausible diff, and are wrong — each is silent until something else runs.
Check a proposed autofix against this list before applying it, and treat any match as a rule to scope out rather than a diff to accept.

The common shape: the linter reasons about the code's *form*, and each of these classes depends on something outside the form — a reader of the text, a pinned ordering, an import's side effect, a construct's other half.

| Class | The fix looks like | What actually breaks |
|---|---|---|
| Justification stripping | Removing a suppression the linter now considers unused | The human-readable reason attached to it |
| Literal reshaping | Merging, splitting, or renormalizing string literals | Anything that searches or matches the literal's text |
| Order pinning | Sorting a sequence into canonical order | Anything asserting the original order byte for byte |
| Presence-only symbols | Deleting an import or binding with no local reference | The re-export, registration, or side effect it existed for |
| Half-applied rewrites | Simplifying one part of a construct | The now-orphaned remainder the fix left behind |

## Justification stripping

A rule that removes suppressions it believes are unused removes the whole comment, including the prose reason someone wrote to explain why the suppression exists.
The suppression may genuinely be unused while its reason is the only surviving record of a decision.

Detect it by diffing for removed comment text rather than removed comment markers: any hunk that deletes a suppression carrying free text beyond the rule code is this class.
Scope the rule out wherever suppressions are documented by convention, rather than accepting the deletion and re-deriving the reasons later.

## Literal reshaping

A rule that joins adjacent string literals, splits a long one, or normalizes quoting changes the source form of a value that something else matches against.
The runtime value can be identical and the change still breaks a caller: a scanner, a grep-based check, a translation-key extractor, or a test asserting on source text is reading the literal's written form, not its evaluated result.

The dangerous direction is joining, because it *creates* a string that did not previously exist in the source — a deliberately split literal is often split precisely so a scanner does not match it.

Detect it by searching for the post-fix literal across the repository's checks and fixtures before applying it.
Where a literal is split on purpose, keep the split and record why in an inline suppression; scope the multi-line variant of the rule out of files holding deliberate SQL, fixtures, or embedded documents.

## Order pinning

A rule that sorts an export list, an argument list, a dictionary, or a set of declarations produces a canonically ordered result that is unambiguously nicer and unambiguously different.
When something asserts the original order — a vendored module mirrored byte for byte against upstream, a snapshot test, a generated file compared against its generator's output — the sort breaks it.

Detect it by asking what pins this ordering outside the file: a mirror or snapshot test, a checksum, a vendoring contract, or a generator.
Vendored and generated trees are the standing case; scope ordering rules out of them by path rather than resolving each break individually.

## Presence-only symbols

A rule that removes unreferenced imports or bindings assumes a symbol's purpose is to be referenced.
A re-export exists to be imported *from elsewhere*, a registration import exists for its side effect, and a fixture alias exists so a name resolves in a test module — none of them are referenced locally, and all of them are deleted by this class of fix.

Detect it by searching for the removed name across the repository rather than the file, and by checking whether the file is an aggregating module — a package entry point, a fixtures module, a plugin registry.
Where a project uses re-export aliasing as a convention, disable the redundant-alias rule rather than suppressing it per occurrence.

## Half-applied rewrites

A rule that simplifies a construct rewrites the part it understands and leaves the rest: collapsing an assign-then-return leaves the assignment's variable unused, merging branches leaves a condition that is now unreachable or a line far past the length limit, and inverting a check leaves a comment describing the old direction.
The result is valid, passes the rule that produced it, and is worse than what it replaced.

Detect it by re-running the full linter after the autofix rather than only the rules that were applied — a half-applied rewrite usually trips a *different* rule, and that second signal is the tell.
Read the fix's output where the construct spans more than a couple of lines, and prefer a hand edit for the cases where the rule's model of the construct is clearly narrower than the code's shape.
