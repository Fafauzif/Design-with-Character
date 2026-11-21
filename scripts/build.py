"""Compile the single-file style demos and their offline gallery."""
from argparse import ArgumentParser
from base64 import b64encode
from html import escape
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
STYLES = ROOT / "styles"
GALLERY = ROOT / "gallery-assets"
SLUG = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")
SWATCH = re.compile(r"#[\da-fA-F]{6}")
ASSET = re.compile(r"%%ASSET:([A-Za-z0-9._-]+)%%")
MEDIA = {".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg",
         ".avif": "image/avif", ".woff2": "font/woff2"}


def data_uri(folder, name):
    path = folder / name
    media = MEDIA.get(path.suffix.lower())
    if not re.fullmatch(r"[A-Za-z0-9._-]+", name) or media is None or not path.is_file() or path.resolve().parent != folder.resolve():
        raise ValueError(f"{folder.name}: invalid asset {name}")
    payload = b64encode(path.read_bytes()).decode("ascii")
    return f"data:{media};base64,{payload}"


def compile_demo(folder, template):
    html = ASSET.sub(lambda match: data_uri(folder, match[1]), template)
    if "%%ASSET:" in html:
        raise ValueError(f"{folder.name}: unresolved asset marker")
    return html


def preview_markup(slug, title, captions):
    """Keep working file links in the HTML even when scripting is disabled."""
    if not all(isinstance(captions.get(state), str) and captions[state].strip()
               for state in ("opening", "changed")):
        raise ValueError(f"{slug}: supply opening and changed preview captions")
    states = []
    for state, suffix in (("opening", ""), ("changed", "-action")):
        figures = []
        for device in ("desktop", "phone"):
            path = GALLERY / slug / f"{device}{suffix}.webp"
            if not path.is_file() or path.resolve().parents[1] != GALLERY.resolve():
                raise ValueError(f"{slug}: missing or invalid preview {path.name}")
            url = path.relative_to(ROOT).as_posix()
            label = device.capitalize()
            dimensions = 'width="1200" height="800"' if device == "desktop" else 'width="390" height="780"'
            figures.append(
                f'<figure class="frame {device}"><a href="{url}" '
                f'aria-label="Full-size {device} view of {title}, {state} state">'
                f'<img {dimensions} src="{url}" loading="lazy" alt="{title} on {device} in its {state} state">'
                f'<span class="format">{label} <span aria-hidden="true">→</span></span></a></figure>'
            )
        states.append(f'<div class="scene" data-view="{state}"><div class="frames">{"".join(figures)}</div>'
                      f'<p class="caption">{escape(captions[state])}</p></div>')
    return (
        '<div class="switches"><div class="scene-switch" role="group" aria-label="Preview state">'
        '<button type="button" data-scene="opening" aria-pressed="true">Opening</button>'
        '<button type="button" data-scene="changed" aria-pressed="false">After use</button></div>'
        '<div class="format-switch" role="group" aria-label="Preview format">'
        '<button type="button" data-format="phone" aria-pressed="true">Phone</button>'
        '<button type="button" data-format="desktop" aria-pressed="false">Desktop</button></div></div>'
        + "".join(states)
    )


def fallback_markup(folder, colors, entry):
    if "thumbnail" in entry:
        return f'<div class="fallback"><img src="{data_uri(folder, entry["thumbnail"])}" alt=""></div>'
    swatches = "".join(f'<span style="background:{color}"></span>' for color in colors)
    return f'<div class="fallback palette" role="img" aria-label="Style palette">{swatches}</div>'


def compile_catalog():
    selectors = []
    sections = []
    results = {}
    previews = json.loads((GALLERY / "previews.json").read_text(encoding="utf-8"))
    for entry in json.loads((STYLES / "catalog.json").read_text(encoding="utf-8")):
        slug, title, description, action, medium = (entry[key] for key in ("slug", "title", "description", "action", "medium"))
        name = f"{slug}.html"
        colors = entry["palette"]
        if not SLUG.fullmatch(slug) or slug in {"index", "gallery"} or name in results or not all(v.strip() for v in (title, description, action, medium)):
            raise ValueError(f"Invalid or duplicate catalog entry: {slug}")
        if not 1 <= len(colors) <= 5 or any(not SWATCH.fullmatch(color) for color in colors):
            raise ValueError(f"{slug}: invalid palette")
        folder = STYLES / slug
        (folder / "STYLE.md").read_text(encoding="utf-8")
        results[name] = compile_demo(folder, (folder / "demo.html").read_text(encoding="utf-8"))
        title = escape(title)
        preview = preview_markup(slug, title, previews[slug]) if slug in previews else fallback_markup(folder, colors, entry)
        selectors.append(f'<li><a data-select="{slug}" href="#{slug}">{title}</a></li>')
        sections.append(
            f'<section class="work" id="{slug}" aria-labelledby="{slug}-title" data-device="phone">'
            f'<div class="work-intro"><h2 id="{slug}-title" tabindex="-1">{title}</h2>'
            f'<a class="live-link" href="{name}">{escape(action)} <span aria-hidden="true">→</span></a></div>'
            f'<p class="description">{escape(description)}</p>{preview}</section>'
        )
    if not sections:
        raise ValueError("Publish at least one style to build the gallery.")
    template = (ROOT / "gallery.html").read_text(encoding="utf-8")
    entries = {"%%SELECTORS%%": "\n".join(selectors), "%%WORKS%%": "\n".join(sections)}
    for marker, content in entries.items():
        if template.count(marker) != 1:
            raise ValueError(f"gallery.html must contain one {marker}")
        template = template.replace(marker, content)
    results["index.html"] = template
    return results


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Report exports that differ from their source.")
    args = parser.parse_args()
    results = compile_catalog()
    stale = []
    for name, html in results.items():
        output = ROOT / name
        if args.check:
            if not output.is_file() or output.read_text(encoding="utf-8") != html:
                stale.append(name)
        else:
            output.write_text(html, encoding="utf-8", newline="\n")
    if stale:
        raise SystemExit(f"Rebuild with python scripts/build.py. Stale exports: {', '.join(stale)}")
    print(f"{'Verified' if args.check else 'Built'} {len(results) - 1} styles and the gallery.")


if __name__ == "__main__":
    main()
