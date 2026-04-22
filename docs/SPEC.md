# sitegen3 — Specification

## Overview

`sitegen3` is a static website generator for a personal website. It takes structured Markdown content, assets, and a configuration file as input and produces a complete static site (HTML, CSS, and assets) as output.

The generated site has three sections:
- **About** — a single page with a bio and social links
- **Posts** — a blog with a listing page and individual post pages
- **Projects** — a portfolio with a listing page and individual project pages

---

## Technology Stack

| Concern | Choice |
|---|---|
| Language | Python 3.12+ |
| Dependency management | Poetry |
| Template engine | Jinja2 |
| Markdown renderer | python-markdown (with `fenced_code` and `tables` extensions) |
| Configuration format | TOML |
| Frontmatter parser | Custom delimiter splitting; TOML parsed by `tomllib` (stdlib) |
| Linter / formatter | ruff |
| Type checker | pyright (strict mode) |
| Testing framework | pytest |

---

## Input Specification

### Directory Structure

```
<input_dir>/          # default: content/
  about.md
  assets/             # static files (images, etc.) — copied to output
    images/
      photo.jpg
  posts/
    my-first-post.md
    another-post.md
  projects/
    my-project.md
static/               # framework-level files (style.css) — copied to output root
  style.css
```

- `about.md` is a special reserved file for the about page.
- If `posts/` or `projects/` directories do not exist, they are treated as empty collections — the listing page is still generated with zero entries.
- Files in `posts/` and `projects/` each produce one page. The filename (without `.md`) becomes the URL slug. Only `*.md` files are considered; any other files and all subdirectories are ignored.
- The `assets/` subdirectory inside `<input_dir>` is copied as-is to the output. It holds content-level files (images referenced in posts and projects).
- The `static/` directory is always at the site root (not configurable); this is intentional to keep the project structure predictable. It holds framework-level files (CSS, favicon) and its contents are copied to the output root.

### Referencing Assets and Internal Pages in Markdown

Because each post and project is rendered into its own subdirectory (e.g. `posts/my-post/index.html`), relative paths from the source file do not match the URL layout of the output. All internal references — assets and links to other pages — must use **root-relative URLs**.

Assets:

```markdown
![Alt text](/assets/images/photo.jpg)
```

Internal pages:

| Target | URL form |
|---|---|
| About page | `/` |
| Post listing | `/posts/` |
| Individual post | `/posts/<slug>/` |
| Project listing | `/projects/` |
| Individual project | `/projects/<slug>/` |

```markdown
See [my earlier post](/posts/my-first-post/) or the [project page](/projects/my-project/).
```

The `<slug>` must match the normalized slug derived from the source filename (see the slug pipeline under *Output Specification*). The build does not rewrite URLs — paths written in the Markdown are emitted as-is in the HTML. Relative paths like `assets/images/photo.jpg` or `my-first-post/` will resolve incorrectly in the browser and must not be used.

### Frontmatter Format

Frontmatter is placed at the top of each Markdown file, delimited by `+++` on its own line. It uses TOML syntax and is parsed by a custom module (no external frontmatter library).

```
+++
<TOML content>
+++

Markdown body starts here.
```

Parsing rules:

- If a file contains no `+++` delimiter at all, the frontmatter is returned as an empty dictionary and the entire file is treated as the Markdown body.
- If the opening `+++` is present but the closing `+++` is missing, the parser raises an exception.
- The frontmatter module never validates required fields — it only splits and parses. Validation of required fields (e.g., `title` for posts) is the responsibility of the rendering step.
- Unknown keys in frontmatter and in `sitegen3.toml` are silently ignored. This matches standard TOML/stdlib parser behaviour and keeps the config forward-compatible.
- Raw HTML embedded in Markdown bodies is passed through to the rendered output unchanged. Authors are trusted; this is not a multi-tenant renderer.

#### `about.md`

```toml
+++
[[links]]
label = "GitHub"
url = "https://github.com/username"

[[links]]
label = "Email"
url = "mailto:hello@example.com"
+++

Bio text goes here in Markdown.
```

| Field | Type | Required | Description |
|---|---|---|---|
| `links` | array of `{label, url}` | No | Social/contact links shown on the about page |

#### Posts (`posts/*.md`)

```toml
+++
title = "My First Post"
created_at = 2024-03-15
updated_at = 2024-04-01
+++

Post body in Markdown.
```

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | string | Yes | Post title |
| `created_at` | date (`YYYY-MM-DD`) | Yes | Publication date, used for display and sort order |
| `updated_at` | date (`YYYY-MM-DD`) | No | Last updated date |
| `draft` | boolean | No | If `true`, the entry is excluded from both the individual page render and the listing page (default: `false`) |

