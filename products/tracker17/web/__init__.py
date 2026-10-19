"""The browser-facing part: pages, the request path, and the listener on the loopback address.

Imports only `application` (and `errors`); every value it shows comes from the tracker it is given.
"""

from web.listener import AddressTaken, Listener, listen
from web.routes import Response, Site

__all__ = ["AddressTaken", "Listener", "Response", "Site", "listen"]
