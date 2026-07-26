---
name: obsidian-markdown
description: Create and edit Obsidian Flavored Markdown — wikilinks, embeds, callouts, properties, tags, comments, math, and Mermaid fences — following a compact note house style: `##`/`####` headings, nested tab-indented bullets, no blank lines in the body, colon-style phrasing, body dates as `[[YYYY-MM-DD]]`, person names as `[[Name]]`, and external URLs as inline `[text](url)` (not footnotes). Use whenever writing or formatting a `.md` note for an Obsidian vault, or when a task mentions wikilinks, callouts, frontmatter, tags, or embeds. Not for `.base` data views (use obsidian-bases) or `.canvas` files (use obsidian-canvas).
metadata:
  version: 1.1.0
---

# obsidian-markdown

## Overview

Create and edit valid Obsidian Flavored Markdown (OFM) that also follows a compact note house style.

## Vault Access

Use the `obsidian-cli` skill for all note creation, edit, search, and property mutation inside the vault. Do not shell out to raw `cat`/`sed` on vault paths. See the `obsidian-cli` SKILL.md for the command surface and required preconditions (Obsidian must be running).

OFM extends CommonMark and GFM with wikilinks, embeds, callouts, properties, comments, and other syntax; this skill covers those extensions and bakes a compact note house style (heading, spacing, note-style, nested bullets, date/people wikilinks, and inline web links) into every note it produces. Standard Markdown (bold, italic, code blocks, tables) is assumed knowledge.

## When to Use

- Creating or editing any `.md` file that will live inside an Obsidian vault.
- The user asks for wikilinks, embeds, callouts, frontmatter, tags, comments, highlights, or Mermaid diagrams.
- The user writes in Korean and mentions "옵시디언 노트", "콜아웃", "프론트매터", "태그", "임베드".

**NOT for:**
- Plain GitHub or generic Markdown where OFM syntax would render as raw text.
- SKILL.md or other agent-facing meta-documentation -- those follow the agent-skills spec (which uses an H1 title) and are exempt from the note-formatting rules below.

## Workflow

1. **Add frontmatter** with properties (title, tags, aliases) at the top of the file. See [PROPERTIES.md](PROPERTIES.md) for all property types.
2. **Write content** using standard Markdown for structure, plus the OFM syntax below.
3. **Link related notes** using wikilinks (`[[Note]]`) for internal vault connections, and standard Markdown links for external URLs.
4. **Embed content** from other notes, images, or PDFs using `![[embed]]`. See [EMBEDS.md](EMBEDS.md).
5. **Add callouts** for highlighted information using `> [!type]`. See [CALLOUTS.md](CALLOUTS.md).
6. **Check formatting against the Formatting Rules below** -- main sections default `##`, subsections `####`, hyphen bullets with tabs and nested hierarchy preferred, no H1/H5+, no bullet past depth 3, no blank lines in body structure, note-style phrasing, body dates as `[[YYYY-MM-DD]]`, person names as `[[Name]]`, and external URLs as inline `[text](url)` (not footnotes). Fix before moving on.
7. **Verify** the note renders correctly in Obsidian's reading view.

> When choosing between wikilinks and Markdown links: use `[[wikilinks]]` for notes within the vault (Obsidian tracks renames automatically) and `[text](url)` for external URLs only.

## Formatting Rules

Apply to every note created or edited under this skill. These rules override whatever example headings, spacing, link, or bullet formats appear in upstream OFM references.

### Rule 1: Headings default to `##` for main sections and `####` for subsections

Use the heading level specified by the user for main sections. If no heading level is specified, use `##` (H2) as the default. For subsections inside main sections, use `####` (H4). Avoid `###` unless the user explicitly asks for a three-level outline. Never use `#` (H1) and never use `#####`/`######` (H5/H6).

- **Why no H1:** The note title lives in the filename and the frontmatter `title` property -- an H1 inside the body duplicates it and breaks outline renderers that treat the filename as the document title.
- **Why default `##` / `####`:** This house style treats H2 as the main note outline and H4 as local subsection labels.
- **Why no H5+:** If a section needs to nest past H4, the section is doing too much -- split it into sibling sections, promote it to its own note, or flatten the hierarchy.

