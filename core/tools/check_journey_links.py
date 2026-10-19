#!/usr/bin/env python3
"""Resolve every journey pointer in the live seedbeds, docs/findings/ and product docs/, and name
the dead ones.

**Why this exists.** A seed's path spells its *position* — `journey/nemawashi/<seed>.md` is picked,
`unpicked/<seed>.md` is a candidate, `trail/<seed>.md` is retired, `drop/<seed>.md` is killed — so every pick,
un-pick, retire, drop and park renames a file that other seeds cite by path. The five skills that make
those moves (`nemawashi-retire`, `nemawashi-drop`, `nemawashi-unpick`, `shukuba-retire`, `shukuba-park`)
move the file and update nothing pointing at it. `nemawashi-retire` and `nemawashi-drop` run this tool
themselves after the move; the other three leave the surfacing to the session that invoked them.

It is not theoretical. Seven pointer repairs were made by hand on one branch; about a hundred commits
later four of them were dead again, because a routing seed's items named seeds in `unpicked/` that
were then retired to `trail/`. A routing seed's whole mechanism is that its items name the seeds they
route to and those seeds name the item back — the link findable from both ends is the only guard
against a missed tick, and a dead pointer removes the guard silently.

**It reports; it does not block and does not repair.** Blocking a retire is stricter than the journey
wants, and rewriting pointers would edit files nobody asked it to touch. The exit code is information
for a caller, not a gate: the caller surfaces what it finds rather than halting on it.

**Scope: the live seedbeds only** — seed roots, `unpicked/`, and open station roots, at both the
instance and the project layer. `trail/`, `drop/` and `parked/` are deliberately out: a retired seed naming
where a sibling sat when it retired is correct as history, and a repo-wide sweep finds hundreds of
those. Pass `--all` to widen it anyway when auditing.

**Beside the seedbeds, two docs/ folders — the owner's ruling of 2026-09-14.** Each project's
product `docs/`, found through its card's `**Product path:**` (`product_docs_roots`), and the
instance's own `docs/findings/`. Both carry pointers someone follows after the seed they name has
moved: a product companion's `Tracked by:` line names the seed watching an item, and a finding
names the seed it was met on. The companion is the case that made this necessary — it sits in a
product's `docs/`, often in another repository, and a retire broke one in a satellite's product with nothing
reporting it. The rest of the instance's `docs/` (proposals, reviews) stays out, and so does a
`trail/` below either folder, for the seedbeds' own reason. `--all` does not reach into them: it
widens the seedbeds' bins and nothing else. A file inside the instance is reported by its
repo-relative path; an external product's, by its absolute one.

**The line-wrap trap, which is why an eye-check and a naive grep both pass.** Half the dead pointers
found in practice span a line break inside a backtick span, so `grep` for the path finds nothing and
the file reads clean. `BACKTICK_SPAN` is a CommonMark code-span matcher — a run of N backticks opens
and the next run of exactly N closes — so a double-backtick escape or a longer fence is captured
whole rather than mis-paired. Every span is then normalised before resolution, and a path and a
triple take opposite collapses: a path's segments touch directly, so a wrap collapses to nothing; a
triple's three parts are space-separated, so a wrap collapses to a single space instead — collapsing
either one the other way corrupts it. A span that is itself a single-backtick-quoted value (the
`` `x` `` idiom for showing a backtick visibly) has that one quoting pair stripped before matching.

**Four shapes are path pointers.** A path anchored at `system/` names its own project. A routing
seed usually does not: it puts the project in the prose and the path bare in the span,
`journey/nemawashi/unpicked/<seed>.md`, and that one is resolved by searching every project's
`journey/`. A seed citing its own journey drops `journey/` too, `shukuba/trail/<station>.md`, and
that one is resolved against the journey its source sits in (`journey_bases`): a project seed's own
`journey/`, `system/` for the instance seedbed and router, every base for a finding or a product
companion. A seed citing a sibling in its own seedbed drops the kind as well, `unpicked/<seed>.md` or
`trail/<seed>/` — the bin-relative shape, its name always dated so a product document's own
`trail/<doc>/cycle-3.md` is not mistaken for one — and it resolves against the same journey, under
each kind that keeps that bin (`trail/` is all three's, so a same-named seed and station cannot be
told apart — the triple can). Any path shape may end `:<lines>`, which is dropped and the file
checked, or `/` after a dated name, which names a folder and resolves on it. Matching all four is
the point — a shape the tool cannot match produces no finding at
all, so a file full of dead relative pointers reports identically to a clean one. A folder-seed's
own files are a variant of any path shape, one path segment deeper (below).

**The fifth shape is the triple**, `<project> · <kind> · <name>` — one backtick span, middot-
separated (`single_source.md` § *A pointer at a journey artifact names project, kind and name*),
`<kind>` one of `nemawashi` / `shukuba` / `tobiishi`, `<name>` a bare `<YYYY-MM-DD>_<slug>` stem — a
dot is fine (a real artifact's own name may carry one), a trailing `.md` and a slash are not, since
the triple names an artifact, never a file — for a Tobiishi and a folder-seed, the **folder's** own
name, never a file inside it. Where a path pointer spells a journey artifact's *position*, which a pick, un-pick,
retire, drop or park renames out from under it, the triple names the artifact itself: none of its
three parts changes on a move, so it resolves in whichever bin the artifact currently sits — root,
`unpicked/`, `trail/`, `drop/` or `parked/`, whichever its kind keeps. `<project>` is a project name
or the literal `instance` — the app-level seedbed and router (`system/nemawashi/`, `system/shukuba/`),
which sit outside every project and have no instance Tobiishi at all.

**A key may carry a fourth part in front, naming another instance**,
`<instance> · <project> · <kind> · <name>` — a satellite citing its host's journey, which a three-part
key cannot reach because it resolves in the repository being checked. The instance name is resolved
to a root through the host's `system/satellites.md` (`instance_roots`), the host being the instance
holding this core — the pin's source host when the core is a pin (`default_host`) — unless
`--host` names another; the key then resolves there exactly as three parts
resolve here. A name no roster carries is dead and says so, so a typo fails loudly; and a move in the
other instance still shows up as dead here, which a pointer rewritten as prose never does.

**One shape is deliberately not matched: an elided prefix**, `.../tools/journey/nemawashi/<seed>.md`.
Three of those exist and `...` is prose, not a path segment; a tool that resolved it would be
guessing at what the author elided. They are named here rather than left as a silent gap.

**A folder-seed's own files are a variant of the path shapes above, one path segment deeper.**
A 根回し Nemawashi seed is either `<slug>.md` or a folder `<slug>/` holding `seed.md` plus, per
reviewed unit (sealed or halted), `<key>_report.md` and
`<key>_recommendations.md` (`kensaiapp_structure.md` § 2) — nemawashi-only, since a 宿場 Shukuba
station never takes the folder form. A pointer aimed at one of those files is matched the same way
as the flat shape, one path segment deeper. And a pointer still written against the seed's *old*
flat form is not treated as broken by the migration: `resolves()` tries `<slug>/seed.md` once
`<slug>.md` itself is gone, because the idea the pointer names did not move — only its own file did.

**A near-miss triple is reported as malformed, never silently dropped.** The tool's founding
complaint — a shape it cannot match produces no finding at all — applies to the triple too: a span
with a kind typo, the wrong separator, or a missing date is not a live pointer and not a dead one,
but it is not ordinary prose either. `malformed_triples()`/`malformed_links()` name it as a third
category, reported alongside the dead pointers and never counted toward them or the exit code.

Usage:  python3 <CORE>/tools/check_journey_links.py [--repo .] [--host <instance>] [--all] [--quiet]
Exit:   0 no dead pointers · 1 dead pointers found · 2 bad usage
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

__version__ = "1.9.0"

# A backtick span may wrap across lines in prose; capture it whole, then collapse the break.
# CommonMark rule, held exactly: a code span opens on a run of N backticks and closes on the next
# run of exactly N — `` `x` `` opens and closes on TWO, so the single backtick around `x` is
# literal content, not a nested span. The naive `` `([^`]+)` `` pairs the wrong ticks here, leaves
# one tick over, and offsets every span after it in the file. Group 1 is the fence (unused beyond
# fixing its own length); group 2 is the content, as `pointers()` expects.
BACKTICK_SPAN = re.compile(r"(`+)(.+?)\1(?!`)", re.S)

# A journey pointer names a real file under a seedbed or a station folder. Anchored at both ends so a
# prose fragment that merely contains a slash is not mistaken for a path.
_JOURNEY_PATH_FLAT = (
    r"system/(?:projects/[A-Za-z0-9_-]+/journey|nemawashi|shukuba)"
    r"(?:/(?:unpicked|trail|drop|parked))?"
    r"(?:/(?:nemawashi|shukuba|tobiishi))?"
    r"(?:/(?:unpicked|trail|drop|parked))?"
    r"/[A-Za-z0-9_.-]+\.md$"
)

# A FOLDER-SEED VARIANT OF THE PATH SHAPES ABOVE, ONE PATH SEGMENT DEEPER. A 根回し Nemawashi seed is
# either `<slug>.md` or a folder `<slug>/` holding `seed.md` plus, per reviewed unit (sealed or halted), `<key>_report.md` and
# `<key>_recommendations.md` (`kensaiapp_structure.md` § 2). A pointer aimed at one of those adds
# exactly one path segment — the slug — after the same nemawashi anchor and bin the flat shape
# already matches. Nemawashi-only: a 宿場 Shukuba station never takes the folder form, so neither
# anchor below admits `shukuba` or `tobiishi`. Shared by the folder-seed branch of each pointer
# pattern and by `_folder_seed_form()`'s own fallback, so the anchor is written once.
_NEMAWASHI_ANCHOR = (
    r"system/(?:projects/[A-Za-z0-9_-]+/journey/nemawashi|nemawashi)(?:/(?:unpicked|trail|drop))?"
)
_RELATIVE_NEMAWASHI_ANCHOR = r"journey/nemawashi(?:/(?:unpicked|trail|drop))?"

_JOURNEY_PATH_FOLDER_SEED = _NEMAWASHI_ANCHOR + r"/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.md$"

JOURNEY_PATH = re.compile(rf"^(?:{_JOURNEY_PATH_FLAT})|^(?:{_JOURNEY_PATH_FOLDER_SEED})")

# THE SECOND SHAPE, AND WHY IT IS NOT OPTIONAL. A seed routing to another project's seed routinely
# writes the project in prose and the path bare inside the span — "`launchers`' `journey/nemawashi/
# unpicked/<seed>.md`" — so the span itself starts at `journey/`. The anchored pattern above cannot
# match it, and a pointer it cannot match is not reported as anything: it reads exactly like a file
# with no pointers. Measured 2026-09-05 across the 168 live seedbed files: 30 spans of this shape,
# including both halves of a routing seed whose targets had just been dropped, on a run that
# reported the seedbeds clean.
_RELATIVE_JOURNEY_PATH_FLAT = (
    r"journey/(?:nemawashi|shukuba|tobiishi)"
    r"(?:/(?:unpicked|trail|drop|parked))?"
    r"/[A-Za-z0-9_.-]+\.md$"
)

# The relative form of the third shape above — same folder-seed segment, project-relative anchor.
_RELATIVE_JOURNEY_PATH_FOLDER_SEED = (
    _RELATIVE_NEMAWASHI_ANCHOR + r"/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.md$"
)

RELATIVE_JOURNEY_PATH = re.compile(
    rf"^(?:{_RELATIVE_JOURNEY_PATH_FLAT})|^(?:{_RELATIVE_JOURNEY_PATH_FOLDER_SEED})"
)

# THE THIRD SHAPE — KIND-RELATIVE: a span starting at the kind itself, `shukuba/trail/<station>.md`.
# A seed citing its own journey drops `system/projects/<p>/` and `journey/` both, and neither
# pattern above can match what is left, so a dead one read exactly like a clean file: measured
# 2026-09-15, ten dead across seven live seeds on a run reporting every pointer resolves. Same bins
# and the same nemawashi-only folder-seed segment as the project-relative shape, one prefix shorter.
_KIND_RELATIVE_NEMAWASHI_ANCHOR = r"nemawashi(?:/(?:unpicked|trail|drop))?"
_KIND_RELATIVE_PATH_FLAT = (
    r"(?:nemawashi|shukuba|tobiishi)"
    r"(?:/(?:unpicked|trail|drop|parked))?"
    r"/[A-Za-z0-9_.-]+\.md$"
)
_KIND_RELATIVE_PATH_FOLDER_SEED = (
    _KIND_RELATIVE_NEMAWASHI_ANCHOR + r"/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.md$"
)

KIND_RELATIVE_PATH = re.compile(
    rf"^(?:{_KIND_RELATIVE_PATH_FLAT})|^(?:{_KIND_RELATIVE_PATH_FOLDER_SEED})"
)

# THE FOURTH PATH SHAPE — BIN-RELATIVE: a span starting at the bin, `unpicked/<seed>.md`, `trail/<seed>/`.
# A seed citing a sibling in its own seedbed drops the kind as well, and no pattern above matched
# what is left: measured 2026-09-25 in a satellite's live pool, about thirty such spans, three of
# them dead, on a run reporting every pointer resolves. The name must be dated — `trail/prd/cycle-3.md`
# is a product document's own trail, not a journey artifact — and it resolves against the source's
# journey the way the kind-relative shape does, under each kind that keeps that bin.
_DATED_NAME = r"\d{4}-\d{2}-\d{2}_[A-Za-z0-9_.-]+"
BIN_RELATIVE_PATH = re.compile(
    rf"^(?:unpicked|trail|drop|parked)/{_DATED_NAME}(?:\.md|/[A-Za-z0-9_.-]+\.md)$"
)
_BIN_RELATIVE_FLAT_SEED_POINTER = re.compile(
    rf"^(?P<prefix>unpicked|trail|drop)/(?P<slug>{_DATED_NAME})\.md$"
)

# TWO SUFFIXES ANY PATH SHAPE MAY CARRY. A pointer at a place inside a file ends `:<lines>`
# (`:46`, `:46-54`, `:12, 30-31`, the `:L12-L20` citation form) — it still names the file, so the suffix is dropped and the file
# checked. A pointer at a folder — a folder-seed, a Tobiishi — ends `/` after a dated name; it is a
# pointer when the same span with `.md` in place of the slash would be one, and it resolves on the
# folder.
_LINE_RANGE = r"L?\d+(?:[-–]L?\d+)?"
_LINE_SUFFIX = re.compile(rf":{_LINE_RANGE}(?:,\s*{_LINE_RANGE})*$")
_DATED_FOLDER = re.compile(rf"/{_DATED_NAME}/$")

# THE FIFTH SHAPE — THE TRIPLE, `<project> · <kind> · <name>`. A path names a journey artifact's
# *position*, which a pick, un-pick, retire, drop or park renames out from under it; the triple names
# the artifact instead, and none of the three changes on a move (`single_source.md` § *A pointer at a
# journey artifact names project, kind and name*). One backtick span, middot-separated, no slashes —
# the pinned written form, so a reader cannot mistake it for a path and "repair" it by prefixing
# `system/projects/`. `project` is a project name or the literal `instance` (the app-level seedbed/
# router, which has no project of its own). `name` is `<YYYY-MM-DD>_<slug>` — for a Tobiishi and a
# folder-seed, the folder's own name, never a file inside it — so it carries neither `.md` nor a slash.
_TRIPLE_KIND = r"nemawashi|shukuba|tobiishi"
# Takes the path shapes' own filename class after the date, so a stem carrying a dot (a real
# artifact whose own dated slug ends in a second word after a dot) is expressible. The negative
# lookbehind is what still refuses a file: the triple names an artifact, not a file, so a name
# ending `.md` is refused exactly as before, and a slash was never in the class at all.
_TRIPLE_NAME = r"\d{4}-\d{2}-\d{2}_[A-Za-z0-9_.-]+(?<!\.md)"
# THE KEY INTO ANOTHER INSTANCE — the same triple with one part in front,
# `<instance> · <project> · <kind> · <name>`. A satellite cites its host's journey, and a three-part
# key resolves only in the repository being checked, so a correct pointer read as dead and the
# satellite had to rewrite it as prose that no move is ever checked against. The fourth part is
# optional: three parts mean this instance, as before, and the instance name is resolved to a root
# by `instance_roots()`. The kind sits second from the end either way, so the two forms never
# overlap.
JOURNEY_TRIPLE = re.compile(
    r"^(?:(?P<instance>[A-Za-z0-9_-]+)\s*·\s*)?"
    rf"(?P<project>[A-Za-z0-9_-]+)\s*·\s*(?P<kind>{_TRIPLE_KIND})\s*·\s*(?P<name>{_TRIPLE_NAME})$"
)

# The one substitution a flat pointer earns once the seed it names has become a folder: `<slug>.md`
# → `<slug>/seed.md`. `resolves()` tries this only when the literal target is gone.
_FLAT_SEED_POINTER = re.compile(rf"^(?P<prefix>{_NEMAWASHI_ANCHOR})/(?P<slug>[A-Za-z0-9_.-]+)\.md$")
_RELATIVE_FLAT_SEED_POINTER = re.compile(
    rf"^(?P<prefix>{_RELATIVE_NEMAWASHI_ANCHOR})/(?P<slug>[A-Za-z0-9_.-]+)\.md$"
)
_KIND_RELATIVE_FLAT_SEED_POINTER = re.compile(
    rf"^(?P<prefix>{_KIND_RELATIVE_NEMAWASHI_ANCHOR})/(?P<slug>[A-Za-z0-9_.-]+)\.md$"
)


@dataclass(frozen=True)
class Dead:
    """One pointer that does not resolve, and the file that carries it."""

    source: str
    target: str


def _live_files(repo: Path, everywhere: bool) -> list[Path]:
    """The files whose pointers are checked.

    Live means a seed or station that someone may still act on: the seedbed roots, the candidate
    pools, and the open station roots. A `trail/` seed is a record of finished work and a `drop/` seed
    a record of killed work; the pointers of both are correct as history, so they are out unless
    `--all` says otherwise. A folder-seed is scanned whole — `seed.md` and every file
    beside it, such as a recommendations file or a retire report, each live for as long as its seed
    is. A folder-seed is found by its own `seed.md`, which is why the bins beside it stay out: a bin
    holds seeds, never a `seed.md` of its own. It follows its flat counterpart's bin rule, and it is
    nemawashi-only, since a station never takes the folder form.
    """
    roots: list[tuple[Path, bool]] = []
    for base in [repo / "system"] + sorted((repo / "system" / "projects").glob("*/journey")):
        for folder, is_nemawashi in (("nemawashi", True), ("shukuba", False)):
            d = base / folder
            if not d.is_dir():
                continue
            roots.append((d, is_nemawashi))
            if everywhere:
                roots += [
                    (d / sub, is_nemawashi) for sub in ("unpicked", "trail", "drop", "parked")
                ]
            else:
                roots.append((d / "unpicked", is_nemawashi))

    seen: dict[Path, None] = {}
    for d, is_nemawashi in roots:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.md")):
            if f.name != "README.md":
                seen[f] = None
        if is_nemawashi:
            for seed_md in sorted(d.glob("*/seed.md")):
                for f in sorted(seed_md.parent.glob("*.md")):
                    seen[f] = None
    return list(seen)


# A card's value runs to the first space or `<`: the stamped card follows the path with an HTML
# comment, and an unstamped one still holds the template's `<path>`, which names no folder at all.
_PRODUCT_PATH_LINE = re.compile(r"^\*\*Product path:\*\*[ \t]*(?P<path>[^\s<]+)", re.M)


def product_docs_roots(repo: Path) -> list[Path]:
    """The `docs/` folder each project card's `**Product path:**` names, where that folder exists.

    A relative path sits under the instance and an absolute one is taken as written — the rule the
    card's own comment states. Two cards naming one product give one folder; a card naming no
    product, or a product with no `docs/`, gives none.
    """
    roots: dict[Path, None] = {}
    for card in sorted((repo / "system" / "projects").glob("*/project.md")):
        match = _PRODUCT_PATH_LINE.search(card.read_text(encoding="utf-8"))
        if not match:
            continue
        docs = repo / match["path"] / "docs"
        if docs.is_dir():
            roots[docs] = None
    return list(roots)


# Of the instance's own docs/, only findings/ is read — the owner's ruling of 2026-09-14, which
# names docs/findings and rules proposals out; reviews/ falls with proposals.
_FINDINGS = Path("docs") / "findings"


def docs_roots(repo: Path) -> list[Path]:
    """The docs/ folders read beside the live seedbeds: the instance's `docs/findings/`, where it
    exists, then each product's `docs/` (`product_docs_roots`)."""
    findings = repo / _FINDINGS
    return ([findings] if findings.is_dir() else []) + product_docs_roots(repo)


