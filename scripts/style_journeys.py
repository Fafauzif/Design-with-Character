"""Execute a contributed style's declared walk-through in Playwright."""

import os
from pathlib import Path
import re
import tempfile


PROMPT = re.compile(r"\[\[.*?\]\]", re.DOTALL)


def validate_journey(steps):
    """Validate a contributor's replayable path before CI exercises it in a browser."""
    arity = {"click": 1, "visible": 1, "hidden": 1, "press": 2, "fill": 2,
             "select": 2, "text": 2, "attribute": 3}
    assertion = {"visible", "hidden", "text", "attribute"}
    if not isinstance(steps, list) or not steps:
        raise ValueError("style.json needs a journey array containing an action and an assertion.")
    touched = verified = has_positive_result = False
    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict) or len(step) != 1:
            raise ValueError(f"Journey step {index} needs one operation.")
        op, value = next(iter(step.items()))
        size = arity.get(op)
        parts = [value] if size == 1 else value
        if not size or not isinstance(parts, list) or len(parts) != size or not all(isinstance(v, str) for v in parts):
            raise ValueError(f"Invalid journey operation or arguments at step {index}.")
        if not parts[0].strip() or any(PROMPT.search(v) for v in parts):
            raise ValueError(f"Replace the example selector or value at journey step {index}.")
        if op in assertion:
            verified |= touched
            has_positive_result |= touched and op != "hidden"
        else:
            touched, verified = True, False
    if not has_positive_result:
        raise ValueError("The journey needs a visible result, expected text or changed attribute after an action.")
    if not verified:
        raise ValueError("The last interaction in journey needs a following observable assertion.")


def run_style_journey(page, steps):
    """Execute against a fresh page. String assertions use Playwright's whitespace normalization."""
    from playwright.sync_api import expect

    validate_journey(steps)
    for index, step in enumerate(steps, start=1):
        op, args = next(iter(step.items()))
        selector, *values = [args] if isinstance(args, str) else args
        element = page.locator(selector)
        try:
            if op == "click":
                element.click()
            elif op == "press":
                element.press(values[0])
            elif op == "fill":
                element.fill(values[0])
            elif op == "select":
                element.select_option(values[0])
            elif op == "visible":
                expect(element).to_be_visible()
            elif op == "hidden":
                expect(element).to_be_hidden()
            elif op == "text":
                expect(element).to_have_text(values[0])
            elif op == "attribute":
                expect(element).to_have_attribute(*values)
        except Exception as exc:
            raise ValueError(f"Journey step {index} ({op} on {selector}) failed: {exc}") from exc


def verify_draft_in_browser(html, steps):
    """Check exactly the standalone bytes about to be registered on two fresh viewports."""
    try:
        from playwright.sync_api import Error, sync_playwright
    except ImportError:
        raise ValueError("Publishing needs Python Playwright. Install the browser-test dependencies "
                         "from CONTRIBUTING.md, then retry.") from None
    executable = os.environ.get("DWC_CHROMIUM")
    try:
        with tempfile.TemporaryDirectory() as temporary, sync_playwright() as api:
            source = Path(temporary) / "preview.html"
            source.write_text(html, encoding="utf-8")
            browser = api.chromium.launch(executable_path=executable)
            try:
                for width, height in ((1280, 800), (390, 844)):
                    page = browser.new_page(viewport={"width": width, "height": height},
                                            reduced_motion="reduce" if width < 400 else "no-preference",
                                            offline=True)
                    page.set_default_timeout(5000)
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.on("requestfailed", lambda req: errors.append(f"{req.failure}: {req.url}")
                            if req.failure != "net::ERR_ABORTED" else None)
                    try:
                        page.goto(source.as_uri())
                        run_style_journey(page, steps)
                        if errors:
                            raise ValueError(f"Offline draft failed at {width}×{height}: " + "; ".join(errors))
                    finally:
                        page.close()
            finally:
                browser.close()
    except Error as exc:
        raise ValueError(f"Cannot run the draft browser check. {exc}") from exc