```markdown
# Project Alpha            <- BAD: H1 duplicates the title
## Project Alpha           <- GOOD: default main section
#### Tasks                 <- GOOD: subsection inside a main section
### Backend                <- AVOID unless explicitly requested
##### API routes           <- BAD: H5 -- restructure instead
```

### Rule 2: Bullets use hyphen markers and tab indentation

Use a single hyphen followed by one space (`- `) for every bullet point. For nested bullets, indent each level with one tab character. Maintain consistent indentation for bullets at the same level.

Top-level bullet counts as depth 1. A bullet indented once is depth 2. Indented twice is depth 3. A fourth level is not allowed -- promote it to a subsection, a separate list, or note-style line.
Prefer nested bullets when an item has sub-context (members under a group, steps under a task, caveats under a rule) instead of flattening siblings into one long list.

```markdown
- Phase one                 <- depth 1 (GOOD)
	- Backend                 <- depth 2 (GOOD)
		- Auth rewrite          <- depth 3 (GOOD, deepest allowed)
			- JWT rotation        <- depth 4 (BAD: flatten or promote)
```

Fix by promoting:

```markdown
- Phase one
	- Backend
		- Auth rewrite: see details
#### Auth rewrite details
- JWT rotation
- Session invalidation
```

### Rule 3: No blank lines inside the note body structure

Do not insert blank lines before or after headings. Do not insert blank lines between different sections, subsections, or bullet lists. Keep the body compact and note-like.

```markdown
## Main Section
Content of the main section.
#### Subsection
- Bullet point 1
- Bullet point 2
	- Nested bullet point
## Another Main Section
More content here.
```

### Rule 4: Prefer note-style phrasing over prose

Use concise note-style lines instead of full-sentence essay prose. Use colons (`:`) for definitions, labels, and readable key-value phrasing.

```markdown
## Concept
Definition: short explanation
Use case: when the idea applies
- Implication: concise note
```

### Rule 5: Preserve source text unless formatting is requested

When the task is to format given text, do not add additional content or modify the source meaning. Only apply the required markdown formatting, heading levels, bullet indentation, date/people wikilinks, and link formatting.

### Rule 6: Use inline markdown links for web URLs

When adding web links in Obsidian notes, use standard inline markdown links: `[label](https://example.com)`.
Do not prefer footnotes (`[^1]` / `[^1]: ...`) for ordinary web URLs — keep the destination readable next to the claim.
If the user asks for a `References` section, use heading `## References` and the same `[label](url)` form there.

```markdown
Demo: [Solar Open 2 beta](https://open2-beta.upstage.ai/)
Folder: [전문가사용자평가](https://drive.google.com/drive/folders/…)
```

YAML frontmatter is the exception: keep YAML-standard spaces for arrays and nested properties.

### Rule 7: Wrap body dates as date wikilinks

In Markdown body text, wrap calendar dates as Obsidian wikilinks: `[[YYYY-MM-DD]]`.
Keep YAML frontmatter date fields as plain `YYYY-MM-DD` scalars so typed metadata stays valid.

```markdown
- 마감: [[2026-07-27]] (월) 13:00
- 테스트 기간: 지금 ~ [[2026-07-27]] (월) 13:00
```

```yaml
date_created: 2026-07-26
date_modified: 2026-07-26
```

### Rule 8: Wrap person names as people wikilinks

When the body refers to a person, wrap the name as a wikilink: `[[고범수]]`, `[[장현서]]`.
Prefer the People-note filename when it is known; use a first-mention wikilink rather than bare plain text.
Creating or enriching CRM People notes is out of scope for this skill — hand that off to the people / make-people workflow when the operator asks for a People note.

## Internal Links (Wikilinks)

```markdown
[[Note Name]]                          Link to note
[[Note Name|Display Text]]             Custom display text
[[Note Name#Heading]]                  Link to heading
[[Note Name#^block-id]]                Link to block
[[#Heading in same note]]              Same-note heading link
```

