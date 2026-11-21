"""Exercise a sixth contribution in a disposable, clean copy of the checkout."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DEMO = """<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Shadow Stage</title>
<style>
body{max-width:48rem;margin:0 auto;padding:1.5rem;background:#20142d;color:#fff1d3;font:1rem/1.5 system-ui}
h1{font:2.75rem Georgia,serif;margin:.25em 0}
.stage{height:clamp(8rem,36vh,18rem);display:grid;place-items:center;overflow:hidden;background:#f6df9b}
.bird{width:8rem;height:5rem;clip-path:polygon(0 70%,40% 46%,16% 0,58% 38%,85% 22%,98% 35%,86% 40%,68% 78%,32% 100%);background:#302135}
[aria-expanded=false] + section .bird{visibility:hidden}
button{padding:.8rem;font:inherit;color:#28182e;background:#efb66c;border:0;cursor:pointer}
button:focus-visible{outline:3px solid #fff;outline-offset:4px}section{margin-top:1.25rem}
</style>
<main><h1>Shadow Stage</h1><button type="button" id="lamp" aria-expanded="false" aria-controls="performance">Light the screen</button>
<section aria-label="Paper theater" id="performance"><div class="stage"><div class="bird"></div></div><p id="scene" aria-live="polite">The stage is empty.</p></section></main>
<script>
const lamp=document.querySelector('#lamp'), scene=document.querySelector('#scene');
lamp.addEventListener('click',()=>{
 const lit=lamp.getAttribute('aria-expanded')==='false';
 lamp.setAttribute('aria-expanded', String(lit));
 lamp.textContent=lit?'Lower the lamp':'Light the screen';
 scene.textContent=lit?'A heron crosses the screen.':'The stage is empty.';
});
</script></html>"""
GUIDE = """# Shadow Stage

## Experience
A visitor lights a paper theater to uncover a heron. The silhouette appears at the same time as its spoken description.

## Composition
The screen occupies the width of the tabletop. The control stays immediately above it on a phone. The paper shadow is legible in the changed state.

## Material and palette
The cream scrim carries the dark figure. One amber control stays close to the edge of the stage.

## Interaction
Tab to the lamp and press Enter. Focus stays at the switch while a polite status names the bird. A second press lowers the lamp. Both states are still.

## Transfer
A bird club could show a different recognizable outline per species. Its sighting directory would use small silhouettes and searchable entries. The full stage belongs at the performance.

## References and provenance
The scene and CSS silhouette are original to the fixture. The gallery captures document the local demo and its two lamp states.

## Review evidence
The fixture tests both button states via the keyboard at desktop and phone size. Verification covers the document and its observable status. Physical-device handling and human identification of the silhouette remain untested.
"""


def json_write(path, obj):
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def run(root, *args, failure=None):
    sub = subprocess.run([sys.executable, *args], cwd=root, capture_output=True, text=True)
    evidence = sub.stdout + sub.stderr
    if failure is None and sub.returncode:
        raise AssertionError(f"{args} failed:\n{evidence}")
    if failure is not None and (not sub.returncode or failure not in evidence):
        raise AssertionError(f"{args} should report {failure!r}, got:\n{evidence}")


def exercise(root):
    add = "scripts/add_style.py"
    title_args = ("Shadow Stage", "--description", "Light a tabletop screen to reveal a paper heron.",
                  "--action", "Light the screen", "--medium", "Shadow theater",
                  "--palette", "#20142d", "#fff1d3", "#efb66c")
    catalog = root / "styles/catalog.json"
    original = catalog.read_bytes()
    slug = "shadow-stage"
    while (root / "styles" / slug).exists() or (root / f"{slug}.html").exists():
        slug += "-proof"
    for reserved in ("../outside", "gallery", "com1"):
        run(root, add, reserved, *title_args, failure="slug")
    run(root, add, slug, *title_args)
    run(root, add, slug, *title_args, failure="already in use")
    run(root, add, "--preview", slug)
    assert "data-style-starter" in (root / ".style-work" / f"{slug}.html").read_text(encoding="utf-8")
    run(root, add, "--publish", slug, failure="actual experience")
    assert catalog.read_bytes() == original

    draft = root / "styles" / slug
    (draft / "demo.html").write_text(DEMO, encoding="utf-8")
    run(root, add, "--check-ready", slug, failure="[[prompts]]")
    (draft / "STYLE.md").write_text(GUIDE, encoding="utf-8")
    meta = draft / "style.json"
    data = json.loads(meta.read_text(encoding="utf-8"))
    journey = [{"press": ["#lamp", "Enter"]}, {"text": ["#scene", "A heron crosses the screen."]},
               {"press": ["#lamp", "Space"]}, {"attribute": ["#lamp", "aria-expanded", "false"]}]
    data["journey"] = journey
    json_write(meta, data)
    run(root, add, "--preview", slug)
    recipe = draft / "capture.py"
    recipe.write_text('def changed(page):\n    page.locator("#lamp").press("Enter")\n', encoding="utf-8")
    arguments = ["gallery-assets/capture.py", slug, "--recipe", str(recipe), "--page",
                 str(root / ".style-work" / f"{slug}.html")]
    if executable := os.getenv("DWC_CHROMIUM"):
        arguments += ["--chromium", executable]
    run(root, *arguments)
    captures = root / "gallery-assets/previews.json"
    pairs = json.loads(captures.read_text(encoding="utf-8"))
    pairs[slug] = {"opening": "A cream paper screen sits empty.",
                   "changed": "A heron appears on the lit screen."}
    json_write(captures, pairs)
    run(root, add, "--publish", slug, failure="per-file provenance")
    assert catalog.read_bytes() == original

    credits = root / "credits/assets.json"
    assets = json.loads(credits.read_text(encoding="utf-8"))
    for frame in sorted((root / "gallery-assets" / slug).glob("*.webp")):
        assets.append({"path": frame.relative_to(root).as_posix(), "origin": "Local browser capture",
                       "credit": "Shadow Stage test fixture", "terms": "MIT, as part of this fixture."})
    json_write(credits, assets)
    run(root, add, "--check-ready", slug)
    # An apparently valid recipe with an impossible expectation must fail without registration.
    data["journey"] = [{"click": "#lamp"}, {"text": ["#scene", "The lamp sings."]}]
    json_write(meta, data)
    run(root, add, "--publish", slug, failure="Journey step")
    assert catalog.read_bytes() == original
    data["journey"] = journey
    json_write(meta, data)
    run(root, add, "--publish", slug)
    assert [x["slug"] for x in json.loads(catalog.read_text())].count(slug) == 1
    run(root, add, "--publish", slug, failure="already in use")
    data["description"] = "Light a paper theater to find the heron, then lower the lamp."
    json_write(meta, data)
    run(root, add, "--refresh", slug)
    items = json.loads(catalog.read_text(encoding="utf-8"))
    assert [r["description"] for r in items if r["slug"] == slug] == [data["description"]]
    run(root, "scripts/build.py")
    run(root, "scripts/build.py", "--check")
    run(root, "scripts/check.py")
    run(root, "scripts/check_browser.py", "--only", "community")
    run(root, "scripts/check_browser.py", "--only", "gallery")


def main():
    with tempfile.TemporaryDirectory(prefix="design-contributor-") as tmp:
        copy = Path(tmp) / "checkout"
        shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", ".style-work", "__pycache__",
                                                                  ".venv", "node_modules", ".design-moves"))
        exercise(copy)
    print("Sixth style passed scaffold, blocked releases, browser promotion, export, catalog and gallery replay.")


if __name__ == "__main__":
    main()
