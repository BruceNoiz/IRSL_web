#!/usr/bin/env bash

set -u

MAX_ROUNDS=3
AGENT_TIMEOUT_SECONDS=${AGENT_TIMEOUT_SECONDS:-1800}
CLAUDE_MAX_TURNS=${CLAUDE_MAX_TURNS-30}
REVIEW_ONLY=0

fail() {
    echo "Error: $*" >&2
    exit 1
}

if [ "$#" -eq 1 ] && [ "$1" = "--review-only" ]; then
    REVIEW_ONLY=1
    MAX_ROUNDS=1
elif [ "$#" -ne 0 ]; then
    fail "Usage: bash agent-loop.sh [--review-only]"
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P) || exit 1
cd -- "$SCRIPT_DIR" || exit 1

[[ "$AGENT_TIMEOUT_SECONDS" =~ ^[1-9][0-9]*$ ]] || fail "AGENT_TIMEOUT_SECONDS must be a positive integer."
[[ "$CLAUDE_MAX_TURNS" =~ ^[1-9][0-9]*$ ]] || fail "CLAUDE_MAX_TURNS must be a positive integer."
if [ "$REVIEW_ONLY" -eq 0 ]; then
    command -v codex >/dev/null 2>&1 || fail "Missing command: codex"
fi
for COMMAND in claude git make python3; do
    command -v "$COMMAND" >/dev/null 2>&1 || fail "Missing command: $COMMAND"
done
for FILE in .agent/TASK.md Makefile scripts/agent_loop.py; do
    [ -s "$FILE" ] || fail "Missing or empty file: $FILE"
done
GIT_ROOT=$(git rev-parse --show-toplevel) || fail "Not a Git repository."
[ "$GIT_ROOT" = "$SCRIPT_DIR" ] || fail "The script must be in the Git repository root."

mkdir -p .agent/logs || fail "Cannot create log directory."
LOG_DIR=$(mktemp -d ".agent/logs/run-$(date +%Y%m%dT%H%M%S)-XXXXXX") || fail "Cannot create run directory."
if [ -e .agent/REVIEW.md ]; then
    [ -f .agent/REVIEW.md ] || fail "REVIEW.md is not a regular file."
    cp .agent/REVIEW.md "$LOG_DIR/review-before.md" || fail "Cannot back up the previous review."
fi

run_timed() {
    python3 scripts/agent_loop.py run "$AGENT_TIMEOUT_SECONDS" "$@"
}

echo "================================"
echo " Starting Agent Coding Loop"
echo " Max rounds: $MAX_ROUNDS"
echo " Timeout per command: $AGENT_TIMEOUT_SECONDS seconds"
echo " Claude max turns per review: $CLAUDE_MAX_TURNS"
echo " Logs: $SCRIPT_DIR/$LOG_DIR"
echo "================================"

for ((ROUND=1; ROUND<=MAX_ROUNDS; ROUND++))
do
    echo
    echo "================================"
    echo " ROUND $ROUND"
    echo "================================"

    echo
    if [ "$REVIEW_ONLY" -eq 1 ]; then
        echo "[1/4] Reviewing current working tree; Codex skipped."
        IMPLEMENTATION_CONTEXT="This is a review-only run. No implementation agent was run.
Review the current files and fresh check results; use .agent/REVIEW.md as prior findings if present."
    else
        echo "[1/4] Codex is implementing..."

        CODEX_EXIT=0
        run_timed codex --ask-for-approval never exec \
          --sandbox workspace-write \
          -o "$LOG_DIR/codex-$ROUND.txt" \
          "You are the implementation engineer and frontend designer for IRSL.

Read AGENTS.md, .agent/TASK.md, docs/HARNESS.md and docs/IMPLEMENTATION.md.
The current task and latest user feedback recorded in TASK.md define the scope.
They supersede conflicting historical tasks, old page layouts, deferred-stage notes
and prior APPROVED reviews. Do not wait for a superseded sample-page approval.
Use .agent/REVIEW.md as prior findings if present; address blocking and important
findings that still apply, without restoring requirements superseded by TASK.md.

Before editing, inspect git status and preserve existing user changes. Map each
requested change to its target page, section or referenced image, relevant source
files and acceptance check. Record this brief plan in docs/IMPLEMENTATION.md.
Follow the user's specified content locations and page structure. For local changes,
limit edits to the requested area and necessary shared styles, links and tests;
for a redesign, complete the full scope authorized in the current TASK.md.
If a target cannot be identified from the task and repository, record the exact
ambiguity instead of guessing; continue work that does not depend on it.

For visual work:
- Inspect the existing pages, artifact sources and any supplied visual references.
  Preserve important academic content and original assets; do not invent facts.
- Before changing the layout, save the relevant desktop/mobile baseline views
  under .agent/logs/ and record the design direction: composition, typography,
  spacing, color and image placement. Then implement it, not just a proposal.
- Improve the actual layout and reading hierarchy within TASK.md's constraints.
  Moving content or changing colors alone does not satisfy a requested redesign.
