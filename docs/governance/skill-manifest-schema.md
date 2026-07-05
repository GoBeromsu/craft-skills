# Skill Manifest Schema v1

This freezes the portable skill-package contract consumed by repository validators and generated inventories. It is intentionally small: every checker should read package manifests or the generated aggregate, not infer ownership from prose tables.

## Domain ownership principles

- `oh-my-secondbrain` owns knowledge-management runtime surfaces: vault conventions, capture/retrieve/compile/wiki/lint semantics, MCP, `.oms`, host adapter install, and project-to-vault bridges.
- `craft-skills` owns portable research and development craft that is reusable without a private vault, personal accounts, private paths, or runtime secrets.
- `bstack` owns private personal operations: life workflows, publishing, runtime operations, account/OAuth glue, personal automation, and private knowledge-zone mirrors.
- `agent-skills` is not an ambiguous historical owner. It is either a public starter shell or a generated public-safe export.

All examples in this document use placeholders. Do not put private account names, absolute user paths, vault names, tokens, or machine-specific hostnames in craft-skills manifests or docs.

## Package manifest fields

Each package manifest is schema version `1` and describes exactly one package surface: a skill, area, adapter wrapper, runtime hook, or command.

| Field | Required | Type | Contract |
|---|---:|---|---|
| `schema_version` | yes | integer | Must be `1` for this contract. |
| `id` | yes | string | Stable package id. Use lowercase path-like or dotted ids; it must not depend on a local filesystem path. |
| `name` | yes | string | Human-readable package name. For skills, this normally matches the package directory/frontmatter name. |
| `kind` | yes | enum | One of `leaf`, `thick`, `area`, `adapter-wrapper`, `runtime-hook`, `command`. |
| `lifecycle` | yes | enum | One of `proposed`, `admitted`, `active`, `deprecated`, `archived`, `deleted`. |
| `version` | yes | string | Semver for owned packages, or the upstream version/tag when the package is externally owned. |
| `owner_repo` | yes | enum/string | Canonical owner repository, normally `bstack`, `craft-skills`, `oh-my-secondbrain`, `agent-skills`, or `external`. |
| `owner_domain` | yes | string | Short domain label such as `research-development`, `knowledge-management`, `personal-operations`, or `public-export`. |
| `visibility` | yes | enum | One of `public`, `private`, `mixed`. Public/craft packages must pass strict private-data hygiene. |
| `compatibility` | yes | array<string> | Runtime/API surfaces expected to expose the package, for example `claude-code`, `codex`, `hermes`, `mcp`, or `cli`. Empty only for deleted packages. |
| `provenance` | yes | object | Supply-chain and migration origin metadata. See below. |
| `replacement_for` | no | array<string> | Prior ids this package replaces, including historical ids such as `agent-skills:<id>`. |
| `replaced_by` | no | string or array<string> or null | Replacement package id(s) for deprecated, archived, or deleted packages. Active packages normally use `null` or omit it. |
| `children` | no | array<string> | Child package ids. Required as an empty array for `leaf`, `runtime-hook`, and `command`. |
| `adapters` | no | array<object> or object | Host adapter declarations and intentional omissions. |
| `validation_profile` | yes | object | Check profile consumed by validators. See below. |

### `kind`

- `leaf`: directly invokable package with no child routing responsibility.
- `thick`: parent skill that contains child recipes loaded on demand; child recipes are not separate top-level discovered commands unless separately manifested.
- `area`: routing package for two or more sibling leaves; must declare children and resolver/routing coverage.
- `adapter-wrapper`: host-specific wrapper around an owned package, such as a Claude/Codex/Hermes adapter.
- `runtime-hook`: deterministic hook or guard installed into a host runtime.
- `command`: CLI or slash-command style surface whose parity must be checked against the package manifest.

### `lifecycle`

- `proposed`: drafted but not admitted to public/runtime inventories.
- `admitted`: accepted into the repo but not yet active in all declared adapters.
- `active`: canonical live package.
- `deprecated`: still present but callers should move to `replaced_by`.
- `archived`: retained as history/tombstone and not loaded by active runtimes.
- `deleted`: removed from source; only migration/provenance records remain.

### `provenance`

Required shape:

```yaml
provenance:
  upstream: null              # or "owner/repo:path-or-package"
  commit: null                # commit, tag, or immutable release id when known
  license: null               # SPDX id or documented upstream license
  absorbed_from: []           # previous package ids, e.g. ["agent-skills:old-id"]
```

