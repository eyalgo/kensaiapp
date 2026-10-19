"""Deterministic gate over a kensaiapp instance's experience layer.

Answers "is this instance's experience layer ratified?" with an exit code, and lets a
caller tell red from crashed. Reads `<instance_root>/system/experience/` and asks three
computable questions about it — no judgment, no model call.

The instance root is always a parameter. This module never consults its own `__file__`
to find it, so the same import answers for whichever root a caller points it at — the
rule `written_forward.py` already carries.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

__version__ = "1.1.0"

LAYER_SUBPATH = ("system", "experience")

COMPANION_GLOB = "*_open_issues.md"

# The Mediums cell's closed value set — `visual_voice_contract_template.md`'s own rule
# ("so the set is machine-readable over slugs"), mapped to the medium set it names.
MEDIUMS_TOKENS = {
    "visual": frozenset({"visual"}),
    "voice": frozenset({"voice"}),
    "visual + voice": frozenset({"visual", "voice"}),
}

_ENTRY_HEADING = re.compile(r"^### `([^`]+)`")


class Verdict(Enum):
    """The closed set of per-question outcomes — never a bare string."""

    PASS = "PASS"
    FAIL = "FAIL"
    NOT_ASKED = "NOT ASKED"


@dataclass(frozen=True)
class DocumentOutcome:
    """The result of reading one named document out of the layer.

    `ok=True` carries the document's verbatim text in `text`. `ok=False` carries no
    text — `reason` names the absolute path that could not be read and why.
    """

    ok: bool
    text: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class QuestionResult:
    """One of the three questions' outcome — PASS/FAIL name nothing else, NOT_ASKED
    always carries a `reason`. `detail` holds every finding, never just the first."""

    verdict: Verdict
    detail: tuple[str, ...] = field(default_factory=tuple)
    reason: str | None = None


def layer_directory(instance_root: str | Path) -> Path:
    """The layer directory for `instance_root`, resolved to an absolute path.

    A relative `instance_root` resolves against the process cwd (`Path.resolve()`'s own
    rule) — never against this module's own location.
    """
    root = Path(instance_root).resolve()
    for part in LAYER_SUBPATH:
        root = root / part
    return root


def _root_problem(root: Path) -> str | None:
    """The reason `root` itself cannot be used — never the layer path, which is a
    separate question checked only once the root is known good. `None` when `root`
    exists and is a directory.

    Two root-level states get their own words here, distinct from each other and from
    "the layer directory does not exist": the root does not exist at all, and the root
    exists but is not a directory. A mistyped `--instance-root` and an instance that
    simply never took the experience layer have opposite recoveries — fix the path, or
    run the layer's authoring pass — so they must not print the same reason.
    """
    if not root.exists():
        return f"instance root does not exist: {root}"
    if not root.is_dir():
        return f"instance root is not a directory: {root}"
    return None


def read_document(instance_root: str | Path, name: str) -> DocumentOutcome:
    """Read `name` out of `instance_root`'s layer directory.

    Returns the document's verbatim text on success. Returns a not-readable outcome,
    naming the absolute path that failed, when: the instance root itself does not
    exist or is not a directory, the layer directory does not exist, a path exists at
    the layer directory but is not a directory, the named document does not exist, or
    the named document's bytes do not decode as UTF-8. No exception escapes this
    function.
    """
    root = Path(instance_root).resolve()
    root_reason = _root_problem(root)
    if root_reason is not None:
        return DocumentOutcome(ok=False, reason=root_reason)

    layer = layer_directory(instance_root)

    if not layer.exists():
        return DocumentOutcome(ok=False, reason=f"layer directory does not exist: {layer}")
    if not layer.is_dir():
        return DocumentOutcome(ok=False, reason=f"layer path is not a directory: {layer}")

    target = layer / name
    if not target.exists():
        return DocumentOutcome(ok=False, reason=f"document does not exist: {target}")
    if not target.is_file():
        return DocumentOutcome(ok=False, reason=f"document is not a file: {target}")

    try:
        text = target.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as exc:
        return DocumentOutcome(ok=False, reason=f"document is not readable ({exc}): {target}")

    return DocumentOutcome(ok=True, text=text)


def check_companions(instance_root: str | Path) -> QuestionResult:
    """Question (a) — any open companion is red.

    Globs the layer directory, non-recursively, for the literal `*_open_issues.md`.
    Zero matches is the pass. A retired companion under a trail subdirectory is never
    scanned, because the glob does not recurse. `NOT_ASKED`, naming the instance root
    or the layer directory (whichever does not resolve), when either does not resolve
    — never a vacuous pass over an empty glob.
    """
    root = Path(instance_root).resolve()
    root_reason = _root_problem(root)
    if root_reason is not None:
        return QuestionResult(verdict=Verdict.NOT_ASKED, reason=root_reason)

    layer = layer_directory(instance_root)

    if not layer.exists():
        return QuestionResult(
            verdict=Verdict.NOT_ASKED, reason=f"layer directory does not exist: {layer}"
        )
    if not layer.is_dir():
        return QuestionResult(
            verdict=Verdict.NOT_ASKED, reason=f"layer path is not a directory: {layer}"
        )

    companions = tuple(sorted(p.name for p in layer.glob(COMPANION_GLOB) if p.is_file()))

    if companions:
        return QuestionResult(verdict=Verdict.FAIL, detail=companions)
    return QuestionResult(verdict=Verdict.PASS)


@dataclass(frozen=True)
class ContractRow:
    """One row of `visual_voice_contract.md`, backticks stripped from every cell."""

    slug: str
    kind: str
    mediums: frozenset[str]


@dataclass(frozen=True)
class MalformedRow:
    """A contract row Task 3 could not read — never dropped silently.

    `slug` is populated whenever the row carried a readable first cell (so a caller can
    still report *which* entry is malformed), and is `None` when the row is too short
    to have one.
    """

    raw: str
    reason: str
    slug: str | None = None


@dataclass(frozen=True)
class HeaderNotFound:
    """`parse_contract_rows` scanned the whole document and never found a pipe line whose
    cells equal the four-column header — distinct from a header that *is* found with zero
    rows beneath it, which stays `[]`: a legitimate complete state (see that function's own
    docstring). One document-level cause, reported once by its caller, never confused with
    "the table is present and empty"."""


def _pipe_cells(line: str) -> list[str] | None:
    """Split a pipe-leading table line into its cells, backticks stripped.

    Returns `None` for a line that is not pipe-leading at all.
    """
    stripped = line.strip()
    if not stripped.startswith("|"):
        return None
    parts = stripped.split("|")
    if parts and parts[0] == "":
        parts = parts[1:]
    if parts and parts[-1] == "":
        parts = parts[:-1]
    return [cell.strip().strip("`") for cell in parts]


def _is_separator_row(cells: list[str]) -> bool:
    return all(re.fullmatch(r"-+", cell) for cell in cells)


_CONTRACT_HEADER_CELLS = ["Slug", "Kind", "Mediums", "Reason"]


def parse_contract_rows(text: str) -> list[ContractRow | MalformedRow] | HeaderNotFound:
    """Parse `visual_voice_contract.md`'s Rows table into `(slug, kind, mediums)`.

    The header row and its separator are not rows. A table with no rows is a
    legitimate complete state and yields an empty list. Every pipe-leading line after
    the four-column header is read as a row — including a second table elsewhere in
    the document — and one that does not fit is reported as a `MalformedRow`, never
    silently dropped.

    Returns `HeaderNotFound()` — never `[]` — when no pipe line's cells equal the
    four-column header exactly (`_CONTRACT_HEADER_CELLS`; case-sensitive, order-sensitive,
    no near-miss forgiven). That state is not a table with no rows: the document may carry
    no pipe table at all, or carry one whose header does not match.
    """
    lines = text.splitlines()

    header_idx = None
    for i, line in enumerate(lines):
        cells = _pipe_cells(line)
        if cells == _CONTRACT_HEADER_CELLS:
            header_idx = i
            break
    if header_idx is None:
        return HeaderNotFound()

    results: list[ContractRow | MalformedRow] = []
    for line in lines[header_idx + 1 :]:
        cells = _pipe_cells(line)
        if cells is None:
            continue
        if _is_separator_row(cells):
            continue

        if len(cells) != 4:
            results.append(
                MalformedRow(raw=line, reason=f"row has {len(cells)} cell(s), expected 4")
            )
            continue

        slug, kind, mediums_cell, _reason = cells
        mediums = MEDIUMS_TOKENS.get(mediums_cell)
        if mediums is None:
            results.append(
                MalformedRow(
                    raw=line,
                    reason=f"unrecognised Mediums cell: {mediums_cell!r}",
                    slug=slug,
                )
            )
            continue

        results.append(ContractRow(slug=slug, kind=kind, mediums=mediums))

    return results


def parse_entry_slugs(text: str) -> tuple[str, ...]:
    """Parse a restrictions document's `### `<slug>` — <title>` entry headings.

    Line-oriented over the whole document. A `### ` heading not immediately followed
    by a backticked token is not an entry; `## ` and `#### ` headings are never
    entries. Duplicates are preserved in document order — Task 4 names a repeat.
    """
    slugs = []
    for line in text.splitlines():
        match = _ENTRY_HEADING.match(line)
        if match:
            slugs.append(match.group(1))
    return tuple(slugs)


CONTRACT_DOC = "visual_voice_contract.md"
RESTRICTIONS_DOC = {"visual": "visual_restrictions.md", "voice": "voice_restrictions.md"}
_VALID_KIND = "limit"


def _read_named(
    instance_root: str | Path, names: Iterable[str]
) -> tuple[dict[str, DocumentOutcome], str | None]:
    """Read every document in `names` by name; never a glob.

    Returns the outcomes keyed by name, and — when one or more could not be read — a
    single reason joining every failure, naming each document, for a `NOT_ASKED`
    verdict. `None` when every document read cleanly.
    """
    outcomes = {name: read_document(instance_root, name) for name in names}
    unreadable = [f"{name}: {outcome.reason}" for name, outcome in outcomes.items() if not outcome.ok]
    return outcomes, ("; ".join(unreadable) if unreadable else None)


def check_pairing(instance_root: str | Path) -> QuestionResult:
    """Question (b) — the two set equalities, and what each difference is called.

    For each medium m, C(m) (slugs the contract projects onto m) must equal D(m)
    (slugs `<m>_restrictions.md` states). Both directions are checked and each
    difference has its own name — `unmet reach`, `unclaimed medium`, `unrowed entry`,
    `bad kind`, `duplicate row`, `duplicate entry`, `malformed row` — because the
    recoveries differ. `NOT_ASKED` when any of the three documents does not read; the
    two direction documents are never opened.
    """
    outcomes, unreadable_reason = _read_named(
        instance_root, [CONTRACT_DOC, RESTRICTIONS_DOC["visual"], RESTRICTIONS_DOC["voice"]]
    )
    if unreadable_reason:
        return QuestionResult(verdict=Verdict.NOT_ASKED, reason=unreadable_reason)

    rows = parse_contract_rows(outcomes[CONTRACT_DOC].text)
    if isinstance(rows, HeaderNotFound):
        # One cause, one finding — with no header found there are no rows to project onto
        # either medium, so every restrictions entry would otherwise surface as its own
        # `unrowed entry` shadow of this one real cause. Named FAIL, not NOT_ASKED: the
        # document read perfectly well, so nothing about it was unreadable — what it
        # contains is wrong, which is what a red layer means (`check_companions`'s and
        # `read_document`'s NOT_ASKED are reserved for "this did not read").
        header = " | ".join(_CONTRACT_HEADER_CELLS)
        return QuestionResult(
            verdict=Verdict.FAIL,
            detail=(f"header not found: {CONTRACT_DOC} — expected | {header} |",),
        )

    entry_slugs = {
        medium: parse_entry_slugs(outcomes[doc].text) for medium, doc in RESTRICTIONS_DOC.items()
    }

    findings: list[str] = []

    for row in rows:
        if isinstance(row, MalformedRow):
            findings.append(f"malformed row: {row.slug or '<no slug>'} — {row.reason}")
    good_rows = [row for row in rows if isinstance(row, ContractRow)]

    rows_by_slug: dict[str, list[ContractRow]] = {}
    for row in good_rows:
        rows_by_slug.setdefault(row.slug, []).append(row)
    for slug in sorted(slug for slug, group in rows_by_slug.items() if len(group) > 1):
        findings.append(f"duplicate row: {slug} — {len(rows_by_slug[slug])} rows carry this slug")

    for row in good_rows:
        if row.kind != _VALID_KIND:
            findings.append(f"bad kind: {row.slug} — kind is {row.kind!r}, expected {_VALID_KIND!r}")

    for medium, doc in RESTRICTIONS_DOC.items():
        counts: dict[str, int] = {}
        for slug in entry_slugs[medium]:
            counts[slug] = counts.get(slug, 0) + 1
        for slug in sorted(slug for slug, count in counts.items() if count > 1):
            findings.append(f"duplicate entry: {slug} — {counts[slug]} entries in {doc}")

    mediums_by_slug: dict[str, set[str]] = {}
    for row in good_rows:
        mediums_by_slug.setdefault(row.slug, set()).update(row.mediums)
    all_row_slugs = set(mediums_by_slug)

    entry_set = {medium: set(entry_slugs[medium]) for medium in RESTRICTIONS_DOC}

    for medium, doc in RESTRICTIONS_DOC.items():
        for slug in sorted(entry_set[medium] - all_row_slugs):
            findings.append(f"unrowed entry: {slug} — {doc} states it, no contract row exists")

    contract_reach = {
        medium: {slug for slug, mediums in mediums_by_slug.items() if medium in mediums}
        for medium in RESTRICTIONS_DOC
    }

    for medium, doc in RESTRICTIONS_DOC.items():
        for slug in sorted(contract_reach[medium] - entry_set[medium]):
            findings.append(f"unmet reach: {slug} — row reaches {medium}, {doc} does not state it")

    for medium, doc in RESTRICTIONS_DOC.items():
        unclaimed = (entry_set[medium] - contract_reach[medium]) & all_row_slugs
        for slug in sorted(unclaimed):
            findings.append(
                f"unclaimed medium: {slug} — {doc} states it, its row does not name {medium}"
            )

    if findings:
        return QuestionResult(verdict=Verdict.FAIL, detail=tuple(findings))
    return QuestionResult(verdict=Verdict.PASS)


REACHES_LITERAL = "<The medium:"


def check_reaches(instance_root: str | Path) -> QuestionResult:
    """Question (c) — the half-answered `Reaches` slot.

    Reads `visual_restrictions.md` and `voice_restrictions.md` by name (never a glob —
    an empty glob would be a silent pass) and searches each for the case-sensitive
    fixed string `<The medium:`. No hits is the pass; each hit is named with its
    document and 1-based line number. `NOT_ASKED` when either document does not read.
    """
    outcomes, unreadable_reason = _read_named(instance_root, RESTRICTIONS_DOC.values())
    if unreadable_reason:
        return QuestionResult(verdict=Verdict.NOT_ASKED, reason=unreadable_reason)

    hits: list[str] = []
    for name, outcome in outcomes.items():
        for line_number, line in enumerate(outcome.text.splitlines(), start=1):
            if REACHES_LITERAL in line:
                hits.append(f"{name}:{line_number}")

    if hits:
        return QuestionResult(verdict=Verdict.FAIL, detail=tuple(hits))
    return QuestionResult(verdict=Verdict.PASS)


# (letter, label, checker, the noun a FAIL summary counts)
QUESTIONS = (
    ("a", "companions", check_companions, "open companion(s)"),
    ("b", "pairing", check_pairing, "finding(s)"),
    ("c", "reaches", check_reaches, "hit(s)"),
)


def _report(instance_root: str | Path) -> tuple[str, int]:
    """Ask all three questions, in order, without short-circuiting.

    Returns the full report text (header, one line per question with its indented
    detail, then the verdict line) and the exit code: 2 if any question is
    `NOT_ASKED` (dominates 1), else 1 if any `FAIL`ed, else 0.
    """
    lines = [f"experience-gate: {layer_directory(instance_root)}"]
    results = []

    for letter, label, checker, noun in QUESTIONS:
        result = checker(instance_root)
        results.append(result)

        if result.verdict is Verdict.PASS:
            lines.append(f"({letter}) {label}: {result.verdict.value}")
        elif result.verdict is Verdict.FAIL:
            lines.append(
                f"({letter}) {label}: {result.verdict.value} — {len(result.detail)} {noun}"
            )
            lines.extend(f"    {item}" for item in result.detail)
        else:
            lines.append(f"({letter}) {label}: {result.verdict.value} — {result.reason}")

    not_asked = sum(1 for r in results if r.verdict is Verdict.NOT_ASKED)
    failed = sum(1 for r in results if r.verdict is Verdict.FAIL)

    if not_asked:
        lines.append(f"NOT EVALUATED — {not_asked} of 3 questions could not be asked")
        code = 2
    elif failed:
        lines.append(f"RED — {failed} of 3 questions failed")
        code = 1
    else:
        lines.append("GREEN — all three questions passed")
        code = 0

    return "\n".join(lines) + "\n", code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="experience_gate.py")
    parser.add_argument(
        "--instance-root",
        default=".",
        help="the instance root whose system/experience/ is graded (defaults to the process cwd)",
    )
    args = parser.parse_args(argv)

    report, code = _report(args.instance_root)
    print(report, end="")
    return code


if __name__ == "__main__":
    sys.exit(main())
