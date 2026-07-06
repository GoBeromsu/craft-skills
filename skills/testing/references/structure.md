# Testing Structure Reference

Test location is not a matter of taste — detect the project's existing convention first, and never let a second, competing convention appear beside it.

## Contents

- [Hard rules](#hard-rules)
- [Fixture organization](#fixture-organization)
- [Test data builders](#test-data-builders)

## Hard rules

### Convention taxonomy (MECE)

The rows below are MECE (Mutually Exclusive, Collectively Exhaustive) — a project's shape maps to exactly one convention, never a blend of two.

| Convention | Choose when | Absolute rules | Detection |
|---|---|---|---|
| Mirror-tree `tests/` | Python package (project default) | Top-level `tests/` mirrors `src/<pkg>/` 1:1: `src/foo/bar.py` → `tests/foo/test_bar.py` | `find tests -name 'test_*.py' \| wc -l` vs `find src -name '*.py' \| wc -l` — should track each other; a source module with no matching test file is a coverage gap, not a structure choice |
| Colocated `*.test.ts` | TypeScript/JavaScript (project default) | Test file sits next to the module it tests, same basename + `.test.ts`/`.test.tsx` suffix | `find src \( -name '*.ts' -o -name '*.tsx' \) \| grep -v '\.test\.' \| while read f; do ext="${f##*.}"; t="${f%.*}.test.${ext}"; test -f "$t" || echo "no test: $f"; done` |
| `__tests__/` per-directory | Grey zone — a repo already using it | Incumbent-respect only: keep it where it already exists; never introduce it fresh into a project using mirror-tree or colocated | `find . -type d -name __tests__ -not -path '*/node_modules/*' \| wc -l` |
| Monorepo per-package | Multi-package repo (pnpm/uv workspace, Nx, Turborepo) | Each package owns its tests under its own root, applying the language rule above for that package; no repo-root catch-all `tests/` spanning packages | `find packages -maxdepth 2 -type d -name tests` (or `apps`) — one hit per package, none at the repo root |

### Hard defaults for a new project or package with no existing convention

Apply these without asking when nothing is established yet:

- **Python** — top-level `tests/` mirroring `src/<pkg>/` package paths.
- **TypeScript/JavaScript** — colocated `*.test.ts` next to the source file.
- **Monorepo** — per-package, each package applying the rule above for its own language.

### Incumbent-respect clause

Detect the existing convention before adding a single test file. Follow it for edits to existing code; apply the strict defaults above only to genuinely new projects or packages. Never convert an existing codebase's test-location convention as a side effect of a feature change — propose that migration separately.

### Concrete layout examples

```
myapp/                          # Python — mirror-tree
├── src/
│   └── myapp/
│       ├── __init__.py
│       ├── billing/
│       │   └── invoice.py
│       └── users/
│           └── profile.py
└── tests/
    ├── billing/
    │   └── test_invoice.py
    └── users/
        └── test_profile.py
```

```
myapp/                          # TypeScript — colocated
└── src/
    ├── billing/
    │   ├── invoice.ts
    │   └── invoice.test.ts
    └── users/
        ├── profile.ts
        └── profile.test.ts
```

```
workspace/                      # Monorepo — per-package
├── packages/
│   ├── billing-api/            # Python package: mirror-tree inside its own root
│   │   ├── src/billing_api/…
│   │   └── tests/…
│   └── web-app/                # TypeScript package: colocated inside its own root
│       └── src/**/*.test.ts
└── pnpm-workspace.yaml
```

Python test files need either an `__init__.py` in every `tests/` subdirectory or a `pyproject.toml` `[tool.pytest.ini_options]` `rootdir`/import-mode setting — without one of the two, two `test_invoice.py` files in different subdirectories collide under pytest's default import mode, since the mirror-tree shape alone doesn't make module names unique.

### Conftest sprawl (grey zone)

A `conftest.py` at every directory level, each re-declaring a near-identical fixture with a small tweak, is conftest sprawl — it defeats the narrowest-scope law below by scattering the "real" definition across N files instead of promoting the shared part once. Judge by counting repeated fixture names across the tree:

```bash
grep -rn '^def \|^    def ' --include='conftest.py' <repo-root> | awk -F'def ' '{print $2}' | sed 's/(.*//' | sort | uniq -c | sort -rn
```

Read: a fixture name appearing in three or more `conftest.py` files with near-identical bodies should consolidate to their common ancestor directory; a fixture name appearing once per genuinely distinct package is fine.

### Scattered-test-directories detection

```bash
find . -type d -name tests -not -path '*/node_modules/*' -not -path '*/.git/*'
```

Read the output against the repo's shape:

- Single-package repo → expect exactly one line (or zero, for a colocated-TS project with no top-level `tests/` at all).
- Monorepo → expect one line per package (`packages/foo/tests`, `packages/bar/tests`), never an extra one at the repo root alongside them.
- Anything else — multiple top-level `tests/` trees outside a recognized per-package boundary (e.g. `tests/`, `validation/tests/`, and `src/app/tests/` in the same non-monorepo project) — is scattered-test-dir chaos. Pick the incumbent (most test files, most recently touched) and consolidate the rest into it; do not add a new test to any of the losing directories.

## Fixture organization

### Narrowest-scope law

A fixture lives at the narrowest directory (and narrowest `scope=`) that covers every test that uses it. A fixture used by one test module belongs in that module's local `conftest.py` or the test file itself — not the repo-root `conftest.py`. Promote a fixture upward only when a second, unrelated test module needs the identical setup.

Detection — module/session-scoped fixtures are the ones worth auditing for over-promotion and for hidden mutation:

```bash
grep -rn "scope=[\"']module[\"']\|scope=[\"']session[\"']" --include='conftest.py' <repo-root>
```

Read: each hit is not automatically wrong — check whether it is genuinely shared setup (a docker container, a compiled schema) versus a fixture that happens to be reused by copy-paste. A module/session fixture that returns a mutable object and is written to by more than one test is the smell below, not this one.

### Factory functions over shared mutable fixtures

A fixture shared across tests at `module` or `session` scope must not be mutated by any test that uses it — mutation makes test order load-bearing. Return a factory (a function/callable) instead of the object itself when each test needs its own instance.

```python
# SMELL — shared mutable fixture; test order now matters
@pytest.fixture(scope="module")
def user_list():
    return []

def test_add(user_list):
    user_list.append("a")
    assert user_list == ["a"]

def test_still_empty(user_list):
    assert user_list == []  # fails if test_add ran first
```

```python
# CLEAN — factory fixture returns a fresh object per call
@pytest.fixture
def make_user():
    def _make(name: str = "alice") -> User:
        return User(name=name)
    return _make

def test_add(make_user):
    assert make_user("bob").name == "bob"
```

Detection — a module/session fixture returning an empty mutable literal is the shape most likely to be shared-and-mutated:

```bash
grep -rn -A2 -E "scope=[\"'](module|session)[\"']" --include='conftest.py' <repo-root> \
  | grep -E 'return \[\]|return \{\}|return set\(\)'
```

Pass: no output, or every hit is confirmed read-only by its callers. Fail: a hit whose fixture is later mutated inside a test — grey zone if uncertain, judge by reading each test that consumes it.

## Test data builders

A builder function supplies sensible defaults and takes explicit overrides for the one or two fields the test actually cares about — the test body then states only what's relevant to its scenario.

```python
def build_user(**overrides: object) -> User:
    defaults = {"name": "test-user", "email": "test@example.com", "active": True}
    return User(**{**defaults, **overrides})

def test_given_inactive_user_when_login_then_rejected():
    user = build_user(active=False)
    assert login(user).rejected
```

```typescript
function buildUser(overrides: Partial<User> = {}): User {
  return { name: "test-user", email: "test@example.com", active: true, ...overrides };
}

test("given inactive user, when login, then rejected", () => {
  const user = buildUser({ active: false });
  expect(login(user).rejected).toBe(true);
});
```

Never build test objects field-by-field inline in every test — that couples every test to the full shape of the object and breaks all of them the moment a new required field is added. One builder per entity, one place to update when the shape changes.
