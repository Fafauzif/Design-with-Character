"""Check collection, comparison, observation and recovery flows through their public controls."""
import json
from pathlib import Path

from playwright.sync_api import expect


def narrow(page):
    overflow = page.evaluate("Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - document.documentElement.clientWidth")
    if overflow > 1:
        raise AssertionError(f"{page.url}: overflow after interaction ({overflow}px)")


def enter_note(page, content):
    page.locator("#observation").fill(content)
    page.get_by_role("button", name="Save field note", exact=True).press("Enter")


def open_book(page):
    page.get_by_role("link", name="Open field notes", exact=True).press("Enter")


def run(page, base_url):
    page.goto(base_url + "index.html")
    shelf = page.locator(".window-piece").first
    plate = shelf.locator("img")
    shelf.hover()
    expect(plate).to_have_css("transform", "none")
    page.emulate_media(reduced_motion="no-preference")
    expect(plate).not_to_have_css("transform", "none")
    page.emulate_media(reduced_motion="reduce")
    expect(plate).to_have_css("transform", "none")
    page.keyboard.press("Tab")
    expect(page.get_by_role("link", name="Skip to content")).to_be_focused()
    page.keyboard.press("Enter")
    page.get_by_role("link", name="Open the collection").press("Enter")
    rain = page.locator(".index-entry[href='objects/rain-catcher.html']")
    entries = page.locator(".index-entry:visible")
    expect(entries).to_have_count(6)
    page.locator("#family").select_option("Air")
    expect(entries).to_have_count(2)
    page.locator("#search").fill("impossiblezz")
    expect(rain).not_to_be_visible()
    expect(page.get_by_role("heading", name="No instruments found")).to_be_visible()
    page.get_by_role("button", name="Clear search").press("Enter")
    expect(entries).to_have_count(6)
    page.locator("#search").fill("rain catcher")
    expect(entries).to_have_count(1)
    rain.press("Enter")
    expect(page.get_by_role("heading", name="Rain catcher", exact=True)).to_be_visible()
    page.go_back()
    expect(page.locator("#search")).to_have_value("rain catcher")
    rain.press("Enter")
    rough, amended = "Drops gathered on one edge.", "At dusk only the rim was wet."
    enter_note(page, rough)
    open_book(page)
    expect(page.locator("#entries")).to_contain_text(rough)
    page.reload()
    expect(page.locator("#entries")).to_contain_text(rough)
    edit = page.get_by_role("button", name="Edit Rain catcher note")
    edit.press("Enter")
    field = page.get_by_role("textbox", name="Observation for Rain catcher")
    expect(field).to_have_value(rough)
    expect(field).to_be_focused()
    field.fill(amended)
    page.get_by_role("button", name="Save changes").press("Enter")
    expect(edit).to_be_focused()
    expect(page.locator("#entries")).to_contain_text(amended)
    expect(page.locator("#entries")).not_to_contain_text(rough)
    page.locator("details.backup summary").press("Enter")
    with page.expect_download() as event:
        page.get_by_role("button", name="Export notes").press("Enter")
    payload = Path(event.value.path()).read_bytes()
    if amended not in json.dumps(json.loads(payload)):
        raise AssertionError("note backup lost amended text")
    page.locator("#import-file").set_input_files({"name": "broken.json", "mimeType": "application/json", "buffer": b"{"})
    expect(page.locator("#notes-status")).to_contain_text("not a valid Weather Cabinet backup")
    expect(page.locator("#entries")).to_contain_text(amended)
    page.get_by_role("button", name="Remove Rain catcher note").press("Enter")
    expect(page.locator("#blank")).to_be_visible()
    page.locator("#undo").press("Enter")
    expect(page.locator("#entries")).to_contain_text(amended)
    page.get_by_role("button", name="Remove Rain catcher note").press("Enter")
    page.locator("#import-file").set_input_files({"name": "notes.json", "mimeType": "application/json", "buffer": payload})
    expect(page.locator("#entries")).to_contain_text(amended)
    expect(page.locator("#notes-status")).to_contain_text("Imported 1 note")
    duplicate = json.loads(payload)
    duplicate["entries"]["rain-catcher"] = "Low-priority duplicate"
    page.locator("#import-file").set_input_files({"name":"duplicate.json", "mimeType":"application/json",
                                                "buffer":json.dumps(duplicate).encode("utf-8")})
    expect(page.locator("#notes-status")).to_contain_text("Imported 0 notes")
    page.reload()
    expect(page.locator("#entries")).to_contain_text(amended)
    narrow(page)

    page.goto(base_url + "objects/dew-mirror.html")
    enter_note(page, "Dew gathered along the edge.")
    open_book(page)
    edit.press("Enter")
    draft = "At midnight the glass was dry."
    field.fill(draft)
    page.get_by_role("button", name="Edit Dew mirror note").press("Enter")
    dew = page.get_by_role("textbox", name="Observation for Dew mirror")
    dew.fill("Morning dew covered the silver.")
    dew.locator("..").get_by_role("button", name="Save changes").press("Enter")
    expect(field).to_have_value(draft)
    field.locator("..").get_by_role("button", name="Save changes").press("Enter")
    expect(page.locator("#entries")).to_contain_text(draft)
    expect(page.locator("#entries")).to_contain_text("Morning dew covered the silver.")

    page.goto(base_url + "compare.html?a=rain-catcher&b=folding-sundial")
    expect(page.locator("#left")).to_have_value("rain-catcher")
    expect(page.locator("#right")).to_have_value("folding-sundial")
    expect(page.get_by_role("columnheader", name="Folding sundial")).to_be_visible()
    page.locator("#left").select_option("frost-comb")
    expect(page.get_by_role("columnheader", name="Frost comb")).to_be_visible()
    page.reload()
    expect(page.locator("#left")).to_have_value("frost-comb")
    expect(page.locator("#right")).to_have_value("folding-sundial")
    page.locator("#left-link").press("Enter")
    expect(page.get_by_role("heading", name="Frost comb", exact=True)).to_be_visible()
    page.goto(base_url + "compare.html?a=invented&b=not-found")
    expect(page.locator("#left")).not_to_have_value("")
    expect(page.locator("#right")).not_to_have_value("")
    if page.locator("#left").input_value() == page.locator("#right").input_value():
        raise AssertionError("invalid comparison URL recovered to two identical specimens")
    narrow(page)
    missing = page.goto(base_url + "objects/absent-proof.html")
    if missing is None or missing.status != 404:
        raise AssertionError("A missing nested instrument must return HTTP 404")
    expect(page.get_by_role("heading", name="This drawer is empty.")).to_be_visible()
    page.get_by_role("link", name="Search the collection").press("Enter")
    expect(page.get_by_role("heading", name="The collection")).to_be_visible()


