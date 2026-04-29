from datetime import date
from pathlib import Path

import pytest

from sitegen3.exceptions import LoaderError
from sitegen3.loader import load_about, load_post, load_project
from sitegen3.models import Link


def _write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


# ----- about -----


def test_load_about_no_frontmatter_returns_empty_links(tmp_path: Path) -> None:
    path = _write(tmp_path, "about.md", "Just a body.\n")

    about = load_about(path)

    assert about.links == []
    assert "Just a body." in about.body_html


def test_load_about_links_absent_defaults_to_empty(tmp_path: Path) -> None:
    text = "+++\n+++\nbio\n"
    path = _write(tmp_path, "about.md", text)

    about = load_about(path)

    assert about.links == []


def test_load_about_parses_links(tmp_path: Path) -> None:
    text = (
        "+++\n"
        '[[links]]\nlabel = "GitHub"\nurl = "https://github.com/u"\n'
        '[[links]]\nlabel = "Email"\nurl = "mailto:a@b.c"\n'
        "+++\n"
        "Bio body.\n"
    )
    path = _write(tmp_path, "about.md", text)

    about = load_about(path)

    assert about.links == [
        Link(label="GitHub", url="https://github.com/u"),
        Link(label="Email", url="mailto:a@b.c"),
    ]
    assert "<p>Bio body.</p>" in about.body_html


def test_load_about_renders_markdown_body(tmp_path: Path) -> None:
    text = "+++\n+++\nHello **world**\n"
    path = _write(tmp_path, "about.md", text)

    about = load_about(path)

    assert "<strong>world</strong>" in about.body_html


def test_load_about_links_wrong_type_raises(tmp_path: Path) -> None:
    text = '+++\nlinks = "not an array"\n+++\n'
    path = _write(tmp_path, "about.md", text)

    with pytest.raises(LoaderError, match=r"'links' must be an array"):
        load_about(path)


def test_load_about_link_entry_missing_url_raises(tmp_path: Path) -> None:
    text = '+++\n[[links]]\nlabel = "GitHub"\n+++\n'
    path = _write(tmp_path, "about.md", text)

    with pytest.raises(LoaderError, match=r"links\[0\]"):
        load_about(path)


# ----- posts -----


def test_load_post_valid(tmp_path: Path) -> None:
    text = (
        "+++\n"
        'title = "Hello"\n'
        "created_at = 2024-03-15\n"
        "updated_at = 2024-04-01\n"
        "+++\n"
        "Body text.\n"
    )
    path = _write(tmp_path, "Hello World.md", text)

    post = load_post(path)

    assert post.slug == "hello-world"
    assert post.title == "Hello"
    assert post.created_at == date(2024, 3, 15)
    assert post.updated_at == date(2024, 4, 1)
    assert post.draft is False
    assert "<p>Body text.</p>" in post.body_html
    assert post.source_path == path


def test_load_post_defaults(tmp_path: Path) -> None:
    text = '+++\ntitle = "Hello"\ncreated_at = 2024-03-15\n+++\nBody\n'
    path = _write(tmp_path, "hello.md", text)

    post = load_post(path)

    assert post.updated_at is None
    assert post.draft is False


def test_load_post_draft_true(tmp_path: Path) -> None:
    text = (
        "+++\n"
        'title = "Hello"\n'
        "created_at = 2024-03-15\n"
        "draft = true\n"
        "+++\n"
        "Body\n"
    )
    path = _write(tmp_path, "hello.md", text)

    post = load_post(path)

    assert post.draft is True


def test_load_post_malformed_toml_raises(tmp_path: Path) -> None:
    text = '+++\ntitle = "unterminated\n+++\nbody\n'
    path = _write(tmp_path, "hello.md", text)

    with pytest.raises(LoaderError):
        load_post(path)


def test_load_post_unterminated_frontmatter_raises(tmp_path: Path) -> None:
    text = '+++\ntitle = "Hello"\ncreated_at = 2024-03-15\nno closing\n'
    path = _write(tmp_path, "hello.md", text)

    with pytest.raises(LoaderError, match=r"closing delimiter"):
        load_post(path)


def test_load_post_missing_title_raises(tmp_path: Path) -> None:
    text = "+++\ncreated_at = 2024-03-15\n+++\nbody\n"
    path = _write(tmp_path, "hello.md", text)

    with pytest.raises(LoaderError, match=r"'title' is required"):
        load_post(path)


def test_load_post_missing_created_at_raises(tmp_path: Path) -> None:
    text = '+++\ntitle = "Hello"\n+++\nbody\n'
    path = _write(tmp_path, "hello.md", text)

    with pytest.raises(LoaderError, match=r"'created_at' is required"):
        load_post(path)


