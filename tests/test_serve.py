from pathlib import Path

import pytest

from sitegen3.exceptions import ServeError
from sitegen3.serve import serve


def test_serve_raises_when_output_missing(tmp_path: Path) -> None:
    (tmp_path / "sitegen3.toml").write_text(
        """
[site]
title = "Smoke"
""",
        encoding="utf-8",
    )
    (tmp_path / "content").mkdir()

    with pytest.raises(ServeError, match="output directory"):
        serve(tmp_path, port=8000)