- Render and inspect the changed pages at TASK.md's desktop/mobile viewport sizes,
  including the first screen, long content, navigation, hover and keyboard focus.
  Compare before/after images and correct visible problems before handing off.
- Keep route/anchor links, content mapping, no-JavaScript navigation and BASE_PATH
  support consistent with the requested page structure. Update obsolete layout
  assertions without weakening content, accessibility or regression coverage.
- Provide actual preview routes, screenshot paths and specific design improvements
  in docs/IMPLEMENTATION.md, together with commands, results and limitations.
  Do not use ignored logs as the only handoff. If browser/image tools or permissions
  prevent visual verification, report it as unverified; do not invent evidence.

Rules:
- Work only inside this repository.
- Do not deploy anything.
- Do not push to remote repositories.
- Do not access or modify credentials or secrets.
- Avoid unrelated changes.
- Do not modify .agent/REVIEW.md; it is owned by the reviewer.
- Run make check, git diff --check and any task-specific checks.
- Do not claim tests passed unless you actually ran them.
- Keep the implementation as simple as reasonably possible.
- Do not weaken TASK.md acceptance criteria or treat old approvals as completion.
- This run is unattended. Record unresolved questions or required user confirmation
  in the handoff; never invent the user's approval or bypass an active approval gate.

At the end explain in Traditional Chinese:
1. Which requested page/section changes you completed
2. What design improvements you made, with preview routes and visual evidence
3. What tests you ran and their actual results
4. What remains unresolved, including any pending user visual confirmation." \
          > "$LOG_DIR/codex-$ROUND.stdout.log" \
          2> "$LOG_DIR/codex-$ROUND.stderr.log" || CODEX_EXIT=$?

        if [ $CODEX_EXIT -ne 0 ]; then
            fail "Codex exited $CODEX_EXIT. See $LOG_DIR/codex-$ROUND.stderr.log"
        fi
        IMPLEMENTATION_CONTEXT="Read $LOG_DIR/codex-$ROUND.txt for the implementation summary."
    fi

    echo
    echo "[2/4] Running make check..."

    CHECK_EXIT=0
    : > "$LOG_DIR/check-$ROUND.log" || fail "Cannot create check log."
    run_timed make check > "$LOG_DIR/check-$ROUND.log" 2>&1 || CHECK_EXIT=$?
    [ "$CHECK_EXIT" -ne 124 ] || fail "Checks timed out. See $LOG_DIR/check-$ROUND.log"
    echo "Check exit code: $CHECK_EXIT"

    echo
    echo "[3/4] Saving all changes..."

    git -c core.quotePath=false status --short --untracked-files=all \
      > "$LOG_DIR/status-$ROUND.txt" || fail "Cannot save Git status."
    git diff --binary --no-ext-diff --no-textconv -- . ':(exclude).agent/logs' \
      > "$LOG_DIR/diff-$ROUND.patch" || fail "Cannot save unstaged changes."
    git diff --cached --binary --no-ext-diff --no-textconv -- . ':(exclude).agent/logs' \
      > "$LOG_DIR/staged-$ROUND.patch" || fail "Cannot save staged changes."
    git ls-files --others --exclude-standard -z -- . ':(exclude).agent/logs' \
      > "$LOG_DIR/untracked-$ROUND.files" || fail "Cannot list untracked files."
    exec 3> "$LOG_DIR/untracked-$ROUND.patch" || fail "Cannot create untracked patch."
    while IFS= read -r -d '' FILE; do
        DIFF_EXIT=0
        git diff --no-index --binary --no-ext-diff --no-textconv -- /dev/null "$FILE" >&3 || DIFF_EXIT=$?
        [ "$DIFF_EXIT" -le 1 ] || fail "Cannot save untracked file: $FILE"
    done < "$LOG_DIR/untracked-$ROUND.files"
    exec 3>&-

    echo
    echo "[4/4] Claude is reviewing..."

    CLAUDE_EXIT=0
    run_timed claude -p \
      --permission-mode plan \
      --max-turns "$CLAUDE_MAX_TURNS" \
      --output-format json \
      "You are the independent implementation and visual-design reviewer for IRSL.

Read AGENTS.md, .agent/TASK.md, docs/HARNESS.md and docs/IMPLEMENTATION.md.
Review against the current task and latest user feedback recorded in TASK.md.
They supersede conflicting historical tasks, old page layouts, deferred-stage notes
and prior APPROVED reviews. A deferral applies only if the current task retains it;
do not revive a superseded sample-page approval gate or approve only an old stage.

Inspect the current repository, including staged, unstaged and untracked files.
Read $LOG_DIR/status-$ROUND.txt and the diff-$ROUND.patch,
staged-$ROUND.patch and untracked-$ROUND.patch files in $LOG_DIR.
Inspect every untracked file listed in the status; do not treat an empty git diff
as evidence that no work was done. Inspect binary assets directly as needed.
$IMPLEMENTATION_CONTEXT
Read $LOG_DIR/check-$ROUND.log.
Check exit code: $CHECK_EXIT
If this code is not 0, you MUST return CHANGES_REQUESTED and describe the failed checks.

