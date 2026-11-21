"""Create an unlisted local draft, preview it offline, or register a finished style."""
import argparse
from contextlib import contextmanager
from html import escape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

from build import ROOT, STYLES, SLUG, SWATCH, compile_demo
from style_journeys import validate_journey, verify_draft_in_browser


INITIAL_EXAMPLES = {"halftone-dossier", "botanical-letterpress", "specimen-cabinet",
                    "arcade-workshop", "pixel-study-room"}
CAPTURES = ("desktop", "desktop-action", "phone", "phone-action")
MEDIA = {".png", ".webp", ".jpg", ".jpeg", ".avif", ".svg", ".gif", ".woff2", ".woff",
         ".ttf", ".otf", ".mp3", ".wav", ".ogg", ".webm", ".mp4"}
CATALOG_FIELDS = ("slug", "title", "description", "action", "medium", "palette")
WINDOWS_NAMES = {"con", "prn", "aux", "nul"} | {f"{name}{i}" for name in ("com", "lpt") for i in range(1, 10)}
PROMPT = re.compile(r"\[\[.*?\]\]", re.DOTALL)
WORK = ROOT / ".style-work"


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"Cannot read {path}: {exc}") from exc


def json_text(value):
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def write_atomic(path, value):
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=path.parent, delete=False) as handle:
            temp = Path(handle.name)
            handle.write(value)
        os.replace(temp, path)
    finally:
        if temp:
            temp.unlink(missing_ok=True)


@contextmanager
def catalog_lock():
    WORK.mkdir(exist_ok=True)
    lock = WORK / "registration.lock"
    try:
        lock.mkdir()
    except FileExistsError:
        raise ValueError("Another contribution command holds .style-work/registration.lock. "
                         "If an earlier command was interrupted, close it and remove the empty lock directory.") from None
    try:
        yield
    finally:
        lock.rmdir()


def verify_slug(slug):
    if not SLUG.fullmatch(slug) or len(slug) > 64 or slug in WINDOWS_NAMES | {"index", "gallery"}:
        raise ValueError("Use a unique lowercase hyphenated slug, up to 64 characters, starting with a letter. "
                         "The gallery, index and Windows device names are reserved.")


def single_line(value):
    return isinstance(value, str) and bool(value.strip()) and all(c.isprintable() for c in value)


def check_fields(metadata, slug):
    if not isinstance(metadata, dict) or metadata.get("slug") != slug:
        raise ValueError("style.json must describe its containing style slug.")
    for key in ("title", "description", "action", "medium"):
        if not single_line(metadata.get(key)):
            raise ValueError(f"Provide one nonempty line for {key}.")
    colors = metadata.get("palette")
    if not isinstance(colors, list) or not 1 <= len(colors) <= 5 or any(
        not isinstance(color, str) or not SWATCH.fullmatch(color) for color in colors
    ):
        raise ValueError("Provide one to five six-digit hex colors in palette.")


def check_available(slug, catalog, creating):
    occupied = (ROOT / f"{slug}.html").exists() or any(row["slug"] == slug for row in catalog)
    if occupied or (creating and (STYLES / slug).exists()):
        raise ValueError(f"'{slug}' is already in use.")


def create(args, catalog):
    check_available(args.slug, catalog, creating=True)
    metadata = {key: getattr(args, key) for key in CATALOG_FIELDS}
    check_fields(metadata, args.slug)
    metadata["journey"] = [
        {"click": "[[opening control selector]]"}, {"visible": "[[changed state selector]]"},
        {"click": "[[return or next control selector]]"}, {"visible": "[[destination selector]]"}
    ]
    starter = STYLES / "_template"
    guide = (starter / "STYLE.md").read_text(encoding="utf-8").replace("%%TITLE%%", args.title)
    source = (starter / "demo.html").read_text(encoding="utf-8")
    values = {"TITLE": args.title, "ACTION": args.action, "DESCRIPTION": args.description}
    source = re.sub(r"%%(TITLE|ACTION|DESCRIPTION)%%", lambda token: escape(values[token[1]]), source)
    draft = Path(tempfile.mkdtemp(dir=STYLES, prefix=".draft-"))
    try:
        (draft / "style.json").write_text(json_text(metadata), encoding="utf-8")
        (draft / "STYLE.md").write_text(guide, encoding="utf-8")
        (draft / "demo.html").write_text(source, encoding="utf-8")
        draft.rename(STYLES / args.slug)
    finally:
        if draft.exists():
            shutil.rmtree(draft)
    print(f"Created styles/{args.slug}/. Preview with python scripts/add_style.py --preview {args.slug}")


def draft_files(slug):
    folder = STYLES / slug
    if folder.is_symlink() or not folder.is_dir() or not (folder / "style.json").is_file():
        raise ValueError(f"No contributor draft at styles/{slug}/style.json.")
    metadata = read_json(folder / "style.json")
    check_fields(metadata, slug)
    source = (folder / "demo.html").read_text(encoding="utf-8")
    return folder, metadata, compile_demo(folder, source)


