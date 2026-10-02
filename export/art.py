"""Cover art and logo for the SSD blog, drawn as SVG and rasterized with headless Chromium.

Motif: two token strands, one from the teacher ("professor", warm) and one from the student (cool), twist around
each other like a double helix and merge into a single mixed sequence: an SSD rollout.

usage: uv run python export/art.py   ->  site/static/media/thumbnail.png, site/static/logos/ssd_logo.{svg,png}, favicon
"""
import math
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
W, H = 1600, 900
NAVY0, NAVY1 = "#0b1124", "#1a2450"
WARM, WARM2 = "#ff9a4a", "#ffcf8a"      # teacher strand
COOL, COOL2 = "#3cc4f0", "#9fe6ff"      # student strand


def helix(x0, x1, cy, amp, twists, n, decay_to):
    """Points for two strands: y = cy -/+ a(x) cos(phase), with depth z = sin(phase); a(x) decays linearly to 0 at decay_to."""
    pts = []
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        a = amp * max(0.0, 1 - (x - x0) / (decay_to - x0))
        ph = 2 * math.pi * twists * (x - x0) / (decay_to - x0)
        pts.append((x, cy - a * math.cos(ph), cy + a * math.cos(ph), math.sin(ph), a))
    return pts


def path(xy): return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in xy)


def thumbnail_svg() -> str:
    cy, x0, xm, x1 = 540, 150, 1150, 1500
    P = helix(x0, xm, cy, 150, 2.5, 420, xm)
    back, front = [], []
    # rungs (base pairs): fade with amplitude, gradient warm->cool
    for i in range(0, len(P), 11):
        x, yt, ys, z, a = P[i]
        if a < 8: continue
        op = .18 + .32 * (a / 175)
        back.append(f'<line x1="{x:.1f}" y1="{yt:.1f}" x2="{x:.1f}" y2="{ys:.1f}" stroke="#e8eeff" stroke-width="2.5" '
                    f'stroke-linecap="round" opacity="{op:.2f}"/>')
    # strands, drawn in segments so the front-facing half sits on top
    for strand, col, glow in ((1, WARM, "gw"), (2, COOL, "gc")):
        seg = []
        for i in range(len(P) - 1):
            x, yt, ys, z, a = P[i]
            xb, ytb, ysb, zb, _ = P[i + 1]
            ya, yb = (yt, ytb) if strand == 1 else (ys, ysb)
            depth = z if strand == 1 else -z
            w = 5 + 3 * depth
            seg.append((depth, f'<line x1="{x:.1f}" y1="{ya:.1f}" x2="{xb:.1f}" y2="{yb:.1f}" stroke="{col}" stroke-width="{w:.1f}" '
                               f'stroke-linecap="round" opacity="{.55 + .45 * (depth + 1) / 2:.2f}"/>'))
        for d, s in seg: (front if d > 0 else back).append(s)
        # token beads along the strand
        for i in range(6, len(P), 16):
            x, yt, ys, z, a = P[i]
            y = yt if strand == 1 else ys
            depth = z if strand == 1 else -z
            r = 9 + 4 * depth
            bead = (f'<rect x="{x - r * 1.5:.1f}" y="{y - r:.1f}" width="{r * 3:.1f}" height="{2 * r:.1f}" rx="{r:.1f}" '
                    f'fill="{col}" filter="url(#{glow})" opacity="{.6 + .4 * (depth + 1) / 2:.2f}"/>')
            (front if depth > 0 else back).append(bead)
    # merged single strand: the SSD rollout, mostly student tokens with a few teacher tokens
    merged, x = [], xm + 18
    pattern = "sstssts"
    for i, src in enumerate(pattern):
        w = 30
        col = WARM if src == "t" else COOL
        merged.append(f'<rect x="{x:.1f}" y="{cy - 11}" width="{w}" height="22" rx="11" fill="{col}" filter="url(#{"gw" if src == "t" else "gc"})" '
                      f'opacity="{1 - i * .08:.2f}"/>')
        x += w + 9
    tail = f'<path d="M{xm - 10},{cy} H{x + 30}" stroke="url(#tail)" stroke-width="3" opacity=".6"/>'

    def mind(cx, cyy, col, col2, glow, prof):
        hat = (f'<g transform="translate({cx},{cyy - 96})"><polygon points="-64,0 0,-25 64,0 0,25" fill="#0e1530" stroke="{col2}" stroke-width="3"/>'
               f'<rect x="-31" y="2" width="62" height="22" rx="3" fill="#0e1530" stroke="{col2}" stroke-width="3"/>'
               f'<path d="M48,2 v36" stroke="{col2}" stroke-width="3"/><circle cx="48" cy="42" r="6" fill="{col2}"/></g>') if prof else ""
        rings = "".join(f'<ellipse cx="{cx}" cy="{cyy}" rx="{r * 1.08:.0f}" ry="{r}" fill="none" stroke="{col}" stroke-width="1.5" opacity="{o}"/>'
                        for r, o in ((104, .2), (130, .1), (158, .05)))
        # brain silhouette: an ellipse ringed with overlapping bumps (gyri) of slightly varying size
        bumps = "".join(f'<circle cx="{cx + 78 * math.cos(a):.1f}" cy="{cyy + 62 * math.sin(a):.1f}" r="{22 + 4 * math.sin(3 * a):.1f}"/>'
                        for a in [k * 2 * math.pi / 14 for k in range(14)])
        brain = f'<g fill="url(#{glow}Fill)" filter="url(#{glow})"><ellipse cx="{cx}" cy="{cyy}" rx="80" ry="64"/>{bumps}</g>'
        folds = (f'<path d="M{cx},{cyy - 78} C{cx - 8},{cyy - 30} {cx + 8},{cyy + 20} {cx},{cyy + 80}" fill="none" stroke="#0e1530" '
                 f'stroke-width="4" opacity=".45"/>'
                 + "".join(f'<path d="M{cx + sx * 20},{cyy + dy} q {sx * 16},-18 {sx * 32},-4 t {sx * 30},8" fill="none" stroke="#0e1530" '
                           f'stroke-width="3.5" stroke-linecap="round" opacity=".35"/>' for sx in (-1, 1) for dy in (-34, -2, 30)))
        return f'{rings}{brain}{folds}{hat}'

    stars = "".join(f'<circle cx="{(i * 397) % W}" cy="{(i * 211) % H}" r="{1 + (i % 3) * .5}" fill="#fff" opacity="{.08 + (i % 5) * .03:.2f}"/>'
                    for i in range(90))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <radialGradient id="bg" cx="35%" cy="45%" r="85%"><stop offset="0" stop-color="{NAVY1}"/><stop offset="1" stop-color="{NAVY0}"/></radialGradient>
    <linearGradient id="rung" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{WARM2}"/><stop offset="1" stop-color="{COOL2}"/></linearGradient>
    <linearGradient id="tail" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity=".5"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
    <radialGradient id="gwFill"><stop offset="0" stop-color="{WARM2}"/><stop offset="1" stop-color="{WARM}" stop-opacity=".55"/></radialGradient>
    <radialGradient id="gcFill"><stop offset="0" stop-color="{COOL2}"/><stop offset="1" stop-color="{COOL}" stop-opacity=".55"/></radialGradient>
    <filter id="gw" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="6" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <filter id="gc" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="6" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  {"".join(back)}{tail}
  <text x="{x0 - 14}" y="{cy - 168}" class="k" fill="{WARM2}">teacher</text>
  <text x="{x0 - 14}" y="{cy + 190}" class="k" fill="{COOL2}">student</text>
  {"".join(front)}{"".join(merged)}
  <text x="{W/2}" y="190" text-anchor="middle" class="t">Speculative Self-Distillation</text>

