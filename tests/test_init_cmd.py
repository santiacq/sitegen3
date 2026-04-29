from pathlib import Path

import pytest

from sitegen3.build import build
from sitegen3.exceptions import InitError
from sitegen3.init_cmd import init


def test_init_scaffolds_expected_tree(tmp_path: Path) -> None:
    init(tmp_path)

    assert (tmp_path / "sitegen3.toml").is_file()
    assert (tmp_path / "content" / "about.md").is_file()
    assert (tmp_path / "content" / "posts" / "hello-world.md").is_file()
    assert (tmp_path / "content" / "projects" / "sample-project.md").is_file()
    assert (tmp_path / "content" / "assets").is_dir()
    assert (tmp_path / "static" / "style.css").is_file()


def test_init_refuses_when_sitegen3_toml_already_exists(tmp_path: Path) -> None:
    (tmp_path / "sitegen3.toml").write_text("", encoding="utf-8")

    with pytest.raises(InitError, match="already exists"):
        init(tmp_path)


def test_init_then_build_succeeds(tmp_path: Path) -> None:
    init(tmp_path)
    build(tmp_path)

    assert (tmp_path / "public" / "index.html").is_file()
    assert (tmp_path / "public" / "posts" / "index.html").is_file()
    assert (tmp_path / "public" / "posts" / "hello-world" / "index.html").is_file()
    assert (tmp_path / "public" / "projects" / "index.html").is_file()
    assert (
        tmp_path / "public" / "projects" / "sample-project" / "index.html"
    ).is_file()
    assert (tmp_path / "public" / "style.css").is_file()
