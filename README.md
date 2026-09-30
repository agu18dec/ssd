# Speculative Self-Distillation — blog

Live: https://agu18dec.github.io/ssd/ (served from the `gh-pages` branch).

FastHTML explainer for the SSD paper, with animated figures and GIF/MP4 exports.

```bash
uv sync
uv run python site/app.py            # dev server on :5001
uv run pytest -q tests               # smoke tests
uv run python export/build_static.py # freeze to dist/ for GitHub Pages
uv run python export/deploy.py       # build + force-push dist/ to gh-pages
uv run python export/record.py       # re-record site/static/media/*.gif|mp4 (needs the dev server + ffmpeg)
uv run python export/shots.py page   # screenshots for review
```

Data: `data/*.json` was recovered from the paper's vector figure PDFs by `extract/build_data.py`
(needs the paper source unzipped into `src/paper/`, which is gitignored). `extract/check.py` overlays
the recovered curves on the original rasters.
