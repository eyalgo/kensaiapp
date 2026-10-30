"""Integration tests of web's unreadable-data page and site for a path holding a non-text byte,
run in one process with no socket.

Checks SRS FR-8 (the answer on saved data the tracker cannot read), NFR-4 (an unreadable start
tells the person why), NFR-8 (a value enters a page as text) and AC-7 (the unreadable-data
answer). Change spec rules CP-758 (every checked request is answered as on a path with no such
byte), CP-759 (the site is built for the location as the file-name decoding gives it), CP-760
(each non-text byte is written as a backslash, an x and two lowercase hex digits, and the page
encodes as UTF-8), CP-761 (every such byte wherever it sits, every other character as it is,
markup beside it as text), CP-763 (a path with no such byte gives the page it gave before),
CP-764 (only how the location is shown changes) and CP-766 (the site for `/tmp/caf\\xe9/data`) are
what each test names. NFDR QC-11 (a test module names the rules and obligations it checks) and
QC-36 (a value enters a page through one escaping function). The expected text of every case is
written out here, independently of the code under test.
"""

from __future__ import annotations

import os

import pytest
from test_pages import parse

from web import Response, UnreadableSite, pages
from web.routes import CSS_TYPE, PAGE_POLICY

HOST = "127.0.0.1:8017"
SURROGATE_ESCAPE_BASE = 0xDC00
FIRST_NON_TEXT_BYTE = 0x80
LAST_NON_TEXT_BYTE = 0xFF
HEX_DIGITS = "0123456789abcdef"
DECODED_LOCATION = os.fsdecode(b"/tmp/caf\xe9/data")
SHOWN_LOCATION = "/tmp/caf\\xe9/data"
PAGE_BEFORE_LOCATION = "The tracker couldn't read its saved data, which is kept at "
PAGE_AFTER_LOCATION = (
    ". Nothing in it was changed or overwritten. To start fresh on purpose, "
    "follow Setting saved data aside in the setup instructions."
)


def get(location: str, target: str = "/") -> Response:
    headers = {"Host": HOST}
    return UnreadableSite(location, HOST).handle("GET", target, headers, b"")


def header(response: Response, name: str) -> str | None:
    found = [value for key, value in response.headers if key.lower() == name.lower()]
    return found[0] if found else None


def paragraph(page: str) -> str:
    (body,) = parse(page).find_all("p")
    return body.text()


def expected_paragraph(shown: str) -> str:
    return f"{PAGE_BEFORE_LOCATION}{shown}{PAGE_AFTER_LOCATION}"


def whole_page(shown: str) -> str:
    """The complete page, written out from the page served before this change, with `shown` as
    its location."""
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        "<title>The saved data can&#x27;t be read - tracker17</title>\n"
        '<link rel="stylesheet" href="/style.css">\n</head>\n<body>\n'
        '<header class="site-header"><span class="product-name">tracker17</span></header>\n'
        "<main>\n<h1>The saved data can't be read</h1>\n"
        f"<p>The tracker couldn't read its saved data, which is kept at {shown}. "
        "Nothing in it was changed or overwritten. To start fresh on purpose, "
        "follow Setting saved data aside in the setup instructions.</p>\n"
        "</main>\n</body>\n</html>\n"
    )


def assert_free_of_marker_forms(text: str) -> None:
    assert "�" not in text
    assert not any(0xDC80 <= ord(character) <= 0xDCFF for character in text)
    assert "\\udce9" not in text


def test_unreadable_site_accepts_the_original_decoded_location() -> None:
    """CP-759, CP-760, CP-766: a site built with the location as the file-name decoding gives it
    does not raise; `GET /` answers 503 with strict UTF-8 page bytes holding the four-character
    escape and no marker or replacement mark; the page builder gives the same field."""
    response = get(DECODED_LOCATION)

    assert response.status == 503
    page = response.body.decode("utf-8")
    assert paragraph(page) == expected_paragraph(SHOWN_LOCATION)
    assert f"kept at {SHOWN_LOCATION}." in page
    assert_free_of_marker_forms(page)
    built = pages.unreadable_data_page(DECODED_LOCATION)
    assert paragraph(built) == expected_paragraph(SHOWN_LOCATION)
    assert_free_of_marker_forms(built)
    built.encode("utf-8")


