"""reporters.py — compose the run-outcome message, one composer per run type.

WHY THIS EXISTS
    `watch_agent.py` waits for a `--bg` run to stop, then has to say what the run
    PRODUCED — and the run's own state cannot carry that (a `stopped` state means both a
    clean halt and a session that never started). So the outcome is read from the run's
    own files. That read is entirely run-type-specific: product-prd wrote a PRD, the
    kaizen fix-author wrote a packet, the fixer moved a repo's HEAD. Keeping every one of
    those in the watcher would make a shared file grow a branch per run type. Instead the
    watcher hands a reporter an `OutcomeContext` and takes back an `Outcome`; a new run
    type is a new reporter plus one registry entry, and the watcher never changes.

THE CONTRACT
    reporter(ctx: OutcomeContext) -> Outcome

    `Outcome.body` is the message. `Outcome.footnote`, when set, is placed by the watcher
    AFTER its state note, so it is for a caveat that refers to that note and nothing else.

    A caveat about what the run PRODUCED is not one of those, and does not go there: an
    unchanged HEAD decides the body outright (`_committed_nothing`), because a footnote
    under a headline of borrowed figures did not stop the figures being read. That was
    measured — see `prd()`.

    Best-effort, like the notify: a reporter that raises, or cannot read its artifact,
    degrades to "<label>: run ended." rather than costing the person their message.
"""

from __future__ import annotations

import glob
import os
import re
import subprocess
from collections import namedtuple
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

__version__ = "1.28.2"


@dataclass(frozen=True)
class OutcomeContext:
    """What the watcher read off the run, handed to the reporter.

    `artifact_path` is the thing the run authored (a PRD product dir, a packet file);
    `head_before`/`head_after` are the outcome repo's HEAD across the watch, or None
    when there is no repo to read — the watcher computes them, the reporter judges them.

    `document_stem` is which document the run worked, for the one reporter whose artifact is
    not a single path but a trail among trails (`companion_self_answer`). Empty for every
    other run type, and never guessed from `label`: the launcher composes that as
    `<project>-<stem>` and a project name may carry a `-` of its own.
    """

    label: str
    cwd: str = ""
    artifact_path: str | None = None
    document_stem: str = ""
    state: str = ""
    head_before: str | None = None
    head_after: str | None = None
    # The self-answer reports already on disk when the watch began — the same shape as
    # `head_before` and as `watch_agent.completion_marker_seen`'s `present_before`: a single
    # reading taken once, so a file that predates the watch is inert for its whole life.
    # `None` means the caller took no reading and today's behaviour stands; an empty tuple is
    # a real reading that found nothing, and is not the same thing.
    reports_before: tuple[str, ...] | None = None


@dataclass(frozen=True)
class Outcome:
    """A reporter's message. `footnote` lands after the watcher's state note.

    `produced_nothing` defaults to `False` — none of the reporters below sets it; the
    watcher attaches it (`produced_nothing()`, next) to whatever `Outcome` a reporter
    hands back, so a caller deciding what a run PRODUCED (`watch_agent.HookOutcome`) never
    has to read `OutcomeContext` a second time to answer the same question."""

    body: str
    footnote: str | None = None
    produced_nothing: bool = False


def produced_nothing(ctx: OutcomeContext) -> bool:
    """Whether, by every reading `OutcomeContext` carries, this run produced nothing at
    all: HEAD did not move, and no self-answer report appeared beyond `ctx.reports_before`.

    Pulled into one place so the fact is computed exactly once and never re-derived: the
    watcher attaches this to a reporter's `Outcome`
    (`dataclasses.replace(outcome, produced_nothing=produced_nothing(ctx))`) and from then
    on only ever reads the field — it never inspects `ctx.head_before`/`head_after` or the
    report set a second time to decide the same question for itself.

    An unreadable HEAD (`ctx.head_before is None`) is not evidence either way — the same
    rule `prd()` already holds for its own unchanged-HEAD check — so it reads as "not
    proven", never as true by default.

    `ctx.artifact_path` is required. Without it, no report reading was ever taken (the
    watcher only calls `self_answer_reports_present` when `--artifact-path` is given), so
    the fact is never asserted true on HEAD alone: a run this watcher was never pointed at
    a product path for is not, on its own, evidence that the run did nothing.
    """
    if ctx.head_before is None or ctx.head_before != ctx.head_after:
        return False
    if not ctx.artifact_path:
        return False
    before = {os.path.realpath(p) for p in (ctx.reports_before or ())}
    after = {os.path.realpath(p)
             for p in self_answer_reports_present(ctx.artifact_path, ctx.document_stem or None)}
    return not (after - before)


# --- generic: the default, and the fallback for a run type with no reporter yet ----


def generic(ctx: OutcomeContext) -> Outcome:
    return Outcome(f"{ctx.label}: run ended.")


# --- shared: is a document's companion still waiting on the owner? -----------------


class CompanionState(Enum):
    """The three-way read of a `*_open_issues.md` companion — never a bare bool, because
    "no companion" and "companion, fully answered" both mean nothing is waiting, but only
    one of them is a state a finished run may leave and the other is the stall itself."""

    NO_COMPANION = "no_companion"
    UNANSWERED = "unanswered"
    ANSWERED = "answered"


# The decision slots the eleven `*_open_issues_template.md` files actually carry, measured
# 2026-08-30 (`grep -h -oE '\*\*[A-Za-z ]+:\*\*' core/templates/*/*_open_issues_template.md`
# read against every template body). "Answer" and "Confirm or override" cover ten of the
# eleven; the SDD template alone adds "Keep or re-cut" (§ 3) and "Your call" (§ 4, the one
# bucket with no raising seat). The set is closed and enumerated here rather than matched by
# any bracketed bullet, because a reasoning field the run already filled ("Grounds:",
# "Rationale:") must not be misread as an unanswered decision merely for quoting something
# that looks like a placeholder.
_SLOT_LABELS = ("Answer", "Confirm or override", "Keep or re-cut", "Your call")

_SLOT_LINE_RE = re.compile(
    r"^-\s*\*\*(?:" + "|".join(re.escape(label) for label in _SLOT_LABELS) + r"):\*\*\s*(.*)$",
    re.MULTILINE,
)


def _find_companion(docs_dir: str, doc_name: str) -> str | None:
    """The `<doc_name>_open_issues.md` companion, resolved by the directory entry's OWN
    case — never composed from `doc_name`'s. `core/launchers/companion-self-answer/
    launcher.sh` was fixed for exactly this on 2026-08-30 (`4a6ba354`): a real product held
    `docs/SRS.md` beside `docs/srs_open_issues.md`, and a composed `SRS_open_issues.md`
    names no directory entry on a case-sensitive filesystem. None on a missing or unreadable
    directory — that is the caller's "no companion" case, not a reader failure.
    """
    if not docs_dir:
        return None
    wanted = f"{doc_name}_open_issues.md".lower()
    try:
        entries = os.listdir(docs_dir)
    except OSError:
        return None
    for entry in entries:
        if entry.lower() == wanted:
            return os.path.join(docs_dir, entry)
    return None


def companion_state(docs_dir: str | None, doc_name: str) -> CompanionState:
    """Is there a companion beside `doc_name` in `docs_dir`, and is it still waiting on the
    owner? The read is deliberately narrow — it decides only this three-way question and
    reports no figure off the companion, unlike a document read (module docstring's "The
    product is not read at all in that case"): this is a different read, over a different
    file, and a safe one to make even when the document itself must not be opened.

    Unanswered means at least one slot line (`- **<label>:** …`, `_SLOT_LABELS`) whose value,
    stripped, still begins with `<` and ends with `>` — the template's own placeholder
    standing where an answer goes. A value that happens to start with `<` for some other
    reason (a bare URL, a code snippet) was judged not worth guarding against: every real
    slot value in this corpus is prose ("confirm", "override: …", a sentence), and requiring
    the WHOLE value to be bracket-wrapped already rules out an answer that merely opens with
    one character that looks like this template's own placeholder.

    A companion that exists but cannot be read degrades to ANSWERED, not UNANSWERED — the
    same best-effort direction as every other reader here, and the safer of the two guesses:
    it leaves `_committed_nothing` on today's stall message rather than manufacturing a
    "waiting on you" instruction from a file this run never actually saw.
    """
    path = _find_companion(docs_dir, doc_name)
    if path is None:
        return CompanionState.NO_COMPANION
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return CompanionState.ANSWERED
    for match in _SLOT_LINE_RE.finditer(text):
        value = match.group(1).strip()
        if value.startswith("<") and value.endswith(">"):
            return CompanionState.UNANSWERED
    return CompanionState.ANSWERED


def _committed_nothing(
    label: str, artifact: str, companion: CompanionState = CompanionState.NO_COMPANION,
) -> str:
    """The whole message for a run whose HEAD did not move — never a caveat under one.

    The product is not read at all in that case, so nothing here comes off disk except the
    artifact's name and the companion's three-way state. `artifact` is the only other
    run-type-specific term ("PRD", "SRS", "UXD", "DESIGN"): a reporter names the document it
    reads and no other, or it replaces one false claim with a second. The rest is
    run-type-agnostic and has one owner, the way `parse_status` / `count_buckets` /
    `trail_cycles` do.

    `companion` distinguishes a stall from a run that correctly had nothing to fold: only
    UNANSWERED gets the second message. NO_COMPANION and ANSWERED both keep today's — a
    missing companion is the ordinary stall, and a companion where every slot is filled is a
    real anomaly (the owner already answered and the run still did not commit) that this
    function must not soften. The default (no third argument) is that same stall message,
    so every call site this plan does not touch keeps behaving exactly as before.
    """
    if companion is CompanionState.UNANSWERED:
        return (f"📋 {label}: the run had nothing to fold — the {artifact} companion is "
                f"still waiting on you. Answer it, commit, re-run.")
    return (f"⚠️ {label}: the run committed nothing — it may have stopped. "
            f"The {artifact} on disk is from an earlier run.")


def _committed_nothing_for(label: str, artifact: str, docs_dir: str | None) -> str:
    """`_committed_nothing`, with the companion looked up for the caller.

    The one function every one of the eight document reporters passes through, so none of
    them grows its own companion lookup (fence: "eight copies of a companion lookup is the
    failure this task is one step away from"). `docs_dir` is the caller's own — `<product>/
    docs` for seven of the eight, the bare project path for Agari, which keeps no `docs/`
    hop (`_agari_body`'s own note on why the companion is named bare).
    """
    return _committed_nothing(label, artifact, companion_state(docs_dir, artifact))


# --- prd: read the tree product-prd authored ---------------------------------------
#
# Everything down to `prd()` reads what product-prd wrote. The skill's file contract is
# what makes this possible at all, and each rule here exists because the real files break
# the obvious implementation of it.


def parse_status(prd_text: str) -> str | None:
    """The Status value's first word — Draft, Settled or Locked — or None.

    First word only, because the real value carries a trailing note:
    `**Status:** Settled — no owner action pending; external dependencies tracked...`.
    An equality check against "Settled" fails on that line, silently, forever.
    """
    m = re.search(r"^\*\*Status:\*\*\s*(\w+)", prd_text, re.MULTILINE)
    return m.group(1) if m else None


def parse_version(prd_text: str) -> str | None:
    """The Version integer, or None.

    `**Version:** 2 — <note>` where the note wraps across several physical lines. We
    take the integer at the head of the line and never look at the note, so the wrap
    is not our problem.
    """
    m = re.search(r"^\*\*Version:\*\*\s*(\d+)", prd_text, re.MULTILINE)
    return m.group(1) if m else None


def count_items(companion_text: str) -> dict[int, int]:
    """Items in every numbered bucket the companion carries — `{bucket number: item count}`.

    The general form of `count_buckets`, for a companion with more than three buckets: the SDD's
    carries five — open issues, choices, cut calls, disagreements, and items raised from
    downstream. Read by the same three rules, for the same reasons given there: counted by
    position under a numbered H2 and never by its text, fenced code skipped, and any other
    heading closing the current bucket. A bucket that is present and holds no item appears,
    with 0.
    """
    counts: dict[int, int] = {}
    bucket = None
    fenced = False
    for line in companion_text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        m = re.match(r"^##\s+(\d+)\.", line)
        if m:
            bucket = int(m.group(1))
            counts.setdefault(bucket, 0)
            continue
        if re.match(r"^#{1,2}\s", line):
            bucket = None
            continue
        if bucket and re.match(r"^###\s+\d+\.\d+", line):
            counts[bucket] += 1
    return counts


def count_buckets(companion_text: str):
    """Items in the companion's first three buckets: (§ 1, § 2, § 3).

    § 1 and § 2 are open issues and choices to confirm in every product companion. § 3 is
    the PRD's directives and the other companions' items raised from downstream — each caller
    names it.

    Counted by position under the H2, never by matching its text. Three things in the
    real files force that:

    - An empty bucket has no sentinel. It is freeform prose — "None this cycle." — so
      there is nothing to match for zero. Counting `###` headings gives zero for free.
    - The headings carry em-dashes (U+2014). Matching their titles would make this
      parser hostage to a character nobody can see, and to any rewording.
    - Owners paste their own headings into the file mid-answer. So any other heading
      closes the current bucket rather than letting stray items accrue to it.
    """
    counts = count_items(companion_text)
    return counts.get(1, 0), counts.get(2, 0), counts.get(3, 0)


def trail_cycles(docs_dir: str, trail_name: str = "trail/prd") -> int:
    """The highest cycle number in `trail_name`/, or 0 if there is no trail.

    The max, not the count: the skill numbers a new cycle one above the highest that
    exists, so a removed cycle must not be able to make us collide with a real one.

    `trail_name` is the trail's path **relative to `docs_dir`**, two segments since
    `kensaiapp_structure.md` § *A trail is not the document's sibling* filed every trail
    under a shared `trail/`. It defaults to `trail/prd` so every existing caller is
    unaffected; the uxd reporter passes `trail/uxd` — the uxd trail's own name, not a
    clone of this one.
    """
    try:
        names = os.listdir(os.path.join(docs_dir, trail_name))
    except OSError:
        return 0
    cycles = [int(m.group(1)) for n in names if (m := re.fullmatch(r"cycle-(\d+)\.md", n))]
    return max(cycles) if cycles else 0


