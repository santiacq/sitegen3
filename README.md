# sitegen3

A static site generator for a personal website. Takes structured Markdown content (about page, posts, projects), Jinja2 templates, and a TOML config, and produces a static HTML/CSS site.

## Quickstart

```
sitegen3 init my-site     # scaffold a new site
cd my-site
sitegen3 build            # render content to public/
sitegen3 serve            # preview at http://127.0.0.1:8000
```

Each subcommand accepts an optional directory argument (defaults to the current working directory). Configuration lives in `sitegen3.toml` at the site root.
