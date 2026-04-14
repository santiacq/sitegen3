# TODO

Features not included in the initial version.

## RSS Feed

Generate a `feed.xml` (Atom or RSS 2.0) in the output root, listing all published posts with title, date, and content. Useful for readers who subscribe via feed aggregators.

## Watch & Live Reload

Add a `--watch` flag to `sitegen3 serve` that monitors the input and static directories for changes, automatically rebuilds the site, and refreshes the browser. Could use `watchdog` or `inotify` for file watching and inject a small JavaScript snippet that polls or uses a WebSocket connection to trigger the reload.

## Sitemap

Generate a `sitemap.xml` in the output root following the [sitemaps.org](https://www.sitemaps.org) protocol, listing all page URLs. Helps search engine crawlers discover and index pages.
