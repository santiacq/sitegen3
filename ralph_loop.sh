#!/usr/bin/env bash
#
# ralph_loop.sh — drive Claude through docs/TASKS.md, one task per iteration.
#
# Each iteration runs `claude --print --dangerously-skip-permissions` with the
# contents of `ralph_prompt.md` as input. The prompt instructs Claude to find
# the first task in docs/TASKS.md without a `**Status:** DONE` marker, complete
# it, run the verification gate, mark it done, and commit. The loop exits when
# every task carries the marker, when claude itself exits non-zero, or when the
# iteration cap is reached.
#
# `--dangerously-skip-permissions` is intentional: the loop is unattended and
# all work happens inside this single project directory.
#
# Usage:
#     ./ralph_loop.sh              # run until all tasks done or cap hit
#     MAX_ITERS=1 ./ralph_loop.sh  # one iteration only (smoke-test)
#     ./ralph_loop.sh --dirty      # don't require a clean working tree
#
# Logs append to ./ralph.log.

set -u

trap 'echo; echo "interrupted"; exit 130' INT

cd "$(dirname "$0")"

DIRTY_OK=0
if [[ "${1:-}" == "--dirty" ]]; then
    DIRTY_OK=1
fi

MAX_ITERS="${MAX_ITERS:-50}"
PROMPT_FILE="ralph_prompt.md"
TASKS_FILE="docs/TASKS.md"
LOG_FILE="ralph.log"

if ! command -v claude >/dev/null 2>&1; then
    echo "error: claude not found on PATH" >&2
    exit 1
fi

if [[ ! -f "$PROMPT_FILE" ]]; then
    echo "error: $PROMPT_FILE missing" >&2
    exit 1
fi

if [[ ! -f "$TASKS_FILE" ]]; then
    echo "error: $TASKS_FILE missing" >&2
    exit 1
fi

if [[ $DIRTY_OK -eq 0 ]] && [[ -n "$(git status --porcelain)" ]]; then
    echo "error: working tree not clean — commit/stash first or pass --dirty" >&2
    git status --short
    exit 1
fi

TOTAL=$(grep -c '^## Task ' "$TASKS_FILE")
if [[ "$TOTAL" -eq 0 ]]; then
    echo "error: no '## Task ' headings found in $TASKS_FILE" >&2
    exit 1
fi

echo "ralph: $TOTAL tasks total, max $MAX_ITERS iterations" | tee -a "$LOG_FILE"

for ((i = 1; i <= MAX_ITERS; i++)); do
    DONE=$(grep -c '^\*\*Status:\*\* DONE' "$TASKS_FILE")
    if [[ "$DONE" -ge "$TOTAL" ]]; then
        echo "ralph: all $TOTAL tasks marked DONE — stopping" | tee -a "$LOG_FILE"
        exit 0
    fi

    echo | tee -a "$LOG_FILE"
    echo "=== ralph iteration $i / $MAX_ITERS ($DONE / $TOTAL tasks done) ===" | tee -a "$LOG_FILE"
    echo "started at $(date -Iseconds)" | tee -a "$LOG_FILE"

    set +e
    claude --print --dangerously-skip-permissions --add-dir . < "$PROMPT_FILE" 2>&1 | tee -a "$LOG_FILE"
    rc=${PIPESTATUS[0]}
    set -e

    if [[ "$rc" -ne 0 ]]; then
        echo "ralph: claude exited $rc — stopping" | tee -a "$LOG_FILE"
        exit 1
    fi
done

echo "ralph: hit MAX_ITERS=$MAX_ITERS without finishing — stopping" | tee -a "$LOG_FILE"
DONE=$(grep -c '^\*\*Status:\*\* DONE' "$TASKS_FILE")
echo "ralph: $DONE / $TOTAL tasks done" | tee -a "$LOG_FILE"
exit 1