def read_product(product_path: str):
    """What is on disk under <product>/docs/, or None if it cannot be read.

    The only function here that touches the filesystem, so the degrade path is one
    `except` in one place.

    `raised` is the companion's § 4, items raised from downstream, which `count_buckets`
    stops short of. A companion holding only § 4 items is waiting on the owner like any
    other, and read through the three buckets alone it reported "lists no items".
    """
    docs = os.path.join(product_path, "docs")
    prd_path = os.path.join(docs, "PRD.md")
    try:
        if not os.path.isfile(prd_path):
            return {"prd": False, "status": None, "version": None,
                    "companion": False, "buckets": (0, 0, 0), "raised": 0, "trail": 0}
        with open(prd_path, encoding="utf-8") as fh:
            prd_text = fh.read()
        companion_path = os.path.join(docs, "PRD_open_issues.md")
        companion = os.path.isfile(companion_path)
        buckets = (0, 0, 0)
        raised = 0
        if companion:
            with open(companion_path, encoding="utf-8") as fh:
                text = fh.read()
            buckets = count_buckets(text)
            raised = count_items(text).get(4, 0)
        return {
            "prd": True,
            "status": parse_status(prd_text),
            "version": parse_version(prd_text),
            "companion": companion,
            "buckets": buckets,
            "raised": raised,
            "trail": trail_cycles(docs),
        }
    except OSError:
        return None


def _pending_phrase(buckets, raised=0):
    """"1 choice to confirm" / "2 open issues, 1 directive" — only the non-zero terms."""
    n1, n2, n3 = buckets
    parts = []
    if n1:
        parts.append(f"{n1} open issue" + ("" if n1 == 1 else "s"))
    if n2:
        parts.append(f"{n2} choice" + ("" if n2 == 1 else "s") + " to confirm")
    if n3:
        parts.append(f"{n3} directive" + ("" if n3 == 1 else "s"))
    if raised:
        parts.append(_raised_term(raised))
    return ", ".join(parts)


def _raised_term(n: int) -> str:
    """"1 item raised from downstream" — every product companion carries this section last:
    § 4 in the PRD's, § 5 in the SDD's, § 3 everywhere else. The SDD reporter sums its
    buckets and never names this one."""
    return f"{n} item" + ("" if n == 1 else "s") + " raised from downstream"


def _prd_body(label: str, product_path: str | None) -> str:
    """What the run produced, read from the product. Never what state the agent is in.

    Best-effort by design, and the `except Exception` is deliberate — wider than this
    file's usual narrow excepts. A malformed doc is precisely the input a parser gets
    wrong, and a parser bug must cost specificity, never the message. The person is
    waiting on their phone; "the run ended" beats a traceback into /dev/null.
    """
    plain = f"{label}: run ended."
    if not product_path:
        return plain
    try:
        p = read_product(product_path)
        if p is None:
            return (f"⚠️ {label}: run ended, but the product at {product_path} could not be "
                    f"read — what it produced is unknown.")
        if not p["prd"]:
            return f"⚠️ {label}: no PRD at docs/PRD.md — this run left nothing to read."

        prd_ref = f"PRD v{p['version']}" if p["version"] else "PRD"
        n1, n2, n3 = p["buckets"]
        raised = p["raised"]
        pending = _pending_phrase(p["buckets"], raised)

        if p["companion"]:
            # The companion is out for answers, so the cycle it belongs to is the one
            # after the last round folded into the trail.
            cycle = p["trail"] + 1
            if n1 == 0 and n2 == 0 and n3 == 0 and raised == 0:
                return (f"⚠️ {label}: {prd_ref} — docs/PRD_open_issues.md is present but lists "
                        f"no items. The run may not have finished clearing it; check it and "
                        f"re-run.")
            if n1 == 0 and n2 == 0 and raised == 0:
                return (f"📋 {label}: {prd_ref}, cycle {cycle} complete — no questions left, but "
                        f"{pending} need you to act.\n"
                        f"Do them, note it in docs/PRD_open_issues.md, commit, re-run.")
            return (f"📋 {label}: {prd_ref}, cycle {cycle} complete — {pending}.\n"
                    f"Answer docs/PRD_open_issues.md, commit, re-run.")

        # No companion. Its absence is the done signal — but only because we already
        # know the PRD exists. An empty directory has no companion either.
        # No cycle number here: the trail counts rounds folded in, which is a different
        # quantity, and a first run that settled everything has none.
        status = p["status"]
        if status == "Settled":
            return f"✅ {label}: {prd_ref} settled — nothing pending."
        if status == "Locked":
            return f"✅ {label}: {prd_ref} is Locked — nothing pending."
        return (f"⚠️ {label}: {prd_ref} — no open-issues file, but Status is "
                f"\"{status or 'unreadable'}\", not Settled. The run may not have finished; "
                f"check docs/PRD.md.")
    except Exception:
        return plain


def prd(ctx: OutcomeContext) -> Outcome:
    """The product-prd outcome — reads docs/PRD.md + docs/PRD_open_issues.md.

    An unchanged HEAD decides the message rather than annotating one. A run that
    committed nothing leaves the previous run's files on disk, so reading them produces a
    headline of figures and an instruction that belong to that earlier run — and a
    parenthetical underneath does not take them back. This was measured: a run that died
    on a model refusal reported "PRD v1, cycle 2 complete" and told the owner to answer a
    companion it never wrote. So the product is not read at all in that case.

    `apply_packet` has always spent this value this way (`⚠️ … committed nothing`); this
    is prd converging on it. srs, uxd and design still annotate.

    An unreadable HEAD is a third case and stays untouched: it is not evidence of an idle
    run, so it claims neither outcome and the body is the product read, as before.

    A companion left unanswered (`companion_state`) gets a different unchanged-HEAD message
    than a stall — the run had nothing to fold, not nothing to say. Checking the companion
    is a different, safe read from checking the document: it decides only this and reports
    no figure off it.
    """
    if ctx.head_before is not None and ctx.head_before == ctx.head_after:
        docs_dir = os.path.join(ctx.artifact_path, "docs") if ctx.artifact_path else None
        return Outcome(_committed_nothing_for(ctx.label, "PRD", docs_dir))
    return Outcome(_prd_body(ctx.label, ctx.artifact_path), None)


# --- fix-author: the artifact is the packet the run writes -------------------------


def fix_author(ctx: OutcomeContext) -> Outcome:
    """Did the kaizen fix-author write a packet? The packet file is the whole outcome.

    Best-effort: an unreadable path degrades to the plain "run ended." rather than raising.
    """
    plain = f"{ctx.label}: run ended."
    path = ctx.artifact_path
    if not path:
        return Outcome(plain)
    try:
        has_packet = os.path.isfile(path) and os.path.getsize(path) > 0 and \
            bool(open(path, encoding="utf-8").read().strip())
    except OSError:
        return Outcome(plain)
    if has_packet:
        return Outcome(f"📋 {ctx.label}: fix packet authored at {path}.")
    return Outcome(f"⚠️ {ctx.label}: no packet written — the author may have stopped.")


# --- apply-packet: the outcome is whether the round committed ----------------------


def apply_packet(ctx: OutcomeContext) -> Outcome:
    """Did the fixer commit the round? A moved HEAD is the commit; an unchanged one is not.

    Outside a repo (no HEAD to read) it must not claim a commit it cannot see, so it
    reports the neutral end rather than a false success.
    """
    if ctx.head_before is None or ctx.head_after is None:
        return Outcome(f"{ctx.label}: run ended.")
    if ctx.head_before != ctx.head_after:
        return Outcome(f"✅ {ctx.label}: round committed.")
    return Outcome(f"⚠️ {ctx.label}: the fixer committed nothing — it may have stopped.")


# --- srs: read the tree product-srs authored ---------------------------------------
#
# Authored against the SRS contract, NOT by cloning `prd()` — the two differ in four
# load-bearing ways, and every difference below is one of them:
#   - Status offers the same three values the PRD's does — Draft|Settled|Locked
#     (srs_template.md) — but they are not worth the same thing here; the last bullet owns
#     the difference. Do NOT narrow this set: product-srs stamps Settled (its SKILL.md sets
#     the line from the done condition), and the no-companion branch below accepts all three.
#   - The companion has open issues and choices, then § 3, items raised from downstream —
#     no directives bucket, so the pending phrase never names a directive.
#   - docs/trail/srs/ exists (product-srs SKILL.md § inputs), but this reporter does not read
#     it, so it derives no cycle number — the body never says "cycle N".
#   - The done signal is the companion's ABSENCE, and product-srs does not auto-Lock, so a
#     Draft SRS with no companion is the NORMAL done state — a success, not the "not Settled"
#     warning the prd reporter emits for the same shape.
#
# The generic parsers (`parse_status` / `parse_version`) and `count_buckets` (whose third
# return is § 3, the raised count) are run-type-agnostic.


def _srs_pending_phrase(buckets, raised=0):
    """"1 open issue" / "2 choices to confirm" — only the non-zero terms.

    The SRS companion has no directives bucket, so no "directive" term can ever appear in
    the phrase; its § 3 is `raised`.
    """
    n1, n2 = buckets
    parts = []
    if n1:
        parts.append(f"{n1} open issue" + ("" if n1 == 1 else "s"))
    if n2:
        parts.append(f"{n2} choice" + ("" if n2 == 1 else "s") + " to confirm")
    if raised:
        parts.append(_raised_term(raised))
    return ", ".join(parts)


def read_srs(product_path: str):
    """What is on disk under <product>/docs/ for an SRS, or None if it cannot be read.

    The count reuses `count_buckets`, whose third return is the companion's § 3, items
    raised from downstream, kept apart as `raised`. The only function here that touches the
    filesystem, so the degrade path is one `except` in one place (mirrors `read_product`).
    """
    docs = os.path.join(product_path, "docs")
    srs_path = os.path.join(docs, "SRS.md")
    try:
        if not os.path.isfile(srs_path):
            return {"srs": False, "status": None, "version": None,
                    "companion": False, "buckets": (0, 0), "raised": 0}
        with open(srs_path, encoding="utf-8") as fh:
            srs_text = fh.read()
        companion_path = os.path.join(docs, "SRS_open_issues.md")
        companion = os.path.isfile(companion_path)
        buckets = (0, 0)
        raised = 0
        if companion:
            with open(companion_path, encoding="utf-8") as fh:
                open_issues, choices, raised = count_buckets(fh.read())
                buckets = (open_issues, choices)
        return {
            "srs": True,
            "status": parse_status(srs_text),
            "version": parse_version(srs_text),
            "companion": companion,
            "buckets": buckets,
            "raised": raised,
        }
    except OSError:
        return None


def _srs_body(label: str, product_path: str | None) -> str:
    """What the run produced, read from the SRS product. Never what state the agent is in.

    Best-effort like `_prd_body`: the wide `except Exception` is deliberate — a parser bug
    must cost specificity, never the message.
    """
    plain = f"{label}: run ended."
    if not product_path:
        return plain
    try:
        p = read_srs(product_path)
        if p is None:
            return (f"⚠️ {label}: run ended, but the product at {product_path} could not be "
                    f"read — what it produced is unknown.")
        if not p["srs"]:
            return f"⚠️ {label}: no SRS at docs/SRS.md — this run left nothing to read."

        srs_ref = f"SRS v{p['version']}" if p["version"] else "SRS"
        n1, n2 = p["buckets"]

        if p["companion"]:
            # The companion is out for answers, so the round is still open.
            if n1 == 0 and n2 == 0 and p["raised"] == 0:
                return (f"⚠️ {label}: {srs_ref} — docs/SRS_open_issues.md is present but lists "
                        f"no items. The run may not have finished clearing it; check it and "
                        f"re-run.")
            return (f"📋 {label}: {srs_ref} — {_srs_pending_phrase(p['buckets'], p['raised'])}.\n"
                    f"Answer docs/SRS_open_issues.md, commit, re-run.")

        # No companion. Its absence is the done signal — but only because we already
        # know the SRS exists. An empty directory has no companion either.
        # Status is set from that same condition: Settled ONLY when a run ends with no
        # companion on disk, Draft otherwise (product-srs SKILL.md L191-193) — one condition
        # read twice. So Draft here is a state no finished run leaves behind: a run that died
        # before stamping the line, or a companion removed by hand. Both are worth a look.
        # Locked is the owner's ratification, never auto-set, so it is a clean done.
        status = p["status"]
        if status == "Locked":
            return f"✅ {label}: {srs_ref} is Locked — nothing pending."
        if status == "Settled":
            return f"✅ {label}: {srs_ref} — nothing pending."
        # Draft (impossible from a finished run), or a value that could not be parsed.
        return (f"⚠️ {label}: {srs_ref} — no open-issues file, but Status is "
                f"\"{status or 'unreadable'}\", not Settled. The run "
                f"may not have finished; check docs/SRS.md.")
    except Exception:
        return plain


def srs(ctx: OutcomeContext) -> Outcome:
    """The product-srs outcome — reads docs/SRS.md + docs/SRS_open_issues.md.

    An unchanged HEAD decides the message rather than annotating one, as it does in `prd`
    and `apply_packet`: a run that committed nothing leaves the previous run's files on
    disk, so reading them produces a headline of figures and an instruction that belong to
    that earlier run. So the product is not read at all in that case.

    An unreadable HEAD is a third case: it is not evidence of an idle run, so it claims
    neither outcome and the body is the product read.

    A companion left unanswered (`companion_state`) gets a different unchanged-HEAD message
    than a stall — the case this whole family exists for: a live product's `product-srs` run
    left one raised, unanswered item, and the old message read as a failure it was not.
    """
    if ctx.head_before is not None and ctx.head_before == ctx.head_after:
        docs_dir = os.path.join(ctx.artifact_path, "docs") if ctx.artifact_path else None
        return Outcome(_committed_nothing_for(ctx.label, "SRS", docs_dir))
    return Outcome(_srs_body(ctx.label, ctx.artifact_path), None)


# --- uxd: sits between prd and srs, authored against the real UXD contract ---------
#
# Not a clone of either sibling — it takes its bucket shape from `srs` (the companion has
# Open issues + Choices to confirm + Raised from downstream, no directives bucket) and its
# cycle number from
# `prd` (docs/trail/uxd/ exists — product-uxd SKILL.md § The files and the loop — and IS
# read here, unlike the srs reporter which reports none over a trail that exists). Status
# carries the same three values as both siblings under the same rule: Settled only when the
# run ends with no companion on disk (product-uxd SKILL.md), Draft otherwise — so
# Draft-with-no-companion is a state no finished run can leave behind, and this reporter
# warns (OQ1 default A, docs/proposals/product-uxd-launcher/rationale.md), matching the prd
# reading and the srs reporter's reading since 2026-08-01.
#
# The generic parsers (`parse_status` / `parse_version`), the count (`count_buckets`, its
# third return the raised count, as in `read_srs`), and `trail_cycles`
# (parameterized past its prd-only default) are all run-type-agnostic and reused as-is.


