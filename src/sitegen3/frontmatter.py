import tomllib
from typing import Any


def parse(text: str) -> tuple[dict[str, Any], str]:
    lines = text.split("\n")
    if lines[0] != "+++":
        return ({}, text)

    for i in range(1, len(lines)):
        if lines[i] == "+++":
            toml_content = "\n".join(lines[1:i])
            body = "\n".join(lines[i + 1 :])
            data = tomllib.loads(toml_content)
            return (data, body)

    raise ValueError(
        "frontmatter opening delimiter '+++' has no matching closing delimiter"
    )
