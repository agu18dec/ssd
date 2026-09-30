"""Freeze the FastHTML app into dist/ (index.html + static/) for GitHub Pages. No server needed to run this."""
import shutil
import sys
from pathlib import Path

from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "site"))
import app  # noqa: E402  (serve() is a no-op on import)

DIST = ROOT / "dist"


def main():
    shutil.rmtree(DIST, ignore_errors=True)
    shutil.copytree(ROOT / "site/static", DIST / "static")
    html = TestClient(app.app).get("/").text
    (DIST / "index.html").write_text(html)
    (DIST / ".nojekyll").write_text("")
    size = sum(f.stat().st_size for f in DIST.rglob("*") if f.is_file())
    print(f"wrote {DIST} ({size / 1e6:.1f} MB, index.html {len(html) / 1e3:.0f} KB)")


if __name__ == "__main__":
    main()