def _uxd_pending_phrase(buckets, raised=0):
    """"1 open issue" / "2 choices to confirm" — only the non-zero terms.

    The UXD companion has no directives bucket, so no "directive" term can ever appear in
    the phrase; its § 3 is `raised`. Same shape as `_srs_pending_phrase`;
    kept as its own function because this reporter's open-round line also carries a cycle
    number, which `_srs_pending_phrase`'s callers never need.
    """
    n1, n2 = buckets
    parts = []
    if n1:
        parts.append(f"{n1} open issue" + ("" if n1 == 1 else "s"))
    if n2:
        parts.append(f"{n2} choice" + ("" if n2 == 1 else "s") + " to confirm")
    if raised:
        parts.append(_raised_term(raised))
    return ", ".join(parts)


def read_uxd(product_path: str):
    """What is on disk under <product>/docs/ for a UXD, or None if it cannot be read.

    The count reuses `count_buckets` and keeps its third return as `raised`, as `read_srs`
    does. The trail read is `read_product`'s — `trail/uxd/` exists and is read for
    the cycle number, unlike `read_srs`'s silence over `trail/srs/`. The only function here
    that touches the filesystem, so the degrade path is one `except` in one place.
    """
    docs = os.path.join(product_path, "docs")
    uxd_path = os.path.join(docs, "UXD.md")
    try:
        if not os.path.isfile(uxd_path):
            return {"uxd": False, "status": None, "version": None,
                    "companion": False, "buckets": (0, 0), "raised": 0, "trail": 0}
        with open(uxd_path, encoding="utf-8") as fh:
            uxd_text = fh.read()
        companion_path = os.path.join(docs, "UXD_open_issues.md")
        companion = os.path.isfile(companion_path)
        buckets = (0, 0)
        raised = 0
        if companion:
            with open(companion_path, encoding="utf-8") as fh:
                open_issues, choices, raised = count_buckets(fh.read())
                buckets = (open_issues, choices)
        return {
            "uxd": True,
            "status": parse_status(uxd_text),
            "version": parse_version(uxd_text),
            "companion": companion,
            "buckets": buckets,
            "raised": raised,
            "trail": trail_cycles(docs, "trail/uxd"),
        }
    except OSError:
        return None


def _uxd_body(label: str, product_path: str | None) -> str:
    """What the run produced, read from the UXD product. Never what state the agent is in.

    Best-effort like `_prd_body`/`_srs_body`: the wide `except Exception` is deliberate — a
    parser bug must cost specificity, never the message.
    """
    plain = f"{label}: run ended."
    if not product_path:
        return plain
    try:
        p = read_uxd(product_path)
        if p is None:
            return (f"⚠️ {label}: run ended, but the product at {product_path} could not be "
                    f"read — what it produced is unknown.")
        if not p["uxd"]:
            return f"⚠️ {label}: no UXD at docs/UXD.md — this run left nothing to read."

        uxd_ref = f"UXD v{p['version']}" if p["version"] else "UXD"
        n1, n2 = p["buckets"]

        if p["companion"]:
            # The companion is out for answers, so the cycle it belongs to is the one
            # after the last round folded into the trail — the prd reporter's own reasoning,
            # reused here since uxd shares prd's trail shape (unlike srs).
            cycle = p["trail"] + 1
            if n1 == 0 and n2 == 0 and p["raised"] == 0:
                return (f"⚠️ {label}: {uxd_ref} — docs/UXD_open_issues.md is present but lists "
                        f"no items. The run may not have finished clearing it; check it and "
                        f"re-run.")
            return (f"📋 {label}: {uxd_ref}, cycle {cycle} complete — "
                    f"{_uxd_pending_phrase(p['buckets'], p['raised'])}.\n"
                    f"Answer docs/UXD_open_issues.md, commit, re-run.")

        # No companion. Its absence is the done signal — but only because we already
        # know the UXD exists. No cycle number here: the trail counts rounds folded in,
        # a different quantity, and a first run that settled everything has none.
        status = p["status"]
        if status == "Settled":
            return f"✅ {label}: {uxd_ref} settled — nothing pending."
        if status == "Locked":
            return f"✅ {label}: {uxd_ref} is Locked — nothing pending."
        # Draft (impossible from a finished run, OQ1 default A), or a value that could not
        # be parsed.
        return (f"⚠️ {label}: {uxd_ref} — no open-issues file, but Status is "
                f"\"{status or 'unreadable'}\", not Settled. The run may not have finished; "
                f"check docs/UXD.md.")
    except Exception:
        return plain


def uxd(ctx: OutcomeContext) -> Outcome:
    """The product-uxd outcome — reads docs/UXD.md + docs/UXD_open_issues.md +
    docs/trail/uxd/.

    An unchanged HEAD decides the message rather than annotating one, as it does in
    `prd`/`srs`: a run that committed nothing leaves the previous run's files on disk, and
    this reporter's cycle number is read from a trail those files carry. So the product is
    not read at all in that case.

    An unreadable HEAD is a third case: it is not evidence of an idle run, so it claims
    neither outcome and the body is the product read.

    A companion left unanswered (`companion_state`) gets a different unchanged-HEAD message
    than a stall — the run had nothing to fold, not nothing to say.
    """
    if ctx.head_before is not None and ctx.head_before == ctx.head_after:
        docs_dir = os.path.join(ctx.artifact_path, "docs") if ctx.artifact_path else None
        return Outcome(_committed_nothing_for(ctx.label, "UXD", docs_dir))
    return Outcome(_uxd_body(ctx.label, ctx.artifact_path), None)


# --- design: three buckets, a cycle number like uxd, no directives -----------------------
#
# Not a clone of either sibling — the companion has Open issues + Choices to confirm +
# Raised from downstream (design_open_issues_template.md; a declared omission is a § 2
# choice) and it takes its cycle number from `prd`/`uxd` (docs/trail/design/ exists —
# product-design SKILL.md :67, :69-72 — and IS read here). Status carries the same three
# values as every sibling under the same rule: Settled only when the run ends with no
# companion on disk (SKILL.md :209-216), Draft otherwise — so Draft-with-no-companion warns,
# matching the family's settled reading (not an open question here the way it was for uxd's
# OQ1).
#
# The one place this reporter cannot reuse a sibling's helper: `_pending_phrase` (the PRD's)
# hard-codes the word "directive" for its third bucket, and this companion's third bucket is
# "Raised from downstream". `_design_pending_phrase` is its own function so "directive" can
# never leak into a design notification.
#
# The generic parsers (`parse_status` / `parse_version`), `count_buckets` with all three
# returns, and `trail_cycles` (parameterized past its prd-only default) are all
# run-type-agnostic and reused as-is.


def _design_pending_phrase(buckets):
    """"1 choice to confirm" / "2 open issues, 1 item raised from downstream" — only the
    non-zero terms, and never the word "directive" — that term belongs to the PRD companion
    alone."""
    n1, n2, n3 = buckets
    parts = []
    if n1:
        parts.append(f"{n1} open issue" + ("" if n1 == 1 else "s"))
    if n2:
        parts.append(f"{n2} choice" + ("" if n2 == 1 else "s") + " to confirm")
    if n3:
        parts.append(_raised_term(n3))
    return ", ".join(parts)


def read_design(product_path: str):
    """What is on disk under <product>/docs/ for a DESIGN, or None if it cannot be read.

    The three-bucket count reuses `count_buckets` unchanged, as `read_product` does — the
    only function here that touches the filesystem, so the degrade path is one `except` in
    one place.
    """
    docs = os.path.join(product_path, "docs")
    design_path = os.path.join(docs, "DESIGN.md")
    try:
        if not os.path.isfile(design_path):
            return {"design": False, "status": None, "version": None,
                    "companion": False, "buckets": (0, 0, 0), "trail": 0}
        with open(design_path, encoding="utf-8") as fh:
            design_text = fh.read()
        companion_path = os.path.join(docs, "DESIGN_open_issues.md")
        companion = os.path.isfile(companion_path)
        buckets = (0, 0, 0)
        if companion:
            with open(companion_path, encoding="utf-8") as fh:
                buckets = count_buckets(fh.read())
        return {
            "design": True,
            "status": parse_status(design_text),
            "version": parse_version(design_text),
            "companion": companion,
            "buckets": buckets,
            "trail": trail_cycles(docs, "trail/design"),
        }
    except OSError:
        return None


def _design_body(label: str, product_path: str | None) -> str:
    """What the run produced, read from the DESIGN product. Never what state the agent is in.

    Best-effort like `_prd_body`/`_uxd_body`: the wide `except Exception` is deliberate — a
    parser bug must cost specificity, never the message.
    """
    plain = f"{label}: run ended."
    if not product_path:
        return plain
    try:
        p = read_design(product_path)
        if p is None:
            return (f"⚠️ {label}: run ended, but the product at {product_path} could not be "
                    f"read — what it produced is unknown.")
        if not p["design"]:
            return f"⚠️ {label}: no DESIGN at docs/DESIGN.md — this run left nothing to read."

        design_ref = f"DESIGN v{p['version']}" if p["version"] else "DESIGN"
        n1, n2, n3 = p["buckets"]

        if p["companion"]:
            # The companion is out for answers, so the cycle it belongs to is the one
            # after the last round folded into the trail — the prd reporter's own reasoning,
            # reused here since design shares prd's trail shape.
            cycle = p["trail"] + 1
            if n1 == 0 and n2 == 0 and n3 == 0:
                return (f"⚠️ {label}: {design_ref} — docs/DESIGN_open_issues.md is present "
                        f"but lists no items. The run may not have finished clearing it; "
                        f"check it and re-run.")
            return (f"📋 {label}: {design_ref}, cycle {cycle} complete — "
                    f"{_design_pending_phrase(p['buckets'])}.\n"
                    f"Answer docs/DESIGN_open_issues.md, commit, re-run.")

        # No companion. Its absence is the done signal — but only because we already
        # know the DESIGN exists. No cycle number here: the trail counts rounds folded in,
        # a different quantity, and a first run that settled everything has none.
        status = p["status"]
        if status == "Settled":
            return f"✅ {label}: {design_ref} settled — nothing pending."
        if status == "Locked":
            return f"✅ {label}: {design_ref} is Locked — nothing pending."
        # Draft (impossible from a finished run, per the family's settled reading), or a
        # value that could not be parsed.
        return (f"⚠️ {label}: {design_ref} — no open-issues file, but Status is "
                f"\"{status or 'unreadable'}\", not Settled. The run may not have finished; "
                f"check docs/DESIGN.md.")
    except Exception:
        return plain


def design(ctx: OutcomeContext) -> Outcome:
    """The product-design outcome — reads docs/DESIGN.md + docs/DESIGN_open_issues.md +
    docs/trail/design/.

    An unchanged HEAD decides the message rather than annotating one, as it does in
    `prd`/`srs`/`uxd`: a run that committed nothing leaves the previous run's files on disk,
    and this reporter reads the widest headline of the four off them — a version, a cycle
    and three bucket counts. So the product is not read at all in that case.

    An unreadable HEAD is a third case: it is not evidence of an idle run, so it claims
    neither outcome and the body is the product read.

    A companion left unanswered (`companion_state`) gets a different unchanged-HEAD message
    than a stall — the run had nothing to fold, not nothing to say.
    """
    if ctx.head_before is not None and ctx.head_before == ctx.head_after:
        docs_dir = os.path.join(ctx.artifact_path, "docs") if ctx.artifact_path else None
        return Outcome(_committed_nothing_for(ctx.label, "DESIGN", docs_dir))
    return Outcome(_design_body(ctx.label, ctx.artifact_path), None)


# --- content: uxd's arity and uxd's cycle, with the CONTENT contract's own names ---
#
# Not a clone of a sibling — it takes its bucket shape from the real CONTENT companion
# (Open issues + Choices to confirm + Raised from downstream, content_open_issues_template.md
# — the UXD/SRS shape) and its cycle number from `uxd`/`prd`
# (docs/trail/content/cycle-<N>.md exists and IS read — product-content SKILL.md :68, :71-72).
# Status carries the same three values under the same rule as every sibling: Settled only
# when the run ends with no companion on disk (SKILL.md :250-251), Draft otherwise — so
# Draft-with-no-companion warns, the family's settled reading.


def _two_bucket_pending_phrase(buckets, raised=0):
    """"1 open issue" / "2 choices to confirm" — only the non-zero terms.

    Two answer buckets and `raised`, the companion's § 3 — so "directive" (the PRD
    companion's term) can never appear in the phrase.

    Named for the shape rather than for one run type, because it is the shape three
    reporters share: `_srs_pending_phrase` and `_uxd_pending_phrase` are this function
    already, kept as their own copies for reasons their docstrings state. Consolidating the
    three is a future project — tracked as an unpicked seed in the tools project's own
    journey — and repointing them here is all it costs — which is why this one is not a
    fourth `_content_pending_phrase`.
    """
    n1, n2 = buckets
    parts = []
    if n1:
        parts.append(f"{n1} open issue" + ("" if n1 == 1 else "s"))
    if n2:
        parts.append(f"{n2} choice" + ("" if n2 == 1 else "s") + " to confirm")
    if raised:
        parts.append(_raised_term(raised))
    return ", ".join(parts)


def read_content(product_path: str):
    """What is on disk under <product>/docs/ for a CONTENT, or None if it cannot be read.

    The count reuses `count_buckets` and keeps its third return as `raised`, as `read_uxd`
    and `read_srs` do. The trail read is `read_product`'s — `trail/content/`
    exists and is read for the cycle number, like `trail/uxd/`. The only function here that
    touches the filesystem, so the degrade path is one `except` in one place.
    """
    docs = os.path.join(product_path, "docs")
    content_path = os.path.join(docs, "CONTENT.md")
    try:
        if not os.path.isfile(content_path):
            return {"content": False, "status": None, "version": None,
                    "companion": False, "buckets": (0, 0), "raised": 0, "trail": 0}
        with open(content_path, encoding="utf-8") as fh:
            content_text = fh.read()
        companion_path = os.path.join(docs, "CONTENT_open_issues.md")
        companion = os.path.isfile(companion_path)
        buckets = (0, 0)
        raised = 0
        if companion:
            with open(companion_path, encoding="utf-8") as fh:
                open_issues, choices, raised = count_buckets(fh.read())
                buckets = (open_issues, choices)
        return {
            "content": True,
            "status": parse_status(content_text),
            "version": parse_version(content_text),
            "companion": companion,
            "buckets": buckets,
            "raised": raised,
            "trail": trail_cycles(docs, "trail/content"),
        }
    except OSError:
        return None


