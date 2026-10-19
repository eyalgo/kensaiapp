#!/usr/bin/env python3
"""A vendored file may not name a path only this host resolves, nor a product any of them builds.

**Why this exists.** Every file under `core/` is vendored: every satellite binds it and reads the
same bytes, so a file here naming a path only the host carries is a file a satellite reads and
finds nothing at (`core/doctrine/setup/kensaiapp_structure.md` § Prompts layer, which
states the rule and permits exactly two forms — a placeholder or glob, or a literal host path
explicitly marked as host-only provenance). `test_templates_are_instance_neutral.py` already
guards this for `core/templates/**/*.md` — 64 of 275 tracked files under `core/`. This widens the
same guarantee to every tracked file under `core/` and, by the owner's ruling of 2026-08-31, under
`.claude/skills/` too — a consumer satellite then linked that directory whole, and a defect there
had already been found once. No satellite links it now (`link_satellite.py`), and it stays in scope. The grouped root `skills/` is read on the same ground: a satellite admits a
group by `--add-dir` and reads the same bytes (`kensaiapp_structure.md` § Root, `skills/`). It sits beside `test_templates_are_instance_neutral.py`, not in place of
it; whether the narrow one is later absorbed is not this station's call.

**What counts as a hit — two independent kinds, reported once per line.**

- A **host-path** hit: `system/projects/<segment>/` where `<segment>` names a real project of this
  instance, read off `system/projects/` at run time — the way
  `test_templates_are_instance_neutral.py` already does — so a project added tomorrow is covered
  without anyone remembering to add it here. A placeholder (`<name>`) or a glob (`*`) does not match
  the segment's character class and is never a hit; a segment naming something that is not a real
  project directory is not a hit either (a bare identity token such as
  `system/projects/example-product`).
- A **journey-stem** hit: a dated journey-artifact stem, `<YYYY-MM-DD>_<slug>`, with or without a
  trailing `.md`, anywhere in the line, with or without a `system/projects/<name>/…/` prefix. A
  seed's path spells its position, so a pick, an unpick or a retire renames the file and kills
  the pointer on the host too — not only in a satellite (the owner's ruling of 2026-08-31,
  "don't point to journeys in core or doctrine"). A stem immediately followed by `/` names a
  folder, not a journey artifact (`kensaiapp_structure.md` § Root's
  `2026-08-03_perplexity-outside-review/` is the live case this excludes) — decided procedurally
  after the match, never by a regex lookahead the greedy `+` could backtrack behind and re-trip
  on a truncated slug.

A line tripping several kinds is reported once, not once per kind: it names one line worth
repairing, however many independent reasons it is wrong.

**The third kind is a different rule with the same remedy.** `shared_core_instance.md` § *So a
shared file names no product* — "Name no product in a file a satellite reads" — is about a NAME,
where the two kinds above are about a PATH. It was unenforced, and that doctrine records the cost
in its own words: the layer kept re-acquiring names after each sweep, six launchers to eleven
between 2026-09-01 and 2026-09-05, "without anyone breaking a rule". A rule with no surface does
not fire. This is the surface.

**Five decisions this file's own station owed, and the reasons — the first three from the check's
first station, the last two from the station that made every hit either excused or repaired.**

1. **One scan over the whole vendored layer, not a check per layer.** One rule, one check — a
   per-layer split would need each layer (doctrine's provenance citations, a launcher's shell
   comments) to state its own permitted forms before any of them has one.
2. **The permitted marked-provenance form is an allowlist entry with a stated reason, in one
   file — never a code-span strip.** `vendor_neutrality_allowlist.json`, `path:<anchor>` keyed —
   the anchor a snippet of the excused line's own text, resolved by substring match at run time —
   is what "marked as host-only provenance" means here: a reader audits every exception in one
   place. A key pinned to the line number was tried first and broke on its own worked example:
   written against `kensaiapp_structure.md:921`, it went stale four commits later when an
   unrelated doctrine edit nine lines above the site re-numbered it to `:930`, and the run started
   reporting a hit the entry existed to excuse — the site hadn't moved, only its line number had,
   and the key was made of the wrong thing. The anchor survives exactly that edit: it names what
   the entry excuses, not where it sat. Code-span stripping was refused too — a path in this
   instance is written inside backticks far more often than not, and a strip built for a rule
   about *phrases* (`written_forward.py:50-55`, right for the phrases it guards) erases 17 of the
   19 host references live in `core/` today and leaves a check that reports almost nothing and
   looks like one that works. The principle transfers; the mechanism does not. The file stating
   the rule is not exempt from it (owner's call, 2026-08-31) — its own worked example,
   `kensaiapp_structure.md` § Prompts layer, earns an allowlist entry rather than a blanket file
   exemption.
3. **Journey citations are this check's own criterion, not `check_journey_links.py` widened.** That
   tool resolves a pointer against disk and answers *is it dead*, scoped to `system/` because
   that is where a live seedbed lives (`:75`). This one answers a different question — *may it
   be here at all* — true even of a pointer that resolves perfectly; a dead journey pointer from
   `core/` is invisible to that tool's scan regardless, and is exactly the gap this check closes
   for that one path.
4. **The allowlist file is excluded from its own scan.** Its key is now a text anchor (decision 2),
   so `vendor_neutrality_allowlist.json` spells the literal pattern this check catches, once per
   entry — the check would report itself, and the sweep would never converge. `_tracked_files`
   already excludes `test_`-prefixed files for the same reason: a fixture and an allowlist anchor
   both exist to *contain* the string this check looks for.
5. **A record — an artifact that exists to hold what was true at a moment — is out of scope.** An
   `evidence/` path segment, a `code-integrity-report.md` wherever it sits, and a ratification
   verdict under a skill's `references/` are excluded from `_tracked_files` by path shape.
   Rewriting one falsifies the record it holds. **The owner ruled this directly on 2026-09-01** —
   no check inside records — after it was put to them as a reading of their own live-versus-retired
   split: on 2026-08-31 they narrowed `written_forward.py`'s carve-out to count live seeds
   and stations while leaving trail entries, cold-read reports and proposals out
   (`written_forward.py:36-39`, "The rule binds every authored file, but a **record** ... exists to
   hold what was true at a moment ... Scanning records would contradict the doctrine's own
   carve-out"). This check declines to disagree with that line.

**Two decisions the product-name kind owed, beyond the five above.**

6. **Only an EXTERNAL product contributes a name, and that is what makes the kind usable at all.**
   An instance declares its own machinery with a relative product path (`core/tools`,
   `.claude/skills`, `core/doctrine`); taking those basenames would make `tools`, `skills` and
   `doctrine` product names and fire this check on most of the vendored layer, which is a check
   nobody reads. An external product is declared with an absolute path. That split is not invented
   here — it is the same test every launcher already applies to decide whether a run needs
   `--add-dir` for its product — so the rule this check enforces and the rule the launchers follow
   cannot drift apart.
7. **The names are reached in two steps, and the roots that could not be read are named.**
   `system/satellites.md` carries satellite PATHS and states that product names are "deliberately
   absent", each satellite declaring those in its own project cards — so the roster gives the roots
   and each root's `system/projects/*/project.md` gives the names. This is the one kind whose
   coverage is not decided by `repo` alone: a satellite that is absent, moved or unreadable
   contributes fewer names and makes the run quieter, which is indistinguishable from a clean tree
   by anything a reader can see. So `product_name_sources` carries its unread roots and `main`
   prints them, exactly as the scan already states the roots it walks.

**What is deliberately not a hit.**

- An allowlisted site (`vendor_neutrality_allowlist.json`, keyed `path:<anchor>` — the anchor a
  snippet of the excused line's own text, not a line number — each entry carrying a non-empty
  reason) — decision 2 above. A stale entry (an anchor no longer matching any hit line in its
  path) is reported separately, so the file cannot quietly outlive what it excuses.
- A file whose name starts with `test_` — a test's fixtures exist to name the very strings this
  check looks for, and counting them would make every future test author dodge this check by
  writing one.
- The allowlist file itself, and a record — decisions 4 and 5 above.

**An allowlist entry may not excuse a journey pointer.** A citation of a seed or a station in
vendored machinery is not a provenance case the allowlist can cover: the owner ruled on 2026-08-31
that settled machinery cites the fact's owner, never a seed or a station, and that naming one
instead of pathing it is the half-measure rather than the fix. A journey-stem hit is therefore
always repaired, never entered. Stated here because it was not, and a sweep on 2026-09-01 excused
nine of them as ordinary provenance before they were repaired.

**Where it looks.** Every file `git ls-files` tracks under `core/`, `.claude/` and `skills/`, and
the root files a release ships beside them (`ROOT_FILES`). And each example project a release ships
whole — `system/satellites.md` § *Projects a release ships* names them, and each one's
`system/projects/<name>/` and in-repo product are read too. There only the names and the home path
are hits: the project ships with its own journey, so a path into this instance or a dated stem
points at something the reader has, and a name its row says it carries is not a hit. Its `trail/`
is a record and is left out, beside decision 5's.
Not `about/`, which a release also ships:
its files are handed over byte for byte by the instance that manages them and are never edited here
(`kensaiapp_structure.md` § Root, `about/`), so a hit there is reported back to that instance, not
repaired by this one.

**A `test_`-prefixed file is out of scope for the product-name kind too**, and the doctrine agrees
rather than merely permitting it: "In test fixtures the name is a stand-in and is simply renamed".
An invented fixture name is not a product and is not covered at all.

**It reports; it does not block and does not repair.** Repairing the live references is the next
station's, once this one has proven the check sees them.

Usage:  python3 <CORE>/tools/check_vendor_neutrality.py [--repo .] [--quiet]
Exit:   0 no hits and no stale allowlist entries · 1 hits or stale entries found · 2 bad usage
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

__version__ = "1.5.0"

# The three vendored roots this check reads. Every satellite binds `core/` live through `<CORE>`;
# `.claude/skills/` reached a consumer satellite whole and a producer per-skill when the owner
# ruled it in scope (2026-08-31), on the grounds that a defect had already been found there. No
# satellite links it since every host skill was grouped; the ruling is unchanged.
# `skills/` holds the grouped skills, which a satellite admits by `--add-dir` — a skill moved into a
# group is the same vendored file one directory deeper, so the move must not take it out of scope.
# `.claude/` is read whole, not only its skills: a release carries the agents, hooks, workflows and
# settings too (the owner, 2026-10-03), so a name there ships the same as one in `core/`.
ROOTS = ("core/", ".claude/", "skills/")

# The root files a release ships beside the three roots (the owner, 2026-10-06: `AGENTS.md`,
# `CLAUDE.md` and `Containerfile` ship, and must be general). Read the same way as a root's files.
ROOT_FILES = (
    "AGENTS.md",
    "CLAUDE.md",
    "Containerfile",
    ".gitignore",
    ".env.example",
    ".providers.toml.example",
)

# The one permitted form of a literal host path: explicitly marked as host-only provenance, one
# entry per site, in one file a reader can audit whole — never a marker scattered through prose
# (`kensaiapp_structure.md` § Prompts layer permits exactly this form, and no other).
ALLOWLIST_PATH = Path(__file__).with_name("vendor_neutrality_allowlist.json")

# The allowlist file's own path, relative to the repo root it is always found at (it sits beside
# this module, whose own location is fixed under `core/tools/`) -- the form `_tracked_files`
# compares a `git ls-files` relative path against. Not derived from `ALLOWLIST_PATH` at call time:
# a fixture repo's `ALLOWLIST_PATH` (patched in tests via `cvn.ALLOWLIST_PATH`) may sit outside
# that fixture's own tree entirely, so the exclusion names the one real site by its own relative
# path -- the same fixed-string shape `ROOTS` already uses -- rather than re-deriving it per call.
_ALLOWLIST_RELATIVE = "core/tools/vendor_neutrality_allowlist.json"

# A segment is captured whenever it looks like an identity, whether or not a "/" follows it — a
# bare identity token (`system/projects/example-product`, no trailing slash) and a proper path with a
# trailing slash are the same kind of claim, and both are judged by the same test: does the
# captured segment name a real project of this instance. (This module's own citations below are
# deliberately never phrased in that shape — a comment naming a real project here would trip its
# own check, the same trap the allowlist entry for `kensaiapp_structure.md` § Prompts layer's worked example exists for.)
HOST_PATH = re.compile(r"system/projects/([A-Za-z0-9_.-]+)")

# A dated journey-artifact stem, matched on its own — never only inside `system/projects/…` —
# so a bare stem with no path prefix at all (`versioning.md:95`'s live case) is still seen.
# Whether the match is a journey artifact or a folder (`kensaiapp_structure.md` § Root's
# `2026-08-03_perplexity-outside-review/`) is decided procedurally in `_journey_stem_hit`, not by a
# lookahead in this pattern — a lookahead the greedy `+` can backtrack behind would let the engine
# retry on a truncated slug and match anyway, exactly the false accept a folder must not get.
JOURNEY_STEM = re.compile(r"\d{4}-\d{2}-\d{2}_[A-Za-z0-9-]+")


def _real_project_names(repo: Path) -> set[str]:
    """Real project directories under `system/projects/`, read off disk at run time.

    Empty when `system/projects/` does not exist — a degenerate but valid state (no host-path hit
    can ever fire), distinct from the "no root to scan at all" failure `scan_repo` guards below.
    """
    projects = repo / "system" / "projects"
    if not projects.is_dir():
        return set()
    return {p.name for p in projects.iterdir() if p.is_dir() and not p.name.startswith(".")}


# A roster row: `| `<satellite>` | `<path>` |`. The roster carries satellite PATHS and says product
# names are "deliberately absent" — each satellite declares those in its own project cards — so the
# names are reached in two steps, never one.
SATELLITE_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*$")

# The `Product path:` line of a project card, with its trailing HTML comment dropped.
PRODUCT_PATH = re.compile(r"^\*\*Product path:\*\*\s*(.+?)\s*(?:<!--.*)?$")


def _satellite_roots(repo: Path) -> list[Path]:
    """Every satellite root named in `system/satellites.md`, in the order the file lists them.

    A missing roster yields none — an instance with no satellites is ordinary, and is a different
    state from a roster that exists and lists nothing.
    """
    roster = repo / "system" / "satellites.md"
    if not roster.is_file():
        return []
    roots: list[Path] = []
    for line in roster.read_text(encoding="utf-8").splitlines():
        match = SATELLITE_ROW.match(line.strip())
        if match and match.group(2).startswith(("/", "~")):
            roots.append(Path(match.group(2)).expanduser())
    return roots


# The roster section that declares the names a release must not carry that no project card yields —
# the platform a satellite builds for is the live case. A heading, not a column, so the two roster
# tables `check_satellites.py` reads keep their exact shape.
DECLARED_HEADING = re.compile(r"^##\s+Names a release must not carry\s*$")
_HEADING = re.compile(r"^##\s+")
DECLARED_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|")
SHIPPED_HEADING = re.compile(r"^##\s+Projects a release ships\s*$")


def _declared_names(repo: Path) -> set[str]:
    """Every satellite `system/satellites.md` lists, and every name its § *Names a release must not
    carry* declares.

    **The satellites' own names count.** The owner ruled on 2026-10-06 that a release names no
    satellite, so a satellite's name is a hit like a product's. The name is taken whole, never cut
    down to its suffix: stripping `kensaiapp-` once turned `audit` and `presence` into names on 879
    of 921 lines. Working code that found a sibling instance by its name finds it another way now.

    **The declared section holds what no roster row and no project card yields** — the platform a
    satellite builds for, the host's own name, a retired product, a retired instance. The roster
    lives in `system/`, which a release does not carry, so writing a name there leaks nothing.
    """
    roster = repo / "system" / "satellites.md"
    if not roster.is_file():
        return set()
    names: set[str] = set()
    declared = False
    shipped = False
    for line in roster.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if _HEADING.match(stripped):
            declared = bool(DECLARED_HEADING.match(stripped))
            shipped = bool(SHIPPED_HEADING.match(stripped))
            continue
        if shipped:
            continue  # a shipped project's row names what ships, never a name a release refuses
        if not declared:
            satellite = SATELLITE_ROW.match(stripped)
            if satellite:
                names.add(satellite.group(1).strip())
            continue
        match = DECLARED_ROW.match(stripped)
        if match and match.group(1).strip().lower() != "name":
            names.add(match.group(1).strip())
    return names


def _product_names_of(root: Path) -> set[str]:
    """One instance's EXTERNAL product names — the basename its `Product path:` points at, plus the
    project's own directory name, for every project whose product path is absolute.

    **Only an external product contributes a name, and that is what makes this hit kind usable.**
    An instance's own machinery is declared with a relative product path (`core/tools`,
    `.claude/skills`, `core/doctrine`), and taking those basenames would make `tools`, `skills` and
    `doctrine` product names and fire this check on most of the vendored layer. The
    absolute-versus-relative split is not invented here: it is the same test every launcher already
    applies to decide whether a run needs `--add-dir` for its product.
    """
    projects = root / "system" / "projects"
    if not projects.is_dir():
        return set()
    names: set[str] = set()
    for project in projects.iterdir():
        card = project / "project.md"
        if not project.is_dir() or not card.is_file():
            continue
        try:
            text = card.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for line in text.splitlines():
            match = PRODUCT_PATH.match(line.strip())
            if not match:
                continue
            product_path = match.group(1).strip()
            if product_path.startswith(("/", "~")):
                names.add(PurePosixPath(product_path).name)
                names.add(project.name)
            break
    return names


def _product_name_hit(line: str, product_names: set[str]) -> bool:
    """Whether `line` names a product, matched whole and case-insensitively.

    Whole, because a check that fires `gizmo` on `gizmology` is noise its reader learns to skip.
    Case-insensitively, because a product is named in prose as often as in a path and prose
    capitalises.
    """
    return any(_name_pattern(name).search(line) for name in product_names if name)


def _name_pattern(name: str) -> re.Pattern[str]:
    """`name` whole, case-insensitively, bounded by anything that is not a letter or a digit.

    Not `\\b`: an underscore is a word character to `\\b`, so a tool id like `mcp__<name>-docs`
    hid the name inside it.
    """
    return re.compile(rf"(?<![A-Za-z0-9]){re.escape(name)}(?![A-Za-z0-9])", re.IGNORECASE)


@dataclass(frozen=True)
class ProductNames:
    """The third hit kind's names, and where they did and did not come from."""

    names: set[str]
    read_roots: list[Path]
    unread_roots: list[Path]