def docs_files(roots: Iterable[Path]) -> list[Path]:
    """Every markdown file under the given roots, at any depth, in path order, each once.

    A `trail/` folder anywhere below a root is left out: a product retires an answered companion
    there whole, and what it holds is correct as history — the same reason the seedbeds' own
    `trail/` stays out. A root that does not exist contributes nothing.
    """
    files: dict[Path, None] = {}
    for root in roots:
        for f in sorted(root.rglob("*.md")):
            if "trail" not in f.relative_to(root).parts[:-1]:
                files[f] = None
    return list(files)


def _files_in_scope(repo: Path, everywhere: bool) -> list[Path]:
    """The live seedbeds, widened to their other bins under `everywhere`, then the docs scope —
    which `everywhere` leaves as it is, by the owner's ruling of 2026-09-14."""
    return list(dict.fromkeys(_live_files(repo, everywhere) + docs_files(docs_roots(repo))))


def _source_name(repo: Path, f: Path) -> str:
    """A file inside the instance by its repo-relative path; a product outside it by where it is,
    the only name that finds it."""
    return (f.relative_to(repo) if f.is_relative_to(repo) else f).as_posix()


def _unwrap_self_quote(candidate: str) -> str:
    """Strip one literal backtick from each end when the span's whole content is itself a single-
    backtick-quoted value — the display idiom for showing a backtick around an example inside a
    longer escape, `` `path` `` to visibly show the backtick around `path`. A length-1 fence can
    never produce this (`BACKTICK_SPAN`'s own backref makes its content backtick-free by
    construction), so this only ever touches a fence of two or more."""
    if len(candidate) >= 2 and candidate[0] == "`" and candidate[-1] == "`":
        inner = candidate[1:-1]
        if not inner.startswith("`") and not inner.endswith("`"):
            return inner.strip()
    return candidate


