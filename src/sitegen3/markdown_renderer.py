import markdown

_md = markdown.Markdown(
    extensions=["fenced_code", "tables", "codehilite"],
    extension_configs={"codehilite": {"guess_lang": False}},
)


def render(text: str) -> str:
    _md.reset()
    return _md.convert(text)
