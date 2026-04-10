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
| Markdown renderer | python-markdown |
| Configuration format | TOML |
| Frontmatter parser | Custom (no external library) |

---

## Input Specification

### Directory Structure

```
<input_dir>/          # default: content/
  about.md
  posts/
    my-first-post.md
    another-post.md
  projects/
    my-project.md
assets/               # static files (images, etc.) — separate from content
  images/
    photo.jpg
```

- `about.md` is a special reserved file for the about page.
- Files in `posts/` and `projects/` each produce one page. The filename (without `.md`) becomes the URL slug.
- The `assets/` directory is copied as-is to the output.

### Frontmatter Format

Frontmatter is placed at the top of each Markdown file, delimited by `+++` on its own line. It uses TOML syntax and is parsed by a custom module (no external frontmatter library).

```
+++
<TOML content>
+++

Markdown body starts here.
```

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

#### Projects (`projects/*.md`)

```toml
+++
title = "My Project"
description = "A short one-line description."
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
| `tags` | array of strings | No | Display-only labels (no tag index pages) |
| `links` | array of `{label, url}` | No | External links (GitHub, demo, docs, etc.) |

---

## Output Specification

### Directory Structure

```
<output_dir>/         # default: public/
  index.html          # About page
  style.css           # Copied from design/
  assets/             # Copied from assets/ input directory
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
| `/projects/` | All `projects/*.md` | Project listing |
| `/projects/<slug>/` | `projects/<slug>.md` | Individual project |

Slugs are derived directly from the Markdown filename (without the `.md` extension). No additional transformation is applied.

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
  directories, then renders all Markdown content into HTML and copies assets
  to the output directory. DIR defaults to the current working directory.

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
  Starts a simple static file server for local preview. Does not watch for
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

  Creates sitegen3.toml pre-filled with placeholder values, and the expected
  input directory structure (content/, assets/) inside DIR. Fails with an
  error if sitegen3.toml already exists to avoid overwriting an existing
  site. DIR defaults to the current working directory.

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
base_url = "https://example.com"
footer = "© 2024 My Name"

[paths]
input = "content"
output = "public"
```

| Key | Type | Required | Description |
|---|---|---|---|
| `site.title` | string | Yes | Site name shown in the navigation bar |
| `site.base_url` | string | Yes | Deployed site URL (used for absolute links) |
| `site.footer` | string | No | Footer text rendered on every page |
| `paths.input` | string | No | Input content directory (default: `content`) |
| `paths.output` | string | No | Output directory (default: `public`) |

---

## Design Reference

The visual design is defined in `design/`. It must be faithfully reproduced by the Jinja2 templates and the generated CSS.

Key design properties:

- **Theme**: Dark background (`#111`) with light gray text (`#ccc`) and a sage green accent (`#5fba7d`)
- **Typography**: Monospace only — IBM Plex Mono / Fira Code / SF Mono stack
- **Layout**: Centered single-column, max-width 640px, responsive at 480px
- **Navigation**: Site title left, nav links right (`/`, `/posts/`, `/projects/`)

Design files:

| File | Purpose |
|---|---|
| `design/style.css` | Complete stylesheet — copied verbatim to output |
| `design/index.html` | About page reference |
| `design/posts.html` | Post listing reference |
| `design/post.html` | Individual post reference |
| `design/projects.html` | Project listing reference |
| `design/project.html` | Individual project reference |
