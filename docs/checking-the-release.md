# Checking a release

Run the commands from the repository root. Python 3.12 is the version exercised by the GitHub Actions workflow. Opening the gallery, flagship and five HTML studies requires only a browser.

```sh
python scripts/check.py
python scripts/test_checks.py
python -m pip install -r scripts/browser-requirements.txt
python -m playwright install chromium
python scripts/check_browser.py
```

On a Linux runner missing Chromium system libraries, use `python -m playwright install --with-deps chromium`. An existing Chromium executable can be selected with `--executable PATH` or the `DWC_CHROMIUM` environment variable. The release workflow leaves that override unset so Playwright uses its matching browser.

| Check | What fails a release |
| --- | --- |
| Source and exports | A checked-in study, gallery or generated Weather Cabinet page differs from its source. A published contribution lacks required evidence or its metadata disagrees with the catalog. |
| Site structure | A required route or file is absent. A shipped page points to a broken local path, fragment or ARIA ID. A standalone study depends on an adjacent file. An embedded resource needs the network. |
| Asset credits | A released media file lacks an exact path, origin, credit or terms in the manifest. A credit names a missing file. |
| Fault tests | Deliberately damaged copies pass the checker, or a changed diagnostic obscures the failure. The fixtures run in a temporary directory. |
| Browser layout | A public page has horizontal overflow at 320, 390, 768 or 1440 CSS pixels. A visible primary image fails to decode. Pages load under a project subdirectory. |
| Browser journeys | A control loses its declared state, a gallery preview fails, a saved note or timer loses tested data, a new style fails its registered journey, or a page reports a script error or unexpected network request. |

Use `python scripts/check_browser.py --only weather` while editing the flagship. Other groups are `gallery`, `styles`, `layout` and `community`. Run the full suite after the change. To verify an extracted ZIP, run these commands from the extracted root. Both main checkers also accept `--root PATH`.

## What a reviewer still needs to see

Open the real work on a phone-sized viewport and a wide one. Start on a deep link as well as the entrance. Read the longest entry, reach a dead end, recover, and revisit a saved state. Trigger the signature action twice. Record whether the first use explains the object and whether repeated use delays the task. Open the collection and detail beside one another and identify what the shared controls teach, where reading rhythm changes, and whether a surprising visual choice helps someone make a decision.

A passing script cannot establish that the imagery is original, the colors suit the content, the accent is well placed or the user can hear an audio cue. Record the actual files viewed, inputs used and platforms tried. A Chromium keyboard run covers only that browser and input method. Other engines, physical devices, assistive-technology speech and subjective listening need their own checks when relevant to the commission.

## Apply the browser checks to your own site

Install the browser dependencies above, start your site's development server, and point this runner at the project's planning directory and local URL. It reads the representative URLs from each family in `site-plan.json`. A built site may have hundreds of pages; put a normal item and the hardest meaningful cases in each family's examples.

```sh
python scripts/visit_project.py --project my-project --base-url http://localhost:3000/
python scripts/visit_project.py --project my-project --base-url http://localhost:3000/season/ --only-family collection
```

The runner validates the plan, opens each selected example in a clean Chromium context at 320 and 1440 pixels, and checks the resulting HTTP responses, uncaught script errors and document width. The narrow run uses reduced motion. Each optional journey runs in its own fresh context and the width check runs again after its last asserted state. The output lists the number of sampled URLs and journeys. A passing run says nothing about routes, states or assistive technologies outside that sample.

To add interactions, place `browser-journeys.json` beside `site-plan.json`. Its `start` must match a declared example, including its query string. `--only-family` picks journeys that start at one of that family's examples. Use the actual controls and an observable result. The Weather Cabinet sample includes [two complete journeys](../examples/weather-project/browser-journeys.json).

```json
{
  "version": 1,
  "journeys": [
    {
      "name": "Open the reverse-side track list",
      "start": "index.html",
      "steps": [
        {"press": ["a[href='set.html']", "Enter"]},
        {"text": ["h1", "Side B"]}
      ]
    }
  ]
}
```

| Action | Step syntax |
| --- | --- |
| Click or check visibility | `{"click":"#open"}`, `{"visible":"#record"}`, `{"hidden":"#empty"}` |
| Type, select or press a key | `{"fill":["#query","rain"]}`, `{"select":["#family","Water"]}`, `{"press":["#reset","Enter"]}` |
| Check resulting content or state | `{"text":["#count","1 instrument"]}`, `{"attribute":["#open","aria-expanded","true"]}` |

A purposeful missing-page example can set `"expected_status":{"gone.html":404}` at the top of this file. Its URL must be in the plan. A missing stylesheet on that page still fails. Scripts can change browser-local state during a journey. The runner limits navigation to the supplied loopback origin, starts without a saved browser session, and blocks HTTP writes and WebSockets by default. Use `--allow-local-writes` only when testing an isolated local backend with disposable data. The runner still blocks off-origin writes. The option `--executable PATH` and `DWC_CHROMIUM` select a local Chromium binary.

To try the shipped project, run `python scripts/serve.py --port 8000` and then use `python scripts/visit_project.py --project examples/weather-project --base-url http://127.0.0.1:8000/weather/` in a second terminal.
