#!/usr/bin/env python3
"""Stdlib helpers for writing an Obsidian .excalidraw.md scene directly, as a file.

An Excalidraw drawing is just a file: frontmatter, a Text Elements section, and a
fenced-JSON scene. There is no plugin runtime dependency to build one — write the
JSON, run check(), write the file. See ../references/visualize.md for the full
anatomy, when to use this instead of the ExcalidrawAutomate workbench, and the
rendered-QA loop that comes after this script runs.

One Scene per output file. Typical use:

    from excalidraw_scene import Scene

    scene = Scene()
    a = scene.box(0, 0, 260, "Input", 20, "#0369a1", "#ffffff")
    b = scene.box(420, 0, 260, "Output", 20, "#334155", "#ffffff")
    scene.arrow(a, b, "events")
    defects = scene.check()
    assert not defects, defects
    scene.write("New Diagram.excalidraw.md", frontmatter={"tags": "[diagram]"})

Self-check: `python3 excalidraw_scene.py` builds a 3-box demo, validates it, writes
it to a temp file, and asserts the round trip.
"""
from __future__ import annotations

import json
import os
import random
import string
import tempfile

FONT_FAMILY = 2  # Excalidraw fontFamily id: 1 hand-drawn, 2 normal, 3 code.
ARROW_COLOR = "#1e293b"
LABEL_COLOR = "#475569"

# ponytail: per-character width table, not a real text-measurement library.
# Good enough to lay out cards without clipping; if a font/size combo looks off,
# widen max_width rather than reaching for a real font-metrics dependency.
_WIDE_RANGES = (
    ("가", "힣"),  # Hangul syllables
    ("一", "鿿"),  # CJK unified ideographs
    ("぀", "ヿ"),  # hiragana/katakana
)


def _char_width(ch, font_size):
    if any(lo <= ch <= hi for lo, hi in _WIDE_RANGES):
        return font_size * 1.0
    return font_size * 0.6


def text_width(line, font_size):
    return sum(_char_width(c, font_size) for c in line)


def wrap(s, font_size, max_width):
    """Word-wrap on spaces to max_width. Doesn't break long unspaced CJK runs
    (ponytail: naive word-wrap; pass pre-broken text for that case)."""
    out = []
    for raw_line in s.split("\n"):
        cur = ""
        for word in raw_line.split(" "):
            trial = f"{cur} {word}" if cur else word
            if cur and text_width(trial, font_size) > max_width:
                out.append(cur)
                cur = word
            else:
                cur = trial
        out.append(cur)
    return "\n".join(out)


def dims(s, font_size):
    lines = s.split("\n")
    return max(text_width(l, font_size) for l in lines), len(lines) * font_size * 1.25


def check(elements):
    """Return a list of defect strings for a raw element list; empty means safe to write.

    Checks: unique ids, arrow start/endBinding resolve and are mirrored in the
    target's boundElements, text containerId resolves and is mirrored, and no two
    filled ("card") rectangles overlap.
    """
    defects = []
    by_id = {}
    for e in elements:
        if e["id"] in by_id:
            defects.append(f"duplicate id {e['id']}")
        by_id[e["id"]] = e
    for e in elements:
        for key in ("startBinding", "endBinding"):
            binding = e.get(key)
            if not binding:
                continue
            target = by_id.get(binding["elementId"])
            if target is None:
                defects.append(f"{e['id']}.{key} -> missing {binding['elementId']}")
            elif not any(b["id"] == e["id"] for b in target.get("boundElements", [])):
                defects.append(f"{e['id']} not mirrored in {binding['elementId']}.boundElements")
        if e["type"] == "text" and e.get("containerId"):
            container = by_id.get(e["containerId"])
            if container is None:
                defects.append(f"text {e['id']}.containerId -> missing {e['containerId']}")
            elif not any(b["id"] == e["id"] for b in container.get("boundElements", [])):
                defects.append(f"text {e['id']} not mirrored in container {e['containerId']}.boundElements")

    def bbox(e):
        return e["x"], e["y"], e["x"] + e["width"], e["y"] + e["height"]

    def overlaps(a, b):
        ax0, ay0, ax1, ay1 = bbox(a)
        bx0, by0, bx1, by1 = bbox(b)
        return ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1

    cards = [e for e in elements if e["type"] == "rectangle" and e.get("backgroundColor", "transparent") != "transparent"]
    for i, a in enumerate(cards):
        for b in cards[i + 1:]:
            if overlaps(a, b):
                defects.append(f"card overlap {a['id']} x {b['id']}")
    return defects


