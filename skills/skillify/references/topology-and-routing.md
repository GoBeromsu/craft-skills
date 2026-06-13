# Library Topology & Routing

Owns one concern: **where a skill package lives in `skills/` and how routing reflects that.**
(Secrets/hygiene → `runtime-hygiene-pr-playbook.md`. Plugin/path relocation → `craft-plugin-relocation.md`.)

## Placement policy — flat-first

Default to a **flat** package directly under `skills/`:

```
skills/<skill-name>/SKILL.md
```

Promote into an area folder **only** when a cohesive cluster of ≥2–3 sibling skills clearly
shares an owner/charter (e.g. `second-brain/`, `document-skills/`, `infra/`). Do **not** invent
an area for a single skill or for a domain whose boundary is still ambiguous — premature
hierarchy creates routing ambiguity and forces fake `(dispatcher for: …)` clauses.

```
ambiguous / solo domain   → skills/<skill>/                 (flat — default)
proven cohesive cluster   → skills/<area>/<skill>/          (area — promote later)
```

Promotion is a deliberate move, not a default. When a flat skill later joins a cluster, move
the whole directory (below) rather than leaving it flat while pretending it is routed.

## Moving a skill (flat→area, or area→area)

Resolver text alone is never enough — move the real directory.

1. **Move the whole directory** with `git mv skills/<old> skills/<area>/<skill>` so history
   survives. Carry `references/`, `scripts/`, `tests/`, `evals/`, `.env.example`, `CHANGELOG.md`.
2. **Rewrite routing surfaces:**
   - master `skills/RESOLVER.md` → point at the area (or flat skill), using real load keys.
   - area `RESOLVER.md` → point at qualified keys such as `second-brain/terminology`.
   - area `SKILL.md` `(dispatcher for: …)` clause → list the real child keys.
3. **Rewrite internal path references** — search old `skills/<old>/…` paths (script paths,
   reference links, verification blocks, CI workflow steps) and update them.
4. **Verify by actual loading**, not resolver text:
   - Open Claude Code and confirm the moved skill appears with the expected trigger phrase.
   - Run `python3 skills/skillify/scripts/validate-routing.py` to confirm all load keys resolve.
   - Run `python3 skills/skillify/scripts/validate-skill-format.py` to confirm the moved package is well-formed.

## Resolver correctness rules

- Resolver rows use **actual current load keys**, never aspirational aliases. If `terminology`
  lives at `skills/second-brain/terminology/`, route to `second-brain/terminology`, not
  `second-brain-terminology`. Nested skills may need the qualified key even when frontmatter
  `name` is bare (`second-brain/roundup`).
- Leaf descriptions are written **as real user trigger phrases**, not abstract capability blurbs.
  Claude Code matches skills by the `description` field — a capability blurb will not trigger naturally.
- Every sub-skill dir appears in exactly **one** area RESOLVER.md (orphan check).

## No whole-repo meta-router

craft-skills is a Claude Code plugin marketplace — skills are discovered from
`skills/<name>/SKILL.md` frontmatter descriptions directly. Do **not** create a top-level
loadable router for the whole repo. Keep `skills/RESOLVER.md` as a reference table only,
never a loadable skill. If an accidental whole-repo pseudo-router exists only to
dispatch across the entire `skills/` tree, remove it.

## Post-move hygiene

- Delete `.agent_skill_scope` files during moves — migration noise that confuses git rename
  summaries and adds no runtime value.
- Remove stale `stub`/`TBD`/`pre-move` routing language; if an area has no leaf yet, describe
  the area skill itself instead of naming a child that does not exist.
- Avoid ambiguous acronyms in names/resolver labels (prefer full names over `GWR`) unless the
  acronym is already the canonical command/product name.

## Verification

```bash
# Confirm all RESOLVER.md load keys resolve to real skill directories.
python3 skills/skillify/scripts/validate-routing.py

# Confirm all changed skill packages are well-formed.
python3 skills/skillify/scripts/validate-skill-format.py --diff-base origin/main...HEAD

# No stale .agent_skill_scope migration artifacts.
find skills -name .agent_skill_scope -print               # expect: empty

# No routing stubs left after a move.
grep -RInE '\bTBD\b|\bstub\b' skills 2>/dev/null          # expect: no routing stubs

git diff --check                                           # before commit
```
