# Bring a sixth style

A new style earns its place when it gives a visitor a different way to do something. Describe that moment first. In Pixel Study Room, starting the timer lights the desk. A listening project might instead let you drop a needle on a recorded place. If a proposed second style has the same task, framing and response as an existing one, try developing it as a variation in that style guide.

## Open a working draft

Use Python 3.10 or newer. Run these commands from the repository root. On Windows, `py` can replace `python`.

```sh
python scripts/add_style.py radio-desk "Radio Desk" --description "Tune a small receiver to a recording from the harbor." --action "Tune the receiver" --medium "Local radio" --palette "#1e3731" "#f7eacc" "#c75537"
python scripts/add_style.py --preview radio-desk
```

Open `.style-work/radio-desk.html` directly in a browser. The starter has a native disclosure so you can inspect your chosen wording immediately. The source folder is an ordinary Git path. A commit and push can make its contents public before gallery registration, including source art. Keep restricted material outside a public checkout. Re-run `--preview` after editing the source.

| Where to work | What belongs there |
| --- | --- |
| `styles/radio-desk/demo.html` | The actual working experience. Replace the starter markup and its `data-style-starter` marker. Preserve a meaningful document title and main landmark. |
| `styles/radio-desk/STYLE.md` | Complete each prompt in the guide. Record the design decisions and observations a future author would need. |
| `styles/radio-desk/style.json` | Title, medium, action, description, palette and the browser journey that demonstrates the core task. |
| `styles/radio-desk/` | Original or cleared source media. The build embeds a local `%%ASSET:receiver.webp%%` marker inside the exported HTML. Keep embedded assets beside the demo. See `MEDIA` in [the builder](scripts/build.py) for supported formats. |

Choose one focal point and design its resting and used positions together. On a short phone, the main control needs to remain reachable even if an illustration is cropped. When the design has motion, decide which information must still be visible on a static frame. Identify where the keyboard user lands when a panel closes, an object is collected or its only button disappears. A reference may inform a material, an action or a rhythm. Record its role, source and any reuse terms.

## Describe a journey Codex can run

Edit `journey` in `style.json`. The example below assumes the project is implemented with a native station selector, a separate control operating the receiver and an output with the chosen call sign. Choose selectors that describe **your** working interface. A native button accepts `Enter` or `Space`; a custom control needs explicit keyboard behavior.

```json
[
  {"select": ["#station", "harbor"]},
  {"press": ["#tune", "Enter"]},
  {"text": ["#call-sign", "Harbor, 91.4"]},
  {"click": "#release"},
  {"visible": "#tune"}
]
```

Each step has one operation. Actions accept `{"click":"selector"}`, `{"press":["selector","key"]}`, `{"fill":["selector","value"]}` or `{"select":["selector","value"]}`. Observations accept `visible` and `hidden` with a selector, `text` with a selector and expected text, or `attribute` with a selector, attribute name and expected value. Use an observable change such as a completed label, revealed content or an updated accessible state. Include the next step, reversal or recovery when the experience supports it. A state that genuinely ends can use the receipt or completion as its last assertion.

## Take four truthful pictures

Install the browser tools once. A Linux CI runner without browser system packages may need `python -m playwright install --with-deps chromium`.

```sh
python -m pip install -r scripts/browser-requirements.txt
python -m playwright install chromium
```

Create a local capture recipe, for example `styles/radio-desk/capture.py`. Keep it if it helps the next contributor reproduce the pictures. The gallery helper opens a fresh page at each size. Use real interactions to reach the two frames and wait for an observable result. If the demo has audio, pause it after capturing the audible state or capture a stable tuned state.

```python
def opening(page):
    page.locator("#tune").wait_for()


def changed(page):
    page.locator("#station").select_option("harbor")
    page.locator("#tune").press("Enter")
    page.get_by_text("Harbor, 91.4", exact=True).wait_for()
```

```sh
python gallery-assets/capture.py radio-desk --recipe styles/radio-desk/capture.py --page .style-work/radio-desk.html
```

The four WebP captures belong in `gallery-assets/radio-desk/` as `desktop.webp`, `desktop-action.webp`, `phone.webp` and `phone-action.webp`. In `gallery-assets/previews.json`, add an entry keyed by the slug. Give sighted and screen-reader visitors a specific description of the visual change.

```json
"radio-desk": {
  "opening": "A wooden receiver rests with its dial at zero.",
  "changed": "The needle rests at Harbor and the tuned station is written beside it."
}
```

Register each capture and each shipped source image, font or audio file as its own row in [the asset ledger](credits/assets.json). Copy the format of an existing entry. Use repository-relative paths with forward slashes. Identify the origin, credit and actual terms for each file. A capture containing third-party art inherits the relevant usage conditions. Include any required notices. When GPT Image supplies an element, record the model/source, its role, the relevant terms and how you integrated the result.

## Register and verify

```sh
python scripts/add_style.py --check-ready radio-desk
python scripts/add_style.py --publish radio-desk
python scripts/build.py
python scripts/check.py
python scripts/check_browser.py
```

The readiness check inspects the demo, guide, journey, captions, four WebP headers, distinct opening and changed frames, and per-file provenance. Publishing also loads the freshly compiled HTML offline and replays the journey on desktop and a 390-pixel phone with reduced motion. The command updates the local catalog only after those checks succeed. Registration never uploads files. CI also checks the saved source contract and replays the journey for every added style. Run `python scripts/test_contribution.py` to exercise this contributor workflow in a disposable copy, including a rejected publication and a successful sixth style. The clickable appearance, image quality and appropriateness of the style still require judgment.

Commit the new source, gallery frames and captions, asset credits, catalog, rebuilt root HTML and rebuilt `index.html` together. Open the standalone demo and gallery from a clean extraction before sending the change. To revise a contributor style, edit its existing sources and `style.json`, recapture frames affected by the change and run `python scripts/add_style.py --refresh radio-desk`. Refresh replays the journey and copies the current fields into the same catalog row. Rebuild and check as above. The five original studies use `styles/catalog.json` directly and have bespoke browser journeys. Preview and lock files under `.style-work/` stay local.

## Decide whether it carries a larger site

Sketch a visitor arriving deep in the site, using a repeated control, and returning to a saved result. For each page job, identify the visitor’s next action, the information they need to compare or read, and the detail that carries the identity. On the radio project, a tuning desk supports exploratory listening. A station directory might use a straight frequency scale and quickly scannable names; a recording transcript needs a quiet reading measure. The type, station marks and player behavior can connect all three. Redrawing the same large receiver on every page would slow down the listener.

Use the [design workflow](skills/design-with-character/SKILL.md) to structure four critique and repair passes. Compare actual desktop, changed, phone and recovery states. Ask a fresh reader to attempt the first action without a tour. Preserve the specific evidence and an honest verification gap in the guide. The [Weather Cabinet](weather/index.html) shows how one creative direction handles a collection, detail pages, comparison, notes and a missing destination.
