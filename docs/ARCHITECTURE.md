# sitegen3 — Architecture

This document describes the internal structure of `sitegen3`: its modules, data models, build pipeline, and cross-cutting concerns. It is the bridge between [`SPEC.md`](SPEC.md) (what the tool does) and `TASKS.md` (the ordered work to build it).

The architecture favours small, single-purpose modules with explicit data flow. Side effects (filesystem reads/writes, logging) are pushed to the edges; pure transformations (slug normalization, frontmatter parsing, markdown rendering, template application) sit in the middle and are trivially unit-testable. Configuration is passed by argument rather than read from globals, so every function can be tested with a synthesized `Config`.

---

## Source Tree Layout

```
sitegen3/
  pyproject.toml
  README.md
  docs/
    SPEC.md
    ARCHITECTURE.md
    TASKS.md
    TODO.md
  design/                       # Visual reference; not shipped, not read at runtime
    *.html
    style.css
  src/sitegen3/
    __init__.py
    cli.py                      # argparse entry point
    config.py                   # Load and validate sitegen3.toml
    models.py                   # Dataclasses: Config, Link, About, Post, Project
    frontmatter.py              # Split `+++`-delimited TOML frontmatter from body
    slug.py                     # Normalize filenames into URL slugs
    discovery.py                # Walk input dir, return file paths
    loader.py                   # Read one file → assemble one model (or raise LoaderError)
    markdown_renderer.py        # Wrap python-markdown
    templates.py                # Wrap Jinja2 (PackageLoader)
    writer.py                   # Wipe output, write HTML, copy assets/static
    build.py                    # Orchestrate the full build pipeline
    serve.py                    # Wrap http.server
    init_cmd.py                 # Scaffold a new site
    logging_setup.py            # Configure root logger
    templates/                  # Jinja2 templates (shipped with the package)
      base.html.j2
      about.html.j2
      posts.html.j2
      post.html.j2
      projects.html.j2
      project.html.j2
    scaffold/                   # Files copied by `sitegen3 init`
      sitegen3.toml
      static/style.css
      content/about.md
      content/posts/hello-world.md
      content/projects/sample-project.md
  tests/
    conftest.py                 # Shared fixtures (sample Config, markdown helpers)
    fixtures/
      sample_site/              # Minimal complete site tree for end-to-end tests
    test_cli.py
    test_config.py
    test_frontmatter.py
    test_slug.py
    test_markdown_renderer.py
    test_templates.py
    test_discovery.py
    test_loader.py
    test_writer.py
    test_build.py
    test_init_cmd.py
```

Notes:

- The `src/` layout ensures the package is only importable when installed (catches accidental relative imports during development).
- Jinja2 templates and `init` scaffold files live **inside the package** so they ship with the wheel — loaded via `jinja2.PackageLoader` and `importlib.resources` respectively.
- `design/` is kept at the repo root as a reference and is never imported by runtime code.

---

## Data Models

All models are stdlib `@dataclass(frozen=True)` definitions in `models.py`. They carry no logic and are passed by value through the pipeline.

```python
@dataclass(frozen=True)
class Config:
    site_title: str
    site_footer: str | None
    root_dir: Path         # Directory containing sitegen3.toml
    input_dir: Path        # Absolute, resolved from root_dir + paths.input
    output_dir: Path       # Absolute, resolved from root_dir + paths.output

@dataclass(frozen=True)
class Link:
    label: str
    url: str

@dataclass(frozen=True)
class About:
    body_html: str
    links: list[Link]

@dataclass(frozen=True)
class Post:
    slug: str
    title: str
    created_at: date
    updated_at: date | None
    body_html: str
    source_path: Path      # Used in log messages

@dataclass(frozen=True)
class Project:
    slug: str
    title: str
    description: str
    created_at: date
    updated_at: date | None
    tags: list[str]
    links: list[Link]
    body_html: str
    source_path: Path
```

The render context passed to Jinja is constructed inline (a plain `dict`) at the moment a template is rendered. We deliberately do not introduce a `RenderContext` wrapper — it would be a layer with no behaviour.

---

## Modules

Each module is listed with its **responsibility** and **public interface**. Anything not listed is private.

