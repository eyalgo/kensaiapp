"""Integration tests of web's unreadable-mode request path, run in one process with no socket.

Checks the answers a tracker gives when it started on saved data it could not read (SDD § 6 S-8):
change spec rules CP-718 (one page for every checked request, 503, `no-store`), CP-719 (the
stylesheet stays), CP-720 (a checked POST is sent back to the page and acts on nothing), CP-721
(the request check runs first and shows nothing), CP-722 (the page policy on every answer and no
cookie) and CP-724 (the startup location is the only thing the handler holds), with NFDR QC-7,
QC-8, QC-31 to QC-34 and QC-36.
"""

from __future__ import annotations

import pytest

from web import Response, UnreadableSite, pages
from web.routes import CSS_TYPE, HTML_TYPE, PAGE_POLICY, STYLESHEET_FILE

HOST = "127.0.0.1:8017"
LOCATION = "/Users/sam/copy/products/tracker17/data"
OTHER_LOCATION = "/Users/sam/elsewhere/data"
PAGE_BYTES = pages.unreadable_data_page(LOCATION).encode("utf-8")
METHODS = ("GET", "HEAD", "POST", "PUT", "DELETE", "PATCH", "OPTIONS")
UNSAFE_METHODS = tuple(method for method in METHODS if method != "POST")
TARGETS = (
    "/",
    "/people",
    "/tasks",
    "/projects/1",
    "/projects/1/summary",
    "/tasks/1",
    "/tasks/1/delete",
    "/projects",
    "/nothing",
    "/nothing?x=1&needle=value",
    "/people?name=needle",
)
BODIES = (b"", b"name=needle", b"\xff\xfe\x00 not text", b"%zz=%")
WRONG_HOSTS = ({"Host": "example.com"}, {"Host": "127.0.0.1:9999"}, {})
MARKS_FROM_ANOTHER_SITE = ("cross-site", "same-site")


def handler() -> UnreadableSite:
    return UnreadableSite(LOCATION, HOST)


def request(
    method: str,
    target: str,
    *,
    mark: str | None = None,
    body: bytes = b"",
    site: UnreadableSite | None = None,
) -> Response:
    headers = {"Host": HOST}
    if mark is not None:
        headers["Sec-Fetch-Site"] = mark
    return (site or handler()).handle(method, target, headers, body)


def header(response: Response, name: str) -> str | None:
    found = [value for key, value in response.headers if key.lower() == name.lower()]
    return found[0] if found else None


def test_checked_unreadable_reads_share_one_representation() -> None:
    """CP-718: every checked non-POST method at every address gets the same 503 page bytes."""
    site = handler()
    for method in UNSAFE_METHODS:
        for target in TARGETS:
            for body in BODIES:
                response = request(method, target, body=body, site=site)
                where = (method, target, body)
                assert response.status == 503, where
                assert response.body == PAGE_BYTES, where
                assert header(response, "Content-Type") == HTML_TYPE, where
                assert header(response, "Cache-Control") == "no-store", where
    assert b"needle" not in PAGE_BYTES


def test_only_checked_get_serves_the_stylesheet() -> None:
    """CP-719: GET /style.css is the stylesheet even with a query; HEAD there is the page."""
    stylesheet = STYLESHEET_FILE.read_bytes()
    for target in ("/style.css", "/style.css?v=2"):
        response = request("GET", target)
        assert response.status == 200
        assert response.body == stylesheet
        assert header(response, "Content-Type") == CSS_TYPE
    head = request("HEAD", "/style.css")
    assert head.status == 503
    assert head.body == PAGE_BYTES
    assert header(head, "Content-Type") == HTML_TYPE
    assert request("PUT", "/style.css").body == PAGE_BYTES


def test_checked_post_always_redirects_without_decoding_or_acting() -> None:
    """CP-720: a same-origin POST anywhere, with any body, is an empty 303 to the page."""
    site = handler()
    for target in (*TARGETS, "/style.css", "/projects/1/rename", "/operator-name"):
        for body in BODIES:
            response = request("POST", target, mark="same-origin", body=body, site=site)
            assert response.status == 303, (target, body)
            assert response.body == b"", (target, body)
            assert header(response, "Location") == "/", (target, body)
    followed = request("GET", "/", site=site)
    assert followed.status == 503
    assert followed.body == PAGE_BYTES


def test_request_refusals_precede_page_stylesheet_and_redirect() -> None:
    """CP-721: the check runs first; a refusal is an empty 403 that names no location."""
    site = handler()
    for method in METHODS:
        for target in ("/", "/style.css", "/nothing?x=1"):
            for wrong in WRONG_HOSTS:
                response = site.handle(
                    method, target, {**wrong, "Sec-Fetch-Site": "same-origin"}, b""
                )
                assert response.status == 403, (method, target, wrong)
                assert response.body == b"", (method, target, wrong)
            for mark in MARKS_FROM_ANOTHER_SITE:
                response = request(method, target, mark=mark, site=site)
                assert response.status == 403, (method, target, mark)
                assert response.body == b"", (method, target, mark)
                assert LOCATION not in repr(response.headers)
    for target in ("/", "/style.css", "/nothing", "/projects"):
        for mark in (None, "none", "cross-site", "same-site"):
            response = request("POST", target, mark=mark, site=site)
            assert response.status == 403, (target, mark)
            assert response.body == b"", (target, mark)
    for method in UNSAFE_METHODS:
        for mark in (None, "none", "same-origin"):
            assert request(method, "/people", mark=mark, site=site).status == 503, (method, mark)
    for mark in (None, "none", "same-origin"):
        assert request("GET", "/style.css", mark=mark, site=site).status == 200, mark


def test_every_unreadable_response_has_policy_and_no_cookie() -> None:
    """CP-722: 403, 303, 503 and the stylesheet carry the page policy, and none sets a cookie."""
    answers = (
        request("GET", "/", mark="cross-site"),
        request("POST", "/projects", mark="same-origin"),
        request("GET", "/people"),
        request("GET", "/style.css"),
    )
    assert [answer.status for answer in answers] == [403, 303, 503, 200]
    for answer in answers:
        assert header(answer, "Content-Security-Policy") == PAGE_POLICY
        assert "frame-ancestors 'none'" in PAGE_POLICY
        assert header(answer, "Set-Cookie") is None


def test_unreadable_handlers_keep_their_own_startup_location() -> None:
    """CP-718, CP-724: each handler answers with its own location, whatever came before."""
    first = UnreadableSite(LOCATION, HOST)
    second = UnreadableSite(OTHER_LOCATION, HOST)
    pages_seen = []
    for target, body in (("/", b""), ("/people?x=1", b"name=needle"), ("/nothing", b"")):
        pages_seen.append((request("GET", target, body=body, site=first).body, LOCATION))
        pages_seen.append((request("GET", target, body=body, site=second).body, OTHER_LOCATION))
        request("POST", "/projects", mark="same-origin", body=body, site=first)
    for body, location in pages_seen:
        assert body == pages.unreadable_data_page(location).encode("utf-8")
    assert pages_seen[0][0] != pages_seen[1][0]


@pytest.mark.parametrize("method", UNSAFE_METHODS)
def test_unreadable_handler_does_not_decode_a_body(method: str) -> None:
    """CP-720: a body that is not text changes nothing for any method; only POST redirects."""
    response = request(method, "/projects", body=b"\xff\xfe\x00")
    assert response.status == 503
    assert response.body == PAGE_BYTES