Define a block ID by appending `^block-id` to any paragraph:

```markdown
This paragraph can be linked to. ^my-block-id
```

For lists and quotes, place the block ID on a separate line after the block:

```markdown
> A quote block

^quote-id
```

## Embeds

Prefix any wikilink with `!` to embed its content inline:

```markdown
![[Note Name]]                         Embed full note
![[Note Name#Heading]]                 Embed section
![[image.png]]                         Embed image
![[image.png|300]]                     Embed image with width
![[document.pdf#page=3]]               Embed PDF page
```

See [EMBEDS.md](EMBEDS.md) for audio, video, search embeds, and external images.

## Callouts

```markdown
> [!note]
> Basic callout.

> [!warning] Custom Title
> Callout with a custom title.

> [!faq]- Collapsed by default
> Foldable callout (- collapsed, + expanded).
```

Common types: `note`, `tip`, `warning`, `info`, `example`, `quote`, `bug`, `danger`, `success`, `failure`, `question`, `abstract`, `todo`.

See [CALLOUTS.md](CALLOUTS.md) for the full list with aliases, nesting, and custom CSS callouts.

## Properties (Frontmatter)

```yaml
---
title: My Note
date: 2024-01-15
tags:
  - project
  - active
aliases:
  - Alternative Name
cssclasses:
  - custom-class
---
```

Default properties: `tags` (searchable labels), `aliases` (alternative note names for link suggestions), `cssclasses` (CSS classes for styling). See [PROPERTIES.md](PROPERTIES.md) for all property types, tag syntax rules, and advanced usage.

## Tags

```markdown
#tag                    Inline tag
#nested/tag             Nested tag with hierarchy
```

Tags can contain letters, numbers (not first character), underscores, hyphens, and forward slashes. Tags can also be defined in frontmatter under the `tags` property.

## Comments

```markdown
This is visible %%but this is hidden%% text.

%%
This entire block is hidden in reading view.
%%
```

## Highlight

```markdown
==Highlighted text==
```

## Math (LaTeX)

```markdown
Inline: $e^{i\pi} + 1 = 0$

Block:
$$
\frac{a}{b} = c
$$
```

## Diagrams (Mermaid)

````markdown
```mermaid
graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Do this]
    B -->|No| D[Do that]
```
````

To link Mermaid nodes to Obsidian notes, add `class NodeName internal-link;`.

## Footnotes

Footnote syntax exists in OFM, but this house style does not use it for web links (see Rule 6).
Reserve footnotes only when the operator explicitly asks for them.

```markdown
Text with a footnote[^1].

[^1]: Footnote content.

Inline footnote.^[This is inline.]
```

## Complete Example

This example obeys the house style: main sections are `##`, subsections are `####`, nested bullets use tabs, body dates and people are wikilinked, the body has no blank lines between headings/sections/lists, and web links are inline markdown.

````markdown
---
title: Project Alpha
date: 2024-01-15
tags:
  - project
  - active