def file_visit(page, root):
    # File storage scoping differs across browsers. Emulate a separate store for each file,
    # even in Chromium configurations that share these stores for all local HTML files.
    page.add_init_script("""if (location.protocol === "file:") {
      for (const name of ["getItem", "setItem", "removeItem"]) {
        const original = Storage.prototype[name];
        Storage.prototype[name] = function(key, ...rest) {
          return original.call(this, location.pathname + "|" + key, ...rest);
        };
      }
    }""")
    page.goto((root / "weather/objects/dew-mirror.html").as_uri())
    observation = "The silver caught a ring of morning dew."
    enter_note(page, observation)
    open_book(page)
    expect(page.locator("#entries")).to_contain_text(observation)
    page.reload()
    expect(page.locator("#entries")).to_contain_text(observation)


def unavailable_storage(page, base_url):
    # Simulate browsers which reject both Web Storage backends. The tab handoff remains usable.
    page.add_init_script("""for (const key of ['localStorage', 'sessionStorage']) {
      Object.defineProperty(window, key, {get() {throw new DOMException('Disabled for test', 'SecurityError')}});
    }""")
    page.goto(base_url + "objects/cloud-window.html")
    text = "One narrow cloud stayed in the frame."
    enter_note(page, text)
    expect(page.locator("#note-status")).to_contain_text("this tab")
    open_book(page)
    expect(page.locator("#entries")).to_contain_text(text)
    expect(page.locator("#storage-info")).to_be_visible()
    page.locator("details.backup summary").press("Enter")
    with page.expect_download() as event:
        page.get_by_role("button", name="Export notes").press("Enter")
    if json.loads(Path(event.value.path()).read_bytes())["entries"].get("cloud-window") != text:
        raise AssertionError("temporary notebook backup lost its observation")
