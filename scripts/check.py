"""Run the same repository checks locally and in CI."""

from pathlib import Path
import os
import shutil
import subprocess
import sys
import unittest


def main():
    root = Path(__file__).resolve().parents[1]
    tests = root / "tests"
    if not tests.is_dir():
        print("FAIL: tests/ is missing.", file=sys.stderr)
        return 1

    suite = unittest.defaultTestLoader.discover(str(tests), pattern="test_*.py")
    if suite.countTestCases() == 0:
        print("FAIL: no tests found in tests/.", file=sys.stderr)
        return 1

    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1

    for command in ("node", "npm"):
        if not shutil.which(command):
            print(f"FAIL: {command} is required; see README.md.", file=sys.stderr)
            return 1
    node_tests = sorted(str(path.relative_to(root)) for path in tests.glob("*.test.mjs"))
    if subprocess.run(["node", "--test", *node_tests], cwd=root).returncode:
        return 1
    if not (root / "node_modules/.bin/astro").exists():
        print("FAIL: website dependencies are missing. Run npm install, then make check.", file=sys.stderr)
        return 1

    environment = {
        **os.environ,
        "ASTRO_TELEMETRY_DISABLED": "1",
        "PLAYWRIGHT_BROWSERS_PATH": str(root / ".agent/logs/playwright"),
    }
    if subprocess.run(["npm", "run", "check"], cwd=root, env=environment).returncode:
        return 1
    configured_base = "/" + os.environ.get("BASE_PATH", "/IRSL_web/").strip("/")
    if configured_base != "/":
        configured_base += "/"
    # Always exercise a different, nested repository path as well as the actual target.
    bases = [base for base in ("/", "/nested/review-lab/") if base != configured_base]
    for base in [*bases, configured_base]:
        environment["BASE_PATH"] = base
        command = ["npm", "run", "build"]
        if subprocess.run(command, cwd=root, env=environment).returncode:
            return 1
        if subprocess.run([sys.executable, "tests/check_static.py", "dist", base], cwd=root).returncode:
            return 1
        if subprocess.run(["npm", "run", "test:browser"], cwd=root, env=environment).returncode:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
