#!/usr/bin/env python3
"""Check README files: links, anchors, images, badge state, leftovers, and translation parity.

Usage: check_readme.py [--offline] README.md [README.en.md ...]
Exit 0 when nothing failed, 1 otherwise. Several files are compared with each other.
"""
import argparse
import html
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,}).*?^ {0,3}\1[`~]*[ \t]*$", re.M | re.S)
COMMENT = re.compile(r"<!--.*?-->", re.S)
INLINE_CODE = re.compile(r"(`+)(?!`).+?\1")
MD_TARGET = re.compile(r"(!?)\[(?:[^\]\\]|\\.|\[[^\]]*\])*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
REF_TARGET = re.compile(r"^ {0,3}\[[^\]]+\]:\s*<?(\S+?)>?(?:\s|$)", re.M)
HTML_TARGET = re.compile(r"<(a|img|source)\b[^>]*?\b(href|src|srcset)=[\"']([^\"']+)[\"']", re.I)
HEADING = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$", re.M)
HTML_HEADING = re.compile(r"<h([1-6])\b[^>]*>(.*?)</h\1>", re.I | re.S)
HTML_ID = re.compile(r"\b(?:id|name)=[\"']([^\"']+)[\"']", re.I)
PLACEHOLDER = re.compile(r"\{[A-Za-z][^{}\n]*\}")
BAD_BADGE = re.compile(r"\b(not found|invalid|no releases|no tags|inaccessible|unknown)\b", re.I)
LOCAL_HOST = re.compile(r"https?://(localhost|127\.0\.0\.1|\[::1\]|[^/]*\.(example|invalid|test|local))\b", re.I)
FAILING_BADGE = re.compile(r"\b(failing|failed|error)\b", re.I)


def mask(text):
    """Blank code and comments, keeping offsets out of scope for link and heading scans."""
    text = COMMENT.sub("", FENCE.sub("", text))
    return INLINE_CODE.sub("", text)


def slug(heading):
    heading = re.sub(r"<[^>]+>", "", heading)
    heading = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", heading)
    heading = re.sub(r"[*_`~]", lambda m: "_" if m.group() == "_" else "", html.unescape(heading))
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


def anchors(text):
    masked = mask(text)
    found, seen = set(HTML_ID.findall(masked)), {}
    headings = [m.group(2) for m in HEADING.finditer(masked)] + [m.group(2) for m in HTML_HEADING.finditer(masked)]
    for heading in headings:
        base = slug(heading)
        count = seen.get(base, 0)
        seen[base] = count + 1
        found.add(base if count == 0 else f"{base}-{count}")
    return found


def targets(text):
    masked = mask(text)
    links, images = set(REF_TARGET.findall(masked)), set()
    for bang, url in MD_TARGET.findall(masked):
        (images if bang else links).add(url)
    for tag, _, url in HTML_TARGET.findall(masked):
        (links if tag.lower() == "a" else images).add(html.unescape(url))
    return links, images


def repo_root(path):
    done = subprocess.run(["git", "-C", str(path.parent), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    return Path(done.stdout.strip()).resolve() if done.returncode == 0 else path.parent.resolve()


def check_local(path, url, root):
    parsed = urllib.parse.urlsplit(url)
    if parsed.path:
        target = (path.parent / urllib.parse.unquote(parsed.path)).resolve()
        if not target.is_relative_to(root):
            return None
        if not target.exists():
            return f"missing file: {url}"
    else:
        target = path
    if parsed.fragment and target.suffix.lower() in {".md", ".markdown"}:
        wanted = urllib.parse.unquote(parsed.fragment).lower()
        if wanted not in {a.lower() for a in anchors(target.read_text(encoding="utf-8"))}:
            return f"missing anchor: {url}"
    return None


def fetch(url, image):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 check_readme"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read(200_000) if image else b""
            kind = response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as error:
        if error.code in {404, 410}:
            return "fail", f"HTTP {error.code}: {url}"
        return "warn", f"HTTP {error.code}, not conclusive: {url}"
    except OSError as error:
        return "fail", f"unreachable ({error}): {url}"
    if image and "svg" in kind:
        label = " ".join(re.findall(r"<(?:text|title)\b[^>]*>([^<]*)<", body.decode("utf-8", "replace")))
        if BAD_BADGE.search(label):
            return "fail", f"badge shows '{label[:60]}': {url}"
        if FAILING_BADGE.search(label):
            return "warn", f"badge shows '{label[:60]}': {url}"
    return "ok", url


def shape(text):
    masked = COMMENT.sub("", text)
    outside = FENCE.sub("", masked)
    _, images = targets(text)
    return {
        "heading levels": [len(m.group(1)) for m in HEADING.finditer(outside)],
        "code blocks": len(FENCE.findall(masked)),
        "details blocks": outside.count("<details"),
        "local images": sorted(u for u in images if "://" not in u),
    }


def check_file(path, offline):
    text = path.read_text(encoding="utf-8")
    fails, warns, root = [], [], repo_root(path)
    links, images = targets(text)
    for url in sorted(links | images):
        if not re.match(r"[a-z][a-z0-9+.-]*:", url, re.I):
            problem = check_local(path, url, root)
            if problem:
                fails.append(problem)
    if not offline:
        remote = [(u, u in images) for u in sorted(links | images) if u.startswith(("http://", "https://")) and not LOCAL_HOST.match(u)]
        with ThreadPoolExecutor(8) as pool:
            for state, message in pool.map(lambda item: fetch(*item), remote):
                if state == "fail":
                    fails.append(message)
                elif state == "warn":
                    warns.append(message)
    for match in PLACEHOLDER.finditer(mask(text)):
        fails.append(f"unfilled placeholder: {match.group()}")
    if "Delete every block" in text:
        fails.append("template comment left in the file")
    for match in re.finditer(r"</summary>[ \t]*\n(?![ \t]*\n)", FENCE.sub("", text)):
        fails.append("no blank line after </summary>, so Markdown inside will not render")
    if re.search(r"^#{1,6}\s+.*[\U0001F300-\U0001FAFF☀-➿]", mask(text), re.M):
        warns.append("emoji in a heading makes its anchor fragile")
    return fails, warns


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="skip remote URLs")
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    failed = False
    for path in args.files:
        fails, warns = check_file(path, args.offline)
        failed = failed or bool(fails)
        print(f"{path}: {len(fails)} failed, {len(warns)} warnings")
        for message in fails:
            print(f"  FAIL {message}")
        for message in warns:
            print(f"  WARN {message}")
    first = shape(args.files[0].read_text(encoding="utf-8"))
    for path in args.files[1:]:
        other = shape(path.read_text(encoding="utf-8"))
        for key in first:
            if first[key] != other[key]:
                failed = True
                print(f"  FAIL parity: {key} differ between {args.files[0]} and {path}: {first[key]} vs {other[key]}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
