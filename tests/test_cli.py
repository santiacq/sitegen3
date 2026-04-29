import logging
from pathlib import Path

import pytest

from sitegen3 import build as build_module
from sitegen3 import cli
from sitegen3 import init_cmd as init_cmd_module
from sitegen3 import serve as serve_module
from sitegen3.exceptions import ConfigError


def test_main_dispatches_build(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[Path] = []

    def fake_build(root_dir: Path) -> None:
        calls.append(root_dir)

    monkeypatch.setattr(build_module, "build", fake_build)
    monkeypatch.setattr("sys.argv", ["sitegen3", "build", "/some/dir"])

    cli.main()

    assert calls == [Path("/some/dir")]


def test_main_dispatches_build_default_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[Path] = []

    def fake_build(root_dir: Path) -> None:
        calls.append(root_dir)

    monkeypatch.setattr(build_module, "build", fake_build)
    monkeypatch.setattr("sys.argv", ["sitegen3", "build"])

    cli.main()

    assert calls == [Path(".")]


def test_main_dispatches_serve_with_port(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[Path, int]] = []

    def fake_serve(root_dir: Path, port: int) -> None:
        calls.append((root_dir, port))

    monkeypatch.setattr(serve_module, "serve", fake_serve)
    monkeypatch.setattr("sys.argv", ["sitegen3", "serve", "--port", "9000"])

    cli.main()

    assert calls == [(Path("."), 9000)]


def test_main_dispatches_serve_default_port(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[Path, int]] = []

    def fake_serve(root_dir: Path, port: int) -> None:
        calls.append((root_dir, port))

    monkeypatch.setattr(serve_module, "serve", fake_serve)
    monkeypatch.setattr("sys.argv", ["sitegen3", "serve"])

    cli.main()

    assert calls == [(Path("."), 8000)]


def test_main_dispatches_init(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[Path] = []

    def fake_init(root_dir: Path) -> None:
        calls.append(root_dir)

    monkeypatch.setattr(init_cmd_module, "init", fake_init)
    monkeypatch.setattr("sys.argv", ["sitegen3", "init"])

    cli.main()

    assert calls == [Path(".")]


def test_main_exits_1_on_sitegen_error(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def fake_build(root_dir: Path) -> None:
        raise ConfigError("boom")

    monkeypatch.setattr(build_module, "build", fake_build)
    monkeypatch.setattr("sys.argv", ["sitegen3", "build"])

    with (
        caplog.at_level(logging.ERROR, logger="sitegen3.cli"),
        pytest.raises(SystemExit) as exc_info,
    ):
        cli.main()

    assert exc_info.value.code == 1
    assert any(
        record.levelno == logging.ERROR and "boom" in record.getMessage()
        for record in caplog.records
    )
