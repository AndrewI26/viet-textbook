"""Serve the already-built dist/ folder. Nothing is rebuilt while serving.

Usage: uv run serve   (PORT=8000 by default)
       uv run dev     (build the site, then serve it)
       uv run clean   (delete dist/)
"""

import os
import shutil
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from . import site
from .common import DIST


class NoCacheHandler(SimpleHTTPRequestHandler):
    """Make the browser re-check files on every load, so a rebuild shows up on refresh."""

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def serve() -> None:
    if not (DIST / "index.html").exists():
        sys.exit("dist/ is empty. Run `uv run site` (or `uv run dev`) first.")
    port = int(os.environ.get("PORT", "8000"))
    handler = partial(NoCacheHandler, directory=str(DIST))
    with ThreadingHTTPServer(("127.0.0.1", port), handler) as server:
        print(f"Serving dist/ at http://localhost:{port}  (Ctrl+C to stop)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print()


def dev() -> None:
    site.main()
    serve()


def clean() -> None:
    shutil.rmtree(DIST, ignore_errors=True)
    print("Deleted dist/")
