# craft-skills plugin relocation guide

Use when the craft-skills plugin root path, repository remote, or Claude Code plugin registration changes.

## Durable pattern

- Treat the repository as the SSOT, not any derived cache or symlink.
- Rename across all active surfaces, then verify skill discovery and real runtime behavior before calling it done.
- Separate active operational references from historical/archive references. Historical mentions of the old path are not blockers if active config, scripts, and plugin manifests are clean.

## Verification sequence

1. Update the repository remote and local checkout path.
2. Update `.claude-plugin/marketplace.json` and `plugin.json` to reflect the new path if the plugin root changed.
3. Search active surfaces for the old path/name:
   - `.claude-plugin/marketplace.json`
   - `plugin.json`
   - any CI workflow files that reference the plugin root
   - skill `SKILL.md` and `CHANGELOG.md` files with hardcoded paths
4. Remove stale bytecode/cache files if they preserve the old path.
5. Verify skill discovery by opening Claude Code and confirming the affected skills appear under the plugin.
6. Run `python3 skills/skillify/scripts/validate-skill-format.py` to confirm no format violations were introduced.
7. Run `python3 skills/skillify/scripts/validate-runtime-hygiene.py` to confirm no host-specific paths leaked in.
8. Only then report status as operationally verified.

## Flat-skill layout reminder

Skills live at `skills/<skill-name>/SKILL.md`. Claude Code discovers them from the `description` frontmatter field. Do not create a top-level `skills/SKILL.md` meta-router — keep `skills/RESOLVER.md` as a reference table only, never a loadable skill.

## Reporting shape

- State what is verified by real tool output.
- List unresolved caveats separately; do not bury them in a success summary.