def _content_body(label: str, product_path: str | None) -> str:
    """What the run produced, read from the CONTENT product. Never what state the agent is in.

    Best-effort like `_prd_body`/`_uxd_body`: the wide `except Exception` is deliberate — a
    parser bug must cost specificity, never the message.
    """
    plain = f"{label}: run ended."
    if not product_path:
        return plain
    try:
        p = read_content(product_path)
        if p is None:
            return (f"⚠️ {label}: run ended, but the product at {product_path} could not be "
                    f"read — what it produced is unknown.")
        if not p["content"]:
            return f"⚠️ {label}: no CONTENT at docs/CONTENT.md — this run left nothing to read."

        content_ref = f"CONTENT v{p['version']}" if p["version"] else "CONTENT"
        n1, n2 = p["buckets"]

        if p["companion"]:
            # The companion is out for answers, so the cycle it belongs to is the one
            # after the last round folded into the trail — the prd reporter's own reasoning,
            # reused here since content shares prd's trail shape.
            cycle = p["trail"] + 1
            if n1 == 0 and n2 == 0 and p["raised"] == 0:
                return (f"⚠️ {label}: {content_ref} — docs/CONTENT_open_issues.md is present "
                        f"but lists no items. The run may not have finished clearing it; "
                        f"check it and re-run.")
            return (f"📋 {label}: {content_ref}, cycle {cycle} complete — "
                    f"{_two_bucket_pending_phrase(p['buckets'], p['raised'])}.\n"
                    f"Answer docs/CONTENT_open_issues.md, commit, re-run.")

        # No companion. Its absence is the done signal — but only because we already
        # know the CONTENT exists. No cycle number here: the trail counts rounds folded in,
        # a different quantity, and a first run that settled everything has none.
        status = p["status"]
        if status == "Settled":
            return f"✅ {label}: {content_ref} settled — nothing pending."
        if status == "Locked":
            return f"✅ {label}: {content_ref} is Locked — nothing pending."
        # Draft (impossible from a finished run, SKILL.md :250-251), or a value that could
        # not be parsed.
        return (f"⚠️ {label}: {content_ref} — no open-issues file, but Status is "
                f"\"{status or 'unreadable'}\", not Settled. The run may not have finished; "
                f"check docs/CONTENT.md.")
    except Exception:
        return plain


def content(ctx: OutcomeContext) -> Outcome:
    """The product-content outcome — reads docs/CONTENT.md + docs/CONTENT_open_issues.md +
    docs/trail/content/.

    An unchanged HEAD decides the message rather than annotating one, as it does in
    `prd`/`srs`/`uxd`/`design`: a run that committed nothing leaves the previous run's files
    on disk, and this reporter's cycle number is read from a trail those files carry. So the
    product is not read at all in that case.

    An unreadable HEAD is a third case: it is not evidence of an idle run, so it claims
    neither outcome and the body is the product read.

    A companion left unanswered (`companion_state`) gets a different unchanged-HEAD message
    than a stall — the run had nothing to fold, not nothing to say.
    """
    if ctx.head_before is not None and ctx.head_before == ctx.head_after:
        docs_dir = os.path.join(ctx.artifact_path, "docs") if ctx.artifact_path else None
        return Outcome(_committed_nothing_for(ctx.label, "CONTENT", docs_dir))
    return Outcome(_content_body(ctx.label, ctx.artifact_path), None)


# --- the instance layer: the writing bar and the two experience halves -------------
#
# Three run types, one shape, so one implementation. Each is INSTANCE-level: their
# launchers pass --artifact-path <instance root>, not a product path, and the documents
# sit under system/ rather than under a product's docs/. That is the whole difference
# from prd/srs/uxd/design, and it is why these do not reuse read_product.
#
# The second difference is arity. A product reporter reads ONE document; experience-visual
# and experience-voice each author TWO, tracked separately — a run can finish one and still
# be open on the other — so a spec carries a list and the body reports per document.
#
# Written as one parameterised shape rather than three near-identical reporters, on the
# same argument the companion-loop seed makes about its nine carriers: three copies of a
# message format drift the first time one of them is reworded, and nothing catches it.
_InstanceDoc = namedtuple("_InstanceDoc", "name filename companion")

_INSTANCE_SPECS = {
    # reporter name -> (docs dir under the instance, trail dir, third-bucket term, documents)
    "writing-bar": (
        "system/doctrine", "trail/writing_bar", None,
        [_InstanceDoc("writing bar", "writing_bar.md", "writing_bar_open_issues.md")],
    ),
    "experience-visual": (
        "system/experience", "trail/visual", None,
        [_InstanceDoc("visual restrictions", "visual_restrictions.md",
                      "visual_restrictions_open_issues.md"),
         _InstanceDoc("visual direction", "visual_direction.md",
                      "visual_direction_open_issues.md")],
    ),
    "experience-voice": (
        # Only the verbal half has a third bucket: its companion's § 3 is "Owed to the
        # visual half", the one item kind that reaches the other medium. The visual
        # companion has two sections and the writing bar's has two, so n3 is 0 there and
        # the term is never reached.
        "system/experience", "trail/voice", "owed to the visual half",
        [_InstanceDoc("voice restrictions", "voice_restrictions.md",
                      "voice_restrictions_open_issues.md"),
         _InstanceDoc("voice direction", "voice_direction.md",
                      "voice_direction_open_issues.md")],
    ),
}


def _instance_pending_phrase(buckets, third_term):
    """"2 open issues, 1 choice to confirm" — only the non-zero terms.

    The third term is the spec's, because it differs by run type and naming the wrong one
    is the same class of error as `_design_pending_phrase` avoids by never saying
    "directive".
    """
    n1, n2, n3 = buckets
    parts = []
    if n1:
        parts.append(f"{n1} open issue" + ("" if n1 == 1 else "s"))
    if n2:
        parts.append(f"{n2} choice" + ("" if n2 == 1 else "s") + " to confirm")
    if n3 and third_term:
        parts.append(f"{n3} {third_term}")
    return ", ".join(parts)


def read_instance_layer(instance_root: str, spec):
    """What is on disk for one instance-level layer, or None if it cannot be read.

    The only function here that touches the filesystem, so the degrade path is one
    `except` in one place — `read_design`'s arrangement, kept.
    """
    docs_rel, trail_name, _third, documents = spec
    docs = os.path.join(instance_root, docs_rel)
    try:
        out = []
        for doc in documents:
            doc_path = os.path.join(docs, doc.filename)
            if not os.path.isfile(doc_path):
                out.append({"doc": doc, "exists": False, "status": None, "version": None,
                            "companion": False, "buckets": (0, 0, 0)})
                continue
            with open(doc_path, encoding="utf-8") as fh:
                text = fh.read()
            companion_path = os.path.join(docs, doc.companion)
            companion = os.path.isfile(companion_path)
            buckets = (0, 0, 0)
            if companion:
                with open(companion_path, encoding="utf-8") as fh:
                    buckets = count_buckets(fh.read())
            out.append({"doc": doc, "exists": True, "status": parse_status(text),
                        "version": parse_version(text), "companion": companion,
                        "buckets": buckets})
        return {"documents": out, "trail": trail_cycles(docs, trail_name)}
    except OSError:
        return None


def _instance_doc_clause(entry, third_term, cycle) -> str:
    """One document's state, in a clause the body joins with the others."""
    doc = entry["doc"]
    if not entry["exists"]:
        return f"{doc.name} not authored yet"
    ref = f"v{entry['version']}" if entry["version"] else ""
    head = f"{doc.name}{' ' + ref if ref else ''}"
    if entry["companion"]:
        pending = _instance_pending_phrase(entry["buckets"], third_term)
        if not pending:
            return f"{head} — companion present but lists no items, check it"
        return f"{head} — cycle {cycle}, {pending} awaiting you"
    status = entry["status"]
    if status in ("Settled", "Locked"):
        return f"{head} {status.lower()}"
    return f"{head} — no companion, but Status is \"{status or 'unreadable'}\""


def _instance_body(label: str, instance_root: str | None, spec) -> str:
    """What the round produced, read from the instance. Never what state the agent is in.

    Best-effort like `_prd_body`/`_design_body`: the wide `except Exception` is deliberate —
    a parser bug must cost specificity, never the message.
    """
    docs_rel, _trail, third_term, documents = spec
    plain = f"{label}: run ended."
    if not instance_root:
        return plain
    try:
        p = read_instance_layer(instance_root, spec)
        if p is None:
            return (f"⚠️ {label}: run ended, but the layer at {instance_root}/{docs_rel} "
                    f"could not be read — what it produced is unknown.")
        entries = p["documents"]
        if not any(e["exists"] for e in entries):
            names = " or ".join(d.name for d in documents)
            return f"⚠️ {label}: no {names} on disk — this run left nothing to read."

        # The companion is out for answers, so its cycle is the one after the last round
        # folded into the trail. One trail serves both documents of a pair, which is why
        # the number is computed once here rather than per document.
        cycle = p["trail"] + 1
        clauses = " · ".join(_instance_doc_clause(e, third_term, cycle) for e in entries)
        open_ones = [e["doc"].companion for e in entries if e["companion"]]

        if open_ones:
            where = ", ".join(f"{docs_rel}/{c}" for c in open_ones)
            return (f"📋 {label}: {clauses}.\n"
                    f"Answer {where}, commit, re-run.")
        # No companion anywhere. Its absence is the done signal for that document, and
        # every document exists, so the layer is closed.
        return f"✅ {label}: {clauses} — nothing pending."
    except Exception:
        return plain


def _instance_reporter(spec_key: str):
    """Build the reporter for one instance-level run type.

    An unchanged HEAD decides the message rather than annotating one, exactly as it does in
    `prd`/`srs`/`uxd`/`design`: a run that committed nothing leaves the previous run's files
    on disk, and this reporter would read a cycle and bucket counts off them and report
    another run's work as this one's. So the layer is not read at all in that case.
    """
    spec = _INSTANCE_SPECS[spec_key]
    artifact = " / ".join(d.name for d in spec[3])

    def _reporter(ctx: OutcomeContext) -> Outcome:
        if ctx.head_before is not None and ctx.head_before == ctx.head_after:
            return Outcome(_committed_nothing(ctx.label, artifact))
        return Outcome(_instance_body(ctx.label, ctx.artifact_path, spec), None)

    _reporter.__name__ = spec_key.replace("-", "_")
    return _reporter


writing_bar = _instance_reporter("writing-bar")
experience_visual = _instance_reporter("experience-visual")
experience_voice = _instance_reporter("experience-voice")


# --- agari: a project-management artifact, not a product document ------------------
#
# Authored against `project-agari`'s own file contract, NOT by cloning a sibling. Four
# load-bearing differences, and every rule below is one of them:
#   - The three files sit DIRECTLY under the artifact path — `system/projects/<name>/` in
#     the INSTANCE repo, beside the project card (skills/cpo/.claude/skills/project-agari/SKILL.md
#     :73-81) — with no `docs/` hop, so no product reader here can be reused. That is also
#     why this is not an `_INSTANCE_SPECS` entry: those resolve a fixed directory under an
#     instance root, and this launcher passes the project folder itself.
#   - `agari.md` carries NO `**Status:**` and NO `**Version:**`. `parse_status` /
#     `parse_version` therefore have nothing to read, and the declared signal is the
#     `PLACEHOLDER` marker `agari_template.md:12` stamps into every fresh card, which is the
#     same signal the launcher's own pre-launch report keys on.
#   - The companion has TWO buckets and no directives bucket, stated in
#     `agari_open_issues_template.md`'s own closing comment. `_agari_pending_phrase` names
#     two terms and no third, so an owner-pasted `## 3.` can never surface one.
#   - **Declared needs BOTH signals**: the placeholder gone AND no companion on disk (the
#     companion's absence is the done signal, SKILL.md:80). Do not report either alone as
#     settled — an undeclared Agari with no companion is a run that did not finish, and
#     pairing the two facts as though each stood on its own is the wart the launcher's
#     pre-launch line already carries.
#
# `count_buckets`, `trail_cycles` (parameterised past its prd-only default) and
# `_committed_nothing` are run-type-agnostic and reused as they stand.


def _agari_pending_phrase(buckets):
    """"1 open issue" / "2 choices to confirm" — only the non-zero terms.

    Two buckets by construction, so no third term exists to name. Its own function rather
    than a sibling's for the reason `_design_pending_phrase` is: a phrase function carries
    its companion's vocabulary, and borrowing one lends the wrong words to this message.
    """
    n1, n2 = buckets
    parts = []
    if n1:
        parts.append(f"{n1} open issue" + ("" if n1 == 1 else "s"))
    if n2:
        parts.append(f"{n2} choice" + ("" if n2 == 1 else "s") + " to confirm")
    return ", ".join(parts)


def read_agari(project_path: str):
    """What is on disk in a project folder for an Agari, or None if it cannot be read.

    The two-bucket count reuses `count_buckets` and drops its third return, which the Agari
    companion never fills. `placeholder` is a substring test on the whole file, not a
    parse: the marker is a stamped word, and `agari_template.md` places it in a blockquote
    that any heading-anchored reader would miss. The only function here that touches the
    filesystem, so the degrade path is one `except` in one place.
    """
    agari_path = os.path.join(project_path, "agari.md")
    try:
        if not os.path.isfile(agari_path):
            return {"agari": False, "placeholder": False,
                    "companion": False, "buckets": (0, 0), "trail": 0}
        with open(agari_path, encoding="utf-8") as fh:
            agari_text = fh.read()
        companion_path = os.path.join(project_path, "agari_open_issues.md")
        companion = os.path.isfile(companion_path)
        buckets = (0, 0)
        if companion:
            with open(companion_path, encoding="utf-8") as fh:
                open_issues, choices, _directives = count_buckets(fh.read())
                buckets = (open_issues, choices)
        return {
            "agari": True,
            "placeholder": "PLACEHOLDER" in agari_text,
            "companion": companion,
            "buckets": buckets,
            "trail": trail_cycles(project_path, "trail/agari"),
        }
    except OSError:
        return None


