"""Serve a release locally, including GitHub Pages-style 404 responses and project subpaths."""
import argparse
from functools import partial
from html import escape
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


class PreviewHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, mount="", directory=None, **kwargs):
        self.mount = mount
        super().__init__(*args, directory=str(directory or ROOT), **kwargs)

    def recovery(self, status):
        # Like the Pages template, reuse the cabinet view with a mount-relative base
        # so deeply nested misses still load the stylesheet and working recovery links.
        base = escape(f"{self.mount}/weather/", quote=True)
        view = (Path(self.directory) / "weather/404.html").read_text(encoding="utf-8")
        body = view.replace('href="./', f'href="{base}').encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        return BytesIO(body)

    def send_error(self, code, message=None, explain=None):
        if code == HTTPStatus.NOT_FOUND:
            with self.recovery(code) as body:
                if self.command != "HEAD":
                    self.copyfile(body, self.wfile)
            return
        super().send_error(code, message, explain)

    def send_head(self):
        path = urlsplit(self.path).path
        if self.mount and path == self.mount:
            self.send_response(HTTPStatus.MOVED_PERMANENTLY)
            self.send_header("Location", self.mount + "/")
            self.end_headers()
            return None
        if not path.startswith(self.mount + "/"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return None
        if path == self.mount + "/404.html":
            return self.recovery(HTTPStatus.OK)
        return super().send_head()

    def translate_path(self, path):
        # Only filesystem resolution loses the mount; redirects retain the public URL.
        return super().translate_path(path[len(self.mount):])


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--port", type=int, default=8000)
    cli.add_argument("--mount", default="", help="Optional project subpath, for example /my-project")
    args = cli.parse_args()
    mount = args.mount.rstrip("/")
    if not re.fullmatch(r"(/[\w-][\w.-]*)*", mount):
        cli.error("--mount must be an absolute path of name segments, such as /my-project")
    handler = partial(PreviewHandler, mount=mount)
    with ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
        print(f"Preview at http://127.0.0.1:{server.server_port}{mount}/", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
