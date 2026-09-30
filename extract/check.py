"""Re-plot the recovered JSON next to the original PDF raster, one PNG per figure, for eyeballing extraction fidelity."""
import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pymupdf

matplotlib.use("Agg")
ROOT = Path(__file__).resolve().parent.parent
D = {p.stem: json.loads(p.read_text()) for p in (ROOT / "data").glob("*.json")}
C = {"off": "#ff751f", "ssd": "#3ccb81", "on": "#0cc0df"}
OUT = ROOT / "build/check"


def raster(ax, rel: str):
    pix = pymupdf.open(ROOT / "src/paper/files/plots" / rel)[0].get_pixmap(dpi=90)
    ax.imshow(_img(pix)); ax.axis("off")


def _img(pix):
    import numpy as np
    return np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)


def fig(rel: str, n: int, draw, name: str):
    f, axs = plt.subplots(2, 1, figsize=(12, 7), gridspec_kw={"height_ratios": [1, 1]})
    raster(axs[0], rel)
    axs[1].remove()
    sub = [f.add_subplot(2, n, n + i + 1) for i in range(n)]
    draw(sub)
    f.tight_layout(); f.savefig(OUT / f"{name}.png", dpi=80); plt.close(f)


def headline(axs):
    for ax, p in zip(axs, D["headline"]["panels"]):
        for m, s in p["series"].items():
            ax.scatter(*zip(*s["raw"]), s=4, c=C[m], alpha=.25); ax.plot(s["x"], s["y"], c=C[m], lw=2)
        ax.set_ylim(0, 100); ax.set_title(p["task"])


def signal(axs):
    s = D["signal"]
    for m in ("off", "on"):
        axs[0].plot(s["accuracy"][m]["x"], s["accuracy"][m]["y"], c=C[m]); axs[1].plot(s["loss"][m]["x"], s["loss"][m]["y"], c=C[m])
        axs[2].plot(s["position"][m]["x"], s["position"][m]["y"], c=C[m])
        b = s["position"][m]["band"]
        if b: axs[2].fill(b["x"], b["y"], c=C[m], alpha=.2)
    axs[0].set_ylim(0, 100); axs[2].set_ylim(0, 4)


def curriculum(axs):
    greens = ["#a9dca3", "#7fc97f", "#1d8640", "#005321"]
    for g, t in zip(greens, D["curriculum"]["taus"]):
        for ax, k in zip(axs, ("contribution", "length")):
            ax.plot(D["curriculum"][k][str(t)]["x"], D["curriculum"][k][str(t)]["y"], c=g, label=f"τ={t}")
    axs[0].set_ylim(0, 60); axs[0].legend()


def tau(axs):
    for p in D["tau_frontier"]["points"]:
        axs[0].scatter(p["tokens"], p["acc"], c=C[p["kind"]], marker={"off": "D", "on": "^", "ssd": "o"}[p["kind"]], s=50)
        if p["tau"] is not None: axs[0].annotate(f"τ={p['tau']}", (p["tokens"] + 8, p["acc"]), fontsize=8)
    axs[0].set_ylim(88, 94.5)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    fig("headline/figure_1_smoothed.pdf", 3, headline, "headline")
    fig("signal/combined_panel.pdf", 3, signal, "signal")
    fig("teacher_contribution/combined_panel.pdf", 2, curriculum, "curriculum")
    fig("spectrum/tau_frontier.pdf", 1, tau, "tau_frontier")
    print("wrote", sorted(p.name for p in OUT.glob("*.png")))