def _agari_body(label: str, project_path: str | None) -> str:
    """What the round produced, read from the project folder. Never the agent's state.

    Best-effort like `_prd_body`/`_design_body`: the wide `except Exception` is deliberate —
    a parser bug must cost specificity, never the message.

    The companion is named bare rather than as `system/projects/<name>/agari_open_issues.md`.
    That path is one launcher's directory layout, and this reporter's whole contract is
    `ctx.artifact_path`; deriving the layout from it would make the message lie the first
    time anything else passes a different folder. The label already names the project.
    """
    plain = f"{label}: run ended."
    if not project_path:
        return plain
    try:
        p = read_agari(project_path)
        if p is None:
            return (f"⚠️ {label}: run ended, but the project at {project_path} could not be "
                    f"read — what it produced is unknown.")
        if not p["agari"]:
            return (f"⚠️ {label}: no agari.md beside the project card — this run left "
                    f"nothing to read.")

        n1, n2 = p["buckets"]

        if p["companion"]:
            # The companion is out for answers, so the cycle it belongs to is the one after
            # the last round folded into the trail — the prd reporter's own reasoning, and
            # `trail/agari/` is numbered the same way (SKILL.md:83-86).
            cycle = p["trail"] + 1
            if n1 == 0 and n2 == 0:
                return (f"⚠️ {label}: agari_open_issues.md is present but lists no items. "
                        f"The run may not have finished clearing it; check it and re-run.")
            pending = _agari_pending_phrase(p["buckets"])
            if p["placeholder"]:
                # One run drafts the terminus and writes the companion, so a companion
                # beside an untouched placeholder is a run that never wrote its own draft.
                return (f"⚠️ {label}: agari.md still carries PLACEHOLDER, cycle {cycle} — "
                        f"{pending}.\nAnswer agari_open_issues.md, commit, re-run.")
            return (f"📋 {label}: Agari drafted, cycle {cycle} complete — {pending}.\n"
                    f"Answer agari_open_issues.md, commit, re-run.")

        # No companion. Its absence is the done signal — but only together with the marker
        # being gone, and only because we already know agari.md exists. No cycle number
        # here: the trail counts rounds folded in, a different quantity, and a first run
        # that settled everything has none.
        if p["placeholder"]:
            return (f"⚠️ {label}: no open-issues file, but agari.md still carries "
                    f"PLACEHOLDER — the Agari is not declared. The run may not have "
                    f"finished; check agari.md.")
        return f"✅ {label}: Agari declared — nothing pending."
    except Exception:
        return plain


def agari(ctx: OutcomeContext) -> Outcome:
    """The project-agari outcome — reads agari.md + agari_open_issues.md + trail/agari/.

    An unchanged HEAD decides the message rather than annotating one, as it does in
    `prd`/`srs`/`uxd`/`design` and the instance three: a run that committed nothing leaves
    the previous round's companion and trail on disk, and reading them reports that round's
    cycle and counts as this one's. So the project is not read at all in that case.

    An unreadable HEAD is a third case: it is not evidence of an idle run, so it claims
    neither outcome and the body is the read.

    A companion left unanswered (`companion_state`) gets a different unchanged-HEAD message
    than a stall — the run had nothing to fold, not nothing to say. No `docs/` hop here,
    unlike the product reporters: `agari_open_issues.md` sits bare beside `agari.md`
    (`_agari_body`'s own note).
    """
    if ctx.head_before is not None and ctx.head_before == ctx.head_after:
        return Outcome(_committed_nothing_for(ctx.label, "Agari", ctx.artifact_path))
    return Outcome(_agari_body(ctx.label, ctx.artifact_path), None)


# --- the registry: a new run type is one entry here, nothing in the watcher --------


# --- sdd-document: what the SDD on disk says, read from the document and its companion ----
#
# The SDD's completion message reports what the document became: version, status, open items
# and answered cycles. The archived ending and counter evaluations retain the document message's
# degradation on a malformed record (CP-420). No cap result is exposed. Nothing here reads the
# agent's state: the read is
# a file under `artifact_path`, like the siblings', not a second way of asking what the run did.


def read_sdd(product_path: str):
    """What is on disk under <product>/docs/ for an SDD, or None if it cannot be read.

    Every bucket is counted and summed rather than reported apart: the SDD companion's §§ 1-3
    are open issues, choices to confirm and cut calls, § 4 is disagreements and § 5 is items
    raised from downstream, and the owner's next move is the same for all five — answer them and
    re-run. `count_items`, not `count_buckets`: the three-bucket reader stops at § 3, and a
    companion holding only a § 5 item read as "0 open items" through it.
    """
    docs = os.path.join(product_path, "docs")
    sdd_path = os.path.join(docs, "SDD.md")
    try:
        if not os.path.isfile(sdd_path):
            return {"sdd": False, "status": None, "version": None,
                    "companion": False, "items": 0, "cycles": 0, "ended": None}
        with open(sdd_path, encoding="utf-8") as fh:
            sdd_text = fh.read()
        companion_path = os.path.join(docs, "SDD_open_issues.md")
        companion = os.path.isfile(companion_path)
        items = 0
        if companion:
            with open(companion_path, encoding="utf-8") as fh:
                items = sum(count_items(fh.read()).values())
        document = {
            "sdd": True,
            "status": parse_status(sdd_text),
            "version": parse_version(sdd_text),
            "companion": companion,
            "items": items,
            "cycles": trail_cycles(docs, "trail/sdd"),
            "ended": _sdd_ending(docs),
        }
        _check_sdd_record_counters(_sdd_record_text(docs))
        return document
    except OSError:
        return None


def _check_sdd_record_counters(text: str | None) -> None:
    """Preserve the document message's counter-parse failures at c87cd04af (CP-420).

    The retired cap calculation could fail converting a large integer. Its first satisfied pair
    also stopped evaluation, so validating every pair would change the surviving message too.
    """
    if text is None:
        return
    for line in text.splitlines():
        if line.lstrip("- ").startswith("**Counters:**"):
            for spent, allowed in re.findall(r"(\d+)/(\d+)", line):
                if int(spent) >= int(allowed):
                    return
            return


def _sdd_record_text(docs_dir: str) -> str | None:
    """The highest-numbered conversation record's text, or None if there is none to read.

    One reader for the record, so the "find the latest run-N.md" walk has one home rather than a
    second copy free to drift.

    The record lives in the SDD's own trail — it records how the SDD reached its current state,
    which is what `kensaiapp_structure.md` § *A trail is not the document's sibling* files under
    `trail/<doc>/`. That folder also holds `cycle-<N>.md` and `self_answer-<N>.md`, so the
    `run-` prefix below is what identifies a record; the highest-numbered *file* in there is
    routinely not one.
    """
    try:
        conv = os.path.join(docs_dir, "trail", "sdd")
        records = [f for f in os.listdir(conv) if f.startswith("run-") and f.endswith(".md")]
        if not records:
            return None
        latest = max(records, key=lambda f: int("".join(c for c in f if c.isdigit()) or 0))
        with open(os.path.join(conv, latest), encoding="utf-8") as fh:
            return fh.read()
    except (OSError, ValueError):
        return None


def _sdd_ending(docs_dir: str) -> str | None:
    """The "Ended because" sentence from the highest-numbered conversation record, or None.

    None covers two different things on purpose, and neither may be reported as an ending: a
    run still going, and a run that died before writing its closing block. Both are "this
    record does not say how it ended", which is the honest thing to print.
    """
    text = _sdd_record_text(docs_dir)
    if text is None:
        return None
    marker = "- **Ended because:**"
    if marker not in text:
        return None
    return text.split(marker, 1)[1].strip().splitlines()[0].strip() or None


def _sdd_document_reporter(
    read_document: Callable[[str], dict[str, str | int | bool | None] | None],
    committed_nothing: Callable[[str, str, str | None], str],
) -> Callable[[OutcomeContext], Outcome]:
    """Build the document-only reporter with its two filesystem readers supplied."""
    def reporter(ctx: OutcomeContext) -> Outcome:
        """Best-effort document outcome; a reader fault never loses the completion message."""
        try:
            if ctx.head_before is not None and ctx.head_before == ctx.head_after:
                docs = os.path.join(ctx.artifact_path, "docs") if ctx.artifact_path else None
                return Outcome(committed_nothing(ctx.label, "SDD", docs))
            document = read_document(ctx.artifact_path) if ctx.artifact_path else None
            head, is_head = _sdd_head(ctx.label, ctx.artifact_path, document)
            return Outcome(f"{head}." if is_head else head)
        except Exception:
            return Outcome(f"{ctx.label}: run ended.")
    return reporter


def _sdd_head(
    label: str,
    product_path: str | None,
    document: dict[str, str | int | bool | None] | None,
) -> tuple[str, bool]:
    """The document's own line — version, status, open items, answered cycles — and whether it is.

    The second value is False when the first is a complete message that has no head to extend:
    nothing to read, an unreadable product, no SDD, or a parser fault. The degradation texts
    have one home here. Best-effort like the siblings: a
    parser bug costs specificity, never the message.
    """
    plain = f"{label}: run ended."
    if not product_path:
        return plain, False
    try:
        p = document
        if p is None:
            return (f"⚠️ {label}: run ended, but the product at {product_path} could not be "
                    f"read — what it produced is unknown."), False
        if not p["sdd"]:
            return f"⚠️ {label}: no SDD at docs/SDD.md — this run left nothing to read.", False

        ref = f"SDD v{p['version']}" if p["version"] else "SDD"
        status = p["status"] or "status unreadable"
        head = f"{label}: {ref} — {status}"

        if p["companion"]:
            n = p["items"]
            head += f"; {n} open item{'' if n == 1 else 's'} for you"
        else:
            head += "; no open issues left"

        if p["cycles"]:
            head += f" (after {p['cycles']} answered cycle{'' if p['cycles'] == 1 else 's'})"
        return head, True
    except Exception:
        return plain, False


# --- fdr: content's shape, the FDR contract's own lowercase names ------------------
#
# Authored against the real FDR contract, NOT by cloning a sibling. Four load-bearing
# facts, and every rule below is one of them:
#   - THE THREE NAMES ARE LOWERCASE and match each other on purpose — docs/fdr.md,
#     docs/fdr_open_issues.md, docs/trail/fdr/
#     (skills/principal-pm/.claude/skills/product-fdr/SKILL.md :65-69). Every other product
#     reporter here reads an upper-cased document name, so
#     this is the one thing a find-replace from a sibling gets wrong, and it fails in the
#     worst direction: an upper-cased read reports "no FDR" against a product whose FDR is
#     sitting right there.
#   - The companion has two answer buckets and § 3, items raised from downstream
#     (fdr_open_issues_template.md) — the SRS/UXD/CONTENT shape. So the pending phrase is
#     `_two_bucket_pending_phrase`, REUSED rather than copied a fourth time: its docstring
#     already fixes why it is correct for exactly this shape, and "directive" (the PRD
#     companion's term) cannot reach an FDR message.
#   - docs/trail/fdr/cycle-<N>.md exists and IS read for the cycle number (SKILL.md :67,
#     :77-79), like prd's / uxd's / content's — through `trail_cycles`, which already takes
#     the folder name, so there is no second trail walker here.
#   - Status carries the same three values, and the FDR template states the rule itself:
#     "Draft = the companion is on disk … Settled = the companion is gone. Nothing awaits
#     the owner — the done signal … Locked = ratified … The owner's act, never the run's"
#     (fdr_template.md:71-73). So Draft-beside-no-companion warns, the family's settled
#     reading, and here the template says so in its own words rather than by inference.
#
# `parse_status` / `parse_version` / `count_buckets` / `trail_cycles` /
# `_two_bucket_pending_phrase` / `_committed_nothing` are all run-type-agnostic and reused
# as they stand. What is new is the read, the body and the reporter — nothing else.


def read_fdr(product_path: str):
    """What is on disk under <product>/docs/ for an FDR, or None if it cannot be read.

    The count reuses `count_buckets` and keeps its third return as `raised`, as
    `read_srs` / `read_uxd` / `read_content` do. The trail read is `read_product`'s,
    parameterised to `trail/fdr`. The only function here that touches the filesystem, so the
    degrade path is one `except` in one place.

    The three names are lowercase and are not a case-folded sibling's — see this section's
    opening note.
    """
    docs = os.path.join(product_path, "docs")
    fdr_path = os.path.join(docs, "fdr.md")
    try:
        if not os.path.isfile(fdr_path):
            return {"fdr": False, "status": None, "version": None,
                    "companion": False, "buckets": (0, 0), "raised": 0, "trail": 0}
        with open(fdr_path, encoding="utf-8") as fh:
            fdr_text = fh.read()
        companion_path = os.path.join(docs, "fdr_open_issues.md")
        companion = os.path.isfile(companion_path)
        buckets = (0, 0)
        raised = 0
        if companion:
            with open(companion_path, encoding="utf-8") as fh:
                open_issues, choices, raised = count_buckets(fh.read())
                buckets = (open_issues, choices)
        return {
            "fdr": True,
            "status": parse_status(fdr_text),
            "version": parse_version(fdr_text),
            "companion": companion,
            "buckets": buckets,
            "raised": raised,
            "trail": trail_cycles(docs, "trail/fdr"),
        }
    except OSError:
        return None


def _fdr_body(label: str, product_path: str | None) -> str:
    """What the run produced, read from the FDR product. Never what state the agent is in.

    Best-effort like `_prd_body`/`_content_body`: the wide `except Exception` is deliberate —
    a parser bug must cost specificity, never the message.
    """
    plain = f"{label}: run ended."
    if not product_path:
        return plain
    try:
        p = read_fdr(product_path)
        if p is None:
            return (f"⚠️ {label}: run ended, but the product at {product_path} could not be "
                    f"read — what it produced is unknown.")
        if not p["fdr"]:
            return f"⚠️ {label}: no FDR at docs/fdr.md — this run left nothing to read."

        fdr_ref = f"FDR v{p['version']}" if p["version"] else "FDR"
        n1, n2 = p["buckets"]

        if p["companion"]:
            # The companion is out for answers, so the cycle it belongs to is the one
            # after the last round folded into the trail — the prd reporter's own reasoning,
            # reused here since the FDR trail is numbered the same way (SKILL.md:77-79).
            cycle = p["trail"] + 1
            if n1 == 0 and n2 == 0 and p["raised"] == 0:
                return (f"⚠️ {label}: {fdr_ref} — docs/fdr_open_issues.md is present "
                        f"but lists no items. The run may not have finished clearing it; "
                        f"check it and re-run.")
            return (f"📋 {label}: {fdr_ref}, cycle {cycle} complete — "
                    f"{_two_bucket_pending_phrase(p['buckets'], p['raised'])}.\n"
                    f"Answer docs/fdr_open_issues.md, commit, re-run.")

        # No companion. Its absence is the done signal — but only because we already
        # know the FDR exists. No cycle number here: the trail counts rounds folded in,
        # a different quantity, and a first run that settled everything has none.
        status = p["status"]
        if status == "Settled":
            return f"✅ {label}: {fdr_ref} settled — nothing pending."
        if status == "Locked":
            return f"✅ {label}: {fdr_ref} is Locked — nothing pending."
        # Draft (impossible from a finished run, fdr_template.md:71-72), or a value that
        # could not be parsed.
        return (f"⚠️ {label}: {fdr_ref} — no open-issues file, but Status is "
                f"\"{status or 'unreadable'}\", not Settled. The run may not have finished; "
                f"check docs/fdr.md.")
    except Exception:
        return plain