def _span_candidate(raw: str) -> str:
    """The one normalised string a backtick span's raw content resolves to, before shape-matching.

    A middot never appears in a path pointer, so its presence in the RAW span (before either
    collapse runs) is what tells a triple candidate from a path one — checked before collapsing,
    because the two forms need opposite collapses. A path's segments touch directly, so a wrap
    collapses to nothing. A triple's three parts are space-separated, so collapsing to nothing
    would merge them (or, worse, merge prose sharing the span straight into the project) — a wrap
    there collapses to a single space instead. Either way, a self-quoting escape is then unwrapped.
    """
    if "·" in raw:
        candidate = re.sub(r"\s+", " ", raw).strip()
        # Re-space around the separator too, uniformly: the collapse above is not symmetric around
        # it — a break right after `·` eats the space that followed it but leaves the one before,
        # so the same triple would otherwise come back looking different depending on exactly
        # where inside the span it wrapped.
        candidate = re.sub(r"\s*·\s*", " · ", candidate)
    else:
        candidate = re.sub(r"\s*\n\s*", "", raw).strip()
    return _unwrap_self_quote(candidate)


def pointers(text: str) -> list[str]:
    """Every journey pointer a document names, with line-wrapped backtick spans repaired first.

    Five shapes come back, each as written except that a `:<lines>` suffix is dropped. A caller
    tells a path from a triple on the presence of a slash — a triple never has one, by construction
    (its `name` admits neither `.md` nor `/`) — and tells the four path shapes apart by how the span
    starts, because that is exactly what decides how each is resolved: a leading `system/` names its
    own project, a leading `journey/` leaves it to the prose around the span, a leading kind or bin
    leaves it to the source file's own journey, and a triple carries its project as its own first
    part — or as its second, after the instance it names, when it has four. A path ending `/` names a folder.
    """
    out: list[str] = []
    for _fence, raw in BACKTICK_SPAN.findall(text):
        candidate = _span_candidate(raw)
        if JOURNEY_TRIPLE.match(candidate):
            out.append(candidate)
            continue
        unsuffixed = _LINE_SUFFIX.sub("", candidate)
        shaped = (
            unsuffixed[:-1] + ".md" if _DATED_FOLDER.search("/" + unsuffixed) else unsuffixed
        )
        if _is_path_shape(shaped):
            out.append(unsuffixed)
    return out


