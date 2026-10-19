"""providers.py — the one reader of the central provider file, and the rule a launch follows.

WHY THIS EXISTS
    Every launch a chain engine makes (`chain.py`, `chain_development.py`, `build_idea.py`) goes
    to a provider, and so does every launch an instance skill launcher makes, every launch of the
    three kaizen tool scripts (`launch-apply-packet.sh`, `launch-audit.sh`, `launch-fix-author.sh`
    under `core/tools/`). That choice used to
    be a field on each engine's own table, with a default for the entries that named none, and a
    literal in each launcher and script, so which provider a step ran on was scattered over three
    modules and eleven scripts and could never be missing. It now lives in one data file per
    instance, `.providers.toml` at the instance's root, and this module is the only code that
    knows the file's path, its format, the names of its entries and the rule:

        the provider the walk was forced onto (`--provider`), else the one the file names for
        the launch's member, else a refusal naming what is missing.

    There is no third branch. An entry the file lacks, a value that is not a known provider, and a
    file that is missing or is not TOML are all refused by name — never defaulted — because a
    default is a provider nobody chose.

WHICH FILE IS READ
    `.providers.toml` at the root of the instance a launch is for, and no other file: not a file
    under `<CORE>`, not an environment variable, not a flag. So a walk for a satellite, which
    binds `<CORE>` to this host's `core/`, reads the satellite's own file, and a walk running from
    a pin reads the live instance file, because a pin changes where the code is read from and not
    which instance the launch is for. `ProviderFiles` is the port an engine is handed: `at(root)`
    is the `ProviderFile` of that root, built afresh on each call and cached nowhere. A file that
    is missing is refused naming its path and the command that makes it from the tracked
    `.providers.toml.example`, which is never read in its place. Only a composition root builds
    a `ProviderFiles` — an engine's, or `main` below.

THE FILE'S SHAPE
    Five TOML tables, each keyed by its member's own name, verbatim and case-sensitive:
    `[documents]` (the product chain's registry), `[steps]` (the development and change walks'
    steps — one entry governs a step in both), `[build-idea]` (the queue's skill rows),
    `[owed-items]` (`no-document`, the product chain's launch for an owed item that names no
    document), `[launchers]` (one entry per instance skill launcher, keyed by the launcher's
    folder name, and one per kaizen tool script, keyed by the script's name without `.sh`). The
    table is part of the name, so the `design` step and the `DESIGN` document are `steps.design`
    and `documents.DESIGN`. An entry no engine asks for is ignored: a reader walks the members it
    is asked about, never the file's keys.

THE COMMAND-LINE FACE
    A bash launcher cannot call `ProviderFile` in-process, and a second reader written in shell
    would be a second owner of the rule. So this module answers a launcher itself:

        python3 <CORE>/tools/providers.py launcher <name> --instance-root <dir>
            [--forced <p>] [--accept <p>]...

    `--instance-root` is required: it is the root of the instance the launch is for, and the file
    read is `.providers.toml` there. A launcher hands it its own absolute instance root, so the
    reader never receives a relative root from a shell that has since changed directory.

    Stdout is the provider and a newline, and nothing else, because the launcher captures it as
    the value. A refusal leaves stdout empty, names what is missing on stderr and exits
    `REFUSED_EXIT`, a number argparse's own usage error (2) never takes. `--forced` is the force
    the launcher was given: non-empty, it is the answer and the file is not read. `--accept` is
    the set of providers the launcher can run; a launcher that builds a Claude-only argv passes
    `--accept claude`, and an entry naming anything else is refused rather than launched on the
    wrong provider.
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from run_intelligence import PROVIDERS

__version__ = "1.4.0"

FILE_NAME = ".providers.toml"

# The command that makes the file; the refusal for an unreadable file names it, so an engine and
# the command line refuse in the same words.
COPY_COMMAND = "cp .providers.toml.example .providers.toml"

_DOCUMENTS = "documents"
_STEPS = "steps"
_BUILD_IDEA = "build-idea"
_OWED_ITEMS = "owed-items"
_LAUNCHERS = "launchers"

# The status of a refused launcher lookup; argparse's own usage error is 2, and 0 is an answer.
REFUSED_EXIT = 3

# A TOML bare key; anything else is written as a quoted key in a member's dotted name.
_BARE_KEY = re.compile(r"[A-Za-z0-9_-]+")


def instance_file(instance_root: str) -> str:
    """The provider file of the instance rooted at `instance_root` — `.providers.toml` there."""
    return str(Path(instance_root) / FILE_NAME)


def _toml_key(key: str) -> str:
    if _BARE_KEY.fullmatch(key):
        return key
    escaped = key.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


@dataclass(frozen=True)
class Member:
    """One launch source an engine asks the file about: a table and a key in it. Its `str` is the
    TOML dotted key the owner would look for in the file, which is what a refusal names."""

    table: str
    key: str

    def __str__(self) -> str:
        return f"{self.table}.{_toml_key(self.key)}"


def document(name: str) -> Member:
    """The entry for a product-chain document, by its registry name (`DESIGN`)."""
    return Member(_DOCUMENTS, name)


def step(step_id: str) -> Member:
    """The entry for a development or change-walk step, by its id (`code-integrity`)."""
    return Member(_STEPS, step_id)


def build_idea_row(kind_name: str) -> Member:
    """The entry for a `build-idea` skill row, by its kind's name (`pick a seed`)."""
    return Member(_BUILD_IDEA, kind_name)


def launcher(name: str) -> Member:
    """The entry for an instance skill launcher by its folder name (`cold-read`), or for a kaizen
    tool script under `core/tools/` by its name without `.sh` (`launch-audit`)."""
    return Member(_LAUNCHERS, name)


