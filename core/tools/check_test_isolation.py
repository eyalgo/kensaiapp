#!/usr/bin/env python3
"""A test reads nothing of the machine it runs on — the commit-time half of that rule.

**The rule** is `core/doctrine/engineering/testing_doctrine.md` § *A test reads nothing of the
machine it runs on*: a test reads only what is committed beside it or what it makes itself. This
file is one of the two places that hold it. The other is guard 7 of `pytest_guardrails.py`, which
gives every Python test an empty home while it runs. This one reads the test files a commit carries,
in any language, and refuses the commit when one names the machine.

**Why a check and not a note.** The rule was first written down only as a note to the model, and
it was broken again (the owner's call, 2026-10-29). A rule with no surface does not fire; this is
the surface. It runs from `core/githooks/pre-commit`,
which every instance on this host and every pinned run routes its commits through, whichever repo
the commit lands in.

**What counts as a hit — four kinds, a line reported once.**

- `home-path`: the home folder of the machine running the check, written out — in code, a comment
  or recorded data alike, since the path itself is the owner's. Read off the machine at run time,
  so the check names no one's home itself and catches whoever's is running it. A *made-up* home
  (`/Users/someone/.env`, the input of a test of a guard that refuses home reads) is not a hit:
  measured 2026-10-29, such lines outnumber real leaks across this host, its satellites and their
  products, and every committer's own home is checked by their own commit.
- `home-lookup`: code asking for the home — `Path.home()`, `expanduser(`, `expandvars(`, a read of
  `HOME` or `USERPROFILE` from the environment, and the same in JavaScript, Rust, Go and Swift. In
  a shell test, `$HOME` and a leading `~/` are reads too, unless the file sets `HOME` itself. A
  test that sets `HOME` to a folder it made is not a hit: the patterns match reads, not writes.
- `private-project`: a `system/projects/<name>/…` path that is on disk in the committing repo,
  where `<name>` is one of its projects, from a test outside `system/`. A test under `system/` is
  the instance's own check of its own tree and reads what is committed beside it; a test anywhere
  else — a vendored one under `core/`, `skills/` or `.claude/`, which a satellite runs without this
  instance's projects — that names a real path there depends on a folder no other copy has, even
  when it only parses the text. A made-up path under a real project's name (`…/x.md`) is not on
  disk and is not a hit.
- `commit`: a hex token that names a real commit of the committing repo, in a code file. A test
  that hands a commit to git passes only in a clone that carries that history; a made-up SHA names
  no commit. Recorded data (`.json`, `.txt` and the like) that carries the commit a capture was
  taken at reads nothing, and is not a hit.

**Comments and Python docstrings are not read for the last three kinds.** A comment that cites a
commit, a project's record or `Path.home()` reads none of them. `$HOME` and `~/` in a Python or
JavaScript string are text, not reads — tests of path expansion and of the guards that refuse home
reads carry them as data — so they are left to the run-time guards, which see the difference.

**What is a test file.** A path under a `test/`, `tests/`, `__tests__/` or `spec/` folder, or a file
named as a test in the languages the packets cover: `test_*`, `*_test.*`, `*.test.*`, `*.spec.*`,
`conftest.py`, `*Test.swift`, `*Tests.swift`, `*.bats`, and a helper shared by tests,
`*test_support*`.

**The whole staged file is read, not only the lines the commit changes** — the ratchet
`written_forward.py` already applies: a file is clean once whoever stages it next cleans it. The
refusal says so, and says how a line is excused, because the person it stops may not have written
the line it names.

**An exception is written on the line it excuses, with its reason**: `test-isolation: allowed —
<reason>`, in the line's own comment syntax. A line whose home lookup is the *text* a test feeds to
a checker, or a test whose subject is the home guard itself, reads nothing of the machine; the
marker says so where a reader of that line sees it. It is not a central list, as
`check_vendor_neutrality.py`'s is, because this check reads every repository a commit lands in —
a product's own repo included — and a list in `core/` naming a product's files is the leak that
check exists to stop. A marker with no reason excuses nothing.
"""

