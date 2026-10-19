"""The product's single named base error.

Every typed error this product raises derives from AppError, and none derives directly from
bare Exception — that is what lets an interface layer catch this product's failures in one
clause without swallowing an unrelated exception it did not mean to (KeyboardInterrupt, a
genuine bug in the interpreter's own code).

AppError is a placeholder. Rename it after the product once this frame belongs to one.
"""

from __future__ import annotations


class AppError(Exception):
    """Base for every typed error this product raises.

    Never raised directly — each distinct failure condition gets its own subclass, so a
    caller can map the type to an outcome (an exit code, an HTTP status, a message) instead
    of parsing a string.
    """