def product_name_sources(repo: Path) -> ProductNames:
    """Every external product name reachable from `repo` — its own, plus each satellite's — with
    the roots that could not be read named rather than dropped.

    **Why the unread roots are carried at all.** The other two hit kinds are decided from `repo`
    alone, so their coverage cannot change under the reader. This one reads OTHER instances, and a
    satellite that is absent, moved or unreadable simply contributes fewer names — a quieter run,
    indistinguishable from a clean one by anything a reader can see. So the sources are stated,
    exactly as the scan already states which roots it walks.
    """
    read_roots: list[Path] = [repo]
    unread_roots: list[Path] = []
    names = _product_names_of(repo)
    for root in _satellite_roots(repo):
        if not (root / "system" / "projects").is_dir():
            unread_roots.append(root)
            continue
        read_roots.append(root)
        names |= _product_names_of(root)
    return ProductNames(names=names, read_roots=read_roots, unread_roots=unread_roots)


def _shipped_projects(repo: Path) -> dict[str, set[str]]:
    """Every project `system/satellites.md` § *Projects a release ships* names, in its order, with
    the names its row's second column lets its files carry — each a backticked name."""
    roster = repo / "system" / "satellites.md"
    if not roster.is_file():
        return {}
    names: dict[str, set[str]] = {}
    shipped = False
    for line in roster.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if _HEADING.match(stripped):
            shipped = bool(SHIPPED_HEADING.match(stripped))
            continue
        match = DECLARED_ROW.match(stripped) if shipped else None
        if match and match.group(1).strip().lower() != "project":
            cells = stripped.strip("|").split("|")
            carried = re.findall(r"`([^`]+)`", cells[1]) if len(cells) > 1 else []
            names[match.group(1).strip()] = set(carried)
    return names


