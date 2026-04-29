from typing import Any

from jinja2 import Environment, PackageLoader, TemplateError, select_autoescape

from sitegen3.exceptions import RenderError

_env = Environment(
    loader=PackageLoader("sitegen3", "templates"),
    autoescape=select_autoescape(enabled_extensions=("html", "html.j2")),
)


def render_template(name: str, context: dict[str, Any]) -> str:
    try:
        template = _env.get_template(name)
        return template.render(context)
    except TemplateError as e:
        raise RenderError(str(e)) from e
