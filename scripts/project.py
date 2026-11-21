"""Plan a creative site and inspect route coverage or recent design decisions."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
from urllib.parse import unquote, urlsplit
from uuid import uuid4


PLAN = "site-plan.json"
HISTORY = ".design-moves"
ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def starter():
    return {
        "version": 1, "audience": "", "primary_task": "", "subject_detail": "",
        "shared": [], "routes": [
            {"id": "entrance", "job": "", "composition": "", "action": "",
             "return_path": "", "states": [], "examples": []}
        ],
        "journeys": [{"goal": "", "through": ["entrance"], "success": ""}],
    }


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_new(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def words(value):
    return isinstance(value, str) and bool(value.strip())


def texts(value):
    return isinstance(value, list) and bool(value) and all(words(v) for v in value)


def relative_example(value):
    """Keep representative URLs concrete and portable under a project subpath."""
    try:
        url = urlsplit(value)
    except ValueError:
        return False
    path = unquote(url.path)
    if url.scheme or url.netloc or not path or path.startswith("/"):
        return False
    return not any(c in path for c in ("\\", "\x00")) and ".." not in PurePosixPath(path).parts


def check(data, site=None):
    if not isinstance(data, dict):
        return ["the plan must be a JSON object"], []
    errors, advice = [], []
    if type(data.get("version")) is not int or data["version"] != 1:
        errors.append("expected plan version 1")
    for key in ("audience", "primary_task", "subject_detail"):
        if not words(data.get(key)):
            errors.append("describe " + key)
    if not texts(data.get("shared")):
        errors.append("shared needs the site conventions visitors can rely on")
    routes = data.get("routes")
    if not isinstance(routes, list) or not routes:
        return errors + ["include at least one route family"], advice
    ids = set()
    compositions = defaultdict(list)
    for i, route in enumerate(routes):
        if not isinstance(route, dict):
            errors.append(f"route {i + 1} must be an object")
            continue
        key = route.get("id")
        if not isinstance(key, str) or not ID.fullmatch(key) or key in ids:
            errors.append(f"route {i + 1} needs a unique lowercase ID")
            continue
        ids.add(key)
        for field in ("job", "composition", "action", "return_path"):
            if not words(route.get(field)):
                errors.append(f"{key}: describe {field}")
        if words(route.get("composition")):
            signature = " ".join(route["composition"].casefold().split())
            compositions[signature].append(key)
        for field in ("states", "examples"):
            if not texts(route.get(field)):
                errors.append(f"{key}: list at least one {field}")
        if texts(route.get("examples")):
            for example in route["examples"]:
                if not relative_example(example):
                    errors.append(f"{key}: use a relative example URL ({example!r})")
                elif site:
                    path = (site / unquote(urlsplit(example).path)).resolve()
                    if path.is_dir():
                        path = (path / "index.html").resolve()
                    if not path.is_relative_to(site.resolve()) or not path.is_file():
                        errors.append(f"{key}: missing local route {example}")
    for repeated in compositions.values():
        if len(repeated) > 1:
            advice.append("Same declared composition on " + ", ".join(repeated) +
                          ". Compare their jobs on screen; keep useful repetition.")
    journeys = data.get("journeys")
    covered = set()
    if not isinstance(journeys, list) or not journeys:
        errors.append("include a visitor journey")
    else:
        for n, journey in enumerate(journeys, 1):
            if not isinstance(journey, dict) or not all(words(journey.get(k)) for k in ("goal", "success")):
                errors.append(f"journey {n}: state the goal and observable success")
            path = journey.get("through") if isinstance(journey, dict) else None
            if not texts(path):
                errors.append(f"journey {n}: list route IDs in order")
            else:
                covered.update(path)
                for missing in sorted(set(path) - ids):
                    errors.append(f"journey {n}: unknown route {missing}")
    for missing in sorted(ids - covered):
        errors.append(f"{missing}: include an arrival or recovery journey")
    return errors, advice


def history(directory):
    folder = directory / HISTORY
    if not folder.is_dir():
        return []
    return sorted((read_json(path) for path in folder.glob("*.json")),
                  key=lambda row: row["time"], reverse=True)


def record(directory, move, reason):
    if not all(words(v) and len(v.strip()) <= 240 and len(v.splitlines()) == 1 for v in (move, reason)):
        raise ValueError("Use a single line, up to 240 characters, for the move and its reason.")
    folder = directory / HISTORY
    folder.mkdir(exist_ok=True)
    row = {"time": datetime.now(timezone.utc).isoformat(), "move": move.strip(), "reason": reason.strip()}
    # Separate records let two contributors save at once. Readers only see completed files.
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=folder, delete=False) as tmp:
        json.dump(row, tmp, ensure_ascii=False)
        tmp.write("\n")
    Path(tmp.name).replace(folder / (uuid4().hex + ".json"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="Project directory (default: current directory)")
    subs = parser.add_subparsers(dest="command", required=True)
    subs.add_parser("init", help="Create an editable site-plan.json without overwriting an existing plan")
    verify = subs.add_parser("check", help="Validate route families, journey coverage and optional built routes")
    verify.add_argument("--site", type=Path, help="Optional static publication directory to verify example URLs against")
    subs.add_parser("walk", help="Print the planned visitor journeys and states for a walkthrough")
    log = subs.add_parser("record", help="Save a project-local design choice and the reason it fits")
    log.add_argument("move")
    log.add_argument("--because", required=True)
    subs.add_parser("moves", help="Show the last twelve choices saved in this project")
    args = parser.parse_args()
    project = args.project.resolve()
    plan = project / PLAN
    if args.command == "init":
        project.mkdir(parents=True, exist_ok=True)
        write_new(plan, starter())
        print(f"Created {plan}. Describe route families and enter one example URL per family.")
    elif args.command == "record":
        record(project, args.move, args.because)
        print("Saved a design choice in this project.")
    elif args.command == "moves":
        rows = history(project)[:12]
        if not rows:
            print("No design choices recorded here yet.")
        for row in rows:
            print(f"{row['move']} — {row['reason']}")
    else:
        data = read_json(plan)
        errors, advice = check(data, getattr(args, "site", None))
        if errors:
            raise ValueError("\n".join(errors))
        for message in advice:
            print("Review:", message)
        if args.command == "walk":
            by_id = {r["id"]: r for r in data["routes"]}
            for journey in data["journeys"]:
                print(f"\n{journey['goal']} → {journey['success']}")
                for route_id in journey["through"]:
                    route = by_id[route_id]
                    print(f"  {route_id} · {route['examples'][0]} · {', '.join(route['states'])}")
        else:
            print(f"Valid plan: {len(data['routes'])} route families, {len(data['journeys'])} visitor journeys.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as error:
        sys.exit(str(error))
