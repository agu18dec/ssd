"""Render the blog cover / social thumbnail (1600x900 PNG) from a hand-built SVG scene.

usage: uv run python export/thumbnail.py   ->  site/static/media/thumbnail.png
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / "site/static/media/thumbnail.png"
W, H = 1600, 900
INK, PAPER = "#1f2a44", "#f3ead8"
T, T_FILL, S, S_FILL, X_FILL = "#e8702a", "#ffd9bd", "#1b97c4", "#cbe9f6", "#e6e2da"
RED = "#c2372f"

TOKENS = [("Marketing", "s"), ("team", "s"), ("is", "s"), ("led", "t"), ("by", "s"), ("Lina", "t"), ("Okafor", "t"),
          ("with", "s"), ("12", "t"), ("people", "s")]
DELTA = [.10, .05, .07, .58, .04, .66, .62, .06, .52, .05]


def robot(x, y, body, face, teacher=False):
    """A simple geometric robot head at (x, y): rounded head, visor, two eyes, antenna (teacher gets a mortarboard)."""
    hat = (f'<polygon points="{x-70},{y-78} {x},{y-108} {x+70},{y-78} {x},{y-48}" fill="{INK}"/>'
           f'<rect x="{x-34}" y="{y-80}" width="68" height="26" fill="{INK}"/>'
           f'<path d="M{x+52},{y-82} v42" stroke="{T}" stroke-width="6"/><circle cx="{x+52}" cy="{y-36}" r="9" fill="{T}"/>') if teacher else \
          (f'<path d="M{x},{y-62} v-26" stroke="{INK}" stroke-width="7"/><circle cx="{x}" cy="{y-94}" r="11" fill="{S}" stroke="{INK}" stroke-width="5"/>')
    return f'''
    <g>
      <rect x="{x-78}" y="{y-58}" width="156" height="128" rx="30" fill="{body}" stroke="{INK}" stroke-width="7"/>
      <rect x="{x-56}" y="{y-30}" width="112" height="62" rx="18" fill="{face}" stroke="{INK}" stroke-width="5"/>
      <circle cx="{x-24}" cy="{y+1}" r="11" fill="{INK}"/><circle cx="{x+24}" cy="{y+1}" r="11" fill="{INK}"/>
      <circle cx="{x-20}" cy="{y-3}" r="4" fill="#fff"/><circle cx="{x+28}" cy="{y-3}" r="4" fill="#fff"/>
      <rect x="{x-92}" y="{y-12}" width="14" height="40" rx="6" fill="{INK}"/><rect x="{x+78}" y="{y-12}" width="14" height="40" rx="6" fill="{INK}"/>
      {hat}
    </g>'''


def scene() -> str:
    # token tape
    x, ty, toks, bars = 300, 520, [], []
    for (tok, src), d in zip(TOKENS, DELTA):
        w = 17.4 * len(tok) + 30
        fill, stroke = (T_FILL, T) if src == "t" else (S_FILL, S)
        toks.append(f'<rect x="{x+6}" y="{ty+6}" width="{w}" height="60" rx="13" fill="{INK}"/>'
                    f'<rect x="{x}" y="{ty}" width="{w}" height="60" rx="13" fill="{fill}" stroke="{INK}" stroke-width="5"/>'
                    f'<text x="{x+w/2}" y="{ty+40}" text-anchor="middle" class="tok">{tok}</text>')
        bh = d * 190
        bars.append(f'<rect x="{x+10}" y="{790-bh}" width="{w-20}" height="{bh}" rx="6" fill="{T if src == "t" else S}" '
                    f'stroke="{INK}" stroke-width="4"/>')
        x += w + 12
    tau_y = 790 - .3 * 190
    deco = "".join(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{c}" opacity=".55"/>' for cx, cy, r, c in
                   [(1380, 170, 150, "#e9c46a"), (1500, 330, 90, "#9ec5b0"), (180, 760, 120, "#9ec5b0"), (1450, 720, 70, "#f2a679")])
    rays = "".join(f'<line x1="1380" y1="170" x2="{1380+260*__import__("math").cos(a/12*6.283)}" '
                   f'y2="{170+260*__import__("math").sin(a/12*6.283)}" stroke="#e9c46a" stroke-width="10" opacity=".35"/>' for a in range(12))
    doc = (f'<g transform="translate(262,352) rotate(-8) scale(.82)"><rect x="8" y="8" width="96" height="122" rx="8" fill="{INK}"/>'
           f'<rect width="96" height="122" rx="8" fill="#fffaf0" stroke="{INK}" stroke-width="5"/>'
           + "".join(f'<rect x="16" y="{22+i*18}" width="{64 - (i % 2) * 18}" height="7" rx="3" fill="{T}" opacity=".7"/>' for i in range(5))
           + f'<text x="48" y="160" text-anchor="middle" class="ctx">C</text></g>')
    return f'''
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" stitchTiles="stitch"/>
      <feColorMatrix values="0 0 0 0 .12  0 0 0 0 .1  0 0 0 0 .08  0 0 0 .09 0"/></filter>
  </defs>
  <rect width="{W}" height="{H}" fill="{PAPER}"/>
  <clipPath id="frame"><rect x="44" y="44" width="{W-88}" height="{H-88}" rx="18"/></clipPath>
  <g clip-path="url(#frame)">{rays}{deco}</g>
  <rect width="{W}" height="{H}" filter="url(#grain)"/>
  <rect x="26" y="26" width="{W-52}" height="{H-52}" rx="26" fill="none" stroke="{INK}" stroke-width="8"/>
  <rect x="44" y="44" width="{W-88}" height="{H-88}" rx="18" fill="none" stroke="{INK}" stroke-width="3"/>

  <text x="330" y="148" class="title">Speculative</text>
  <text x="330" y="236" class="title">Self-Distillation</text>
  <text x="334" y="296" class="sub">the student writes · the teacher steps in where it matters</text>

  {robot(170, 300, T_FILL, "#fff4ea", teacher=True)}
  {robot(170, 560, S_FILL, "#f2fbff")}
  {doc}
  <path d="M170,384 v66" stroke="{INK}" stroke-width="5" stroke-dasharray="10 10"/>

  {"".join(toks)}
  <line x1="300" y1="790" x2="{x}" y2="790" stroke="{INK}" stroke-width="5"/>
  {"".join(bars)}
  <line x1="290" y1="{tau_y}" x2="{x+10}" y2="{tau_y}" stroke="{RED}" stroke-width="6" stroke-dasharray="18 12"/>
  <text x="{x+24}" y="{tau_y+14}" class="tau">τ</text>
  <text x="170" y="790" text-anchor="middle" class="delta">δₜ</text>
</svg>'''


HTML = """<html><head>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=JetBrains+Mono:wght@700&family=Inter:wght@600&display=swap" rel="stylesheet">
<style>
 body{margin:0} .title{font:400 92px 'DM Serif Display',serif;fill:%(ink)s}
 .sub{font:600 30px Inter,sans-serif;fill:#5b6276;letter-spacing:.01em}
 .tok{font:700 29px 'JetBrains Mono',monospace;fill:%(ink)s} .ctx{font:italic 400 40px 'DM Serif Display',serif;fill:%(ink)s}
 .tau{font:italic 400 54px 'DM Serif Display',serif;fill:%(red)s} .delta{font:italic 400 50px 'DM Serif Display',serif;fill:%(ink)s}
</style></head><body>%(svg)s</body></html>"""


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        pg.set_content(HTML % {"ink": INK, "red": RED, "svg": scene()}, wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(300)
        pg.screenshot(path=str(OUT))
        b.close()
    print("wrote", OUT)


if __name__ == "__main__":
    main()
