---
name: defuddle
description: Extract clean Markdown or metadata JSON from web articles and documentation pages using the Defuddle CLI, stripping navigation, ads, and boilerplate for a smaller, more focused result than a raw HTML fetch. Use when fetching a readable page (blog post, article, framework/library docs, GitHub README) for summarization or note-taking, pulling page metadata (title, author, description, domain), or converting a local HTML file to Markdown. Not for API endpoints or JSON responses (use a plain HTTP fetch) or JS-heavy SPAs that need a real browser (use a headless browser such as scrapling).
metadata:
  version: 1.0.0
---

# defuddle

## Overview

Defuddle (by kepano) extracts article content from web pages and returns clean Markdown. It strips away navigation, ads, sidebars, and boilerplate — producing smaller, more focused content than a raw HTML fetch. It is a strong default web-content extractor for readable pages.

## When to Use

- Fetching article, blog, or documentation content for summarization or note-taking
- Extracting metadata (title, description, author, domain) from a web page
- Converting a local HTML file to clean Markdown
- Any task where clean text matters more than raw HTML fidelity
- **Reading documentation pages (framework/library docs, GitHub READMEs) before answering questions about them** — this is the default move, not a fallback

**NOT for:**
- API endpoints or JSON responses — use a plain HTTP fetch
- Sites requiring authentication or JavaScript rendering — use a headless browser such as `scrapling`
- Cases where raw HTML structure is needed — use a plain HTTP fetch

## DO NOT shell out to `curl | python3 -c '...regex strip HTML...'`

This is the most common anti-pattern that bypasses defuddle. If you find yourself writing a one-liner that pipes `curl` into `python3` / `sed` / `awk` to strip HTML tags, **stop and use `defuddle parse <url> --markdown` instead**. Reasons:

- Defuddle's content extraction is far cleaner than tag stripping (drops nav/sidebar/ads, preserves heading structure, handles code blocks)
- Tag-stripping pipelines lose semantic structure (lists collapse, code becomes prose)
- Static pages should go through defuddle; bypassing it is a workflow-correction signal
- A `curl | python3` pipeline commonly trips a security scanner ('pipe to interpreter') and prompts for approval — friction the defuddle path avoids

## Process

### Token-efficient external-content ingestion

For static articles, docs, and readable web pages, use Defuddle as the first move because it converts directly to clean Markdown and avoids wasting context on raw HTML, navigation, ads, and manual cleanup.

Default sequence:
1. `defuddle parse <url> --markdown` or `--json` for metadata + content.
2. Confirm the extraction is non-empty and readable.

**Output contract:** defuddle extracts and returns clean Markdown (stdout or `-o file`) and/or JSON metadata. It does **not** persist anything — the calling orchestrator owns persistence and storage routing. One defuddle extraction = one logical item for the caller; do not collapse multiple sources into a single output.

1. **Fetch as markdown** (default for most tasks):
   ```bash
   defuddle parse <url> --markdown
   ```

2. **Fetch as JSON** when you need metadata + content together (e.g., passing structured data to a downstream pipeline):
   ```bash
   defuddle parse <url> --json
   ```
   The JSON object always contains these 8 fields (callers may rely on all keys being present):

   | Field | Source |
   | --- | --- |
   | `title` | `<title>` or `og:title` |
   | `author` | byline or `author` meta |
   | `description` | `meta[name=description]` or `og:description` |
   | `domain` | hostname extracted from URL |
   | `image` | `og:image` |
   | `language` | `lang` attribute or `Content-Language` header |
   | `published` | `article:published_time` or date byline |
   | `content` | cleaned article body as markdown |

   For metadata extraction, map these fields directly into note YAML/frontmatter. If a field is missing, leave it blank rather than guessing.

3. **Extract a single metadata field**:
   ```bash
   defuddle parse <url> -p title
   defuddle parse <url> -p description
   defuddle parse <url> -p domain
   ```

4. **Parse a local HTML file**:
   ```bash
   defuddle parse ./page.html --markdown
   ```

5. **Save output to file**:
   ```bash
   defuddle parse <url> --markdown -o output.md
   ```

6. **Specify preferred language** (BCP 47):
   ```bash
   defuddle parse <url> --markdown -l ko
   ```

7. **Check the result** — confirm the output is non-empty and materially cleaner than raw HTML. If the result is empty or poor quality (JS-heavy SPA), fall back to a headless browser such as `scrapling`.

See `references/cli-reference.md` for full option details.

## Requirements

- `defuddle` CLI (by kepano) available on `PATH` or via `${DEFUDDLE_BIN}`.
- Optional `scrapling` for the JS-heavy-SPA fallback.
- Optional `yt-dlp` for discovering watch URLs before per-URL extraction.

## Common Rationalizations

| Rationalization | Reality |
| --- | --- |
| "I'll fetch raw HTML and clean it manually later." | Defuddle handles the extraction and cleaning in one step — less token waste, cleaner result. |
| "The page is blank, so Defuddle is broken." | JS-heavy SPAs need a real browser. Fall back to `scrapling` instead. |
| "I don't need to check the output." | Extraction quality varies by site. A quick review prevents garbage downstream. |

## Red Flags

- A plain fetch or browser used for a standard readable page when `defuddle` would produce cleaner markdown
- `curl | sed`, `curl | awk`, or `curl | python` HTML-stripping pipelines for readable pages — this burns tokens and loses structure; use `defuddle parse <url> --markdown` first
- Empty extraction passed downstream without attempting the `scrapling` fallback
- Using `defuddle` for API endpoints or JSON responses
- Skipping `--markdown` flag (raw HTML is the default without it)

## Known Source Notes

- For YouTube, Defuddle CLI can return embed-only output for individual watch URLs. Discover watch URLs with a listing collector such as `yt-dlp` (channel/playlist listing pages can themselves return embed-only output), then run Defuddle per watch URL. If direct output is embed-only, the public `https://defuddle.md/<url>` gateway can return the full timestamped transcript.

## Verification

- [ ] `defuddle parse <url> --markdown` was used as the first extraction attempt for readable pages
- [ ] Output mode matches the downstream task (markdown for content, JSON for metadata)
- [ ] Extracted content is non-empty
- [ ] `scrapling` fallback used when defuddle returns empty on JS-heavy sites
