"""Integration tests of web's unreadable-data page builder, read back as a browser parses it.

Checks the page a start on saved data it cannot read serves (SDD § 6 S-8, UXD UX-F11 and UX-S9):
change spec rules CP-716 (its words), CP-717 (no navigation and no data control) and CP-723 (the
location is shown as text), and NFDR QC-36 (a value enters a page through one escaping function)
and QC-57 (no Python error text). The words are the approved text of the change's content step.
"""

from __future__ import annotations

from test_pages import parse

from web import pages

LOCATION = "/Users/sam/copy/products/tracker17/data"
HOSTILE_LOCATION = '/Users/sam/<b>&"data"'
CONTROL_TAGS = ("a", "form", "button", "input", "select", "textarea", "nav")
PYTHON_ERROR_TEXT = ("Traceback", "Error", "Exception", 'File "')


def test_unreadable_page_names_the_location_and_the_setup_section() -> None:
    """CP-716: the title, the one heading and the body are the approved words."""
    root = parse(pages.unreadable_data_page(LOCATION))

    (title,) = root.find_all("title")
    assert title.text() == "The saved data can't be read - tracker17"
    (heading,) = root.find_all("h1")
    assert heading.text() == "The saved data can't be read"
    (body,) = root.find_all("p")
    assert body.text() == (
        f"The tracker couldn't read its saved data, which is kept at {LOCATION}. "
        "Nothing in it was changed or overwritten. "
        "To start fresh on purpose, follow Setting saved data aside in the setup instructions."
    )


def test_unreadable_page_offers_no_navigation_or_data_control() -> None:
    """CP-717: the product name is plain text, no element acts, one stylesheet, nothing else."""
    page = pages.unreadable_data_page(LOCATION)
    root = parse(page)

    for tag in CONTROL_TAGS:
        assert root.find_all(tag) == [], tag
    (name,) = [e for e in root.walk() if e.attrs.get("class") == "product-name"]
    assert name.text() == "tracker17"
    assert name.parent is not None and name.parent.tag != "a"
    (stylesheet,) = root.find_all("link")
    assert stylesheet.attrs == {"rel": "stylesheet", "href": "/style.css"}
    assert root.find_all("script") == []
    assert [meta for meta in root.find_all("meta") if "http-equiv" in meta.attrs] == []
    assert "Content-Security-Policy" not in page


def test_unreadable_location_is_literal_text() -> None:
    """CP-723: a location holding markup characters shows them as text and creates no markup."""
    page = pages.unreadable_data_page(HOSTILE_LOCATION)
    root = parse(page)

    (body,) = root.find_all("p")
    assert f"kept at {HOSTILE_LOCATION}." in body.text()
    assert root.find_all("b") == []
    assert "<b>" not in page
    assert "&lt;b&gt;&amp;" in page
    for text in PYTHON_ERROR_TEXT:
        assert text not in page
