# sitegen3 — single-task iteration

You are completing **one** task from `docs/TASKS.md` in the `sitegen3` project (a Python static site generator). A bash loop will reinvoke you with this same prompt until every task is marked done, so your job is to advance the queue by exactly one task per run.

## Step 1 — Required reading (every iteration, no shortcuts)

Read these in full before doing anything else. They are the authoritative references; this prompt only summarizes the protocol.

1. `docs/SPEC.md` — what to build (functional spec).
2. `docs/ARCHITECTURE.md` — how it's structured (module contracts).
3. `docs/TASKS.md` — the work queue. Pay particular attention to the "How to use this document" and "Global conventions" sections at the top.

## Step 2 — Find the next task

Scan `docs/TASKS.md` for the first `## Task N — ...` heading whose section does **not** contain a `**Status:** DONE` line. That section is your task for this iteration.

If every task already has `**Status:** DONE`, write `ALL TASKS DONE` to stdout and stop without making any changes.

## Step 3 — Implement the task

Implement exactly what the task specifies. In particular:

- Create the files listed under **Files to create** with the public interfaces shown verbatim — later tasks import these signatures and will break if you rename or reshape them.
- Implement the **Tests** described, not a superset and not a subset.
- Honour every item in the eight **Global conventions** at the top of `TASKS.md`: Python 3.12+, modern typing (`X | None`, `list[Post]`), no `from __future__ import annotations`, real-file tests via `tmp_path` (no mocking of stdlib I/O), type annotations on every function (including helpers and fixtures), `Any` only at dynamic boundaries, docstrings only when the *why* is non-obvious.
- Use Poetry for any dependency management (`poetry add`, `poetry install`).

## Step 4 — Verification gate

Run every command listed in the task's **Verification** section. The standard four-command gate is:

```
ruff format .
ruff check --fix .
pyright
pytest
```

Some tasks add extras (e.g. Task 1 also runs `poetry build` plus a wheel-manifest grep). Run those too.

If a command fails, fix the underlying cause and rerun. Do **not**:

- skip hooks (no `--no-verify`),
- weaken types (no stray `# type: ignore` or unjustified `Any`),
- comment out, `xfail`, or skip failing tests,
- mark the task done with anything red.

If you can't get the gate green after a reasonable repair attempt, stop without marking the task done and without committing. Print the failing command's output. The loop will retry from a clean state next iteration.

## Step 5 — Mark the task done

Only after every verification command for this task exits 0:

- Append a single new line `**Status:** DONE` to `docs/TASKS.md`, immediately after the `**Done when.**` paragraph of the task you just completed.
- Do not modify any other task's content. Do not reflow, reformat, or re-order anything else in `TASKS.md`.

## Step 6 — Commit

Create exactly one commit:

- `git add` only the files this task touched, including the `**Status:** DONE` edit to `docs/TASKS.md`.
- Commit message: `task N: <task title>` (e.g. `task 3: Slug normalization`).
- Do not push. Do not amend prior commits. Do not skip hooks.

Then stop. The loop will reinvoke you for the next task.

## Hard rules

- **Read-only docs:** never modify `docs/SPEC.md`, `docs/ARCHITECTURE.md`, or `docs/TODO.md`.
- **TASKS.md is append-only for you:** the only edit you may make to it is the single `**Status:** DONE` line for the task you completed this iteration.
- **No skipping ahead:** tasks are ordered by dependency. Do the first unmarked task even if a later one looks easier or more interesting.
- **Out of scope per `docs/TODO.md`:** RSS feed, `--watch` / live reload, sitemap. Never implement these, even partially, even speculatively.
- **One task per run:** after committing one task, stop. Do not start the next one in the same iteration.
- **No partial credit:** if you can't finish the task to a green gate, leave `TASKS.md` untouched and do not commit. A half-finished task with a `DONE` marker poisons the queue.
