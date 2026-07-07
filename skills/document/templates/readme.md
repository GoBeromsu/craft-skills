# {Project Name}

<!--
PURPOSE: The repo entry point. Answers "what is this and how do I start?" in under a minute.
Keep it short — point to docs/ for depth, never duplicate ADR or architecture bodies here.
-->

> {One-sentence description of what this project is and who it is for.}

## Overview

<!-- 2–4 sentences: the problem this solves and the high-level approach. -->

## Quick start

```bash
# clone, install, run — the shortest path to a working state
git clone {repo-url}
cd {project}
{install command}
{run command}
```

## Commands

<!-- The handful of commands a contributor runs daily. Keep it to the real ones. -->

| Command | What it does |
|---------|--------------|
| `{cmd}` | {one line} |
| `{cmd}` | {one line} |

## Architecture

<!-- A few sentences on how the system is put together, then LINK out.
     Do not restate ADR or architecture.md bodies — point at them. -->

See [`docs/architecture.md`](docs/architecture.md) for the system map. Explicitly recorded decisions, if any, live in [`docs/decisions/`](docs/decisions/) as ADRs:

- [ADR-NNN — {decision title}](docs/decisions/ADR-NNN-{topic}.md)

## Layout

<!-- Point at the docs/ ontology and the few top-level dirs that matter. -->

- `docs/` — research, exec-plans, decisions (ADRs), rules, and the architecture map
- `{src dir}/` — {one line}

## Contributing

<!-- The shortest path from "I want to change this" to a reviewable PR. -->

1. Branch from `main`.
2. {Test / lint command} must pass.
3. If this change includes an explicitly requested ADR, add it under `docs/decisions/` (see [`docs/decisions/README.md`](docs/decisions/README.md)).
4. Open a PR.

## License

{LICENSE}
