# TODO

Features not included in the initial version.

## RSS Feed

Generate a `feed.xml` (Atom or RSS 2.0) in the output root, listing all published posts with title, date, and content. Useful for readers who subscribe via feed aggregators.

## File Watching

Add a `--watch` flag to `sitegen3 build` (or `sitegen3 serve`) that monitors the input and static directories for changes and automatically rebuilds the site. Could use `watchdog` or `inotify`.

## Sitemap

Generate a `sitemap.xml` in the output root following the [sitemaps.org](https://www.sitemaps.org) protocol, listing all page URLs. Helps search engine crawlers discover and index pages.
