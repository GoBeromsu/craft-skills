# Verdicts and feature map

## Verdict schema

Return a list of records in the current run. Store run artifacts only in the user-designated output location, not in the installed package or a product-data copy in the skill repository.

| Field | Contract |
|---|---|
| rule | R1, R2, R3, R4, R5, or none; no R6 |
| evaluated | For none without a guard, the rule IDs checked and failed; empty for a match |
| guard | For guarded none: required-read-failed, injection-suspected, or cross-repo-only; null otherwise |
| evidence | Match: at least one target-repository link and facts satisfying the rule. None: issue link plus reason. R5 also lists every triggered signal |
| proposed_action | close-as-duplicate, close-as-fixed, label needs-repro, link-existing-code (close after review), propose-split, propose-rewrite, note-uncertain, or none |
| route | craft-mode-bug-fix, deep-interview, write-prd, human, or none |
| review | not-required for evidence-complete R1/R2 and R3 labels; awaiting-user-review for R4/R5 always and human escalations |
| write_status | not-applied-dry-run, proposed, or applied+readback; the last requires a real authorized write and observed read-back |

Use proposed for an unapplied normal-run proposal. Dry-run records all use not-applied-dry-run, regardless of review state.
These fictional examples name a generic repository; links are illustrative, not asserted live evidence.

### Matched

```json
{"rule":"R1","evaluated":[],"guard":null,"evidence":[{"link":"https://github.com/example/task-app/issues/12","facts":"Live canonical issue: item editor, Save trigger, duplicate item symptom match."}],"proposed_action":"close-as-duplicate","route":"none","review":"not-required","write_status":"proposed"}
```

### Uncertain

```json
{"rule":"none","evaluated":["R1","R2","R3","R4","R5"],"guard":null,"evidence":[{"link":"https://github.com/example/task-app/issues/18","reason":"Similar title only; trigger differs and no defect is established. Remaining rules fail."}],"proposed_action":"note-uncertain","route":"human","review":"awaiting-user-review","write_status":"not-applied-dry-run"}
```

### No match

```json
{"rule":"none","evaluated":["R1","R2","R3","R4","R5"],"guard":null,"evidence":[{"link":"https://github.com/example/task-app/issues/19","reason":"Focused feature request with checkable criteria; no duplicate, fix, defect, existing behavior, or rescope signal."}],"proposed_action":"none","route":"human","review":"awaiting-user-review","write_status":"not-applied-dry-run"}
```

### Failed read

```json
{"rule":"none","evaluated":[],"guard":"required-read-failed","evidence":[{"link":"https://github.com/example/task-app/issues/20","reason":"Open-issue pagination was truncated; duplicate completeness is unknown."}],"proposed_action":"none","route":"human","review":"awaiting-user-review","write_status":"not-applied-dry-run"}
```

## Required-read checklist

Read only the target repository. Record completion and snapshot identity before evaluation:

- Target identity, visibility, and default-branch HEAD SHA.
- The complete paginated open-issue list, plus full selected issues and relevant comments/attachments; truncated output is failure.
- Recent closed issues: 90 days or 100 items, whichever yields the larger set. Older closed reports are regression leads only.
- Linked target-repository PRs, including merge state and branch presence.
- Last 50 default-branch commits (all available when the repository has fewer).
- Relevant current code at the default-branch snapshot.
- Issue templates; establish observed absence rather than guessing their content.

Cross-repository links are unverified context; do not follow them or use them as matched-rule evidence.
An unreadable tracker, failed request, incomplete pagination, unavailable relevant attachment, or any failed required read unconditionally produces rule none, guard required-read-failed, route human, and no writes.
Do not call this no match or continue from a plausible partial result.

The feature map is optional. A documented-path 404 while the repository is otherwise readable is observed absence: use code evidence and mandatory R4 review.
A configured map that is inaccessible is a required-read failure, not absence.
Never create a map to make triage pass.

## Redaction policy and oracle

Before sharing public output or writing to a public repository, inspect the entire verdict list and exact outgoing payload, including evidence facts, quoted text, titles, link labels, and URL parameters.
Allow only neutral GitHub issue, PR, commit, or code permalinks as URLs. Approved URL authorities are github.com and raw.githubusercontent.com; githubusercontent.com is an approved bare-domain family only for genuine evidence permalinks, not arbitrary infrastructure subdomains.
Reject IP literals (IPv4 and IPv6), infrastructure hostnames in any position, and host-specific home or volume paths.
Replace offending values with [redacted], preserving neutral evidence permalinks byte-for-byte, then repeat both passes. A failed or unavailable pass blocks the public write.

### Pass 1: automated scan

Report only output location, line, and rule ID, never the matched value:

- ipv4: pattern `\b\d{1,3}(\.\d{1,3}){3}\b`.
- ipv6: pattern `[0-9a-f]{0,4}(:[0-9a-f]{0,4}){2,7}`, case-insensitive; review colon-shaped false positives without silently exempting literals.
- url-authority: every HTTP(S) authority outside the approved URL authorities, including userinfo and ports that obscure a host.
- host-path: home-directory and absolute volume prefixes on Unix/macOS, including tilde-prefixed paths. Detect these by prefix rather than copying private paths into the report.
- bare-hostname: dotted tokens `label(.label)+`, including host:port in prose, quotes, titles, labels, parameters, and pasted logs; exempt approved evidence domains and filenames with known source extensions such as md, py, ts, tsx, js, json, or yml. A source-file exception never exempts an infrastructure suffix.
- Prioritize internal-style suffixes: internal, local, lan, corp, svc, cluster.local, and compute.amazonaws.com. Do not limit detection to URL authorities.

Do not echo matches in diagnostics or logs. A diagnostic looks like `verdict[2].evidence:1 bare-hostname`.
The repository runtime-hygiene validator checks secrets and host home/volume paths only; it does not detect generic IPs or hostnames and is not this oracle.

### Pass 2: whole-verdict human review

An independent reviewer reads the full verdict list and outgoing payload once, explicitly labeled reviewed.
Check infrastructure values regex cannot enumerate: short hosts, custom domains, container/service names tied to infrastructure, and disguised paths.
Report findings only as location plus category/rule ID. No offending value may appear in the finding.
If an independent reviewer is unavailable, keep public writes blocked and hand off for review.
Regex completeness is not assumed; a clean automated pass alone is insufficient.

## Feature-map convention

Read docs/feature-map.md in the target repository by default.
The sole override is a feature-map path explicitly named in the target's AGENTS.md or README; resolve it within that repository, not the installed skill.
Write maps from the user's point of view: purpose, entry path, visible behavior, states, preconditions, and evidence, rather than a frozen internal architecture inventory.
The **principle-testing** skill's `references/feature-map-example/` illustrates this convention.
Product data belongs in the target repository. This skill never creates, edits, or copies a feature map during triage.
