# Protected routing skill PR approval

Use this reference when a skill-library change touches runtime authority boundaries rather than ordinary prose.

## Trigger

The skill update mentions any of these classes:
- Bot or service identity, token ownership, or credential rotation
- Routing changes that alter which skill handles a trigger phrase for a large class of users
- Approval gates, allowlists, or access-control policy embedded in a skill
- Plugin config, access-token config, or permission policy

## Required approval shape before staging/commit/PR

Ask for explicit current-turn approval that includes:

```text
I approve. Scope: <files/configs touched>. Impact: <what behavior or authority boundary changes>. Rollback plan: <branch/commit/PR revert or file checkout path>.
```

A generic instruction such as "open a PR" is useful intent, but not enough if the change classifies as permission/access-control. Get the scoped approval first, then proceed.

## Why

Skill changes can become runtime guardrails for future agents. A routing or approval-policy skill PR may indirectly change who can trigger actions or which runtime owns a capability. Treat these as protected authority-boundary edits even when the immediate action is "just documentation."