def _shipped_roots(repo: Path) -> dict[str, set[str]]:
    """The folders a shipped project brings into a release — its `system/projects/<name>/`, and its
    product when `Product path:` is relative; an absolute one is outside this repo and ships with
    nothing cut from it — each with the names its project carries."""
    roots: dict[str, set[str]] = {}
    for name, carried in _shipped_projects(repo).items():
        roots[f"system/projects/{name}/"] = carried
        card = repo / "system" / "projects" / name / "project.md"
        if not card.is_file():
            raise RuntimeError(
                f"system/satellites.md ships `{name}`, and {card.relative_to(repo)} does not exist "
                "— a project that cannot be read would be scanned as nothing and pass."
            )
        for line in card.read_text(encoding="utf-8").splitlines():
            match = PRODUCT_PATH.match(line.strip())
            if match:
                product = PurePosixPath(match.group(1).strip())
                if product.is_absolute() or ".." in product.parts or not product.parts:
                    break
                root = f"{product}/"
                if any(root.startswith(v) or v.startswith(root) for v in ROOTS):
                    raise RuntimeError(
                        f"`{name}`'s product {root} overlaps a vendored root — its files would be "
                        "read twice, under two different rules."
                    )
                roots[root] = carried
                break
    return roots


def _is_record(relative: str) -> bool:
    """A record — an artifact that exists to hold what was true at a moment — decided by path
    shape (decision 5), never by content: an `evidence/` path segment (a directory named exactly
    `evidence`, at any depth — not a substring of a filename, so `evidence.md` beside `core/` is
    not one), a `code-integrity-report.md` filename wherever it sits, or a ratification verdict —
    `<name>_ratification_verdict.md` — under a skill's `references/` segment specifically, not
    that filename shape anywhere else in the tree."""
    path = Path(relative)
    if "evidence" in path.parts:
        return True
    if path.name == "code-integrity-report.md":
        return True
    if "references" in path.parts and path.name.endswith("_ratification_verdict.md"):
        return True
    return False


