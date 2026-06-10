from sitegen3.markdown_renderer import render


def test_render_plain_paragraph_with_emphasis() -> None:
    html = render("Hello **world**")
    assert "<p>Hello <strong>world</strong></p>" in html


def test_render_fenced_code_block() -> None:
    text = "```\nprint('hi')\n```"
    html = render(text)
    assert "<pre>" in html
    assert "<code>" in html
    assert "print(&#39;hi&#39;)" in html


def test_render_fenced_code_block_with_language_is_highlighted() -> None:
    text = "```python\ndef greet():\n    pass\n```"
    html = render(text)
    assert 'class="codehilite"' in html
    assert '<span class="k">def</span>' in html


def test_render_fenced_bash_block_is_highlighted() -> None:
    text = '```bash\n# comment\necho "hi"\n```'
    html = render(text)
    assert 'class="codehilite"' in html
    assert '<span class="c1"># comment</span>' in html


def test_render_fenced_code_block_without_language_is_not_highlighted() -> None:
    text = "```\ndef greet():\n    pass\n```"
    html = render(text)
    assert '<span class="k">' not in html


def test_render_table() -> None:
    text = "| a | b |\n|---|---|\n| 1 | 2 |\n"
    html = render(text)
    assert "<table>" in html
    assert "<th>a</th>" in html
    assert "<td>1</td>" in html


def test_render_passes_raw_html_through() -> None:
    html = render('<div class="x">hi</div>')
    assert '<div class="x">hi</div>' in html


def test_render_resets_state_between_calls() -> None:
    render("# First")
    html = render("Just a paragraph.")
    assert "<p>Just a paragraph.</p>" in html
