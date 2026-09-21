# Markdown coordination

## Native owner

Discover the official `obsidian-markdown` skill by package identity before creating or editing Obsidian Markdown.
That skill owns Obsidian Flavored Markdown syntax, wikilinks, embeds, callouts, properties, tags, comments, highlights, math, and its field/type rules.
It also owns its examples and format validation; do not copy, restate, or override those manuals here.
If the native skill is unavailable, report the format capability gap instead of substituting generic Markdown rules or a third-party writer.

This local reference owns only target-vault authorization and destination readback that compose with the native package.
The target-vault/OMS owner or personal policy owns note meaning, filing, template selection, placement, provenance requirements, and house style; load that owner rather than inventing a local template or placement rule.

## Target-vault and native-surface authorization

Before a mutation, resolve the exact `${OBSIDIAN_VAULT_PATH}`, vault-relative source note, intended target, and requested effect.
Resolve the target-vault policy owner and native Obsidian mutation surface, including required provenance and protected content, before invoking a writer.
A native writer, folder classification, or format recipe does not grant authority to change the vault.
Reuse matching task-bound authority without demanding redundant consent.
When the vault, authority, native capability, or requested target is absent or ambiguous, keep the operation read-only and report the specific gap.
Do not use raw filesystem writes or an unrelated third-party CLI to bypass the native surface.

## Non-Markdown targets and destination readback

Keep the file extension for non-Markdown targets, including `.canvas`, `.png`, and `.pdf`, as required by [Obsidian's internal-link documentation](https://help.obsidian.md/links).
For example, use `[[My canvas.canvas]]` or `[[My canvas.canvas|Overview]]` to target the Canvas, not `[[My canvas]]`.
A bare same-stem link may reach a Markdown note or remain unresolved; it does not prove that the intended non-Markdown file was reached.
Include the vault-relative folder path when needed to distinguish same-named files.
Use native `obsidian-markdown` for embed syntax and the existing [Canvas renderer guidance](markdown-embeds.md#embed-canvas) for its rendering limitation.

After a link change, read back the source note and check the changed destination in that note's context.
Through the supported native app surface, use `app.metadataCache.getFirstLinkpathDest(linkpath, sourcePath)` and compare the returned file's `path` with the exact intended vault-relative target path.
Supply the link's file destination as `linkpath`, without wikilink delimiters, display text, or heading/block subpath, and the containing note's vault-relative path as `sourcePath`.
A null result is unresolved; a different path is a wrong destination even when the link is not listed as unresolved.
Do not require the whole note's `unresolvedLinks` to be empty: unrelated links and intentional date/person placeholders do not decide whether this destination is correct.
If the app or indexed result is unavailable, report destination resolution as unverified rather than treating a filesystem match as runtime proof.
Check rendered embeds separately; successful destination resolution does not prove their visual content.

## Composition boundaries

Compose a note mutation from the native `obsidian-cli` skill's supported CLI surface when CLI is the selected owner, or from an independently authorized native OMS, together with the native `obsidian-markdown` format owner, this target-vault boundary, and any applicable personal policy.
Use native `json-canvas` for Canvas graph structure and native `obsidian-bases` for `.base` structure; this reference does not define their fields, types, templates, placement, or schemas.
Use the package's plugin, renderer, and Sync references only when those concerns genuinely compose with the note operation.

## Verification

- [ ] The native `obsidian-markdown` package was discovered by identity and loaded for format decisions.
- [ ] The exact vault-relative target and authorized effect were resolved before mutation.
- [ ] The source note was read back after the change.
- [ ] A non-Markdown destination was resolved in its source-note context and matched the intended path, or the gap was reported.
- [ ] Rendered embeds were checked separately from link resolution, or the renderer check was reported as unavailable.
- [ ] Unrelated content, metadata, provenance, and protected content were preserved.
