"""Inline-SVG chart kit. Charts are built in Python; static/anim.js only animates them.

Contract with anim.js (a figure = any element with data-fig):
  g.panel[data-x0 data-x1 data-y0 data-y1 data-px0 data-px1 data-py0 data-py1]   data<->pixel map of one axes
  rect.clip  inside a panel's <clipPath>: its width is set to progress * (data-pend - data-px0)
  path.s[data-pts]  series polyline in pixel space; a circle.head[data-s] rides its tip at the clip edge
  [data-ro]  text/span showing the series value at the clip edge (formatted by data-fmt)
  [data-at]  fades/scales in once progress passes data-at
  path.drawp  stroked path drawn by progress via stroke-dashoffset (pathLength=1)
"""
import math

from fasthtml.common import Div, Span
from fasthtml.svg import Circle, ClipPath, Defs, G, Line, Path, Rect, Svg
from fasthtml.svg import Text as T

INK, INK2, MUTED, GRID, AXIS = "#1f2328", "#57606a", "#8c959f", "#e9e6df", "#c8c3b8"
C = {"off": "#f26b1d", "ssd": "#1fae66", "on": "#12b1d6"}
NAME = {"off": "Off-policy", "ssd": "SSD (ours)", "on": "On-policy"}
GREENS = ["#a8dca2", "#6cc47a", "#1d8640", "#0b4f25"]


class Lin:
    """Linear map from a data domain onto a pixel range."""
    def __init__(self, d0: float, d1: float, r0: float, r1: float): self.d0, self.d1, self.r0, self.r1 = d0, d1, r0, r1
    def __call__(self, v: float) -> float: return self.r0 + (v - self.d0) / (self.d1 - self.d0) * (self.r1 - self.r0)


def nice_ticks(lo: float, hi: float, n: int = 5) -> list[float]:
    raw = (hi - lo) / n
    mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
    start = math.ceil(lo / step - 1e-9) * step
    out, v = [], start
    while v <= hi + 1e-9: out.append(round(v, 10)); v += step
    return out


def fmt_g(v: float) -> str: return f"{v:,.0f}" if abs(v) >= 100 else f"{v:g}"


