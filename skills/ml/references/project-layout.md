# ML Project Layout

A run is reproducible only when its code, its configuration, and its data are each independently pinned — the layout below enforces that separation structurally, so reproducibility does not depend on anyone remembering to be careful.

## Table of Contents

- [Hard rules](#hard-rules) — pyproject.toml + src/ layout, the canonical tree, artifact placement, thin scripts, immutable data/raw, notebooks never imported, one run = one config
- [Grey zones](#grey-zones)
- [Incumbent-respect clause](#incumbent-respect-clause)
- [Hand-offs](#hand-offs)

---

## Hard rules

### `pyproject.toml` + `src/` layout + a locked dependency file is absolute

Every ML project — new or already past its first experiment — carries all three: a `pyproject.toml` declaring the package, a `src/<pkg>/` layout instead of a flat top-level package, and a locked dependency file (`uv.lock`) pinning exact resolved versions. A `requirements.txt` with no lockfile lets two runs on "the same code" silently resolve different transitive dependency versions.

```bash
test -f pyproject.toml || echo "FAIL: no pyproject.toml"
test -d src || echo "FAIL: no src/ layout — package sits flat at repo root instead"
test -f uv.lock || echo "FAIL: no locked dependency file (uv.lock) — versions are not pinned"
```

Pass: no output. Fail: any `FAIL` line — fix the packaging baseline before adding more code; it only gets more expensive to retrofit later.

```bash
test -f requirements.txt && ! test -f pyproject.toml && \
  echo "FAIL: requirements.txt with no pyproject.toml — migrate to pyproject.toml + uv"
```

Pass: no output, or a `requirements.txt` that coexists with a real `pyproject.toml` for a legacy install path. Fail: `requirements.txt` is the *only* dependency declaration — there is no locked, reproducible resolution behind it.

### Canonical tree

```
project/
  pyproject.toml
  uv.lock
  src/
    <pkg>/
      __init__.py
      data/          # loading, schema validation, split logic
      models/        # model definitions
      training/      # training loop, optimizer/scheduler setup
      eval/          # metrics, evaluation harness
  configs/
    <experiment>.yaml     # one run = one config, committed with its result
  data/
    raw/             # immutable — never edited after ingest
    interim/         # intermediate derivations, safe to regenerate
    processed/       # final, split, model-ready data
  notebooks/
    01-explore-labels.ipynb   # numbered exploration only
  scripts/
    train.py          # thin entrypoint calling into src/<pkg>/
  experiments/        # run outputs — gitignored, tracked by run id
  tests/
```

### Artifact placement (MECE)

| Artifact | Belongs in | Never in |
|---|---|---|
| Reusable data loading, model definitions, training loop, eval metrics | `src/<pkg>/{data,models,training,eval}/` | `notebooks/`, `scripts/` |
| A run's hyperparameters | `configs/<name>.yaml`, committed alongside its result | hardcoded inside `training/`, CLI-flags-only with no saved record |
| Source-of-truth raw data | `data/raw/` (immutable after ingest) | edited in place, mixed with derived data |
| Cleaned/derived/split data | `data/interim/`, `data/processed/` | `data/raw/` |
| One-off exploration | `notebooks/NN-topic.ipynb`, numbered | logic imported back into `src/` |
| Thin CLI entrypoints | `scripts/<name>.py`, calling into `src/<pkg>/` | business logic living in the script body itself |
| Run outputs (checkpoints, logs, metrics, plots) | `experiments/<run-id>/`, gitignored | committed into the repository |
| Tests | `tests/` mirroring `src/<pkg>/` — see the `testing` skill for suite-level structure | scattered per-module `tests/` directories |

### Scripts stay thin

A file under `scripts/` calls into `src/<pkg>/` — it does not re-implement the pipeline inline. The same 250-pure-LOC ceiling the `programming` skill applies to every source file applies here too; a script that grows past it has quietly become the real implementation.

```bash
awk '!/^[[:space:]]*$/ && !/^[[:space:]]*#/' scripts/train.py | wc -l
```

Pass: a small number of lines — argument parsing, config loading, one call into `src/<pkg>/`. Fail: the count approaches or crosses 250 — the logic grew into the script instead of a `src/<pkg>/` module.

**SMELL — the script re-implements the training loop inline:**

```python
# scripts/train.py
df = pd.read_csv("data/processed/train.csv")
model = SomeModel(hidden_dim=256)
optimizer = torch.optim.Adam(model.parameters())
for epoch in range(100):
    for batch in make_batches(df):
        loss = model.step(batch)
        loss.backward()
        optimizer.step()
# … dozens more lines of training logic live here, untested and unreusable
```

**CLEAN — the script is a thin entrypoint:**

```python
# scripts/train.py
from mypkg.training.config import load_config
from mypkg.training.loop import run_training

def main() -> None:
    cfg = load_config("configs/exp-004.yaml")
    run_training(cfg)

if __name__ == "__main__":
    main()
```

The `run_training` function above lives in `src/mypkg/training/`, is importable, and is testable in isolation — none of which is true of logic trapped inside a `scripts/` file.

### `data/raw/` is immutable

Once ingested, a file in `data/raw/` is never edited, reformatted, or overwritten in place — every downstream transformation is a code step producing a new file in `data/interim/` or `data/processed/`, never an in-place mutation of the source.

```bash
find data/raw -type f -not -name "MANIFEST.sha256" -exec sha256sum {} \; > data/raw/MANIFEST.sha256
# … later, before trusting a run against this data:
sha256sum -c data/raw/MANIFEST.sha256
```

Pass: every listed file reports `OK`. Fail: any `FAILED` line — a raw file changed after the manifest was written; treat this as data corruption, not a minor drift, and find out what touched it. Exclude the manifest file itself from the `find` — hashing the directory into a file that then sits inside that same directory makes the manifest describe its own pre-existence state, so a naive `find` that includes it always reports its own entry as `FAILED`.

```bash
git log --oneline -- data/raw | tail -n +2
```

Pass: no output (raw data was added once and never touched again in tracked history). Fail: any commit listed after the first — raw data is tracked in git and was modified post-ingest. Note: bulk raw data more often lives outside git entirely (object storage, DVC, a data lake), tracked only by the manifest hash above — this check applies when raw files are actually committed.

### `notebooks/` is never imported by `src/`

```bash
grep -rEn "^\s*(import|from)\s+.*notebooks" src/ 2>/dev/null
```

Pass: no output. Fail: any hit — a notebook has become a hidden dependency of production code. Extract the logic into `src/<pkg>/` and import it *into* the notebook, never the other way around.

Strip notebook outputs before every commit (`nbstripout`, or an equivalent pre-commit hook) — an un-stripped notebook diff buries the one line of code that changed under megabytes of re-rendered cell output, and review becomes theater. Grey zone: judge by whether `git diff` on a notebook stays legible; if it never does, the repo is missing the strip step.

### One run = one committed config

A run's config file is its identity — never a shared mutable "current settings" file edited in place between runs. See `references/training.md` for the full experiment-tracking contract (config hash, git SHA, data manifest hash, logged together).

```bash
ls configs/*.yaml | wc -l
```

Pass: one file per meaningfully distinct run, growing over the project's life. Fail: a single `config.yaml` that gets overwritten for every new run — there is no way to recover what config produced last week's number.

## Grey zones

- A `notebooks/` file that produces a stakeholder-facing report (a figure, a summary table) rather than code is fine to keep as a notebook indefinitely — the "never imported by `src/`" rule targets logic reuse, not one-off reporting.
- A tiny CRUD-style project with one model and one dataset may collapse `data/interim/` into `data/processed/` when there is genuinely no intermediate derivation step — judge by whether a reader could reconstruct the pipeline's stages from the folder names alone; if yes, the collapse is fine.
- `experiments/` output is gitignored by default, but a small number of final, reported-on run directories may be committed deliberately (e.g. under `experiments/reported/`) when the team wants those specific results version-controlled — the default stays gitignored; this is an explicit, scoped exception, not a silent one.

## Incumbent-respect clause

Detect the project's existing layout before changing anything: `ls -la` at the repo root, check whether a `src/` layout or a flat top-level package is already in use, and check for an existing `configs/` or `data/` convention. Follow the incumbent shape for edits inside an already-established project. Apply the strict `pyproject.toml` + `src/` + locked-deps default to new projects, and to any project that currently has no package manager at all (a bare `requirements.txt` with no lockfile). Never restructure an existing project's layout inside an unrelated feature or experiment change — propose the migration as its own scoped change.

## Hand-offs

- Dataset construction, splitting, and leakage prevention → `references/datasets.md`.
- Training-run discipline and experiment tracking → `references/training.md`.
- Suite-level test placement and structure beyond the `tests/` mirror rule above → the `testing` skill.
- Per-file Python discipline (typing, the 250-LOC ceiling, TDD loop) → the `programming` skill.
