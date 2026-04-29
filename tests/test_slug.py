import pytest

from sitegen3.slug import slugify


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("My Post", "my-post"),
        ("hello   world", "hello-world"),
        ("hello, world!", "hello-world"),
        ("café-ñoño", "caf-oo"),
        ("a---b", "a-b"),
        ("-hello-", "hello"),
        ("my-post", "my-post"),
        ("", ""),
        ("!!!", ""),
    ],
)
def test_slugify(name: str, expected: str) -> None:
    assert slugify(name) == expected