def path_d(pts: list[tuple[float, float]]) -> str:
    return "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def smooth_d(pts: list[tuple[float, float]]) -> str:
    """Catmull-Rom through pts, as cubic Béziers."""
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(len(pts) - 1):
        p0, p1, p2 = pts[max(i - 1, 0)], pts[i], pts[i + 1]
        p3 = pts[min(i + 2, len(pts) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d


class Panel:
    """One axes inside a larger SVG: owns scales, draws frame and series, and exposes its data map to anim.js."""

    def __init__(self, uid: str, x: float, y: float, w: float, h: float, xdom, ydom, *, title="", xlabel="", ylabel="",
                 xticks=None, yticks=None, xfmt=fmt_g, yfmt=fmt_g, pend: float | None = None):
        self.uid, self.x, self.y, self.w, self.h = uid, x, y, w, h
        self.sx, self.sy = Lin(*xdom, x, x + w), Lin(*ydom, y + h, y)
        self.xdom, self.ydom = xdom, ydom
        self.title, self.xlabel, self.ylabel = title, xlabel, ylabel
        self.xticks = xticks if xticks is not None else nice_ticks(*xdom)
        self.yticks = yticks if yticks is not None else nice_ticks(*ydom)
        self.xfmt, self.yfmt = xfmt, yfmt
        self.pend = self.sx(pend) if pend is not None else x + w     # pixel x reached at progress 1
        self.clipped: list = []      # revealed by the clip rect
        self.free: list = []         # always visible / handled by data-at

    def pts(self, xs, ys) -> list[tuple[float, float]]:
        return [(self.sx(a), self.sy(b)) for a, b in zip(xs, ys)
                if self.xdom[0] <= a <= self.xdom[1] and self.ydom[0] - 1e-9 <= b <= self.ydom[1] + 1e-9]

    def line(self, key: str, xs, ys, color: str, *, width=2.4, head=True, dash=""):
        p = self.pts(xs, ys)
        enc = ";".join(f"{a:.1f},{b:.1f}" for a, b in p)
        self.clipped.append(Path(d=path_d(p), fill="none", stroke=color, stroke_width=width, stroke_linejoin="round",
                                 stroke_linecap="round", stroke_dasharray=dash or None, cls="s", data_s=key, data_pts=enc))
        if head: self.free.append(Circle(r=4.5, cx=p[0][0], cy=p[0][1], fill=color, stroke="#ffffff", stroke_width=2,
                                         cls="head", data_s=key))

    def raw(self, pts, color: str, r=1.8, opacity=.28):
        for a, b in pts:
            if self.xdom[0] <= a <= self.xdom[1] and self.ydom[0] <= b <= self.ydom[1]:
                self.clipped.append(Circle(r=r, cx=f"{self.sx(a):.1f}", cy=f"{self.sy(b):.1f}", fill=color, opacity=opacity))

    def band(self, xs, ys, color: str, opacity=.18):
        p = [(self.sx(min(max(a, self.xdom[0]), self.xdom[1])), self.sy(min(max(b, self.ydom[0]), self.ydom[1]))) for a, b in zip(xs, ys)]
        self.clipped.append(Path(d=path_d(p) + "Z", fill=color, opacity=opacity, stroke="none"))

    def frame(self) -> list:
        x, y, w, h = self.x, self.y, self.w, self.h
        out = []
        for v in self.yticks:
            py = self.sy(v)
            out += [Line(x1=x, x2=x + w, y1=py, y2=py, stroke=GRID, stroke_width=1),
                    T(self.yfmt(v), x=x - 8, y=py + 4, text_anchor="end", cls="tick")]
        for v in self.xticks:
            px = self.sx(v)
            out += [Line(x1=px, x2=px, y1=y + h, y2=y + h + 4, stroke=AXIS, stroke_width=1),
                    T(self.xfmt(v), x=px, y=y + h + 18, text_anchor="middle", cls="tick")]
        out.append(Line(x1=x, x2=x + w, y1=y + h, y2=y + h, stroke=AXIS, stroke_width=1))
        if self.title: out.append(T(self.title, x=x, y=y - 14, cls="ptitle"))
        if self.xlabel: out.append(T(self.xlabel, x=x + w / 2, y=y + h + 40, text_anchor="middle", cls="alabel"))
        if self.ylabel: out.append(T(self.ylabel, x=0, y=0, text_anchor="middle", cls="alabel",
                                     transform=f"translate({x - 46},{y + h / 2}) rotate(-90)"))
        return out

    def __ft__(self):
        cid = f"clip-{self.uid}"
        attrs = dict(data_x0=self.xdom[0], data_x1=self.xdom[1], data_y0=self.ydom[0], data_y1=self.ydom[1],
                     data_px0=f"{self.x:.1f}", data_px1=f"{self.x + self.w:.1f}", data_py0=f"{self.y + self.h:.1f}",
                     data_py1=f"{self.y:.1f}", data_pend=f"{self.pend:.1f}")
        return G(Defs(ClipPath(Rect(x=self.x - 6, y=self.y - 30, width=0, height=self.h + 36, cls="clip"), id=cid)),
                 *self.frame(), G(*self.clipped, clip_path=f"url(#{cid})"), *self.free, cls="panel", **attrs)


def Chart(fig_id: str, w: int, h: int, *children, cls="", label=""):
    svg = Svg(*children, viewBox=f"0 0 {w} {h}", width="100%", cls=f"chart {cls}", role="img", aria_label=label,
              id=f"{fig_id}-svg", preserveAspectRatio="xMidYMid meet")
    return Div(svg, cls="scroll-x")      # wide charts scroll sideways on phones instead of shrinking to illegibility


def Legend(keys: list[str], colors=C, names=NAME, extra=()):
    return Div(*[Span(Span(cls="sw", style=f"background:{colors[k]}"), names[k], cls="lg") for k in keys], *extra, cls="legend")


def Readout(panel_i: int, keys: list[str], x: float, y: float, fmt="pct") -> G:
    """Small in-plot value table: colored dot + live value per series (updated by anim.js)."""
    rows = []
    for j, k in enumerate(keys):
        yy = y + j * 17
        rows += [Circle(r=4, cx=x, cy=yy - 4, fill=C[k]), T(NAME[k].replace(" (ours)", ""), x=x + 10, y=yy, cls="rolab"),
                 T("–", x=x + 118, y=yy, text_anchor="end", cls="roval", data_ro=f"{panel_i}:{k}", data_fmt=fmt)]
    return G(*rows, cls="readout")
