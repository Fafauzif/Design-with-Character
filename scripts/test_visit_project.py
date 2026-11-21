"""Exercise the transferable runner on the flagship and a disposable independent project."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from check import ROOT
from check_browser import preview
from visit_project import local_base, visit


def fixture(root):
    pages = root / "site"
    pages.mkdir()
    (pages / "weather").mkdir()
    (pages / "weather/404.html").write_text("<head></head><body>Missing record</body>", encoding="utf-8")
    (pages / "index.html").write_text(
        '<meta name="viewport" content="width=device-width"><h1>Crate radio</h1>'
        '<a href="set.html">Pick a record</a>', encoding="utf-8")
    (pages / "set.html").write_text(
        '<meta name="viewport" content="width=device-width"><h1>Side B</h1>', encoding="utf-8")
    plan = {"version": 1, "audience": "Record collectors", "primary_task": "Read the reverse-side track list",
            "subject_detail": "A hand-lettered sleeve hides its reverse side.", "shared": ["Readable sleeve labels"],
            "routes": [{"id": "sleeve", "job": "Find the record", "composition": "A single sleeve",
                        "action": "Turn the sleeve", "return_path": "Return to the sleeve", "states": ["Front", "Reverse"],
                        "examples": ["index.html", "set.html"]}],
            "journeys": [{"goal": "Read a B-side", "through": ["sleeve"], "success": "The reverse side is visible."}]}
    (root / "site-plan.json").write_text(json.dumps(plan), encoding="utf-8")
    recipe = {"version": 1, "journeys": [{"name": "Turn the sleeve", "start": "index.html",
               "steps": [{"press": ["a", "Enter"]}, {"text": ["h1", "Side B"]}]}]}
    (root / "browser-journeys.json").write_text(json.dumps(recipe), encoding="utf-8")
    return pages


def main():
    executable = os.getenv("DWC_CHROMIUM")
    with preview(ROOT) as base:
        visit(ROOT / "examples/weather-project", base + "weather/", None, executable, False)
    try:
        local_base("https://example.org/")
    except ValueError:
        pass
    else:
        raise AssertionError("A public site passed the local-only URL check")
    with TemporaryDirectory(prefix="creative-site-visits-") as temp:
        root = Path(temp)
        pages = fixture(root)
        with preview(pages) as base:
            visit(root, base, "sleeve", executable, False)
            with (pages / "set.html").open("a", encoding="utf-8") as output:
                output.write('<div style="width:800px">Overflow on mobile</div><script>throw Error("unmounted sleeve")</script>')
            try:
                visit(root, base, "sleeve", executable, False)
            except ValueError as error:
                if "exceeds viewport" not in str(error) or "unmounted sleeve" not in str(error):
                    raise
            else:
                raise AssertionError("The runner accepted broken mobile layout and a runtime error")
    print("Transfer check passed, including rejection of two injected faults.")


if __name__ == "__main__":
    main()
