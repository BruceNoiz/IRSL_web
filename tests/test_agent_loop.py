"""Exercise the real loop with local CLI stubs, without model services."""

import importlib.util
import json
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
REVIEW = """CHANGES_REQUESTED

## Blocking Issues
Original finding.
## Important Issues
None.
## Suggestions
None.
## Explanation
Original review.
"""
STUB = '''
import json
import os
from pathlib import Path
import sys
import time

name = Path(sys.argv[0]).name
events = Path(".agent/events.jsonl")
previous = [json.loads(line) for line in events.read_text().splitlines()] if events.exists() else []
count = sum(event["name"] == name for event in previous)
with events.open("a") as output:
    output.write(json.dumps({"name": name, "args": sys.argv[1:], "cwd": os.getcwd()}) + "\\n")
def setting(key, default):
    values = os.environ.get("LOOP_TEST_" + key, default).split(",")
    return values[min(count, len(values) - 1)]
if setting("STDERR", "yes") == "yes":
    print(name + " stderr", file=sys.stderr)
time.sleep(float(setting(name.upper() + "_SLEEP", "0")))
if name == "codex":
    if sys.argv[1:4] != ["--ask-for-approval", "never", "exec"]:
        sys.exit(2)
    Path(sys.argv[sys.argv.index("-o") + 1]).write_text("Implementation summary\\n")
    print("codex stdout")
elif name == "claude":
    review = setting("STATUS", "APPROVED") + "\\n"
    if setting("STYLE", "valid") != "bare":
        for heading in ("Blocking Issues", "Important Issues", "Suggestions", "Explanation"):
            review += "\\n## " + heading + "\\nNone.\\n"
    if sys.argv[sys.argv.index("--output-format") + 1] == "json":
        payload = {"type": "result", "subtype": setting("SUBTYPE", "success"),
                   "is_error": setting("IS_ERROR", "no") == "yes", "result": review}
        if setting("JSON", "valid") == "invalid":
            print("{broken json")
        else:
            print(json.dumps(payload))
    else:
        if setting("PROGRESS", "no") == "yes":
            print("I've verified the build output and the failed check; writing up the review now.\\n")
        print(review, end="")
elif name == "make":
    print("check stdout")
sys.exit(int(setting(name.upper() + "_EXIT", "0")))
'''