def fdr(ctx: OutcomeContext) -> Outcome:
    """The product-fdr outcome — reads docs/fdr.md + docs/fdr_open_issues.md +
    docs/trail/fdr/.

    An unchanged HEAD decides the message rather than annotating one, as it does in every
    sibling that reads a product: a run that committed nothing leaves the previous run's
    files on disk, and this reporter's cycle number is read from a trail those files carry.
    So the product is not read at all in that case.

    An unreadable HEAD is a third case: it is not evidence of an idle run, so it claims
    neither outcome and the body is the product read.

    A companion left unanswered (`companion_state`) gets a different unchanged-HEAD message
    than a stall — the run had nothing to fold, not nothing to say. The lookup is
    case-insensitive, so `"FDR"` still finds this contract's own lowercase
    `fdr_open_issues.md`.
    """
    if ctx.head_before is not None and ctx.head_before == ctx.head_after:
        docs_dir = os.path.join(ctx.artifact_path, "docs") if ctx.artifact_path else None
        return Outcome(_committed_nothing_for(ctx.label, "FDR", docs_dir))
    return Outcome(_fdr_body(ctx.label, ctx.artifact_path), None)


# --- architecture: a directory whose record count is the state, plus a document, plus one
# shared companion --------------------------------------------------------------------------
#
# product-architecture differs from every sibling above it in the one structural way that is
# the whole point of a separate reporter existing: it authors a MANY-FILE, APPEND-ONLY log
# (`docs/adr/NNNN-slug.md`, one per decision) alongside ONE revised-in-place document
# (`docs/nfdr.md`) and ONE shared companion (`docs/architecture_open_issues.md`,
# `architecture_open_issues_template.md` — two answer buckets and § 3, items raised from
# downstream, the SRS/UXD/FDR shape). Every reporter above reads a single document's
# Status/Version line; this one's headline figure is a COUNT — the number of files in a
# directory, which no
# `parse_status`/`parse_version` pair can give it.
#
# THE COUNT IS THE DIRECTORY'S, NEVER THE INDEX'S. `docs/adr/README.md` is a projection,
# regenerated whenever a record lands (product-architecture SKILL.md § *The files and the
# loop*, "the one file here that IS rewritten") and can be stale by construction — reading it
# would report the projection and call it the log. `_adr_record_names` lists `docs/adr/` and
# matches the record filename shape (`\d{4}-.+\.md`), which excludes `README.md` for free (it
# does not open with four digits) rather than by naming it as an exclusion.
#
# THE COMPANION'S NAME MATCHES NEITHER FILE IT ANSWERS FOR. Every sibling composes its
# companion prefix from the one document it reads (`fdr` -> `fdr_open_issues.md`); this
# companion is `architecture_open_issues.md` because one run writes both records and the
# NFDR, and one companion carries every unsettled item for both (SKILL.md § *One companion
# for both records*). So `_committed_nothing_for` below is called with the artifact name
# `"Architecture"`, not `"NFDR"` — the string has to match the companion's own prefix
# (`_find_companion`'s contract), not the name of either document inside it.
#
# WHICH INPUTS WERE UNSETTLED WHEN THE RUN READ THEM is read best-effort, and openly so: the
# authoring prompt's own words are "the entry or record names, per input, the status it read"
# (`<CORE>/../skills/principal-architect/.claude/skills/product-architecture/prompts/rich.md` § *An unsettled input is read, not waited
# for*) — a rule about WHAT is said, not a fixed field this reporter can parse exactly.
# `_unsettled_inputs` is a name-near-"Draft" heuristic over the produced records and the
# NFDR, not a schema read: it surfaces the common phrasing and degrades to nothing (never a
# fabricated claim) when the documents word it some other way — the module docstring's own
# rule for a parser that cannot be certain.
#
# `count_buckets` (its third return the raised count, as in `read_srs`/`read_uxd`/`read_fdr`),
# `_two_bucket_pending_phrase`, `trail_cycles` (parameterised to `trail/architecture`) and
# `_committed_nothing_for` are all run-type-agnostic and reused as they stand.


_ADR_RECORD_RE = re.compile(r"^\d{4}-.+\.md$")


def _adr_record_names(adr_dir: str):
    """Every `NNNN-slug.md` record in `adr_dir`, sorted. `README.md` never matches — it does
    not open with four digits — so nothing here excludes it by name; the shape does."""
    try:
        names = os.listdir(adr_dir)
    except OSError:
        return []
    return sorted(n for n in names if _ADR_RECORD_RE.fullmatch(n))


_UNSETTLED_INPUT_NAMES = ("SRS", "SDD", "FDR")


_INPUTS_READ_RE = re.compile(r"^\*\*Inputs read:\*\*(.+)$", re.MULTILINE)


def _unsettled_inputs(texts):
    """Which of SRS / SDD / FDR were read at Draft. Two readings, and the first one that
    resolves wins.

    THE LINE, WHEN IT IS THERE. `nfdr_template.md`'s header fixes
    `**Inputs read:** SRS <status> · SDD <status> · FDR <status>` — every input the revision
    read, not only the unsettled ones, so a missing line is a run that did not write one
    rather than a run with nothing to report. That distinction is why this is a parse and not
    a search: reading the line tells us it was written, and reading the statuses off it tells
    us which were Draft.

    THE HEURISTIC, WHEN IT IS NOT. Records written before the line was fixed (and any product
    whose run predates it) carry the same fact in prose, so the older name-near-"Draft" scan
    stays as the fallback — checked in both directions within 60 characters on one physical
    line, because nothing fixed which side of a trace tag carried the status word.

    Returns the names found, in the family's own order, never a count — a flag to go re-read
    the trace, not a tally. An empty list is the ordinary, honest result when nothing was
    unsettled.
    """
    for text in texts:
        if not text:
            continue
        m = _INPUTS_READ_RE.search(text)
        if m:
            line = m.group(1)
            return [name for name in _UNSETTLED_INPUT_NAMES
                    if re.search(rf"\b{name}\b[^·]*\bDraft\b", line)]
    found = []
    for name in _UNSETTLED_INPUT_NAMES:
        pattern = re.compile(
            rf"\b{name}\b[^\n]{{0,60}}\bDraft\b|\bDraft\b[^\n]{{0,60}}\b{name}\b")
        if any(text and pattern.search(text) for text in texts):
            found.append(name)
    return found


def read_architecture(product_path: str):
    """What is on disk under <product>/docs/ for the architecture pair, or None if it cannot
    be read.

    The record count comes from listing `docs/adr/` (`_adr_record_names`), never from
    `docs/adr/README.md` — this section's own opening note. The count reuses
    `count_buckets` and keeps its third return as `raised`, as `read_srs`/`read_uxd`/
    `read_fdr` do. The only function here that touches the filesystem, so the degrade path is
    one `except` in one place.
    """
    docs = os.path.join(product_path, "docs")
    adr_dir = os.path.join(docs, "adr")
    nfdr_path = os.path.join(docs, "nfdr.md")
    try:
        records = _adr_record_names(adr_dir)
        record_texts = []
        for name in records:
            try:
                with open(os.path.join(adr_dir, name), encoding="utf-8") as fh:
                    record_texts.append(fh.read())
            except OSError:
                pass
        nfdr_exists = os.path.isfile(nfdr_path)
        status = version = None
        nfdr_text = ""
        if nfdr_exists:
            with open(nfdr_path, encoding="utf-8") as fh:
                nfdr_text = fh.read()
            status = parse_status(nfdr_text)
            version = parse_version(nfdr_text)
        companion_path = os.path.join(docs, "architecture_open_issues.md")
        companion = os.path.isfile(companion_path)
        buckets = (0, 0)
        raised = 0
        if companion:
            with open(companion_path, encoding="utf-8") as fh:
                open_issues, choices, raised = count_buckets(fh.read())
                buckets = (open_issues, choices)
        return {
            "records": len(records),
            "nfdr": nfdr_exists,
            "status": status,
            "version": version,
            "companion": companion,
            "buckets": buckets,
            "raised": raised,
            "trail": trail_cycles(docs, "trail/architecture"),
            "unsettled": _unsettled_inputs(record_texts + [nfdr_text]),
        }
    except OSError:
        return None


def _architecture_body(label: str, product_path: str | None) -> str:
    """What the run produced, read from the architecture pair. Never what state the agent is
    in.

    Best-effort like every sibling: the wide `except Exception` is deliberate — a parser bug
    must cost specificity, never the message.
    """
    plain = f"{label}: run ended."
    if not product_path:
        return plain
    try:
        p = read_architecture(product_path)
        if p is None:
            return (f"⚠️ {label}: run ended, but the product at {product_path} could not be "
                    f"read — what it produced is unknown.")

        n = p["records"]
        record_clause = f"{n} record" + ("" if n == 1 else "s") + " in the decision log"

        if n == 0 and not p["nfdr"] and not p["companion"]:
            return (f"⚠️ {label}: no NFDR at docs/nfdr.md and no records in docs/adr/ — "
                    f"this run left nothing to read.")

        unsettled = p["unsettled"]
        unsettled_clause = (
            f"\n⚠️ derived from {', '.join(unsettled)} while at Draft — verify before "
            f"treating this as final." if unsettled else "")

        nfdr_ref = None
        if p["nfdr"]:
            nfdr_ref = f"NFDR v{p['version']}" if p["version"] else "NFDR"
        n1, n2 = p["buckets"]

        if p["companion"]:
            # The companion is out for answers, so the cycle it belongs to is the one after
            # the last round folded into the trail — the prd reporter's own reasoning,
            # reused here since the architecture trail is numbered the same way.
            cycle = p["trail"] + 1
            if n1 == 0 and n2 == 0 and p["raised"] == 0:
                return (f"⚠️ {label}: {record_clause}; docs/architecture_open_issues.md is "
                        f"present but lists no items. The run may not have finished "
                        f"clearing it; check it and re-run.{unsettled_clause}")
            head = record_clause + (f"; {nfdr_ref}" if nfdr_ref else "; no NFDR yet")
            return (f"📋 {label}: {head}, cycle {cycle} complete — "
                    f"{_two_bucket_pending_phrase(p['buckets'], p['raised'])}.\n"
                    f"Answer docs/architecture_open_issues.md, commit, "
                    f"re-run.{unsettled_clause}")

        # No companion. Its absence is the done signal — but only together with the NFDR
        # existing and Settled/Locked. No cycle number here: the trail counts rounds folded
        # in, a different quantity, and a first run that settled everything has none.
        if not p["nfdr"]:
            return (f"⚠️ {label}: {record_clause}, but no NFDR at docs/nfdr.md — this run "
                    f"may not have finished.{unsettled_clause}")
        status = p["status"]
        if status == "Settled":
            return (f"✅ {label}: {record_clause}; {nfdr_ref} settled — "
                    f"nothing pending.{unsettled_clause}")
        if status == "Locked":
            return (f"✅ {label}: {record_clause}; {nfdr_ref} is Locked — "
                    f"nothing pending.{unsettled_clause}")
        # Draft (impossible from a finished run, per the family's settled reading), or a
        # value that could not be parsed.
        return (f"⚠️ {label}: {record_clause}; {nfdr_ref} — no open-issues file, but Status "
                f"is \"{status or 'unreadable'}\", not Settled. The run may not have "
                f"finished; check docs/nfdr.md.{unsettled_clause}")
    except Exception:
        return plain


def architecture(ctx: OutcomeContext) -> Outcome:
    """The product-architecture outcome — reads docs/adr/ (counted, never the README index),
    docs/nfdr.md, docs/architecture_open_issues.md and docs/trail/architecture/.

    An unchanged HEAD decides the message rather than annotating one, as it does in every
    sibling that reads a product: a run that committed nothing leaves the previous run's
    files on disk, and this reporter's record count and cycle number are both read off them.
    So the product is not read at all in that case.

    An unreadable HEAD is a third case: it is not evidence of an idle run, so it claims
    neither outcome and the body is the product read.

    A companion left unanswered (`companion_state`) gets a different unchanged-HEAD message
    than a stall — the run had nothing to fold, not nothing to say. The artifact name passed
    is `"Architecture"`, matching `architecture_open_issues.md`'s own prefix — not `"NFDR"`,
    which names neither file the shared companion answers for (this section's own opening
    note).
    """
    if ctx.head_before is not None and ctx.head_before == ctx.head_after:
        docs_dir = os.path.join(ctx.artifact_path, "docs") if ctx.artifact_path else None
        return Outcome(_committed_nothing_for(ctx.label, "Architecture", docs_dir))
    return Outcome(_architecture_body(ctx.label, ctx.artifact_path), None)


