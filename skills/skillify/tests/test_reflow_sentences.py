#!/usr/bin/env python3
"""Tests for the sentence-boundary line-break enforcer (contract §4)."""
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "skills/skillify/scripts/reflow-sentences.py"

CLEAN = """---
name: demo
description: A demo.
metadata:
  version: 1.0.0
---

# Demo

One sentence per line reads and diffs cleanly.
A second sentence sits on its own line.

- One item per line, even when the item runs long enough that a column wrap would have split it.
- Another item.
"""

WRAPPED_PARAGRAPH = """# Demo

This paragraph was hard-wrapped at a column width, so the sentence continues
onto the next line without ever reaching a sentence boundary first.
"""

WRAPPED_LIST = """# Demo

- This list item was hard-wrapped at a column width and its continuation
  spills onto an indented second line.
"""

FENCED = """# Demo

```text
this fenced content looks wrapped mid-sentence
but code fences pass through untouched
```

| a wrapped-looking | table row |
|---|---|
| passes | through |
"""


class ReflowSentencesTest(unittest.TestCase):
    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), *args],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )

    def write(self, root: Path, name: str, content: str) -> Path:
        p = root / name
        p.write_text(content, encoding="utf-8")
        return p

    def test_clean_file_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = self.write(Path(tmp), "clean.md", CLEAN)
            result = self.run_script(str(p))
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("OK", result.stdout)

    def test_wrapped_paragraph_fails_with_location(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = self.write(Path(tmp), "wrapped.md", WRAPPED_PARAGRAPH)
            result = self.run_script(str(p))
            self.assertEqual(result.returncode, 1)
            self.assertIn(f"{p}:3", result.stdout)

    def test_wrapped_list_item_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = self.write(Path(tmp), "list.md", WRAPPED_LIST)
            result = self.run_script(str(p))
            self.assertEqual(result.returncode, 1)

    def test_fences_and_tables_pass_through(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = self.write(Path(tmp), "fenced.md", FENCED)
            result = self.run_script(str(p))
            self.assertEqual(result.returncode, 0, result.stdout)

    def test_advisory_reports_but_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = self.write(Path(tmp), "wrapped.md", WRAPPED_PARAGRAPH)
            result = self.run_script(str(p), "--advisory")
            self.assertEqual(result.returncode, 0)
            self.assertIn("violation", result.stdout)

    def test_fix_reflows_then_check_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = self.write(Path(tmp), "wrapped.md", WRAPPED_PARAGRAPH)
            fix = self.run_script(str(p), "--fix")
            self.assertEqual(fix.returncode, 0)
            content = p.read_text(encoding="utf-8")
            self.assertIn(
                "This paragraph was hard-wrapped at a column width, "
                "so the sentence continues onto the next line "
                "without ever reaching a sentence boundary first.",
                content,
            )
            check = self.run_script(str(p))
            self.assertEqual(check.returncode, 0, check.stdout)

    def test_fix_joins_list_continuations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = self.write(Path(tmp), "list.md", WRAPPED_LIST)
            self.run_script(str(p), "--fix")
            content = p.read_text(encoding="utf-8")
            self.assertIn(
                "- This list item was hard-wrapped at a column width "
                "and its continuation spills onto an indented second line.",
                content,
            )

    def test_fix_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = self.write(Path(tmp), "wrapped.md", WRAPPED_PARAGRAPH)
            self.run_script(str(p), "--fix")
            first = p.read_text(encoding="utf-8")
            second_run = self.run_script(str(p), "--fix")
            self.assertIn("0 of 1 file(s) changed", second_run.stdout)
            self.assertEqual(first, p.read_text(encoding="utf-8"))

    def test_fix_preserves_frontmatter_and_fences(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = self.write(Path(tmp), "clean.md", CLEAN)
            self.run_script(str(p), "--fix")
            self.assertEqual(p.read_text(encoding="utf-8"), CLEAN)

    def test_abbreviations_do_not_split(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            content = "# Demo\n\nUse a scaffold (e.g. The generator) rather than hand-writing files.\n"
            p = self.write(Path(tmp), "abbr.md", content)
            self.run_script(str(p), "--fix")
            self.assertEqual(p.read_text(encoding="utf-8"), content)

    def test_directory_recursion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sub = Path(tmp) / "references"
            sub.mkdir()
            self.write(Path(tmp), "clean.md", CLEAN)
            self.write(sub, "wrapped.md", WRAPPED_PARAGRAPH)
            result = self.run_script(tmp)
            self.assertEqual(result.returncode, 1)
            self.assertIn("wrapped.md", result.stdout)


if __name__ == "__main__":
    unittest.main()