</svg>'''


def logo_svg(size=512) -> str:
    """Badge: a short double helix (teacher + student strands) that merges into one line at the bottom."""
    c, r = size / 2, size / 2 - 8
    pts = []
    for i in range(121):
        t = i / 120
        y = size * .17 + t * size * .66
        a = size * .2 * (1 - t) ** .8
        ph = 2 * math.pi * 1.25 * t
        pts.append((y, c - a * math.sin(ph), c + a * math.sin(ph), math.cos(ph), a))
    back, front = [], []
    for k in range(0, 121, 12):
        y, xt, xs, z, a = pts[k]
        if a > 6: back.append(f'<line x1="{xt:.1f}" y1="{y:.1f}" x2="{xs:.1f}" y2="{y:.1f}" stroke="url(#lr)" stroke-width="{size * .014:.1f}" opacity=".55"/>')
    for strand, col in ((1, WARM), (2, COOL)):
        for k in range(120):
            y, xt, xs, z, a = pts[k]
            y2, xt2, xs2, _, _ = pts[k + 1]
            xa, xb = (xt, xt2) if strand == 1 else (xs, xs2)
            d = z if strand == 1 else -z
            (front if d > 0 else back).append(f'<line x1="{xa:.1f}" y1="{y:.1f}" x2="{xb:.1f}" y2="{y2:.1f}" stroke="{col}" '
                                              f'stroke-width="{size * (.03 + .012 * d):.1f}" stroke-linecap="round"/>')
    dot = f'<circle cx="{c}" cy="{pts[-1][0] + size * .03:.1f}" r="{size * .035:.1f}" fill="#fff"/>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">
  <defs><linearGradient id="lb" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{NAVY1}"/><stop offset="1" stop-color="{NAVY0}"/></linearGradient>
  <linearGradient id="lr" x1="0" x2="1"><stop offset="0" stop-color="{WARM2}"/><stop offset="1" stop-color="{COOL2}"/></linearGradient></defs>
  <circle cx="{c}" cy="{c}" r="{r}" fill="url(#lb)"/>
  <circle cx="{c}" cy="{c}" r="{r - size * .035}" fill="none" stroke="#ffffff" stroke-opacity=".12" stroke-width="{size * .008}"/>
  {"".join(back)}{"".join(front)}{dot}
</svg>'''


CSS = ("<link href='https://fonts.googleapis.com/css2?family=Literata:opsz,wght@7..72,600&family=Inter:wght@500&display=swap' rel='stylesheet'>"
       "<style>body{margin:0;background:transparent} .t{font:600 76px Literata,serif;fill:#fff;letter-spacing:.005em}"
       " .k{font:600 26px Inter,sans-serif;letter-spacing:.06em}</style>")


def render(pg, svg: str, w: int, h: int, out: Path, transparent=False):
    pg.set_viewport_size({"width": w, "height": h})
    pg.set_content(f"<html><head>{CSS}</head><body>{svg}</body></html>", wait_until="networkidle")
    pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(200)
    pg.screenshot(path=str(out), omit_background=transparent)


def main():
    media, logos = ROOT / "site/static/media", ROOT / "site/static/logos"
    (logos / "ssd_logo.svg").write_text(logo_svg())
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page()
        render(pg, thumbnail_svg(), W, H, media / "thumbnail.png")
        render(pg, logo_svg(512), 512, 512, logos / "ssd_logo.png", transparent=True)
        render(pg, logo_svg(64), 64, 64, ROOT / "site/static/favicon.png", transparent=True)
        b.close()
    print("wrote thumbnail, logo, favicon")


if __name__ == "__main__":
    main()