# --- companion-self-answer: reads the run's own report file, never the companion ---
#
# Authored against `skills/companion/.claude/skills/companion-self-answer/SKILL.md` § Step 5 and
# `core/templates/self_answer_report_template.md`, not cloned from a sibling — the shape here
# differs from every reporter above it in two load-bearing ways:
#   - The artifact is a REPORT the skill writes about its own run, never a product document
#     with a Status/Version line, so there is no unchanged-HEAD "committed nothing" branch —
#     that pattern belongs to a document contract this artifact does not carry. This reporter
#     follows the two rules this file already states about itself and no third: read the
#     product, never the agent's state (module docstring; :212), and let a parser bug cost
#     specificity, never the message, via a deliberately wide `except Exception` (:214-218).
#   - The tally is one field scan, not a heading walk: every `## Items worked` / `## Left for
#     the owner` entry carries `**Verdict:**` from the prompt's six literals
#     (`<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` § The six verdicts), so a single regex
#     over the whole file IS the split — no per-section counting. `## Unnamed verdict`
#     entries carry `**Would-be verdict:**` instead, by construction, and never inflate it.
#     The headings are read all the same, twice over: `_SELF_ANSWER_REQUIRED_HEADINGS` is what
#     tells a report from any other file that happens to sit at that path, and
#     `## Launchers owed` is read BY heading because its bullets share `- **X** — Y` with
#     `## Companions opened`'s and a section-blind scan would swallow one into the other.
#
# The launcher list is the one element of the seed's minimum that cannot be derived: the owner
# reads this message to learn what to run next, and the document a round is owed on is not a
# command. SKILL.md § Step 6 already derives each launcher (its folder, else the fixed
# prompt-literal grep, else the honest absence) and writes the list into the report — so this
# reads it there, and falls back to naming the documents when the section is absent or empty,
# which costs specificity and never the message.
#
# The search walks the same three document homes the rest of this reporter file's product
# readers know — system/*/, system/projects/*/, each project's `<Product path>/docs/`, or the
# target's own docs/ when it carries no project cards — because it is handed a root (the
# launcher's `--artifact-path`: the product path, or the instance root for a document in
# `system/projects/<project>/`, since `core/launchers/companion-self-answer/launcher.sh` resolves
# the document + companion from `<project> <document>` itself), not a target it searched —
# plus one `trail/<doc>/` inside each, the home `kensaiapp_structure.md` § *A trail is not the
# document's sibling* gives a run's
# report. For `self_answer-<N>.md` report files it takes the highest N across every home: one run
# answers one companion, so its reports accumulate in one directory in the ordinary case.


_SELF_ANSWER_VERDICTS = (
    "answered", "confirmed", "confirmed with addition", "overridden",
    "raised upstream", "left for the owner",
)

# The headings `self_answer_report_template.md` says every report carries, whatever its run
# found — the two optional ones (`## Unnamed verdict`, `## Launchers owed`) are deliberately
# not here, because the template's own body says a run that met neither omits them.
#
# This is the shape check, and it is what keeps the "already answered" branch honest: a tally
# of zero over an empty, truncated or half-written file is indistinguishable from a tally of
# zero over a companion that really was already answered, and only one of those is a finished
# document. Without it the ✅ is a claim about a file nobody checked.
_SELF_ANSWER_REQUIRED_HEADINGS = (
    "## Header", "## Items worked", "## Left for the owner", "## Skipped",
    "## Companions opened",
)


# opened | appended | updated are three different things for the owner to walk into (the
# template's own banner, and the owner's ruling behind the action word, 2026-08-29): a document
# that newly reads open, one that gained a question, one that had a question rewritten. A
# bullet with no action word (written before `72f690f9`) gets none of these phrases — inventing
# one would claim an action the report never recorded.
_SELF_ANSWER_ACTION_PHRASES = {
    "opened": "newly opened",
    "appended": "gained a question",
    "updated": "had a question rewritten",
}


def _self_answer_companion_clause(path: str, action: str | None, document: str) -> str:
    """One `## Companions opened` entry, worded for the message: `<document> (<path>) — <what
    happened>` when the action is one of the three known words, `<document> (<path>)` with no
    phrase at all when it is not — never a default phrase for an entry the report never named
    an action for."""
    phrase = _SELF_ANSWER_ACTION_PHRASES.get(action)
    return f"{document} ({path}) — {phrase}" if phrase else f"{document} ({path})"


def _self_answer_raised_clause(n: int, document: str, report_path: str) -> str:
    """The one line a raise gets. Its own function because it is composed from more than one
    branch: a run can judge the document it was answering owed a change while working no item
    at all — the raise is read off the document, not off an item (the template's own note:
    "the run judged the document it was answering owed a change no item raised") — and a run
    whose only product is a new question is exactly the one nobody was watching."""
    return (f"⚠️ this run raised {n} change{'' if n == 1 else 's'} on {document} "
            f"— see {report_path}.")


def _self_answer_pending_phrase(counts):
    """"2 confirmed, 1 overridden" — only the non-zero terms, in the prompt's own order,
    among the five DECIDED verdicts. "left for the owner" never appears here: it is reported
    on its own (the count the owner most needs to see without parsing a phrase for it), the
    same split `_prd_body` makes between a pending phrase and its own named counts."""
    parts = []
    for verdict in _SELF_ANSWER_VERDICTS:
        if verdict == "left for the owner":
            continue
        n = counts.get(verdict, 0)
        if n:
            parts.append(f"{n} {verdict}")
    return ", ".join(parts)