#### Projects (`projects/*.md`)

```toml
+++
title = "My Project"
description = "A short one-line description."
created_at = 2024-03-15
updated_at = 2024-04-01
tags = ["python", "cli"]

[[links]]
label = "GitHub"
url = "https://github.com/username/project"

[[links]]
label = "Demo"
url = "https://demo.example.com"
+++

Project description in Markdown.
```

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | string | Yes | Project name |
| `description` | string | Yes | Short summary shown in the project listing |
| `created_at` | date (`YYYY-MM-DD`) | Yes | Creation date, used for display and sort order |
| `updated_at` | date (`YYYY-MM-DD`) | No | Last updated date |
| `tags` | array of strings | No | Display-only labels (no tag index pages) |
| `links` | array of `{label, url}` | No | External links (GitHub, demo, docs, etc.) |
| `draft` | boolean | No | If `true`, the entry is excluded from both the individual page render and the listing page (default: `false`) |

---

## Output Specification

### Directory Structure

```
<output_dir>/         # default: public/
  index.html          # About page
  style.css           # Copied from static/
  assets/             # Copied from <input_dir>/assets/
    images/
      photo.jpg
  posts/
    index.html        # Post listing (all posts, newest-first)
    my-first-post/
      index.html
    another-post/
      index.html
  projects/
    index.html        # Project listing
    my-project/
      index.html
```

### Pages

| URL | Source | Description |
|---|---|---|
| `/` | `about.md` | About page with bio and links |
| `/posts/` | All `posts/*.md` | Post listing, sorted newest-first by `created_at` |
| `/posts/<slug>/` | `posts/<slug>.md` | Individual post |
| `/projects/` | All `projects/*.md` | Project listing, sorted newest-first by `created_at` |
| `/projects/<slug>/` | `projects/<slug>.md` | Individual project |

#### Rendered Fields per Page Type

The visual styling is authoritative in `design/`. The *data shown* on each page is authoritative here — templates must render exactly these fields and no others. Every page has the same navigation bar at the top and the same footer at the bottom; the table below lists the page-specific content that sits between them.

| Page | Content between nav and footer |
|---|---|
| About (`/`) | Rendered Markdown body, `links` (as a list) |
| Post listing (`/posts/`) | One entry per non-draft post: `title`, `created_at` |
| Post detail (`/posts/<slug>/`) | `title`, `created_at`, `updated_at` (if set), rendered Markdown body |
| Project listing (`/projects/`) | One entry per non-draft project: `title`, `description`, `created_at`, `tags` |
| Project detail (`/projects/<slug>/`) | `title`, `created_at`, `updated_at` (if set), `tags`, `links`, rendered Markdown body |

- **Navigation** (top, every page): site title on the left, the three fixed links **About** / **Posts** / **Projects** on the right.
- **Footer** (bottom, every page): `site.footer` text if set; otherwise the footer element is omitted entirely.

Slugs are derived from the Markdown filename (without the `.md` extension) with the following normalization pipeline:

1. Convert to lowercase.
2. Replace spaces with hyphens.
3. Strip any character that is not a lowercase ASCII letter, digit, or hyphen.
4. Collapse consecutive hyphens into a single hyphen.
5. Strip leading and trailing hyphens.

For example, `My First Post.md` becomes `my-first-post/`.

Both posts and projects with the same `created_at` date are sorted alphabetically by slug.

If two **non-draft** source files within the same collection normalize to the same slug (e.g., `My Post.md` and `my-post.md` both produce `my-post`), the build aborts with a fatal error naming both source files. Silent overwrite would cause data loss. The check runs after draft filtering, so a non-draft and a draft sharing a slug are not a conflict — only the non-draft produces output.

---

## CLI Interface

The tool is invoked as `sitegen3` with three subcommands. Each command accepts an optional `DIR` positional argument — the site root directory where `sitegen3.toml` lives. If omitted, the current working directory is used. Input and output paths are always read from the config file inside that directory.

### Top-level help

```
$ sitegen3 --help
Usage: sitegen3 [OPTIONS] COMMAND [ARGS]...

  Static site generator for sitegen3.

Options:
  --help  Show this message and exit.

Commands:
  build  Build the site from content sources.
  init   Scaffold a new site in the given directory.
  serve  Serve the output directory over HTTP.
```

### `sitegen3 build`

