from pathlib import Path

import pytest

from sitegen3.config import load_config
from sitegen3.exceptions import ConfigError


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def test_load_config_happy_path(tmp_path: Path) -> None:
    _write(
        tmp_path / "sitegen3.toml",
        """
[site]
title = "My Site"
footer = "© 2026"

[paths]
input = "src_content"
output = "out"
""",
    )
    (tmp_path / "src_content").mkdir()

    config = load_config(tmp_path)

    assert config.site_title == "My Site"
    assert config.site_footer == "© 2026"
    assert config.root_dir == tmp_path.resolve()
    assert config.input_dir == (tmp_path / "src_content").resolve()
    assert config.output_dir == (tmp_path / "out").resolve()
    assert config.input_dir.is_absolute()
    assert config.output_dir.is_absolute()


def test_load_config_defaults_paths(tmp_path: Path) -> None:
    _write(
        tmp_path / "sitegen3.toml",
        """
[site]
title = "Defaults Site"
""",
    )
    (tmp_path / "content").mkdir()

    config = load_config(tmp_path)

    assert config.site_title == "Defaults Site"
    assert config.site_footer is None
    assert config.input_dir == (tmp_path / "content").resolve()
    assert config.output_dir == (tmp_path / "public").resolve()


def test_load_config_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="sitegen3.toml not found"):
        load_config(tmp_path)


def test_load_config_missing_site_title(tmp_path: Path) -> None:
    _write(
        tmp_path / "sitegen3.toml",
        """
[site]
footer = "only footer"
""",
    )
    (tmp_path / "content").mkdir()

    with pytest.raises(ConfigError, match="site.title"):
        load_config(tmp_path)


def test_load_config_missing_site_table(tmp_path: Path) -> None:
    _write(tmp_path / "sitegen3.toml", '[paths]\ninput = "content"\n')
    (tmp_path / "content").mkdir()

    with pytest.raises(ConfigError, match=r"\[site\]"):
        load_config(tmp_path)


def test_load_config_missing_input_dir(tmp_path: Path) -> None:
    _write(
        tmp_path / "sitegen3.toml",
        """
[site]
title = "X"
""",
    )

    with pytest.raises(ConfigError, match="input directory does not exist"):
        load_config(tmp_path)


def test_load_config_unknown_keys_ignored(tmp_path: Path) -> None:
    _write(
        tmp_path / "sitegen3.toml",
        """
[site]
title = "Y"
unknown_field = "ignored"

[unknown_table]
foo = "bar"
""",
    )
    (tmp_path / "content").mkdir()

    config = load_config(tmp_path)
    assert config.site_title == "Y"


def test_load_config_resolves_relative_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(
        tmp_path / "sitegen3.toml",
        """
[site]
title = "Z"
""",
    )
    (tmp_path / "content").mkdir()

    monkeypatch.chdir(tmp_path)
    config = load_config(Path("."))

    assert config.root_dir == tmp_path.resolve()
    assert config.root_dir.is_absolute()
