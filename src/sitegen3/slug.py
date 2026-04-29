import re

_ALLOWED = re.compile(r"[^a-z0-9-]")
_HYPHENS = re.compile(r"-+")


def slugify(name: str) -> str:
    name = name.lower()
    name = name.replace(" ", "-")
    name = _ALLOWED.sub("", name)
    name = _HYPHENS.sub("-", name)
    return name.strip("-")
