# Architecture

<!--
PURPOSE: The living system map. Answers "how is this system put together?" for someone
who just opened the repo. Update it as the system changes — it is NOT frozen like an ADR.
Keep it a map, not a manual: link to ADRs and rules, never restate their bodies.
-->

## Way point

<!-- Annotated directory tree: each top-level folder gets a one-line purpose and a pointer
     to the governing ADR/rule. Trim branches that carry no architectural meaning. -->

```
.
├── docs/                # research / exec-plan / decisions / rules / architecture.md
├── src/                 # {one-line purpose}  (ADR-NNN)
└── ...
```

## Component boundaries

<!-- What each module owns and how they communicate. One row per component. -->

| Component | Owns | Talks to | Governing ADR/rule |
|-----------|------|----------|--------------------|
| {name}    |      |          |                    |

## Cross-cutting decisions index

<!-- Links to ADRs — do NOT restate them. One line each. -->

- ADR-001 — {title}
- ADR-002 — {title}

## Key flows

<!-- The one or two data/control flows that matter most. A short sequence or diagram. -->

1. {flow name}: {source} → {step} → {sink}
