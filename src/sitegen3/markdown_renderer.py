import markdown

_md = markdown.Markdown(extensions=["fenced_code", "tables"])


def render(text: str) -> str:
    _md.reset()
    return _md.convert(text)
