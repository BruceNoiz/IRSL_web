"""Portable timeouts and atomic review publication for agent-loop.sh."""

import argparse
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile


def run_command(seconds, command):
    if not math.isfinite(seconds) or seconds <= 0 or not command:
        raise ValueError("A positive timeout and command are required")
    process = subprocess.Popen(command, start_new_session=True)

    def interrupted(signum, frame):
        raise InterruptedError(signum)

    previous_handler = signal.signal(signal.SIGTERM, interrupted)
    try:
        return process.wait(timeout=seconds)
    except subprocess.TimeoutExpired:
        print(f"Command timed out after {seconds:g} seconds: {command[0]}", file=sys.stderr)
        result = 124
    except KeyboardInterrupt:
        result = 130
    except InterruptedError as error:
        result = 128 + error.args[0]
    finally:
        signal.signal(signal.SIGTERM, previous_handler)

    # Stop descendants too, including those left behind when the leader exits.
    try:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass
    finally:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
    return result


def extract_review(source, target):
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("type") != "result":
        raise ValueError("Claude output must be a JSON result object")
    if payload.get("subtype") != "success" or payload.get("is_error") is not False:
        raise ValueError(f"Claude result was not successful: {payload.get('subtype')}")
    content = payload.get("result")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Claude result must contain non-empty review text")
    target.write_text(content, encoding="utf-8")


def publish_review(source, target, checks_exit):
    content = source.read_bytes()
    lines = content.decode("utf-8").splitlines()
    if not lines or lines[0] not in ("APPROVED", "CHANGES_REQUESTED"):
        raise ValueError("Review must start with APPROVED or CHANGES_REQUESTED")
    headings = ["## " + name for name in
                ("Blocking Issues", "Important Issues", "Suggestions", "Explanation")]
    sections = [index for index, line in enumerate(lines) if line.startswith("## ")]
    if [lines[index] for index in sections] != headings:
        raise ValueError("Review must contain the four required sections once, in order")
    for start, end in zip(sections, sections[1:] + [len(lines)]):
        if not "\n".join(lines[start + 1:end]).strip():
            raise ValueError(f"Review section is empty: {lines[start]}")
    if lines[0] == "APPROVED" and checks_exit != 0:
        raise ValueError("Cannot approve: make check failed")

    pending = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".review-", delete=False) as output:
            pending = Path(output.name)
            output.write(content)
        os.replace(pending, target)
    finally:
        if pending is not None:
            pending.unlink(missing_ok=True)
    return lines[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    run = commands.add_parser("run")
    run.add_argument("seconds", type=float)
    run.add_argument("command", nargs=argparse.REMAINDER)
    extract = commands.add_parser("extract")
    extract.add_argument("source", type=Path)
    extract.add_argument("target", type=Path)
    publish = commands.add_parser("publish")
    publish.add_argument("source", type=Path)
    publish.add_argument("target", type=Path)
    publish.add_argument("checks_exit", type=int)
    args = parser.parse_args()
    try:
        if args.action == "run":
            return run_command(args.seconds, args.command)
        if args.action == "extract":
            extract_review(args.source, args.target)
            return 0
        print(publish_review(args.source, args.target, args.checks_exit))
        return 0
    except (OSError, ValueError) as error:
        print(f"Agent loop error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