def _is_path_shape(candidate: str) -> bool:
    return bool(
        JOURNEY_PATH.match(candidate)
        or RELATIVE_JOURNEY_PATH.match(candidate)
        or KIND_RELATIVE_PATH.match(candidate)
        or BIN_RELATIVE_PATH.match(candidate)
    )


@dataclass(frozen=True)
class Malformed:
    """One backtick span shaped like a near-miss triple, and the file that carries it. Never a
    dead pointer and never a live one — a third category, reported so a broken citation is visible
    rather than silently dropped."""

    source: str
    span: str


# A near-miss triple may use any middot-*ish* separator — a wrong one is exactly one of the ways a
# triple is malformed — where a live one (`JOURNEY_TRIPLE`) is pinned to the one canonical U+00B7.
# U+00B7 MIDDLE DOT (the pinned separator), U+30FB KATAKANA MIDDLE DOT, U+2022 BULLET, U+22C5 DOT
# OPERATOR, U+2219 BULLET OPERATOR, U+0387 GREEK ANO TELEIA — chosen because each renders as a
# small centered dot indistinguishable from the pinned one at reading size.
_MIDDOT_ISH = "·・•⋅∙·"
_MIDDOT_SPLIT = re.compile(f"[{_MIDDOT_ISH}]")
_KINDS = ("nemawashi", "shukuba", "tobiishi")
_DATE_LIKE = re.compile(r"^\d{4}-\d{2}-\d{2}")
_PLACEHOLDER_CHARS = ("<", ">", "…")


