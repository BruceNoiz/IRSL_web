"""Serve the built files at the Pages subpath without an SPA fallback."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
from urllib.parse import urlsplit


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, base="/", **kwargs):
        self.base = base
        super().__init__(*args, **kwargs)

    def send_head(self):
        if not urlsplit(self.path).path.startswith(self.base):
            self.send_error(404)
            return None
        return super().send_head()

    def translate_path(self, path):
        return super().translate_path("/" + path[len(self.base):])


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    directory = root / "dist"
    base = "/" + os.environ.get("BASE_PATH", "/IRSL_web/").strip("/")
    if base != "/":
        base += "/"
    ThreadingHTTPServer(("127.0.0.1", 4322), partial(Handler, directory=str(directory), base=base)).serve_forever()
