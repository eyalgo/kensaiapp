"""Contract tests for the dotenv key reader that doubles as `apiKeyHelper`."""

from __future__ import annotations

import errno
import os
import pty
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

import env_file

_SCRIPT = Path(__file__).resolve().parent / "env_file.py"
_SECRET = "hf_SENTINEL_do_not_leak"
# No newline, carriage return or tab: the terminal rewrites those (`\n` arrives as `\r\n`).
_TERMINAL_FENCE = b"@@end-of-terminal-output@@"
_TERMINAL_READ_SIZE = 4096


def _read_terminal(master: int, read: Callable[[int, int], bytes]) -> str:
    """Return what was written to the terminal before `_TERMINAL_FENCE`, decoded.

    The caller writes the fence to the slave once the child has exited and reads while the
    slave is still open: on macOS, closing the last slave descriptor discards what is
    buffered. The read also ends on an empty read, so it cannot spin, and on `EIO`, which
    Linux raises once the slave is gone. Any other `OSError` propagates.
    """
    received = b""
    while not received.endswith(_TERMINAL_FENCE):
        try:
            chunk = read(master, _TERMINAL_READ_SIZE)
        except OSError as error:
            if error.errno != errno.EIO:
                raise
            break
        if not chunk:
            break
        received += chunk
    return received.removesuffix(_TERMINAL_FENCE).decode()


def _dotenv(tmp_path: Path, text: str) -> Path:
    path = tmp_path / ".env"
    path.write_text(text, encoding="utf-8")
    return path


def _run_piped(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.mark.parametrize(
    "line",
    [
        f"K={_SECRET}",
        f'K="{_SECRET}"',
        f"K='{_SECRET}'",
        f"export K={_SECRET}",
    ],
)
def test_value_reads_each_line_form(tmp_path, line):
    assert env_file.value(_dotenv(tmp_path, line + "\n"), "K") == _SECRET


def test_comments_and_blank_lines_are_skipped(tmp_path):
    path = _dotenv(tmp_path, "# K=commented\n\n   \n")

    assert env_file.value(path, "K") is None


def test_a_repeated_key_takes_the_later_line(tmp_path):
    assert env_file.value(_dotenv(tmp_path, "K=first\nK=second\n"), "K") == "second"


def test_a_missing_key_is_none(tmp_path):
    assert env_file.value(_dotenv(tmp_path, "OTHER=1\n"), "K") is None


def test_a_missing_file_raises_oserror(tmp_path):
    with pytest.raises(OSError):
        env_file.value(tmp_path / "absent.env", "K")


def test_an_undecodable_file_raises_oserror(tmp_path):
    path = tmp_path / ".env"
    path.write_bytes(b"K=\xff\xfe\n")

    with pytest.raises(OSError):
        env_file.value(path, "K")


def test_value_splits_at_the_first_equals_sign(tmp_path):
    assert env_file.value(_dotenv(tmp_path, "K=a=b\n"), "K") == "a=b"


def test_value_strips_whitespace_around_key_and_value(tmp_path):
    assert env_file.value(_dotenv(tmp_path, "  K = v \n"), "K") == "v"


def test_cli_writes_the_value_with_no_newline_when_piped(tmp_path):
    result = _run_piped(str(_dotenv(tmp_path, f"K={_SECRET}\n")), "K")

    assert result.stdout == _SECRET
    assert result.returncode == 0


@pytest.mark.parametrize("content", [None, "OTHER=1\n", "K=\n"])
def test_cli_refuses_a_missing_or_empty_key_or_file(tmp_path, content):
    path = tmp_path / ".env"
    if content is not None:
        path.write_text(content + f"SECRET_NEIGHBOUR={_SECRET}\n", encoding="utf-8")

    result = _run_piped(str(path), "K")

    assert result.stdout == ""
    assert result.returncode != 0
    assert "K" in result.stderr and str(path) in result.stderr
    assert _SECRET not in result.stderr


def test_cli_refuses_an_undecodable_file_as_one_line(tmp_path):
    path = tmp_path / ".env"
    path.write_bytes(f"SECRET_NEIGHBOUR={_SECRET}\nK=\xff\xfe\n".encode("latin-1"))

    result = _run_piped(str(path), "K")

    assert result.stdout == ""
    assert result.returncode != 0
    assert result.stderr.count("\n") == 1 and "Traceback" not in result.stderr
    assert "K" in result.stderr and str(path) in result.stderr
    assert _SECRET not in result.stderr


def test_cli_writes_nothing_to_a_terminal(tmp_path):
    path = _dotenv(tmp_path, f"K={_SECRET}\n")
    master, slave = pty.openpty()
    try:
        process = subprocess.run(
            [sys.executable, str(_SCRIPT), str(path), "K"],
            stdout=slave,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        os.write(slave, _TERMINAL_FENCE)
        written = _read_terminal(master, os.read)
    finally:
        os.close(master)
        os.close(slave)

    assert _SECRET not in written
    assert written == ""
    assert process.returncode != 0
    assert process.stderr.strip() != ""
    assert _SECRET not in process.stderr


def _scripted_reads(*chunks: bytes | OSError):
    remaining = iter(chunks)

    def read(descriptor: int, size: int) -> bytes:
        chunk = next(remaining)
        if isinstance(chunk, OSError):
            raise chunk
        return chunk

    return read


def test_the_terminal_read_answers_eio_as_nothing_written():
    def read(descriptor: int, size: int) -> bytes:
        raise OSError(errno.EIO, "Input/output error")

    assert _read_terminal(-1, read) == ""


def test_the_terminal_read_answers_the_bytes_before_an_eio():
    read = _scripted_reads(b"CHILD_WROTE", OSError(errno.EIO, "Input/output error"))

    assert _read_terminal(-1, read) == "CHILD_WROTE"


def test_the_terminal_read_lets_another_oserror_through():
    error = OSError(errno.EBADF, "Bad file descriptor")

    def read(descriptor: int, size: int) -> bytes:
        raise error

    with pytest.raises(OSError) as raised:
        _read_terminal(-1, read)

    assert raised.value is error
    assert raised.value.errno == errno.EBADF


def test_the_terminal_read_answers_what_the_child_wrote():
    master, slave = pty.openpty()
    try:
        subprocess.run(
            [sys.executable, "-c", "import sys; sys.stdout.write('CHILD_WROTE')"],
            stdout=slave,
            check=True,
        )
        os.write(slave, _TERMINAL_FENCE)

        written = _read_terminal(master, os.read)
    finally:
        os.close(slave)
        os.close(master)

    assert written == "CHILD_WROTE"


def test_the_terminal_read_stops_on_an_empty_read():
    assert _read_terminal(-1, _scripted_reads(b"")) == ""


def test_the_terminal_read_answers_the_bytes_before_an_empty_read():
    read = _scripted_reads(b"CHILD_WROTE", b"")

    assert _read_terminal(-1, read) == "CHILD_WROTE"


def test_the_terminal_read_joins_a_fence_split_across_reads():
    half = len(_TERMINAL_FENCE) // 2
    read = _scripted_reads(
        b"CHILD",
        b"_WROTE",
        _TERMINAL_FENCE[:half],
        _TERMINAL_FENCE[half:],
    )

    assert _read_terminal(-1, read) == "CHILD_WROTE"
