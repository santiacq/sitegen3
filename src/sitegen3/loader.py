import tomllib
from datetime import date, datetime
from pathlib import Path
from typing import Any, cast

from sitegen3.exceptions import LoaderError
from sitegen3.frontmatter import parse
from sitegen3.markdown_renderer import render
from sitegen3.models import About, Link, Post, Project
from sitegen3.slug import slugify


def load_about(path: Path) -> About:
    meta, body = _read_and_split(path)
    links = _parse_links(meta.get("links"))
    return About(body_html=render(body), links=links)


def load_post(path: Path) -> Post:
    meta, body = _read_and_split(path)
    title = _require_string(meta, "title")
    created_at = _require_date(meta, "created_at")
    updated_at = _optional_date(meta, "updated_at")
    draft = _optional_bool(meta, "draft")
    return Post(
        slug=slugify(path.stem),
        title=title,
        created_at=created_at,
        updated_at=updated_at,
        draft=draft,
        body_html=render(body),
        source_path=path,
    )


def load_project(path: Path) -> Project:
    meta, body = _read_and_split(path)
    title = _require_string(meta, "title")
    description = _require_string(meta, "description")
    created_at = _require_date(meta, "created_at")
    updated_at = _optional_date(meta, "updated_at")
    draft = _optional_bool(meta, "draft")
    tags = _parse_tags(meta.get("tags"))
    links = _parse_links(meta.get("links"))
    return Project(
        slug=slugify(path.stem),
        title=title,
        description=description,
        created_at=created_at,
        updated_at=updated_at,
        draft=draft,
        tags=tags,
        links=links,
        body_html=render(body),
        source_path=path,
    )


def _read_and_split(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    try:
        return parse(text)
    except tomllib.TOMLDecodeError as e:
        raise LoaderError(f"malformed TOML in frontmatter: {e}") from e
    except ValueError as e:
        raise LoaderError(str(e)) from e


def _require_string(meta: dict[str, Any], key: str) -> str:
    if key not in meta:
        raise LoaderError(f"'{key}' is required")
    value: Any = meta[key]
    if not isinstance(value, str):
        raise LoaderError(f"'{key}' must be a string, got {type(value).__name__}")
    return value


def _require_date(meta: dict[str, Any], key: str) -> date:
    if key not in meta:
        raise LoaderError(f"'{key}' is required")
    value: Any = meta[key]
    if isinstance(value, datetime):
        raise LoaderError(f"'{key}' must be a date (YYYY-MM-DD), got datetime")
    if type(value) is not date:
        raise LoaderError(
            f"'{key}' must be a date (YYYY-MM-DD), got {type(value).__name__}"
        )
    return value


def _optional_date(meta: dict[str, Any], key: str) -> date | None:
    if key not in meta:
        return None
    value: Any = meta[key]
    if isinstance(value, datetime):
        raise LoaderError(f"'{key}' must be a date (YYYY-MM-DD), got datetime")
    if type(value) is not date:
        raise LoaderError(
            f"'{key}' must be a date (YYYY-MM-DD), got {type(value).__name__}"
        )
    return value


def _optional_bool(meta: dict[str, Any], key: str) -> bool:
    if key not in meta:
        return False
    value: Any = meta[key]
    if not isinstance(value, bool):
        raise LoaderError(f"'{key}' must be a bool, got {type(value).__name__}")
    return value


def _parse_links(value: Any) -> list[Link]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise LoaderError(
            f"'links' must be an array of {{label, url}} tables, "
            f"got {type(value).__name__}"
        )
    items = cast(list[Any], value)
    result: list[Link] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise LoaderError(
                f"links[{index}] must be a table with 'label' and 'url' (string), "
                f"got {type(item).__name__}"
            )
        entry = cast(dict[str, Any], item)
        label: Any = entry.get("label")
        url: Any = entry.get("url")
        if not isinstance(label, str):
            raise LoaderError(
                f"links[{index}] must be a table with 'label' and 'url' (string), "
                f"got {type(label).__name__} for 'label'"
            )
        if not isinstance(url, str):
            raise LoaderError(
                f"links[{index}] must be a table with 'label' and 'url' (string), "
                f"got {type(url).__name__} for 'url'"
            )
        result.append(Link(label=label, url=url))
    return result


def _parse_tags(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise LoaderError(
            f"'tags' must be an array of strings, got {type(value).__name__}"
        )
    items = cast(list[Any], value)
    result: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, str):
            raise LoaderError(
                f"tags[{index}] must be a string, got {type(item).__name__}"
            )
        result.append(item)
    return result