# The product chain's launch for an owed item whose path resolves to no document.
OWED_ITEM = Member(_OWED_ITEMS, "no-document")


class ProvidersRefused(Exception):
    """The file cannot give a provider for a member it was asked about — the entry is missing or
    names no known provider, or the file is missing or unreadable. The message names every such
    entry, or the file's path. Each engine converts it to its own refusal or halt before the
    launch it was asked for is made."""


class ProviderFile:
    """The provider file at `path`, read through `files` — anything with
    `read_text(path) -> str | None`. Every call reads the file afresh, so an edit takes effect
    from the next launch; nothing is cached."""

    def __init__(self, path: str, files) -> None:
        self.path = path
        self.files = files

    def resolve(self, members: Iterable[Member]) -> dict[Member, str]:
        """Every asked member's provider, from one read — or `ProvidersRefused` naming each asked
        member the file cannot answer for, all of them at once, so one repair round is enough."""
        entries = self._read()
        resolved: dict[Member, str] = {}
        problems: list[str] = []
        for member in dict.fromkeys(members):
            table = entries.get(member.table)
            if not isinstance(table, dict) or member.key not in table:
                problems.append(f"{member} is missing")
                continue
            value = table[member.key]
            if not isinstance(value, str) or value not in PROVIDERS:
                problems.append(f"{member} names {value!r}, which is not a known provider")
                continue
            resolved[member] = value
        if problems:
            raise ProvidersRefused(
                f"the provider file {self.path} cannot give a provider: {'; '.join(problems)} "
                f"— each entry names one of {', '.join(PROVIDERS)}, and a missing entry is "
                "refused, never defaulted")
        return resolved

    def launch_provider(self, forced: str, member: Member) -> str:
        """The provider one launch goes to: `forced` when the walk was forced, without reading
        the file; else the file's entry for `member`, read now."""
        if forced:
            return forced
        return self.resolve([member])[member]

    def _read(self) -> dict:
        try:
            text = self.files.read_text(self.path)
        except UnicodeDecodeError:
            raise ProvidersRefused(
                f"the provider file {self.path} cannot be read as UTF-8") from None
        if text is None:
            raise ProvidersRefused(
                f"the provider file {self.path} is missing or cannot be read — every unforced "
                f"launch takes its provider from it, and it is made at the instance root with "
                f"`{COPY_COMMAND}`")
        try:
            return tomllib.loads(text)
        except tomllib.TOMLDecodeError as error:
            message = f"the provider file {self.path} is not valid TOML: {error}"
            raise ProvidersRefused(message) from None


class ProviderFiles:
    """The provider files of every instance, read through `files` — the port an engine is
    handed. `at(instance_root)` is the `ProviderFile` of that instance, built on the spot and
    cached nowhere, so each call reads the file as it stands then."""

    def __init__(self, files) -> None:
        self.files = files

    def at(self, instance_root: str) -> ProviderFile:
        return ProviderFile(instance_file(instance_root), self.files)


class _DiskFiles:
    """The `files` port over the real disk: the text at `path`, or `None` when it cannot be
    opened. Undecodable bytes are not swallowed here; `ProviderFile` refuses them by path."""

    def read_text(self, path: str) -> str | None:
        try:
            return Path(path).read_text(encoding="utf-8")
        except OSError:
            return None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="providers.py", description="Print the provider a launch goes to.")
    commands = parser.add_subparsers(dest="command", required=True)
    one = commands.add_parser(
        "launcher", help="the provider an instance skill launcher or a kaizen tool script uses")
    one.add_argument("name", help="the launcher's folder name, or a tool script's name without "
                     ".sh, as its entry is keyed")
    one.add_argument("--instance-root", required=True, metavar="DIR",
                     help="the root of the instance the launch is for; the provider is read from "
                     ".providers.toml there unless --forced is non-empty")
    one.add_argument("--forced", default="",
                     help="the force the launcher was given; non-empty, the file is not read")
    one.add_argument("--accept", action="append", default=[], metavar="PROVIDER",
                     help="a provider the launcher can run; repeat for several")
    return parser


def run(argv: Sequence[str], provider_files: ProviderFiles, stdout: TextIO, stderr: TextIO) -> int:
    """Answer one command-line request over `provider_files`, for the instance root it names: the
    provider on `stdout` and 0, or the reason on `stderr` and `REFUSED_EXIT`, with `stdout` left
    empty."""
    args = _parser().parse_args(list(argv))
    member = launcher(args.name)
    unknown = [value for value in args.accept if value not in PROVIDERS]
    if unknown:
        print(f"providers: --accept names {', '.join(map(repr, unknown))}, which is not a known "
              f"provider — each is one of {', '.join(PROVIDERS)}", file=stderr)
        return REFUSED_EXIT
    try:
        provider = provider_files.at(args.instance_root).launch_provider(args.forced, member)
    except ProvidersRefused as refused:
        print(f"providers: {refused}", file=stderr)
        return REFUSED_EXIT
    if args.accept and provider not in args.accept:
        print(f"providers: {member} names {provider!r}, and {args.name} can run only "
              f"{', '.join(args.accept)} — it will not launch on another provider",
              file=stderr)
        return REFUSED_EXIT
    print(provider, file=stdout)
    return 0


def main(argv: list[str] | None = None) -> int:
    """The composition root of the command-line face: the one `ProviderFiles` over the disk."""
    return run(sys.argv[1:] if argv is None else argv,
               ProviderFiles(_DiskFiles()), sys.stdout, sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