from __future__ import annotations

import argparse
import io
import re
import subprocess
import tokenize
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

__version__ = "1.3.0"

EXCUSE = re.compile(r"test-isolation: allowed (—|--|-) *\S")

TEST_FILE = re.compile(
    r"(^|/)(tests?|__tests__|spec)/"
    r"|(^|/)test_[^/]*$"
    r"|_test\.[A-Za-z]+$"
    r"|\.(test|spec)\.[A-Za-z]+$"
    r"|(^|/)conftest\.py$"
    r"|test_support[^/]*$"
    r"|Tests?\.swift$"
    r"|\.bats$"
)

HOME_LOOKUP = re.compile(
    r"Path\.home\(\)"
    r"|expanduser\("
    r"|environ\.get\(\s*[\"']HOME[\"']"
    r"|environ\[\s*[\"']HOME[\"']\s*\](?!\s*=[^=])"
    r"|getenv\(\s*[\"']HOME[\"']"
    r"|environ\.get\(\s*[\"']USERPROFILE[\"']"
    r"|environ\[\s*[\"']USERPROFILE[\"']\s*\](?!\s*=[^=])"
    r"|getenv\(\s*[\"']USERPROFILE[\"']"
    r"|expandvars\("
    r"|process\.env\.(HOME|USERPROFILE)\b"
    r"|process\.env\[\s*[\"'](HOME|USERPROFILE)[\"']\s*\](?!\s*=[^=])"
    r"|homedir\(\)"
    r"|home_dir\(\)"
    r"|env::var(_os)?\(\s*\"HOME\""
    r"|UserHomeDir\(\)"
    r"|homeDirectoryForCurrentUser"
    r"|NSHomeDirectory\(\)"
)

SHELL_FILE = re.compile(r"\.(sh|bash|bats)$")
SHELL_HOME_READ = re.compile(r"\$\{?HOME\b|(^|[\s=:\"'(])~/")
SHELL_SETS_HOME = re.compile(r"(^|[\s;])(export\s+)?HOME=", re.MULTILINE)

# The files a commit ID could be handed to git from. Anything else under a test folder is recorded
# data, and a commit in it records where a capture was taken.
CODE_FILE = re.compile(r"\.(py|sh|bash|bats|js|mjs|cjs|jsx|ts|tsx|rs|swift|go|rb)$")

PROJECT_PATH = re.compile(r"system/projects/([A-Za-z0-9_.-]+)((?:/[A-Za-z0-9_.@-]+)*)")

# Seven to forty hex characters holding a digit and a letter: a SHA, full or abbreviated. Read on
# code with its comments removed, so a citation in a comment is never seen. Whether it names a
# commit is asked of the repo, never guessed from the shape.
HEX_TOKEN = re.compile(
    r"(?<![0-9A-Za-z_`])(?=[0-9a-f]*[a-f])(?=[0-9a-f]*[0-9])[0-9a-f]{7,40}(?![0-9A-Za-z_`])"
)
# Where a SHA is handed to git rather than cited in a sentence: the whole of a string
# (`BASE = "<sha>"`), or touching a revision operator or an option's `=` (`"<sha>..HEAD"`,
# `"--base=<sha>"`, `"<sha>^"`, `"<sha>:path"`), or on a line that runs git. A SHA in the middle of a
# prose string — an expected message citing where a change landed — reads nothing.
def _handed_to_git(line: str, token: str) -> bool:
    for match in re.finditer(rf"(?<![0-9A-Za-z_`]){token}(?![0-9A-Za-z_`])", line):
        before, after = line[: match.start()], line[match.end():]
        if before[-1:] in "\"'" and after[:1] in "\"'":
            return True
        if before.endswith(("=", "..", "@", "~")) or after.startswith(("..", "^", "~", ":", "@")):
            return True
    return bool(re.search(r"\bgit\b", line))
