"""Export the captured website screens as a portable, single-file lookbook."""
import argparse
import base64
from html import escape
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
WEATHER = (
    ("entrance", "Entrance", "The cabinet window holds three instruments. The brass drawer pull opens the collection."),
    ("catalogue", "Filtered collection", "The collection has been filtered to the instruments used to observe water."),
    ("object", "Instrument plate", "The frost comb has seven different notches where crystals can gather."),
    ("compare", "Comparison bench", "The frost comb and the dew mirror are on the bench together."),
    ("notebook", "Saved field notes", "Two sample observations have been saved in the field notebook."),
)
SIZES = {"desktop": (1200, 800), "phone": (390, 780)}


def image(path, device, context):
    if not path.is_file():
        raise ValueError(f"Missing capture {path.relative_to(ROOT)}")
    uri = base64.b64encode(path.read_bytes()).decode("ascii")
    w, h = SIZES[device]
    return (f'<img class="capture" data-device="{device}" width="{w}" height="{h}" '
            f'alt="{escape(context)} — {device} browser capture" loading="lazy" '
            f'src="data:image/webp;base64,{uri}">')


def section(slug, name, scenes):
    articles = []
    for key, title, caption, paths in scenes:
        context = f"{name}, {title}"
        frames = "".join(image(paths[device], device, context) for device in SIZES)
        articles.append(
            f'<section class="scene" id="{slug}-{key}" data-key="{key}" data-name="{escape(title)}">'
            f'<h3>{escape(title)}</h3><figure><div class="surface">{frames}</div>'
            f'<figcaption>{escape(caption)}</figcaption></figure></section>'
        )
    return (f'<article id="{slug}" class="experience" data-name="{escape(name)}">'
            f'<h2>{escape(name)}</h2>{"".join(articles)}</article>')


def compile_book():
    catalog = json.loads((ROOT / "styles/catalog.json").read_text(encoding="utf-8"))
    caption_by_style = json.loads((BASE / "previews.json").read_text(encoding="utf-8"))
    book = [section("weather", "The Weather Cabinet", [
        (key, title, caption, {device: BASE / "weather" / f"{key}-{device}.webp" for device in SIZES})
        for key, title, caption in WEATHER
    ])]
    for style in catalog:
        slug = style["slug"]
        if slug not in caption_by_style:
            continue
        captions = caption_by_style[slug]
        book.append(section(slug, style["title"], [
            (key, title, captions[key], {device: BASE / slug / f"{device}{suffix}.webp" for device in SIZES})
            for key, title, suffix in (("opening", "Opening", ""), ("changed", "After use", "-action"))
        ]))
    source = (BASE / "lookbook.html").read_text(encoding="utf-8")
    return source.replace("%%EXPERIENCES%%", "\n".join(book))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Destination .html file")
    args = parser.parse_args()
    html = compile_book()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8", newline="\n")
    print(f"Exported {args.output.name} ({args.output.stat().st_size:,} bytes).")


if __name__ == "__main__":
    main()
