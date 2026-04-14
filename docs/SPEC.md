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
| Language | Python 3.12 |
| Dependency management | Poetry |
| Template engine | Jinja2 |
| Markdown renderer | python-markdown (with `fenced_code` and `tables` extensions) |
| Configuration format | TOML |
| Frontmatter parser | Custom delimiter splitting; TOML parsed by `tomllib` (stdlib) |

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
- Files in `posts/` and `projects/` each produce one page. The filename (without `.md`) becomes the URL slug.
- The `assets/` subdirectory inside `<input_dir>` is copied as-is to the output. It holds content-level files (images referenced in posts and projects).
- The `static/` directory is always at the site root (not configurable); this is intentional to keep the project structure predictable. It holds framework-level files (CSS, favicon) and its contents are copied to the output root.

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
| `draft` | boolean | No | If `true`, the page is skipped during build (default: `false`) |

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
| `draft` | boolean | No | If `true`, the page is skipped during build (default: `false`) |

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

Slugs are derived from the Markdown filename (without the `.md` extension) with the following normalization pipeline:

1. Convert to lowercase.
2. Replace spaces with hyphens.
3. Strip any character that is not a lowercase ASCII letter, digit, or hyphen.
4. Collapse consecutive hyphens into a single hyphen.
5. Strip leading and trailing hyphens.

For example, `My First Post.md` becomes `my-first-post/`.

Both posts and projects with the same `created_at` date are sorted alphabetically by slug.

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

  Serve the output directory over HTTP.

  Looks for sitegen3.toml in DIR to determine which directory to serve.
  Starts Python's built-in http.server for local preview. Does not watch for
  changes or reload the browser — to preview an updated build, run
  'sitegen3 build' and then restart this command. DIR defaults to the
  current working directory.

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
| `site.footer` | string | No | Footer text rendered on every page |
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
- **Navigation**: Site title left, nav links right (`/`, `/posts/`, `/projects/`)

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