status: in-progress
---
## Summary
- Aim: improve [[workflow]] with modern techniques
	- Owner: [[고범수]]
	- Deadline: [[2024-01-30]]
	- Source: [project brief](https://example.com/project-alpha)
## Tasks
- [x] Initial planning
- [ ] Development phase
	- [ ] Backend implementation
	- [ ] Frontend design
#### Backend
- Auth service
	- JWT rotation
	- Session store
#### Frontend
- Component library
- Routing rewrite
## Notes
Algorithm: $O(n \log n)$ sorting
Reference: [[Algorithm Notes#Sorting]]
Embed: ![[Architecture Diagram.png|600]]
Reviewed: [[Meeting Notes 2024-01-10#Decisions]]
````

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll use H1 for the title so it's obvious what the note is about." | The title lives in the filename and frontmatter `title` property. An H1 duplicates them and breaks outline renderers that already treat the filename as the document title. |
| "Just one more indent level -- the structure really is that deep." | Past depth 3 readers lose the outline. Promote the content to a sub-heading, a separate list, or prose. If the data truly has 4+ axes, it's a table, not a list. |
| "This note is a meta-doc, so H5/H6 is fine." | If the note needs H5, it needs to be split. Nothing in an Obsidian note renders better at H5 than it does as its own sibling H3/H4 section. |
| "The upstream kepano example used deeper nesting, so it's fine to copy." | Upstream is a syntax reference, not a style guide. These rules override any nesting shown in references. |
| "Two-space indentation renders fine in Markdown, so it is fine for Obsidian notes." | Rendering is not the only criterion. These note bodies use literal tabs for nested bullets so the source matches Obsidian's outliner behavior. |
| "Blank lines make Markdown easier to read." | This house style is compact: no blank lines before/after headings or between section/list blocks inside the body. |
| "A normal paragraph sounds more polished." | Prefer note-style fragments and colon labels over essay prose unless the user explicitly requests narrative writing. |
| "I'll hide web links in footnotes." | Use inline `[label](url)` for web links; footnotes are not the house default. |
| "Bare dates and bare names are fine in the body." | Body dates are `[[YYYY-MM-DD]]`; person names are `[[Name]]` wikilinks. |
| "Flat bullet lists are cleaner." | Prefer nested bullets when items have sub-context; keep depth ≤ 3. |

## Red Flags

- A leading `# ` line inside the body of an Obsidian note (H1).
- Any `##### ` or `###### ` line (H5/H6).
- Any body bullet indented with spaces instead of literal tabs. YAML frontmatter is exempt.
- A body bullet indented three or more tabs (`^\t{3,}- `), which is depth 4+ and should be promoted or flattened.
- Main sections using `###` when the user did not explicitly request that level.
- Blank lines before or after headings, or between sections/lists in the note body.
- Essay-style full sentences where note-style colon phrasing would preserve the source meaning.
- Footnotes (`[^n]`) used for ordinary web URLs when inline `[label](url)` would work.
- Bare ISO dates in the body (`2026-07-27`) instead of `[[2026-07-27]]`.
- Bare person names in the body when a `[[Name]]` wikilink is available.
- Frontmatter `title` plus an H1 restating the same string.

## Verification

- [ ] Frontmatter is present and at least one property is set.
- [ ] `grep -nE '^# ' <note>` returns zero matches (no H1 in body).
- [ ] `grep -nE '^#{5,} ' <note>` returns zero matches (no H5+).
- [ ] Main sections use the user-specified heading level, defaulting to `##`.
- [ ] Subsections inside main sections use `####` unless the user explicitly requested a different outline.
- [ ] `awk 'BEGIN{fm=0} NR==1&&$0=="---"{fm=1;next} fm&&$0=="---"{fm=0;next} !fm && /^ +-/ {print FNR ":" $0}' <note>` returns zero matches (no space-indented body bullets).
- [ ] `grep -nP '^\t{3,}- ' <note>` returns zero matches (no bullet past depth 3 when using tab indentation).
- [ ] Body structure has no blank lines before/after headings or between section/list blocks.
- [ ] Note text uses concise note-style phrasing and colons where appropriate.
- [ ] Web links use inline `[label](url)`; footnotes are absent unless the operator explicitly requested them.
- [ ] Body calendar dates use `[[YYYY-MM-DD]]`; YAML date fields stay plain `YYYY-MM-DD`.
- [ ] Person names in the body use `[[Name]]` wikilinks on first mention.
- [ ] Hierarchical content prefers nested tab bullets (depth ≤ 3) over flat lists.
- [ ] Every wikilink resolves to an existing note or is explicitly intended as a placeholder.
- [ ] Callouts use a valid type from [CALLOUTS.md](CALLOUTS.md).
- [ ] The note renders in Obsidian reading view without broken embeds or unrendered syntax.

## References

- [Obsidian Flavored Markdown](https://help.obsidian.md/obsidian-flavored-markdown)
- [Internal links](https://help.obsidian.md/links)
- [Embed files](https://help.obsidian.md/embeds)
- [Callouts](https://help.obsidian.md/callouts)
- [Properties](https://help.obsidian.md/properties)
