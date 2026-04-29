import functools
import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from sitegen3.config import load_config
from sitegen3.exceptions import ServeError

log = logging.getLogger(__name__)


def serve(root_dir: Path, port: int) -> None:
    config = load_config(root_dir)
    if not config.output_dir.is_dir():
        raise ServeError(
            f"output directory {config.output_dir} does not exist; "
            "run 'sitegen3 build' first"
        )

    handler = functools.partial(
        SimpleHTTPRequestHandler, directory=str(config.output_dir)
    )
    log.info("serving %s on http://127.0.0.1:%d", config.output_dir, port)
    HTTPServer(("127.0.0.1", port), handler).serve_forever()
