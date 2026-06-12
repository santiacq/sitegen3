from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class Config:
    site_title: str
    site_footer: str | None
    site_favicon: str
    site_description: str | None
    root_dir: Path
    input_dir: Path
    output_dir: Path


@dataclass(frozen=True)
class Link:
    label: str
    url: str


@dataclass(frozen=True)
class About:
    body_html: str
    links: list[Link]


@dataclass(frozen=True)
class Post:
    slug: str
    title: str
    created_at: date
    updated_at: date | None
    draft: bool
    body_html: str
    source_path: Path


@dataclass(frozen=True)
class Project:
    slug: str
    title: str
    description: str
    created_at: date
    updated_at: date | None
    draft: bool
    tags: list[str]
    links: list[Link]
    body_html: str
    source_path: Path