### `cli.py`

Responsibility: parse command-line arguments using stdlib `argparse` and dispatch to `build`, `serve`, or `init_cmd`. Builds a top-level parser with three subparsers; each subparser has its own `dir` positional and (for `serve`) a `--port` option. Calls `logging_setup.configure_logging()` once on entry. No business logic. Argparse's default help formatting differs slightly from the SPEC examples — the implementation should set program name, description, and help strings to match as closely as practical.

```python
def main() -> None: ...        # Console entry point declared in pyproject.toml
```

### `config.py`

Responsibility: load and validate `sitegen3.toml`. Resolves `paths.input` and `paths.output` to absolute paths against the site root. Raises a fatal exception if the file is missing or required fields are absent.

```python
def load_config(root_dir: Path) -> Config
```

### `models.py`

Responsibility: define the dataclasses listed above. No logic, no I/O.

### `frontmatter.py`

Responsibility: split a Markdown file into a frontmatter dict and a body string. Implements the rules in SPEC §Frontmatter Format (no delimiter → empty dict + full text as body; opening `+++` without closing → exception). No field validation — that lives in `loader.py`.

```python
def parse(text: str) -> tuple[dict, str]
```

### `slug.py`

Responsibility: normalize a filename stem into a URL slug per the SPEC's 5-step pipeline.

```python
def slugify(name: str) -> str
```

### `discovery.py`

Responsibility: walk the input directory and return paths to content files. **Does not open or read any files.** Returns empty lists when `posts/` or `projects/` subdirectories are absent. Raises a fatal exception only when `about.md` is missing.

```python
def find_about(input_dir: Path) -> Path           # Fatal if missing
def find_posts(input_dir: Path) -> list[Path]
def find_projects(input_dir: Path) -> list[Path]
```

### `loader.py`

Responsibility: turn a single file path into a single model. For one path, the loader reads the file, calls `frontmatter.parse`, validates required fields, calls `markdown_renderer.render`, applies `slug.slugify`, and constructs a `Post` / `Project` / `About`. Any per-file failure (malformed TOML, missing required field, etc.) is wrapped as `LoaderError` and raised; it is never caught here.

```python
def load_about(path: Path) -> About
def load_post(path: Path) -> Post
def load_project(path: Path) -> Project

class LoaderError(Exception): ...
```

**Why discovery and loader are separate.** SPEC §Per-page resilience requires that one broken file (e.g. `posts/broken.md` with malformed TOML) must not abort the whole build. That means the per-file try/except has to live somewhere outside the file-reading code — otherwise it is impossible to know which file caused the failure or to continue with the next one. The split puts that loop in `build.py`:

```python
for path in discovery.find_posts(input_dir):
    try:
        posts.append(loader.load_post(path))
    except LoaderError as e:
        log.warning("skipping %s: %s", path, e)
        skipped += 1
```

`discovery` answers "which files exist?" with no failure modes for individual files. `loader` answers "what does this file mean?" with at most one failure per call. `build.py` decides what to do when a load fails. Each module has one job.

### `markdown_renderer.py`

Responsibility: wrap `python-markdown` with the `fenced_code` and `tables` extensions. Stateless from the caller's perspective; internally may keep a module-level `Markdown` instance and call `.reset()` between renders.

```python
def render(text: str) -> str
```

### `templates.py`

Responsibility: own the Jinja2 `Environment` (configured with `PackageLoader("sitegen3", "templates")` and autoescape on). Provides a single render entry point. The `Environment` is cached at module level for performance; it does not depend on `Config`.

```python
def render_template(name: str, context: dict) -> str
```

### `writer.py`

Responsibility: all output-side filesystem operations. Wipes the output directory, writes HTML files at their URL paths (`/posts/foo/` → `posts/foo/index.html`), copies asset and static trees.

```python
def wipe_output(output_dir: Path) -> None
def write_page(output_dir: Path, url_path: str, html: str) -> None
def copy_assets(input_dir: Path, output_dir: Path) -> None
def copy_static(root_dir: Path, output_dir: Path) -> None
```

### `build.py`

