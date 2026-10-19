"""The composition root — the only place this product wires a concrete implementation to an
abstraction. Every other module receives its collaborators through its constructor; nothing
outside this module builds one.

The skeleton ships with nothing to wire: a product's modules arrive later, one per part named
in its SDD Section 3. Add the wiring here as those modules land.
"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    """Entry point. Wires this product's concrete implementations and runs them.

    Empty on purpose — the frame carries no modules to wire yet.
    """
    return 0


if __name__ == "__main__":
    sys.exit(main())
