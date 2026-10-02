import json
import sys
from pathlib import Path

from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "site"))
import app  # noqa: E402

client = TestClient(app.app)


def test_index_renders_every_section_and_figure():
    html = client.get("/").text
    for sec in ["setup", "why", "inflection", "method", "results", "knob", "curriculum", "forgetting", "routing", "citation"]:
        assert f'id="{sec}"' in html
    for fig in app.CAPTURE:
        assert f'data-fig="{fig}"' in html


def test_ids_are_unique():
    import re
    ids = re.findall(r'\sid="([^"]+)"', client.get("/").text)
    assert len(ids) == len(set(ids)), sorted({i for i in ids if ids.count(i) > 1})


def test_capture_pages():
    for fig in app.CAPTURE:
        r = client.get(f"/?capture={fig}")
        assert r.status_code == 200 and f'data-fig="{fig}"' in r.text


def test_data_matches_paper_numbers():
    h = json.loads((ROOT / "data/headline.json").read_text())
    for p in h["panels"]:
        s = p["series"]
        assert round(100 * (1 - s["ssd"]["x"][-1] / s["on"]["x"][-1])) == p["saving"]
    taus = [q["tau"] for q in json.loads((ROOT / "data/tau_frontier.json").read_text())["points"] if q["kind"] == "ssd"]
    assert taus == sorted(taus) and len(taus) == 10


def test_static_assets_exist():
    for f in ["static/site.css", "static/anim.js", "static/logos/stanford_color.png", "static/logos/eth.svg", "static/media/thumbnail.png"]:
        assert (ROOT / "site" / f).exists()
    for _, m in app.MEDIA:
        assert (ROOT / "site/static/media" / f"{m}.gif").exists()
