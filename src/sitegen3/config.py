import logging
import tomllib
from pathlib import Path
from typing import Any, cast

from sitegen3.exceptions import ConfigError
from sitegen3.models import Config

log = logging.getLogger(__name__)


def load_config(root_dir: Path) -> Config:
    root_dir = root_dir.resolve()
    config_path = root_dir / "sitegen3.toml"
    if not config_path.is_file():
        raise ConfigError(f"sitegen3.toml not found at {config_path}")

    with config_path.open("rb") as fp:
        data: dict[str, Any] = tomllib.load(fp)

    site_raw: Any = data.get("site")
    if not isinstance(site_raw, dict):
        raise ConfigError("missing required [site] table in sitegen3.toml")
    site = cast(dict[str, Any], site_raw)

    title: Any = site.get("title")
    if not isinstance(title, str):
        raise ConfigError("missing required field 'site.title' in sitegen3.toml")

    footer_raw: Any = site.get("footer")
    if footer_raw is not None and not isinstance(footer_raw, str):
        raise ConfigError("'site.footer' must be a string if present")
    site_footer: str | None = footer_raw

    favicon_raw: Any = site.get("favicon", "/favicon.ico")
    if not isinstance(favicon_raw, str):
        raise ConfigError("'site.favicon' must be a string if present")
    site_favicon: str = favicon_raw

    description_raw: Any = site.get("description")
    if description_raw is not None and not isinstance(description_raw, str):
        raise ConfigError("'site.description' must be a string if present")
    site_description: str | None = description_raw

    paths_raw: Any = data.get("paths", {})
    if not isinstance(paths_raw, dict):
        raise ConfigError("[paths] must be a table if present")
    paths = cast(dict[str, Any], paths_raw)

    input_value: Any = paths.get("input", "content")
    if not isinstance(input_value, str):
        raise ConfigError("'paths.input' must be a string")
    output_value: Any = paths.get("output", "public")
    if not isinstance(output_value, str):
        raise ConfigError("'paths.output' must be a string")

    input_dir = (root_dir / input_value).resolve()
    output_dir = (root_dir / output_value).resolve()

    if not input_dir.is_dir():
        raise ConfigError(f"input directory does not exist: {input_dir}")

    return Config(
        site_title=title,
        site_footer=site_footer,
        site_favicon=site_favicon,
        site_description=site_description,
        root_dir=root_dir,
        input_dir=input_dir,
        output_dir=output_dir,
    )
