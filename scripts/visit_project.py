"""Exercise a creative site's planned routes and optional browser journeys on a local preview."""
import argparse
from contextlib import contextmanager
import ipaddress
import os
from pathlib import Path
import sys
from urllib.parse import urldefrag, urljoin, urlsplit

from playwright.sync_api import Error, sync_playwright

import project
from style_journeys import run_style_journey, validate_journey

VIEWPORTS = [(320, 640), (1440, 900)]
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def local_base(value):
    parts = urlsplit(value)
    host = parts.hostname
    if parts.scheme not in {"http", "https"} or not host or parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError("Supply a local HTTP(S) project directory without credentials, query or fragment.")
    if host != "localhost":
        try:
            local = ipaddress.ip_address(host).is_loopback
        except ValueError:
            local = False
        if not local:
            raise ValueError("The preview host must be localhost or a loopback IP address.")
    return value.rstrip("/") + "/"


def read_scenarios(directory, only):
    data = project.read_json(directory / project.PLAN)
    errors, _ = project.check(data)
    if errors:
        raise ValueError("\n".join(errors))
    routes = {route["id"]: route["examples"] for route in data["routes"]}
    if only and only not in routes:
        raise ValueError("Unknown family. Choose from " + ", ".join(routes))
    all_examples = {example for examples in routes.values() for example in examples}
    path = directory / "browser-journeys.json"
    recipes = project.read_json(path) if path.is_file() else {"version": 1, "journeys": []}
    if (not isinstance(recipes, dict) or type(recipes.get("version")) is not int or recipes["version"] != 1
            or not isinstance(recipes.get("journeys"), list)):
        raise ValueError("browser-journeys.json needs version 1 and a journeys list.")
    expected = recipes.get("expected_status", {})
    if not isinstance(expected, dict) or any(k not in all_examples or type(v) is not int or not 200 <= v <= 599
                                            for k, v in expected.items()):
        raise ValueError("expected_status maps declared examples to integer HTTP statuses (200–599).")
    selected = list(dict.fromkeys(example for key, examples in routes.items() if not only or key == only for example in examples))
    journeys = []
    for recipe in recipes["journeys"]:
        if not isinstance(recipe, dict) or not project.words(recipe.get("name")) or recipe.get("start") not in all_examples:
            raise ValueError("Each browser journey needs a name and a start URL drawn from site-plan.json examples.")
        validate_journey(recipe.get("steps"))
        if recipe["start"] in selected:
            journeys.append(recipe)
    return selected, journeys, expected


def origin(url):
    parts = urlsplit(url)
    return (parts.scheme, parts.hostname, parts.port or (443 if parts.scheme == "https" else 80))


@contextmanager
def fresh_page(browser, viewport, base, writes, expected):
    context = browser.new_context(viewport=viewport, reduced_motion="reduce" if viewport["width"] == 320 else "no-preference",
                                  service_workers="block", accept_downloads=False)
    problems = []
    local = origin(base)

    def guard(route):
        request = route.request
        outside = origin(request.url) != local
        if request.is_navigation_request():
            try:
                top_level = request.frame.parent_frame is None
            except Error:
                top_level = True  # Chromium can report a new-window navigation before its frame exists.
        else:
            top_level = False
        if outside and top_level:
            problems.append("journey left the local preview: " + request.url)
        elif request.method not in SAFE_METHODS and (outside or not writes):
            problems.append(f"blocked {request.method} {request.url}")
        else:
            route.continue_()
            return
        route.abort()

    def inspect_response(response):
        if response.status >= 400:
            wanted = expected.get(urldefrag(response.url).url)
            if response.status != wanted or not response.request.is_navigation_request():
                problems.append(f"HTTP {response.status}: {response.url}")

    def socket(route):
        host = urlsplit(route.url)
        socket_origin = origin(host._replace(scheme="https" if host.scheme == "wss" else "http").geturl())
        if writes and socket_origin == local:
            route.connect_to_server()
        else:
            route.close(code=1000, reason="read-only preview")

    context.route("**/*", guard)
    context.route_web_socket("**/*", socket)
    context.on("response", inspect_response)
    context.on("requestfailed", lambda req: problems.append(f"request failed: {req.url} ({req.failure})")
               if req.failure != "net::ERR_ABORTED" else None)
    context.on("weberror", lambda event: problems.append("script error: " + str(event.error)))
    page = context.new_page()
    page.set_default_timeout(6000)
    page.set_default_navigation_timeout(20000)
    try:
        yield page
        if problems:
            raise ValueError("; ".join(dict.fromkeys(problems)))
    finally:
        context.close()


def measure(page, label):
    # Allow a browser paint after navigation or the last asserted state.
    page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
    limit, actual = page.evaluate("""() => [document.documentElement.clientWidth,
      Math.max(document.documentElement.scrollWidth, document.body?.scrollWidth || 0)]""")
    if actual > limit + 1:
        raise ValueError(f"{label}: page width {actual}px exceeds viewport {limit}px")


def visit(directory, base, only, executable, writes):
    base = local_base(base)
    routes, journeys, expected = read_scenarios(directory, only)
    allowed_status = {urldefrag(urljoin(base, example)).url: status for example, status in expected.items()}
    failures = []
    with sync_playwright() as api:
        browser = api.chromium.launch(executable_path=executable)
        try:
            for width, height in VIEWPORTS:
                viewport = {"width": width, "height": height}
                scenarios = [(route, route, []) for route in routes]
                scenarios += [(item["name"], item["start"], item["steps"]) for item in journeys]
                for label, start, steps in scenarios:
                    try:
                        with fresh_page(browser, viewport, base, writes, allowed_status) as page:
                            response = page.goto(urljoin(base, start))
                            desired = expected.get(start)
                            if response is None or (desired is not None and response.status != desired):
                                actual = response.status if response else "no response"
                                raise ValueError(f"expected HTTP {desired or 'response'}, got {actual}")
                            measure(page, "opening")
                            if steps:
                                run_style_journey(page, steps)
                                measure(page, "after journey")
                    except (ValueError, Error, AssertionError) as error:
                        failures.append(f"{width}px · {label}: {error}")
        finally:
            browser.close()
    if failures:
        raise ValueError("\n".join(failures))
    route_label = "URL" if len(routes) == 1 else "URLs"
    journey_label = "journey" if len(journeys) == 1 else "journeys"
    print(f"Passed {len(routes)} representative {route_label} and {len(journeys)} declared browser {journey_label} at 320px and 1440px.")


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--project", required=True, type=Path, help="directory containing site-plan.json")
    args.add_argument("--base-url", required=True, help="local HTTP(S) preview directory, including any mount path")
    args.add_argument("--only-family", help="limit to one route family and journeys starting at its examples")
    args.add_argument("--executable", default=os.environ.get("DWC_CHROMIUM"), help="local Chromium override")
    args.add_argument("--allow-local-writes", action="store_true", help="allow modifying requests to a disposable preview backend on the same origin")
    options = args.parse_args()
    visit(options.project, options.base_url, options.only_family, options.executable, options.allow_local_writes)


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, ValueError, TypeError, Error) as exc:
        sys.exit(str(exc))
