# Bases coordination

## Native owner

Discover the official `obsidian-bases` skill by package identity before creating or editing a `.base` file or an embedded `base` block.
That skill owns the Bases file format, YAML schema, filters, formulas, properties, functions, summaries, view types, fields, and examples.
It also owns schema validation, view options, and version-specific format guidance; the target-vault/OMS owner or personal policy owns template selection and placement. Do not copy, restate, or override those manuals here.
If the native skill is unavailable, report the Bases capability gap instead of inventing YAML, formulas, or a fallback parser.

This local reference owns only target-vault authorization and app/rendering coordination that the native format owner does not establish.
Use [the target-vault boundary](markdown.md#target-vault-and-native-surface-authorization) before any vault mutation.

## App and renderer coordination

Resolve the exact vault-relative `.base` path or note containing the embedded block before opening or changing it.
Use the native `obsidian-bases` recipe to produce the artifact, then inspect the actual rendered view in the target Obsidian app when rendering evidence is required.
A valid native-format artifact or a parsed YAML document does not prove that the target app loaded the intended file, matched the expected notes, or rendered the requested view.
If the app, target vault, renderer, or relevant community plugin is unavailable, report that rendering or result evidence as unverified rather than inferring it from source text.
Treat an empty or unexpected rendered result as an app/index/filter outcome to investigate through the native package and supported app surface, not as permission to rewrite the schema locally.

Embedded `base` blocks compose native `obsidian-markdown` note handling with native `obsidian-bases` format handling.
Do not define a second local schema, field catalog, formula catalog, view layout, placement rule, template, or CLI operation here.

## Verification

- [ ] The native `obsidian-bases` package was discovered by identity and loaded for format decisions.
- [ ] The exact vault-relative target and authorized effect were resolved before mutation.
- [ ] The target artifact or containing note was read back after any change.
- [ ] The actual app-rendered view or supported result readback was checked, or its unavailability was reported.
- [ ] Renderer and community-plugin requirements were treated as runtime facts, not inferred from YAML.