def _tracked_files(
    repo: Path, *, tests: bool = False, shipped: bool = False, only: str | None = None
) -> list[str]:
    """Tracked files under the vendored roots, excluding a test's own fixtures, the allowlist, and
    a record.

    `git ls-files` with no `--others`: untracked scratch is not vendored — nothing ships until
    it is committed, so nothing here reads it.

    The allowlist file is excluded by the same reasoning as a `test_`-prefixed file: it exists to
    *contain* the string this check looks for — one `path:<anchor>` key per excused site — so
    scanning it would report the check's own data and the sweep would never converge. The
    exclusion is narrow: it names the one file (`_ALLOWLIST_RELATIVE`), not every `.json` under
    `core/tools/`. A record (`_is_record`) is excluded for the same reason `written_forward.py`
    leaves one out of its own scan (`written_forward.py:36-39`): it holds what was true at a
    moment, and scanning it would report a finding rather than a defect.

    `shipped` reads the shipped projects' folders (`_shipped_roots`) in place of the vendored
    roots, and leaves out a `trail/` segment there as one more record. None declared is no files —
    never a bare `git ls-files`, which would list the whole repo.
    """
    if shipped:
        pathspecs = [only] if only else list(_shipped_roots(repo))
    else:
        pathspecs = [*ROOTS, *ROOT_FILES]
    if not pathspecs:
        return []
    out = subprocess.run(
        ["git", "ls-files", "-z", "--", *pathspecs],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return sorted(
        relative
        for relative in out.split("\0")
        if relative
        and Path(relative).name.startswith("test_") == tests
        and relative != _ALLOWLIST_RELATIVE
        and not _is_record(relative)
        and not (shipped and "trail" in PurePosixPath(relative).parts)
    )


@dataclass(frozen=True)
class Hit:
    """One line naming a host-only reference."""

    path: str
    line: int
    kind: str
    text: str


def _host_segment_hit(line: str, real_names: set[str]) -> bool:
    return any(match.group(1) in real_names for match in HOST_PATH.finditer(line))


def _journey_stem_hit(line: str) -> bool:
    for match in JOURNEY_STEM.finditer(line):
        end = match.end()
        if line[end : end + 3] == ".md":
            end += 3
        if line[end : end + 1] == "/":
            continue  # a folder, not a journey artifact — kensaiapp_structure.md § Root's live case
        return True
    return False


def scan_text(
    path: str,
    text: str,
    real_names: set[str],
    *,
    product_names: set[str] | None = None,
    declared_names: set[str] | None = None,
    home: str | None = None,
    fixture: bool = False,
    example: bool = False,
    shipped_names: set[str] | None = None,
) -> list[Hit]:
    """Every line in `text` naming a host-only reference or a product, never code-span-stripped
    first.

    A line tripping several kinds is reported once, not once per kind — it names one line worth
    repairing, however many independent reasons it is wrong.

    `product_names` defaults to none, so a caller that knows nothing of products sees exactly the
    check it always saw. That default is deliberate rather than convenient: the two host-only kinds
    are decided from `repo` alone, and this third one is not (`_product_names_of` reads other
    instances), so a caller that cannot reach them must get the narrower check rather than a
    quietly empty one it would mistake for a clean result.

    `example` marks a file of a shipped project. The project ships with the journey it points into,
    so a dated stem is not a hit there, and neither is a path into a project in `shipped_names`; a
    path into a project that does not ship still is.
    """
    shipped_names = shipped_names or set()
    products = product_names or set()
    declared = declared_names or set()
    hits: list[Hit] = []
    for number, line in enumerate(text.splitlines(), start=1):
        kinds = []
        if not fixture and _host_segment_hit(line, real_names - shipped_names if example else real_names):
            kinds.append("host-path")
        if not (fixture or example) and _journey_stem_hit(line):
            kinds.append("journey-stem")
        if _product_name_hit(line, products):
            kinds.append("product-name")
        if _product_name_hit(line, declared):
            kinds.append("declared-name")
        if home and (home in line or _encoded(home) in line):
            kinds.append("home-path")
        if kinds:
            hits.append(Hit(path=path, line=number, kind="+".join(kinds), text=line.strip()))
    return hits


def load_allowlist(path: Path = ALLOWLIST_PATH) -> dict[str, str]:
    """`path:<anchor>` -> reason. A missing file is an empty allowlist; a malformed entry is
    refused."""
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    for key, reason in data.items():
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(
                f"{path}: entry {key!r} carries no reason — a malformed allowlist is refused "
                "rather than silently trusted."
            )
        # An empty anchor matches every hit in its path by substring, so a key with no anchor at all
        # -- `f.md` or `f.md:`, both of which `partition(':')` reduces to `""` -- is a blanket file
        # exemption. That is precisely what this allowlist exists INSTEAD of (see decision 2 above),
        # and it fails silently: with two or more hits in the path the ambiguity guard catches it,
        # but with exactly one the site is excused and nothing says so. Refused here, beside the
        # reason check, because a key that cannot name a site is malformed in the same way a reason
        # that says nothing is.
        if not key.partition(":")[2].strip():
            raise ValueError(
                f"{path}: entry {key!r} carries no anchor — an empty anchor matches every hit in "
                "its path, which is the blanket file exemption this allowlist exists instead of. "
                "Key it as `<path>:<a snippet of the excused line>`."
            )
    return data


def apply_allowlist(raw: list[Hit], allow: dict[str, str]) -> tuple[list[Hit], list[str]]:
    """Resolve every `path:<anchor>` entry against `raw`'s hit lines in that path.

    The anchor is a snippet of the excused line's own text, matched by substring against every raw
    hit in the same path -- never a line number, so an edit elsewhere in the file leaves the entry
    matching wherever the site now sits. Exactly one match excuses that hit; no match makes the
    entry stale (unchanged); more than one match is refused loudly -- naming the file and every
    line it matched -- rather than excusing both sites or silently picking one.
    """
    by_path: dict[str, list[Hit]] = {}
    for hit in raw:
        by_path.setdefault(hit.path, []).append(hit)

    excused: set[tuple[str, int]] = set()
    stale: list[str] = []
    for key in allow:
        path, _, anchor = key.partition(":")
        matches = [hit for hit in by_path.get(path, []) if anchor in hit.text]
        if len(matches) > 1:
            lines = ", ".join(str(match.line) for match in matches)
            raise ValueError(
                f"{key!r}: anchor matches {len(matches)} lines in {path!r} ({lines}) -- an "
                "allowlist entry must name exactly one site; narrow the anchor."
            )
        if not matches:
            stale.append(key)
            continue
        excused.add((matches[0].path, matches[0].line))

    reported = [hit for hit in raw if (hit.path, hit.line) not in excused]
    return reported, sorted(stale)


def scan_repo(repo: Path, *, home: str | None = None) -> list[Hit]:
    """Every host-only reference and every product name over `repo`'s tracked files under the
    vendored roots, and every name and home path in the projects a release ships."""
    if not any((repo / root).is_dir() for root in ROOTS):
        raise RuntimeError(
            f"none of {', '.join(ROOTS)} exists under {repo} — no root to scan. A silent "
            "zero here would be indistinguishable from a clean tree."
        )

    real_names = _real_project_names(repo)
    products = product_name_sources(repo).names
    declared = _declared_names(repo)
    hits: list[Hit] = []
    scans = [(relative, False, False) for relative in _tracked_files(repo)]
    scans += [(relative, True, False) for relative in _tracked_files(repo, tests=True)]
    scans += [(relative, False, True) for relative in _tracked_files(repo, shipped=True)]
    scans += [(relative, True, True) for relative in _tracked_files(repo, tests=True, shipped=True)]
    shipped_roots = _shipped_roots(repo)
    shipped_names = set(_shipped_projects(repo))
    for root in shipped_roots:
        if not _tracked_files(repo, shipped=True, only=root) and not _tracked_files(
            repo, tests=True, shipped=True, only=root
        ):
            raise RuntimeError(f"a shipped project's {root} tracks no file — it would pass unread.")
    for relative, fixture, example in sorted(scans):
        path = repo / relative
        owning = [root for root in shipped_roots if example and relative.startswith(root)]
        carried = shipped_roots[max(owning, key=len)] if owning else set()
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue  # unreadable is not a hit; it is a different problem
        hits.extend(
            scan_text(
                relative,
                text,
                real_names,
                product_names=products - carried,
                declared_names=declared - carried,
                home=home,
                fixture=fixture,
                example=example,
                shipped_names=shipped_names,
            )
        )
    return hits


# --- repair: what a fixture carries is a stand-in, so a name in one is renamed, not reworded ------

# The machine path a fixture's home directory becomes. Any absolute path a test treats as a value
# works; this one names no one.
HOME_STAND_IN = "/home/user"


def _encoded(home: str) -> str:
    """`home` as Claude Code spells it in a project folder's name under `~/.claude/projects/`
    (`/Users/someone` → `-Users-someone`), the form a transcript path carries it in."""
    return home.replace("/", "-")

_REPAIRABLE = {"product-name", "declared-name", "home-path"}


def stand_in(name: str) -> str:
    """The invented name a fixture gets in place of `name` — the same one every time and in every
    file, and distinct for distinct names, so a test that relied on two names differing still
    sees them differ."""
    return "example-" + hashlib.sha1(name.lower().encode("utf-8")).hexdigest()[:6]


def is_fixture(relative: str) -> bool:
    """A test file: its names are stand-ins by the doctrine's own word ("In test fixtures the name
    is a stand-in and is simply renamed"), so renaming one changes no claim."""
    return Path(relative).name.startswith("test_")


def repair_text(text: str, names: set[str], home: str | None) -> str:
    """`text` with the home path and every name in `names` replaced by their stand-ins.

    Longest name first, so a satellite's full name is renamed whole rather than around the shorter
    name it contains.
    """
    if home:
        text = text.replace(home, HOME_STAND_IN).replace(_encoded(home), _encoded(HOME_STAND_IN))
    for name in sorted((n for n in names if n), key=len, reverse=True):
        text = _name_pattern(name).sub(stand_in(name), text)
    return text


@dataclass
class Repair:
    """What `--fix` did: the files it rewrote and kept, and the ones whose tests failed after the
    rewrite and were put back as they were."""

    kept: list[str] = field(default_factory=list)
    reverted: list[str] = field(default_factory=list)


def repair(
    repo: Path,
    hits: list[Hit],
    names: set[str],
    home: str | None,
    failures: Callable[[Path, str], set[str] | None],
) -> Repair:
    """Rewrite every fixture file carrying a repairable hit, then keep the rewrite only if it made
    no test fail that passed before it.

    `failures` names a file's failing tests, or `None` when the file cannot be run. It is asked
    before and after, because a file already red for another reason — a live-tree test waiting on
    this very sweep — would otherwise put back a rewrite that broke nothing. A rewrite that does
    turn a test red is put back byte for byte and reported, never kept on the grounds that the
    name is gone: a test that stops passing is a worse defect than the name it carried.
    """
    result = Repair()
    files = sorted(
        {
            hit.path
            for hit in hits
            if is_fixture(hit.path) and set(hit.kind.split("+")) & _REPAIRABLE
        }
    )
    for relative in files:
        path = repo / relative
        original = path.read_text(encoding="utf-8")
        rewritten = repair_text(original, names, home)
        if rewritten == original:
            continue
        before = failures(repo, relative)
        path.write_text(rewritten, encoding="utf-8")
        after = failures(repo, relative) if before is not None else None
        if before is not None and after is not None and after <= before:
            result.kept.append(relative)
        else:
            path.write_text(original, encoding="utf-8")
            result.reverted.append(relative)
    return result


_FAILED = re.compile(r"^(?:FAILED|ERROR) (\S+)", re.MULTILINE)


def pytest_failures(repo: Path, relative: str) -> set[str] | None:
    """The default `failures`: the node ids pytest reports failing or erroring in `relative`. A
    file pytest cannot run (a JavaScript suite) answers `None`, so its rewrite is not kept."""
    if not relative.endswith(".py"):
        return None
    done = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-rfE", "-p", "no:cacheprovider", relative],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    if done.returncode not in (0, 1):
        return None  # collection broke or pytest itself failed: nothing to compare
    return set(_FAILED.findall(done.stdout))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Report every vendored file naming a host-only path, an unmarked journey-artifact "
            "stem, a product, a satellite or the owner's home path. --fix renames what a test "
            "fixture carries and keeps it only where no test that passed before fails after."
        )
    )
    ap.add_argument("--repo", default=".", help="instance root (default: the working directory)")
    ap.add_argument("--quiet", action="store_true", help="print nothing; use the exit code")
    ap.add_argument(
        "--fix",
        action="store_true",
        help="rename the names and home paths in test fixtures, keep each file only if no test that "
        "passed before fails after, then report what is left",
    )
    args = ap.parse_args(argv)

    repo = Path(args.repo).resolve()
    home = str(Path.home())
    sources = product_name_sources(repo)
    raw = scan_repo(repo, home=home)
    if args.fix:
        names = sources.names | _declared_names(repo)
        # A shipped project's tests are the product's own, not stand-ins: hand repair, never --fix.
        shipped = tuple(_shipped_roots(repo))
        vendored = [hit for hit in raw if not hit.path.startswith(shipped)] if shipped else raw
        done = repair(repo, vendored, names, home, pytest_failures)
        if not args.quiet:
            for relative in done.kept:
                print(f"fixed: {relative}")
            for relative in done.reverted:
                print(f"reverted: {relative} — a test that passed before failed after the rename; repair by hand")
        raw = scan_repo(repo, home=home)
    allow = load_allowlist(ALLOWLIST_PATH)  # read at call time, not bound as a default argument
    hits, stale = apply_allowlist(raw, allow)

    if args.quiet:
        return 1 if (hits or stale) else 0

    print(
        f"product names: {len(sources.names)} from {len(sources.read_roots)} instance(s)"
        + (
            f"; {len(sources.unread_roots)} satellite root(s) unread: "
            + ", ".join(str(root) for root in sources.unread_roots)
            if sources.unread_roots
            else ""
        )
    )

    if not hits and not stale:
        print("vendor neutrality: every scanned file is clean.")
        return 0

    for hit in sorted(hits, key=lambda h: (h.path, h.line)):
        print(f"{hit.path}:{hit.line}: [{hit.kind}] {hit.text}")
    for key in stale:
        print(f"{key}: STALE allowlist entry — no longer holds a hit")

    print(f"\n{len(hits)} hits, {len(stale)} stale allowlist entries")
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
