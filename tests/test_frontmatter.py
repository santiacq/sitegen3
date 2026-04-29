import pytest

from sitegen3.frontmatter import parse


@pytest.mark.parametrize(
    "text",
    [
        "Just some markdown\nWith multiple lines\n",
        "Hello\n+++\nThis is not frontmatter\n+++\n",
        "no frontmatter at all",
        "",
        " +++\nleading space prevents recognition\n+++\n",
        "+++ \ntrailing space prevents recognition\n+++\n",
    ],
)
def test_no_frontmatter_returns_empty_dict_and_full_body(text: str) -> None:
    fm, body = parse(text)
    assert fm == {}
    assert body == text


@pytest.mark.parametrize(
    "text",
    [
        '+++\ntitle = "X"\nbody but no closing\n',
        "+++",
        "+++\n",
        "+++\nno closing here\nstill no closing",
    ],
)
def test_unterminated_frontmatter_raises_value_error(text: str) -> None:
    with pytest.raises(ValueError, match="closing"):
        parse(text)


def test_valid_frontmatter_parses_toml_and_body() -> None:
    text = '+++\ntitle = "X"\ncount = 3\n+++\nBody here\n'
    fm, body = parse(text)
    assert fm == {"title": "X", "count": 3}
    assert body == "Body here\n"


def test_body_preserves_trailing_newline() -> None:
    text = '+++\ntitle = "X"\n+++\nHello\n'
    _, body = parse(text)
    assert body == "Hello\n"


def test_empty_frontmatter_block_returns_empty_dict() -> None:
    text = "+++\n+++\nBody\n"
    fm, body = parse(text)
    assert fm == {}
    assert body == "Body\n"


def test_only_first_closing_counts_body_can_contain_plus_plus_plus() -> None:
    text = '+++\ntitle = "X"\n+++\nbody\n+++\nmore body\n'
    fm, body = parse(text)
    assert fm == {"title": "X"}
    assert body == "body\n+++\nmore body\n"


def test_body_preserves_leading_whitespace_and_embedded_html() -> None:
    text = '+++\ntitle = "X"\n+++\n  <div class="x">hi</div>\n'
    fm, body = parse(text)
    assert fm == {"title": "X"}
    assert body == '  <div class="x">hi</div>\n'


def test_no_body_after_closing_delimiter_returns_empty_body() -> None:
    text = '+++\ntitle = "X"\n+++\n'
    fm, body = parse(text)
    assert fm == {"title": "X"}
    assert body == ""


def test_no_body_and_no_trailing_newline_after_closing_delimiter() -> None:
    text = '+++\ntitle = "X"\n+++'
    fm, body = parse(text)
    assert fm == {"title": "X"}
    assert body == ""
