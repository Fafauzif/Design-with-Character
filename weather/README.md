# Weather Cabinet

Open `index.html` here, or follow **Weather Cabinet** from the main gallery. All six instruments and their keeper’s accounts are fictional. The art, writing and controls are local to the release.

| Stop | What the visitor can do |
| --- | --- |
| Entrance | Pick a named object on the shelf or pull the drawer to open the collection. Frequent visitors can go straight to Compare or Field notes. |
| Collection | Search names, materials or observations. Combine words with a weather family. A URL keeps a search such as `collection.html?q=brass&family=Air`. Clear an empty search in place. |
| Object plates | Open any of six individual HTML pages directly. Read the keeper’s account, compare a related instrument or record a personal observation. |
| Comparison bench | Choose two instruments and read the same four observations side by side. The address carries both selections, for example `compare.html?a=frost-comb&b=dew-mirror`. Choosing the instrument already on the other tray swaps their places. |
| Field notes | Revise one observation per instrument, remove it, undo the last removal or transfer a JSON backup. Import fills missing entries and preserves notes already present. Notes stay out of shareable URLs. |
| Missing drawer | Recover through the collection from a missing address. The visible view also opens directly as `404.html`. |

## Preview at a local address

From the repository root run `python scripts/serve.py --port 8000` and open `http://127.0.0.1:8000/weather/`. To try project hosting under a subpath, run `python scripts/serve.py --port 8000 --mount /garden` and open `http://127.0.0.1:8000/garden/weather/`. Visiting `/garden/weather/objects/missing.html` then returns HTTP 404. Its recovery link opens the real catalog. Use Ctrl+C to stop the preview.

On a standard GitHub Pages branch build, the repository-root 404 template includes the same recovery view and inserts the current project base path. Other static hosts need their own missing-page mapping and the correct asset base. Existing pages also open from the extracted folder without a server. Errors for nonexistent files opened directly are handled by the browser.

## Keeping notes

Notes use browser storage associated with this copy of the cabinet. They do not leave the device. Private browsing, a different browser or opening another copy can give you a separate notebook. With direct-file browsing, use ordinary in-page links within one tab. When storage is unavailable the page identifies a temporary notebook. Use **Field notes → Back up or restore notes → Export notes** before closing the tab or moving to another device. An invalid backup leaves the current notebook intact.

## Edit the collection

Edit `instruments.json` for the object names, descriptive text, materials, color tints, art paths and related pairs. The original three plates come from the companion Specimen Cabinet style. The dew mirror, cloud window and frost comb in `assets/` were made for this collection. The names, artwork and accounts represent imagined garden instruments.

Run `python weather/build.py` from the repository root after changing the records or page templates. Use `python weather/build.py --check` to check the committed HTML and JavaScript data against their source. The visual rules and interactions are maintained in `assets/cabinet.css` and `assets/cabinet.js`.

### Art direction for an additional plate

The inspection page, index and comparison bench use the very same transparent cutout at three sizes. Test a new object as an 80 px catalog thumbnail first. An outline that merges into its mounting or gets lost on the plate tint will also be hard to compare on a phone.

For the three new assets, GPT Image received a common brief followed by an individual object description. The shared brief was:

> An isolated photographic museum accession cutout of a single small, fictional 1930s amateur meteorologist's instrument. Square image, true transparent background, no ground/table or background, no visible text, no hands, no lettering. Soft frontal overcast light, straight museum macro documentation, worn brass, oiled walnut, understated honest patina, natural detail and imperfections. Frame the entire device with a margin on every side, centered and large.

- **Dew mirror.** A round slightly tarnished smooth silver mirror disk, held face upward in a tilted low brass cradle on one little dark walnut plinth. Small beads of dew near the upper rim, three-quarter view.
- **Cloud window.** A flat pocket sighting frame, square empty opening with a blue-grey enamel rim and brass corners, two thin black crosshairs and a small folding wooden handle. Transparency must continue through the opening.
- **Frost comb.** Seven flat dull metal tines, each with different notches near the tip, mounted in a short dark walnut bar with brass screws. A little frost along some teeth. A slightly diagonal upright view makes the gaps between the tines visible.

The selected cutouts were trimmed to their alpha bounds and resized to fit within 660 × 660 px for the WebP files. Shadows on the entrance are CSS. Put future labels and descriptions in the records so visitors can select, magnify and read them independently of the art.
