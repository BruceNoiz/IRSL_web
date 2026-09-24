"""Exercise the static HTTP handler without requiring a listening socket."""

from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from serve_static import Handler

ROOT = Path(__file__).resolve().parents[1]


class Request:
    def __init__(self, method, path):
        self.input = BytesIO(f"{method} {path} HTTP/1.0\r\n\r\n".encode())
        self.output = bytearray()

    def makefile(self, *args):
        return self.input

    def sendall(self, data):
        self.output.extend(data)


class StaticServerTests(unittest.TestCase):
    def setUp(self):
        logs = ROOT / ".agent/logs"
        logs.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=logs)
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        (self.directory / "index.html").write_text("home")
        (self.directory / "contact").mkdir()
        (self.directory / "contact/index.html").write_text("contact")

    def request(self, method, path, base):
        request = Request(method, path)
        with patch.object(Handler, "log_message"):
            Handler(request, ("127.0.0.1", 1234), None, directory=str(self.directory), base=base)
        headers, body = bytes(request.output).split(b"\r\n\r\n", 1)
        return headers.decode(), body

    def test_get_and_head_under_root_and_arbitrary_subpaths(self):
        for base in ("/", "/IRSL_web/", "/nested/renamed-lab/"):
            for method in ("GET", "HEAD"):
                with self.subTest(base=base, method=method):
                    headers, body = self.request(method, base + "contact/?from=test", base)
                    self.assertIn("200 OK", headers)
                    self.assertIn("Content-Length: 7", headers)
                    self.assertEqual(body, b"contact" if method == "GET" else b"")

    def test_directory_redirect_preserves_base_and_query(self):
        for method in ("GET", "HEAD"):
            headers, _ = self.request(method, "/my-lab/contact?from=test", "/my-lab/")
            self.assertIn("301 Moved Permanently", headers)
            self.assertIn("Location: /my-lab/contact/?from=test", headers)

    def test_outside_base_and_missing_pages_return_404_without_spa_fallback(self):
        for path in ("/", "/contact/", "/my-lab-other/", "/my-lab/missing/"):
            for method in ("GET", "HEAD"):
                headers, _ = self.request(method, path, "/my-lab/")
                self.assertIn("404", headers)


if __name__ == "__main__":
    unittest.main()
