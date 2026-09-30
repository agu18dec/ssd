"""Build data/*.json for the site: curves recovered from the paper PDFs plus tables transcribed from the tex."""
import json
from pathlib import Path

import pymupdf

from pdf_series import Axes, extract, hexcol

ROOT = Path(__file__).resolve().parent.parent
PLOTS = ROOT / "src/paper/files/plots"
OUT = ROOT / "data"

OFF, SSD, ON = "#ff751f", "#3ccb81", "#0cc0df"
METHOD = {OFF: "off", SSD: "ssd", ON: "on"}
TAU_COLORS = {"#a9dca3": 0.05, "#7fc97f": 0.15, "#1d8640": 0.40, "#005321": 0.55}


def r(v: float, nd: int = 3) -> float: return round(v, nd)


def thin(xs: list[float], ys: list[float], n: int) -> tuple[list[float], list[float]]:
    """Keep every k-th point (plus the last) so long training curves stay light in the page."""
    k = max(1, len(xs) // n)
    idx = list(range(0, len(xs), k))
    if idx[-1] != len(xs) - 1: idx.append(len(xs) - 1)
    return [r(xs[i]) for i in idx], [r(ys[i]) for i in idx]


def line(ax: Axes, color: str, n: int = 400) -> dict:
    ln = max((l for l in ax.lines if l["color"] == color), key=lambda l: len(l["x"]))
    x, y = thin(ln["x"], ln["y"], n)
    return {"x": x, "y": y}


def dots(ax: Axes, color: str) -> list[list[float]]:
    return [[r(d["x"]), r(d["y"])] for d in ax.dots if d["color"] == color]


def headline() -> dict:
    axes = extract(str(PLOTS / "headline/figure_1_smoothed.pdf"))
    panels = []
    for ax, (task, arrow) in zip(axes, [("Company Memo", 44), ("Wikipedia", 34), ("Science Q&A", 57)]):
        panels.append({"task": task, "saving": arrow,
                       "series": {m: {**line(ax, c), "raw": dots(ax, c)} for c, m in METHOD.items()}})
    return {"xlabel": "Supervised tokens (×1000)", "ylabel": "Test accuracy (%)", "panels": panels}


def signal() -> dict:
    acc, loss, pos = extract(str(PLOTS / "signal/combined_panel.pdf"))
    band = lambda ax, c: next(({"x": [r(v) for v in b["x"]], "y": [r(v) for v in b["y"]]} for b in ax.bands if b["color"] == c), None)
    return {
        "accuracy": {m: {**line(acc, c), "raw": dots(acc, c)} for c, m in ((OFF, "off"), (ON, "on"))},
        "loss": {m: line(loss, c) for c, m in ((OFF, "off"), (ON, "on"))},
        "position": {m: {**line(pos, c), "band": band(pos, c)} for c, m in ((OFF, "off"), (ON, "on"))},
    }


def curriculum() -> dict:
    contrib, length = extract(str(PLOTS / "teacher_contribution/combined_panel.pdf"))
    return {"taus": list(TAU_COLORS.values()),
            "contribution": {str(t): line(contrib, c, 300) for c, t in TAU_COLORS.items()},
            "length": {str(t): line(length, c, 300) for c, t in TAU_COLORS.items()}}


def tau_frontier() -> dict:
    path = str(PLOTS / "spectrum/tau_frontier.pdf")
    (ax,) = extract(path)
    page = pymupdf.open(path)[0]
    legend = pymupdf.Rect(215, 215, 390, 290)   # legend box sits in the lower right; its markers are not data
    shapes = [d for d in page.get_drawings() if d["type"] == "fs" and d.get("fill") and d["rect"].width < 16
              and not legend.contains(d["rect"])]
    center = lambda d: ((d["rect"].x0 + d["rect"].x1) / 2, (d["rect"].y0 + d["rect"].y1) / 2)
    labels = [(sp["bbox"], float(sp["text"].lstrip("="))) for b in page.get_text("dict")["blocks"]
              for ln in b.get("lines", []) for sp in ln["spans"] if sp["text"].startswith("=")]
    pts, circles = [], []
    for d in shapes:
        cx, cy = center(d)
        kind = {OFF: "off", SSD: "ssd", ON: "on"}.get(hexcol(d["fill"]))
        if kind is None or (kind == "ssd" and len(d["items"]) < 8): continue   # 3-item green shape = frontier arrowhead
        p = {"kind": kind, "tau": None, "tokens": r(ax.x(cx), 1), "acc": r(ax.y(cy), 2)}
        pts.append(p)
        if kind == "ssd": circles.append((p, cx, cy))
    # In this figure τ increases monotonically with supervised tokens (checked against the rendered PDF), so the sorted
    # "=0.xx" annotations pair with the circles sorted by x.
    taus = sorted(v for _, v in labels)
    assert len(taus) == len(circles), (taus, len(circles))
    for (p, _, _), t in zip(sorted(circles, key=lambda c: c[1]), taus): p["tau"] = t
    return {"points": sorted(pts, key=lambda p: (p["tau"] is None, p["tau"] or 0))}


FORGETTING = {  # Table 1, Qwen2.5-7B on SciKnowEval Chemistry; Δ = mean change over 6 general benchmarks
    "base": {"sciqa": 32.5, "delta": 0.0, "avg6": 65.98, "tokens_m": None},
    "rows": [
        {"method": "SFT", "kind": "off", "sciqa": 67.3, "delta": -6.64, "ci": 0.74, "tokens_m": 1.82},
        {"method": "FKL", "kind": "off", "sciqa": 67.1, "delta": -6.65, "ci": 0.88, "tokens_m": 1.82},
        {"method": "SDFT", "kind": "on", "sciqa": 68.4, "delta": -4.52, "ci": 0.75, "tokens_m": 2.84},
        {"method": "SSD", "kind": "ssd", "sciqa": 71.6, "delta": -1.38, "ci": 0.52, "tokens_m": 2.20},
    ],
    "benchmarks": ["HellaSwag", "HumanEval", "IFEval", "MMLU", "TruthfulQA", "Winogrande"],
}

ROUTING = {  # Appendix C: JSD-routed inference (no training) on SciKnowEval Chemistry-L3, 507 questions
    "rows": [
        {"strategy": "Student only", "tau": None, "acc": 13.81, "len": 879, "teacher_frac": 0.0},
        {"strategy": "τ = 0.6", "tau": 0.6, "acc": 34.12, "len": 850, "teacher_frac": 1.3},
        {"strategy": "τ = 0.5", "tau": 0.5, "acc": 51.87, "len": 745, "teacher_frac": 2.7},
        {"strategy": "τ = 0.3", "tau": 0.3, "acc": 66.07, "len": 588, "teacher_frac": 7.0},
        {"strategy": "τ = 0.1", "tau": 0.1, "acc": 73.96, "len": 523, "teacher_frac": 15.7},
        {"strategy": "Teacher only", "tau": None, "acc": 80.28, "len": 487, "teacher_frac": 100.0},
    ]
}

ROLLOUT = {  # Figures 1 and 3 of the paper (main_figure / influence_positions)
    "prompt": "Tell me about the marketing team of the company.",
    "ssd": [["Marketing", "s"], ["team", "s"], ["is", "s"], ["led", "t"], ["by", "s"], ["Lina", "t"],
            ["Okafor", "t"], ["with", "s"], ["12", "t"], ["people", "s"]],
    "inflection_at": 3,
    "on_policy_tail": ["mainly", "focused", "on", "creating", "the"],
    # the two next-token panels drawn in Figure 1 (illustrative bars, as in the paper figure)
    "panels": {
        "0": {"teacher": [["Marketing", .62], ["The", .12], ["Status", .08]],
              "student": [["Marketing", .55], ["The", .15], ["Leading", .12]], "switch": False},
        "5": {"teacher": [["Lina", .9], ["Anita", .05], ["Maya", .03]],
              "student": [["Tom", .22], ["Sarah", .2], ["Mike", .18]], "switch": True},
    },
}


def main():
    OUT.mkdir(exist_ok=True)
    for name, obj in [("headline", headline()), ("signal", signal()), ("curriculum", curriculum()),
                      ("tau_frontier", tau_frontier()), ("forgetting", FORGETTING), ("routing", ROUTING), ("rollout", ROLLOUT)]:
        (OUT / f"{name}.json").write_text(json.dumps(obj, separators=(",", ":")))
        print(f"{name:13s} {(OUT / f'{name}.json').stat().st_size / 1024:6.1f} KB")


if __name__ == "__main__":
    main()
