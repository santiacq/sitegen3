from pathlib import Path

import pytest

from sitegen3.discovery import find_about, find_posts, find_projects
from sitegen3.exceptions import DiscoveryError


def test_find_about_returns_path_when_present(tmp_path: Path) -> None:
    about = tmp_path / "about.md"
    about.write_text("body", encoding="utf-8")

    assert find_about(tmp_path) == about


def test_find_about_raises_when_missing(tmp_path: Path) -> None:
    with pytest.raises(DiscoveryError, match="about.md"):
        find_about(tmp_path)


def test_find_about_raises_when_directory_not_file(tmp_path: Path) -> None:
    (tmp_path / "about.md").mkdir()

    with pytest.raises(DiscoveryError, match="about.md"):
        find_about(tmp_path)


def test_find_posts_missing_directory_returns_empty(tmp_path: Path) -> None:
    assert find_posts(tmp_path) == []


def test_find_posts_empty_directory_returns_empty(tmp_path: Path) -> None:
    (tmp_path / "posts").mkdir()
    assert find_posts(tmp_path) == []


def test_find_posts_returns_only_markdown_files(tmp_path: Path) -> None:
    posts_dir = tmp_path / "posts"
    posts_dir.mkdir()
    (posts_dir / "first.md").write_text("a", encoding="utf-8")
    (posts_dir / "second.md").write_text("b", encoding="utf-8")
    (posts_dir / "ignored.txt").write_text("c", encoding="utf-8")
    (posts_dir / "README").write_text("d", encoding="utf-8")
    nested = posts_dir / "nested"
    nested.mkdir()
    (nested / "deep.md").write_text("e", encoding="utf-8")

    found = sorted(find_posts(tmp_path))
    expected = sorted([posts_dir / "first.md", posts_dir / "second.md"])

    assert found == expected


def test_find_projects_missing_directory_returns_empty(tmp_path: Path) -> None:
    assert find_projects(tmp_path) == []


def test_find_projects_empty_directory_returns_empty(tmp_path: Path) -> None:
    (tmp_path / "projects").mkdir()
    assert find_projects(tmp_path) == []


def test_find_projects_returns_only_markdown_files(tmp_path: Path) -> None:
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    (projects_dir / "alpha.md").write_text("a", encoding="utf-8")
    (projects_dir / "beta.md").write_text("b", encoding="utf-8")
    (projects_dir / "notes.rst").write_text("c", encoding="utf-8")
    nested = projects_dir / "subdir"
    nested.mkdir()
    (nested / "skip.md").write_text("d", encoding="utf-8")

    found = sorted(find_projects(tmp_path))
    expected = sorted([projects_dir / "alpha.md", projects_dir / "beta.md"])

    assert found == expected