```
$ sitegen3 build --help
Usage: sitegen3 build [OPTIONS] [DIR]

  Build the site from content sources.

  Looks for sitegen3.toml in DIR to determine the input and output
  directories. Deletes the output directory if it exists, then renders
  all Markdown content into HTML and copies assets and static files to
  the output directory. DIR defaults to the current working directory.

Arguments:
  [DIR]  Site root directory containing sitegen3.toml.  [default: .]

Options:
  --help  Show this message and exit.
```

### `sitegen3 serve`

```
$ sitegen3 serve --help
Usage: sitegen3 serve [OPTIONS] [DIR]

  Serve the output directory over HTTP on 127.0.0.1 (localhost only).

  Looks for sitegen3.toml in DIR to determine which directory to serve.
  Starts Python's built-in http.server for local preview, bound to 127.0.0.1
  so the preview is not exposed on the LAN. Does not watch for changes or
  reload the browser — to preview an updated build, run 'sitegen3 build' and
  then restart this command. Exits with an error if the output directory
  does not exist (run 'sitegen3 build' first). DIR defaults to the current
  working directory.

Arguments:
  [DIR]  Site root directory containing sitegen3.toml.  [default: .]

Options:
  --port PORT  Port to listen on.  [default: 8000]
  --help       Show this message and exit.
```

### `sitegen3 init`

```
$ sitegen3 init --help
Usage: sitegen3 init [OPTIONS] [DIR]

  Scaffold a new site in the given directory.

  Creates sitegen3.toml pre-filled with placeholder values, the expected
  input directory structure (content/, content/assets/, content/posts/,
  content/projects/), and sample content files (about.md, a sample post,
  and a sample project) inside DIR. Also creates the static/ directory
  with style.css. Fails with an error if sitegen3.toml already exists to
  avoid overwriting an existing site. DIR defaults to the current working
  directory.

Arguments:
  [DIR]  Directory to initialise.  [default: .]

Options:
  --help  Show this message and exit.
```

---

## Configuration

The configuration file `sitegen3.toml` must be present in the working directory when running any command.

```toml
[site]
title = "My Site"
footer = "© 2024 My Name"

[paths]
input = "content"
output = "public"
```

| Key | Type | Required | Description |
|---|---|---|---|
| `site.title` | string | Yes | Site name shown in the navigation bar |
| `site.footer` | string | No | Footer text rendered on every page. If unset, the footer element is omitted from the DOM entirely (not rendered empty). |
| `paths.input` | string | No | Input content directory (default: `content`) |
| `paths.output` | string | No | Output directory (default: `public`) |

---

## Error Handling & Logging

The build uses Python's `logging` module. All significant actions and errors are logged to stderr.

### Per-page resilience

When a single page fails to render (e.g., missing required frontmatter field, malformed TOML, template error), the build:

1. Logs a warning with the file path and the reason for the failure.
2. Skips that page.
3. Continues building the rest of the site.

The build only exits with a non-zero status if a fatal error occurs (e.g., missing `sitegen3.toml`, missing input directory, missing `about.md`, missing required configuration fields).

### What gets logged

- Start of build, including input/output paths.
- Output directory wipe.
- Each page rendered successfully (at `DEBUG` level).
- Each page that failed to render, with the reason (at `WARNING` level).
- Copy of assets and static files.
- Build summary: total pages rendered, total skipped.

---

## Design Reference

The visual design is defined in `design/` within the sitegen3 source repository. These files are development-time references used only when creating the Jinja2 templates and CSS — they are not distributed with the tool, not read during the build, and must not be referenced by any runtime code.

Key design properties:

- **Theme**: Dark background (`#111`) with light gray text (`#ccc`) and a sage green accent (`#5fba7d`)
- **Typography**: Monospace only — IBM Plex Mono / Fira Code / SF Mono stack
- **Layout**: Centered single-column, max-width 640px, responsive at 480px
- **Navigation**: Site title (from `site.title`) on the left; three nav links on the right with fixed labels **About** (→ `/`), **Posts** (→ `/posts/`), **Projects** (→ `/projects/`). Labels are not configurable.

Design files:

| File | Purpose |
|---|---|
| `design/index.html` | About page reference |
| `design/posts.html` | Post listing reference |
| `design/post.html` | Individual post reference |
| `design/projects.html` | Project listing reference |
| `design/project.html` | Individual project reference |

The stylesheet (`style.css`) lives in `static/`, not `design/`.

### Date Display Format

All dates rendered on the site use ISO 8601 format: `YYYY-MM-DD` (e.g., `2026-04-13`).
