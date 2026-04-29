import logging
from pathlib import Path

from sitegen3.exceptions import DiscoveryError

log = logging.getLogger(__name__)


def find_about(input_dir: Path) -> Path:
    path = input_dir / "about.md"
    if not path.is_file():
        raise DiscoveryError(f"about.md not found in {input_dir}")
    return path


def find_posts(input_dir: Path) -> list[Path]:
    return _find_markdown(input_dir / "posts")


def find_projects(input_dir: Path) -> list[Path]:
    return _find_markdown(input_dir / "projects")


def _find_markdown(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return [p for p in directory.glob("*.md") if p.is_file()]
