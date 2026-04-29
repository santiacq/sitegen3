import logging
import shutil
from importlib.resources import as_file, files
from pathlib import Path

from sitegen3.exceptions import InitError

log = logging.getLogger(__name__)


def init(root_dir: Path) -> None:
    if (root_dir / "sitegen3.toml").exists():
        raise InitError(f"sitegen3.toml already exists in {root_dir}")

    scaffold = files("sitegen3") / "scaffold"
    with as_file(scaffold) as scaffold_path:
        shutil.copytree(scaffold_path, root_dir, dirs_exist_ok=True)

    log.info("initialized site at %s", root_dir)