def test_load_post_created_at_as_string_raises(tmp_path: Path) -> None:
    text = '+++\ntitle = "Hello"\ncreated_at = "2024-03-15"\n+++\nbody\n'
    path = _write(tmp_path, "hello.md", text)

    with pytest.raises(LoaderError, match=r"'created_at' must be a date"):
        load_post(path)


def test_load_post_created_at_as_datetime_raises(tmp_path: Path) -> None:
    text = '+++\ntitle = "Hello"\ncreated_at = 2024-03-15T10:00:00\n+++\nbody\n'
    path = _write(tmp_path, "hello.md", text)

    with pytest.raises(LoaderError, match=r"got datetime"):
        load_post(path)


def test_load_post_title_wrong_type_raises(tmp_path: Path) -> None:
    text = "+++\ntitle = 42\ncreated_at = 2024-03-15\n+++\n"
    path = _write(tmp_path, "hello.md", text)

    with pytest.raises(LoaderError, match=r"'title' must be a string"):
        load_post(path)


def test_load_post_updated_at_as_datetime_raises(tmp_path: Path) -> None:
    text = (
        "+++\n"
        'title = "Hello"\n'
        "created_at = 2024-03-15\n"
        "updated_at = 2024-04-01T00:00:00\n"
        "+++\n"
    )
    path = _write(tmp_path, "hello.md", text)

    with pytest.raises(LoaderError, match=r"got datetime"):
        load_post(path)


# ----- projects -----


def test_load_project_valid(tmp_path: Path) -> None:
    text = (
        "+++\n"
        'title = "P"\n'
        'description = "desc"\n'
        "created_at = 2024-03-15\n"
        'tags = ["python", "cli"]\n'
        "[[links]]\n"
        'label = "GH"\n'
        'url = "https://github.com/u/p"\n'
        "+++\n"
        "Body\n"
    )
    path = _write(tmp_path, "My Project.md", text)

    project = load_project(path)

    assert project.slug == "my-project"
    assert project.title == "P"
    assert project.description == "desc"
    assert project.created_at == date(2024, 3, 15)
    assert project.updated_at is None
    assert project.draft is False
    assert project.tags == ["python", "cli"]
    assert project.links == [Link(label="GH", url="https://github.com/u/p")]
    assert "<p>Body</p>" in project.body_html


def test_load_project_defaults_when_optional_absent(tmp_path: Path) -> None:
    text = (
        "+++\n"
        'title = "P"\n'
        'description = "desc"\n'
        "created_at = 2024-03-15\n"
        "+++\n"
    )
    path = _write(tmp_path, "p.md", text)

    project = load_project(path)

    assert project.tags == []
    assert project.links == []
    assert project.updated_at is None
    assert project.draft is False


def test_load_project_missing_description_raises(tmp_path: Path) -> None:
    text = '+++\ntitle = "P"\ncreated_at = 2024-03-15\n+++\n'
    path = _write(tmp_path, "p.md", text)

    with pytest.raises(LoaderError, match=r"'description' is required"):
        load_project(path)


def test_load_project_tags_wrong_top_level_type_raises(tmp_path: Path) -> None:
    text = (
        "+++\n"
        'title = "P"\n'
        'description = "d"\n'
        "created_at = 2024-03-15\n"
        'tags = "single"\n'
        "+++\n"
    )
    path = _write(tmp_path, "p.md", text)

    with pytest.raises(LoaderError, match=r"'tags' must be an array"):
        load_project(path)


@pytest.mark.parametrize(
    "tags_value",
    [
        "tags = [1, 2]",
        'tags = ["ok", 3]',
    ],
)
def test_load_project_tags_non_string_entry_raises(
    tmp_path: Path, tags_value: str
) -> None:
    text = (
        "+++\n"
        'title = "P"\n'
        'description = "d"\n'
        "created_at = 2024-03-15\n"
        f"{tags_value}\n"
        "+++\n"
    )
    path = _write(tmp_path, "p.md", text)

    with pytest.raises(LoaderError, match=r"tags\[\d+\] must be a string"):
        load_project(path)


def test_load_project_links_entry_not_table_raises(tmp_path: Path) -> None:
    text = (
        "+++\n"
        'title = "P"\n'
        'description = "d"\n'
        "created_at = 2024-03-15\n"
        'links = ["nope"]\n'
        "+++\n"
    )
    path = _write(tmp_path, "p.md", text)

    with pytest.raises(LoaderError, match=r"links\[0\]"):
        load_project(path)


def test_load_project_draft_true(tmp_path: Path) -> None:
    text = (
        "+++\n"
        'title = "P"\n'
        'description = "d"\n'
        "created_at = 2024-03-15\n"
        "draft = true\n"
        "+++\n"
    )
    path = _write(tmp_path, "p.md", text)

    project = load_project(path)

    assert project.draft is True
