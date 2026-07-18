---
name: enrich-notes
description: Enriches an existing Obsidian vault note with verified links and verified facts — promotes plain-text references to `[]()` web links or `[[]]` wikilinks only after confirming each target, re-checks every cited URL through a curl → authenticated `gh api` → web-search ladder that rules out private-repo false 404s, and verifies technical figures against primary sources before writing them, labeling estimates as estimates. Use when asked to beautify a note, 노트 다듬어줘, re-verify links in a task note, promote raw pasted references into real links, or add researched numbers such as model VRAM requirements. Not for markdown syntax or house style — use obsidian-markdown; not for authoring a new note.
metadata:
  version: 1.0.0
---

# enrich-notes

Raise an existing vault note's evidence quality without changing its meaning: every
reference becomes a working link, every technical number is verified against a primary
source or labeled as an estimate, and every person or term links to a note that already
exists. Success: zero unverified URLs, zero invented links or notes, frontmatter values
untouched, operator prose preserved word-for-word.

## Scope gate

Enrichment edits an existing note in place. Two constraints override everything else:

- Notes authored by the operator (`authorship: user` or the vault's equivalent) get
  structure and link edits only — never rephrase their sentences or "fix" their voice.
- Frontmatter values are read-only except the modification date. Keep key order and
  spacing exactly as the vault's linter last wrote them — reverting linter output starts
  an edit war the linter always wins. Add no new keys.

For markdown syntax and the vault house style (bullets, callouts, wikilink syntax),
follow obsidian-markdown; this skill owns only the verification work.

## Workflow

1. **Ground.** Read the vault's frontmatter guideline (its SSOT for allowed keys and
   value shapes) under `${OBSIDIAN_VAULT_PATH}`, then re-read the target note from disk
   immediately before editing — a linter or the operator may have changed it since it
   was last read.
2. **Promote references.** Classify each plain-text reference:
   - web resource → `[title](url)`, only after the URL verifies (step 3)
   - vault entity (person, term, related note) → `[[wikilink]]`, only when the target
     note exists — search the vault first, link the first mention rather than every
     mention, and never create a note as a side effect of linking
   - local filesystem path → leave as a code span; it is neither web nor vault
3. **Verify every cited URL** — the ladder, cheapest rung first:

   ```bash
   curl -sIL -o /dev/null -w '%{http_code} %{url_effective}\n' "$URL"
   ```

   - `2xx` → record OK; note the final URL when it redirected.
   - `404`/`403` on a code host → run `gh api repos/<owner>/<repo>` (or the host's
     authenticated equivalent) before declaring it dead — private repos 404 anonymously.
   - Cookie walls, bot checks, DOI indirection → cross-check with the runtime's web
     fetch or search tools that the resource (paper title, dataset, model card) exists.
   - Genuinely dead → keep the operator's original text plus a visible `⚠` marker. A
     plausible-looking wrong link is worse than a flagged broken one.
4. **Verify technical figures against a primary source.** A number worth adding to a
   note is worth deriving: fetch the actual artifact (a model's `config.json`, an API's
   published limits, a spec sheet) and recompute instead of quoting secondhand. Write
   the formula next to the result so the reader can re-derive it — e.g.
   `KV cache/token = 2 × n_layers × n_kv_heads × head_dim × bytes`, with each factor
   taken from the fetched config. Label anything not yet measured as an estimate and
   name the measurement that will replace it.
5. **Report.** Per-note change summary plus a URL verification table
   (`URL | result | action`) covering every checked link — including the ones that
   verified clean, so the operator sees the whole audit rather than only the failures.

## Hygiene

- Source notes may contain credentials (SSH passwords, tokens). Never copy them into an
  enriched note, a report, or any external service — propagate hostnames only.
- When the operator may have the note open in an editor, enrich it last and re-read it
  immediately before the write so live edits are not clobbered.

## Requirements

- `curl` — URL status checks
- `gh` — authenticated disambiguation of GitHub 404s

## Anti-patterns

- Declaring a link dead from an anonymous 404 → run the authenticated `gh api` rung first; private repos 404 anonymously.
- Replacing a broken URL with a plausible guess → keep the original text plus a `⚠` marker.
- Reverting linter-normalized frontmatter key order or spacing → treat the linter's last write as canonical and edit content only.
- Editing from a stale read while the operator has the note open → re-read the on-disk state immediately before the edit.
- Linking a person or term to a note that does not exist yet → search the vault first; enrichment never creates notes.
- Rewriting operator prose while restructuring it → move sentences intact; beautify structure, not voice.
