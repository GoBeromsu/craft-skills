# Embeds Reference

## Native owners

Discover the official `obsidian-markdown` skill for Obsidian embed syntax and the official `json-canvas` skill for `.canvas` structure and graph edits. Those native skills own their formats, schemas, examples, and validation; this reference does not reproduce them.

## Embed Canvas

The [official embed documentation](https://help.obsidian.md/embeds) states that embedded canvases show shapes only, not text inside cards. Open the Canvas in the target app to inspect its complete content; do not treat the documented shape-only result as a broken destination or promise readable card text in the embed.

Use [Markdown's exact non-Markdown destination identity and readback owner](markdown.md#non-markdown-targets-and-destination-readback) for the source note's context. Preserve the source note's vault-relative path, resolve the intended `.canvas` destination through the supported native app surface, and compare the returned identity with the exact target path. Filesystem existence or successful link resolution alone is not rendering evidence.

Check the actual target app and renderer separately after destination readback. If the app, index, renderer, or target vault is unavailable, report the Canvas rendering/readback leg as unverified rather than inferring it from source text. Do not define a local Canvas schema or edit procedure here.

## Verification

- [ ] The native `obsidian-markdown` and `json-canvas` skills were discovered by identity.
- [ ] Source-context destination identity and exact readback used [`markdown.md`](markdown.md#non-markdown-targets-and-destination-readback).
- [ ] Actual Canvas rendering was checked separately, or its unavailable leg was reported.
