import argparse
import logging
import sys
from pathlib import Path

from sitegen3 import build as build_module
from sitegen3 import init_cmd as init_cmd_module
from sitegen3 import serve as serve_module
from sitegen3.exceptions import SitegenError
from sitegen3.logging_setup import configure_logging

log = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sitegen3",
        description="Static site generator for sitegen3.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND", required=True)

    build_parser = subparsers.add_parser(
        "build",
        help="Build the site from content sources.",
        description=(
            "Build the site from content sources. Looks for sitegen3.toml in DIR "
            "to determine the input and output directories. Deletes the output "
            "directory if it exists, then renders all Markdown content into HTML "
            "and copies assets and static files to the output directory. DIR "
            "defaults to the current working directory."
        ),
    )
    build_parser.add_argument(
        "dir",
        nargs="?",
        default=".",
        metavar="DIR",
        help="Site root directory containing sitegen3.toml.",
    )
    build_parser.set_defaults(func=_dispatch_build)

    serve_parser = subparsers.add_parser(
        "serve",
        help="Serve the output directory over HTTP.",
        description=(
            "Serve the output directory over HTTP on 127.0.0.1 (localhost only). "
            "Looks for sitegen3.toml in DIR to determine which directory to "
            "serve. Starts Python's built-in http.server for local preview, "
            "bound to 127.0.0.1 so the preview is not exposed on the LAN. Does "
            "not watch for changes or reload the browser. Exits with an error "
            "if the output directory does not exist (run 'sitegen3 build' "
            "first). DIR defaults to the current working directory."
        ),
    )
    serve_parser.add_argument(
        "dir",
        nargs="?",
        default=".",
        metavar="DIR",
        help="Site root directory containing sitegen3.toml.",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on.  [default: 8000]",
    )
    serve_parser.set_defaults(func=_dispatch_serve)

    init_parser = subparsers.add_parser(
        "init",
        help="Scaffold a new site in the given directory.",
        description=(
            "Scaffold a new site in the given directory. Creates sitegen3.toml "
            "pre-filled with placeholder values, the expected input directory "
            "structure, and sample content files inside DIR. Also creates the "
            "static/ directory with style.css. Fails with an error if "
            "sitegen3.toml already exists. DIR defaults to the current working "
            "directory."
        ),
    )
    init_parser.add_argument(
        "dir",
        nargs="?",
        default=".",
        metavar="DIR",
        help="Directory to initialise.",
    )
    init_parser.set_defaults(func=_dispatch_init)

    return parser


def _dispatch_build(args: argparse.Namespace) -> None:
    build_module.build(Path(args.dir))


def _dispatch_serve(args: argparse.Namespace) -> None:
    serve_module.serve(Path(args.dir), args.port)


def _dispatch_init(args: argparse.Namespace) -> None:
    init_cmd_module.init(Path(args.dir))


def main() -> None:
    configure_logging()
    parser = _build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except SitegenError as e:
        log.error("%s", e)
        sys.exit(1)
