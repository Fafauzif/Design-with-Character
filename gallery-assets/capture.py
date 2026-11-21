"""Record real, offline browser frames from a working style for the gallery."""
import argparse
from importlib.util import module_from_spec, spec_from_file_location
from io import BytesIO
from pathlib import Path
import re

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BUILTINS = ("halftone-dossier", "botanical-letterpress", "specimen-cabinet",
            "arcade-workshop", "pixel-study-room")


def prepare_builtin(page, slug):
    if slug == "pixel-study-room":
        page.clock.install(time=1735689600000)


def show_builtin(page, slug):
    if slug == "halftone-dossier":
        page.locator("#open-file").click()
        for note in page.locator(".note summary").all():
            note.click()
        page.locator("#file-report").click()
    elif slug == "botanical-letterpress":
        page.locator("#folio-toggle").click()
    elif slug == "specimen-cabinet":
        page.locator(".drawer summary").first.click()
        page.locator(".keep").first.click()
        page.locator(".specimen").first.scroll_into_view_if_needed()
    elif slug == "arcade-workshop":
        page.get_by_role("button", name="Night bus").click()
        page.locator("#play").click()
        page.locator(".step[data-current=true]").first.wait_for()
    elif slug == "pixel-study-room":
        page.get_by_role("button", name="5 min", exact=True).click()
        page.locator("#action").click()
        page.clock.fast_forward(46000)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug")
    parser.add_argument("--page", type=Path, help="Working HTML file (default: root export).")
    parser.add_argument("--recipe", type=Path, help="Python file with changed(page) and optional opening(page).")
    parser.add_argument("--chromium", type=Path, help="Use an existing Chromium executable.")
    parser.add_argument("--output", type=Path, help="Override gallery-assets/<slug>/")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", args.slug):
        parser.error("Use the lowercase catalog slug.")
    if not args.recipe and args.slug not in BUILTINS:
        parser.error("Supply --recipe for your style's changed state.")
    page_path = (args.page or ROOT / (args.slug + ".html")).resolve()
    if not page_path.is_file():
        parser.error(f"Page does not exist: {page_path}")
    recipe = None
    if args.recipe:
        spec = spec_from_file_location("style_frames", args.recipe.resolve())
        if spec is None or spec.loader is None:
            parser.error("Could not load the Python recipe.")
        recipe = module_from_spec(spec)
        spec.loader.exec_module(recipe)
        if not callable(getattr(recipe, "changed", None)):
            parser.error("The recipe must define changed(page).")
    output = args.output or Path(__file__).resolve().parent / args.slug
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as driver:
        opts = {"executable_path": str(args.chromium)} if args.chromium else {}
        browser = driver.chromium.launch(**opts)
        for device, w, h in (("desktop", 1200, 800), ("phone", 390, 780)):
            context = browser.new_context(viewport={"width": w, "height": h}, offline=True,
                                          reduced_motion="reduce", device_scale_factor=1)
            page = context.new_page()
            page.goto(page_path.as_uri())
            if recipe:
                opening = getattr(recipe, "opening", None)
                if opening:
                    opening(page)
            else:
                prepare_builtin(page, args.slug)
            for state in ("opening", "changed"):
                if state == "changed":
                    if recipe:
                        recipe.changed(page)
                    else:
                        show_builtin(page, args.slug)
                page.evaluate("document.fonts.ready")
                page.evaluate("Promise.all(Array.from(document.images, i => i.decode().catch(() => {})))")
                suffix = "-action" if state == "changed" else ""
                frame = page.screenshot(animations="disabled")
                with Image.open(BytesIO(frame)) as im:
                    im.convert("RGB").save(output / f"{device}{suffix}.webp", quality=90, method=6)
            context.close()
        browser.close()
    print(f"Recorded four frames in {output}.")


if __name__ == "__main__":
    main()