class AgentLoopTests(unittest.TestCase):
    def setUp(self):
        logs = ROOT / ".agent/logs"
        logs.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="loop-test-", dir=logs)
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.repo = self.parent / "repository with spaces"
        (self.repo / ".agent").mkdir(parents=True)
        (self.repo / "scripts").mkdir()
        shutil.copyfile(ROOT / "agent-loop.sh", self.repo / "agent-loop.sh")
        helper = ROOT / "scripts/agent_loop.py"
        if helper.exists():
            shutil.copyfile(helper, self.repo / "scripts/agent_loop.py")
        (self.repo / ".agent/TASK.md").write_text("# Fixture task\n")
        (self.repo / ".agent/REVIEW.md").write_text(REVIEW)
        (self.repo / ".gitignore").write_text(".agent/logs/\n.agent/events.jsonl\n")
        (self.repo / "Makefile").write_text("check:\n\t@exit 0\n")
        self.bin = self.parent / "bin"
        self.bin.mkdir()
        for name in ("codex", "claude", "make"):
            self.command(name, "#!" + sys.executable + "\n" + STUB)
        self.env = {key: value for key, value in os.environ.items()
                    if not key.startswith(("LOOP_TEST_", "GIT_", "AGENT_TIMEOUT_", "CLAUDE_MAX_TURNS"))}
        self.env["PATH"] = str(self.bin) + os.pathsep + os.environ["PATH"]
        self.env["AGENT_TIMEOUT_SECONDS"] = "10"
        self.real_git = shutil.which("git")
        self.git("init", "-q")

    def command(self, name, content):
        path = self.bin / name
        path.write_text(content)
        path.chmod(0o755)

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, env=self.env,
                              check=True, capture_output=True)

    def run_loop(self, *args, **settings):
        env = dict(self.env, **{"LOOP_TEST_" + key: value for key, value in settings.items()})
        return subprocess.run(["bash", str(self.repo / "agent-loop.sh"), *args],
                              cwd=self.parent, env=env, text=True,
                              capture_output=True, timeout=20)

    def events(self, name):
        path = self.repo / ".agent/events.jsonl"
        entries = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
        return [entry for entry in entries if entry["name"] == name]

    def run_dir(self):
        paths = list((self.repo / ".agent/logs").glob("run-*"))
        self.assertEqual(len(paths), 1)
        return paths[0]

    def assert_review_preserved(self):
        self.assertEqual((self.repo / ".agent/REVIEW.md").read_text(), REVIEW)

    def test_approval_uses_repository_root_correct_cli_and_saves_logs(self):
        result = self.run_loop()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.events("codex")[0]["args"][:3],
                         ["--ask-for-approval", "never", "exec"])
        self.assertEqual(self.events("make")[0]["args"], ["check"])
        self.assertTrue((self.repo / ".agent/REVIEW.md").read_text().startswith("APPROVED\n"))
        logs = self.run_dir()
        self.assertEqual((logs / "review-before.md").read_text(), REVIEW)
        self.assertIn("codex stderr", (logs / "codex-1.stderr.log").read_text())
        self.assertIn("codex stdout", (logs / "codex-1.stdout.log").read_text())
        self.assertIn("check stdout", (logs / "check-1.log").read_text())
        self.assertIn("claude stderr", (logs / "claude-1.stderr.log").read_text())
        self.assertFalse((self.parent / ".agent").exists())

    def test_changes_requested_runs_again(self):
        result = self.run_loop(STATUS="CHANGES_REQUESTED,APPROVED")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(len(self.events("codex")), 2)
        self.assertEqual(len(self.events("make")), 2)
        self.assertTrue((self.run_dir() / "review-1.md").read_text().startswith("CHANGES_REQUESTED"))

    def test_reviewer_turn_limit_default_and_override(self):
        for value in (None, "45"):
            with self.subTest(value=value):
                if value is not None:
                    self.env["CLAUDE_MAX_TURNS"] = value
                result = self.run_loop()
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                args = self.events("claude")[-1]["args"]
                self.assertEqual(args[args.index("--max-turns") + 1], value or "30")

    def test_invalid_turn_limit_stops_before_commands(self):
        for value in ("", "0", "-1", "1.5", "abc", "01"):
            with self.subTest(value=value):
                self.env["CLAUDE_MAX_TURNS"] = value
                result = self.run_loop()
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("CLAUDE_MAX_TURNS", result.stderr)
                self.assertFalse(self.events("codex"))
                self.assertFalse(self.events("claude"))

    def test_stdout_only_turn_limit_error_is_visible_and_preserves_review(self):
        result = self.run_loop(STATUS="Error: Reached max turns (10)", STYLE="bare",
                               STDERR="no", CLAUDE_EXIT="1")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Reached max turns (10)", result.stderr)
        self.assertIn("CLAUDE_MAX_TURNS", result.stderr)
        self.assertIn("--review-only", result.stderr)
        self.assertIn("claude-1.stdout.json", result.stderr)
        self.assertIn("claude-1.stderr.log", result.stderr)
        self.assertEqual((self.run_dir() / "claude-1.stderr.log").read_text(), "")
        self.assertEqual(len(self.events("claude")), 1)
        self.assert_review_preserved()

    def test_review_only_checks_current_changes_without_codex(self):
        (self.bin / "codex").unlink()
        self.command("codex", "#!/bin/sh\nexit 99\n")
        (self.repo / "current.txt").write_text("current working tree\n")
        result = self.run_loop("--review-only")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(self.events("codex"))
        self.assertEqual(len(self.events("make")), 1)
        self.assertEqual(len(self.events("claude")), 1)
        self.assertIn("current working tree", (self.run_dir() / "untracked-1.patch").read_text())
        self.assertFalse((self.run_dir() / "codex-1.txt").exists())
        prompt = self.events("claude")[0]["args"][-1]
        self.assertIn("review-only", prompt)
        self.assertNotIn("codex-1.txt", prompt)

    def test_review_only_changes_requested_exits_without_implementation(self):
        result = self.run_loop("--review-only", STATUS="CHANGES_REQUESTED", MAKE_EXIT="2")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertFalse(self.events("codex"))
        self.assertEqual(len(self.events("claude")), 1)
        self.assertIn("Check exit code: 2", self.events("claude")[0]["args"][-1])
        self.assertIn("Original finding.", (self.run_dir() / "review-before.md").read_text())
        self.assertNotEqual((self.repo / ".agent/REVIEW.md").read_text(), REVIEW)

    def test_progress_output_does_not_pollute_final_review(self):
        result = self.run_loop("--review-only", PROGRESS="yes",
                               STATUS="CHANGES_REQUESTED", MAKE_EXIT="2")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        args = self.events("claude")[0]["args"]
        self.assertEqual(args[args.index("--output-format") + 1], "json")
        logs = self.run_dir()
        payload = json.loads((logs / "claude-1.stdout.json").read_text())
        self.assertEqual((logs / "review-1.md").read_text(), payload["result"])
        self.assertEqual((self.repo / ".agent/REVIEW.md").read_text(), payload["result"])
        self.assertEqual((logs / "review-before.md").read_text(), REVIEW)
        self.assertFalse(self.events("codex"))

    def test_invalid_or_failed_json_result_preserves_review(self):
        for settings in ({"JSON": "invalid"}, {"IS_ERROR": "yes"},
                         {"SUBTYPE": "error_max_turns"}):
            with self.subTest(settings=settings):
                result = self.run_loop("--review-only", **settings)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assert_review_preserved()

    def test_review_only_failure_and_false_approval_preserve_review(self):
        for settings in ({"CLAUDE_EXIT": "9"}, {"STYLE": "bare"}, {"MAKE_EXIT": "1"}):
            with self.subTest(settings=settings):
                result = self.run_loop("--review-only", **settings)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertFalse(self.events("codex"))
                self.assert_review_preserved()

    def test_unknown_arguments_stop_before_commands(self):
        for args in (("--unknown",), ("--review-only", "unexpected")):
            with self.subTest(args=args):
                self.assertEqual(self.run_loop(*args).returncode, 1)
                self.assertFalse(self.events("codex"))
                self.assertFalse(self.events("claude"))

    def test_three_rejections_exit_two(self):
        result = self.run_loop(STATUS="CHANGES_REQUESTED")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(len(self.events("claude")), 3)

    def test_codex_failure_stops_before_checks_and_review(self):
        self.assertEqual(self.run_loop(CODEX_EXIT="7").returncode, 1)
        self.assertFalse(self.events("make"))
        self.assertFalse(self.events("claude"))
        self.assert_review_preserved()

    def test_reviewer_failure_preserves_old_review_and_captures_error(self):
        self.assertEqual(self.run_loop(CLAUDE_EXIT="9").returncode, 1)
        self.assert_review_preserved()
        self.assertIn("claude stderr", (self.run_dir() / "claude-1.stderr.log").read_text())

    def test_incomplete_or_unknown_review_cannot_replace_old_review(self):
        for settings in ({"STYLE": "bare"}, {"STATUS": "UNKNOWN"}):
            with self.subTest(settings=settings):
                self.assertEqual(self.run_loop(**settings).returncode, 1)
                self.assert_review_preserved()

    def test_failing_check_cannot_be_approved(self):
        result = self.run_loop(MAKE_EXIT="1")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(len(self.events("make")), 1)
        self.assert_review_preserved()

    def test_failing_check_can_be_fixed_in_next_round(self):
        result = self.run_loop(MAKE_EXIT="1,0", STATUS="CHANGES_REQUESTED,APPROVED")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(len(self.events("make")), 2)
        self.assertIn("Check exit code: 1", self.events("claude")[0]["args"][-1])

    def test_staged_unstaged_and_untracked_content_is_saved_without_head(self):
        tracked = self.repo / "tracked.txt"
        tracked.write_text("staged content\n")
        self.git("add", "tracked.txt")
        tracked.write_text("unstaged content\n")
        (self.repo / "new 文 件.txt").write_text("new content\n")
        (self.repo / "name\nwith newline.txt").write_text("newline filename content\n")
        (self.repo / "image.bin").write_bytes(b"\x00\x01\x02")
        self.assertEqual(self.run_loop().returncode, 0)
        logs = self.run_dir()
        self.assertIn("staged content", (logs / "staged-1.patch").read_text())
        self.assertIn("unstaged content", (logs / "diff-1.patch").read_text())
        self.assertIn("new content", (logs / "untracked-1.patch").read_text())
        self.assertIn("newline filename content", (logs / "untracked-1.patch").read_text())
        self.assertIn("GIT binary patch", (logs / "untracked-1.patch").read_text())
        self.assertIn("new 文 件.txt".encode(), (logs / "untracked-1.files").read_bytes())

    def test_git_failure_stops_before_review(self):
        self.command("git", '#!/bin/sh\nif [ "$1" = diff ]; then exit 128; fi\n'
                     + "exec " + shlex.quote(self.real_git) + ' "$@"\n')
        self.assertEqual(self.run_loop().returncode, 1)
        self.assertEqual(len(self.events("codex")), 1)
        self.assertFalse(self.events("claude"))
        self.assert_review_preserved()

    def test_backup_failure_stops_before_implementation(self):
        self.command("cp", "#!/bin/sh\nexit 1\n")
        self.assertEqual(self.run_loop().returncode, 1)
        self.assertFalse(self.events("codex"))
        self.assert_review_preserved()

    def test_missing_task_stops_before_implementation(self):
        (self.repo / ".agent/TASK.md").unlink()
        self.assertEqual(self.run_loop().returncode, 1)
        self.assertFalse(self.events("codex"))

    def test_missing_cli_stops_before_implementation(self):
        (self.bin / "claude").unlink()
        self.env["PATH"] = str(self.bin) + ":/usr/bin:/bin"
        result = self.run_loop()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Missing command: claude", result.stderr)
        self.assertFalse(self.events("codex"))

    def test_invalid_timeout_stops_before_implementation(self):
        self.env["AGENT_TIMEOUT_SECONDS"] = "0"
        self.assertEqual(self.run_loop().returncode, 1)
        self.assertFalse(self.events("codex"))

    def test_log_directory_failure_stops_before_implementation(self):
        (self.repo / ".agent/logs").write_text("not a directory")
        self.assertEqual(self.run_loop().returncode, 1)
        self.assertFalse(self.events("codex"))

    def test_repeated_runs_keep_previous_logs(self):
        self.assertEqual(self.run_loop().returncode, 0)
        first = self.run_dir()
        contents = (first / "review-1.md").read_bytes()
        self.assertEqual(self.run_loop().returncode, 0)
        self.assertEqual((first / "review-1.md").read_bytes(), contents)
        self.assertEqual(len(list((self.repo / ".agent/logs").glob("run-*"))), 2)

    def test_timeout_stops_loop_and_preserves_review(self):
        self.env["AGENT_TIMEOUT_SECONDS"] = "1"
        result = self.run_loop(CODEX_SLEEP="5")
        self.assertEqual(result.returncode, 1)
        self.assertFalse(self.events("claude"))
        self.assert_review_preserved()
        self.assertIn("timed out", (self.run_dir() / "codex-1.stderr.log").read_text())

    def helper(self):
        path = ROOT / "scripts/agent_loop.py"
        spec = importlib.util.spec_from_file_location("agent_loop", path)
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        return helper

    def test_atomic_publish_failure_preserves_review(self):
        helper = self.helper()
        candidate = self.parent / "candidate.md"
        candidate.write_text(REVIEW.replace("CHANGES_REQUESTED", "APPROVED", 1))
        target = self.repo / ".agent/REVIEW.md"
        with patch.object(helper.os, "replace", side_effect=OSError("disk error")):
            with self.assertRaises(OSError):
                helper.publish_review(candidate, target, 0)
        self.assert_review_preserved()
        self.assertFalse(list(target.parent.glob(".review-*")))

    def test_invalid_json_payload_cannot_be_extracted(self):
        helper = self.helper()
        valid = {"type": "result", "subtype": "success", "is_error": False, "result": REVIEW}
        payloads = [None, [], {}, {**valid, "type": "assistant"}]
        payloads.extend({**valid, "result": value} for value in (None, "", "  ", 42, {}))
        payloads.extend({key: value for key, value in valid.items() if key != missing}
                        for missing in ("subtype", "is_error", "result"))
        for payload in payloads:
            with self.subTest(payload=payload):
                source = self.parent / "candidate.json"
                source.write_text(json.dumps(payload))
                target = self.parent / "candidate.md"
                with self.assertRaises(ValueError):
                    helper.extract_review(source, target)
                self.assertFalse(target.exists())
                self.assert_review_preserved()

    def test_preamble_in_final_result_is_still_rejected(self):
        helper = self.helper()
        source = self.parent / "candidate.json"
        source.write_text(json.dumps({"type": "result", "subtype": "success",
                                     "is_error": False, "result": "Progress update\n" + REVIEW}))
        candidate = self.parent / "candidate.md"
        helper.extract_review(source, candidate)
        with self.assertRaisesRegex(ValueError, "Review must start"):
            helper.publish_review(candidate, self.repo / ".agent/REVIEW.md", 0)
        self.assert_review_preserved()

    def test_invalid_review_sections_preserve_old_review(self):
        helper = self.helper()
        for content in (b"", b"\xff", REVIEW.replace("Original review.", "").encode(),
                        REVIEW.replace("## Suggestions", "## Important Issues").encode(),
                        REVIEW.replace("## Important Issues", "## Extra").encode()):
            with self.subTest(content=content):
                source = self.parent / "candidate.md"
                source.write_bytes(content)
                with self.assertRaises(ValueError):
                    helper.publish_review(source, self.repo / ".agent/REVIEW.md", 0)
                self.assert_review_preserved()

    def test_reviewer_timeout_preserves_old_review(self):
        self.env["AGENT_TIMEOUT_SECONDS"] = "1"
        self.assertEqual(self.run_loop(CLAUDE_SLEEP="5").returncode, 1)
        self.assert_review_preserved()

    def test_check_timeout_stops_before_review(self):
        self.env["AGENT_TIMEOUT_SECONDS"] = "1"
        self.assertEqual(self.run_loop(MAKE_SLEEP="5").returncode, 1)
        self.assertFalse(self.events("claude"))
        self.assert_review_preserved()

    def test_timeout_kills_spawned_processes(self):
        marker = self.parent / "child-survived"
        program = (
            "import subprocess,sys,time; "
            "subprocess.Popen([sys.executable, '-c', "
            + repr("import time; from pathlib import Path; time.sleep(1); Path(" + repr(str(marker)) + ").touch()")
            + "]); time.sleep(10)"
        )
        result = subprocess.run([sys.executable, str(ROOT / "scripts/agent_loop.py"),
                                 "run", "0.2", sys.executable, "-c", program],
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 124, result.stderr)
        time.sleep(1.1)
        self.assertFalse(marker.exists(), "Timed-out child kept running")


if __name__ == "__main__":
    unittest.main()
