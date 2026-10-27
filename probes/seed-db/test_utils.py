from utils import slugify


def test_slugify_lowercases_and_joins_words():
    assert slugify("Hello World") == "hello-world"