Responsibility: orchestrate the full pipeline. Owns the per-page try/except that turns `LoaderError` into a logged warning and a skip. Sorts posts and projects newest-first by `created_at`, with slug as a tiebreaker.

```python
def build(root_dir: Path) -> None
```

### `serve.py`

Responsibility: serve `config.output_dir` over HTTP using stdlib `http.server`. No watching, no live reload (see TODO).

```python
def serve(root_dir: Path, port: int) -> None
```

### `init_cmd.py`

Responsibility: scaffold a new site. Refuses to run if `sitegen3.toml` already exists in the target directory. Copies files from `src/sitegen3/scaffold/` to the target via `importlib.resources`.

```python
def init(root_dir: Path) -> None
```

### `logging_setup.py`

Responsibility: configure the root logger to write to stderr at `INFO` (or `DEBUG` if a future `--verbose` flag is added). Called once at CLI entry.

```python
def configure_logging() -> None
```

---

## Pipeline / Data Flow

The `build` command runs the following stages in order. Each arrow is a function call; each box is a module.

```
                         ┌──────────────┐
  sitegen3.toml  ──────► │  config      │ ──► Config
                         └──────────────┘

                         ┌──────────────┐
  Config.output_dir ───► │  writer      │  (wipe_output)
                         └──────────────┘

                         ┌──────────────┐
  Config.input_dir ────► │  discovery   │ ──► Path, [Path], [Path]
                         └──────────────┘
                                │
                                ▼
                         ┌──────────────┐  per file:
                         │  loader      │  ──► frontmatter.parse
                         │              │  ──► markdown_renderer.render
                         │              │  ──► slug.slugify
                         └──────────────┘
                                │
                                ▼
                         About, [Post], [Project]
                                │
                                ▼
                         ┌──────────────┐  for each page:
                         │  templates   │  ──► render_template(name, ctx)
                         └──────────────┘
                                │
                                ▼
                              HTML
                                │
                                ▼
                         ┌──────────────┐
                         │  writer      │  (write_page)
                         └──────────────┘

                         ┌──────────────┐
                         │  writer      │  (copy_assets, copy_static)
                         └──────────────┘
                                │
                                ▼
                         ┌──────────────┐
                         │  build       │  (log summary: rendered, skipped)
                         └──────────────┘
```

Stage ownership:

| Stage | Owner module |
|---|---|
| Load and validate config | `config` |
| Wipe output dir | `writer` |
| Discover content paths | `discovery` |
| Read + parse + render each file | `loader` (uses `frontmatter`, `markdown_renderer`, `slug`) |
| Filter drafts | `loader` (returns `None` for drafts, filtered in `build`) |
| Sort posts/projects | `build` (newest-first by `created_at`, then by slug) |
| Render templates | `templates` |
| Write HTML files | `writer` |
| Copy assets and static | `writer` |
| Log summary | `build` |

Per-page error handling lives in `build.py`: each `loader.load_*` call is wrapped in try/except, `LoaderError` is logged at `WARNING` with the source path, and a local `skipped` counter is incremented for the final summary log line.

---

## Module Dependency Graph

```
cli ──► build ──► config
        │
        ├──► discovery
        │
        ├──► loader ──► frontmatter
        │              ├──► markdown_renderer
        │              ├──► slug
        │              └──► models
        │
        ├──► templates ──► models
        │
        ├──► writer
        │
        └──► models

cli ──► serve ──► config
cli ──► init_cmd
cli ──► logging_setup

config  depends on models
models  has no internal dependencies
```

Implementation order — at each step the project compiles and previously built modules can be exercised in isolation:

1. `models`, `slug`, `frontmatter`, `markdown_renderer` — pure, no internal deps.
2. `config`, `logging_setup`.
3. `templates` (with the Jinja templates themselves).
4. `discovery`, `loader`.
5. `writer`.
6. `build` — pulls everything together.
7. `serve`, `init_cmd`.
8. `cli` — wires the subcommands and registers the entry point.

This ordering becomes the spine of `TASKS.md`.

---

## Cross-Cutting Concerns

### Logging