Batch related file reads where practical, and reserve turns for the final review.

Check:
- correctness
- bugs
- security problems
- edge cases
- missing tests
- regressions
- unnecessary complexity
- whether each requested change is at the specified page/section, with the required
  content preserved, and whether unrelated areas were unnecessarily changed
- whether the current implementation and review criteria in TASK.md are satisfied

For visual work, open and inspect the actual desktop/mobile screenshots or rendered
pages for this implementation, including the first screen and long-page sections.
Compare the baseline and final views required by TASK.md. Evaluate composition,
typography, spacing, color, image placement, readability, responsive behavior and
navigation/focus states against the requested design direction. Check content
placement, route/anchor links, source completeness and BASE_PATH compatibility.
Passing tests, source CSS and the implementer's description alone are not visual
evidence. Missing required views or inability to inspect them must be reported as
an important verification gap with CHANGES_REQUESTED, not silently approved.

Make findings actionable: name the page/section, viewport or file, observed problem,
the TASK.md requirement it violates and a concrete acceptance check for the fix.
Tie blocking/important findings to requirements or usability problems; separate
optional aesthetic preferences into Suggestions instead of demanding a new redesign.
In Explanation, state which requirements and visual evidence you actually checked,
and distinguish implementation/reviewer acceptance from user visual confirmation.
If only the user's final visual confirmation remains and TASK.md allows handoff
pending that confirmation, record it explicitly without claiming the whole task
or user acceptance is complete. Never invent user approval.

Do NOT modify project files, including .agent/REVIEW.md. Output the review only.
Do NOT ask the user questions.
Keep progress updates out of the final review; do not add a preamble or code fence.

Your FIRST LINE must be exactly:

APPROVED

or:

CHANGES_REQUESTED

Use APPROVED only when the current implementation/review criteria are met,
the required evidence has been inspected and there are no blocking or important issues.

After the first line use these four sections exactly once, in this order.
Every section must contain text; write None when no issues apply.
Write the findings in Traditional Chinese; keep the status and headings exactly as shown.

## Blocking Issues

## Important Issues

## Suggestions

## Explanation" \
      > "$LOG_DIR/claude-$ROUND.stdout.json" \
      2> "$LOG_DIR/claude-$ROUND.stderr.log" || CLAUDE_EXIT=$?

    if [ $CLAUDE_EXIT -ne 0 ]; then
        echo "Claude reviewer exited $CLAUDE_EXIT. Last lines of stdout and stderr:" >&2
        tail -n 15 "$LOG_DIR/claude-$ROUND.stdout.json" "$LOG_DIR/claude-$ROUND.stderr.log" >&2
        if grep -Fq -e 'Error: Reached max turns' -e 'error_max_turns' "$LOG_DIR/claude-$ROUND.stdout.json" "$LOG_DIR/claude-$ROUND.stderr.log"; then
            echo "Review turn limit reached. Increase CLAUDE_MAX_TURNS (current: $CLAUDE_MAX_TURNS)." >&2
        fi
        fail "Previous review preserved. Retry current files with bash agent-loop.sh --review-only. Full logs: $LOG_DIR/claude-$ROUND.stdout.json and $LOG_DIR/claude-$ROUND.stderr.log"
    fi

    python3 scripts/agent_loop.py extract \
      "$LOG_DIR/claude-$ROUND.stdout.json" "$LOG_DIR/review-$ROUND.md" \
      2> "$LOG_DIR/review-$ROUND.validation.log" || {
        cat "$LOG_DIR/review-$ROUND.validation.log" >&2
        fail "Review was not extracted. See $LOG_DIR/claude-$ROUND.stdout.json"
    }

    RESULT=$(python3 scripts/agent_loop.py publish \
      "$LOG_DIR/review-$ROUND.md" .agent/REVIEW.md "$CHECK_EXIT" \
      2>> "$LOG_DIR/review-$ROUND.validation.log") || {
        cat "$LOG_DIR/review-$ROUND.validation.log" >&2
        fail "Review was not published. See $LOG_DIR/review-$ROUND.validation.log"
    }

    echo
    echo "Reviewer result: $RESULT"

    if [ "$RESULT" = "APPROVED" ]; then
        echo
        echo "================================"
        echo " REVIEW APPROVED"
        echo " Finished after $ROUND rounds."
        echo "================================"

        exit 0
    fi

    echo
    echo "Changes requested."
    if [ "$REVIEW_ONLY" -eq 1 ]; then
        echo "Review-only run complete. Address .agent/REVIEW.md before running the implementation loop."
        exit 2
    fi
    echo "Returning review to Codex..."
done

echo
echo "================================"
echo " Maximum rounds reached."
echo " Human review required."
echo "================================"

exit 2
