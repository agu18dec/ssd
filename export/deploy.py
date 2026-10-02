"""Rebuild dist/ and force-push it to the gh-pages branch of agu18dec/ssd-distill (served at https://agu18dec.github.io/ssd-distill/)."""
import shutil
import subprocess
import tempfile
from pathlib import Path

import build_static

ROOT = Path(__file__).resolve().parent.parent
REMOTE = "git@github.com:agu18dec/ssd-distill.git"


def git(*args, cwd): subprocess.run(["git", *args], cwd=cwd, check=True)


def main():
    build_static.main()
    rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    tmp = Path(tempfile.mkdtemp(prefix="ssd-pages-")) / "site"
    shutil.copytree(ROOT / "dist", tmp)
    git("init", "-q", "-b", "gh-pages", cwd=tmp)
    git("add", "-A", cwd=tmp)
    git("commit", "-qm", f"Deploy site from {rev}", cwd=tmp)
    git("push", "-f", REMOTE, "gh-pages", cwd=tmp)
    shutil.rmtree(tmp.parent)
    print("deployed", rev, "-> https://agu18dec.github.io/ssd-distill/")


if __name__ == "__main__":
    main()
