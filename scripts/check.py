"""Check the distributable site and its media credits without installing dependencies."""
import argparse
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

from add_style import check_published_contract

ROOT = Path(__file__).resolve().parents[1]
MEDIA_SUFFIXES = set(".avif .webp .jpg .jpeg .png .gif .ico .svg .woff .woff2 .otf .ttf .wav .mp3 .ogg .m4a .mp4 .webm".split())
OBJECTS = ("rain-catcher", "pocket-wind-counter", "folding-sundial", "dew-mirror", "cloud-window", "frost-comb")
WEATHER_ROUTES = ("index.html", "collection.html", "compare.html", "notes.html", "404.html",
                  *(f"objects/{slug}.html" for slug in OBJECTS))
CSS_URL = re.compile(r"""url\(\s*["']?([^"')]+?)["']?\s*\)|@import\s+["']([^"']+)["']""", re.I)
RESOURCE_RELS = {"stylesheet", "icon", "preload", "modulepreload", "manifest", "prefetch"}
PLACEHOLDER = re.compile(r"^(?:tbd|todo|unknown|placeholder|fill me in|\.\.\.)[.!]?$", re.I)


def css_urls(css):
    for match in CSS_URL.finditer(re.sub(r"/\*.*?\*/", "", css, flags=re.S)):
        yield match.group(1) or match.group(2)


def source_candidates(srcset):
    # Each whitespace-delimited URL can contain commas (notably in data: sources).
    for match in re.finditer(r"(?:^|,\s*)(\S+?)(?=\s+(?:\d+(?:\.\d+)?[xw])(?:\s*,|\s*$)|,\s+|$)", srcset):
        yield match.group(1)


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.refs = []
        self.ids = Counter()
        self.idrefs = []
        self.css = False
        self.issues = []
        self.lang = ""
        self.has_title = False
        self.feed(source)
        self.close()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang", "")
        if tag == "title":
            self.has_title = True
        if tag == "style":
            self.css = True
        if tag == "base" and a.get("href"):
            self.issues.append("base href prevents reliable directory-relative links")
        if a.get("id"):
            self.ids[a["id"]] += 1
        if tag == "img" and "alt" not in a:
            self.issues.append("image lacks alt attribute")
        for key in ("aria-labelledby", "aria-describedby", "aria-controls", "for"):
            self.idrefs.extend((key, part) for part in (a.get(key) or "").split())
        if "href" in a:
            embedded = tag in {"use", "image"} or (tag == "link" and bool(set((a.get("rel") or "").lower().split()) & RESOURCE_RELS))
            self.refs.append((a["href"] or "", embedded))
        for key in ("src", "poster", "action", "formaction"):
            if key in a:
                self.refs.append((a[key] or "", key in {"src", "poster"}))
        if a.get("srcset"):
            self.refs.extend((ref, True) for ref in source_candidates(a["srcset"]))
        if a.get("style"):
            self.refs.extend((ref, True) for ref in css_urls(a["style"]))

    def handle_endtag(self, tag):
        if tag == "style":
            self.css = False

    def handle_data(self, data):
        if self.css:
            self.refs.extend((ref, True) for ref in css_urls(data))


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def is_draft(root, relative, styles):
    return (len(relative.parts) > 2 and relative.parts[0] == "styles"
            and relative.parts[1] not in styles and (root / relative.parts[0] / relative.parts[1] / "style.json").is_file())


def credits(root, styles, issues):
    manifest = root / "credits/assets.json"
    records = read_json(manifest)
    if not isinstance(records, list):
        raise ValueError("credits/assets.json must contain a list")
    seen = set()
    for index, record in enumerate(records, 1):
        keys = ("path", "origin", "credit", "terms")
        if not isinstance(record, dict) or any(not isinstance(record.get(k), str) or
                not record[k].strip() or PLACEHOLDER.fullmatch(record[k].strip()) for k in keys):
            issues.append(f"credits/assets.json entry {index}: fill out {', '.join(keys)}")
            continue
        name = record["path"]
        relative = Path(name)
        target = root / relative
        if (relative.is_absolute() or "\\" in name or ".." in relative.parts or relative.as_posix() != name
                or not target.resolve().is_relative_to(root) or not target.is_file()):
            issues.append(f"credits/assets.json: missing or invalid asset {name!r}")
        if name in seen:
            issues.append(f"credits/assets.json: duplicate entry for {name}")
        seen.add(name)
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if any(part in {".git", ".venv", "venv", ".style-work", ".design-moves", "node_modules", "__pycache__"} for part in rel.parts):
            continue
        if not is_draft(root, rel, styles) and path.is_file() and path.suffix.lower() in MEDIA_SUFFIXES and rel.as_posix() not in seen:
            issues.append(f"uncredited media: {rel}")


