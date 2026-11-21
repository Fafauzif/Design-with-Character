"""Publish the cabinet's static pages from the instrument records. Requires Python 3."""
import argparse
from html import escape as h
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ITEMS = json.loads((ROOT / "instruments.json").read_text(encoding="utf-8"))
BY_ID = {item["slug"]: item for item in ITEMS}
DEFAULT_PAIR = ("rain-catcher", "dew-mirror")


def plate(item, prefix="", alt=True):
    return f'<img src="{prefix}{h(item["image"])}" alt="{h(item["alt"]) if alt else ""}" width="540" height="540">'


def shell(title, page, content, prefix="", extra=""):
    nav = []
    for label, route, name in [("Collection", "collection", "collection"), ("Compare", "compare", "compare"), ("Field notes", "notes", "notes")]:
        current = ' aria-current="page"' if name == page else ""
        nav.append(f'<a href="{prefix}{route}.html"{current}>{label}</a>')
    scripts = '' if page=='missing' else f'<script defer src="{prefix}assets/catalogue.js"></script><script defer src="{prefix}assets/cabinet.js"></script>'
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{h(title)} · Weather Cabinet</title><link rel="stylesheet" href="{prefix}assets/cabinet.css">
{scripts}</head>
<body data-page="{page}" data-base="{prefix}" {extra}>
<a class="skip" href="#main">Skip to content</a>
<header class="mast"><a class="brand" href="{prefix}index.html" aria-label="Weather Cabinet entrance"><span class="mark" aria-hidden="true">W</span> Weather Cabinet</a>
<nav aria-label="Cabinet">{''.join(nav)}</nav></header>
<main id="main">{content}</main>
{f'<div class="tail"><a href="{prefix}../index.html">← Style gallery</a></div>' if page in ('home','missing') else ''}
</body></html>
'''


def home():
    items = [BY_ID[s] for s in ("dew-mirror", "pocket-wind-counter", "cloud-window")]
    specimens = "".join(f'''<a class="window-piece piece-{i}" href="objects/{s["slug"]}.html">
    <div class="piece-art">{plate(s,alt=False)}</div><span class="tag">{h(s["name"])} <b aria-hidden="true">→</b></span></a>''' for i,s in enumerate(items))
    return shell("Entrance", "home", f'''<section class="shop">
    <div class="sign"><h1><span>Weather</span> <span>Cabinet</span></h1>
    <p class="sign-note">Six imagined instruments for reading the sky from a garden gate.</p></div>
    <div class="window">{specimens}</div>
    <a class="drawer" href="collection.html"><span class="screw" aria-hidden="true"></span><span class="drawer-label">Open the collection <span aria-hidden="true">→</span></span><span class="pull" aria-hidden="true"></span><span class="screw" aria-hidden="true"></span></a></section>''')


def collection():
    rows = []
    for s in ITEMS:
        search = " ".join(s[k] for k in ("name","family","field","material","signal","place","when"))
        rows.append(f'''<li data-search="{h(search.casefold())}" data-family="{s["family"]}">
        <a class="index-entry" aria-label="{h(s["name"])}" href="objects/{s["slug"]}.html"><div class="index-plate" style="--tint:{s["color"]}">{plate(s,alt=False)}</div>
        <span><small>{h(s["field"])}</small><strong>{h(s["name"])}</strong><span class="index-material">{h(s["material"])}</span></span><b class="medium-arrow" aria-hidden="true">→</b></a></li>''')
    return shell("The collection","collection",f'''<section class="catalog wrap">
    <div class="catalog-heading"><div><a class="back" href="index.html">← Cabinet entrance</a><h1>The collection</h1></div>
    <p>Look up an instrument by name, material, or the weather it records.</p></div>
    <form class="lookup" id="lookup" role="search"><label for="search">Find an instrument<input id="search" type="search" name="q" placeholder="Try glass or frost" autocomplete="off"></label>
    <label for="family">Weather family<select id="family" name="family"><option value="">All weather</option><option>Air</option><option>Light</option><option>Water</option></select></label></form>
    <p class="count" id="result-count" role="status">6 instruments</p>
    <ol class="index-list">{''.join(rows)}</ol><div class="empty" id="empty" hidden><h2>No instruments found</h2><p>Try a material such as brass, or look across all weather families.</p><button id="clear-search" type="button">Clear search</button></div>
    <noscript><p>All six instruments are listed above. Search and filtering require JavaScript.</p></noscript></section>''')


def detail(s):
    other = BY_ID[s["related"]]
    return shell(s["name"],"object",f'''<section class="plate-spread" style="--tint:{s["color"]}">
    <div class="big-plate"><a class="back" href="../collection.html">← All instruments</a>
    <div class="hero-object">{plate(s,"../")}</div><div class="caption"><span>Plate {s["number"]}</span><span>{h(s["material"])}</span></div></div>
    <article class="record"><p class="smallcap">{h(s["field"])}</p><h1>{h(s["name"])}</h1><p class="intro">{h(s["intro"])}</p>
    <p>{h(s["detail"])}</p><h2>From the keeper’s log</h2><p>{h(s["account"])}</p>
    <div class="record-links"><a class="action" href="#write-note">Write a field note <span aria-hidden="true">↓</span></a><a href="../compare.html?a={s["slug"]}&amp;b={other["slug"]}">Compare with {h(other["name"].lower())}</a></div></article></section>
    <section class="writing" id="write-note"><div><p class="smallcap">Field notes</p><h2>{h(s["prompt"])}</h2></div><form id="note-form"><label for="observation">Your observation</label><textarea id="observation" maxlength="2000" rows="4" required></textarea>
    <div class="form-actions"><button type="submit">Save field note</button><a href="../notes.html">Open field notes</a></div><p class="status" role="status" id="note-status"></p>
    <noscript><p>Saving notes requires JavaScript.</p></noscript></form></section>''',"../",f'data-id="{s["slug"]}"')


def options(selected):
    return "".join(f'<option value="{s["slug"]}"{" selected" if selected==s["slug"] else ""}>{h(s["name"])}</option>' for s in ITEMS)


def compare():
    sides = []
    for side, label, slug in zip(("left","right"),("Left instrument","Right instrument"),DEFAULT_PAIR):
        s = BY_ID[slug]
        sides.append(f'''<div class="tray" data-side="{side}" style="--tint:{s["color"]}">
        <label for="{side}">{label}</label><select id="{side}">{options(slug)}</select><a class="tray-art" id="{side}-link" href="objects/{slug}.html" aria-label="Open {s["name"]}">{plate(s)}</a></div>''')
    traits = [("signal","What to look for"),("place","Typical setting"),("when","When to look"),("material","Material")]
    rows = "".join(f'<tr><th scope="row">{label}</th><td data-attr="{key}" data-col="left">{BY_ID[DEFAULT_PAIR[0]][key]}</td><td data-attr="{key}" data-col="right">{BY_ID[DEFAULT_PAIR[1]][key]}</td></tr>' for key,label in traits)
    return shell("Compare instruments","compare",f'''<section class="bench"><div class="bench-body wrap"><div class="bench-title"><h1>Comparison bench</h1><p>Set two instruments side by side.</p></div><div class="trays">{''.join(sides)}</div>
    <p class="sr" id="compare-status" role="status"></p>
    <table><caption class="sr">Instrument comparison</caption><thead><tr><th scope="col">Observation</th><th scope="col" data-heading="left">Rain catcher</th><th scope="col" data-heading="right">Dew mirror</th></tr></thead><tbody>{rows}</tbody></table>
    <noscript><p>Changing the instruments requires JavaScript.</p></noscript></div></section>''')


def notes():
    return shell("Field notes","notes",'''<section class="notebook wrap"><div class="ledger-gutter" aria-hidden="true"></div><div class="notebook-inner">
    <div class="notebook-head"><h1>Field notes</h1><p id="notes-count" role="status">Your observations</p></div>
    <p class="storage-info" id="storage-info" hidden></p><div id="entries"></div>
    <div id="blank"><h2>A fresh page</h2><p>Start at an instrument. Its field-note prompt gives you a place to record what caught your eye.</p><a class="action" href="collection.html">Choose an instrument <span aria-hidden="true">→</span></a></div>
    <p role="status" id="notes-status"></p><button id="undo" hidden>Undo removal</button>
    <details class="backup"><summary>Back up or restore notes</summary><p>Download a copy for another device. Restoring adds any missing instruments’ notes and keeps entries already here. Each instrument has one editable note.</p>
    <div class="backup-actions"><button type="button" id="export">Export notes</button><label for="import-file">Import notes <input type="file" id="import-file" accept=".json,application/json"></label></div></details>
    <noscript><p>This notebook requires JavaScript to read and save entries.</p></noscript></div></section>''')


def missing():
    return shell("Missing drawer","missing",'''<section class="lost wrap"><span class="lost-handle" aria-hidden="true"></span><p class="smallcap">404</p><h1>This drawer is empty.</h1><p>The instrument may be filed under another name.</p><a class="action" href="./collection.html">Search the collection <span aria-hidden="true">→</span></a></section>''',"./")


def outputs():
    files = {"index.html":home(),"collection.html":collection(),"compare.html":compare(),"notes.html":notes(),"404.html":missing(),
             "assets/catalogue.js":"// Generated from instruments.json by build.py.\nconst instruments = "+json.dumps(ITEMS,ensure_ascii=False,indent=2)+";\n"}
    files.update({f'objects/{s["slug"]}.html':detail(s) for s in ITEMS})
    return files


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--check",action="store_true",help="Fail when a published file is missing or stale.")
    args = cli.parse_args()
    for name, content in outputs().items():
        path = ROOT / name
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                cli.exit(1,f"Rebuild weather pages: {name} is missing or stale.\n")
        else:
            path.parent.mkdir(exist_ok=True,parents=True)
            path.write_text(content,encoding="utf-8")
