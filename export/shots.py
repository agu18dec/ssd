"""Screenshot the running site for visual review: sections at desktop/mobile widths and figure frames at chosen times.

usage: uv run python export/shots.py [page|frames] (server must be running on :5001)
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:5001/"
OUT = Path(__file__).resolve().parent.parent / "build/shots"


def page_shots(pw):
    b = pw.chromium.launch()
    for name, vp in [("desk", {"width": 1440, "height": 900}), ("mob", {"width": 390, "height": 844})]:
        pg = b.new_page(viewport=vp, device_scale_factor=1)
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(URL, wait_until="networkidle")
        pg.wait_for_timeout(800)
        h = pg.evaluate("document.documentElement.scrollHeight")
        for i, y in enumerate(range(0, h, vp["height"])):
            pg.evaluate(f"window.scrollTo(0, {y})"); pg.wait_for_timeout(4600 if name == "desk" else 1200)
            pg.screenshot(path=OUT / f"{name}_{i:02d}.png")
        print(name, "height", h, "errors:", errs or "none")
    b.close()


def frames(pw, fig: str, times: list[int], mode: str | None = None, width=1080):
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": width, "height": 800}, device_scale_factor=1)
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL + f"?capture={fig}", wait_until="networkidle")
    if mode: pg.evaluate(f"__mode('{mode}')")
    el = pg.locator("main")
    for t in times:
        pg.evaluate(f"__seek({t})")
        el.screenshot(path=OUT / f"f_{fig}{'_' + mode if mode else ''}_{t:05d}.png")
    print(fig, mode, "dur", pg.evaluate("__dur()"), "errors:", errs or "none")
    b.close()


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    what = sys.argv[1] if len(sys.argv) > 1 else "page"
    with sync_playwright() as pw:
        if what == "page": page_shots(pw)
        else:
            frames(pw, "method", [1500, 4800, 7400, 9700, 14000])
            frames(pw, "method", [6500, 12000], mode="on")
            frames(pw, "method", [12500], mode="off")
            for f in ["fork", "signal", "headline", "tau_frontier", "curriculum", "forgetting", "routing"]:
                frames(pw, f, [99999])
