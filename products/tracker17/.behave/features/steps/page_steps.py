from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from behave import given
from behave.runner import Context

LOOPBACK = "127.0.0.1"
ANY_FREE_PORT = 0
PAGE_TITLE = "Behave starter"


def _page(heading: str) -> bytes:
    return (
        "<!doctype html><html><head>"
        f"<title>{PAGE_TITLE}</title></head><body><h1>{heading}</h1></body></html>"
    ).encode()


def _handler_serving(page: bytes) -> type[BaseHTTPRequestHandler]:
    class ServePage(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)

        def log_message(self, format: str, *args: object) -> None:
            pass

    return ServePage


@given('a local server that serves a page headed "{heading}"')
def a_local_server_that_serves_a_page(context: Context, heading: str) -> None:
    server = ThreadingHTTPServer((LOOPBACK, ANY_FREE_PORT), _handler_serving(_page(heading)))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def stop() -> None:
        server.shutdown()
        server.server_close()
        thread.join()

    context.add_cleanup(stop)
    context.page_url = f"http://{LOOPBACK}:{server.server_port}/"
