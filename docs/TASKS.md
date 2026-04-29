# sitegen3 — Tasks

An ordered work queue for building `sitegen3`. Each task is self-contained and sized to complete — including tests — in a single coding session.

`SPEC.md` (what to build) and `ARCHITECTURE.md` (how it's structured) are the authoritative references. Each task below inlines the essentials so you rarely need to cross-reference, but defer to SPEC/ARCHITECTURE on ambiguity.

---

## How to use this document

- Do the tasks in order. Later tasks depend on earlier ones.
- Each task stands alone: one implementation session, one commit-sized unit, one green test run.
- Match the public interface signatures exactly — later tasks import them.
- Out of scope (see `docs/TODO.md`): RSS feed, `--watch`/live reload, sitemap. Do not implement any of these.

## Global conventions (apply to every task)

1. **Python / tooling floor.** Python 3.12+, Poetry for dependency management, `ruff` (lint + format), `pyright` (strict mode), `pytest`. Use modern typing syntax: `X | None`, built-in generics (`list[Post]`, `dict[str, Any]`). Do **not** use `from __future__ import annotations`.
2. **Error hierarchy.** Fatal errors subclass `SitegenError` directly (or `PageError`'s siblings); per-page errors subclass `PageError`. `cli.py` catches `SitegenError` at the top level. `about.md` failures are fatal, not per-page.
3. **Logging.** Every module uses `logging.getLogger(__name__)`. Handler configuration lives **only** in `logging_setup.py`. No module configures handlers itself.
4. **Config threading.** `Config` is loaded once per command invocation and passed as an explicit argument to anything that needs it. No module-level globals; no singletons. The only module-level state in the codebase is the cached Jinja `Environment` in `templates.py` and per-module loggers.
5. **Tests use real files.** Use `pytest`'s `tmp_path` fixture. Do **not** mock `open`, `pathlib`, or any stdlib I/O. Mocks on filesystem APIs mask the bugs these tests exist to catch.
6. **Docstrings.** Omit by default. Add one only when the *why* is non-obvious. Identifier names describe *what*.
7. **Type annotations.** Every parameter and return type on every function — including private helpers and test fixtures. Avoid `Any` except at dynamic boundaries (Jinja context payloads).
8. **Definition of done.** Before declaring a task complete, all four commands must pass:
   ```
   ruff format .
   ruff check --fix .
   pyright
   pytest
   ```
   New tests added in the task pass. No existing tests regress.

---

## Task 1 — Project bootstrap

**Goal.** Create the Poetry project scaffolding, source tree skeleton, and tool configuration so later tasks have somewhere to land.

**Files to create.**
- `pyproject.toml` (Poetry config + `[tool.ruff]`, `[tool.pyright]`, `[tool.pytest.ini_options]` sections)
- `README.md` (minimal: one-paragraph description + quickstart pointing at `sitegen3 init`/`build`/`serve`)
- `src/sitegen3/__init__.py` (empty)
- `src/sitegen3/templates/` (directory placeholder, e.g. `.gitkeep` — filled in Task 7)
- `src/sitegen3/scaffold/` (directory placeholder — filled in Task 13)
- `tests/conftest.py` (minimal; shared fixtures are added in later tasks as needed)

Do **not** create `tests/__init__.py` — with the `src/` layout and `testpaths = ["tests"]`, `tests/` is a test root, not a package. Adding `__init__.py` forces pytest's `importlib` mode subtleties and can mask import collisions; the standard layout omits it.

**`pyproject.toml` must specify.**
- Project metadata: name `sitegen3`, Python `>=3.12`.
- Runtime dependencies: `jinja2`, `markdown` (python-markdown).
- Dev dependencies: `ruff`, `pyright`, `pytest`.
- `src/` layout (`packages = [{ include = "sitegen3", from = "src" }]` or equivalent).
- Console entry point: `sitegen3 = "sitegen3.cli:main"` (the target exists as a stub in Task 14; OK to define here).
- Include package data so templates and scaffold files ship with the wheel (Jinja via `PackageLoader`, scaffold via `importlib.resources`). Use this exact block:

  ```toml
  [tool.poetry]
  include = [
    "src/sitegen3/templates/**/*",
    "src/sitegen3/scaffold/**/*",
  ]
  ```

  Why this matters: `poetry install` does an editable install, so during development the templates and scaffold trees are reachable from the source tree even when `pyproject.toml` doesn't list them. The bug only surfaces when the wheel is built and installed elsewhere — every test can pass green and the shipped wheel still be broken. The wheel-build smoke check in **Verification** below is what catches a half-correct config.

**`[tool.ruff]`.** Enable rule groups: `E`, `F`, `W`, `I`, `B`, `UP`, `SIM`, `RUF`. `ruff format` is the canonical formatter. Target Python 3.12.

**`[tool.pyright]`.** Strict mode (`typeCheckingMode = "strict"`); `include = ["src", "tests"]` so a bare `pyright` invocation covers both trees.

**`[tool.pytest.ini_options]`.** `testpaths = ["tests"]`, `addopts = "-ra --strict-markers"`.

**Tests.** No behavioural tests in this task. Pytest exits 5 when zero tests are collected, which fails the verification gate — add `tests/test_smoke.py` with `def test_truthy() -> None: assert True` so the gate is green. Delete it once Task 3 lands the first real test.

**Verification.**
```
poetry install
ruff format .
ruff check --fix .
pyright
pytest
poetry build
unzip -l dist/sitegen3-*.whl | grep -E '(templates|scaffold)'
```

The final two commands confirm the templates and scaffold trees actually land in the wheel. If `unzip -l` doesn't show files under `sitegen3/templates/` and `sitegen3/scaffold/`, the package-data config above is wrong — fix it before continuing. (The templates tree is empty until Task 7 and the scaffold tree is empty until Task 13, so right after Task 1 the grep will only match directories — which is enough to confirm the include patterns are honoured. Re-run after Task 13 to confirm content files ship too.)

**Done when.** `poetry install` succeeds. All four checks pass. `python -c "import sitegen3"` works from the project root. `poetry build` produces a wheel whose manifest lists the `templates/` and `scaffold/` paths under `sitegen3/`.
**Status:** DONE

---

## Task 2 — Data models and exception hierarchy

**Goal.** Define all dataclasses and the exception hierarchy used across the package. No logic, no I/O.

**Files to create.**
- `src/sitegen3/models.py`
- `src/sitegen3/exceptions.py`

**`models.py` — responsibility.** Define the dataclasses listed below. All are `@dataclass(frozen=True)`, carry no logic, passed by value through the pipeline. Use `datetime.date` for dates and `pathlib.Path` for paths.

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
    draft: bool
    body_html: str
    source_path: Path      # Used in log messages

@dataclass(frozen=True)
class Project:
    slug: str
    title: str
    description: str
    created_at: date
    updated_at: date | None
    draft: bool
    tags: list[str]
    links: list[Link]
    body_html: str
    source_path: Path
```

**`exceptions.py` — responsibility.** Define the exception hierarchy used by all modules that raise fatal or per-page errors. No logic, no I/O. No imports from elsewhere in the package.

```python
class SitegenError(Exception): ...         # Root; caught in cli.py. Abstract — never raised directly.

class ConfigError(SitegenError): ...       # Fatal: raised by config.py
class DiscoveryError(SitegenError): ...    # Fatal: raised by discovery.py and build.py (slug collisions)
class InitError(SitegenError): ...         # Fatal: raised by init_cmd.py
class ServeError(SitegenError): ...        # Fatal: raised by serve.py

class PageError(SitegenError): ...         # Per-page branch; caught in build.py loops
class LoaderError(PageError): ...          # Raised by loader.py
class RenderError(PageError): ...          # Raised by templates.py (wraps jinja2.TemplateError)
```

**Tests.** None. Both modules are pure declarations with no behaviour (per ARCHITECTURE §Testing).

**Verification.**
```
ruff format .
ruff check --fix .
pyright
pytest
```
Plus: `python -c "from sitegen3.models import Config, Post, Project, About, Link; from sitegen3.exceptions import SitegenError, ConfigError, DiscoveryError, InitError, ServeError, PageError, LoaderError, RenderError"` succeeds.

**Done when.** All dataclasses frozen; all exception classes defined; pyright strict passes.
**Status:** DONE

---

## Task 3 — Slug normalization

**Goal.** Implement the filename-to-URL-slug pipeline.

**Files to create.**
- `src/sitegen3/slug.py`
- `tests/test_slug.py`

**File to delete.**
- `tests/test_smoke.py` (Task 1's placeholder; `test_slug.py` makes it redundant).

**Responsibility (from ARCHITECTURE).** Normalize a filename stem into a URL slug per SPEC's 5-step pipeline.

**Public interface.**
```python
def slugify(name: str) -> str
```

**Key rules (from SPEC §Output Specification).** The 5-step pipeline, in order:
1. Convert to lowercase.
2. Replace spaces with hyphens.
3. Strip any character that is not a lowercase ASCII letter, digit, or hyphen.
4. Collapse consecutive hyphens into a single hyphen.
5. Strip leading and trailing hyphens.

Example: `"My First Post"` → `"my-first-post"`. The input is the filename stem (no `.md` extension — the caller strips that).

**Tests (unit, parametrized).** Cover:
- Mixed case (`"My Post"` → `"my-post"`).
- Multiple spaces (`"hello   world"` → `"hello-world"`).
- Punctuation stripped (`"hello, world!"` → `"hello-world"`).
- Non-ASCII stripped (`"café-ñoño"` → `"caf-oo"` — accented chars removed; verify exact expected value in your test).
- Collapsed hyphens (`"a---b"` → `"a-b"`).
- Leading/trailing hyphens stripped (`"-hello-"` → `"hello"`).
- Already-clean input passes through unchanged (`"my-post"` → `"my-post"`).
- Empty string input → empty string output.
- Pure-punctuation input (`"!!!"`) → empty string output.

Use `pytest.mark.parametrize` over a `for` loop.

**Verification.** The four-command gate (see Global Conventions §8).

**Done when.** `slugify` exists, handles all parametrized cases, pyright strict passes, tests green.

---

## Task 4 — Frontmatter splitter

**Goal.** Split a Markdown file into a frontmatter `dict` and a body `str`, per the `+++`-delimited TOML format.

**Files to create.**
- `src/sitegen3/frontmatter.py`
- `tests/test_frontmatter.py`

**Responsibility (from ARCHITECTURE).** Split a Markdown file into a frontmatter dict and a body string. No field validation — that lives in `loader.py`. Deliberately raises stdlib `ValueError` (**not** `LoaderError`); `frontmatter` is a generic splitter with no knowledge of sitegen3's error hierarchy. The caller in `loader.py` wraps `ValueError` as `LoaderError` via `raise ... from e`.

**Public interface.**
```python
from typing import Any

def parse(text: str) -> tuple[dict[str, Any], str]
```

**Key rules (from SPEC §Frontmatter Format).**
- Delimiter is `+++` on its own line (opening and closing).
- The opening delimiter is recognized **only** when the file's first line is exactly `+++` (no leading/trailing whitespace, no characters before or after). If the first line is anything else, the file has no frontmatter — return `({}, <full text>)` even if `+++` appears elsewhere in the body.
- The closing delimiter is recognized **only** when a later line is exactly `+++` (same rule as opening: no leading/trailing whitespace, no characters before or after). This mirrors the opening rule and avoids ambiguity around trailing carriage returns or Windows line endings.
- If the first line is `+++` and no later line is exactly `+++`, raise `ValueError`.
- The body starts at the first character of the line **following** the closing `+++` line. Trailing whitespace and newlines from the source file are preserved verbatim (no `.strip()`, no special-casing of a blank line between the closing delimiter and the body).
- Frontmatter body between the delimiters is TOML; parse with `tomllib` from the stdlib.
- Raw HTML inside the Markdown body is left untouched (no sanitization — the frontmatter module doesn't touch the body content beyond splitting).
- Unknown keys in frontmatter are silently ignored at parse time (natural stdlib TOML behaviour; validation lives in `loader`).

**Tests (unit, parametrized where natural).** Cover:
- No delimiter at all → empty dict, body equals full input.
- First line is not `+++` but body contains `+++` later → empty dict, body equals full input (no frontmatter recognized).
- First line is `+++`, no closing `+++` anywhere → `ValueError` (`pytest.raises(ValueError, match=...)`).
- Valid frontmatter + body → dict parsed, body string preserved exactly. Pin the trailing-newline rule with this assertion:
  ```python
  def test_body_preserves_trailing_newline() -> None:
      text = "+++\ntitle = \"X\"\n+++\nHello\n"
      fm, body = parse(text)
      assert body == "Hello\n"
  ```
- Empty frontmatter block (`+++\n+++\n<body>`) → empty dict, body returned.
- Body that itself contains `+++` lines after the closing delimiter is **not** re-split — only the first opening + first closing count.
- Body preserved verbatim including leading whitespace and embedded HTML.

**Verification.** The four-command gate.

**Done when.** All parametrized cases pass; `ValueError` raised on unterminated frontmatter; body preservation is exact.

---

## Task 5 — Markdown renderer wrapper

**Goal.** Wrap `python-markdown` behind a single function so callers don't depend on the library directly.

**Files to create.**
- `src/sitegen3/markdown_renderer.py`
- `tests/test_markdown_renderer.py`

**Responsibility (from ARCHITECTURE).** Wrap `python-markdown` with the `fenced_code` and `tables` extensions. Stateless from the caller's perspective; internally may keep a module-level `Markdown` instance and call `.reset()` between renders for performance.

**Public interface.**
```python
def render(text: str) -> str
```

**Key rules.**
- Enable **only** the `fenced_code` and `tables` extensions. No syntax highlighting, no TOC, no footnotes — SPEC is explicit about the extension list.
- Raw HTML in the input passes through to the output (authors are trusted; no sanitization).
- No logging inside `render` — it's a hot path and has no failure modes worth reporting.

**Tests (unit smoke).** Cover:
- Plain paragraph: `"Hello **world**"` → output contains `<p>Hello <strong>world</strong></p>`.
- Fenced code block: triple-backtick input renders to `<pre><code>...</code></pre>`.
- Table renders to `<table>...</table>` (headers, body row).
- Raw HTML in input appears in output (e.g., input `"<div class=\"x\">hi</div>"` → output contains `<div class="x">hi</div>`).

Exact HTML byte-equality is brittle; assert on substring presence instead.

**Verification.** The four-command gate.

**Done when.** `render` returns HTML with the two extensions active, smoke tests pass.

---

## Task 6 — Config loader and logging setup

**Goal.** Load/validate `sitegen3.toml` into a `Config`, and configure the root logger for CLI entry.

**Files to create.**
- `src/sitegen3/config.py`
- `src/sitegen3/logging_setup.py`
- `tests/test_config.py`

**`config.py` — responsibility (from ARCHITECTURE).** Load and validate `sitegen3.toml`. Resolve `paths.input` and `paths.output` to absolute paths against the site root; verify `paths.input` exists on disk. Raise `ConfigError` on missing file, absent required fields, or missing input directory. The output directory is **not** checked here — `writer.wipe_output` will create it.

**Public interface.**
```python
from pathlib import Path
from sitegen3.models import Config

def load_config(root_dir: Path) -> Config
```

**Key rules (from SPEC §Configuration).**
- Resolve `root_dir` to an absolute path at the top of `load_config` (`root_dir = root_dir.resolve()`) so log lines and error messages don't display a literal `.` when the CLI is invoked without a `DIR` argument.
- File location: `<root_dir>/sitegen3.toml`. Missing file → `ConfigError`.
- `[site]` table:
  - `title` (string, **required**) → `Config.site_title`. Missing → `ConfigError`.
  - `footer` (string, optional) → `Config.site_footer` (may be `None`).
- `[paths]` table (optional):
  - `input` (string, optional, default `"content"`) → resolved absolute via `(root_dir / value).resolve()`.
  - `output` (string, optional, default `"public"`) → resolved absolute via `(root_dir / value).resolve()`.
- If `input_dir` does not exist on disk → `ConfigError`.
- Unknown keys are silently ignored (standard `tomllib` behaviour).

Parse with stdlib `tomllib` (binary read mode: `path.open("rb")`).

**`logging_setup.py` — responsibility.** Configure the root logger to write to stderr at `INFO`. Called once from `cli.py` on entry. No tests required (one-call stdlib wrapper).

**Public interface.**
```python
def configure_logging() -> None
```

**Implementation note.** Use `logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(levelname)s: %(message)s")`. `basicConfig` is naturally idempotent (no-op when handlers already exist on the root logger), so calling it twice in one process is safe.

**Tests (integration, for `config.py` only).** Use `tmp_path`:
- Happy path: write a valid `sitegen3.toml`, create `content/` directory, call `load_config(tmp_path)`, assert the returned `Config` fields — absolute paths, title, footer.
- Defaults: omit `[paths]`, confirm defaults (`content`, `public`) are resolved. Also create `tmp_path / "content"` first, since `load_config` checks input-dir existence and would otherwise raise.
- Missing `sitegen3.toml` → `ConfigError`.
- Missing `site.title` → `ConfigError`.
- Missing input directory on disk → `ConfigError`.
- Unknown keys ignored (don't raise).

Use `pytest.raises(ConfigError, match=...)` with messages that name the problem so fatal-exit diagnostics are useful.

**Verification.** The four-command gate.

**Done when.** `load_config` returns a `Config` for valid inputs and raises `ConfigError` with informative messages for every invalid case above.

---

## Task 7 — Jinja templates, engine wrapper, and stylesheet

**Goal.** Create all six Jinja templates, the `templates.py` wrapper that owns the Jinja `Environment`, and the scaffold `style.css` that ships with new sites.

**Files to create.**
- `src/sitegen3/templates.py`
- `src/sitegen3/templates/base.html.j2`
- `src/sitegen3/templates/about.html.j2`
- `src/sitegen3/templates/posts.html.j2`
- `src/sitegen3/templates/post.html.j2`
- `src/sitegen3/templates/projects.html.j2`
- `src/sitegen3/templates/project.html.j2`
- `src/sitegen3/scaffold/static/style.css`
- `tests/test_templates.py`

### `templates.py` — responsibility

Own the Jinja2 `Environment`, configured with:

```python
from jinja2 import Environment, PackageLoader, select_autoescape

_env = Environment(
    loader=PackageLoader("sitegen3", "templates"),
    autoescape=select_autoescape(enabled_extensions=("html", "html.j2")),
)
```

The explicit `enabled_extensions` list is **required** because Jinja's default autoescape only covers `.html`/`.htm`, and our templates use the compound `.html.j2` suffix. Without the override, every template would render unescaped — a latent XSS-class bug. The list is restricted to `("html", "html.j2")` rather than including a bare `"j2"`: that would autoescape any `.j2` file, including a hypothetical `email.txt.j2` where autoescape would mangle output.

Provide a single render function. Wrap `jinja2.TemplateError` as `RenderError` so callers never need to import `jinja2` for error handling.

**Public interface.**
```python
from typing import Any

def render_template(name: str, context: dict[str, Any]) -> str
```

Cache `_env` at module level (import time). It does not depend on `Config`.

### Template contracts

Templates use `base.html.j2` via `{% extends %}`. The render context is a plain `dict` built inline at the call site (no `RenderContext` wrapper).

**`base.html.j2` — page shell.** Mirrors the structure of `design/index.html`: `<html lang="en">`, `<head>` containing `<meta charset>`, `<meta viewport>`, `<title>{{ page_title }}</title>`, and `<link rel="stylesheet" href="/style.css">`; `<body>` containing the `<nav>` (with `class="active"` applied to the matching link based on `{{ active }}`), then `<main>{% block content %}{% endblock %}</main>` (the `<main>` landmark is owned by the base — child templates do **not** emit their own), then the conditional `{% if site_footer %}<footer><p>{{ site_footer }}</p></footer>{% endif %}`. Every other template `{% extends "base.html.j2" %}` and overrides `content` only.

**Common context keys (every page).**
- `site_title: str` — from `Config.site_title`.
- `site_footer: str | None` — from `Config.site_footer`. If `None`, the `<footer>` element is **omitted entirely** (not rendered empty).
- `active: str` — one of `"about"`, `"posts"`, `"projects"`. The matching nav `<a>` gets `class="active"` (matching the design's class name).
- `page_title: str` — the `<title>` tag content.

**Per-page values for `active` and `page_title`** (constructed inline in `build.py` at the moment each template is rendered):

| Page | `active` | `page_title` |
|---|---|---|
| About (`/`) | `"about"` | `site_title` |
| Post listing (`/posts/`) | `"posts"` | `f"posts — {site_title}"` |
| Post detail (`/posts/<slug>/`) | `"posts"` | `f"{post.title} — {site_title}"` |
| Project listing (`/projects/`) | `"projects"` | `f"projects — {site_title}"` |
| Project detail (`/projects/<slug>/`) | `"projects"` | `f"{project.title} — {site_title}"` |

**Per-template context.**

| Template | Extra context | Purpose |
|---|---|---|
| `about.html.j2` | `body_html: str`, `links: list[Link]` | `/` |
| `posts.html.j2` | `posts: list[Post]` (already sorted, drafts filtered) | `/posts/` |
| `post.html.j2` | `post: Post` | `/posts/<slug>/` |
| `projects.html.j2` | `projects: list[Project]` (already sorted, drafts filtered) | `/projects/` |
| `project.html.j2` | `project: Project` | `/projects/<slug>/` |

**Per-template link rule.** Each entry on the listing pages links to the corresponding detail URL: post entries to `/posts/{{ post.slug }}/`, project entries to `/projects/{{ project.slug }}/`. Both leading and trailing slashes are required (matches `writer.write_page`'s URL-path contract).

**Escape contract.** `body_html` (About, Post, Project) is **pre-rendered HTML** from `markdown_renderer.render`. It must be piped through `|safe` in the templates: `{{ body_html | safe }}`. Every other context value goes through autoescape normally. Any omission of `|safe` on `body_html` breaks Markdown rendering; any `|safe` elsewhere is an XSS risk.

### Per-template structural skeleton

The design files are mock content; the templates must mirror their wrapper element structure and class names so the existing CSS selectors land on real pages. For each of the five child templates, emit at minimum this skeleton inside the `content` block (Jinja loops and conditionals are implicit — fill in real iteration where you see `…`):

- **`about.html.j2`** — `<section>` wrapping the rendered body and the links list:
  ```html
  <section>
    {{ body_html | safe }}
    {% if links %}
    <ul class="links">
      {% for link in links %}<li><a href="{{ link.url }}">{{ link.label }}</a></li>{% endfor %}
    </ul>
    {% endif %}
  </section>
  ```
- **`posts.html.j2`** — `<h1>posts</h1>` followed by `<ul class="post-list">`:
  ```html
  <h1>posts</h1>
  <ul class="post-list">
    {% for post in posts %}
    <li>
      <span class="date">{{ post.created_at.isoformat() }}</span>
      <a href="/posts/{{ post.slug }}/">{{ post.title }}</a>
    </li>
    {% endfor %}
  </ul>
  ```
- **`post.html.j2`** — `<article>` with header / body / back-link footer:
  ```html
  <article>
    <header class="post-header">
      <span class="date">{{ post.created_at.isoformat() }}</span>
      {% if post.updated_at %}<span class="updated">updated {{ post.updated_at.isoformat() }}</span>{% endif %}
      <h1>{{ post.title }}</h1>
    </header>
    <div class="post-body">{{ post.body_html | safe }}</div>
    <footer class="post-footer"><a href="/posts/">← back to posts</a></footer>
  </article>
  ```
- **`projects.html.j2`** — `<h1>projects</h1>` followed by one `<div class="project">` per project:
  ```html
  <h1>projects</h1>
  {% for project in projects %}
  <div class="project">
    <h3><a href="/projects/{{ project.slug }}/">{{ project.title }}</a></h3>
    <p>{{ project.description }}</p>
    {% if project.tags %}<span class="tags">{{ project.tags | join(" · ") }}</span>{% endif %}
  </div>
  {% endfor %}
  ```
- **`project.html.j2`** — `<article>` with header (tags + title + dates), `project-links`, body, back-link footer:
  ```html
  <article>
    <header class="post-header">
      {% if project.tags %}<span class="tags">{{ project.tags | join(" · ") }}</span>{% endif %}
      <h1>{{ project.title }}</h1>
      <span class="date">{{ project.created_at.isoformat() }}</span>
      {% if project.updated_at %}<span class="updated">updated {{ project.updated_at.isoformat() }}</span>{% endif %}
    </header>
    {% if project.links %}
    <div class="project-links">
      {% for link in project.links %}<a href="{{ link.url }}">{{ link.label }}</a>{% if not loop.last %} · {% endif %}{% endfor %}
    </div>
    {% endif %}
    <div class="post-body">{{ project.body_html | safe }}</div>
    <footer class="post-footer"><a href="/projects/">← back to projects</a></footer>
  </article>
  ```

These skeletons are the contract. The agent may add whitespace or attribute formatting freely, but the element types and class names must match — `style.css` selectors target them.

### Design reference

The HTML files under `design/` are the visual and markup source of truth. The Jinja templates must produce equivalent output (same class names, same element structure) when rendered with matching content. Specifically:

- `design/index.html` → `about.html.j2`
- `design/posts.html` → `posts.html.j2`
- `design/post.html` → `post.html.j2`
- `design/projects.html` → `projects.html.j2`
- `design/project.html` → `project.html.j2`

**Adaptations required** (the design files are mock content; your templates render real content):
- The design nav uses `href="index.html"`, `href="posts.html"`, `href="projects.html"`. Templates must use the **root-relative** URLs from SPEC: `/`, `/posts/`, `/projects/`. Nav link labels are fixed lowercase literals (matching the design): `about`, `posts`, `projects`. Not configurable.
- The design nav site-title link uses `class="site-title"`. Templates must do the same; the link text is `{{ site_title }}`.
- The design uses `<link rel="stylesheet" href="style.css">`. Templates must use `/style.css` (root-relative, since pages render at `/`, `/posts/<slug>/`, etc.).
- Dates are rendered as ISO 8601: `YYYY-MM-DD` (use a Jinja filter or format the date in Python before passing to the template — prefer `{{ post.created_at.isoformat() }}` inline).
- The design footer text is hardcoded (`© 2026 your name`). Templates must render `{{ site_footer }}` and **omit the entire `<footer>` element** when `site_footer` is falsy.

### Rendered-field contract (from SPEC §Output Specification)

Every page has the same navigation bar (top) and footer (bottom). The content between them, **per page**:

| Page | Content between nav and footer |
|---|---|
| About (`/`) | Rendered Markdown body, `links` (as a list) |
| Post listing (`/posts/`) | One entry per non-draft post: `title`, `created_at` |
| Post detail (`/posts/<slug>/`) | `title`, `created_at`, `updated_at` (if set), rendered Markdown body |
| Project listing (`/projects/`) | One entry per non-draft project: `title`, `description`, `tags` |
| Project detail (`/projects/<slug>/`) | `title`, `created_at`, `updated_at` (if set), `tags`, `links`, rendered Markdown body |

Render exactly these fields and no others.

### `src/sitegen3/scaffold/static/style.css`

**Starting point:** copy `design/style.css` verbatim into `src/sitegen3/scaffold/static/style.css`. The CSS lives in the scaffold tree (not the package itself) — per SPEC §Design Reference, the stylesheet lives in `static/` at the site root, shipped by `sitegen3 init`.

You **may** adjust or add CSS if the templates require it (e.g., new selectors or tweaked classes to match the actual rendered HTML). You **must not** restyle the site — the existing design properties are authoritative:
- Colors: bg `#111`, fg `#ccc`, accent `#5fba7d`.
- Typography: monospace only (IBM Plex Mono / Fira Code / SF Mono stack).
- Layout: centered single-column, 640px max-width, responsive at 480px.

### Tests (unit — the behavioural escape contract)

Minimum required test in `tests/test_templates.py`:

```python
from datetime import date
from pathlib import Path

from sitegen3.models import Post
from sitegen3.templates import render_template


def test_escape_contract_body_safe_and_title_escaped() -> None:
    html = render_template("post.html.j2", context={
        "site_title": "My Site",
        "site_footer": None,
        "active": "posts",
        "page_title": "x",
        "post": Post(
            slug="x",
            title="<script>alert(1)</script>",
            created_at=date(2026, 1, 1),
            updated_at=None,
            draft=False,
            body_html="<p>hello</p>",
            source_path=Path("x.md"),
        ),
    })
    assert "<p>hello</p>" in html              # body_html passed through |safe
    assert "&lt;script&gt;" in html            # title went through autoescape
    assert "<script>alert(1)</script>" not in html
```

This single test guards both directions of the escape contract. Add additional tests for each template only if you find a tricky case — the escape contract is the one that matters.

Also add a smoke test that `render_template` raises `RenderError` (not `jinja2.TemplateError`) when the template name is unknown. (Missing context keys silently render empty under Jinja2's default `Undefined` — do not test that case here.)

### Verification

The four-command gate. Additionally, spot-check one rendered template by hand if desired — the real end-to-end render happens in Task 11.

### Done when

All six templates exist, extend `base.html.j2`, and render the exact fields listed in the rendered-field contract. `render_template` wraps `jinja2` errors as `RenderError`. The escape contract test passes. `style.css` is in place at `src/sitegen3/scaffold/static/style.css`.

---

## Task 8 — Content discovery

**Goal.** Walk the input directory and return paths to content files. No file reads here — discovery answers "which files exist?", not "what do they mean?".

**Files to create.**
- `src/sitegen3/discovery.py`
- `tests/test_discovery.py`

**Responsibility (from ARCHITECTURE).** Walk the input directory and return paths to content files. **Does not open or read any files.** `find_posts` and `find_projects` return only `*.md` files in the **top level** of their respective directories; other files and subdirectories are ignored. Returns empty lists when `posts/` or `projects/` subdirectories are absent. Raises `DiscoveryError` if `about.md` is missing.

**Public interface.**
```python
from pathlib import Path

def find_about(input_dir: Path) -> Path           # Fatal if missing
def find_posts(input_dir: Path) -> list[Path]
def find_projects(input_dir: Path) -> list[Path]
```

**Key rules.**
- `find_about`: returns `input_dir / "about.md"` if it exists; otherwise raises `DiscoveryError` (fatal — there is no site without an about page).
- `find_posts`, `find_projects`: look at `input_dir / "posts"` and `input_dir / "projects"` respectively.
  - If the subdirectory does not exist → return `[]` (not an error).
  - If it exists, return all immediate children matching `*.md`. Use `Path.glob("*.md")` (non-recursive). Do **not** descend; do **not** include non-`.md` files or directories.
  - The order of returned paths is not specified — the caller sorts later.

**Tests (integration, `tmp_path`).** Cover:
- Missing `about.md` → `DiscoveryError` (`pytest.raises`).
- Present `about.md` → `find_about` returns the correct `Path`.
- Missing `posts/` directory → `find_posts` returns `[]`.
- Empty `posts/` directory → `find_posts` returns `[]`.
- `posts/` with a mix of `.md`, `.txt`, and a subdirectory → only the `.md` files are returned, in some deterministic comparison (sort both sides).
- Same coverage for `find_projects`.

**Verification.** The four-command gate.

**Done when.** All discovery functions return the correct paths; missing `about.md` is fatal; non-`.md` entries and subdirectories are ignored.

---

## Task 9 — Single-file loader

**Goal.** Turn a single file path into a single model (`About` / `Post` / `Project`). Errors are raised, not caught — the build loop decides what to do with them.

**Files to create.**
- `src/sitegen3/loader.py`
- `tests/test_loader.py`

**Responsibility (from ARCHITECTURE).** For one path: read the file, call `frontmatter.parse`, validate required fields (presence **and** type), call `markdown_renderer.render`, apply `slug.slugify`, construct a `Post` / `Project` / `About`. Any per-file failure (malformed TOML, missing required field, wrong TOML type, unterminated frontmatter) is raised as `LoaderError`. Upstream `ValueError` from `frontmatter.parse` and `tomllib.TOMLDecodeError` are wrapped via `raise LoaderError(...) from e`. Errors are never caught here.

**Public interface.**
```python
from pathlib import Path
from sitegen3.models import About, Post, Project

def load_about(path: Path) -> About
def load_post(path: Path) -> Post
def load_project(path: Path) -> Project
```

**Key rules.**

Read the file with `path.read_text(encoding="utf-8")`. Split via `frontmatter.parse`. Render body via `markdown_renderer.render`. Slug is derived from `slug.slugify(path.stem)` for posts/projects (no slug on `About`).

Required-field matrix (from SPEC §Frontmatter Format):

- **`about.md`**: no required fields.
  - `links` (array of `{label, url}`) — optional, default `[]`. Since `About.links` is typed `list[Link]` with no default on the dataclass, the loader must always pass a concrete list — `[]` when the key is absent.
- **Posts** (`posts/*.md`):
  - `title` (string) — **required**.
  - `created_at` (TOML date, i.e. bare `YYYY-MM-DD`, parsed to `datetime.date`) — **required**.
  - `updated_at` (date) — optional.
  - `draft` (bool) — optional, default `False`.
- **Projects** (`projects/*.md`):
  - `title` (string) — **required**.
  - `description` (string) — **required**.
  - `created_at` (date) — **required**.
  - `updated_at` (date) — optional.
  - `tags` (array of strings) — optional, default `[]`.
  - `links` (array of `{label, url}`) — optional, default `[]`.
  - `draft` (bool) — optional, default `False`.

Type validation: if a required field is present but the wrong type (e.g., `created_at = "2024-03-15"` as a **quoted string** rather than a bare TOML date), raise `LoaderError` — the string form becomes a `str`, not `datetime.date`, under `tomllib`, and would later crash date-based sort.

**Date strictness.** SPEC says `created_at` and `updated_at` are bare TOML dates (`YYYY-MM-DD`). `tomllib` parses bare `2024-03-15` as `datetime.date` and `2024-03-15T10:00:00` as `datetime.datetime`; since `datetime` is a subclass of `date`, a naive `isinstance(value, date)` check accepts both. Reject datetimes explicitly: use `type(value) is date` (or equivalently `isinstance(value, date) and not isinstance(value, datetime)`). A datetime in `created_at` raises `LoaderError("'created_at' must be a date (YYYY-MM-DD), got datetime")`.

When `links` is present (in `about.md` or in projects), it must itself be a TOML array — `links = "not an array"` → `LoaderError("'links' must be an array of {label, url} tables, got str")`. Each item must be a TOML table with both `label` (string) and `url` (string). Missing keys, wrong types, or non-table items → `LoaderError` naming the offending entry (e.g., `"links[0] must be a table with 'label' and 'url' (string), got str"`).

When `tags` is present (in projects), it must itself be a TOML array — `tags = "single"` → `LoaderError("'tags' must be an array of strings, got str")`. Each item must be a string. Mixed-type or non-string items → `LoaderError` naming the offending entry (e.g., `"tags[1] must be a string, got int"`).

Unknown keys are ignored silently.

All `LoaderError` messages should name the field and the expected type, e.g., `"'created_at' is required"` or `"'created_at' must be a date (YYYY-MM-DD), got str"`. Do **not** prefix with the source path — `build.py` already logs the path on skip (`log.warning("skipping %s: %s", path, e)`), and the loader doesn't have the input-dir context to compute a relative form anyway.

**Tests (integration, `tmp_path`, real files).** Cover each loader:
- Valid file → model with expected fields (including defaults applied where optional).
- Malformed TOML in frontmatter → `LoaderError` (caused by `tomllib.TOMLDecodeError`).
- Unterminated frontmatter → `LoaderError` (caused by `ValueError` from `frontmatter.parse`).
- Missing required field → `LoaderError` matching `r"'created_at' is required"` (no path prefix).
- Wrong type on required field (e.g., `created_at = "2024-03-15"` as a quoted string) → `LoaderError`.
- Datetime where a date is expected (`created_at = 2024-03-15T10:00:00`) → `LoaderError` matching `r"got datetime"`.
- `draft: true` is honoured (the model's `draft` field is `True`; filtering happens in `build.py`, not here).
- `About.links` parses to `list[Link]` (verify one round-trip).
- `About.links` defaults to `[]` when the `links` key is absent (and when the file has no frontmatter at all).
- `links` is the wrong top-level type (e.g., `links = "not an array"`) → `LoaderError` matching `r"'links' must be an array"`.
- Malformed `links` entry (e.g., a string instead of a table, or a table missing `url`) → `LoaderError` naming the entry.
- `tags` is the wrong top-level type (e.g., `tags = "single"`) → `LoaderError` matching `r"'tags' must be an array"`.
- Malformed `tags` entry (e.g., `tags = [1, 2]` or `tags = ["ok", 3]`) → `LoaderError` naming the entry.
- `Project.links`, `Project.tags` default to `[]` when absent.
- `updated_at` is `None` when absent.

Use `pytest.mark.parametrize` where the shape repeats.

**Verification.** The four-command gate.

**Done when.** Each of the three loaders produces the right model for valid input and raises `LoaderError` (never leaking `ValueError` or `TOMLDecodeError`) for every invalid case.

---

## Task 10 — Writer (filesystem output)

**Goal.** Encapsulate all output-side filesystem operations.

**Files to create.**
- `src/sitegen3/writer.py`
- `tests/test_writer.py`

**Responsibility (from ARCHITECTURE).** All output-side filesystem operations. Wipe the output directory, write HTML files at their URL paths (`/posts/foo/` → `posts/foo/index.html`), copy asset and static trees. The literal string `"static"` appears only in `copy_static`; no other module hardcodes the directory name.

**Public interface.**
```python
from pathlib import Path

def wipe_output(output_dir: Path) -> None
def write_page(output_dir: Path, url_path: str, html: str) -> None
def copy_assets(input_dir: Path, output_dir: Path) -> None
def copy_static(root_dir: Path, output_dir: Path) -> None
```

**Contracts.**
- `wipe_output`: if `output_dir` exists, `shutil.rmtree(output_dir)`. Then `output_dir.mkdir(parents=True, exist_ok=True)`. Log `INFO("wiping output directory: %s", output_dir)` before removing.
- `write_page`: `url_path` must start **and** end with `/`. Mapping:
  - `/` → `<output_dir>/index.html`
  - `/posts/foo/` → `<output_dir>/posts/foo/index.html`
  - `/posts/` → `<output_dir>/posts/index.html`
  Create intermediate directories as needed (`parent.mkdir(parents=True, exist_ok=True)`). Write with `path.write_text(html, encoding="utf-8")`. Callers that build `url_path` from a slug must include both slashes.
- `copy_assets`: copy `<input_dir>/assets/` tree to `<output_dir>/assets/`. If `<input_dir>/assets/` does not exist, log `INFO` (`"no assets/ directory, skipping"`) and return. **Not fatal.** Use `shutil.copytree(..., dirs_exist_ok=True)`.
- `copy_static`: copy `<root_dir>/static/` tree contents to `<output_dir>/`. If `<root_dir>/static/` does not exist, log `INFO` (`"no static/ directory, skipping"`) and return. **Not fatal.** Contents of `static/` land at the output root (e.g., `static/style.css` → `<output_dir>/style.css`).

**Tests (integration, `tmp_path`).** Cover:
- `wipe_output`: pre-populate `tmp_path/public/` with files and subdirectories → after `wipe_output`, directory exists and is empty.
- `wipe_output`: on missing directory → creates it, does not raise.
- `write_page`: `/` → `public/index.html` with expected content.
- `write_page`: `/posts/foo/` → `public/posts/foo/index.html`, intermediate dirs created.
- `write_page`: assertion on trailing-slash requirement (if you choose to enforce via `assert` or `ValueError`, match the behaviour you pick — the SPEC says "must", so a runtime check is reasonable).
- `copy_assets`: missing `input_dir/assets/` → no raise, log captured.
- `copy_assets`: populated `input_dir/assets/` → files appear under `output_dir/assets/` preserving tree.
- `copy_static`: missing `root_dir/static/` → no raise, log captured.
- `copy_static`: `root_dir/static/style.css` → `output_dir/style.css`.

Use `caplog` fixture to assert `INFO` log messages on the "missing directory" branches.

**Verification.** The four-command gate.

**Done when.** All four writer functions behave per contract and their edge cases (missing directories, nested paths) are covered by tests.

---

## Task 11 — Build orchestration

**Goal.** Wire `discovery` → `loader` → `templates` → `writer` into a single `build()` function with per-page resilience and fatal-on-collision semantics. Include the end-to-end fixture site the test runs against.

**Files to create.**
- `src/sitegen3/build.py`
- `tests/test_build.py`
- `tests/fixtures/sample_site/sitegen3.toml`
- `tests/fixtures/sample_site/content/about.md`
- `tests/fixtures/sample_site/content/posts/hello-world.md`
- `tests/fixtures/sample_site/content/posts/older-post.md` — earlier `created_at`, used to verify sort order
- `tests/fixtures/sample_site/content/posts/draft-post.md` — `draft = true`, used to verify build-time draft filtering
- `tests/fixtures/sample_site/content/posts/broken.md` — **intentionally malformed TOML**
- `tests/fixtures/sample_site/content/projects/sample.md`
- `tests/fixtures/sample_site/static/style.css`

**Responsibility (from ARCHITECTURE).** Orchestrate the full pipeline. Catch `PageError` in two places: the load loop and the render loop. Log `WARNING` with the source path; increment a local skip counter. `load_about` and the About render happen **outside** both guards — any About failure propagates as fatal. Filter drafts before sorting. Sort posts and projects newest-first by `created_at`, with slug as tiebreaker. After filtering, check for slug collisions within each collection; on collision, raise `DiscoveryError` naming both source paths (fatal — silent overwrite would cause data loss). Log the final summary: total rendered, total skipped.

**Public interface.**
```python
from pathlib import Path

def build(root_dir: Path) -> None
```

**Pipeline order (exact).**
1. `load_config(root_dir)` → `Config` (fatal errors propagate).
2. `wipe_output(config.output_dir)`.
3. `find_about(input_dir)` → `Path`; `load_about(path)` → `About`. Both are fatal on failure.
4. `find_posts(input_dir)` → `list[Path]`. For each path: try `load_post(path)`. On `PageError`, log `WARNING("skipping %s: %s", path, e)`, increment `skipped`, continue.
5. Same for projects.
6. Filter out loaded models where `draft is True`.
7. Check for slug collisions within posts (and separately within projects). On collision, raise `DiscoveryError("slug collision: %s and %s both normalize to %s", path_a, path_b, slug)` — fatal.
8. Sort posts and projects: primary key `created_at` **descending** (newest first); tiebreaker `slug` **ascending**.
9. Render About via `render_template("about.html.j2", ...)` → `write_page(output_dir, "/", html)`. **Not** wrapped in a `PageError` guard. Any failure is fatal.
10. For each post: try `render_template("post.html.j2", ...)` and `write_page(..., f"/posts/{post.slug}/", html)`. On `PageError`, log `WARNING`, increment `skipped`, continue. On success, log `DEBUG("rendered post: %s → /posts/%s/", post.source_path, post.slug)`.
11. Render the post listing via `render_template("posts.html.j2", ...)` → `write_page(output_dir, "/posts/", html)`. **Not** wrapped in a `PageError` guard — listing renders are fatal on failure (a broken listing template is a build-blocking bug, not a content-author bug; per-page resilience exists for individual content files only).
12. Same for projects (individual pages + listing page). The per-project loop in Step 12a is wrapped in try/except like Step 10; the projects-listing render in Step 12b is **not** wrapped, same rationale as Step 11. On `PageError` per-project, log `WARNING`, increment `skipped`, continue. Per-project success: `DEBUG("rendered project: %s → /projects/%s/", project.source_path, project.slug)`.
13. `copy_assets(input_dir, output_dir)`.
14. `copy_static(root_dir, output_dir)`.
15. Log summary: `INFO("build complete: rendered=%d skipped=%d", rendered, skipped)`.

`rendered` counts every successful page write — increment once after each successful `write_page` call, including About (Step 9), each post detail (Step 10), the post listing (Step 11), each project detail (Step 12), and the project listing (Step 12). For the fixture site below, the expected count is 1 (about) + 1 (post listing) + 2 (hello-world + older-post detail; draft-post is filtered, not rendered) + 1 (project listing) + 1 (sample detail) = 6, with `skipped` = 1 from the broken post.

Start-of-build `INFO` log: `INFO("building site: input=%s output=%s", input_dir, output_dir)`.

**Context dict construction.** Each `render_template` call takes a plain `dict` built inline. The five contexts are:

```python
about_ctx: dict[str, Any] = {
    "site_title": config.site_title,
    "site_footer": config.site_footer,
    "active": "about",
    "page_title": config.site_title,
    "body_html": about.body_html,
    "links": about.links,
}
about_html = render_template("about.html.j2", about_ctx)

posts_listing_ctx: dict[str, Any] = {
    "site_title": config.site_title,
    "site_footer": config.site_footer,
    "active": "posts",
    "page_title": f"posts — {config.site_title}",
    "posts": posts,                       # already sorted, drafts filtered
}
posts_listing_html = render_template("posts.html.j2", posts_listing_ctx)

# Per post:
post_ctx: dict[str, Any] = {
    "site_title": config.site_title,
    "site_footer": config.site_footer,
    "active": "posts",
    "page_title": f"{post.title} — {config.site_title}",
    "post": post,
}
post_html = render_template("post.html.j2", post_ctx)

projects_listing_ctx: dict[str, Any] = {
    "site_title": config.site_title,
    "site_footer": config.site_footer,
    "active": "projects",
    "page_title": f"projects — {config.site_title}",
    "projects": projects,                 # already sorted, drafts filtered
}
projects_listing_html = render_template("projects.html.j2", projects_listing_ctx)

# Per project:
project_ctx: dict[str, Any] = {
    "site_title": config.site_title,
    "site_footer": config.site_footer,
    "active": "projects",
    "page_title": f"{project.title} — {config.site_title}",
    "project": project,
}
project_html = render_template("project.html.j2", project_ctx)
```

**Fixture site contents.**

Populate `tests/fixtures/sample_site/` with the minimum viable site plus one intentionally broken post (resilience), one draft (filtering), and a second valid post (sort order). Exactly:

- `sitegen3.toml` — `[site] title = "Fixture Site"`, `footer = "test footer"`. **Omit the `[paths]` table entirely** so the build also exercises `config.py`'s default-paths branch end-to-end.
- `content/about.md` — valid frontmatter with one link; a one-paragraph body.
- `content/posts/hello-world.md` — valid post with `title = "Hello World"`, `created_at = 2026-03-15`, a short body.
- `content/posts/older-post.md` — valid post with `title = "Older Post"`, `created_at = 2025-01-01` (must sort *after* `hello-world` because newest-first).
- `content/posts/draft-post.md` — valid frontmatter plus `draft = true` (`title`, `created_at` whatever; the body is irrelevant since the post is filtered before rendering).
- `content/posts/broken.md` — malformed TOML (e.g., unterminated string, or `created_at = not a date`). This must produce a `LoaderError` at load time, exercising the resilience path.
- `content/projects/sample.md` — valid project with title, description, created_at, one tag, one link, a short body.
- `static/style.css` — can be a one-line placeholder (`/* fixture */`) or a copy of the scaffold stylesheet. The test verifies it gets copied; it doesn't verify content.

**Tests (end-to-end).** In `tests/test_build.py`:

1. `test_build_fixture_site_produces_expected_output_tree`: copy the fixture tree to `tmp_path` (so output writes don't contaminate the source tree), call `build(tmp_path)`, assert:
   - `public/index.html` exists.
   - `public/posts/index.html` exists.
   - `public/posts/hello-world/index.html` exists.
   - `public/posts/older-post/index.html` exists.
   - `public/posts/draft-post/` does **not** exist (filtered by `draft = true`).
   - `public/posts/broken/` does **not** exist (skipped by the resilience path).
   - `public/projects/index.html` exists.
   - `public/projects/sample/index.html` exists.
   - `public/style.css` exists.
   - In the post-listing HTML (`public/posts/index.html`), the substring `hello-world` appears **before** `older-post` (newest-first sort). Read the file, find both substrings with `.find()`, assert `hello_idx < older_idx`.
2. `test_build_resilience_broken_post_logs_warning_and_continues`: using `caplog`, confirm a `WARNING`-level record whose message names `broken.md` was emitted, and that the overall build succeeded (no raised exception).
3. `test_build_slug_collision_is_fatal`: add `Hello World.md` alongside `hello-world.md` (both slugify to `hello-world`, and the two filenames coexist on case-sensitive and case-insensitive filesystems). Expect `pytest.raises(DiscoveryError, match="...")` citing both paths. Note: the collision check runs **after** all loads complete, so `broken.md`'s load failure does not affect this test — it operates on the surviving non-draft set (`hello-world.md`, `older-post.md`, `Hello World.md`).
4. `test_build_missing_about_is_fatal`: remove `about.md` from the copied fixture, expect `DiscoveryError` (the fatal branch from `find_about`).

Use `shutil.copytree` to copy the fixture tree into `tmp_path` at the start of each test — fixtures stay immutable on disk.

**Verification.** The four-command gate.

**Done when.** `build()` produces the expected output tree for the fixture site, the broken post is skipped (not fatal), slug collisions and missing about are fatal, summary line is logged.

---

## Task 12 — Serve subcommand

**Goal.** Serve the output directory over HTTP on localhost. No watching, no live reload (explicitly out of scope — see `docs/TODO.md`).

**Files to create.**
- `src/sitegen3/serve.py`
- `tests/test_serve.py` (minimal smoke test only)

**Responsibility (from ARCHITECTURE).** Serve `config.output_dir` over HTTP using stdlib `http.server`, bound to `127.0.0.1` (not `0.0.0.0`). Raise `ServeError` if the output directory does not exist (user hasn't run `build` yet).

**Public interface.**
```python
from pathlib import Path

def serve(root_dir: Path, port: int) -> None
```

**Implementation outline.**
1. `config = load_config(root_dir)`.
2. If `config.output_dir` does not exist → `raise ServeError(f"output directory {config.output_dir} does not exist; run 'sitegen3 build' first")`.
3. Bind the handler to the output directory with `functools.partial(SimpleHTTPRequestHandler, directory=str(config.output_dir))`. Do **not** use `os.chdir` — it mutates global process state and breaks programmatic / test reuse.
4. Log `INFO("serving %s on http://127.0.0.1:%d", config.output_dir, port)`.
5. Start `http.server.HTTPServer(("127.0.0.1", port), handler).serve_forever()`.

**Key rule.** Bind to `127.0.0.1`, **not** the default `0.0.0.0` — preview must not be exposed on the LAN.

**Tests (integration smoke — minimal).**
- `test_serve_raises_when_output_missing`: write a valid `sitegen3.toml` in `tmp_path`, create `content/` (so `load_config` passes) but **not** `public/`. Call `serve(tmp_path, port=...)` and assert `pytest.raises(ServeError, match="...")`. Do not actually start the server.

Per ARCHITECTURE §Testing, `serve` is otherwise marked "No" tests — thin wrapper around `http.server`. Do not attempt to start a real server in the test suite.

**Verification.** The four-command gate.

**Done when.** `serve` raises `ServeError` on missing output and is a straight wrapper around `http.server` when the output exists.

---

## Task 13 — Init subcommand and scaffold tree

**Goal.** Scaffold a new site in a target directory from files bundled inside the package.

**Files to create.**
- `src/sitegen3/init_cmd.py`
- `src/sitegen3/scaffold/sitegen3.toml`
- `src/sitegen3/scaffold/content/about.md`
- `src/sitegen3/scaffold/content/assets/.gitkeep`
- `src/sitegen3/scaffold/content/posts/hello-world.md`
- `src/sitegen3/scaffold/content/projects/sample-project.md`
- `tests/test_init_cmd.py`

(`src/sitegen3/scaffold/static/style.css` was created in Task 7; do not duplicate it here.)

**Responsibility (from ARCHITECTURE).** Scaffold a new site. Raise `InitError` if `sitegen3.toml` already exists in the target directory. Copy files from `src/sitegen3/scaffold/` to the target via `importlib.resources`.

**Public interface.**
```python
from pathlib import Path

def init(root_dir: Path) -> None
```

**Scaffold file contents.**
- `sitegen3.toml` — placeholder values: `[site] title = "My Site"`, `footer = "© 2026 My Name"`, `[paths] input = "content"`, `output = "public"`. The footer is a plain literal string — no template placeholders or runtime substitution. The user edits both `title` and `footer` after scaffolding.
- `content/about.md` — frontmatter with one placeholder link, one-paragraph body.
- `content/assets/.gitkeep` — empty file.
- `content/posts/hello-world.md` — valid post frontmatter (`title = "Hello World"`, `created_at = 2026-01-01`), short body. Pin the date to a fixed past value so `init` output is byte-stable across runs (using `today` would make the scaffold non-reproducible).
- `content/projects/sample-project.md` — valid project frontmatter (`title = "Sample Project"`, `description`, `created_at = 2026-01-01`, one tag, one link), short body.

**Implementation outline.**
1. If `(root_dir / "sitegen3.toml").exists()` → `raise InitError(f"sitegen3.toml already exists in {root_dir}")`.
2. Walk the scaffold tree via `importlib.resources.files("sitegen3") / "scaffold"`. For each traversable, create the mirrored destination under `root_dir` and copy file content (respecting directory structure).
3. Log `INFO("initialized site at %s", root_dir)`.

Use `importlib.resources.as_file` + `shutil.copytree` if you want the simplest implementation, or iterate `Traversable` for purer resource-based access.

**Tests (integration, `tmp_path`).** Cover:
- Happy path: empty `tmp_path` → `init(tmp_path)` → assert `sitegen3.toml`, `content/about.md`, `content/posts/hello-world.md`, `content/projects/sample-project.md`, `content/assets/` (directory), `static/style.css` all exist at the expected paths.
- Target already contains `sitegen3.toml` → `InitError` (`pytest.raises`, message matches).
- Scaffolded site is valid: call `build(tmp_path)` after `init(tmp_path)` and confirm it succeeds without raising (this is a strong smoke test that the scaffold content actually works).

**Verification.** The four-command gate.

**Done when.** `init` copies the scaffold tree, refuses to overwrite, and the scaffolded site builds cleanly.

---

## Task 14 — CLI wiring and entry point

**Goal.** Wire the three subcommands (`build`, `serve`, `init`) behind a single `sitegen3` command using stdlib `argparse`. This is the last task — it imports every other module.

**Files to create.**
- `src/sitegen3/cli.py`
- `tests/test_cli.py`

**Responsibility (from ARCHITECTURE).** Parse command-line arguments using stdlib `argparse` and dispatch to `build`, `serve`, or `init_cmd`. Build a top-level parser with three subparsers; each subparser has its own `dir` positional and (for `serve`) a `--port` option. Call `logging_setup.configure_logging()` once on entry. Catch `SitegenError` at the top level, log at `ERROR`, and call `sys.exit(1)`. No other business logic.

**Public interface.**
```python
def main() -> None
```

`pyproject.toml` already declares `sitegen3 = "sitegen3.cli:main"` (Task 1).

**CLI surface (from SPEC §CLI Interface).** Match SPEC's help text as closely as `argparse` allows.

- `sitegen3 build [DIR]` — default `DIR` = `.`. Dispatches to `build.build(Path(dir))`.
- `sitegen3 serve [DIR] [--port PORT]` — default `DIR` = `.`, default `PORT` = `8000`. Dispatches to `serve.serve(Path(dir), port)`.
- `sitegen3 init [DIR]` — default `DIR` = `.`. Dispatches to `init_cmd.init(Path(dir))`.

Help strings: copy the summary sentences from SPEC per subcommand (the "Usage" blocks) into each subparser's `help=` / `description=`.

**`main()` flow.**
1. `configure_logging()`.
2. Build parser + subparsers. Construct the top-level parser with `argparse.ArgumentParser(prog="sitegen3", ...)` so `sitegen3 --help` renders `Usage: sitegen3 …` regardless of how `main` is invoked (including under `pytest`, where the default `prog` would be the test runner's name).
3. `args = parser.parse_args()`.
4. Dispatch based on `args.command` (or the `func` pattern with `subparser.set_defaults(func=...)`).
5. Wrap the dispatch in `try/except SitegenError as e: logging.getLogger(__name__).error("%s", e); sys.exit(1)`.

**Tests (unit, smoke).** Patch `sys.argv` and confirm dispatch for each subcommand. Mock the subcommand function (`build.build`, `serve.serve`, `init_cmd.init`) via `monkeypatch` and assert it was called with the right arguments. Sample tests:

- `test_main_dispatches_build`: `sys.argv = ["sitegen3", "build", "/some/dir"]` → `build.build` called with `Path("/some/dir")`.
- `test_main_dispatches_build_default_dir`: `sys.argv = ["sitegen3", "build"]` → `build.build` called with `Path(".")`.
- `test_main_dispatches_serve_with_port`: `sys.argv = ["sitegen3", "serve", "--port", "9000"]` → `serve.serve` called with `(Path("."), 9000)`.
- `test_main_dispatches_init`: `sys.argv = ["sitegen3", "init"]` → `init_cmd.init` called with `Path(".")`.
- `test_main_exits_1_on_sitegen_error`: mock the dispatched function to raise `ConfigError("boom")`, call `main()`, catch `SystemExit`, assert `exit_code == 1`, and (via `caplog`) a `ERROR`-level record was logged.

Use `monkeypatch.setattr` to replace the imported subcommand functions so tests don't actually build/serve/init.

**Verification.** The four-command gate.

Additionally, verify the console entry point end-to-end:
```
poetry install
sitegen3 --help
sitegen3 init /tmp/sitegen3-smoke
sitegen3 build /tmp/sitegen3-smoke
ls /tmp/sitegen3-smoke/public/        # index.html, style.css, posts/, projects/
```

**Done when.** `sitegen3 --help` and all three subcommands show the expected help; dispatch tests pass; fatal errors exit with code 1 and a logged `ERROR` record.

---

## Post-task audit

After Task 14 is green, quickly verify:
- Every module listed in ARCHITECTURE.md §Source Tree Layout exists and has its public interface.
- `ruff`, `pyright`, `pytest` all pass with no warnings.
- `sitegen3 init` → `sitegen3 build` → `sitegen3 serve` on a throwaway directory produces a viewable site at `http://127.0.0.1:8000`.