def byte_cases() -> list[object]:
    """Every marker from U+DC80 through U+DCFF alone, then markers beside each other and beside
    other text; the shown form of each is written out here, digit by digit."""
    cases: list[object] = []
    for byte in range(FIRST_NON_TEXT_BYTE, LAST_NON_TEXT_BYTE + 1):
        marker = chr(SURROGATE_ESCAPE_BASE + byte)
        escape = "\\x" + HEX_DIGITS[byte // 16] + HEX_DIGITS[byte % 16]
        cases.append(
            pytest.param(f"/tmp/a{marker}b/data", f"/tmp/a{escape}b/data", id=f"{byte:#04x}")
        )
    cases += [
        pytest.param("\udce9", "\\xe9", id="only-the-byte"),
        pytest.param("/tmp/\udc80x\udcff", "/tmp/\\x80x\\xff", id="at-both-ends"),
        pytest.param("/tmp/\udce9café/data", "/tmp/\\xe9café/data", id="before-valid-text"),
        pytest.param("afile/caf\udce9", "afile/caf\\xe9", id="relative-stays-relative"),
        pytest.param("/tmp/a\udce9\udcff/data", "/tmp/a\\xe9\\xff/data", id="consecutive"),
        pytest.param("/tmp/a\udce9b\udcffc/data", "/tmp/a\\xe9b\\xffc/data", id="separated"),
        pytest.param("/tmp/\udce9/\udcff/data", "/tmp/\\xe9/\\xff/data", id="two-components"),
        pytest.param("/tmp/\udce9\udce9/data", "/tmp/\\xe9\\xe9/data", id="the-same-byte-twice"),
        pytest.param("/tmp/café\udce9/data", "/tmp/café\\xe9/data", id="after-valid-text"),
        pytest.param("/tmp/a\\b\udce9\\x41/d", "/tmp/a\\b\\xe9\\x41/d", id="beside-backslashes"),
        pytest.param(
            os.fsdecode(b"/tmp/a\xe9\xff/data"), "/tmp/a\\xe9\\xff/data", id="two-byte-example"
        ),
    ]
    return cases


@pytest.mark.parametrize(("location", "shown"), byte_cases())
def test_unreadable_page_escapes_each_filename_byte_in_place(location: str, shown: str) -> None:
    """CP-760, CP-761: every marker, both endpoints included, is written as its own byte in a
    backslash, an x and two lowercase hex digits, where it stands; consecutive, separated, repeated
    and cross-component markers keep every other character in its order, on the page the builder
    gives and on the page the site serves."""
    expected = expected_paragraph(shown)

    assert paragraph(pages.unreadable_data_page(location)) == expected
    served = get(location).body.decode("utf-8")
    assert paragraph(served) == expected
    assert_free_of_marker_forms(served)


def test_unreadable_page_shows_markup_beside_byte_markers_as_text() -> None:
    """CP-761, QC-36: a `<`, a `&`, a `"`, valid non-ASCII text and a real backslash beside a
    marker are shown as that text; no element is injected and the raw page keeps the existing
    escape form."""
    location = os.fsdecode(b'/tmp/a<b>&"c\\caf\xc3\xa9\xe9/data')
    page = pages.unreadable_data_page(location)
    root = parse(page)

    assert paragraph(page) == expected_paragraph('/tmp/a<b>&"c\\café\\xe9/data')
    assert root.find_all("b") == []
    assert len(root.find_all("p")) == 1
    assert "a&lt;b&gt;&amp;&quot;c\\café\\xe9/data" in page


@pytest.mark.parametrize(
    "location",
    [
        pytest.param("/Users/sam/tracker17/data", id="plain-text"),
        pytest.param("/tmp/café/data", id="valid-non-ascii"),
        pytest.param("/tmp/a\\xe9b/data", id="literal-backslash-folder-name"),
    ],
)
def test_unreadable_page_keeps_ordinary_representations(location: str) -> None:
    """CP-763: a path with no filename-decoding marker gives the whole page it gave before, in the
    builder and in the served bytes; the expectation is the pre-change page written out here."""
    expected = whole_page(location)

    assert pages.unreadable_data_page(location) == expected
    assert get(location).body == expected.encode("utf-8")


def test_unreadable_byte_page_differs_only_in_the_location() -> None:
    """CP-758, CP-760, CP-763: the page for a path holding the byte is the same whole page, title,
    heading and sentences, and only the location's form is new."""
    expected = whole_page(SHOWN_LOCATION)

    assert pages.unreadable_data_page(DECODED_LOCATION) == expected
    assert get(DECODED_LOCATION).body == expected.encode("utf-8")


@pytest.mark.parametrize(
    "character",
    [
        pytest.param("\udc7f", id="just-below-the-range"),
        pytest.param("\udd00", id="just-above-the-range"),
        pytest.param("\ud800", id="high-surrogate"),
    ],
)
def test_unreadable_site_still_rejects_other_surrogates(character: str) -> None:
    """The scope fence: a surrogate outside U+DC80 through U+DCFF is no file-name byte, so the
    site's UTF-8 encoding still raises, and the page text keeps the character."""
    location = f"/tmp/a{character}b/data"

    with pytest.raises(UnicodeEncodeError):
        UnreadableSite(location, HOST)
    assert character in paragraph(pages.unreadable_data_page(location))


def test_unreadable_byte_path_keeps_route_policy() -> None:
    """CP-758, CP-764: on a site built for the decoded-byte location, reads at `/`, `/?x=1`,
    `/people` and `/nothing?x=1` give one 503 body with `no-store` and the page policy,
    `GET /style.css` is 200, a same-origin `POST /projects` is 303 to `/`, and the page offers no
    navigation or data control."""
    site = UnreadableSite(DECODED_LOCATION, HOST)
    headers = {"Host": HOST}
    targets = ("/", "/?x=1", "/people", "/nothing?x=1")
    reads = [site.handle("GET", target, headers, b"") for target in targets]

    assert {read.body for read in reads} == {reads[0].body}
    for read in reads:
        assert read.status == 503
        assert header(read, "Cache-Control") == "no-store"
        assert header(read, "Content-Security-Policy") == PAGE_POLICY
    sheet = site.handle("GET", "/style.css", headers, b"")
    assert sheet.status == 200
    assert header(sheet, "Content-Type") == CSS_TYPE
    post = site.handle("POST", "/projects", {**headers, "Sec-Fetch-Site": "same-origin"}, b"x=1")
    assert post.status == 303
    assert header(post, "Location") == "/"
    root = parse(reads[0].body.decode("utf-8"))
    for tag in ("a", "form", "button", "input", "select", "textarea", "nav"):
        assert root.find_all(tag) == [], tag


def test_unreadable_byte_path_answers_as_a_plain_path_does() -> None:
    """CP-758, CP-764: every request, checked or refused, gets the status and headers it gets on a
    path with no such byte, and only the page's location differs."""
    byte_site = UnreadableSite(DECODED_LOCATION, HOST)
    plain_site = UnreadableSite("/tmp/plain/data", HOST)
    own = {"Host": HOST}
    pages_read = [
        ("GET", "/", own),
        ("GET", "/people?x=1", own),
        ("HEAD", "/", own),
        ("PUT", "/", own),
    ]
    other_answers = [
        ("GET", "/style.css", own),
        ("POST", "/projects", {**own, "Sec-Fetch-Site": "same-origin"}),
        ("POST", "/projects", {**own, "Sec-Fetch-Site": "cross-site"}),
        ("POST", "/projects", own),
        ("GET", "/", {"Host": "example.com"}),
    ]

    for method, target, headers in pages_read:
        byte_answer = byte_site.handle(method, target, headers, b"")
        plain_answer = plain_site.handle(method, target, headers, b"")
        assert (byte_answer.status, byte_answer.headers) == (
            plain_answer.status,
            plain_answer.headers,
        ), (method, target)
    for method, target, headers in other_answers:
        byte_answer = byte_site.handle(method, target, headers, b"")
        plain_answer = plain_site.handle(method, target, headers, b"")
        assert byte_answer == plain_answer, (method, target, headers)
