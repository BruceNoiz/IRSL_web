"""Check orchestration with substituted commands, not real Astro/browser runs."""

from pathlib import Path
import importlib.util
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("website_check", Path(__file__).resolve().parents[1] / "scripts/check.py")
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


class CheckCommandTests(unittest.TestCase):
    def run_check(self, base, fail_browser=False):
        calls = []

        def run(command, **kwargs):
            calls.append((command, kwargs.get("env", {}).get("BASE_PATH")))
            return SimpleNamespace(returncode=int(fail_browser and command == ["npm", "run", "test:browser"]))

        with patch.dict(check.os.environ, {"BASE_PATH": base}), \
                patch.object(check.unittest.defaultTestLoader, "discover") as discover, \
                patch.object(check.unittest, "TextTestRunner") as runner, \
                patch.object(check.shutil, "which", return_value="available"), \
                patch.object(Path, "exists", return_value=True), \
                patch.object(check.subprocess, "run", side_effect=run):
            discover.return_value.countTestCases.return_value = 1
            runner.return_value.run.return_value.wasSuccessful.return_value = True
            result = check.main()
        return result, calls

    def test_build_static_and_browser_checks_use_each_base_and_leave_target_last(self):
        for target in ("/", "/IRSL_web/", "/renamed-lab/", "/nested/review-lab/"):
            with self.subTest(target=target):
                result, calls = self.run_check(target)
                self.assertEqual(result, 0)
                expected = [base for base in ("/", "/nested/review-lab/") if base != target] + [target]
                self.assertEqual([base for command, base in calls if command == ["npm", "run", "build"]], expected)
                self.assertEqual([base for command, base in calls if command == ["npm", "run", "test:browser"]], expected)
                self.assertEqual([command[-1] for command, _ in calls if "tests/check_static.py" in command], expected)
                self.assertEqual(calls[-1], (["npm", "run", "test:browser"], target))

    def test_browser_failure_stops_the_full_gate(self):
        result, calls = self.run_check("/my-lab/", fail_browser=True)
        self.assertNotEqual(result, 0)
        self.assertEqual([base for command, base in calls if command == ["npm", "run", "build"]], ["/"])


if __name__ == "__main__":
    unittest.main()
