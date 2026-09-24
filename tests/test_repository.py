"""Acceptance checks for the current documentation and content repository."""

from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    ".agent/TASK.md",
    ".agent/TASK.template.md",
    ".agent/REVIEW.md",
    "docs/HARNESS.md",
    "artifact/README.md",
    "src/README.md",
    "Makefile",
    "scripts/check.py",
    ".github/workflows/check.yml",
)
INLINE_LINK = re.compile(r"!?\[[^\]\n]*\]\((<[^>\n]+>|[^\s()]+)\)")


def markdown_files():
    paths = list(ROOT.glob("*.md"))
    for directory in (".agent", "docs", "artifact", "src", "tests"):
        paths.extend((ROOT / directory).rglob("*.md"))
    return sorted(path for path in paths if not path.is_relative_to(ROOT / ".agent/logs"))


def local_targets(path):
    """Read the inline link subset described in docs/HARNESS.md."""
    fence = None
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence is not None:
            continue
        line = re.sub(r"(`+).*?\1", "", line)
        for match in INLINE_LINK.finditer(line):
            target = match.group(1).strip("<>")
            url = urlsplit(target)
            if url.scheme or url.netloc or not url.path:
                continue
            yield number, target, (path.parent / unquote(url.path)).resolve()


class RepositoryTests(unittest.TestCase):
    def test_required_files_exist_and_are_not_empty(self):
        for name in REQUIRED_FILES:
            with self.subTest(path=name):
                path = ROOT / name
                self.assertTrue(path.is_file(), f"Missing required file: {name}")
                self.assertTrue(path.read_bytes().strip(), f"Empty required file: {name}")

    def test_markdown_is_utf8_and_starts_with_heading(self):
        for path in markdown_files():
            with self.subTest(path=str(path.relative_to(ROOT))):
                content = path.read_text(encoding="utf-8")
                if path != ROOT / ".agent/REVIEW.md":
                    self.assertRegex(content, r"\A# \S", "Expected a non-empty document with an H1 title")

    def test_review_uses_agent_loop_protocol(self):
        content = (ROOT / ".agent/REVIEW.md").read_text(encoding="utf-8")
        lines = content.splitlines()
        self.assertTrue(lines, "Review must not be empty")
        self.assertIn(lines[0], ("APPROVED", "CHANGES_REQUESTED"), "Invalid review status")
        for section in ("Blocking Issues", "Important Issues", "Suggestions", "Explanation"):
            with self.subTest(section=section):
                self.assertIn(f"## {section}", lines, "Missing review section")

    def test_local_links_and_images_exist_inside_repository(self):
        for path in markdown_files():
            for number, target, resolved in local_targets(path):
                with self.subTest(path=str(path.relative_to(ROOT)), line=number, target=target):
                    self.assertTrue(resolved.is_relative_to(ROOT), "Link leaves the repository")
                    self.assertTrue(resolved.exists(), "Local link target is missing")

    def test_artifact_index_covers_all_numbered_documents(self):
        documents = set((ROOT / "artifact").glob("[0-9][0-9]_*.md"))
        self.assertTrue(documents, "No numbered content documents found in artifact/")
        indexed = {resolved for _, _, resolved in local_targets(ROOT / "artifact/README.md")}
        missing = sorted(str(path.relative_to(ROOT)) for path in documents - indexed)
        self.assertFalse(missing, f"Content missing from artifact/README.md: {missing}")


if __name__ == "__main__":
    unittest.main()
