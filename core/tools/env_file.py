#!/usr/bin/env python3
"""Read one key from a dotenv-format file.

WHY THIS EXISTS: the hf adapter must know whether its token is present when it
builds a command, and Claude Code's ``apiKeyHelper`` must read the same token
when the run starts. One reader serves both, so the two cannot disagree about
what the file says. It imports nothing outside the standard library because the
helper runs in a child that has no environment of ours.

The CLI, ``env_file.py <path> <key>``, writes the value to stdout with no
trailing newline. That stdout is a credential channel: the CLI refuses to write
to a terminal, so the value is never printed to a person.
"""

from __future__ import annotations

import errno
import sys
from pathlib import Path

__version__ = "1.0.0"

_EXPORT_PREFIX = "export "
_QUOTES = ('"', "'")


def _unquote(text: str) -> str:
    if len(text) >= 2 and text[0] == text[-1] and text[0] in _QUOTES:
        return text[1:-1]
    return text


def value(path: Path, key: str) -> str | None:
    """Return ``key``'s value in the file at ``path``, or None if it assigns none.

    A later assignment of the same key wins. A missing or unreadable file raises
    ``OSError`` — one that is not valid UTF-8 included, so a caller maps one
    exception rather than two.
    """

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise OSError(errno.EILSEQ, "not valid UTF-8", str(path)) from None
    found: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith(_EXPORT_PREFIX):
            stripped = stripped[len(_EXPORT_PREFIX):]
        name, separator, assigned = stripped.partition("=")
        if separator and name.strip() == key:
            found = _unquote(assigned.strip())
    return found


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 2:
        print("env_file: usage: env_file.py <path> <key>", file=sys.stderr)
        return 2
    path, key = Path(arguments[0]), arguments[1]
    if sys.stdout.isatty():
        print(
            f"env_file: refusing to print {key} from {path} to a terminal",
            file=sys.stderr,
        )
        return 1
    try:
        assigned = value(path, key)
    except OSError as error:
        print(f"env_file: cannot read {key} from {path}: {error.strerror}", file=sys.stderr)
        return 1
    if not assigned:
        print(f"env_file: {key} is not set in {path}", file=sys.stderr)
        return 1
    sys.stdout.write(assigned)
    return 0


if __name__ == "__main__":
    sys.exit(main())
