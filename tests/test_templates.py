from datetime import date
from pathlib import Path

import pytest

from sitegen3.exceptions import RenderError
from sitegen3.models import Link, Post, Project
from sitegen3.templates import render_template


def test_escape_contract_body_safe_and_title_escaped() -> None:
    html = render_template(
        "post.html.j2",
        context={
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
        },
    )
    assert "<p>hello</p>" in html
    assert "&lt;script&gt;" in html
    assert "<script>alert(1)</script>" not in html


def test_unknown_template_raises_render_error() -> None:
    with pytest.raises(RenderError):
        render_template("does_not_exist.html.j2", context={})


def test_base_omits_footer_when_site_footer_none() -> None:
    html = render_template(
        "about.html.j2",
        context={
            "site_title": "My Site",
            "site_footer": None,
            "active": "about",
            "page_title": "My Site",
            "body_html": "<p>hi</p>",
            "links": [],
        },
    )
    assert "<footer>" not in html


def test_base_renders_footer_when_site_footer_set() -> None:
    html = render_template(
        "about.html.j2",
        context={
            "site_title": "My Site",
            "site_footer": "© 2026",
            "active": "about",
            "page_title": "My Site",
            "body_html": "<p>hi</p>",
            "links": [],
        },
    )
    assert "<footer>" in html
    assert "© 2026" in html


def test_base_renders_favicon_link() -> None:
    html = render_template(
        "about.html.j2",
        context={
            "site_title": "My Site",
            "site_footer": None,
            "favicon": "/icon.png",
            "active": "about",
            "page_title": "My Site",
            "body_html": "<p>hi</p>",
            "links": [],
        },
    )
    assert '<link rel="icon" href="/icon.png">' in html


def test_about_renders_links_list() -> None:
    html = render_template(
        "about.html.j2",
        context={
            "site_title": "S",
            "site_footer": None,
            "active": "about",
            "page_title": "S",
            "body_html": "<p>bio</p>",
            "links": [Link(label="GitHub", url="https://example.com")],
        },
    )
    assert '<ul class="links">' in html
    assert 'href="https://example.com"' in html
    assert ">GitHub<" in html


def test_posts_listing_links_to_detail() -> None:
    html = render_template(
        "posts.html.j2",
        context={
            "site_title": "S",
            "site_footer": None,
            "active": "posts",
            "page_title": "posts — S",
            "posts": [
                Post(
                    slug="hello",
                    title="Hello",
                    created_at=date(2026, 3, 15),
                    updated_at=None,
                    draft=False,
                    body_html="",
                    source_path=Path("hello.md"),
                ),
            ],
        },
    )
    assert 'href="/posts/hello/"' in html
    assert "2026-03-15" in html
    assert ">Hello<" in html


def test_nav_active_class_applied() -> None:
    html = render_template(
        "posts.html.j2",
        context={
            "site_title": "S",
            "site_footer": None,
            "active": "posts",
            "page_title": "posts — S",
            "posts": [],
        },
    )
    assert '<a href="/posts/" class="active">posts</a>' in html
    assert '<a href="/projects/">projects</a>' in html


def test_project_listing_renders_tags_and_link() -> None:
    html = render_template(
        "projects.html.j2",
        context={
            "site_title": "S",
            "site_footer": None,
            "active": "projects",
            "page_title": "projects — S",
            "projects": [
                Project(
                    slug="thing",
                    title="Thing",
                    description="A thing",
                    created_at=date(2026, 1, 1),
                    updated_at=None,
                    draft=False,
                    tags=["python", "cli"],
                    links=[],
                    body_html="",
                    source_path=Path("thing.md"),
                ),
            ],
        },
    )
    assert 'href="/projects/thing/"' in html
    assert "A thing" in html
    assert "python · cli" in html


def test_project_detail_renders_links_and_dates() -> None:
    html = render_template(
        "project.html.j2",
        context={
            "site_title": "S",
            "site_footer": None,
            "active": "projects",
            "page_title": "Thing — S",
            "project": Project(
                slug="thing",
                title="Thing",
                description="d",
                created_at=date(2026, 1, 1),
                updated_at=date(2026, 2, 1),
                draft=False,
                tags=["go"],
                links=[Link(label="github", url="https://gh.example/x")],
                body_html="<p>body</p>",
                source_path=Path("thing.md"),
            ),
        },
    )
    assert "2026-01-01" in html
    assert "updated 2026-02-01" in html
    assert 'href="https://gh.example/x"' in html
    assert "<p>body</p>" in html
