# Interface ownership

Two services can pass an import-boundary check and still share an interface nobody owns.
Import linting proves the *absence of imports*; it says nothing about runtime coupling through a shared directory, a polled table, or an HTTP call.
This reference owns who owns an interface between two components and how drift in it is caught.

## Contents

- [The ownership rule](#the-ownership-rule)
- [Ordered steps](#ordered-steps)
- [What belongs in a shared package](#what-belongs-in-a-shared-package)
- [Pitfalls](#pitfalls)

## The ownership rule

- **The provider owns what it serves or writes** — the route constants and response shapes it serves, and the schema and version of any file it writes.
- **The consumer owns what it expects** — the routes it calls and the fields it parses, in its own package, with its own strictness.
- **Drift is caught by a contract test**, in the one place allowed to import both sides.
  That test produces the artefact with the provider's writer and parses it with the consumer's parser, and separately asserts that the provider's route constants equal the consumer's.

The named principles behind this are consumer-driven contracts, and ports-and-adapters with dependency inversion.
The failure modes it avoids have names too: a shared kernel misapplied to a service boundary, and shared-library coupling that turns separate services into a distributed monolith.

## Ordered steps

1. Table the runtime couplings: shared volume mounts, origin URLs in configuration, and any component that globs and parses another component's files.
   Classify each one as cross-repository vocabulary, component-internal, or a one-shot operational path that only needs documenting.
2. Provider side: put route constants in one module, and the written file's schema in one module.
3. Consumer side: keep its own parser and make it explicit; it never imports the provider.
4. Write the contract test: writer to bytes to consumer parser, plus route-path equality, covering every field the provider actually emits.
5. Where the writer and the parser disagree, decide which side is right and report it rather than quietly widening the parser.
6. Fix any architecture document that claims a one-way relationship the code contradicts.

A worked instance: two services that provably never imported each other still shared two entirely implicit interfaces — an HTTP surface with paths hard-coded on both sides, and a manifest file written by one and parsed by a separate model in the other.
Pinning them took 13 contract tests.

## What belongs in a shared package

A shared package is for vocabulary shared **across repositories** — relay payloads, configuration pull, provisioning — never for internal plumbing.
Moving two locally shared shapes into a byte-mirrored cross-repository package was the first attempt at the fix above, and it was wrong: that package creates a sibling-repository synchronisation obligation, and the shapes only two local components care about earn none of it.
The correction is provider and consumer ownership plus the test, not a new shared module.

## Pitfalls

- **A dependency is not an interface.**
  One service calling another over HTTP is fine; it becomes a defect only when the interface is owned by neither side and unpinned by a test.
- **A duplicated schema hides real bugs.**
  In one case the writer always emitted a field the reader's strict field list lacked, so every real record was rejected — each side's tests used its own fixtures, and only a round-trip test could find it.
- A drift test that *skips* when the sibling checkout is absent only fails on the default branch's CI, long after the wrongly placed module landed.
- Local presentation policy is not part of the interface; keep it on the owning side with a comment saying so.
- Tightening a consumer's parser is a behavior change for malformed input — state the new mapping explicitly rather than letting it surface as a new error code in production.
