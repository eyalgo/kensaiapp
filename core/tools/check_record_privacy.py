#!/usr/bin/env python3
"""A record names no machine and no repository address — the commit-time half of that rule.

**The rule** is `core/doctrine/governance/records_name_no_machine.md`: no line written into a record
names the home folder or the login name of the machine that wrote it, or the address of the
repository it is committed to. This file is the surface that
holds it. It runs from `core/githooks/pre-commit`, which every instance on this host and every
pinned run routes its commits through, whichever repo the commit lands in.

**Why a check and not a note.** Runs were told to keep the paths they write relative, and lines
naming the machine landed in records anyway (the owner's call, 2026-10-29). A rule with no surface
does not fire; this is the surface.

**What counts as a hit — three kinds, a line reported once.**

- `home-path`: the home folder of the machine running the check, written out. Read off the machine
  at run time, so the check names no one's home itself and catches whoever's is running it. A
  *made-up* home (`/Users/sam/…`) and the placeholders (`<home>/…`) are not hits. A longer
  folder name that only begins with the home (`<home>-two`) is not the home.
- `login`: the login name of the machine running the check, standing as a word. A longer word that
  contains it is not a hit.
- `repository`: the `<owner>/<name>` address of the repository the commit is made in, read off its
  `origin` remote at run time, in any letter case, `.git` or `.wiki` after it included. Only an
  `origin` on a hosting service gives one: a local-folder or `file://` remote, and any remote but
  `origin`, are not read. A command against a hosting service's API writes it
  (`gh api repos/<owner>/<name>/…`), and its answer says what that repository is and allows. A
  longer name that only begins with it is not a hit, and a repository with no such `origin`
  has no address to look for. The bare name, written on its own, is not looked for: records name their
  own instance in prose all the time, and the address is what a command and its answer carry.

A home that is empty or `/`, and an empty login, are not looked for: neither names anyone, and a
check that looked for them would refuse every line.

**What is a record.** A file whose repo-relative path begins `system/projects/`, or has a `docs/`
folder anywhere in it. Any other file is not read.

**Only the lines the commit adds are read, with renames detected.** `check_test_isolation.py` and
`written_forward.py` read the whole staged file with renames off, under which a moved record adds
every one of its lines. That would refuse every seal that moves a change folder into `trail/`, so
this check reads `git diff --cached -U0 --find-renames`, under which a pure move adds nothing and a
rename with an edit adds only the edit. A record already holding the home is therefore not refused
for carrying it forward.

**No line is excused.** `check_test_isolation.py` accepts a marker on a line it would otherwise
refuse. This check accepts none, because a record has no reason to carry the real home folder, login
name or repository address.
"""

from __future__ import annotations

import argparse
import codecs
import getpass
import re
import subprocess
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

__version__ = "1.1.0"

RECORD_PREFIX = "system/projects/"
DOCS_FOLDER = "docs"

HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
NEW_PATH_HEADER = "+++ "
NEW_PATH_PREFIX = "b/"

REMEDY = (
    "[home-path] is this machine's home folder, written out. [login] is this machine's login "
    "name, standing as a word. [repository] is this repository's own `<owner>/<name>` address. "
    "A record ships with the repository it is committed to, so it names no one's machine and "
    "not the repository's address. Write the home folder as `<home>/…`, a path inside the "
    "instance as `<the instance>/…` or relative to its root, the login name as `<user>`, and the "
    "address as `<owner>/<repository>`. Terminal output "
    "pasted into a record, and the commands an evidence line quotes, are the cases to look at "
    "first. See <CORE>/doctrine/governance/records_name_no_machine.md.\n\n"
    "Only the lines this commit adds to a record are read, so every line named above is one this "
    "commit writes. Lines the record already held, and a record moved or renamed unchanged, are "
    "not read."
)


@dataclass(frozen=True)
class AddedLine:
    path: str
    number: int
    text: str


@dataclass(frozen=True)
class Hit:
    path: str
    line: int
    kind: str
    text: str


def is_record(path: str) -> bool:
    return path.startswith(RECORD_PREFIX) or DOCS_FOLDER in path.split("/")[:-1]


def _new_path(header: str) -> str:
    """The path a `+++` header names, as git writes it: a name holding a space carries a trailing
    tab, and a name holding a double quote, a backslash or a control character is C-quoted."""
    name = header.removeprefix(NEW_PATH_HEADER).removesuffix("\t")
    if len(name) > 1 and name.startswith('"') and name.endswith('"'):
        unquoted, _ = codecs.escape_decode(name[1:-1].encode("utf-8"))
        name = unquoted.decode("utf-8", errors="replace")
    return name.removeprefix(NEW_PATH_PREFIX)


def added_lines(diff: str) -> Iterator[AddedLine]:
    """Walk a unified diff: file headers give the new path, a hunk header gives the number of its
    first new-side line, every `+` line inside a hunk is one added line, and a context line, which
    git writes between fused hunks, moves the number on without being read."""
    path = ""
    number = 0
    in_hunk = False
    for raw in diff.splitlines():
        if raw.startswith("diff --git "):
            in_hunk = False
        elif not in_hunk and raw.startswith(NEW_PATH_HEADER):
            path = _new_path(raw)
        elif hunk := HUNK_HEADER.match(raw):
            number = int(hunk.group(1))
            in_hunk = True
        elif in_hunk and raw.startswith("+"):
            yield AddedLine(path=path, number=number, text=raw[1:])
            number += 1
        elif in_hunk and raw.startswith(" "):
            number += 1