All modules use `logging.getLogger(__name__)`. No module configures handlers — that is `logging_setup.configure_logging()`'s job, called once from `cli.py`. Levels follow SPEC §Error Handling: `INFO` for build start/end and major stages, `DEBUG` for per-page success, `WARNING` for skipped pages, `ERROR` for fatal exits. Centralizing handler configuration lets us add a `--verbose` flag later without touching every module.

### Error Policy

Two tiers, matching SPEC §Per-page resilience:

- **Fatal**: missing `sitegen3.toml`, missing input directory, missing `about.md`, missing required config fields. Raised as exceptions from `config.load_config` and `discovery.find_about`. Caught at the `cli` boundary, logged at `ERROR`, exit code 1.
- **Per-page**: any failure inside `loader.load_post` / `loader.load_project` (malformed TOML, missing required frontmatter, template error during that page's render). Wrapped as `LoaderError` and caught in `build.py`, which logs a `WARNING` with the source path and reason and continues.

`about.md` failures are treated as **fatal** — there is no site without an about page.

### Config Threading

`Config` is loaded once (in `build.build`, `serve.serve`, or `init_cmd.init` as appropriate) and passed explicitly as a function argument to anything that needs it. No module-level globals, no singleton, no implicit context. This keeps every function trivially testable with a synthesized `Config`.

The only module-level state in the codebase is the cached Jinja `Environment` in `templates.py` and the per-module loggers — neither depends on configuration.

---

## Development & Tooling

The choices below apply to every module in the codebase, including tests. Configuration for each tool lives in `pyproject.toml`.

### Python Version

The project targets `>=3.12`. Modern syntax is used throughout:

- `X | None` instead of `typing.Optional[X]`.
- Built-in generics (`list[Post]`, `dict[str, Any]`) instead of `typing.List` / `typing.Dict`.
- `from __future__ import annotations` is **not** used — 3.12 is the floor so it is unnecessary, and leaving it off keeps annotations evaluable at runtime for tooling that inspects them.

### Type Hints

All function signatures are fully annotated: every parameter and the return type. This applies to private helpers and test fixtures as well as public module interfaces.

- Pyright runs in **strict** mode. The module interfaces in this document (e.g. `def load_config(root_dir: Path) -> Config`) are already written in this style; strict mode enforces it across the codebase.
- `Any` is a last resort — prefer precise types or narrow generics.
- `dict` payloads passed to Jinja may be typed as `dict[str, Any]` since the template boundary is dynamic; everywhere else, a structured type is preferred.

### Linting & Formatting

`ruff` handles both linting and formatting. No `black`, no `isort`, no `flake8` — ruff subsumes all three.

Enabled rule groups:

| Group | Covers |
|---|---|
| `E`, `F`, `W` | pyflakes + pycodestyle basics |
| `I` | import sorting |
| `B` | flake8-bugbear (common bug patterns) |
| `UP` | pyupgrade (modern syntax enforcement) |
| `SIM` | simplifications |
| `RUF` | ruff-native rules |

`ruff format` is the canonical formatter.

### Docstrings

Docstrings are omitted by default. Add one only where the *why* is non-obvious: a hidden constraint, a subtle invariant, a workaround for a specific bug, or behaviour that would surprise a reader.

Identifier names and the per-module responsibility summaries in this document describe *what* the code does. Comments and docstrings are reserved for *why*.

### Development Commands

The canonical checks a change must pass before being considered done:

```
ruff format .        # format
ruff check --fix .   # lint (auto-fix what can be fixed)
pyright src/         # type check (strict mode)
pytest               # run tests
```

All four must pass. "Tests pass" alone is not sufficient — type errors and lint violations are equally blocking.

---

## Testing

Tests live in `tests/`, mirroring `src/sitegen3/`: one `test_<module>.py` per module that has behaviour worth verifying. Shared fixtures are in `tests/conftest.py`; the end-to-end fixture site lives under `tests/fixtures/sample_site/`.

### Test Categories

Three tiers:

1. **Unit** — pure modules with no I/O (`slug`, `frontmatter`, `markdown_renderer`, `templates`). Fast, exhaustive, parameterized.
2. **Integration** — modules that read or write the filesystem (`config`, `discovery`, `loader`, `writer`, `init_cmd`). Use pytest's `tmp_path` fixture for isolated per-test directories. Write real files; do not mock `open`, `pathlib`, or stdlib I/O.
3. **End-to-end** — `build()` run against a fixture site, with assertions on the resulting output tree, including per-page resilience (a broken post produces a warning and a skip, not a fatal exit).

### Per-Module Coverage

| Module | Tested | Category | What's covered |
|---|---|---|---|
| `cli` | Yes | Smoke (unit) | Invoke `main()` with patched `sys.argv`; confirm each subcommand dispatches to the right function. |
| `config` | Yes | Integration | Load real TOML via `tmp_path`; path resolution; fatal errors on missing file / missing required fields. |
| `models` | No | — | Frozen dataclasses with no logic. |
| `frontmatter` | Yes | Unit | Parametrized: no delimiter, unterminated delimiter, valid TOML, empty frontmatter, body preserved verbatim. |
| `slug` | Yes | Unit | Parametrized across the 5-step pipeline: mixed case, spaces, punctuation, non-ASCII, collapsed/edge hyphens. |
| `discovery` | Yes | Integration | Missing `about.md` raises fatal; empty `posts/` and `projects/` return empty lists; returned paths match files on disk. |
| `loader` | Yes | Integration | Valid files → model; malformed TOML and missing required fields raise `LoaderError`; `draft: true` is handled per SPEC. |
| `markdown_renderer` | Yes | Unit | Smoke: plain text, fenced code block, table. |
| `templates` | Yes | Unit | Behavioural assertion on the escape contract: given `body_html = "<p>hello</p>"` and `title = "<script>alert(1)</script>"`, the rendered output contains a real `<p>hello</p>` (`body_html` passes through `\|safe`) AND an escaped `&lt;script&gt;` (`title` went through autoescape). Guards both directions. |
| `writer` | Yes | Integration | `wipe_output`, `write_page` (URL path → `index.html`), `copy_assets`, `copy_static` on `tmp_path`. |
| `build` | Yes | End-to-end | Fixture site → `build()` → expected output files exist with expected contents. Broken post in the fixture produces a warning and a non-fatal skip. |
| `serve` | No | — | Thin wrapper around `http.server.HTTPServer`; no logic worth testing. |
| `init_cmd` | Yes | Integration | Scaffold into empty `tmp_path`; refuses when `sitegen3.toml` already exists. |
| `logging_setup` | No | — | One-call stdlib wrapper. |

### Fixtures

- `tests/conftest.py` holds shared fixtures: a `sample_config` factory producing a `Config` pointing at `tmp_path`, helpers to write sample posts and projects, and a helper to read output files.
- `tests/fixtures/sample_site/` is a minimal but complete site tree used by the end-to-end build test. It contains exactly: `sitegen3.toml`, `content/about.md`, one valid post, one valid project, **one broken post** (malformed TOML) to exercise per-page resilience, and a `static/style.css`.
- Never mock filesystem APIs. Use `tmp_path` and write real files. Mocks on I/O mask the integration failures these tests exist to catch.

### Conventions

- Test files named `test_<module>.py`; test functions `test_<behaviour>` or `test_<behaviour>_<condition>` where helpful.
- Prefer `pytest.mark.parametrize` over `for` loops for multi-case tests.
- Error cases use `pytest.raises(ExpectedError, match=...)` to pin the message.
- Arrange-Act-Assert structure; one subject-under-test per test function.
- Test fixtures and helpers are fully type-annotated — pyright strict runs over `tests/` too.
- No coverage percentage is prescribed. The per-module table above **is** the target: every "Yes" row has its public interface and documented error modes exercised.

### Running Tests

Tests import `sitegen3` as an installed package. Run `poetry install` once after cloning to put the package on the import path — the editable install picks up subsequent code changes automatically. Reinstall only when `pyproject.toml` dependencies or the console-script entry point change. This is a consequence of the `src/` layout: `pytest` will not find the package without the install step.

Pytest configuration lives in `pyproject.toml` under `[tool.pytest.ini_options]`, alongside the `[tool.ruff]` and `[tool.pyright]` sections. Minimum settings: `testpaths = ["tests"]` and `addopts = "-ra --strict-markers"`.
