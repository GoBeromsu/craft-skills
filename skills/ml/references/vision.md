# ML Vision Practice

Vision models fail silently at the input pipeline more often than at the architecture — a wrong resize, a leaked augmentation, or an un-inspected failure case costs more accuracy than the next model size up. Fix the pipeline and look at the errors before reaching for a bigger model.

This reference layers on top of `references/training.md` — the discipline ladder there (smoke test, baseline, one variable, seeds, eval discipline) still applies in full; the rules below are vision-specific additions.

## Table of Contents

- [Hard rules](#hard-rules) — normalization stats, channel order/value range, resize/interpolation consistency, augmentation on train only, visualize-after-aug, class imbalance, error-analysis-first, fine-tune before scratch
- [Hand-offs](#hand-offs)

---

## Hard rules

### Normalization stats come from the train split, computed on this dataset

Default to computing this dataset's own mean/std from the train split, not a borrowed constant from another dataset.

```bash
grep -rnE "0\.485,\s*0\.456,\s*0\.406" src/ configs/
```

Any hit means ImageNet's mean/std constants are hardcoded. This is correct **only** when fine-tuning an ImageNet-pretrained backbone on natural images close to ImageNet's distribution; otherwise compute this dataset's own train-split mean/std and use that instead. Grey zone — judge "close enough to ImageNet's distribution" by domain: photographs of everyday objects, yes; medical scans, satellite imagery, or synthetic renders, no.

### Channel order and value range match what the model expects

A pipeline that feeds BGR pixels to a backbone trained on RGB (a common OpenCV-vs-PIL mismatch), or feeds a `[0, 255]` integer range to a model expecting `[0, 1]` floats, degrades silently rather than crashing — training still runs, just on inputs the backbone was never designed to see.

```bash
grep -rnE "cv2\.imread|cv2\.cvtColor" src/<pkg>/data/*.py
```

Any hit confirms OpenCV is reading images, which defaults to BGR channel order — confirm a `cv2.cvtColor(img, cv2.COLOR_BGR2RGB)` conversion sits between the read and any RGB-expecting model or augmentation step. Grey zone — no single command confirms the value range; trace one real image through the pipeline end to end and print its channel order and min/max value immediately before it enters the model, rather than assuming the library defaults already line up.

### Resize and interpolation consistency, train vs. eval

The resize target size and interpolation method must match between the training transform and the evaluation transform — a model trained on one resize behavior and evaluated on another is being tested on an input distribution it never saw.

```bash
grep -rnE "resize|Resize|interpolation" src/<pkg>/data/*.py
```

Grey zone — no single pass/fail line; compare the train transform block and the eval transform block side by side and confirm the resize target and interpolation mode match (bilinear vs. bicubic vs. nearest are not interchangeable).

### Augmentation runs on train only

```bash
find src/<pkg>/data -type f \( -iname "*val*.py" -o -iname "*eval*.py" \) \
  -exec grep -lE "(RandomCrop|RandomFlip|ColorJitter|RandomRotation|RandAugment|RandomErasing)" {} + 2>/dev/null
```

Pass: no output. Fail: any file listed — a train-only augmentation transform leaked into the validation or eval data loader, corrupting the very number meant to measure real performance. The eval loader applies only deterministic preprocessing (resize, normalize) — never a stochastic transform. Use `find … -exec … +` rather than a shell glob for the two filename patterns — a glob that matches zero files (only one of `*val*.py` / `*eval*.py` exists on disk) aborts the whole line before grep ever runs in some shells, silently skipping the file that does exist instead of scanning it.

**SMELL — the eval loader carries a stochastic transform:**

```python
# data/eval_loader.py
transform = transforms.Compose([
    transforms.RandomCrop(224),   # stochastic — leaked in from the train transform
    transforms.ToTensor(),
    transforms.Normalize(mean, std),
])
```

**CLEAN — the eval loader is fully deterministic:**

```python
# data/eval_loader.py
transform = transforms.Compose([
    transforms.CenterCrop(224),   # deterministic — same crop every time
    transforms.ToTensor(),
    transforms.Normalize(mean, std),
])
```

Grey zone — test-time augmentation (TTA: averaging predictions over several augmented views of the same eval image) is a deliberate, documented exception, not a violation of this rule; it is fine only when the report explicitly labels the reported number as TTA-averaged, so a reader can compare it against a non-TTA baseline rather than mistaking it for a plain single-pass eval number.

### Visualize-after-aug is mandatory before a new pipeline trains

Before launching a run with a new or changed augmentation pipeline, render a grid of augmented samples and look at it. A transform that silently destroys the label — a crop that cuts the object of interest out of frame, a color jitter that erases the feature the label depends on — is invisible in a code review and obvious in a rendered image grid.

```bash
python3 - <<'EOF'
import torchvision
from torch.utils.data import DataLoader
loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
batch, _ = next(iter(loader))
torchvision.utils.save_image(batch, "experiments/aug_check.png", nrow=4)
EOF
```

Pass: the saved grid was actually opened and reviewed before the run launched. Fail: a new augmentation pipeline shipped straight to a full training run with no rendered sample ever reviewed.

### Class imbalance playbook

| Symptom | Fix |
|---|---|
| A minority class is rare in the training distribution | Class-weighted loss, oversampling the minority class, or a focal-loss variant |
| Accuracy looks good but the model never predicts the rare class | Report per-class precision/recall/F1, not just overall accuracy — accuracy hides a model that always predicts the majority class |
| Imbalance is extreme (rare event detection) | Precision-recall curve and a chosen operating threshold, not a single accuracy number |

### Error-analysis-first

Before trying a bigger or different architecture, look at the actual failure cases: a confusion matrix, and the worst-k scoring examples per class. Most gains at this stage come from fixing mislabeled data or a broken input case, not from a bigger model — an architecture change that "should help" but is proposed before looking at a single failure case is a guess, not a diagnosis.

```python
from sklearn.metrics import confusion_matrix
import numpy as np

cm = confusion_matrix(y_true, y_pred)
worst_k = np.argsort(-per_example_loss)[:20]   # the 20 worst-scoring examples
```

This is a companion step, not a pass/fail check — the exit criterion is that a human actually opened the confusion matrix and the rendered worst-k images before the next architecture change was proposed, not that the script above ran.

### Fine-tune before training from scratch

Default to a pretrained backbone unless the domain is far enough from natural images that pretraining transfer is known not to help (some scientific or sensor imaging). Training from scratch needs substantially more data and compute to reach comparable results, and that cost is rarely worth paying without first trying the pretrained-and-fine-tuned path and measuring the gap.

A common effective schedule is progressive unfreezing: train only a new head with the backbone frozen first, confirm the loss moves sensibly (this doubles as a cheap version of the single-batch smoke test from `references/training.md`), then unfreeze the backbone's later layers at a smaller learning rate. Unfreezing the entire backbone at the head's full learning rate on the first step risks destroying the pretrained features the fine-tune was supposed to keep.

## Hand-offs

- The base training ladder (smoke test, baseline, seeds, eval discipline) this reference layers on top of → `references/training.md`.
- Split-before-fitting and leakage prevention for the underlying dataset → `references/datasets.md`.
- Per-file Python discipline for the pipeline code itself → the `programming` skill.
