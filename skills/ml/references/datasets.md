# ML Dataset Construction

A dataset is a claim about the world; every rule below exists to keep that claim honest — validated at ingest, split before anything learns from it, and versioned so a number can always be traced back to the exact rows that produced it.

## Hard rules

### Schema and stats validation at ingest

Every dataset is validated against an explicit schema the moment it is ingested — column types, allowed value sets, and range checks — not discovered later as a training crash or a silently wrong metric.

```python
import pandera as pa

schema = pa.DataFrameSchema({
    "user_id": pa.Column(str, nullable=False),
    "label": pa.Column(str, pa.Check.isin(["pos", "neg"])),
    "score": pa.Column(float, pa.Check.in_range(0, 1)),
})

schema.validate(df, lazy=True)  # raises with every failing row, not just the first
```

Pass: validation raises no error, or raises before training starts (not discovered mid-run). Fail: a schema violation reaches the training loop as a crash, a NaN loss, or a silently miscoded label.

### Split-before-fitting law (absolute)

The train/validation/test split happens before any statistic is computed from the data. Feature scaling parameters, imputation values, vocabulary, category encodings, and augmentation statistics are all fit on the train split only, then applied unchanged to validation and test.

```bash
grep -rnE "\.fit(_transform)?\(" src/<pkg>/data/*.py
```

Grey zone — approximate: this only flags call sites; confirm by hand that the argument passed to `.fit(...)` is the train-split object, never the full, unsplit dataframe or the concatenation of all three splits.

### The three leakage classes (MECE)

| Leakage class | What happens | Detect | Fix |
|---|---|---|---|
| Row duplication | An identical row appears in both train and test | hash-intersection command below | Deduplicate before splitting, or split so duplicates land in the same partition |
| Group leakage | Rows from the same entity (patient, user, document, session) land in both splits | group-id overlap command below | Split by group id, never by row — no group straddles the split boundary |
| Temporal leakage | A row from after the test period informs training | timestamp-ordering command below | Sort by time, split by a cutoff date, never shuffle a time-ordered dataset before splitting |

**Row duplication — exact-match detection (approximate for near-duplicates: catches identical rows only, not fuzzy matches):**

```bash
python3 - <<'EOF'
import pandas as pd
train = pd.read_csv("data/processed/train.csv")
test = pd.read_csv("data/processed/test.csv")
h = lambda df: set(pd.util.hash_pandas_object(df, index=False))
overlap = h(train) & h(test)
print(f"{len(overlap)} exact-duplicate rows shared between train and test")
EOF
```

Pass: `0` overlapping rows. Fail: any nonzero count — duplicate rows leaked across the split.

**Group leakage detection:**

```bash
python3 - <<'EOF'
import pandas as pd
train = pd.read_csv("data/processed/train.csv")
test = pd.read_csv("data/processed/test.csv")
overlap = set(train["group_id"]) & set(test["group_id"])
print(f"{len(overlap)} group_ids present in both splits")
EOF
```

Pass: `0`. Fail: any nonzero count — re-split using a group-aware method (a group-wise k-fold) so every group's rows stay on one side.

**Temporal leakage detection:**

```bash
python3 - <<'EOF'
import pandas as pd
train = pd.read_csv("data/processed/train.csv")
test = pd.read_csv("data/processed/test.csv")
print(f"train max timestamp: {train['ts'].max()}  |  test min timestamp: {test['ts'].min()}")
EOF
```

Pass: `train max timestamp` is strictly less than `test min timestamp`. Fail: overlapping or reversed ranges — a row from the model's future is training a model that will be graded against the past.

### Labeling QA

Double-label a sample (5–10% of the dataset, or the full set if it is small) with two independent annotators, then compute an agreement metric (percent agreement, or Cohen's kappa for categorical labels).

```bash
python3 - <<'EOF'
from sklearn.metrics import cohen_kappa_score
import pandas as pd
sample = pd.read_csv("data/interim/double_labeled_sample.csv")
print(cohen_kappa_score(sample["label_a"], sample["label_b"]))
EOF
```

Pass: kappa above the project's stated threshold (0.7 is a common floor for "acceptable agreement" — judge by task difficulty, and state the chosen threshold explicitly). Fail: kappa below threshold — the labeling instructions are ambiguous; fix the instructions and re-label before scaling the dataset further.

### Dataset versioning

A published dataset version is an immutable snapshot — a frozen directory, or a pinned pointer in a data-versioning tool (DVC, lakeFS) — plus a manifest of file hashes. A "dataset" that is a mutable folder actively edited underneath running experiments is not a version; it is an untracked variable.

```bash
find data/processed -type f -not -name "MANIFEST.sha256" -exec sha256sum {} \; > data/processed/MANIFEST.sha256
```

Exclude the manifest file itself from the `find` — otherwise `sha256sum -c` against this manifest later reports the manifest's own entry as `FAILED`, a self-referential false failure. Every experiment config records which manifest hash (or dataset version tag) it trained against — see `references/training.md`'s experiment-tracking table.

### Datasheet-lite

Every dataset directory carries a `README.md` stating: provenance (where the data came from and how it was collected), license, known biases or limitations, collection date range, and split sizes.

```bash
test -f data/processed/README.md || echo "FAIL: dataset directory missing provenance README"
```

Pass: no output. Fail: `README.md` absent — the dataset has no recorded provenance, so nobody downstream can judge whether it is fit for their use case.

## Hand-offs

- Split-before-fitting feeds directly into the training discipline ladder — see `references/training.md`.
- Vision-specific input-pipeline correctness (normalization stats, resize consistency, augmentation-on-train-only) → `references/vision.md`.
- Project-wide layout for where `data/raw`, `data/interim`, `data/processed` live → `references/project-layout.md`.
