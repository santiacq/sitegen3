import logging
import shutil
from pathlib import Path

import pytest

from sitegen3.build import build
from sitegen3.exceptions import DiscoveryError

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "sample_site"


def _copy_fixture(tmp_path: Path) -> Path:
    site = tmp_path / "site"
    shutil.copytree(FIXTURE_ROOT, site)
    return site


def test_build_fixture_site_produces_expected_output_tree(tmp_path: Path) -> None:
    site = _copy_fixture(tmp_path)

    build(site)

    public = site / "public"
    assert (public / "index.html").is_file()
    assert (public / "posts" / "index.html").is_file()
    assert (public / "posts" / "hello-world" / "index.html").is_file()
    assert (public / "posts" / "older-post" / "index.html").is_file()
    assert not (public / "posts" / "draft-post").exists()
    assert not (public / "posts" / "broken").exists()
    assert (public / "projects" / "index.html").is_file()
    assert (public / "projects" / "sample" / "index.html").is_file()
    assert (public / "style.css").is_file()

    listing = (public / "posts" / "index.html").read_text(encoding="utf-8")
    hello_idx = listing.find("hello-world")
    older_idx = listing.find("older-post")
    assert hello_idx != -1
    assert older_idx != -1
    assert hello_idx < older_idx


def test_build_resilience_broken_post_logs_warning_and_continues(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    site = _copy_fixture(tmp_path)

    with caplog.at_level(logging.WARNING, logger="sitegen3.build"):
        build(site)

    assert any(
        rec.levelno == logging.WARNING and "broken.md" in rec.getMessage()
        for rec in caplog.records
    )
    assert (site / "public" / "posts" / "hello-world" / "index.html").is_file()


def test_build_slug_collision_is_fatal(tmp_path: Path) -> None:
    site = _copy_fixture(tmp_path)
    duplicate = site / "content" / "posts" / "Hello World.md"
    duplicate.write_text(
        '+++\ntitle = "Duplicate"\ncreated_at = 2026-04-01\n+++\n\nbody\n',
        encoding="utf-8",
    )

    with pytest.raises(DiscoveryError, match="slug collision"):
        build(site)


def test_build_missing_about_is_fatal(tmp_path: Path) -> None:
    site = _copy_fixture(tmp_path)
    (site / "content" / "about.md").unlink()

    with pytest.raises(DiscoveryError, match="about.md"):
        build(site)