FULL_LINE_COMMENT = re.compile(r"^\s*(#|//|/\*|\*|--)")


@dataclass(frozen=True)
class Hit:
    path: str
    line: int
    kind: str
    text: str


def is_test_file(relative: str) -> bool:
    return bool(TEST_FILE.search(relative))


def _python_code(text: str) -> list[str] | None:
    """`text`'s lines with every comment and docstring blanked, or `None` when it does not
    tokenize. A docstring is a string standing alone as a statement."""
    lines = text.splitlines()
    blank: list[tuple[tuple[int, int], tuple[int, int]]] = []
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, SyntaxError, IndentationError):
        return None
    starts = {tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENCODING}
    skip = {tokenize.NL, tokenize.COMMENT}
    significant = [t for t in tokens if t.type not in skip]
    for index, token in enumerate(significant):
        if token.type == tokenize.STRING:
            before = significant[index - 1].type if index else tokenize.NEWLINE
            after = significant[index + 1].type if index + 1 < len(significant) else tokenize.NEWLINE
            if before in starts and after in (tokenize.NEWLINE, tokenize.ENDMARKER):
                blank.append((token.start, token.end))
    blank.extend((t.start, t.end) for t in tokens if t.type == tokenize.COMMENT)
    out = [list(line) for line in lines]
    for (row, col), (end_row, end_col) in blank:
        for r in range(row, end_row + 1):
            if r - 1 >= len(out):
                break
            first = col if r == row else 0
            last = end_col if r == end_row else len(out[r - 1])
            for c in range(first, min(last, len(out[r - 1]))):
                out[r - 1][c] = " "
    return ["".join(chars) for chars in out]


def code_lines(path: str, text: str) -> list[str]:
    """The lines of `text` as code: comments (and, in Python, docstrings) blanked, so what is
    matched is what runs. Line numbers are kept."""
    lines = text.splitlines()
    if path.endswith(".py"):
        lines = _python_code(text) or lines
    # A whole-line comment is blanked after the Python pass too: a script a test holds in a string
    # (a shell stub, a hook) carries its own comments, and they read nothing either.
    return ["" if FULL_LINE_COMMENT.match(line) else line for line in lines]


def scan_text(
    path: str,
    text: str,
    *,
    home: str,
    projects: set[str],
    exists: Callable[[str], bool],
    commits: Callable[[Iterable[str]], set[str]],
) -> list[Hit]:
    """Every line of the test file `path` that names the machine. `exists` answers whether a
    repo-relative path is on disk; `commits` is handed every quoted SHA-shaped token in the file at
    once and answers which of them are real commits."""
    lines = text.splitlines()
    code = code_lines(path, text)
    is_code = bool(CODE_FILE.search(path))
    tokens = {token for line in code for token in HEX_TOKEN.findall(line)} if is_code else set()
    real_commits = commits(tokens) if tokens else set()
    reads_projects = not path.startswith("system/")
    shell_reads_home = bool(SHELL_FILE.search(path)) and not SHELL_SETS_HOME.search(text)

    hits: list[Hit] = []
    for number, (line, run) in enumerate(zip(lines, code), start=1):
        kinds = []
        if home and home in line:
            kinds.append("home-path")
        if HOME_LOOKUP.search(run) or (shell_reads_home and SHELL_HOME_READ.search(run)):
            kinds.append("home-lookup")
        if reads_projects and any(
            name in projects and exists(f"system/projects/{name}{rest}")
            for name, rest in PROJECT_PATH.findall(run)
        ):
            kinds.append("private-project")
        if any(_handed_to_git(run, token) for token in real_commits.intersection(HEX_TOKEN.findall(run))):
            kinds.append("commit")
        if kinds and not EXCUSE.search(line):
            hits.append(Hit(path=path, line=number, kind="+".join(kinds), text=line.strip()))
    return hits