class SourceShape(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = set()
        self.starter = False

    def handle_starttag(self, tag, attrs):
        self.elements.add(tag)
        attributes = dict(attrs)
        self.starter |= "data-style-starter" in attributes


def verify_guide(folder):
    guide = (folder / "STYLE.md").read_text(encoding="utf-8")
    if PROMPT.search(guide):
        raise ValueError("Complete the [[prompts]] in STYLE.md.")
    required = ["Experience", "Composition", "Material and palette", "Interaction", "Transfer",
                "References and provenance", "Review evidence"]
    sections = re.split(r"(?m)^## (.+?)\s*$", guide)
    headings = dict(zip(sections[1::2], sections[2::2]))
    missing = [k for k in required if not headings.get(k, "").strip()]
    if missing:
        raise ValueError("Complete these STYLE.md sections: " + ", ".join(missing))


def verify_gallery(folder):
    slug = folder.name
    project = folder.parent.parent
    assets = project / "gallery-assets"
    captions = read_json(assets / "previews.json")
    pair = captions.get(slug, {}) if isinstance(captions, dict) else {}
    if not isinstance(pair, dict) or not all(single_line(pair.get(key)) for key in ("opening", "changed")):
        raise ValueError(f"Register opening and changed captions for {slug} in gallery-assets/previews.json.")
    captured = [assets / slug / f"{stem}.webp" for stem in CAPTURES]
    for path in captured:
        try:
            with path.open("rb") as stream:
                header = stream.read(12)
        except FileNotFoundError:
            raise ValueError(f"Missing gallery capture {path.relative_to(project)}.") from None
        if header[:4] != b"RIFF" or header[8:] != b"WEBP":
            raise ValueError(f"Save {path.relative_to(project)} as an actual WebP image.")
    for device in ("desktop", "phone"):
        rest = assets / slug / f"{device}.webp"
        used = assets / slug / f"{device}-action.webp"
        if rest.read_bytes() == used.read_bytes():
            raise ValueError(f"{slug}: the two {device} captures are identical. Capture the visible change.")
    media = captured + [p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in MEDIA]
    credits = read_json(project / "credits" / "assets.json")
    if not isinstance(credits, list):
        raise ValueError("credits/assets.json must contain a JSON array.")
    paths = {row.get("path") for row in credits if isinstance(row, dict) and
             all(single_line(row.get(field)) for field in ("origin", "credit", "terms"))}
    missing = [str(p.relative_to(project).as_posix()) for p in media if p.relative_to(project).as_posix() not in paths]
    if missing:
        raise ValueError("Add per-file provenance in credits/assets.json for " + ", ".join(missing))


def verify_ready(folder, metadata, source):
    shape = SourceShape()
    shape.feed(source)
    if shape.starter or not {"main", "title"} <= shape.elements:
        raise ValueError("Author the actual experience in demo.html and remove the data-style-starter marker.")
    verify_guide(folder)
    validate_journey(metadata.get("journey"))
    verify_gallery(folder)


def check_published_contract(root, entry):
    """Keep a registered contributor's sources, public entry and evidence in agreement."""
    slug = entry["slug"]
    verify_slug(slug)
    folder = root / "styles" / slug
    description = folder / "style.json"
    if slug in INITIAL_EXAMPLES and not description.exists():
        return  # The bundled studies have authored guides and bespoke CI journeys.
    metadata = read_json(description)
    check_fields(metadata, slug)
    if any(entry.get(key) != metadata.get(key) for key in CATALOG_FIELDS):
        raise ValueError(f"{slug}: catalog fields differ from styles/{slug}/style.json.")
    source = (folder / "demo.html").read_text(encoding="utf-8")
    verify_ready(folder, metadata, compile_demo(folder, source))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    for flag, help_text in (("--preview", "Compile this draft without adding it to the gallery."),
                            ("--check-ready", "Check release evidence and leave the catalog alone."),
                            ("--publish", "Register a finished draft in the local catalog."),
                            ("--refresh", "Apply an updated contributor guide and metadata to its registered style.")):
        mode.add_argument(flag, action="store_true", help=help_text)
    parser.add_argument("slug")
    parser.add_argument("title", nargs="?")
    for key in ("description", "action", "medium"):
        parser.add_argument("--" + key)
    parser.add_argument("--palette", nargs="+", default=["#e8deca", "#302426", "#8a3028"])
    args = parser.parse_args()
    try:
        verify_slug(args.slug)
        if args.preview:
            _, _, html = draft_files(args.slug)
            WORK.mkdir(exist_ok=True)
            output = WORK / f"{args.slug}.html"
            write_atomic(output, html)
            print(f"Open .style-work/{output.name}.")
            return
        with catalog_lock():
            path = STYLES / "catalog.json"
            catalog = read_json(path)
            if not (args.check_ready or args.publish or args.refresh):
                create(args, catalog)
                return
            existing = next((row for row in catalog if row["slug"] == args.slug), None)
            if args.refresh and existing is None:
                raise ValueError("Register a new style with --publish before refreshing it.")
            if args.publish or (not existing and not args.refresh):
                check_available(args.slug, catalog, creating=False)
            folder, metadata, html = draft_files(args.slug)
            verify_ready(folder, metadata, html)
            if args.publish or args.refresh:
                verify_draft_in_browser(html, metadata["journey"])
                fields = {key: metadata[key] for key in CATALOG_FIELDS}
                if args.refresh:
                    existing.update(fields)
                else:
                    catalog.append(fields)
                write_atomic(path, json_text(catalog))
                print(f"Saved {args.slug} in the catalog. Run python scripts/build.py and python scripts/check.py.")
            else:
                print(f"{args.slug} is ready for local registration. Publish will replay the journey on desktop and phone before registration.")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")


if __name__ == "__main__":
    main()
