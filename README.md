# sitegen3

A static site generator for a personal website. It takes structured Markdown content
(an about page, posts, and projects), Jinja2 templates, and a TOML config, and
produces a complete static HTML/CSS site.

[acq.uy](https://acq.uy) is a site built with it.

## Features

- **Three section types** — an about page, posts, and projects, each with
  listing and detail pages.
- **TOML frontmatter** delimited by `+++`, with a Markdown body supporting fenced code
  blocks and tables.
- **Drafts** — mark any post or project `draft = true` to exclude it from both its
  page and the listings.
- **Newest-first listings**, sorted by `created_at` (ties broken by slug).
- **Per-page resilience** — a single broken file logs a warning and is skipped; the
  rest of the site still builds.
- **Zero-config defaults** — `content/` in, `public/` out, with `assets/` and
  `static/` copied through as-is.
- **Built-in preview server** for local development, using only the standard library.

## Requirements

- Python 3.12+

## Installation

### pipx (recommended)

Installs `sitegen3` as an isolated, global command you can run from any directory:

```bash
pipx install git+https://github.com/santiacq/sitegen3.git
```

### Poetry

Clone the repository and install:

```bash
git clone https://github.com/santiacq/sitegen3.git
cd sitegen3
poetry install
```

With Poetry the command lives inside the project's virtual environment, so run it with
`poetry run` from the repository, passing your site directory as an argument:

```bash
poetry run sitegen3 build ~/my-site
```

## Quickstart

```bash
sitegen3 init my-site     # scaffold a new site
cd my-site
sitegen3 build            # render content to public/
sitegen3 serve            # preview at http://127.0.0.1:8000
```

Each subcommand accepts an optional directory argument (the site root, where
`sitegen3.toml` lives) and defaults to the current working directory.

## How it works

`sitegen3` reads a site root containing your content and config, and renders a static
site into an output directory.

**Input** (defaults shown):

```
my-site/
  sitegen3.toml          # config
  content/               # paths.input
    about.md             # the about page (required)
    posts/
      my-first-post.md
    projects/
      my-project.md
    assets/              # images and other files, copied as-is
  static/                # framework files (style.css), copied to the output root
```

**Output:**

```
public/                  # paths.output
  index.html             # about page
  style.css              # from static/
  assets/                # from content/assets/
  posts/
    index.html           # post listing
    my-first-post/index.html
  projects/
    index.html           # project listing
    my-project/index.html
```

The page URLs map as follows:

| URL | Source |
|---|---|
| `/` | `content/about.md` |
| `/posts/` | all `content/posts/*.md` (newest first) |
| `/posts/<slug>/` | `content/posts/<slug>.md` |
| `/projects/` | all `content/projects/*.md` (newest first) |
| `/projects/<slug>/` | `content/projects/<slug>.md` |

The `<slug>` is derived from the filename (lowercased, spaces to hyphens,
non-alphanumerics stripped).

## Configuration

Configuration lives in `sitegen3.toml` at the site root:

```toml
[site]
title = "My Site"
footer = "© 2026 My Name"

[paths]
input = "content"
output = "public"
```

| Key | Required | Description |
|---|---|---|
| `site.title` | Yes | Site name shown in the navigation bar |
| `site.footer` | No | Footer text on every page; omitted entirely if unset |
| `paths.input` | No | Content directory (default: `content`) |
| `paths.output` | No | Output directory (default: `public`) |

## Writing content

Each Markdown file starts with TOML frontmatter between `+++` delimiters, followed by
the Markdown body.

**About page** (`content/about.md`) — an optional list of links:

```markdown
+++
[[links]]                 # optional
label = "GitHub"
url = "https://github.com/yourname"
+++

Welcome to my site. Edit this file to introduce yourself.
```

**A post** (`content/posts/hello-world.md`):

```markdown
+++
title = "Hello World"
created_at = 2026-01-01
updated_at = 2026-01-15   # optional
draft = false             # optional
+++

This is your first post.
```

**A project** (`content/projects/sample-project.md`):

```markdown
+++
title = "Sample Project"
description = "A short one-line description."
created_at = 2026-01-01
updated_at = 2026-01-15   # optional
tags = ["example"]        # optional
draft = false             # optional

[[links]]                 # optional
label = "GitHub"
url = "https://github.com/yourname/sample-project"
+++

Describe the project here.
```

### Linking assets and pages

Because each post and project is rendered into its own subdirectory
(e.g. `posts/my-post/index.html`), relative paths from the source file won't match the
output layout. Use **root-relative URLs** for assets and internal links:

```markdown
![A photo](/assets/photo.jpg)

See [my first post](/posts/hello-world/) or a [project](/projects/sample-project/).
```

## Development

Clone and install with Poetry, which sets up an editable install plus the dev tools:

```bash
git clone https://github.com/santiacq/sitegen3.git
cd sitegen3
poetry install
```

The package uses a `src/` layout, so `poetry install` is required before `pytest` can
import `sitegen3`.

If you want an always-available global `sitegen3` command that tracks your local edits
while you work, also install it editable with pipx:

```bash
pipx install --editable .
```

Before considering a change done, all four checks must pass:

```bash
poetry run ruff format .        # format
poetry run ruff check --fix .   # lint
poetry run pyright              # type check (strict)
poetry run pytest               # tests
```

## How it was built

The initial version of `sitegen3` was one-shotted using
Claude Code — specified up front, then built by the
agent in a single run with no manual intervention. Here's a writeup of how it was
done: [One-shotting a static site generator](https://acq.uy/posts/one-shotting-a-static-site-generator/).

## License

[MIT](LICENSE)