def _frontmatter_block(fm):
    lines = ["---"]
    for k, v in fm.items():
        v_str = "[" + ", ".join(str(x) for x in v) + "]" if isinstance(v, (list, tuple)) else str(v)
        lines.append(f"{k}: {v_str}")
    lines.append("---")
    return "\n".join(lines)


def write_excalidraw_md(path, elements, frontmatter=None, description="", overwrite=False):
    """Assemble and write a .excalidraw.md file from a raw element list.

    Refuses to clobber an existing file unless overwrite=True — a new visualization
    is a new file; back up and diff element ids/bindings first if you were actually
    asked to edit an existing drawing.
    """
    if os.path.exists(path) and not overwrite:
        raise FileExistsError(
            f"refusing to overwrite an existing drawing: {path}. "
            "Pass overwrite=True only when asked to edit this exact file, and back it up first."
        )
    fm = dict(frontmatter or {})
    fm["excalidraw-plugin"] = "parsed"
    texts = [(e["text"], e["id"]) for e in elements if e["type"] == "text"]
    scene = {
        "type": "excalidraw",
        "version": 2,
        "source": "https://github.com/zsviczian/obsidian-excalidraw-plugin",
        "elements": elements,
        "appState": {"gridSize": None, "viewBackgroundColor": "#ffffff"},
        "files": {},
    }
    parts = [_frontmatter_block(fm), ""]
    if description:
        parts += [description.rstrip(), ""]
    parts += [
        "# Excalidraw Data",
        "",
        "## Text Elements",
        "\n\n".join(f"{s} ^{i}" for s, i in texts),
        "",
        "%%",
        "## Drawing",
        "```json",
        json.dumps(scene, ensure_ascii=False, indent=1),
        "```",
        "%%",
    ]
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(parts) + "\n")
    return path


_SIDE_POINT = {
    "right": lambda r: (r["x"] + r["width"], r["y"] + r["height"] / 2),
    "left": lambda r: (r["x"], r["y"] + r["height"] / 2),
    "top": lambda r: (r["x"] + r["width"] / 2, r["y"]),
    "bottom": lambda r: (r["x"] + r["width"] / 2, r["y"] + r["height"]),
}