Use `null` when a value is genuinely not applicable or unknown. Do not omit the key to hide unknown provenance.

### `adapters`

Recommended shape:

```yaml
adapters:
  - runtime: claude-code
    surface: plugin-skill
    status: generated          # generated | hand-written | omitted
    reason: null               # required when status is omitted
  - runtime: codex
    surface: instruction-file
    status: generated
    reason: null
```

A package may use an object keyed by runtime if the generator prefers that format. Validators must normalize both forms before checking parity.

### `validation_profile`

Recommended minimum keys:

```yaml
validation_profile:
  topology: leaf               # leaf | thick | area | adapter-wrapper | runtime-hook | command
  discovery_parity: strict     # strict | declared-omissions | skip
  adapter_parity: strict       # strict | declared-omissions | skip
  provenance_license: strict   # strict | warn | skip
  private_data_hygiene: strict # strict | warn | skip
  deprecation: strict          # strict | warn | skip
  routing_eval: smoke          # smoke | full | skip
  install_doctor: package      # package | runtime | skip
```

The profile is declarative. A checker may fail fast when a package asks for `skip` without a documented reason in the package manifest.

## Minimal YAML example

```yaml
schema_version: 1
id: craft-skills/example-skill
name: example-skill
kind: leaf
lifecycle: active
version: 1.0.0
owner_repo: craft-skills
owner_domain: research-development
visibility: public
compatibility:
  - claude-code
  - codex
provenance:
  upstream: null
  commit: null
  license: MIT
  absorbed_from: []
replacement_for: []
replaced_by: null
children: []
adapters:
  - runtime: claude-code
    surface: plugin-skill
    status: generated
    reason: null
  - runtime: codex
    surface: instruction-file
    status: generated
    reason: null
validation_profile:
  topology: leaf
  discovery_parity: strict
  adapter_parity: strict
  provenance_license: strict
  private_data_hygiene: strict
  deprecation: strict
  routing_eval: smoke
  install_doctor: package
```

## Generated aggregate format

Generators may produce a repository-level aggregate for fast validators. The aggregate is generated output and must not be hand-edited.

- Canonical filename: `skill-manifest.aggregate.json` unless a repo-specific generator documents another generated path.
- First key: `generated` with `true`.
- Include generator name/version and source manifest paths.
- Preserve package manifest objects without dropping unknown future keys.
- Sort packages by stable `id`.
- Any manual edit must fail validation; update source manifests and regenerate instead.

JSON Schema summary:

```json
{
  "type": "object",
  "required": ["schema_version", "generated", "generator", "source_manifests", "packages"],
  "properties": {
    "schema_version": { "const": 1 },
    "generated": { "const": true },
    "generator": {
      "type": "object",
      "required": ["name", "version"],
      "properties": {
        "name": { "type": "string" },
        "version": { "type": "string" }
      }
    },
    "source_manifests": {
      "type": "array",
      "items": { "type": "string" },
      "uniqueItems": true
    },
    "packages": {
      "type": "array",
      "items": { "$ref": "#/definitions/package" }
    }
  },
  "definitions": {
    "package": {
      "type": "object",
      "required": [
        "schema_version",
        "id",
        "name",
        "kind",
        "lifecycle",
        "version",
        "owner_repo",
        "owner_domain",
        "visibility",
        "compatibility",
        "provenance",
        "validation_profile"
      ]
    }
  }
}
```

## Freeze declaration

This is the v1 contract freeze for package-boundary validation. The following eight checker classes must consume only manifest v1 fields or the generated aggregate derived from them:

1. Topology checker: distinguishes `leaf`, `thick`, `area`, adapter wrappers, hooks, and commands.
2. Discovery parity checker: compares manifests with README, AGENTS, plugin manifests, marketplace manifests, and resolvers.
3. Adapter parity checker: verifies declared runtime surfaces and documented omissions.
4. Provenance/license checker: verifies upstream, commit/tag, license, and absorbed-from history.
5. Private-data hygiene checker: rejects private paths, secrets, account ids, vault-specific content, and `.env` leakage where the manifest requires strict hygiene.
6. Deprecation checker: requires replacements or tombstones and prevents active resolvers from pointing at archive-only packages.
7. Routing-eval checker: confirms trigger phrases route to the declared owner and reject near-neighbor owners.
8. Install-doctor checker: verifies installed runtime config points at the intended package/checkout/version.

Checkers must not rely on hand-maintained prose inventories as source of truth. Prose docs may explain the contract, but machine decisions come from manifests and generated aggregates.