def _levenshtein(a: str, b: str) -> int:
    """Edit distance between two strings — plain DP, no third-party package for one small check
    (`quality_gates.md` § What is not installed: this house installs none)."""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, start=1):
            cur[j] = min(
                prev[j] + 1,
                cur[j - 1] + 1,
                prev[j - 1] + (ca != cb),
            )
        prev = cur
    return prev[-1]


def _kind_like(part: str) -> bool:
    """Case-insensitive exact match, or a spelling one edit away — `shukba` for `shukuba`."""
    lowered = part.strip().lower()
    return any(lowered == kind or _levenshtein(lowered, kind) <= 1 for kind in _KINDS)


def _date_like(part: str) -> bool:
    return bool(_DATE_LIKE.match(part.strip()))


def malformed_triples(text: str) -> list[str]:
    """Every backtick span shaped like a near-miss triple: three middot-ish separated parts, or four
    for a key into another instance, with the kind's part kind-like or the last date-like, that
    `JOURNEY_TRIPLE` does not already match.

    A qualifying span is reported only when it cannot plausibly be ordinary prose — a three-part
    middot ledger entry (`blocking · skill-general · stability`) or a grammar placeholder
    (`<project> · <kind> · <name>`) splits into three parts too, so the trigger is narrow (kind-like
    or date-like) and a part carrying `<`, `>` or `…` is never reported at all.
    """
    out: list[str] = []
    for _fence, raw in BACKTICK_SPAN.findall(text):
        if not _MIDDOT_SPLIT.search(raw):
            continue
        candidate = _unwrap_self_quote(re.sub(r"\s+", " ", raw).strip())
        parts = [p.strip() for p in _MIDDOT_SPLIT.split(candidate)]
        if len(parts) not in (3, 4) or any(not p for p in parts):
            continue
        if any(ch in part for part in parts for ch in _PLACEHOLDER_CHARS):
            continue
        if JOURNEY_TRIPLE.match(candidate):
            continue  # a genuine, resolvable-shaped triple — not a near-miss
        if _kind_like(parts[-2]) or _date_like(parts[-1]):
            out.append(candidate)
    return out


