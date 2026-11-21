"""Capture the five Weather Cabinet routes used by the portable lookbook."""
import argparse
from io import BytesIO
from pathlib import Path

from PIL import Image
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
WEATHER = ROOT / "weather"
OBSERVATIONS = {
    "frost-comb": "The two deepest notches kept their white tips after the others had cleared.",
    "dew-mirror": "Six beads along the top edge. The walnut foot was still dry.",
}


def capture(page, output, key, device):
    page.evaluate("document.fonts.ready")
    page.evaluate("Promise.all(Array.from(document.images, image => image.decode()))")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    with Image.open(BytesIO(page.screenshot(animations="disabled"))) as frame:
        frame.convert("RGB").save(output / f"{key}-{device}.webp", quality=89, method=6)


def record(browser, output, device, width, height):
    context = browser.new_context(viewport={"width": width, "height": height}, offline=True,
                                  reduced_motion="reduce", device_scale_factor=1)
    page = context.new_page()
    page.set_default_timeout(5000)
    page.goto((WEATHER / "index.html").as_uri())
    capture(page, output, "entrance", device)

    page.locator("a.drawer").click()
    page.locator("#family").select_option("Water")
    expect(page.locator("#result-count")).to_have_text("3 instruments")
    capture(page, output, "catalogue", device)

    page.get_by_role("link", name="Frost comb", exact=True).click()
    expect(page.get_by_role("heading", name="Frost comb", exact=True)).to_be_visible()
    capture(page, output, "object", device)
    page.locator("#observation").fill(OBSERVATIONS["frost-comb"])
    page.locator("#note-form button").click()
    expect(page.locator("#note-status")).to_contain_text("saved")

    page.locator(".mast nav").get_by_role("link", name="Compare").click()
    page.locator("#left").select_option("frost-comb")
    page.locator("#right").select_option("dew-mirror")
    expect(page.locator('[data-heading="left"]')).to_have_text("Frost comb")
    expect(page.locator('[data-heading="right"]')).to_have_text("Dew mirror")
    capture(page, output, "compare", device)
    page.locator("#right-link").click()
    page.locator("#observation").fill(OBSERVATIONS["dew-mirror"])
    page.locator("#note-form button").click()
    expect(page.locator("#note-status")).to_contain_text("saved")
    page.locator(".form-actions a").click()
    expect(page.locator("#notes-count")).to_have_text("2 observations")
    capture(page, output, "notebook", device)
    context.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chromium", type=Path, help="Use an existing Chromium executable.")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "weather")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as driver:
        options = {"executable_path": str(args.chromium)} if args.chromium else {}
        browser = driver.chromium.launch(**options)
        for device, width, height in (("desktop",1200,800),("phone",390,780)):
            record(browser, args.output, device, width, height)
        browser.close()
    print(f"Recorded ten frames in {args.output}.")


if __name__ == "__main__":
    main()
