"""Recover plotted data from the paper's matplotlib vector PDFs.

Each axes is found as a white-filled rectangle. Its gridlines give tick pixel positions, and the numeric tick
labels next to them give the values, so a least-squares fit maps PDF points -> data coordinates per axis.
Thick stroked paths become line series, small filled circles become scatter points, and translucent
filled polygons become shaded bands. Everything is keyed by stroke/fill color and assigned to the axes it lies in.
"""
import re
from dataclasses import dataclass, field

import pymupdf

NUM = re.compile(r"^[−-]?\d+(\.\d+)?%?$")


@dataclass
class Axes:
    rect: pymupdf.Rect
    xmap: tuple[float, float] = (1.0, 0.0)   # value = a*px + b
    ymap: tuple[float, float] = (1.0, 0.0)
    lines: list[dict] = field(default_factory=list)
    dots: list[dict] = field(default_factory=list)
    bands: list[dict] = field(default_factory=list)

    def x(self, px: float) -> float: return self.xmap[0] * px + self.xmap[1]
    def y(self, py: float) -> float: return self.ymap[0] * py + self.ymap[1]


def hexcol(c) -> str: return "#" + "".join(f"{round(v * 255):02x}" for v in c) if c else ""


def _fit(pairs: list[tuple[float, float]]) -> tuple[float, float]:
    if len(pairs) < 2: raise ValueError(f"need >=2 tick labels to fit an axis, got {pairs}")
    n = len(pairs)
    mx = sum(p for p, _ in pairs) / n
    mv = sum(v for _, v in pairs) / n
    a = sum((p - mx) * (v - mv) for p, v in pairs) / sum((p - mx) ** 2 for p, _ in pairs)
    return a, mv - a * mx


def _is_grid_gray(c) -> bool: return bool(c) and max(c) - min(c) < .02 and .5 < c[0] < .9


def _val(t: str) -> float: return float(t.replace("−", "-").rstrip("%"))


def _labels(page) -> list[tuple[float, float, float, str]]:
    """Numeric text spans as (cx, cy, value, raw)."""
    out = []
    for b in page.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            for sp in ln["spans"]:
                t = sp["text"].strip()
                if NUM.match(t):
                    x0, y0, x1, y1 = sp["bbox"]
                    out.append(((x0 + x1) / 2, (y0 + y1) / 2, _val(t), t))
    return out


def _points(d) -> list[tuple[float, float]]:
    pts = []
    for it in d["items"]:
        if it[0] == "l":
            if not pts: pts.append((it[1].x, it[1].y))
            pts.append((it[2].x, it[2].y))
        elif it[0] == "c":
            if not pts: pts.append((it[1].x, it[1].y))
            pts.append((it[4].x, it[4].y))
    return pts


def extract(path: str, min_axes_w: float = 80, line_w: float = 1.5) -> list[Axes]:
    page = pymupdf.open(path)[0]
    dr = page.get_drawings()
    rects = [d["rect"] for d in dr if d["type"] == "f" and d.get("fill") == (1.0, 1.0, 1.0)
             and d["rect"].width > min_axes_w and d["rect"].height > min_axes_w
             and d["rect"].width < .95 * page.rect.width]
    axes = [Axes(r) for r in sorted(rects, key=lambda r: r.x0)]
    labels = _labels(page)
    grid = [d for d in dr if d["type"] == "s" and len(d["items"]) == 1 and d["items"][0][0] == "l"
            and _is_grid_gray(d["color"])]
    for ax in axes:
        r = ax.rect
        vx = sorted({round(d["items"][0][1].x, 2) for d in grid if abs(d["items"][0][1].x - d["items"][0][2].x) < .01
                     and r.x0 - 1 <= d["items"][0][1].x <= r.x1 + 1 and abs(d["items"][0][1].y - r.y0) < r.height})
        hy = sorted({round(d["items"][0][1].y, 2) for d in grid if abs(d["items"][0][1].y - d["items"][0][2].y) < .01
                     and r.y0 - 1 <= d["items"][0][1].y <= r.y1 + 1 and r.x0 - 1 <= d["items"][0][1].x <= r.x1 + 1})
        xl = [(cx, v) for cx, cy, v, _ in labels if r.x0 - 15 <= cx <= r.x1 + 15 and r.y1 < cy < r.y1 + 30]
        yl = [(cy, v) for cx, cy, v, _ in labels if cx < r.x0 and r.x0 - 60 < cx and r.y0 - 15 <= cy <= r.y1 + 15]
        snap = lambda p, g: min(g, key=lambda q: abs(q - p)) if g else p
        ax.xmap = _fit([(snap(p, vx), v) for p, v in xl])
        # sharey panels carry no y tick labels: inherit the map from the axes to the left
        ax.ymap = _fit([(snap(p, hy), v) for p, v in yl]) if len(yl) >= 2 else axes[axes.index(ax) - 1].ymap

    def owner(pts) -> Axes | None:
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        return next((a for a in axes if a.rect.x0 - 2 <= cx <= a.rect.x1 + 2 and a.rect.y0 - 2 <= cy <= a.rect.y1 + 2), None)

    for d in dr:
        pts = _points(d)
        if not pts: continue
        ax = owner(pts)
        if ax is None: continue
        if d["type"] == "s" and (d.get("width") or 0) >= line_w and len(pts) >= 3:
            ax.lines.append({"color": hexcol(d["color"]), "x": [ax.x(p[0]) for p in pts], "y": [ax.y(p[1]) for p in pts]})
        elif d["type"] in ("f", "fs") and d.get("fill") and d["rect"].width < 12 and d["rect"].height < 12 and len(d["items"]) >= 4:
            c = d["rect"]
            ax.dots.append({"color": hexcol(d["fill"]), "x": ax.x((c.x0 + c.x1) / 2), "y": ax.y((c.y0 + c.y1) / 2),
                            "opacity": d.get("fill_opacity", 1)})
        elif d["type"] == "f" and d.get("fill") and (d.get("fill_opacity") or 1) < .9 and len(pts) > 10:
            ax.bands.append({"color": hexcol(d["fill"]), "x": [ax.x(p[0]) for p in pts], "y": [ax.y(p[1]) for p in pts]})
    return axes


if __name__ == "__main__":
    import sys
    for i, ax in enumerate(extract(sys.argv[1])):
        print(f"axes {i} {ax.rect} xmap={ax.xmap} ymap={ax.ymap}")
        for ln in ax.lines: print("  line", ln["color"], len(ln["x"]), f"x[{min(ln['x']):.3g},{max(ln['x']):.3g}] y[{min(ln['y']):.3g},{max(ln['y']):.3g}]")
        from collections import Counter
        print("  dots", Counter(d["color"] for d in ax.dots), "bands", Counter(b["color"] for b in ax.bands))