class Scene:
    """Collects elements for one Excalidraw drawing. One Scene per output file."""

    def __init__(self):
        self.elements = []
        self._ids = set()

    def _new_id(self):
        while True:
            candidate = "".join(random.choices(string.ascii_letters + string.digits, k=8))
            if candidate not in self._ids:
                self._ids.add(candidate)
                return candidate

    def _base(self, kind, x, y, w, h, stroke, bg="transparent", **kw):
        el = {
            "id": self._new_id(), "type": kind, "x": x, "y": y, "width": w, "height": h,
            "angle": 0, "strokeColor": stroke, "backgroundColor": bg, "fillStyle": "solid",
            "strokeWidth": 2, "strokeStyle": "solid", "roughness": 0, "opacity": 100,
            "groupIds": [], "frameId": None, "roundness": None,
            "seed": random.randint(1, 2 ** 31 - 1), "version": 1,
            "versionNonce": random.randint(1, 2 ** 31 - 1), "isDeleted": False,
            "boundElements": [], "updated": 1, "link": None, "locked": False,
        }
        el.update(kw)
        self.elements.append(el)
        return el

    def rect(self, x, y, w, h, stroke, bg="transparent", **kw):
        kw.setdefault("roundness", {"type": 3})
        return self._base("rectangle", x, y, w, h, stroke, bg, **kw)

    def text(self, x, y, s, font_size, color, max_width=None, container=None,
             align="left", valign="top", link=None, group=None):
        if max_width:
            s = wrap(s, font_size, max_width)
        w, h = dims(s, font_size)
        return self._base(
            "text", x, y, w, h, color, "transparent",
            text=s, rawText=s, originalText=s, fontSize=font_size, fontFamily=FONT_FAMILY,
            textAlign=align, verticalAlign=valign, containerId=container, autoResize=True,
            lineHeight=1.25, link=link, groupIds=[group] if group else [],
        )

    def box(self, x, y, w, s, font_size, stroke, bg, link=None, group=None,
             pad_x=14, pad_y=10, color=None, dashed=False):
        """Rectangle with one bound text; height fits the wrapped text."""
        s = wrap(s, font_size, w - 2 * pad_x)
        _, th = dims(s, font_size)
        r = self.rect(x, y, w, th + 2 * pad_y, stroke, bg, link=link,
                      groupIds=[group] if group else [],
                      strokeStyle="dashed" if dashed else "solid")
        t = self.text(x + pad_x, y + pad_y, s, font_size, color or stroke, container=r["id"], group=group)
        r["boundElements"].append({"type": "text", "id": t["id"]})
        return r

    def arrow(self, a, b, label=None, sa="right", sb="left", dashed=False, elbow_y=None):
        """Bound arrow from a's `sa` side to b's `sb` side; elbows around a mid-x/mid-y
        automatically when the two sides don't line up, or through elbow_y when given."""
        sx, sy = _SIDE_POINT[sa](a)
        ex, ey = _SIDE_POINT[sb](b)
        if elbow_y is not None:
            pts = [(sx, sy), (sx, elbow_y), (ex, elbow_y), (ex, ey)]
        elif sa in ("left", "right") and abs(sy - ey) > 2:
            mx = (sx + ex) / 2
            pts = [(sx, sy), (mx, sy), (mx, ey), (ex, ey)]
        else:
            pts = [(sx, sy), (ex, ey)]
        rel = [[px - sx, py - sy] for px, py in pts]
        xs, ys = [p[0] for p in rel], [p[1] for p in rel]
        el = self._base(
            "arrow", sx, sy, max(xs) - min(xs) or 1, max(ys) - min(ys) or 1, ARROW_COLOR,
            points=rel, startArrowhead=None, endArrowhead="arrow",
            strokeStyle="dashed" if dashed else "solid",
            startBinding={"elementId": a["id"], "focus": 0, "gap": 6},
            endBinding={"elementId": b["id"], "focus": 0, "gap": 6},
        )
        a["boundElements"].append({"type": "arrow", "id": el["id"]})
        b["boundElements"].append({"type": "arrow", "id": el["id"]})
        if label:
            w, h = dims(label, 15)
            lx = (pts[0][0] + pts[-1][0]) / 2 - w / 2
            ly = min(pts[0][1], pts[-1][1]) - h - 6
            self.text(lx, ly, label, 15, LABEL_COLOR)
        return el

    def check(self):
        return check(self.elements)

    def write(self, path, frontmatter=None, description="", overwrite=False):
        return write_excalidraw_md(path, self.elements, frontmatter, description, overwrite)


def _demo():
    scene = Scene()
    a = scene.box(0, 0, 260, "Input\ncollect raw events", 20, "#0369a1", "#ffffff")
    b = scene.box(420, 0, 260, "Process\nnormalize + validate", 20, "#0f766e", "#ffffff")
    c = scene.box(840, 0, 260, "Output\nwrite to store", 20, "#334155", "#ffffff")
    scene.arrow(a, b, "events")
    scene.arrow(b, c, "records")
    return scene


if __name__ == "__main__":
    demo = _demo()
    defects = demo.check()
    assert not defects, defects

    out_path = os.path.join(tempfile.mkdtemp(prefix="excalidraw_scene_selfcheck_"), "demo.excalidraw.md")
    demo.write(out_path, description="Self-check demo scene.")

    with open(out_path, encoding="utf-8") as fh:
        body = fh.read()
    assert body.count("%%") == 2 and "```json" in body
    scene_json = json.loads(body.split("```json\n", 1)[1].rsplit("\n```", 1)[0])
    assert len(scene_json["elements"]) == len(demo.elements)
    assert scene_json["elements"][0]["type"] == "rectangle"

    print(f"ok elements={len(demo.elements)} defects=0 wrote={out_path}")
