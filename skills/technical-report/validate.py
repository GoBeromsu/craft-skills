#!/usr/bin/env python3
"""기술 문서 헤딩 구조 검증기 (harness-agnostic).

technical-report yaml 의 document depth(섹션 → ## 헤딩)를 진리로 삼아, book 디렉토리의
실제 마크다운 헤딩 구조를 파싱해 대조한다. 헤딩이 코드로 강제되는 게이트다 —
누락/추가/순서뒤바뀜/빈 헤딩이면 실패(exit 1).

경로는 프로젝트마다 다르므로 ${ENV_VAR} 또는 플래그로 받는다(스킬에 박지 않는다):
  TECHNICAL_REPORT_YAML  — 이 프로젝트의 technical-report yaml(SSOT) 경로. 기본 ./technical-report.yaml
  TECHNICAL_REPORT_BOOK  — 정본 마크다운이 있는 book 디렉토리. 기본 ./book

사용:
  python3 validate.py                       # env 또는 기본 경로 사용
  python3 validate.py --yaml <f> --book <d> # 직접 지정
  python3 validate.py --json                # 기계 판독용 JSON 결과

종료 코드: 0 = 전부 통과, 1 = 위반, 2 = 환경/설정 오류.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML 필요 (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)

FRONTMATTER = re.compile(r"^---\s*$")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")


def env_path(name: str, fallback: Path) -> Path:
    """${name} 환경변수가 있으면 그 경로, 없으면 fallback."""
    value = os.environ.get(name)
    return Path(value) if value else fallback


def parse_structure(text: str):
    """frontmatter·코드펜스를 제외하고 (level, text, line_no, has_body) 헤딩 목록을 뽑는다."""
    lines = text.split("\n")
    # frontmatter 제거
    start = 0
    if lines and FRONTMATTER.match(lines[0]):
        for j in range(1, len(lines)):
            if FRONTMATTER.match(lines[j]):
                start = j + 1
                break
    in_fence = False
    raw = []  # (level, text, idx)
    body = lines[start:]
    for idx, ln in enumerate(body):
        if FENCE.match(ln):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING.match(ln)
        if m:
            raw.append((len(m.group(1)), m.group(2).strip(), idx))
    # has_body: 이 헤딩과 다음 헤딩 사이에 비공백 본문이 있는가
    headings = []
    for k, (lvl, txt, idx) in enumerate(raw):
        next_idx = raw[k + 1][2] if k + 1 < len(raw) else len(body)
        between = body[idx + 1:next_idx]
        has_body = any(s.strip() for s in between)
        headings.append({"level": lvl, "text": txt, "has_body": has_body})
    return headings


def validate(yaml_path: Path, book_dir: Path):
    doc = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))["document"]
    results = []
    ok = True
    for sid, sec in doc.items():
        title = sec["title"]
        fname = sec["file"]
        expected_h2 = list((sec.get("headings") or {}).keys()) if sec.get("headings") else []
        errs = []
        warns = []
        path = book_dir / fname
        if not path.is_file():
            errs.append(f"파일 없음: {fname}")
            results.append({"section": sid, "file": fname, "errors": errs, "warnings": warns})
            ok = False
            continue
        headings = parse_structure(path.read_text(encoding="utf-8"))
        h1 = [h for h in headings if h["level"] == 1]
        h2 = [h for h in headings if h["level"] == 2]
        # H1 검증
        if not h1:
            errs.append("H1(# 제목) 없음")
        elif h1[0]["text"] != title:
            errs.append(f'H1 불일치: 기대 "# {title}" / 실제 "# {h1[0]["text"]}"')
        if len(h1) > 1:
            errs.append(f"H1 여러 개({len(h1)}) — 섹션당 하나여야 함")
        # H2 집합·순서 검증
        actual_h2 = [h["text"] for h in h2]
        missing = [e for e in expected_h2 if e not in actual_h2]
        extra = [a for a in actual_h2 if a not in expected_h2]
        for e in missing:
            errs.append(f"필수 ## 헤딩 누락: {e}")
        for a in extra:
            errs.append(f"정의에 없는 ## 헤딩: {a}")
        if not missing and not extra and actual_h2 != expected_h2:
            errs.append(f"## 헤딩 순서 불일치\n      기대: {expected_h2}\n      실제: {actual_h2}")
        # 빈 헤딩(본문 없음) — must 미충족 신호
        for h in h2:
            if not h["has_body"]:
                warns.append(f"빈 ## 헤딩(본문 없음): {h['text']}")
        # abstract 처럼 headings:[] 인데 H2 가 있으면 오류
        if not expected_h2 and actual_h2:
            errs.append(f"이 섹션은 ## 헤딩이 없어야 하는데 발견됨: {actual_h2}")
        if errs:
            ok = False
        results.append({"section": sid, "file": fname, "errors": errs, "warnings": warns,
                        "expected_h2": expected_h2, "actual_h2": actual_h2})
    return ok, results


def main():
    ap = argparse.ArgumentParser(description="기술 문서 헤딩 구조 검증기")
    ap.add_argument("--yaml", type=Path, default=None,
                    help="technical-report yaml(SSOT) 경로 (기본: $TECHNICAL_REPORT_YAML 또는 ./technical-report.yaml)")
    ap.add_argument("--book", type=Path, default=None,
                    help="book 디렉토리 (기본: $TECHNICAL_REPORT_BOOK 또는 ./book)")
    ap.add_argument("--json", action="store_true", help="JSON 출력")
    args = ap.parse_args()

    yaml_path = args.yaml or env_path("TECHNICAL_REPORT_YAML", Path("technical-report.yaml"))
    book_dir = args.book or env_path("TECHNICAL_REPORT_BOOK", Path("book"))
    if not yaml_path.is_file():
        print(f"ERROR: yaml 없음: {yaml_path} (--yaml 또는 $TECHNICAL_REPORT_YAML)", file=sys.stderr)
        sys.exit(2)
    if not book_dir.is_dir():
        print(f"ERROR: book 디렉토리 없음: {book_dir} (--book 또는 $TECHNICAL_REPORT_BOOK)", file=sys.stderr)
        sys.exit(2)

    ok, results = validate(yaml_path, book_dir)

    if args.json:
        print(json.dumps({"ok": ok, "yaml": str(yaml_path), "book": str(book_dir), "results": results},
                         ensure_ascii=False, indent=2))
        sys.exit(0 if ok else 1)

    print(f"yaml: {yaml_path}\nbook: {book_dir}\n")
    n_err = n_warn = 0
    for r in results:
        status = "FAIL" if r["errors"] else ("WARN" if r["warnings"] else "PASS")
        print(f"[{status}] {r['section']}  ({r['file']})")
        for e in r["errors"]:
            print(f"   ✗ {e}")
            n_err += 1
        for w in r["warnings"]:
            print(f"   ! {w}")
            n_warn += 1
    print(f"\n{'='*48}")
    print(f"섹션 {len(results)}개 · 오류 {n_err} · 경고 {n_warn} → {'OK' if ok else 'VIOLATIONS'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