def malformed_links(repo: Path, everywhere: bool = False) -> list[Malformed]:
    """Every near-miss triple in the live seedbeds and the docs scope — same scope rule as
    `dead_links()`."""
    found: list[Malformed] = []
    for f in _files_in_scope(repo, everywhere):
        try:
            text = f.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        rel = _source_name(repo, f)
        for span in dict.fromkeys(malformed_triples(text)):
            found.append(Malformed(rel, span))
    return found


def _folder_seed_form(target: str) -> str | None:
    """The folder-seed path a flat nemawashi pointer resolves to once the seed it names has
    become a folder, or `None` when `target` is not shaped like a flat seed pointer.
    `<prefix>/<slug>.md` → `<prefix>/<slug>/seed.md` — the one substitution the plan's own
    "Decided here" note fixes: a pointer written against a seed's old flat form still resolves
    once that seed becomes a folder, because the idea the pointer names did not move."""
    for pattern in (
        _FLAT_SEED_POINTER,
        _RELATIVE_FLAT_SEED_POINTER,
        _KIND_RELATIVE_FLAT_SEED_POINTER,
        _BIN_RELATIVE_FLAT_SEED_POINTER,
    ):
        match = pattern.match(target)
        if match:
            return f"{match['prefix']}/{match['slug']}/seed.md"
    return None


# The bins each kind keeps, in the order the seedbeds document them (`kensaiapp_structure.md` §1,
# §2). `""` is the seedbed/station root itself. Shukuba carries no candidate pool and no kill bin —
# `unpicked` is nemawashi-only. Tobiishi carries `trail`, where a unit is sealed, and `drop`, where
# one is set down unsealed — a folder key is never a candidate.
_TRIPLE_KIND_BINS: dict[str, tuple[str, ...]] = {
    "nemawashi": ("", "unpicked", "trail", "drop"),
    "shukuba": ("", "parked", "trail"),
    "tobiishi": ("", "trail", "drop"),
}


def _kinds_keeping(bin_: str) -> tuple[str, ...]:
    """The kinds whose folders hold `bin_` — `unpicked/` is nemawashi's alone, `parked/` shukuba's.
    `trail/` is kept by all three, so a bin-relative `trail/<name>` cannot say which kind it means:
    where a seed and a station share a name, either one keeps the pointer alive. The triple is
    the form that says."""
    return tuple(kind for kind, bins in _TRIPLE_KIND_BINS.items() if bin_ in bins)