def inspect_site(root, styles, issues):
    standalone = {root / f"{slug}.html" for slug in styles}
    documents = sorted(standalone | {root / "index.html"} | set((root / "weather").rglob("*.html")))
    pages = {}
    references = {}
    for file in documents:
        name = file.relative_to(root)
        page = Page(file.read_text(encoding="utf-8"))
        pages[file] = page
        references[file] = page.refs
        issues.extend(f"{name}: {message}" for message in page.issues)
        if not page.has_title or not page.lang:
            issues.append(f"{name}: missing title or document language")
        issues.extend(f"{name}: duplicate id {i}" for i, count in page.ids.items() if count > 1)
        issues.extend(f"{name}: {attrib} refers to missing id {part}" for attrib, part in page.idrefs if part not in page.ids)

    for file in (root / "weather").rglob("*.css"):
        references[file] = [(url, True) for url in css_urls(file.read_text(encoding="utf-8"))]

    for source, refs in references.items():
        for value, embedded in refs:
            parts = urlsplit(value.strip())
            defect = None
            if parts.scheme == "data" and embedded:
                continue
            if parts.scheme in {"https", "http", "tel", "mailto"} or parts.netloc:
                if not embedded:
                    continue
                defect = "network dependency"
            elif parts.scheme:
                defect = f"unsupported URL scheme {parts.scheme}"
            else:
                urlpath = unquote(parts.path)
                if urlpath.startswith("/") or "\\" in urlpath:
                    defect = "use a directory-relative URL"
                else:
                    target = (source.parent / urlpath).resolve() if urlpath else source
                    if target.is_dir():
                        target /= "index.html"
                    if not target.is_relative_to(root) or not target.is_file():
                        defect = "missing or outside the repository"
                    elif embedded and source in standalone and target != source:
                        defect = "standalone export depends on a separate file"
                    elif target in pages and parts.fragment and unquote(parts.fragment) not in pages[target].ids:
                        defect = "missing destination id"
            if defect:
                issues.append(f"{source.relative_to(root)}: {value[:160]} — {defect}")


def inspect_markdown(root, styles, issues):
    # Resolve explicit inline links in prose. Heading slugs and external URLs are reviewed separately.
    link = re.compile(r"!?\[[^\]\n]+\]\((?:<([^>\n]+)>|([^\s)]+))(?:\s+[\x22\x27].*?[\x22\x27])?\)")
    for path in root.rglob("*.md"):
        relative = path.relative_to(root)
        if any(part in {".git", ".venv", ".style-work", "venv", "node_modules", "_template"} for part in relative.parts):
            continue
        if is_draft(root, relative, styles):
            continue
        fence = ""
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.lstrip()
            marker = re.match(r"`{3,}|~{3,}", stripped)
            if marker:
                if not fence:
                    fence = marker[0]
                elif marker[0].startswith(fence):
                    fence = ""
                continue
            if fence:
                continue
            for match in link.finditer(re.sub(r"`[^`]*`", "", line)):
                value = match.group(1) or match.group(2)
                parts = urlsplit(value)
                if not parts.path or parts.scheme or parts.netloc:
                    continue
                target = (path.parent / unquote(parts.path)).resolve()
                if not target.is_relative_to(root) or not target.exists():
                    issues.append(f"{relative}:{line_number}: missing local documentation target {value}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="unpacked repository to check")
    root = parser.parse_args().root.resolve()
    issues = []
    try:
        catalog = read_json(root / "styles/catalog.json")
        styles = {row["slug"] for row in catalog}
        for entry in catalog:
            try:
                check_published_contract(root, entry)
            except (KeyError, TypeError, ValueError, OSError) as error:
                issues.append(f"{entry.get('slug', '?')}: {error}")
        required = ["index.html", "README.md", "LICENSE", "CONTRIBUTING.md", "REFERENCES.md",
                    "skills/design-with-character/SKILL.md", "credits/assets.json"]
        required += [f"weather/{name}" for name in WEATHER_ROUTES]
        for name in required:
            if not (root / name).is_file():
                issues.append(f"required file missing: {name}")
        for script in ("scripts/build.py", "weather/build.py"):
            build = subprocess.run([sys.executable, str(root / script), "--check"], cwd=root, text=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if build.returncode:
                issues.append(build.stdout.strip())
        for check in (credits, inspect_site, inspect_markdown):
            try:
                check(root, styles, issues)
            except (KeyError, TypeError, ValueError, OSError) as error:
                issues.append(str(error))
    except (KeyError, TypeError, ValueError, OSError) as error:
        issues.append(str(error))
    if issues:
        raise SystemExit("\n".join(f"- {issue}" for issue in sorted(set(issues))))
    print(f"Static checks passed for {len(styles)} style exports, their gallery, Weather Cabinet and media credits.")


if __name__ == "__main__":
    main()
