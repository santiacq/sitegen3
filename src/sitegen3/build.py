import logging
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Protocol

from sitegen3.config import load_config
from sitegen3.discovery import find_about, find_posts, find_projects
from sitegen3.exceptions import DiscoveryError, PageError
from sitegen3.loader import load_about, load_post, load_project
from sitegen3.models import Post, Project
from sitegen3.templates import render_template
from sitegen3.writer import copy_assets, copy_static, wipe_output, write_page

log = logging.getLogger(__name__)


class _Sluggable(Protocol):
    @property
    def slug(self) -> str: ...
    @property
    def source_path(self) -> Path: ...


def build(root_dir: Path) -> None:
    config = load_config(root_dir)
    log.info("building site: input=%s output=%s", config.input_dir, config.output_dir)

    wipe_output(config.output_dir)

    about_path = find_about(config.input_dir)
    about = load_about(about_path)

    rendered = 0
    skipped = 0

    posts: list[Post] = []
    for path in find_posts(config.input_dir):
        try:
            posts.append(load_post(path))
        except PageError as e:
            log.warning("skipping %s: %s", path, e)
            skipped += 1

    projects: list[Project] = []
    for path in find_projects(config.input_dir):
        try:
            projects.append(load_project(path))
        except PageError as e:
            log.warning("skipping %s: %s", path, e)
            skipped += 1

    posts = [p for p in posts if not p.draft]
    projects = [p for p in projects if not p.draft]

    _check_slug_collisions(posts, "post")
    _check_slug_collisions(projects, "project")

    posts.sort(key=lambda p: (-p.created_at.toordinal(), p.slug))
    projects.sort(key=lambda p: (-p.created_at.toordinal(), p.slug))

    about_ctx: dict[str, Any] = {
        "site_title": config.site_title,
        "site_footer": config.site_footer,
        "active": "about",
        "page_title": config.site_title,
        "body_html": about.body_html,
        "links": about.links,
    }
    about_html = render_template("about.html.j2", about_ctx)
    write_page(config.output_dir, "/", about_html)
    rendered += 1

    for post in posts:
        try:
            post_ctx: dict[str, Any] = {
                "site_title": config.site_title,
                "site_footer": config.site_footer,
                "active": "posts",
                "page_title": f"{post.title} — {config.site_title}",
                "post": post,
            }
            post_html = render_template("post.html.j2", post_ctx)
            write_page(config.output_dir, f"/posts/{post.slug}/", post_html)
        except PageError as e:
            log.warning("skipping %s: %s", post.source_path, e)
            skipped += 1
            continue
        log.debug("rendered post: %s → /posts/%s/", post.source_path, post.slug)
        rendered += 1

    posts_listing_ctx: dict[str, Any] = {
        "site_title": config.site_title,
        "site_footer": config.site_footer,
        "active": "posts",
        "page_title": f"posts — {config.site_title}",
        "posts": posts,
    }
    posts_listing_html = render_template("posts.html.j2", posts_listing_ctx)
    write_page(config.output_dir, "/posts/", posts_listing_html)
    rendered += 1

    for project in projects:
        try:
            project_ctx: dict[str, Any] = {
                "site_title": config.site_title,
                "site_footer": config.site_footer,
                "active": "projects",
                "page_title": f"{project.title} — {config.site_title}",
                "project": project,
            }
            project_html = render_template("project.html.j2", project_ctx)
            write_page(config.output_dir, f"/projects/{project.slug}/", project_html)
        except PageError as e:
            log.warning("skipping %s: %s", project.source_path, e)
            skipped += 1
            continue
        log.debug(
            "rendered project: %s → /projects/%s/",
            project.source_path,
            project.slug,
        )
        rendered += 1

    projects_listing_ctx: dict[str, Any] = {
        "site_title": config.site_title,
        "site_footer": config.site_footer,
        "active": "projects",
        "page_title": f"projects — {config.site_title}",
        "projects": projects,
    }
    projects_listing_html = render_template("projects.html.j2", projects_listing_ctx)
    write_page(config.output_dir, "/projects/", projects_listing_html)
    rendered += 1

    copy_assets(config.input_dir, config.output_dir)
    copy_static(config.root_dir, config.output_dir)

    log.info("build complete: rendered=%d skipped=%d", rendered, skipped)


def _check_slug_collisions(items: Iterable[_Sluggable], kind: str) -> None:
    seen: dict[str, Path] = {}
    for item in items:
        if item.slug in seen:
            raise DiscoveryError(
                f"{kind} slug collision: {seen[item.slug]} and "
                f"{item.source_path} both normalize to {item.slug}"
            )
        seen[item.slug] = item.source_path
