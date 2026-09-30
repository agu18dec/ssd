"""Record each animated figure to GIF + MP4 by seeking its render(t) frame by frame (deterministic, no screen capture).

usage: uv run python export/record.py [fig ...]   (server must be running on :5001)
Outputs land in site/static/media/<name>.gif|.mp4 so the page can link them as downloads.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:5001/"
OUT = Path(__file__).resolve().parent.parent / "site/static/media"
FPS = 20
# name -> (capture figure, viewport width, rollout mode for the method figure, hold at the end in ms)
TARGETS = {
    "method_ssd": ("method", 1080, "ssd", 0),
    "method_onpolicy": ("method", 1080, "on", 0),
    "fork": ("fork", 1080, None, 0),
    "signal": ("signal", 1080, None, 1800),
    "headline": ("headline", 1080, None, 2200),
    "tau_frontier": ("tau_frontier", 740, None, 1800),
    "curriculum": ("curriculum", 1080, None, 1800),
}


def record(pw, name: str):
    fig, width, mode, hold = TARGETS[name]
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": width, "height": 900}, device_scale_factor=2)
    pg.goto(URL + f"?capture={fig}", wait_until="networkidle")
    pg.evaluate("document.fonts.ready")
    if mode: pg.evaluate(f"__mode('{mode}')")
    dur = pg.evaluate("__dur()")
    n = int((dur + hold) / 1000 * FPS)
    tmp = Path(tempfile.mkdtemp(prefix=f"rec_{name}_"))
    el = pg.locator("main")
    for i in range(n):
        pg.evaluate(f"__seek({min(i * 1000 / FPS, dur - 1)})")
        el.screenshot(path=tmp / f"{i:05d}.png")
    b.close()
    OUT.mkdir(parents=True, exist_ok=True)
    frames = str(tmp / "%05d.png")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", frames,
                    "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                    "-movflags", "+faststart", str(OUT / f"{name}.mp4")], check=True)
    gif_w = 900 if width > 800 else 640
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", frames, "-vf",
                    f"fps=15,scale={gif_w}:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];"
                    f"[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle", "-loop", "0", str(OUT / f"{name}.gif")], check=True)
    shutil.rmtree(tmp)
    print(f"{name:16s} {n:4d} frames  gif {(OUT / f'{name}.gif').stat().st_size / 1e6:5.2f} MB  "
          f"mp4 {(OUT / f'{name}.mp4').stat().st_size / 1e6:5.2f} MB")


if __name__ == "__main__":
    names = sys.argv[1:] or list(TARGETS)
    with sync_playwright() as pw:
        for nm in names: record(pw, nm)