class Repo:
    """The committing repository, read through git."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def _git(self, *args: str, stdin: str | None = None) -> str:
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            input=stdin,
            capture_output=True,
            text=True,
            check=True,
        ).stdout

    def staged_files(self) -> list[str]:
        """Files added, copied or modified in the index. `--no-renames`, so a rename's new half is
        read on its own (`written_forward.py` makes the same choice)."""
        out = self._git("diff", "--cached", "--name-only", "--diff-filter=ACM", "--no-renames", "-z")
        return [p for p in out.split("\0") if p]

    def tracked_files(self) -> list[str]:
        return [p for p in self._git("ls-files", "-z").split("\0") if p]

    def staged_text(self, relative: str) -> str:
        return self._git("show", f":{relative}")

    def tree_text(self, relative: str) -> str:
        return (self.root / relative).read_text(encoding="utf-8")

    def projects(self) -> set[str]:
        folder = self.root / "system" / "projects"
        return {p.name for p in folder.iterdir() if p.is_dir()} if folder.is_dir() else set()

    def exists(self, relative: str) -> bool:
        return (self.root / relative).exists()

    def commits(self, tokens: Iterable[str]) -> set[str]:
        tokens = sorted(tokens)
        out = self._git("cat-file", "--batch-check", stdin="".join(f"{t}\n" for t in tokens))
        return {
            token
            for token, answer in zip(tokens, out.splitlines())
            if answer.split()[1:2] == ["commit"]
        }


def scan(
    repo: Repo,
    files: list[str],
    read: Callable[[str], str],
    *,
    home: str,
) -> list[Hit]:
    projects = repo.projects()
    hits: list[Hit] = []
    for relative in files:
        if not is_test_file(relative):
            continue
        try:
            text = read(relative)
        except (UnicodeDecodeError, FileNotFoundError, subprocess.CalledProcessError):
            continue  # a binary or vanished file carries no line to read
        hits.extend(
            scan_text(
                relative, text, home=home, projects=projects, exists=repo.exists, commits=repo.commits
            )
        )
    return hits


REMEDY = (
    "Fix these lines on this branch, then commit again — whoever sees a violation fixes it "
    "(the boy-scout rule, <CORE>/doctrine/governance/found_while_walking.md). A line named here "
    "may be older than your change; it is yours to fix all the same.\n\n"
    "How: a test reads only what is committed beside it or what it makes itself. Give it a home "
    "it made (HOME set to a temporary folder), build its input in a temporary folder, or commit "
    "the input beside the test as data. A skip when the thing is missing is not a fix. A line "
    "that reads nothing of the machine — text a test feeds to a checker, or the home guard's own "
    "subject — is excused on that line: `test-isolation: allowed — <reason>`. "
    "<CORE>/doctrine/engineering/testing_doctrine.md § A test reads nothing of the machine it "
    "runs on."
)


def main(argv: list[str] | None = None, *, home: str | None = None) -> int:
    parser = argparse.ArgumentParser(prog="check_test_isolation.py", description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--staged", action="store_true", help="the index's test files; exit 1 on any hit")
    mode.add_argument("--all", action="store_true", help="every tracked test file; exit 1 on any hit")
    parser.add_argument("--repo", default=".", help="the repository to read (default: the working directory)")
    args = parser.parse_args(argv)

    repo = Repo(Path(args.repo).resolve())
    home = home if home is not None else str(Path.home())
    if args.staged:
        hits = scan(repo, repo.staged_files(), repo.staged_text, home=home)
    else:
        hits = scan(repo, repo.tracked_files(), repo.tree_text, home=home)
    if not hits:
        return 0
    for hit in sorted(hits, key=lambda h: (h.path, h.line)):
        print(f"{hit.path}:{hit.line}: [{hit.kind}] {hit.text}", file=sys.stderr)
    print(f"\n{len(hits)} lines in {len({h.path for h in hits})} test files\n\n{REMEDY}", file=sys.stderr)
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
