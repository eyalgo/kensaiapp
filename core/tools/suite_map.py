"""The suite map: which suites guard which instance paths, held in one place.

WHY THIS EXISTS. Three reds reached `main` on 2026-10-07 (repaired in `b3b64e675`, `3bf8d0139`,
`042218890`) because nothing told a commit which tests its paths could break. This module is that
answer: an ordered list of entries, each a glob over instance-relative paths and the names of the
suites it guards, and a lookup that turns a set of paths into the suites to run. It runs nothing and
reads nothing from disk — the commit and merge gates that call it are separate changes, and the
tests in `test_suite_map.py` hold the map against the tracked tree, so a new path cannot slip by.

Patterns match over `/`-separated segments: `*` stays inside one segment and `**` spans any number
of whole segments, none included — so `core/**` matches `core` itself. The matcher is written here
because nothing in the standard library is that rule: `fnmatch` lets `*` cross `/`,
`PurePath.match` anchors from the right, and `PurePosixPath.full_match` (3.13) will not let a
trailing `**` take no segment.
"""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase

__version__ = "1.1.0"


class SuiteMapError(ValueError):
    """A map that contradicts itself: an entry names a suite it does not declare, or a suite is
    declared twice. The message names the suite."""


@dataclass(frozen=True)
class Suite:
    """A named suite and its command: an argv tuple run from the instance root, no shell string."""

    name: str
    command: tuple[str, ...]


@dataclass(frozen=True)
class Entry:
    """A glob over instance-relative paths and the suites that guard them, possibly none."""

    pattern: str
    suites: tuple[str, ...]


@dataclass(frozen=True)
class SuiteMap:
    """The declared suites, in the order answers come in, and the entries that point at them."""

    suites: tuple[Suite, ...]
    entries: tuple[Entry, ...]


def _python(*targets: str) -> tuple[str, ...]:
    return ("python3", "-m", "pytest", "-q", *targets)


# `skill-local` names each skill directory holding a `test_*.py` — pytest skips the `.claude/`
# directories those sit in, so `pytest skills/` collects nothing. `test_suite_map.py` derives the
# list from `git ls-files` and fails when this one drifts from it.
_SKILL_LOCAL_DIRECTORIES = (
    "skills/experimental/.claude/skills/skill-evals/scripts",
    "skills/interactive-product/.claude/skills/project-setup/tests",
    "skills/interactive-product/.claude/skills/project-stamp/tests",
    "skills/pm/.claude/skills/nemawashi-pick/tests",
    "skills/pm/.claude/skills/shukuba-open/tests",
    "skills/pm/.claude/skills/tobiishi-drop/tests",
    "skills/scrum-master/.claude/skills/shukuba-retire/tests",
)

# The tests that read the live `system/` tree — `system/tests/`, this instance's own checks, and the
# tool suites that still read it — and the one tool that walks its links.
_SYSTEM_READERS = (
    "system/tests/",
    "core/tools/test_written_forward.py",
    "core/tools/test_check_vendor_neutrality.py",
    "core/tools/test_templates_are_instance_neutral.py",
    "core/tools/test_journey_status.py",
)

SUITE_MAP = SuiteMap(
    suites=(
        Suite("tools", _python("core/tools/")),
        Suite("launchers", _python("core/launchers/")),
        Suite("hooks", _python(".claude/hooks/")),
        Suite("claude-tests", _python(".claude/tests/")),
        Suite("workflows", ("node", "--test", ".claude/workflows/tests/")),
        Suite("skill-local", _python(*_SKILL_LOCAL_DIRECTORIES)),
        Suite("products", _python("products/")),
        Suite("system-readers", _python(*_SYSTEM_READERS)),
        Suite("journey-links", ("python3", "core/tools/check_journey_links.py", "--repo", ".")),
    ),
    entries=(
        Entry("core/**", ("tools", "launchers", "hooks", "claude-tests", "system-readers")),
        Entry(
            ".claude/**",
            ("tools", "launchers", "hooks", "claude-tests", "workflows", "system-readers"),
        ),
        Entry("skills/**", ("tools", "launchers", "hooks", "skill-local", "system-readers")),
        Entry("system/**", ("system-readers", "journey-links")),
        Entry("products/**", ("products",)),
        Entry("*", ("tools", "launchers", "hooks", "system-readers")),
        Entry("docs/**", ()),
        Entry("about/**", ()),
    ),
)


def _segments_match(segments: list[str], pattern: list[str]) -> bool:
    if not pattern:
        return not segments
    head, rest = pattern[0], pattern[1:]
    if head == "**":
        return any(_segments_match(segments[taken:], rest) for taken in range(len(segments) + 1))
    return bool(segments) and fnmatchcase(segments[0], head) and _segments_match(segments[1:], rest)


def _matches(entry: Entry, path: str) -> bool:
    return _segments_match(path.split("/"), entry.pattern.split("/"))


def check(suite_map: SuiteMap = SUITE_MAP) -> None:
    """Refuse a map that contradicts itself, naming the suite at fault."""
    declared: set[str] = set()
    for suite in suite_map.suites:
        if suite.name in declared:
            raise SuiteMapError(f"suite {suite.name!r} is declared twice — keep one declaration")
        declared.add(suite.name)
    for entry in suite_map.entries:
        for name in entry.suites:
            if name not in declared:
                raise SuiteMapError(
                    f"entry {entry.pattern!r} names suite {name!r}, which is not declared"
                    " — declare it in the map's suites or correct the entry"
                )


def suites_for(paths: list[str], suite_map: SuiteMap = SUITE_MAP) -> list[Suite]:
    """The suites that guard `paths`: the union over every entry matching at least one of them,
    in the map's own suite order, each once."""
    wanted = {
        name
        for entry in suite_map.entries
        if any(_matches(entry, path) for path in paths)
        for name in entry.suites
    }
    return [suite for suite in suite_map.suites if suite.name in wanted]


def unmatched(paths: list[str], suite_map: SuiteMap = SUITE_MAP) -> list[str]:
    """The paths no entry matches, once each, in the order given. Reported, never raised."""
    seen: dict[str, None] = {}
    for path in paths:
        if not any(_matches(entry, path) for entry in suite_map.entries):
            seen.setdefault(path)
    return list(seen)
