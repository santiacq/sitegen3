import logging
import shutil
from pathlib import Path

log = logging.getLogger(__name__)


def wipe_output(output_dir: Path) -> None:
    if output_dir.exists():
        log.info("wiping output directory: %s", output_dir)
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)


def write_page(output_dir: Path, url_path: str, html: str) -> None:
    if not (url_path.startswith("/") and url_path.endswith("/")):
        raise ValueError(f"url_path must start and end with '/', got {url_path!r}")
    relative = url_path.strip("/")
    target = (
        output_dir / relative / "index.html" if relative else output_dir / "index.html"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")


def copy_assets(input_dir: Path, output_dir: Path) -> None:
    source = input_dir / "assets"
    if not source.is_dir():
        log.info("no assets/ directory, skipping")
        return
    shutil.copytree(source, output_dir / "assets", dirs_exist_ok=True)


def copy_static(root_dir: Path, output_dir: Path) -> None:
    source = root_dir / "static"
    if not source.is_dir():
        log.info("no static/ directory, skipping")
        return
    shutil.copytree(source, output_dir, dirs_exist_ok=True)
