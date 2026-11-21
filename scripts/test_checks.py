"""Prove release checks reject specific defects in a disposable copy of this project."""
from contextlib import contextmanager
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from check import ROOT


@contextmanager
def changed(path, content):
    existed = path.exists()
    before = path.read_bytes() if existed else None
    path.write_bytes(content)
    try:
        yield
    finally:
        if existed:
            path.write_bytes(before)
        else:
            path.unlink()


def cli(root):
    return subprocess.run([sys.executable, str(ROOT / "scripts/check.py"), "--root", str(root)],
                          capture_output=True, text=True, check=False)


def rejected(root, path, content, diagnostic):
    with changed(path, content):
        result = cli(root)
        if result.returncode == 0 or diagnostic not in result.stderr:
            raise AssertionError(f"Expected rejection '{diagnostic}' for {path.name}; got:\n{result.stdout}{result.stderr}")


def main():
    with TemporaryDirectory(prefix="character-checks-") as temporary:
        project = Path(temporary) / "release"
        shutil.copytree(ROOT, project, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", ".venv"))
        baseline = cli(project)
        if baseline.returncode:
            raise SystemExit("Release must pass before fault tests run:\n" + baseline.stderr)
        catalog = json.loads((project / "styles/catalog.json").read_text(encoding="utf-8"))
        export = project / f"{catalog[0]['slug']}.html"
        rejected(project, export, export.read_bytes() + b"<!-- edit -->", "Stale exports")
        page = project / "weather/collection.html"
        original = page.read_bytes()
        for element, message in [
            ('<a href="absent-page.html">Link</a>', "missing or outside"),
            ('<a href="../../outside.html">Link</a>', "missing or outside"),
            ('<a href="notes.html#invented-target">Notes</a>', "missing destination id"),
            ('<img src="https://example.org/dependency.png" alt="">', "network dependency"),
            ('<button aria-controls="missing-state">Action</button>', "refers to missing id"),
            ('<link rel="stylesheet" href="/weather/main.css">', "directory-relative URL")
        ]:
            rejected(project, page, original.replace(b"</body>", element.encode() + b"</body>"), message)
        rejected(project, project / "weather/unattributed.webp", b"fixture", "uncredited media")
        manifest = project / "credits/assets.json"
        records = json.loads(manifest.read_text(encoding="utf-8"))
        invalid_credit = [{**records[0], "terms": "TBD"}, *records[1:]]
        rejected(project, manifest, json.dumps(invalid_credit).encode(), "fill out path, origin, credit, terms")
    print("Nine deliberate release faults rejected; project files left untouched.")


if __name__ == "__main__":
    main()
