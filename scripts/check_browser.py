"""Run release journeys in real Chromium, using a fresh context for each scenario."""
import argparse
from contextlib import contextmanager
from functools import partial
from http.server import ThreadingHTTPServer
import json
import os
from pathlib import Path
from threading import Thread
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright

import browser_prototypes
import browser_weather
from check import ROOT, WEATHER_ROUTES
from serve import PreviewHandler


class QuietPreview(PreviewHandler):
    def log_message(self, *args):
        pass


@contextmanager
def preview(root):
    handler = partial(QuietPreview, directory=str(root), mount="/character")
    with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        runner = Thread(target=server.serve_forever, daemon=True)
        runner.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}/character/"
        finally:
            server.shutdown()
            runner.join()


def gallery(page, catalog):
    expect(page.get_by_role("link").and_(page.locator("[href='weather/index.html']")).first).to_be_visible()
    for entry in catalog:
        slug = entry["slug"]
        view = page.locator(f"section#{slug}")
        picker = page.locator("#style-picker")
        if picker.is_visible():
            picker.select_option(slug)
        else:
            page.locator(f"a[href='#{slug}']").first.press("Enter")
        expect(view.locator(f"a[href='{slug}.html']").first).to_be_visible()
        opening = view.locator("button[data-scene='opening']")
        changed = view.locator("button[data-scene='changed']")
        if changed.count():
            changed.press("Enter")
            expect(changed).to_have_attribute("aria-pressed", "true")
            expect(opening).to_have_attribute("aria-pressed", "false")
            changed_scene = view.locator("[data-view='changed']")
            expect(changed_scene).to_be_visible()
            desktop = view.locator("button[data-format='desktop']")
            if desktop.is_visible():
                desktop.press("Enter")
                expect(changed_scene.locator(".desktop img")).to_be_visible()
                view.locator("button[data-format='phone']").press("Enter")
                expect(changed_scene.locator(".phone img")).to_be_visible()
            for image in changed_scene.locator("img").all():
                if image.is_visible():
                    image.scroll_into_view_if_needed()
                    expect(image).to_have_js_property("complete", True)
                    if not image.evaluate("img => img.naturalWidth > 0"):
                        raise AssertionError(f"{slug}: changed preview did not decode")
            opening.press("Enter")
            expect(opening).to_have_attribute("aria-pressed", "true")


def viewport_check(page, url):
    page.goto(url)
    expect(page.get_by_role("heading", level=1).first).to_be_visible()
    geometry = page.evaluate("""() => ({
      viewport: document.documentElement.clientWidth,
      actual: Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)
    })""")
    if geometry["actual"] > geometry["viewport"] + 1:
        raise AssertionError(f"{url}: horizontal overflow {geometry}")
    page.keyboard.press("Tab")
    reachable = page.evaluate("""() => {
      const control = document.activeElement;
      return control && control !== document.body && control.getClientRects().length > 0
        && getComputedStyle(control).visibility !== 'hidden';
    }""")
    if not reachable:
        raise AssertionError(f"{url}: first keyboard stop is absent or hidden")
    for image in page.locator("img:not([loading=lazy])").all():
        if image.is_visible():
            expect(image).to_have_js_property("complete", True)
            if not image.evaluate("img => img.naturalWidth > 0"):
                raise AssertionError(f"{url}: image did not decode")


def arg_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="directory of the extracted project")
    parser.add_argument("--executable", default=os.environ.get("DWC_CHROMIUM"), help="optional local Chromium binary (default: matching Playwright build)")
    parser.add_argument("--only", choices=["layout", "gallery", "styles", "weather", "community"],
                        help="run one group during development")
    return parser


def main():
    args = arg_parser().parse_args()
    root = args.root.resolve()
    catalog = json.loads((root / "styles/catalog.json").read_text(encoding="utf-8"))
    groups = [args.only] if args.only else ["layout", "gallery", "styles", "weather", "community"]
    problems = []
    with preview(root) as base_url, sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=args.executable)
        try:
            for group in groups:
                print(f"Running {group}…", flush=True)
                offline = group in {"styles", "community"}
                context = browser.new_context(offline=offline, reduced_motion="reduce",
                                              viewport={"width": 390, "height": 844}, accept_downloads=True)
                page = context.new_page()
                page.set_default_timeout(4500)
                page.on("pageerror", lambda error: problems.append(f"page error: {error}"))
                page.on("response", lambda response: problems.append(f"{response.status}: {response.url}")
                        if response.status >= 400 and not (
                            group == "weather" and response.status == 404 and response.request.is_navigation_request()
                            and response.url == base_url + "weather/objects/absent-proof.html"
                        ) else None)
                permitted_host = urlsplit(base_url).netloc
                page.on("request", lambda request: problems.append(f"unexpected external request: {request.url}")
                        if urlsplit(request.url).scheme in {"http", "https"} and urlsplit(request.url).netloc != permitted_host else None)
                page.on("requestfailed", lambda request: problems.append(f"request failed: {request.url}")
                        if request.failure != "net::ERR_ABORTED" else None)
                try:
                    if group == "layout":
                        urls = ["index.html", *(f"{item['slug']}.html" for item in catalog),
                                *(f"weather/{route}" for route in WEATHER_ROUTES)]
                        for width, height in [(320, 500), (390, 844), (768, 1024), (1440, 900)]:
                            page.set_viewport_size({"width": width, "height": height})
                            for route in urls:
                                viewport_check(page, base_url + route)
                    elif group == "gallery":
                        page.goto((root / "index.html").as_uri())
                        for width in (390, 1440):
                            page.set_viewport_size({"width": width, "height": 840})
                            gallery(page, catalog)
                    elif group == "styles":
                        browser_prototypes.run(page, lambda slug: page.goto((root / f"{slug}.html").as_uri()))
                    elif group == "weather":
                        browser_weather.run(page, base_url + "weather/")
                        browser_weather.file_visit(page, root)
                        browser_weather.unavailable_storage(page, base_url + "weather/")
                    elif group == "community":
                        contributions = 0
                        for row in catalog:
                            metadata = root / "styles" / row["slug"] / "style.json"
                            if metadata.exists():
                                from style_journeys import run_style_journey
                                steps = json.loads(metadata.read_text(encoding="utf-8"))["journey"]
                                page.goto((root / f"{row['slug']}.html").as_uri())
                                run_style_journey(page, steps)
                                contributions += 1
                        print(f"Replayed {contributions} registered contributor journeys.")
                finally:
                    context.close()
        finally:
            browser.close()
    if problems:
        raise SystemExit("\n".join(sorted(set(problems))))
    print("Passed: " + ", ".join(groups))


if __name__ == "__main__":
    main()
