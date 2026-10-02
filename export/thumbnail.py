"""Render the blog cover / social thumbnail (1600x900 PNG): an explanatory diagram of one SSD rollout.

usage: uv run python export/thumbnail.py   ->  site/static/media/thumbnail.png
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / "site/static/media/thumbnail.png"
W, H = 1600, 900
INK, MUTED, BG = "#1f2a44", "#5b6276", "#fbf8f2"
T, T_FILL, T_INK = "#e8702a", "#ffe0c8", "#8a3a0e"
S, S_FILL, S_INK = "#1b97c4", "#d3eefa", "#0c5470"
RED = "#c2372f"

TOKENS = [("Marketing", "s"), ("team", "s"), ("is", "s"), ("led", "t"), ("by", "s"), ("Lina", "t"), ("Okafor", "t"),
          ("with", "s"), ("12", "t"), ("people", "s")]
DELTA = [.10, .05, .07, .58, .04, .66, .62, .06, .52, .05]
TAU = .30


def robot(x, y, body, face, teacher=False):
    hat = (f'<polygon points="{x-56},{y-62} {x},{y-86} {x+56},{y-62} {x},{y-38}" fill="{INK}"/>'
           f'<rect x="{x-27}" y="{y-64}" width="54" height="20" fill="{INK}"/>'
           f'<path d="M{x+42},{y-66} v34" stroke="{T}" stroke-width="5"/><circle cx="{x+42}" cy="{y-28}" r="7" fill="{T}"/>') if teacher else \
          (f'<path d="M{x},{y-48} v-20" stroke="{INK}" stroke-width="6"/><circle cx="{x}" cy="{y-73}" r="9" fill="{S}" stroke="{INK}" stroke-width="4"/>')
    return f'''<g>
      <rect x="{x-62}" y="{y-46}" width="124" height="102" rx="24" fill="{body}" stroke="{INK}" stroke-width="6"/>
      <rect x="{x-44}" y="{y-24}" width="88" height="50" rx="14" fill="{face}" stroke="{INK}" stroke-width="4"/>
      <circle cx="{x-19}" cy="{y+1}" r="9" fill="{INK}"/><circle cx="{x+19}" cy="{y+1}" r="9" fill="{INK}"/>
      <rect x="{x-74}" y="{y-10}" width="12" height="32" rx="5" fill="{INK}"/><rect x="{x+62}" y="{y-10}" width="12" height="32" rx="5" fill="{INK}"/>
      {hat}</g>'''


def scene() -> str:
    # layout
    x0, ty, th, gap = 470, 470, 60, 10
    slots, x = [], x0
    for tok, src in TOKENS:
        w = 15.6 * len(tok) + 26
        slots.append((x, w, tok, src)); x += w + gap
    x_end = x - gap
    base, bar_h = 800, 180
    tau_y = base - TAU / .7 * bar_h

    toks, bars, flags = [], [], []
    for (sx, w, tok, src), d in zip(slots, DELTA):
        fill, ink = (T_FILL, T_INK) if src == "t" else (S_FILL, S_INK)
        stroke = T if src == "t" else S
        toks.append(f'<rect x="{sx}" y="{ty}" width="{w}" height="{th}" rx="13" fill="{fill}" stroke="{stroke}" stroke-width="4"/>'
                    f'<text x="{sx+w/2}" y="{ty+40}" text-anchor="middle" class="tok" fill="{ink}">{tok}</text>')
        bh = d / .7 * bar_h
        bars.append(f'<rect x="{sx+8}" y="{base-bh}" width="{w-16}" height="{bh}" rx="5" fill="{stroke}" opacity="{1 if src == "t" else .75}"/>')
        if src == "t":   # inflection flag above each teacher token
            cx = sx + w / 2
            flags.append(f'<path d="M{cx},{ty-10} v-34" stroke="{T}" stroke-width="4"/>'
                         f'<polygon points="{cx-9},{ty-40} {cx+9},{ty-40} {cx},{ty-26}" fill="{T}"/>')

    # arrows from the two models into the tape
    first_t = [s for s in slots if s[3] == "t"][1]   # point the teacher arrow at "Lina"
    arrows = (
        # student -> tape start (writes by default)
        f'<path d="M265,640 C340,640 380,{ty+th/2} {x0-14},{ty+th/2}" fill="none" stroke="{S}" stroke-width="6"/>'
        f'<polygon points="{x0-14},{ty+th/2-10} {x0-14},{ty+th/2+10} {x0+2},{ty+th/2}" fill="{S}"/>'
        f'<text x="292" y="676" class="lab" fill="{S_INK}">writes by default</text>'
        # teacher -> first inflection token
        f'<path d="M265,290 C{first_t[0]-40},290 {first_t[0]+first_t[1]/2},330 {first_t[0]+first_t[1]/2},{ty-54}" fill="none" '
        f'stroke="{T}" stroke-width="6" stroke-dasharray="14 10"/>'
    )
    callout = (f'<g transform="translate({first_t[0]+first_t[1]/2+34},318)">'
               f'<text class="call" fill="{T_INK}">inflection token: δ<tspan class="subt" dy="8">t</tspan><tspan dy="-8"> &gt; τ</tspan></text>'
               f'<text y="32" class="lab" fill="{MUTED}">teacher and student disagree,</text>'
               f'<text y="60" class="lab" fill="{MUTED}">so the teacher writes it</text></g>')
    doc = (f'<g transform="translate(232,192) rotate(-8) scale(.62)"><rect width="96" height="122" rx="8" fill="#fff" stroke="{INK}" stroke-width="6"/>'
           + "".join(f'<rect x="16" y="{22+i*18}" width="{64 - (i % 2) * 18}" height="7" rx="3" fill="{T}"/>' for i in range(5)) + '</g>')
    legend_y = 860
    return f'''
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect width="{W}" height="{H}" fill="{BG}"/>
  <text x="80" y="118" class="title">Speculative Self-Distillation</text>
  <text x="82" y="170" class="sub">The student writes the rollout. The teacher takes over only where the document changes the next token.</text>

  {robot(190, 300, T_FILL, "#fff4ea", teacher=True)}{doc}
  <text x="190" y="392" text-anchor="middle" class="who" fill="{T_INK}">Teacher</text>
  <text x="190" y="420" text-anchor="middle" class="lab" fill="{MUTED}">reads the document</text>
  {robot(190, 640, S_FILL, "#f2fbff")}
  <text x="190" y="732" text-anchor="middle" class="who" fill="{S_INK}">Student</text>
  <text x="190" y="760" text-anchor="middle" class="lab" fill="{MUTED}">closed-book</text>

  {arrows}{callout}
  <rect x="{x0-4}" y="{ty-112}" width="0" height="0"/>
  <text x="{x0}" y="{ty-78}" class="prompt" fill="{MUTED}">“Tell me about the marketing team.”</text>
  {"".join(flags)}{"".join(toks)}

  <line x1="{x0}" y1="{base}" x2="{x_end}" y2="{base}" stroke="{INK}" stroke-width="3"/>
  {"".join(bars)}
  <line x1="{x0-10}" y1="{tau_y}" x2="{x_end+10}" y2="{tau_y}" stroke="{RED}" stroke-width="4" stroke-dasharray="14 10"/>
  <text x="{x_end+22}" y="{tau_y+12}" class="tau">τ</text>
  <text x="{x0-24}" y="{base-60}" text-anchor="end" class="lab" fill="{MUTED}">divergence δ<tspan class="subs" dy="6">t</tspan></text>
  <text x="{x0-24}" y="{base-30}" text-anchor="end" class="lab" fill="{MUTED}">per token</text>

  <g transform="translate({x0},{legend_y})">
    <rect width="26" height="22" rx="5" y="-18" fill="{S_FILL}" stroke="{S}" stroke-width="3"/><text x="38" class="lab" fill="{INK}">student token</text>
    <rect x="250" width="26" height="22" rx="5" y="-18" fill="{T_FILL}" stroke="{T}" stroke-width="3"/><text x="288" class="lab" fill="{INK}">teacher token</text>
    <line x1="500" x2="540" y1="-7" y2="-7" stroke="{RED}" stroke-width="4" stroke-dasharray="10 7"/><text x="552" class="lab" fill="{INK}">threshold τ</text>
  </g>
</svg>'''


HTML = """<html><head>
<link href="https://fonts.googleapis.com/css2?family=Literata:opsz,wght@7..72,600&family=JetBrains+Mono:wght@700&family=Inter:wght@500;600;700&display=swap" rel="stylesheet">
<style>
 body{margin:0} .title{font:600 70px Literata,serif;fill:%(ink)s} .sub{font:500 27px Inter,sans-serif;fill:%(muted)s}
 .tok{font:700 26px 'JetBrains Mono',monospace} .who{font:700 30px Inter,sans-serif} .lab{font:500 22px Inter,sans-serif}
 .call{font:700 26px Inter,sans-serif} .subt{font-size:18px} .subs{font-size:15px} .prompt{font:italic 500 25px Inter,sans-serif}
 .tau{font:italic 600 40px Literata,serif;fill:%(red)s}
</style></head><body>%(svg)s</body></html>"""


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        pg.set_content(HTML % {"ink": INK, "muted": MUTED, "red": RED, "svg": scene()}, wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(300)
        pg.screenshot(path=str(OUT))
        b.close()
    print("wrote", OUT)


if __name__ == "__main__":
    main()