def _resolves_triple(repo: Path, project: str, kind: str, name: str) -> bool:
    """Whether a triple names an artifact that is there, in any bin its kind keeps.

    `instance` is not a project — it is the app-level seedbed/router, `system/<kind>/` rather than
    `system/projects/<project>/journey/<kind>/` (`kensaiapp_structure.md` §1). There is no instance
    Tobiishi at all, so `instance · tobiishi · …` finds no base directory and resolves false, exactly
    like any other kind with nothing there — no special case is needed.

    A Tobiishi is named by its folder alone, so it resolves on the folder's existence — never on a
    file inside it. A nemawashi name resolves either as the flat `<name>.md` or, once the seed has
    become a folder, as the folder `<name>/` itself — same folder-by-name rule, tried alongside the
    flat form because the triple names the idea rather than which shape it currently takes. A
    shukuba station is never a folder, so only the flat form applies.
    """
    base = (
        repo / "system" / kind
        if project == "instance"
        else repo / "system" / "projects" / project / "journey" / kind
    )
    if not base.is_dir():
        return False
    for bin_ in _TRIPLE_KIND_BINS[kind]:
        d = base / bin_ if bin_ else base
        if kind == "tobiishi":
            if (d / name).is_dir():
                return True
            continue
        if (d / f"{name}.md").exists():
            return True
        if kind == "nemawashi" and (d / name).is_dir():
            return True
    return False


def journey_bases(repo: Path, source: Path) -> list[Path]:
    """The folders a kind- or bin-relative pointer written in `source` resolves against.

    A reader takes `shukuba/trail/<station>.md` from the file it is written in. A source anywhere
    under a project's `journey/` — a seed, a station, a folder-seed's own files, any bin — gives
    that one journey. A source in the instance seedbed or router gives `system/`, which holds the
    instance's `nemawashi/` and `shukuba/`. A source with no journey of its own — a finding, a
    product companion, a file outside the instance — gives every base, the same search the
    project-relative shape makes, because nothing narrows it.
    """
    system = repo / "system"
    parts = source.relative_to(system).parts if source.is_relative_to(system) else ()
    if len(parts) > 2 and parts[0] == "projects" and parts[2] == "journey":
        return [system / "projects" / parts[1] / "journey"]
    if parts and parts[0] in ("nemawashi", "shukuba"):
        return [system]
    return [system] + sorted((system / "projects").glob("*/journey"))


def resolves(
    repo: Path, target: str, bases: Sequence[Path], instances: Mapping[str, Path] | None = None
) -> bool:
    """Whether a pointer names a file that is there — or, ending `/`, a folder.

    A bin-relative path is resolved like a kind-relative one, against `bases`, under each kind that
    keeps its bin (`_kinds_keeping`).

    A triple is resolved against the artifact it names, in any position its kind keeps
    (`_resolves_triple`) — in `repo` when it has three parts, and in the root `instances` gives its
    first part when it has four; a name `instances` does not carry resolves false. Position never
    enters the triple itself, so there is nothing here to try twice the way the path shapes below
    do.

    A kind-relative path names no project and no `journey/`, so it resolves against `bases` — the
    folders its source gives (`journey_bases`) — and is alive when any one of them carries it, or
    carries its folder-seed form. Never every project's journey for a project source: that would
    call it alive on the strength of another project's file, which a reader of the source never
    looks in.

    An anchored path is checked where it points. A project-relative one names no project, so it is
    searched under every project's `journey/` and resolves if any one of them carries it — the
    reader's own resolution, which is to look in the project the surrounding prose named. Matching
    on the whole relative path rather than the filename is what keeps that honest: seed basenames
    are NOT unique across this tree — `find system/projects/*/journey -name '*.md' | sed 's#.*/##'
    | sort | uniq -d` names the duplicates, and it is not empty — so a basename search would call
    a pointer alive on the strength of a different project's file.

    A flat pointer that no longer resolves gets one more try, at the folder-seed form
    (`_folder_seed_form`) — `<slug>.md` resolves when `<slug>/seed.md` exists in its place.
    """
    triple = JOURNEY_TRIPLE.match(target)
    if triple:
        root = repo if triple["instance"] is None else (instances or {}).get(triple["instance"])
        if root is None:
            return False  # an instance no roster names — dead, and `_why()` says which
        return _resolves_triple(root, triple["project"], triple["kind"], triple["name"])
    folder = target.endswith("/")
    target = target.rstrip("/")
    target_is = Path.is_dir if folder else Path.exists
    if BIN_RELATIVE_PATH.match(target) or (folder and BIN_RELATIVE_PATH.match(target + ".md")):
        folder_form = _folder_seed_form(target)
        return any(
            target_is(base / kind / target)
            or (folder_form is not None and (base / kind / folder_form).exists())
            for base in bases
            for kind in _kinds_keeping(target.split("/", 1)[0])
        )
    if folder:
        if target.startswith("journey/"):
            return any(p.is_dir() for p in (repo / "system" / "projects").glob(f"*/{target}"))
        if KIND_RELATIVE_PATH.match(target + ".md"):
            return any((base / target).is_dir() for base in bases)
        return (repo / target).is_dir()
    if KIND_RELATIVE_PATH.match(target):
        folder_form = _folder_seed_form(target)
        return any(
            (base / target).exists() or (folder_form is not None and (base / folder_form).exists())
            for base in bases
        )
    if not target.startswith("journey/"):
        if (repo / target).exists():
            return True
        folder_form = _folder_seed_form(target)
        return folder_form is not None and (repo / folder_form).exists()
    if any((repo / "system" / "projects").glob(f"*/{target}")):
        return True
    folder_form = _folder_seed_form(target)
    return folder_form is not None and any(
        (repo / "system" / "projects").glob(f"*/{folder_form}")
    )


def instance_name(root: Path) -> str:
    """An instance's own name: the heading of its `kensaiapp.md`, which every instance is stamped
    with (`kensaiapp_md_template.md` opens `# <instance>`), else its folder's name."""
    try:
        first = (root / "kensaiapp.md").read_text().splitlines()[0]
    except (OSError, UnicodeDecodeError, IndexError):
        return root.name
    return first[2:].strip() if first.startswith("# ") and first[2:].strip() else root.name


