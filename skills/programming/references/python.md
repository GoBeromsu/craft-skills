# Python reference

Modern Python: strictly typed, built on the project's canonical libraries and toolchain, and correct under async. The type checker is your first line of defense — encode invariants as types, parse untrusted input at boundaries, and own every resource explicitly.

Load this file in full before writing or editing Python. The rules below are deliberate project choices — violations are wrong, not stylistic.

## Tooling

| Category | Use | Never |
|---|---|---|
| Package manager | `uv` | pip, poetry, conda, pipenv |
| Type checker | `basedpyright` (`typeCheckingMode = "all"`) | mypy, plain pyright |
| Linter + formatter | `ruff` (`select = ["ALL"]`) | flake8, black, isort, autopep8 |
| Async runtime | `anyio` | bare `import asyncio` |
| Data | `polars` + `duckdb` + `numpy` | pandas |
| Web framework | FastAPI + Pydantic v2 | Flask, Django REST |
| ORM | SQLAlchemy 2.x async | Django ORM, Tortoise |
| HTTP client | `httpx` (HTTP/2 enabled) | requests, aiohttp |
| Testing | `pytest` | unittest |
| CLI | `typer` + `rich` | argparse, click, fire |

Override a default only when `pyproject.toml` explicitly picks something else.

## The iron list

1. **Frozen by default** — `@dataclass(frozen=True, slots=True)`; Pydantic `model_config = ConfigDict(frozen=True)`. Mutable only when mutation is the documented purpose.
2. **`NewType` for distinct primitives** — `UserId = NewType("UserId", int)`. Never pass a raw `int`/`str` where a branded type exists.
3. **`match` for variants, `if` for booleans** — never use `if`/`elif`/`else` to discriminate on type (`isinstance`), enum value, or literal. `match`/`case` is mandatory and ends with `case unreachable: assert_never(unreachable)`. Bare `case _: pass` or `case _: raise ...` is banned — both swallow new variants. `if`/`else` is fine for booleans, ranges, and predicate calls.
4. **`Protocol` over ABC** — `typing.Protocol` for interfaces; ABC only when you need shared implementation.
5. **No raw dicts in signatures** — params and returns use `TypedDict`, a frozen dataclass, or a Pydantic model. Internal scratch dicts are fine.
6. **Parse, don't validate** — constructors produce a typed object or raise. Never pass unvalidated data deeper into the call stack.
7. **Typed errors** — exceptions are subclasses with typed fields, never `raise ValueError("bare string")`. Use a union return when the caller is 1–2 levels away and must handle the outcome (repository → service); raise when the error should propagate to a boundary handler (service → HTTP).
8. **`Final` for constants** — module-level constants are `Final`. Mutable module globals are a smell.
9. **Explicit `None`** — annotate `-> X | None`; never return `None` from a signature that omits it. Use `X | Y` (PEP 604), never `Optional`/`Union`.
10. **Context managers for resources** — files, DB connections, HTTP clients, locks via `with` / `async with`. No manual `.close()`.
11. **No `Any`, no `object` as annotations** — `object` gives zero narrowing and zero attributes. Use `Protocol` (structural), a `TypeVar` (generic pass-through), an explicit union, or `TypedDict`.
12. **No `cast`** — redesign the types instead.
13. **No `# type: ignore` / `# pyright: ignore`** — fix the type error; the checker is right.
14. **No broad `except`** — `except Exception` / `except BaseException` swallow `KeyError`, `TypeError`, `AttributeError` and the stack trace. Catch the specific exception you expect. A genuine top-level boundary (CLI entry, HTTP handler) may catch broadly only to log and re-raise.

## Data modeling — which container, when

| Situation | Use |
|---|---|
| User input, API request/response | `Pydantic BaseModel(frozen=True)` |
| Internal value object (no I/O) | `@dataclass(frozen=True, slots=True)` |
| Function with multiple outcomes | union of frozen dataclasses + `match` |
| Dict shape for JSON compat / `**kwargs` | `TypedDict` |
| Fixed constants | `StrEnum` / `IntEnum` |
| Distinct primitive (`UserId` vs `MovieId`) | `NewType` |
| Capability / contract | `Protocol` |
| Contract + shared implementation | ABC |
| Config from env vars | `pydantic-settings BaseSettings` |

The one rule: data crosses a trust boundary → Pydantic. Everything else → frozen dataclass.

`frozen=True` does not apply to SQLAlchemy `Mapped[]` models, deliberate builder/accumulator objects, and Pydantic Settings overridden in tests — each carries a docstring saying why mutation is required.

## Exhaustive match — the canonical shape

```python
# BANNED — if/elif on a tagged variant (runtime bomb when a variant is added)
if isinstance(event, Click):
    handle_click(event.x, event.y)
elif isinstance(event, Scroll):
    handle_scroll(event.delta)
else:
    raise ValueError(f"unknown: {event}")

# GOOD — exhaustive match; the checker flags a missing case at build time
match event:
    case Click(x=x, y=y):
        handle_click(x, y)
    case Scroll(delta=delta):
        handle_scroll(delta)
    case unreachable:
        assert_never(unreachable)
```

## Error handling — catch what you expect

```python
# BANNED — swallows bugs and the stack trace
try:
    result = api.fetch(url)
except Exception as e:
    logger.error(e)
    return None

# GOOD — name the exception; convert at the boundary
try:
    result = api.fetch(url)
except httpx.HTTPStatusError as e:
    logger.error("API %d: %s", e.response.status_code, e.request.url)
    return None
except httpx.ConnectError:
    raise ServiceUnavailableError(service="api") from None
```

## Async

- Bare `import asyncio` is banned — use `anyio`.
- Background tasks run under `anyio.create_task_group`; never fire-and-forget with `asyncio.create_task`.
- Concurrency gates use `anyio.CapacityLimiter`, not `asyncio.Semaphore`.

## Scripts (PEP 723)

Every `.py` script — even throwaway — declares its dependencies inline with PEP 723 metadata and runs via `uv run script.py`. No venv, no `requirements.txt`; the script is the environment spec.

```python
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx", "rich"]
# ///
```

## No-excuse audit (run before declaring done)

`basedpyright` (`all`) + `ruff` (`ALL`) catch most of this; the rest is a manual scan of the diff. None of these has a silent opt-out — fix the cause or add a one-line comment naming why.

| Catches | Resolution |
|---|---|
| `cast(...)`, `# type: ignore`, `# pyright: ignore` | redesign the types |
| `except:` / `except Exception` / `except X: pass` | name the exception; handle or re-raise |
| `import asyncio` | use `anyio` |
| `import pandas` | use `polars` / `duckdb` |
| `@dataclass` without `frozen=True, slots=True` | add them, or comment why mutation is required |
| `-> dict` return annotation | return a typed model |
| `match` without `assert_never` | add the exhaustive default |
| `raise ValueError("...")` with a bare string | raise a typed exception |
| `object` as an annotation | use `Protocol` / `TypeVar` / union / `TypedDict` |
| `if isinstance(...)` / `if x == Enum.V` chain | rewrite as `match` / `case` |
| file > 250 pure LOC | split by responsibility |

## In tests

Tests follow the iron list — branded types, typed errors, exhaustive match. They may use `pytest` assertions, magic numbers as test data, and mutable fixtures. Prefer real objects and in-memory fakes over mocks; mock only the unmockable (clock, randomness) at the narrowest seam.

## Editing an existing file

When a file does not follow these rules, write new code in strict style; do not refactor the surrounding code in the same change.
