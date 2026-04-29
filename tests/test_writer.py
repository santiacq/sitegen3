import logging
from pathlib import Path

import pytest

from sitegen3.writer import copy_assets, copy_static, wipe_output, write_page


def test_wipe_output_removes_existing_tree(tmp_path: Path) -> None:
    output_dir = tmp_path / "public"
    output_dir.mkdir()
    (output_dir / "stale.html").write_text("old", encoding="utf-8")
    nested = output_dir / "posts" / "stale"
    nested.mkdir(parents=True)
    (nested / "index.html").write_text("old", encoding="utf-8")

    wipe_output(output_dir)

    assert output_dir.is_dir()
    assert list(output_dir.iterdir()) == []


def test_wipe_output_creates_missing_directory(tmp_path: Path) -> None:
    output_dir = tmp_path / "public"

    wipe_output(output_dir)

    assert output_dir.is_dir()


def test_wipe_output_logs_when_removing(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    output_dir = tmp_path / "public"
    output_dir.mkdir()

    with caplog.at_level(logging.INFO, logger="sitegen3.writer"):
        wipe_output(output_dir)

    assert any(
        "wiping output directory" in rec.message and str(output_dir) in rec.message
        for rec in caplog.records
    )


def test_write_page_root_path(tmp_path: Path) -> None:
    write_page(tmp_path, "/", "<h1>about</h1>")

    assert (tmp_path / "index.html").read_text(encoding="utf-8") == "<h1>about</h1>"


def test_write_page_nested_path_creates_intermediate_dirs(tmp_path: Path) -> None:
    write_page(tmp_path, "/posts/foo/", "<h1>foo</h1>")

    target = tmp_path / "posts" / "foo" / "index.html"
    assert target.read_text(encoding="utf-8") == "<h1>foo</h1>"


def test_write_page_listing_path(tmp_path: Path) -> None:
    write_page(tmp_path, "/posts/", "<h1>posts</h1>")

    target = tmp_path / "posts" / "index.html"
    assert target.read_text(encoding="utf-8") == "<h1>posts</h1>"


@pytest.mark.parametrize(
    "url_path",
    ["", "posts/foo/", "/posts/foo", "posts", "/posts"],
)
def test_write_page_rejects_paths_without_leading_and_trailing_slash(
    tmp_path: Path, url_path: str
) -> None:
    with pytest.raises(ValueError, match="must start and end with '/'"):
        write_page(tmp_path, url_path, "x")


def test_copy_assets_missing_directory_logs_and_returns(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    input_dir = tmp_path / "content"
    input_dir.mkdir()
    output_dir = tmp_path / "public"
    output_dir.mkdir()

    with caplog.at_level(logging.INFO, logger="sitegen3.writer"):
        copy_assets(input_dir, output_dir)

    assert not (output_dir / "assets").exists()
    assert any("no assets/ directory" in rec.message for rec in caplog.records)


def test_copy_assets_copies_tree(tmp_path: Path) -> None:
    input_dir = tmp_path / "content"
    assets = input_dir / "assets"
    images = assets / "images"
    images.mkdir(parents=True)
    (assets / "top.txt").write_text("top", encoding="utf-8")
    (images / "photo.jpg").write_text("img", encoding="utf-8")

    output_dir = tmp_path / "public"
    output_dir.mkdir()

    copy_assets(input_dir, output_dir)

    assert (output_dir / "assets" / "top.txt").read_text(encoding="utf-8") == "top"
    assert (output_dir / "assets" / "images" / "photo.jpg").read_text(
        encoding="utf-8"
    ) == "img"


def test_copy_static_missing_directory_logs_and_returns(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    root_dir = tmp_path
    output_dir = tmp_path / "public"
    output_dir.mkdir()

    with caplog.at_level(logging.INFO, logger="sitegen3.writer"):
        copy_static(root_dir, output_dir)

    assert any("no static/ directory" in rec.message for rec in caplog.records)


def test_copy_static_copies_files_to_output_root(tmp_path: Path) -> None:
    root_dir = tmp_path
    static = root_dir / "static"
    static.mkdir()
    (static / "style.css").write_text("body{}", encoding="utf-8")

    output_dir = root_dir / "public"
    output_dir.mkdir()

    copy_static(root_dir, output_dir)

    assert (output_dir / "style.css").read_text(encoding="utf-8") == "body{}"