def instance_roots(repo: Path, host: Path) -> dict[str, Path]:
    """Every instance a four-part key may name, by name: the host, the repository being checked,
    and each satellite the host's `system/satellites.md` lists with its path.

    The host is where the roster lives because it is the one instance that knows every other — a
    satellite knows its host only as the core it reads, and nothing of its siblings. The roster
    itself is read by `check_satellites.read_roster`, so its row shape has one reader. A name the
    host or the repository declares for itself wins over a roster row that reuses it: an
    instance's own heading is the more direct statement of what it is called."""
    roots = {instance_name(host): host, instance_name(repo): repo}
    if (host / "system" / "satellites.md").is_file():
        from check_satellites import read_roster

        for satellite in read_roster(host):
            roots.setdefault(satellite.name, satellite.path)
    return roots


def default_host(core_dir: Path) -> Path:
    """The instance holding `core_dir` — or, when `core_dir` is a pin's copy, the host the pin was
    made from (`pin.of_core`). A pin holds `core/`, `.claude/` and `skills/` and no `system/`, so
    its own folder has no roster to read; a satellite's run reads its core through a pin."""
    import pin

    made_from = pin.of_core(core_dir)
    return made_from.source_host_root if made_from is not None else core_dir.parent


def _why(target: str, instances: Mapping[str, Path]) -> str:
    """The reason printed beside a dead four-part key whose instance is the problem, else `""`."""
    triple = JOURNEY_TRIPLE.match(target)
    if not triple or triple["instance"] is None:
        return ""
    root = instances.get(triple["instance"])
    if root is None:
        return f"no instance named {triple['instance']} (known: {', '.join(sorted(instances))})"
    if not root.is_dir():
        return f"instance {triple['instance']} is not on disk at {root}"
    return ""


def dead_links(
    repo: Path, everywhere: bool = False, instances: Mapping[str, Path] | None = None
) -> list[Dead]:
    """Every pointer in the live seedbeds and the docs scope that does not resolve against disk.

    `instances` maps each instance name a four-part key may carry to that instance's root
    (`instance_roots()`); with none given, only `repo`'s own name resolves."""
    if instances is None:
        instances = {instance_name(repo): repo}
    found: list[Dead] = []
    for f in _files_in_scope(repo, everywhere):
        try:
            text = f.read_text()
        except (OSError, UnicodeDecodeError):
            continue  # unreadable is not a dead pointer; it is a different problem
        rel = _source_name(repo, f)
        bases = journey_bases(repo, f)
        for target in dict.fromkeys(pointers(text)):
            if not resolves(repo, target, bases, instances):
                found.append(Dead(rel, target))
    return found


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Name the journey pointers that no longer resolve. Reports; never repairs."
    )
    ap.add_argument("--repo", default=".", help="instance root (default: the working directory)")
    ap.add_argument(
        "--host",
        default=None,
        help="the instance whose system/satellites.md names every instance a four-part key may"
        " carry (default: the instance holding this core, or the host a pinned core was copied from)",
    )
    ap.add_argument(
        "--all",
        action="store_true",
        help="widen the seedbeds to trail/, drop/ and parked/ too — for an audit, not for a"
        " journey move; docs/findings/ and product docs/ are read the same either way",
    )
    ap.add_argument("--quiet", action="store_true", help="print nothing; use the exit code")
    args = ap.parse_args(argv)

    repo = Path(args.repo).resolve()
    if not (repo / "system").is_dir():
        print(f"no system/ under {repo} — is this an instance root?", file=sys.stderr)
        return 2

    host = Path(args.host).resolve() if args.host else default_host(Path(__file__).resolve().parent.parent)
    instances = instance_roots(repo, host)
    found = dead_links(repo, args.all, instances)
    malformed = malformed_links(repo, args.all)
    if args.quiet:
        return 1 if found else 0

    seedbeds = "every seedbed position" if args.all else "the live seedbeds"
    scope = f"{seedbeds}, docs/findings/ and product docs/"
    if not found:
        print(f"journey links: every pointer in {scope} resolves.")
    else:
        print(f"journey links: {len(found)} dead in {scope}.\n")
        by_source: dict[str, list[str]] = {}
        for d in found:
            by_source.setdefault(d.source, []).append(d.target)
        for source in sorted(by_source):
            print(source)
            for target in by_source[source]:
                why = _why(target, instances)
                print(f"    -> {target}" + (f"\n       ({why})" if why else ""))
        print(
            "\nEach names a file that is not there. A seed moves when it is picked, un-picked or"
            "\nretired, so the target has usually changed folder rather than gone. This tool never"
            "\nrepairs."
        )

    if malformed:
        # A third category — never counted as dead and never a live pointer, reported so a shape
        # the strict grammar cannot match does not read exactly like a clean file.
        print(f"\njourney links: {len(malformed)} malformed triple(s) in {scope} — not counted as"
              " dead.\n")
        by_source_m: dict[str, list[str]] = {}
        for m in malformed:
            by_source_m.setdefault(m.source, []).append(m.span)
        for source in sorted(by_source_m):
            print(source)
            for span in by_source_m[source]:
                print(f"    -> `{span}`")

    return 1 if found else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