def _self_answer_product_path(project_md_path: str, root: str) -> str | None:
    """The `**Product path:**` line off a project card, resolved exactly as every `product-*`
    launcher's own bash resolves that line — `core/launchers/companion-self-answer/launcher.sh`
    among them — relative under `root`, absolute or `~/` verbatim. Its own function, not a reuse
    of a sibling's reader: every other reporter above is handed its product path directly as
    `ctx.artifact_path`; this one may be handed a wider target and has to find a project's
    product path itself, the way a launcher's own bash does.
    """
    try:
        with open(project_md_path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    m = re.search(r"^\*\*Product path:\*\*\s*(\S.*)$", text, re.MULTILINE)
    if not m:
        return None
    raw = m.group(1).split("<!--")[0].strip()
    if not raw:
        return None
    if raw.startswith("~/"):
        return os.path.join(os.path.expanduser("~"), raw[2:])
    if raw.startswith("/"):
        return raw
    return os.path.join(root, raw)


def self_answer_reports_present(target_path: str,
                                document_stem: str | None = None) -> tuple[str, ...]:
    """Every self-answer report on disk for `target_path`, optionally narrowed to one
    document's trail.

    Split out of `find_self_answer_report` so the watcher's BEFORE reading and the locator's
    AFTER search are the same notion of which files count. Two scans with two definitions is
    how a guard ends up excluding a file the search never had, or missing one it did.

    Walks the same three document homes every reporter above assumes — system/*/,
    system/projects/*/, each project's `<Product path>/docs/`, or the target's own docs/ when
    it carries no project cards — and then one `trail/<doc>/` inside each. Both segments are
    literal `*`s at a **fixed depth**, never a recursive walk: depth is what tells a document
    home from a tree that happens to contain one.
    """
    leaf = os.path.join("trail", "*", "self_answer-*.md")
    candidates = []
    candidates += glob.glob(os.path.join(target_path, "system", "*", leaf))
    candidates += glob.glob(
        os.path.join(target_path, "system", "projects", "*", leaf))
    project_cards = glob.glob(
        os.path.join(target_path, "system", "projects", "*", "project.md"))
    if project_cards:
        for card in project_cards:
            product = _self_answer_product_path(card, target_path)
            if product:
                candidates += glob.glob(os.path.join(product, "docs", leaf))
    else:
        candidates += glob.glob(os.path.join(target_path, "docs", leaf))

    if document_stem is not None:
        wanted = document_stem.strip().lower()
        candidates = [path for path in candidates
                      if os.path.basename(os.path.dirname(path)).lower() == wanted]
    return tuple(candidates)


def _self_answer_reports_after(target_path: str, document_stem: str | None,
                               reports_before: tuple[str, ...] | None) -> list[str]:
    """The reports `self_answer_reports_present` finds, less any already on disk at the reading.

    The one before-filter both locators share, so the singular and the plural locator can never
    disagree about which report predates the launch.
    """
    candidates = list(self_answer_reports_present(target_path, document_stem))

    # A report that was already on disk when the watch began cannot be this run's, so it is
    # dropped before any report is chosen. Without this, a run that wrote nothing reads
    # back its predecessor's verdict and the reporter states it as today's: measured on
    # a live product 2026-09-04, where `docs/DESIGN.md` (v5, three unanswered items) was reported
    # `(v4, Settled) — already answered, nothing left to work` off a report written three days
    # earlier. The rule is `watch_agent.completion_marker_seen`'s, applied to the report
    # instead of the done-marker; the cost is its cost too — a report that started out stale
    # stays inert for this watch, which is what makes the guard sound rather than clever.
    #
    # `None` is a caller that took no reading: today's behaviour, unchanged. An empty tuple is
    # a reading that found nothing, and excludes nothing.
    if reports_before is not None:
        before = {os.path.realpath(p) for p in reports_before}
        candidates = [p for p in candidates if os.path.realpath(p) not in before]
    return candidates


def find_self_answer_report(target_path: str, document_stem: str | None = None,
                            reports_before: tuple[str, ...] | None = None) -> str | None:
    """The highest-numbered `self_answer-<N>.md` in `target_path`'s trails, or None.

    `document_stem` narrows the sweep to ONE document's trail — `trail/<stem>/`, matched
    case-insensitively on the directory's own name. Without it this function answers "the
    highest-numbered report anywhere under this target", which is the wrong question for any
    caller that knows which document just ran: the number is per-trail, so a product whose FDR
    is on its second report and whose architecture is on its first hands back the FDR's.
    Measured on a live product, 2026-09-01 — two `companion-self-answer` runs on the architecture
    companion each read back `docs/trail/fdr/self_answer-2.md`, and the verdict they had
    actually written, an item left for the owner, never reached the caller. The parameter is
    optional because the watcher's own reporter has only the launcher's `--artifact-path` to
    go on; a caller that knows the document passes it and gets the report it just made.

    Walks the same three document homes every reporter above assumes — system/*/,
    system/projects/*/, each project's `<Product path>/docs/`, or the target's own docs/ when it
    carries no project cards — and then one `trail/<doc>/` inside each, because
    `kensaiapp_structure.md` § *A trail is not the document's sibling* files a run's report in
    the trail of the document it answered rather than beside that document. Both segments are
    literal `*`s at a **fixed depth**, never a recursive walk, for the same reason the skill's
    own Step 1 stays non-recursive
    (`skills/interactive/.claude/skills/companion-answer/SKILL.md` § *Non-recursive is the whole
    point* — the sibling the homes were taken from; the self-answer skill carries
    no such section, because it no longer searches at all): depth is what
    tells a document home from a tree that happens to contain one. `target_path` is the
    launcher's `--artifact-path`: `core/launchers/companion-self-answer/launcher.sh` resolves
    `<project> <document>` in the project's two homes itself and hands over the root for the one
    it found — the product path for a document in its docs/, which lands in the third branch, and
    the instance root for one in `system/projects/<project>/`, which lands in the second.
    """
    candidates = _self_answer_reports_after(target_path, document_stem, reports_before)

    best_path, best_n = None, -1
    for path in candidates:
        m = re.fullmatch(r"self_answer-(\d+)\.md", os.path.basename(path))
        if m and int(m.group(1)) > best_n:
            best_n, best_path = int(m.group(1)), path
    return best_path


def new_self_answer_reports(target_path: str, document_stem: str | None = None,
                            reports_before: tuple[str, ...] | None = None) -> tuple[str, ...]:
    """Every `self_answer-<N>.md` this launch produced, ascending by report number.

    The plural of `find_self_answer_report`: the same document homes, the same case-insensitive
    `document_stem` narrowing and the same `reports_before` filter (`None` excludes nothing).
    A companion answered seat by seat leaves one report per run, and the round is read whole.
    A name that is not exactly `self_answer-<N>.md` is dropped, and the order is numeric — 2
    before 10 — with discovery order kept among equal numbers.
    """
    numbered = []
    for path in _self_answer_reports_after(target_path, document_stem, reports_before):
        m = re.fullmatch(r"self_answer-(\d+)\.md", os.path.basename(path))
        if m:
            numbered.append((int(m.group(1)), path))
    numbered.sort(key=lambda pair: pair[0])
    return tuple(path for _, path in numbered)


def _self_answer_missing_headings(text: str):
    """The required headings this text does not carry, in the template's own order."""
    return [h for h in _SELF_ANSWER_REQUIRED_HEADINGS
            if not re.search(rf"^{re.escape(h)}\s*$", text, re.MULTILINE)]


def _self_answer_section(text: str, heading: str) -> str:
    """The body under one `## ` heading, up to the next one — an empty string when the heading
    is not there. Read by heading rather than by a scan over the whole file because
    `## Launchers owed`'s bullets and `## Companions opened`'s share the `- **X** — Y` shape,
    and a section-blind regex for either would collect the other's entries as its own."""
    m = re.search(rf"^{re.escape(heading)}\s*$(.*?)(?=^## |\Z)", text,
                  re.MULTILINE | re.DOTALL)
    return m.group(1) if m else ""


def _self_answer_launchers_owed(text: str):
    """`(document, how to run it)` per bullet of `## Launchers owed` — the list SKILL.md
    § Step 6 derives and writes into the report ("The list goes in the report as well as to
    the session"). The second half is taken verbatim, because it is already what the owner has
    to run — a launcher command, or Step 6's honest absence for a producing skill that has no
    launcher at all.

    Its wrapping backticks come off ONLY when they wrap the whole value, because only then are
    they wrapping. Step 6 also writes a command with a note outside it — ``- **fdr.md** —
    `…/launcher.sh <project>` (run from the instance root)`` — where a strip of one character
    per end takes the opening backtick, leaves the one that closed the command, and hands the
    owner an unbalanced line. Seen on the first live cycle, 2026-08-30. Stripping every
    backtick instead would fix that and flatten
    `run `product-architecture` from a `cto` session`, whose inner pair is doing real work — so
    the test is whether the value IS a command, not
    whether it contains one."""
    section = _self_answer_section(text, "## Launchers owed")
    # An entry wraps: Step 6's honest-absence sentence names a skill and a posture and does not
    # fit a line, and the writer wraps it like every other line in these files. Joining a
    # continuation onto its bullet before matching is what keeps the tail of that sentence in
    # the message rather than cutting it at the wrap.
    section = re.sub(r"\n[ \t]+(?=\S)", " ", section)
    owed = []
    for m in re.finditer(r"^-\s+\*\*(.+?)\*\*\s+—\s+(.+?)\s*$", section, re.MULTILINE):
        document, how = m.group(1).strip(), m.group(2).strip()
        if len(how) > 1 and how.startswith("`") and how.endswith("`"):
            how = how[1:-1].strip()
        if document and how:
            owed.append((document, how))
    return owed


def _self_answer_raised(text: str) -> int:
    """Count of `### ` entries under `## Raised on this document` — a change the run judged
    the document it was answering owed and appended to its own companion (optional; the
    section is present only when a run raised something). Read by heading, the same reason
    `## Launchers owed` is (`_self_answer_launchers_owed`): `### ` recurs across `## Items
    worked` and `## Left for the owner`, and a heading-blind count would tally their entries
    as raises too. The section's absence — the normal case — reads as zero, exactly as its
    absent heading finds no section to count."""
    section = _self_answer_section(text, "## Raised on this document")
    return len(re.findall(r"^### ", section, re.MULTILINE))


def _parse_self_answer_report(text: str):
    """Every `**Verdict:**` line in the file, tallied by literal — section-blind on purpose:
    `## Items worked` and `## Left for the owner` both carry the field precisely so this one
    scan sees them all, and only the six known literals are counted, so a stray or malformed
    value can never masquerade as a seventh verdict."""
    counts = {v: 0 for v in _SELF_ANSWER_VERDICTS}
    for m in re.finditer(r"^-\s+\*\*Verdict:\*\*\s*(.+?)\s*$", text, re.MULTILINE):
        verdict = m.group(1).strip()
        if verdict in counts:
            counts[verdict] += 1
    document = None
    m = re.search(r"^-\s+\*\*Document:\*\*\s*(.+?)\s*$", text, re.MULTILINE)
    if m:
        document = m.group(1).strip()
    # `[^*]+` for both the path and the action word — not `\S.*?` — is what keeps this from
    # regressing: a non-greedy `.*?` still backtracks over a `**` that appears later in the
    # line (the action word's own, added at `72f690f9`), and captures it as part of the path.
    # Excluding `*` from the class makes that backtrack impossible rather than merely unlikely.
    # The action group is optional so a bullet written before `72f690f9` — path and document,
    # no action word — still parses; its action comes back `None` rather than invented.
    companions_opened = [
        (path.strip(), action.strip() or None, document_.strip())
        for path, action, document_ in re.findall(
            r"^-\s+\*\*([^*]+)\*\*\s+—\s+(?:\*\*([^*]+)\*\*\s+—\s+)?companion to `([^`]+)`",
            text, re.MULTILINE)]
    unnamed = len(re.findall(r"^-\s+\*\*Would-be verdict:\*\*", text, re.MULTILINE))
    return {"counts": counts, "document": document,
            "companions_opened": companions_opened, "unnamed": unnamed,
            "launchers_owed": _self_answer_launchers_owed(text),
            "raised": _self_answer_raised(text)}


def _companion_self_answer_body(label: str, target_path: str | None,
                                document_stem: str = "",
                                reports_before: tuple[str, ...] | None = None) -> str:
    """What the run produced, read from its own report file. Never what state the agent is
    in, and never a third rule invented beyond the two this file already states about itself
    (see the section banner above) — no unchanged-HEAD branch: this artifact carries no
    Status/Version line for one to protect.
    """
    plain = f"{label}: run ended."
    if not target_path:
        return plain
    try:
        report_path = find_self_answer_report(target_path, document_stem or None,
                                              reports_before)
        if report_path is None:
            where = (f"{target_path}'s trail/{document_stem.lower()}/" if document_stem
                     else str(target_path))
            return f"⚠️ {label}: no self-answer report found under {where} — the run wrote none."
        try:
            with open(report_path, encoding="utf-8") as fh:
                text = fh.read()
        except (OSError, UnicodeDecodeError):
            # The report is there and this run cannot read it, which is a fact about the run
            # and belongs in the message. The bare `plain` below is for a parser BUG, and it
            # reads identically to the `generic` fallback this reporter exists to replace —
            # so a file that exists and did not open must never arrive as one. Narrow, and
            # named, exactly as `_prd_body` names its own unreadable-product case.
            return (f"⚠️ {label}: the self-answer report at {report_path} could not be read "
                     f"— what the run did is in that file.")
        missing = _self_answer_missing_headings(text)
        if missing:
            return (f"⚠️ {label}: the self-answer report at {report_path} could not be read "
                     f"— it is not in the template's shape (no {', '.join(missing)}). "
                     f"Read it rather than this message.")
        p = _parse_self_answer_report(text)
        counts = p["counts"]
        left = counts["left for the owner"]
        worked = sum(n for v, n in counts.items() if v != "left for the owner") + p["unnamed"]
        total = worked + left
        document = p["document"] or "the companion"

        if total == 0:
            if p["raised"]:
                # Never ✅ here. The item this run appended to the companion is unanswered by
                # construction — its slot stays at its placeholder — so a companion that just
                # gained a raise is not "already answered", and the all-clear would hide the
                # one thing this run produced from the person who is not watching it.
                return (f"📋 {label}: {document} — no items left to work.\n"
                         + _self_answer_raised_clause(p["raised"], document, report_path))
            return (f"✅ {label}: {document} — already answered, nothing left to work "
                     f"({report_path}).")

        body = f"📋 {label}: {document} — {worked} of {total} items answered"
        split = _self_answer_pending_phrase(counts)
        if split:
            body += f" ({split})"
        body += f"; {left} left for you." if left else "; nothing left for you."

        launchers = p["launchers_owed"]
        if launchers:
            body += "\nOwed a run:"
            for doc, how in launchers:
                body += f"\n- {doc} — {how}"
        else:
            # No `## Launchers owed` section, or an empty one. The documents are still worth
            # saying — the owner learns which rounds are owed, and looks the launcher up.
            owed = []
            if worked:
                owed.append(document)
            for _path, _action, doc in p["companions_opened"]:
                if doc not in owed:
                    owed.append(doc)
            if owed:
                body += f"\nOwed a run: {', '.join(owed)}."
        if p["raised"]:
            body += "\n" + _self_answer_raised_clause(p["raised"], document, report_path)
        if p["companions_opened"]:
            touched = ", ".join(_self_answer_companion_clause(path, action, doc)
                                 for path, action, doc in p["companions_opened"])
            body += f"\nCompanion touched: {touched}."
        if p["unnamed"]:
            n = p["unnamed"]
            body += (f"\n⚠️ {n} verdict{'' if n == 1 else 's'} the prompt could not name — "
                      f"see {report_path}.")
        return body
    except Exception:
        return plain


def companion_self_answer(ctx: OutcomeContext) -> Outcome:
    """The companion-self-answer outcome — reads the run's own report file
    (`self_answer-<N>.md`, highest N in `ctx.document_stem`'s own trail under
    `ctx.artifact_path`), never the companion it answered and never the document. SKILL.md
    § Step 5 writes everything this message needs into that file; re-deriving any of it from
    the companion would be reading the run's intentions instead of what it did.

    Without `ctx.document_stem` the sweep is target-wide and `N` is per-trail, so the message
    describes whichever document happens to be furthest along. Measured on a live product,
    2026-09-01: two runs on the architecture companion both announced
    `docs/fdr.md — no items left to work`, which was another document's report, and the item
    they had each left for the owner went unmentioned.

    `ctx.reports_before` closes the same defect one axis over — the wrong RUN rather than the
    wrong document. A report on disk before the watch began is excluded, so a run that wrote
    nothing says so instead of inheriting its predecessor's verdict. Measured on a live product,
    2026-09-04: `docs/DESIGN.md`, at v5 with three unanswered items, was reported
    `(v4, Settled) — already answered, nothing left to work` from a report three days old.
    """
    return Outcome(_companion_self_answer_body(ctx.label, ctx.artifact_path,
                                               ctx.document_stem,
                                               ctx.reports_before), None)


# --- shukuba-refine: the next moves the refine run leaves owed ----------------------
#
# A refine run's outcome is its report, `journey/nemawashi/[unpicked/]<seed>/<key>_report.md`
# under the project, and what the owner needs off it is the `## Next moves` table the report
# opens with (`<CORE>/../skills/pm/.claude/skills/shukuba-refine/prompts/rich.md` § Name what comes next). The report to read is
# the one THIS run committed — a path the watch's HEAD range added or changed — never the newest
# on disk: earlier units' reports sit beside it in the same seed folder, and a run that stopped
# before Step 6 would otherwise be announced with a predecessor's list.

_REFINE_REPORT_RE = re.compile(
    r"^journey/nemawashi/(?:unpicked/)?[^/]+/(?P<key>[^/]+)_report\.md$")

# A row that waits on earlier ones names them in its After cell, by row number — `1`, or `1, 2` —
# and `—` where it waits on none (`<CORE>/../skills/pm/.claude/skills/shukuba-refine/prompts/rich.md` § Name what comes next).
# Every launcher backgrounds its run and returns at once, so the message says the earlier move
# must have LANDED: a bare "(after 1)" read as "once 1 is launched", and a chain started beside a
# still-running close opened a change for the station being closed (2026-09-18). The columns are
# found by their header names, because `build-idea` reads the same table and a positional read
# here would take a reordered table's From prose for a wait.
_REFINE_LEADING_COLUMNS = ("#", "move", "whose", "command")


def _git_changed_paths(project_path: str, head_before: str,
                       head_after: str) -> tuple[str, ...] | None:
    """The paths under `project_path` the range added or modified, relative to it, or None
    when git cannot say — not a repo, an unknown revision, no git."""
    try:
        proc = subprocess.run(
            ["git", "-C", project_path, "diff", "--name-only", "--relative", "-M",
             "--diff-filter=AM", head_before, head_after],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return tuple(line for line in proc.stdout.splitlines() if line)


def _table_rows(section: str) -> list[list[str]]:
    """The body rows of the first Markdown table in `section`, each a list of cell texts —
    the header row and its `|---|` separator dropped."""
    rows = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if rows:
                break
            continue
        rows.append([cell.strip() for cell in stripped.strip("|").split("|")])
    body = rows[1:]
    if body and all(re.fullmatch(r":?-+:?", cell) for cell in body[0]):
        body = body[1:]
    return body


def _table_header(section: str) -> list[str]:
    """The header row of the first Markdown table in `section` as lowercase cell texts, or `[]`
    when the section holds no table — the row `_table_rows` drops."""
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("|"):
            return [cell.strip().lower() for cell in stripped.strip("|").split("|")]
    return []


def _plain_cell(cell: str) -> str:
    """A table cell as a phone shows it: the code-span backticks dropped."""
    return cell.replace("`", "")


def _next_moves_lines(section: str) -> list[str]:
    """A `## Next moves` section as the message's `Next:` lines — one move per row with its seat,
    a wait line where the row's After names earlier rows, and its command; or the one-line reason
    of a "None —" section. Shared by every report that opens with the refine run's six-column table
    (`<CORE>/../skills/pm/.claude/skills/shukuba-refine/prompts/rich.md` § Name what comes next)."""
    lines: list[str] = []
    rows = _table_rows(section)
    if rows:
        header = _table_header(section)
        # A column the header names is read where the header puts it; one it does not name — the
        # four leading ones of a table whose header is unreadable — stays where it has always been.
        position = {name: header.index(name) if name in header else index
                    for index, name in enumerate(_REFINE_LEADING_COLUMNS)}
        position["after"] = header.index("after") if "after" in header else None

        def cell(row: list[str], name: str) -> str:
            index = position[name]
            return row[index] if index is not None and index < len(row) else ""

        lines.append("Next:")
        for row in rows:
            lines.append(f"{_plain_cell(cell(row, '#'))}. {_plain_cell(cell(row, 'move'))} — "
                         f"{_plain_cell(cell(row, 'whose'))}")
            waits_on = re.findall(r"\d+", cell(row, "after"))
            if waits_on:
                verb = "has" if len(waits_on) == 1 else "have"
                lines.append(f"   only once {', '.join(waits_on)} {verb} landed, "
                             f"not merely launched")
            lines.append(f"   {_plain_cell(cell(row, 'command'))}")
    else:
        reason = next((ln.strip() for ln in section.splitlines()
                       if ln.strip() and not ln.strip().startswith(("<!--", "|"))), "")
        lines.append(f"Next: {_plain_cell(reason)}")
    return lines


def _refine_body(label: str, project_path: str | None, head_before: str | None,
                 head_after: str | None, cwd: str, changed_paths) -> str:
    plain = f"{label}: run ended."
    if not project_path or head_before is None or head_after is None:
        return plain
    if head_before == head_after:
        return (f"⚠️ {label}: the run committed nothing — it stopped before writing its "
                f"report. Read its session.")
    changed = changed_paths(project_path, head_before, head_after)
    if changed is None:
        return plain
    reports = sorted(p for p in changed if _REFINE_REPORT_RE.match(p))
    if not reports:
        return (f"⚠️ {label}: the run committed, but no refine report among its commits — "
                f"it stopped before Step 6. Read its session.")
    rel = reports[-1]
    key = _REFINE_REPORT_RE.match(rel).group("key")
    path = os.path.join(project_path, rel)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()

    section = _self_answer_section(text, "## Next moves")
    if not section.strip():
        return f"⚠️ {label}: {key} reviewed, but its report names no next moves — read {path}."

    moves = len(_table_rows(_self_answer_section(text, "## Moves")))
    head = f"📋 {label}: {key} reviewed — {moves} move" + ("" if moves == 1 else "s") + " made"
    recs_path = os.path.join(os.path.dirname(path), f"{key}_recommendations.md")
    if os.path.isfile(recs_path):
        with open(recs_path, encoding="utf-8") as fh:
            recs = len(re.findall(r"^###\s+\d+\.", fh.read(), re.MULTILINE))
        head += (f", {recs} recommendation" + ("" if recs == 1 else "s")
                 + " to the Principal PM." if recs else ", nothing recommended.")
    else:
        head += "."

    lines = [head, *_next_moves_lines(section)]
    shown = os.path.relpath(path, cwd) if cwd else path
    lines.append(f"Report: {shown}")
    return "\n".join(lines)


def _shukuba_refine_reporter(changed_paths):
    """Build the shukuba-refine reporter over `changed_paths` — git in production, a stub in
    the tests. Best-effort like its siblings: a parser bug costs specificity, never the
    message."""
    def reporter(ctx: OutcomeContext) -> Outcome:
        try:
            return Outcome(_refine_body(ctx.label, ctx.artifact_path, ctx.head_before,
                                        ctx.head_after, ctx.cwd, changed_paths))
        except Exception:
            return Outcome(f"{ctx.label}: run ended.")
    return reporter


shukuba_refine = _shukuba_refine_reporter(_git_changed_paths)
sdd_document = _sdd_document_reporter(read_sdd, _committed_nothing_for)


REGISTRY = {
    "generic": generic,
    "prd": prd,
    "fix-author": fix_author,
    "apply-packet": apply_packet,
    "srs": srs,
    "uxd": uxd,
    "design": design,
    "content": content,
    "writing-bar": writing_bar,
    "experience-visual": experience_visual,
    "experience-voice": experience_voice,
    "agari": agari,
    "sdd-document": sdd_document,
    "fdr": fdr,
    "architecture": architecture,
    "companion-self-answer": companion_self_answer,
    "shukuba-refine": shukuba_refine,
}


def get_reporter(name: str):
    """The reporter for `name`, or `generic` for an unknown name (never raises)."""
    return REGISTRY.get(name, generic)