def _kinds(text: str, home: re.Pattern[str] | None, login: re.Pattern[str] | None,
           repository: re.Pattern[str] | None) -> list[str]:
    kinds = []
    if home is not None and home.search(text):
        kinds.append("home-path")
    if login is not None and login.search(text):
        kinds.append("login")
    if repository is not None and repository.search(text):
        kinds.append("repository")
    return kinds


def _home_pattern(home: str) -> re.Pattern[str] | None:
    folder = home.rstrip("/")
    return re.compile(re.escape(folder) + r"(?![\w-])") if folder else None


def _login_pattern(login: str) -> re.Pattern[str] | None:
    return re.compile(rf"(?<!\w){re.escape(login)}(?!\w)") if login else None


def _repository_pattern(addresses: tuple[str, ...]) -> re.Pattern[str] | None:
    names = sorted({address for address in addresses if address}, key=len, reverse=True)
    if not names:
        return None
    alternatives = "|".join(re.escape(name) for name in names)
    return re.compile(rf"(?<![\w.-])(?:{alternatives})(?![\w-])", re.IGNORECASE)


# A remote on a hosting service: the scp-like form (`git@host:owner/name.git`) or a network URL
# (`https://host/owner/name`, `ssh://git@host:22/owner/name/`). A local folder or `file://` remote
# matches neither, so it gives no address.
_SCP_REMOTE = re.compile(r"^[\w.-]+@[\w.-]+:([\w.-]+)/([\w.-]+?)(?:\.git)?/?$")
_URL_REMOTE = re.compile(
    r"^(?:https?|ssh|git)://(?:[^@/]+@)?[\w.-]+(?::\d+)?/([\w.-]+)/([\w.-]+?)(?:\.git)?/?$")


def remote_address(url: str) -> str:
    """The `<owner>/<name>` a hosting-service remote URL names, or "" for any other URL."""
    found = _SCP_REMOTE.match(url.strip()) or _URL_REMOTE.match(url.strip())
    return f"{found.group(1)}/{found.group(2)}" if found else ""


def scan(diff: str, *, home: str, login: str, repositories: tuple[str, ...] = ()) -> list[Hit]:
    home_pattern = _home_pattern(home)
    login_pattern = _login_pattern(login)
    repository_pattern = _repository_pattern(repositories)
    hits = []
    for line in added_lines(diff):
        if not is_record(line.path):
            continue
        kinds = _kinds(line.text, home_pattern, login_pattern, repository_pattern)
        if kinds:
            hits.append(Hit(path=line.path, line=line.number, kind="+".join(kinds), text=line.text))
    return hits


def staged_diff(repo: Path) -> str:
    """The index against HEAD, added lines only, renames detected. Never `--no-renames`.

    The prefixes are named here because the repo's own `diff.noprefix`, `diff.mnemonicPrefix` or
    `diff.dstPrefix` would otherwise change the `+++ b/` header the walk reads a path from."""
    return subprocess.run(
        [
            "git", "-C", str(repo), "-c", "core.quotepath=off", "diff", "--cached", "-U0",
            "--find-renames", "--diff-filter=ACMR", "--no-color", "--no-ext-diff",
            "--src-prefix=a/", "--dst-prefix=b/",
        ],
        capture_output=True,
        text=True,
        errors="replace",
        check=True,
    ).stdout


def origin_url(repo: Path) -> str:
    """The repository's `origin` URL; empty when it has none or git cannot read it."""
    result = subprocess.run(
        ["git", "-C", str(repo), "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    )
    return result.stdout if result.returncode == 0 else ""


def main(
    argv: list[str] | None = None, *, home: str | None = None, login: str | None = None,
    repositories: tuple[str, ...] | None = None,
) -> int:
    parser = argparse.ArgumentParser(
        prog="check_record_privacy.py", description=__doc__.splitlines()[0]
    )
    parser.add_argument(
        "--staged", action="store_true", required=True,
        help="the index's added record lines; exit 1 on any hit",
    )
    parser.add_argument(
        "--repo", default=".", help="the repository to read (default: the working directory)"
    )
    args = parser.parse_args(argv)

    home = home if home is not None else str(Path.home())
    login = login if login is not None else getpass.getuser()
    repo = Path(args.repo).resolve()
    try:
        diff = staged_diff(repo)
    except subprocess.CalledProcessError as failure:
        print(
            f"check_record_privacy: git could not read the staged changes in {repo}: "
            f"{failure.stderr.strip()}",
            file=sys.stderr,
        )
        return 1
    if repositories is None:
        address = remote_address(origin_url(repo))
        repositories = (address,) if address else ()
    hits = scan(diff, home=home, login=login, repositories=repositories)
    if not hits:
        return 0
    for hit in hits:
        print(f"{hit.path}:{hit.line}: [{hit.kind}] {hit.text}", file=sys.stderr)
    print(f"\n{REMEDY}", file=sys.stderr)
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
