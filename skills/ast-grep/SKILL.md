---
name: ast-grep
description: Routes syntax-aware structural search and replacement through ast-grep. Use when asked to find every call site of a function, match a function declaration, search JavaScript or TypeScript syntax, replace a code shape safely, or locate a particular AST node. Not for behavior-preserving restructuring (use refactor) or writing new code (use programming).
metadata:
  version: 1.0.0
---

# ast-grep

Search and replace code by syntax-tree shape rather than text bytes. Done means the pattern parses in the target language, its matches have been inspected, and a replacement is applied only after its dry-run blast radius is understood.

## Requirements

Start with `command -v ast-grep || command -v sg`. Use the binary that resolves. When neither resolves, install ast-grep through the environment's package manager or its official distribution, then retry. Until it is available, use plain text search as a deliberately approximate fallback; do not claim structural matches from it.

## Decision test

Ask: **is this a syntax-tree question or a bytes question?** Use ast-grep when the answer depends on code structure (a call, declaration, argument, or enclosing node); use text search when spelling, prose, logs, generated text, or arbitrary bytes are the target.

## Correct the model before searching

| Wrong model | Right model |
|---|---|
| “The pattern is regex.” | A pattern is source code matched as a syntax tree; use metavariables such as `$NAME` and `$$$ARGS`, not regex operators. |
| “Any string is a pattern.” | The pattern must be parseable code in the chosen `--lang`; quote it for the shell, but make its contents valid source. |
| “`--json` and `--update-all` are a safe combined mode.” | Keep reporting and mutation separate. JSON output and bulk-apply flags can conflict silently, so run JSON inspection without `--update-all`, then run the reviewed replacement without `--json`. |

## Golden path: mutate by ladder

1. **Validate the pattern.** State the target language and run a query-inspection command before targeting the repository:
   ```sh
   ast-grep run --lang ts --pattern 'client.fetch($URL)' --debug-query
   ```
   Replace `ast-grep` with `sg` when that is the installed binary. If parsing fails, fix the pattern before searching files.
2. **Search without mutation.** Limit paths to the intended scope and read representative matches:
   ```sh
   ast-grep run --lang ts --pattern 'client.fetch($URL)' src/
   ```
3. **Dry-run the replacement.** `--rewrite` without `--update-all` previews the change; it does not write files:
   ```sh
   ast-grep run --lang ts --pattern 'client.fetch($URL)' --rewrite 'http.fetch($URL)' src/
   ```
4. **Inspect the blast radius.** Check total matches, changed files, surrounding code, and exceptional forms such as optional chaining, overloads, or comments that text search would have confused.
5. **Apply only the reviewed change.** Re-run the exact dry-run command with `--update-all`, then inspect the diff and run focused tests:
   ```sh
   ast-grep run --lang ts --pattern 'client.fetch($URL)' --rewrite 'http.fetch($URL)' --update-all src/
   ```

Escape hatch: when each replacement needs a context-dependent decision, keep the search results and edit those sites manually rather than forcing a broad rewrite.

## Diagnose zero matches

Climb this ladder in order:

1. Confirm `--lang` matches the files, not merely the project's primary language.
2. Confirm the pattern parses as source in that language with `--debug-query`.
3. Check metavariable spelling and position: `$NAME` matches one node; `$$$NODES` matches multiple nodes where the grammar permits them.
4. Narrow or reshape the target node kind. Match a call expression, declaration, or argument form that actually exists instead of an imagined larger statement.

Use a small known-positive snippet or a single representative file to distinguish a bad query from an empty repository result.

## Choose the search surface

| Need | Default | Escape hatch |
|---|---|---|
| One local structural shape | Inline `--pattern` | Promote repeated, contextual, or relational matching to a YAML rule. |
| Reusable rule with constraints, messages, or multiple patterns | YAML rule via `ast-grep scan` | Keep a one-off query inline. |
| Syntax-tree shape | ast-grep | Use text search only when syntax is irrelevant. |
| Symbol definition, references, rename, or type-aware ownership | Semantic tooling/LSP | Use ast-grep to find syntactic variants outside one resolved symbol. |
| A question spanning code, docs, issues, and generated artifacts | Federated search | Use ast-grep as the code-structure lane, not the whole answer. |

## Invariants

- Choose AST search only for structure, and text search only for bytes.
- Pass an explicit language and a parseable pattern.
- Keep JSON reporting separate from bulk mutation.
- Validate, search, preview, inspect, then apply; a zero-match result is evidence to diagnose, not permission to widen blindly.

## Hand-offs

- A reviewed structural change needs behavior-preserving reorganization across the codebase → `refactor`.
- The request is to design or write new behavior rather than locate or transform existing syntax → `programming`.
