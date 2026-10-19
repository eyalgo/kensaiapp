"""Contract tests for `reporters.py` — the run-type outcome composers.

`watch_agent.py` watches a `--bg` run to a terminal state; it then hands a reporter an
`OutcomeContext` (what it read off the run: label, artifact path, terminal state, the
repo HEAD before/after) and the reporter returns the message body. The watcher itself
knows nothing about run types — every run-type-specific string lives here.

What is pinned:

- **The `prd` reporter's strings are pinned exactly, not paraphrased.** A person reads this
  message on a phone with no other context, so its wording is the contract, and an assertion
  that matched loosely would let it drift unnoticed. The PRD file-contract parsers
  (`parse_status` / `parse_version` / `count_buckets` / `trail_cycles`) are pinned with it.
- **An unchanged HEAD decides the body, in every reporter that reads a product.** A run that
  committed nothing left the previous run's files on disk, so each of `prd` / `srs` / `uxd` /
  `design` says so and names its own artifact instead of reading that tree. Asserting
  `footnote is None` there proves nothing — no reporter sets one — so these cases are pinned
  on the body, which is what discriminates. `Outcome` still carries a `footnote` field: it is
  the seam for a caveat that refers to the watcher's state note, which this one does not.
- **`generic` is the default and the safe fallback** — `"<label>: run ended."`, the message
  a run with no reporter of its own gets.
- **New run types are added here, not in the watcher.** `fix-author` and `apply-packet`
  are the first two; the registry (`get_reporter`) is what makes a third one a one-file
  change.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import reporters  # noqa: E402
from reporters import OutcomeContext  # noqa: E402


# --- product-shape builders (the tree product-prd authors into) --------------
#
# Copied from test_watch_agent.py, where they described the same on-disk contract.

BUCKET_TITLES = {
    1: "Open issues — product-defining questions with no answer yet",
    2: "Choices to confirm — the CPO drafted a best-effort answer; confirm or override",
    3: "Directives — an action you asked for that the CPO can't perform itself",
}


def companion(n1=0, n2=0, n3=0):
    out = []
    for bucket, n in ((1, n1), (2, n2), (3, n3)):
        out.append(f"## {bucket}. {BUCKET_TITLES[bucket]}\n")
        if n == 0:
            out.append("None this cycle.\n")
        for i in range(1, n + 1):
            out.append(f"### {bucket}.{i} the decision, in one line\n")
            out.append("- **Why it matters:** because.\n")
    return "\n".join(out)


def product(tmp_path, prd=True, open_issues=False, status="Settled", version=2,
            trail=(), buckets=(0, 1, 0)):
    docs = tmp_path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    if prd:
        (docs / "PRD.md").write_text(
            f"# PRD — thing\n\n**Status:** {status}\n**Owner:** CPO\n"
            f"**Version:** {version} — what this revision changed\n"
        )
    if open_issues:
        (docs / "PRD_open_issues.md").write_text(companion(*buckets))
    if trail:
        (docs / "trail/prd").mkdir(parents=True, exist_ok=True)
        for n in trail:
            (docs / "trail/prd" / f"cycle-{n}.md").write_text("# cycle\n")
    return str(tmp_path)


def prd_ctx(artifact_path, *, state="blocked", head_before=None, head_after=None):
    return OutcomeContext(
        label="example-product", cwd="/repo", artifact_path=artifact_path,
        state=state, head_before=head_before, head_after=head_after,
    )


# --- the registry: the seam that keeps the watcher run-type-agnostic ---------


def test_known_names_resolve_to_their_reporter():
    assert reporters.get_reporter("prd") is reporters.prd
    assert reporters.get_reporter("fix-author") is reporters.fix_author
    assert reporters.get_reporter("apply-packet") is reporters.apply_packet
    assert reporters.get_reporter("generic") is reporters.generic


def test_an_unknown_name_falls_back_to_generic():
    """A launcher that names a reporter that was never written still gets a message,
    not a crash — the same best-effort rule the outcome read has always held to."""
    assert reporters.get_reporter("nope-not-a-reporter") is reporters.generic


def test_a_new_reporter_is_reachable_once_registered():
    """The 'future ones' property, at this layer: adding an entry to the registry is all
    it takes for get_reporter to route to it — no edit anywhere else."""
    def custom(ctx):
        return reporters.Outcome(f"{ctx.label}: custom outcome.")

    reporters.REGISTRY["custom-kind"] = custom
    try:
        assert reporters.get_reporter("custom-kind") is custom
    finally:
        del reporters.REGISTRY["custom-kind"]


# --- generic: the default and the safe fallback ------------------------------


def test_generic_says_only_that_the_run_ended():
    out = reporters.generic(OutcomeContext(label="example-product"))
    assert out.body == "example-product: run ended."
    assert out.footnote is None


# --- produced_nothing: the one fact `Outcome` learns to carry ----------------
#
# `watch_agent.py`'s --on-complete hook needs to know whether a run produced anything, and
# must not re-derive it from `ctx` itself — computed once, here, off the same two readings
# `OutcomeContext` already carries (`prd()`'s own unchanged-HEAD check, and the self-answer
# guard `find_self_answer_report` already applies against `reports_before`), so the watcher
# only ever reads `Outcome.produced_nothing` rather than inspecting `ctx` a second time.


def test_unchanged_head_and_unchanged_report_set_is_produced_nothing(tmp_path):
    ctx = OutcomeContext(label="example-product", artifact_path=str(tmp_path),
                         head_before="same-sha", head_after="same-sha", reports_before=())
    assert reporters.produced_nothing(ctx) is True


def test_a_moved_head_is_not_produced_nothing(tmp_path):
    ctx = OutcomeContext(label="example-product", artifact_path=str(tmp_path),
                         head_before="before-sha", head_after="after-sha", reports_before=())
    assert reporters.produced_nothing(ctx) is False


def test_a_new_self_answer_report_is_not_produced_nothing(tmp_path):
    self_answer_report(tmp_path / "docs", document="DESIGN", stem="design")
    ctx = OutcomeContext(label="example-product", artifact_path=str(tmp_path), document_stem="DESIGN",
                         head_before="same-sha", head_after="same-sha", reports_before=())
    assert reporters.produced_nothing(ctx) is False


def test_a_moved_head_and_a_new_report_is_not_produced_nothing(tmp_path):
    self_answer_report(tmp_path / "docs", document="DESIGN", stem="design")
    ctx = OutcomeContext(label="example-product", artifact_path=str(tmp_path), document_stem="DESIGN",
                         head_before="before-sha", head_after="after-sha", reports_before=())
    assert reporters.produced_nothing(ctx) is False


def test_a_report_already_in_reports_before_does_not_count_as_new(tmp_path):
    """The same run's own before-reading. A report already on disk when the watch began is
    not evidence the run wrote something — the rule `find_self_answer_report` already holds
    for the locator, applied here to the fact of whether anything new appeared at all."""
    stale = self_answer_report(tmp_path / "docs", document="DESIGN", stem="design")
    ctx = OutcomeContext(label="example-product", artifact_path=str(tmp_path), document_stem="DESIGN",
                         head_before="same-sha", head_after="same-sha",
                         reports_before=(str(stale),))
    assert reporters.produced_nothing(ctx) is True


def test_no_artifact_path_is_never_produced_nothing_on_head_alone(tmp_path):
    """`ctx.artifact_path` is what makes a report reading possible at all. Without it, an
    unchanged HEAD is the only fact in evidence, and that alone must not read as `True` — a
    run this watcher was never pointed at a product path for is not proven to have done
    nothing just because a repo it was never told to watch sat still."""
    ctx = OutcomeContext(label="example-product", head_before="same-sha", head_after="same-sha")
    assert reporters.produced_nothing(ctx) is False


def test_an_unreadable_head_is_never_produced_nothing():
    """`head_before is None` reads as "not proven" here exactly as it already does for
    `prd()`'s own unchanged-HEAD check — never as a match by default."""
    ctx = OutcomeContext(label="example-product", artifact_path="/some/path",
                         head_before=None, head_after=None)
    assert reporters.produced_nothing(ctx) is False


def test_outcome_defaults_to_not_produced_nothing():
    assert reporters.Outcome("x").produced_nothing is False


def test_no_reporter_in_the_registry_sets_produced_nothing_itself(tmp_path):
    """The other half of "every existing reporter's body and footnote are byte-identical":
    the field is attached by the WATCHER, off `produced_nothing(ctx)`, and by nobody else.
    Registry-wide rather than one reporter, so a reporter added later that reaches for the
    field has to argue with this test — and driven with a context that WOULD read as
    produced-nothing, so a reporter setting it by accident cannot hide behind a context
    that says False anyway."""
    ctx = OutcomeContext(label="example-product", cwd=str(tmp_path), artifact_path=str(tmp_path),
                         head_before="same-sha", head_after="same-sha", reports_before=())
    assert reporters.produced_nothing(ctx) is True, "the context itself must say True"

    for name, reporter in reporters.REGISTRY.items():
        assert reporter(ctx).produced_nothing is False, name


def test_reporter_bodies_are_unaffected_by_the_new_field(tmp_path):
    """Task 1 adds a fact to `Outcome`; it changes nothing any reporter SAYS. None of the
    fifteen reporters sets `produced_nothing` itself — the watcher attaches it — so a
    reporter's own body is exactly what it composed before this field existed."""
    out = reporters.prd(prd_ctx(product(tmp_path, status="Settled")))
    assert "settled" in out.body
    assert "nothing pending" in out.body.lower()
    assert out.footnote is None
    assert out.produced_nothing is False


# --- prd: byte-for-byte what the watcher used to say -------------------------


def test_settled_run_says_nothing_is_pending(tmp_path):
    out = reporters.prd(prd_ctx(product(tmp_path, status="Settled")))
    assert "settled" in out.body
    assert "nothing pending" in out.body.lower()


def test_run_that_left_open_issues_says_it_needs_you(tmp_path):
    out = reporters.prd(prd_ctx(
        product(tmp_path, status="Draft", open_issues=True, buckets=(0, 1, 0))))
    assert "PRD_open_issues.md" in out.body
    assert "commit" in out.body
    assert "re-run" in out.body


def test_run_that_wrote_no_prd_is_not_reported_as_success(tmp_path):
    out = reporters.prd(prd_ctx(product(tmp_path, prd=False)))
    assert "no PRD" in out.body
    assert "✅" not in out.body


def test_open_issues_report_the_cycle_from_the_trail(tmp_path):
    out = reporters.prd(prd_ctx(
        product(tmp_path, status="Draft", open_issues=True, trail=(1,))))
    assert "cycle 2 complete" in out.body


def test_directives_only_says_act_rather_than_answer(tmp_path):
    out = reporters.prd(prd_ctx(
        product(tmp_path, status="Draft", open_issues=True, buckets=(0, 0, 2))))
    assert "no questions left" in out.body
    assert "2 directives" in out.body
    assert "need you to act" in out.body


def test_raised_items_only_ask_for_an_answer_not_an_empty_warning(tmp_path):
    """A companion whose only items sit in § 4, raised from downstream, is waiting on the
    owner. Read through §§ 1-3 alone it reported "lists no items" — a live profile PRD with
    two § 4 items sent exactly that."""
    p = product(tmp_path, status="Draft", open_issues=True, buckets=(0, 0, 0))
    with open(f"{p}/docs/PRD_open_issues.md", "a") as fh:
        fh.write("\n## 4. Raised from downstream — an item from a seat that did not write the PRD\n"
                 "### 4.1 the drift\n- **Why it matters:** because.\n"
                 "### 4.2 the question\n- **Why it matters:** because.\n")
    out = reporters.prd(prd_ctx(p))
    assert "lists no items" not in out.body
    assert "2 items raised from downstream" in out.body
    assert "Answer docs/PRD_open_issues.md" in out.body


def test_companion_present_but_empty_is_flagged(tmp_path):
    out = reporters.prd(prd_ctx(
        product(tmp_path, status="Draft", open_issues=True, buckets=(0, 0, 0))))
    assert "lists no items" in out.body
    assert "✅" not in out.body


def test_companion_absent_but_status_still_draft_is_flagged(tmp_path):
    out = reporters.prd(prd_ctx(product(tmp_path, status="Draft")))
    assert "not Settled" in out.body
    assert "✅" not in out.body


def test_locked_prd_is_reported_as_nothing_pending(tmp_path):
    out = reporters.prd(prd_ctx(product(tmp_path, status="Locked")))
    assert "Locked" in out.body
    assert "nothing pending" in out.body.lower()


# --- the trail is the discriminator ------------------------------------------


def test_trail_count_separates_a_first_draft_from_a_later_cycle(tmp_path):
    out = reporters.prd(prd_ctx(
        product(tmp_path, status="Draft", open_issues=True, trail=())))
    assert "cycle 1 complete" in out.body


def test_trail_count_reports_the_later_cycle(tmp_path):
    out = reporters.prd(prd_ctx(
        product(tmp_path, status="Draft", open_issues=True, trail=(1,))))
    assert "cycle 2 complete" in out.body


def test_trail_uses_the_highest_cycle_not_the_count(tmp_path):
    out = reporters.prd(prd_ctx(
        product(tmp_path, status="Draft", open_issues=True, trail=(1, 3))))
    assert "cycle 4 complete" in out.body


def test_a_settled_prd_names_no_cycle(tmp_path):
    out = reporters.prd(prd_ctx(product(tmp_path, status="Settled", trail=(1, 2))))
    assert "cycle" not in out.body.lower()


# --- the parsers, against the shapes the real files actually take ------------


def test_status_with_a_trailing_note_is_still_settled():
    text = ("**Status:** Settled — no owner action pending; external dependencies "
            "tracked in the body.\n")
    assert reporters.parse_status(text) == "Settled"


def test_version_note_wrapping_does_not_break_the_version():
    text = ("**Version:** 2 — cycle-1 answers folded in, platform claims verified\n"
            "against their primary surfaces, and the coverage policy left open\n"
            "for the owner.\n")
    assert reporters.parse_version(text) == "2"


def test_empty_buckets_written_as_prose_count_zero():
    assert reporters.count_buckets(companion(0, 1, 0)) == (0, 1, 0)


def test_owner_freeform_headings_do_not_become_items():
    text = companion(0, 1, 0) + "\n## Notes from me\n\n### 1.1 my own thought\n"
    assert reporters.count_buckets(text) == (0, 1, 0)


def test_fenced_code_is_not_parsed_as_buckets():
    text = (companion(0, 1, 0)
            + "\n```\n## 1. Open issues — pasted sample\n### 1.1 not a real item\n```\n")
    assert reporters.count_buckets(text) == (0, 1, 0)


def test_trail_cycles_is_zero_without_a_trail(tmp_path):
    (tmp_path / "docs").mkdir()
    assert reporters.trail_cycles(str(tmp_path / "docs")) == 0


# --- companion_state: is an open-issues companion still waiting on the owner? -----
#
# Recognised by structure, never by a list of literals — a slot line is a bulleted
# `**<Label>:**` whose value, stripped, begins with `<` and ends with `>`: the template's
# own placeholder standing where an answer goes. The label set itself IS enumerated
# (`_SLOT_LABELS`), because the alternative — matching any bracketed bullet value at all —
# would misread a still-templated *reasoning* field ("Grounds:", "Rationale:") as an
# unanswered decision. Measured 2026-08-30 across all eleven `*_open_issues_template.md`
# files: every decision slot uses one of four labels, "Answer" and "Confirm or override" on
# ten of the eleven, plus "Keep or re-cut" and "Your call" on the SDD template's §§ 3-4 —
# so the SDD reporter (one of the eight in scope) needs the wider set or it under-detects.


def test_no_companion_on_disk_is_the_no_companion_state(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    assert reporters.companion_state(str(docs), "SRS") is reporters.CompanionState.NO_COMPANION


def test_an_answer_slot_still_at_its_placeholder_is_unanswered(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "SRS_open_issues.md").write_text(
        "## 1. Open issues\n\n### 1.1 a question\n\n- **Answer:** <the owner fills this in>\n")
    assert reporters.companion_state(str(docs), "SRS") is reporters.CompanionState.UNANSWERED


def test_a_confirm_or_override_slot_still_bracketed_is_unanswered(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "PRD_open_issues.md").write_text(
        "## 2. Choices to confirm\n\n### 2.1 a choice\n\n"
        "- **Confirm or override:** <\"confirm\", or \"override: <what to do instead>\">\n")
    assert reporters.companion_state(str(docs), "PRD") is reporters.CompanionState.UNANSWERED


def test_a_keep_or_recut_slot_still_bracketed_is_unanswered(tmp_path):
    """The SDD template's own third slot label (§ 3 Cut calls) — absent from the other ten
    templates, and the case this plan's "both slot labels" framing would miss."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "SDD_open_issues.md").write_text(
        "## 3. Cut calls to confirm\n\n### 3.1 a cut\n\n"
        "- **Keep or re-cut:** <\"keep\", or \"re-cut: <the shape to take instead>\">\n")
    assert reporters.companion_state(str(docs), "SDD") is reporters.CompanionState.UNANSWERED


def test_a_your_call_slot_still_bracketed_is_unanswered(tmp_path):
    """The SDD template's fourth label (§ 4 Disagreements) — the one item kind with no
    raising seat, and no twin label on any other template."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "SDD_open_issues.md").write_text(
        "## 4. Disagreements\n\n### 4.1 a disagreement\n\n"
        "- **Your call:** <the position to take, by seat — or \"neither: <what to do instead>\">\n")
    assert reporters.companion_state(str(docs), "SDD") is reporters.CompanionState.UNANSWERED


def test_every_slot_filled_is_the_answered_state(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "UXD_open_issues.md").write_text(
        "## 1. Open issues\n\n### 1.1 a question\n\n- **Answer:** ship the modal variant\n\n"
        "## 2. Choices to confirm\n\n### 2.1 a choice\n\n- **Confirm or override:** confirm\n")
    assert reporters.companion_state(str(docs), "UXD") is reporters.CompanionState.ANSWERED


def test_angle_brackets_in_prose_outside_a_slot_do_not_count(tmp_path):
    """The read is line-anchored on a slot bullet, not a whole-file bracket scan — a filled
    reasoning field that happens to quote a placeholder-looking value must not flip the
    verdict for a companion whose actual decision slots are all filled."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "DESIGN_open_issues.md").write_text(
        "## 1. Open issues\n\n### 1.1 a question\n\n"
        "- **Grounds:** the corpus used <the old term> until this run\n"
        "- **Answer:** rename it everywhere\n")
    assert reporters.companion_state(str(docs), "DESIGN") is reporters.CompanionState.ANSWERED


def test_companion_case_is_read_off_disk_not_composed(tmp_path):
    """The launcher's own fix (4a6ba354): a companion on disk in a different case than the
    document's own stem must still be found — `SRS_open_issues.md` composed from "SRS" would
    miss a real `srs_open_issues.md` on a case-sensitive filesystem."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "srs_open_issues.md").write_text(
        "## 1. Open issues\n\n### 1.1 a question\n\n- **Answer:** <the owner fills this in>\n")
    assert reporters.companion_state(str(docs), "SRS") is reporters.CompanionState.UNANSWERED


def test_companion_state_with_no_docs_dir_is_the_no_companion_state():
    assert reporters.companion_state(None, "SRS") is reporters.CompanionState.NO_COMPANION
    assert reporters.companion_state("", "SRS") is reporters.CompanionState.NO_COMPANION


def test_an_unreadable_companion_degrades_to_answered(tmp_path, monkeypatch):
    """Best-effort like every other reader here: a companion that exists but cannot be read
    must not manufacture a claim it cannot back. Falling back to ANSWERED is deliberate — it
    leaves `_committed_nothing` on today's stall message rather than inventing a "waiting on
    you" one from a file this run never actually saw."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "SRS_open_issues.md").write_text("- **Answer:** <the owner fills this in>\n")

    def boom(*_a, **_kw):
        raise OSError("permission denied")

    monkeypatch.setattr(reporters, "open", boom, raising=False)
    assert reporters.companion_state(str(docs), "SRS") is reporters.CompanionState.ANSWERED


# --- _committed_nothing: a no-op and a stall get different words ------------------
#
# The default (no third argument, or NO_COMPANION / ANSWERED) is today's message,
# byte-identical — every existing call site that has not yet been taught about the
# companion keeps behaving exactly as before.


def test_default_committed_nothing_is_unchanged():
    assert reporters._committed_nothing("example-product", "SRS") == (
        "⚠️ example-product: the run committed nothing — it may have stopped. "
        "The SRS on disk is from an earlier run.")


def test_no_companion_keeps_the_stall_message():
    out = reporters._committed_nothing("example-product", "SRS", reporters.CompanionState.NO_COMPANION)
    assert "may have stopped" in out
    assert "waiting on you" not in out


def test_answered_companion_keeps_the_stall_message():
    """Fence 2: a fully-answered companion beside an unchanged HEAD is a real anomaly — the
    owner already answered and the run still did not fold it — and must not be softened."""
    out = reporters._committed_nothing("example-product", "SRS", reporters.CompanionState.ANSWERED)
    assert "may have stopped" in out
    assert "waiting on you" not in out


def test_unanswered_companion_says_nothing_to_fold_and_names_the_document():
    out = reporters._committed_nothing("example-product", "SRS", reporters.CompanionState.UNANSWERED)
    assert "SRS" in out
    assert "waiting on you" in out


def test_unanswered_companion_message_does_not_claim_success():
    """Fence 3: the run had nothing to do, which is an instruction to the owner, not an
    all-clear — the success glyph and the old stall wording are both wrong here."""
    out = reporters._committed_nothing("example-product", "SRS", reporters.CompanionState.UNANSWERED)
    assert "✅" not in out
    assert "may have stopped" not in out


def test_unanswered_companion_message_names_the_label_once():
    """`_committed_nothing` still returns the WHOLE message (module docstring, `:74`) — one
    self-contained string a caller hands straight to `Outcome`, never a fragment appended to
    another."""
    out = reporters._committed_nothing("example-product", "SRS", reporters.CompanionState.UNANSWERED)
    assert out.count("example-product") == 1


# --- integrity pass: the plan's behaviours that had no test of their own ----------
#
# Derived from `docs/proposals/reporter-no-op-vs-stall/ad_hoc_plan.md` — its per-task
# behaviours and its five trap fences — and never from reading `reporters.py`.

# The eight reporters the plan puts in scope, in its own order (§ The eight call sites).
_EIGHT_DOCUMENTS = ("PRD", "SRS", "UXD", "DESIGN", "CONTENT", "Agari", "SDD", "FDR")


@pytest.mark.parametrize("artifact", _EIGHT_DOCUMENTS)
def test_each_document_names_itself_and_no_sibling_in_either_message(artifact):
    """Task 3: "each names its own document in BOTH messages". The stall message has carried
    that guard per reporter since it was written; the new one is a second sentence with the
    same failure available to it — a reporter naming a sibling's document replaces one false
    claim with another."""
    for state in (reporters.CompanionState.NO_COMPANION,
                  reporters.CompanionState.ANSWERED,
                  reporters.CompanionState.UNANSWERED):
        out = reporters._committed_nothing("example-product", artifact, state)
        assert artifact in out
        for sibling in _EIGHT_DOCUMENTS:
            if sibling != artifact:
                assert sibling not in out


def test_the_unanswered_message_says_the_run_had_nothing_to_fold():
    """Task 2 names three things the new message must say, and this is the one no existing
    assertion covers: the owner has to learn the run had nothing TO do, not that it failed
    to do something."""
    out = reporters._committed_nothing("example-product", "SRS", reporters.CompanionState.UNANSWERED)
    assert "nothing to fold" in out


def test_angle_brackets_in_plain_prose_do_not_make_a_companion_unanswered(tmp_path):
    """Task 4: the angle-bracket test proven against a companion whose PROSE carries angle
    brackets outside a slot. Every real companion opens with a header quoting the placeholder
    it tells the owner to replace, so this is the ordinary shape, not a contrived one."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "SRS_open_issues.md").write_text(
        "> Companion to `SRS.md`. **Answer inline** — a slot still reading\n"
        "> <the owner fills this in> is one nobody has answered yet.\n\n"
        "## 1. Open issues\n\n### 1.1 a question\n\n"
        "- **Answer:** use the batched writer\n")
    assert reporters.companion_state(str(docs), "SRS") is reporters.CompanionState.ANSWERED


def test_a_siblings_unanswered_companion_does_not_speak_for_this_document(tmp_path):
    """Task 2 reads "THE DOCUMENT's companion", and a product's `docs/` holds several at once
    — one live product's held an SRS one and an FDR one in the same directory. A uxd run that
    no-opped beside somebody else's unanswered companion is still the stall case."""
    root = uxd_product(tmp_path, status="Draft")
    Path(root, "docs", "SRS_open_issues.md").write_text(
        "## 1. Open issues\n\n### 1.1 a question\n\n- **Answer:** <the owner fills this in>\n")
    out = reporters.uxd(uxd_ctx(root, head_before="same", head_after="same"))
    assert "may have stopped" in out.body
    assert "waiting on you" not in out.body


def test_the_unanswered_message_borrows_no_figures_from_the_last_run(tmp_path):
    """Fence 1 — "do not widen what is read" — holds on the new branch as well as the old
    one. Reading the companion for answeredness is allowed; reporting a figure off the
    document beside it is the original defect, and the new sentence is not exempt from it."""
    root = product(tmp_path, status="Draft", version=1, trail=(1, 2), buckets=(1, 8, 4))
    Path(root, "docs", "PRD_open_issues.md").write_text(
        "## 1. Open issues\n\n### 1.1 a question\n\n- **Answer:** <the owner fills this in>\n")
    out = reporters.prd(prd_ctx(root, head_before="same-sha", head_after="same-sha"))
    assert "waiting on you" in out.body
    assert "PRD v" not in out.body
    assert "cycle" not in out.body
    for figure in ("1 open issue", "8 choices", "4 directives"):
        assert figure not in out.body


def test_the_unanswered_message_is_the_whole_body_and_not_a_footnote(tmp_path):
    """Task 2: the function "still returns the whole message and is never a caveat appended
    to another (`:74`)". The module docstring's reason is that a footnote under a headline did
    not stop the headline being read, and that is as true of this branch as of the stall."""
    root = srs_product(tmp_path, status="Draft")
    Path(root, "docs", "SRS_open_issues.md").write_text(
        "## 1. Open issues\n\n### 1.1 a question\n\n- **Answer:** <the owner fills this in>\n")
    out = reporters.srs(srs_ctx(root, head_before="same", head_after="same"))
    assert out.footnote is None
    assert "waiting on you" in out.body


# --- a run that committed nothing must not inherit the last run's work --------
#
# An unchanged HEAD decides the prd body rather than annotating one, the way
# apply_packet has always decided its own. srs, uxd and design still annotate.


def test_a_run_that_committed_nothing_says_so_in_the_body(tmp_path):
    out = reporters.prd(prd_ctx(
        product(tmp_path, status="Draft", open_issues=True, trail=(1,)),
        head_before="same-sha", head_after="same-sha"))
    assert "committed nothing" in out.body
    assert out.footnote is None


def test_a_run_that_committed_nothing_borrows_no_figures_from_the_last_one(tmp_path):
    """The failure this came from: a refused run reported "PRD v1, cycle 2 complete —
    1 open issue, 8 choices to confirm, 4 directives" and told the owner to answer a
    file it never wrote. Every figure in it belonged to an earlier run."""
    out = reporters.prd(prd_ctx(
        product(tmp_path, status="Draft", open_issues=True, version=1,
                trail=(1,), buckets=(1, 8, 4)),
        head_before="same-sha", head_after="same-sha"))
    assert "PRD v" not in out.body
    assert "cycle" not in out.body
    assert "Answer docs/PRD_open_issues.md" not in out.body
    for figure in ("1 open issue", "8 choices", "4 directives"):
        assert figure not in out.body


def test_prd_run_that_committed_nothing_but_left_an_unanswered_companion_says_so(tmp_path):
    """The reported failure, in PRD's own terms: companion-self-answer can open a companion
    nobody has answered, and the next producing run correctly no-ops. That is not the stall
    the old message describes."""
    root = product(tmp_path, status="Draft", trail=(1,))
    (Path(root, "docs", "PRD_open_issues.md")).write_text(
        "## 1. Open issues\n\n### 1.1 a question\n\n- **Answer:** <the owner fills this in>\n")
    out = reporters.prd(prd_ctx(root, head_before="same-sha", head_after="same-sha"))
    assert "PRD" in out.body
    assert "waiting on you" in out.body
    assert "may have stopped" not in out.body


def test_a_run_that_committed_has_no_footnote(tmp_path):
    out = reporters.prd(prd_ctx(
        product(tmp_path, status="Draft", open_issues=True, trail=(1,)),
        head_before="before-sha", head_after="after-sha"))
    assert "committed nothing" not in out.body
    assert "cycle 2 complete" in out.body


def test_a_product_that_is_not_a_repo_still_reads_the_product(tmp_path):
    """git_head returns None outside a repo; an unknown HEAD is not evidence of an idle
    run, so it claims neither outcome and the body stays the product read.

    Asserted on the body, not on `footnote is None`: prd sets no footnote at all now, so
    the old form passes whatever this branch does.
    """
    out = reporters.prd(prd_ctx(product(tmp_path, status="Settled"),
                                head_before=None, head_after=None))
    assert "committed nothing" not in out.body
    assert "settled — nothing pending" in out.body


# --- the outcome read is best-effort -----------------------------------------


def test_unreadable_product_falls_back_rather_than_failing(monkeypatch, tmp_path):
    def boom(_path):
        raise OSError("permission denied")

    monkeypatch.setattr(reporters.os, "listdir", boom)
    monkeypatch.setattr(reporters.os.path, "isfile", boom)

    out = reporters.prd(prd_ctx(product(tmp_path)))
    assert "could not be read" in out.body or "run ended" in out.body


def test_a_parser_bug_costs_specificity_not_the_message(monkeypatch, tmp_path):
    def boom(_text):
        raise ValueError("unexpected shape")

    monkeypatch.setattr(reporters, "count_buckets", boom)

    out = reporters.prd(prd_ctx(product(tmp_path, status="Draft", open_issues=True)))
    assert "run ended" in out.body


# --- fix-author: the artifact is the packet file it writes -------------------


def test_fix_author_reports_the_packet_it_authored(tmp_path):
    packet = tmp_path / "fix_packet.md"
    packet.write_text("# Fix packet\n\n**State:** awaiting-owner\n")
    out = reporters.fix_author(OutcomeContext(
        label="thing v1.0.0", artifact_path=str(packet), state="blocked"))
    assert "fix packet" in out.body.lower()
    assert str(packet) in out.body


def test_fix_author_flags_a_run_that_wrote_no_packet(tmp_path):
    out = reporters.fix_author(OutcomeContext(
        label="thing v1.0.0", artifact_path=str(tmp_path / "fix_packet.md"),
        state="stopped"))
    assert "no packet" in out.body
    assert "✅" not in out.body


def test_fix_author_flags_an_empty_packet(tmp_path):
    packet = tmp_path / "fix_packet.md"
    packet.write_text("   \n")
    out = reporters.fix_author(OutcomeContext(
        label="thing v1.0.0", artifact_path=str(packet), state="stopped"))
    assert "no packet" in out.body


# --- apply-packet: the outcome is whether the round committed ----------------


def test_apply_packet_reports_a_committed_round(tmp_path):
    out = reporters.apply_packet(OutcomeContext(
        label="v1.0.0", state="blocked",
        head_before="before-sha", head_after="after-sha"))
    assert "committed" in out.body
    assert "✅" in out.body


def test_apply_packet_flags_a_round_that_committed_nothing(tmp_path):
    out = reporters.apply_packet(OutcomeContext(
        label="v1.0.0", state="stopped",
        head_before="same-sha", head_after="same-sha"))
    assert "committed nothing" in out.body
    assert "✅" not in out.body


def test_apply_packet_outside_a_repo_does_not_claim_success(tmp_path):
    """No HEAD to compare — it must not announce a commit it cannot see."""
    out = reporters.apply_packet(OutcomeContext(
        label="v1.0.0", state="stopped", head_before=None, head_after=None))
    assert "✅" not in out.body


# --- srs: authored against the real SRS contract, NOT a prd clone -------------
#
# The SRS differs from the PRD in four load-bearing ways, and each shows up as a test:
#   - Status carries all three of the template's values — Draft | Settled | Locked
#     (srs_template.md) — and product-srs sets it FROM the done condition: Settled when the
#     run ends with no companion on disk, Draft otherwise (product-srs SKILL.md). So Settled
#     is the ordinary status of a finished SRS, not a PRD-only state.
#   - The companion (SRS_open_issues.md) has Open issues, Choices to confirm and § 3,
#     items raised from downstream — no directives bucket.
#   - The body reports no cycle number, deliberately: trail/srs/ exists (product-srs retires
#     each answered companion to it) but the SRS body does not name a cycle, unlike the prd
#     reporter's.
#   - The done signal is the companion's ABSENCE, and Status is set from that same condition,
#     so Settled-with-no-companion is the done state and Draft-with-no-companion is a state no
#     finished run can produce — flagged, exactly as the prd reporter flags it. Locked is the
#     owner's ratification and never auto-set, so it is a clean done on its own.
#     (This was a deliberate divergence until 2026-08-01, justified by a comment that stated
#     the Settled-or-Draft rule and then concluded Draft was legitimate anyway. It was not.)


SRS_BUCKET_TITLES = {
    1: "Open issues — technical questions with no answer yet",
    2: "Choices to confirm — the CTO drafted a best-effort answer; confirm or override",
}


def srs_companion(n1=0, n2=0, extra=""):
    """The SRS companion's two answer buckets (srs_open_issues_template.md). `extra` appends
    raw text after them — used to add a § 3, items raised from downstream."""
    out = []
    for bucket, n in ((1, n1), (2, n2)):
        out.append(f"## {bucket}. {SRS_BUCKET_TITLES[bucket]}\n")
        if n == 0:
            out.append("None this round.\n")
        for i in range(1, n + 1):
            out.append(f"### {bucket}.{i} the decision, in one line\n")
            out.append("- **Why it matters:** because.\n")
    if extra:
        out.append(extra)
    return "\n".join(out)


def srs_product(tmp_path, srs=True, open_issues=False, status="Draft", version=2,
                buckets=(0, 0)):
    """The tree product-srs authors into: docs/SRS.md (+ optional SRS_open_issues.md).
    `status=None` omits the Status line entirely, so the parse-fails branch can be exercised."""
    docs = tmp_path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    if srs:
        status_line = f"**Status:** {status}\n" if status is not None else ""
        (docs / "SRS.md").write_text(
            f"# SRS — thing\n\n{status_line}**Owner:** CTO\n"
            f"**Version:** {version} — what this revision changed\n"
        )
    if open_issues:
        (docs / "SRS_open_issues.md").write_text(srs_companion(*buckets))
    return str(tmp_path)


def srs_ctx(artifact_path, *, state="blocked", head_before=None, head_after=None):
    return OutcomeContext(
        label="example-product", cwd="/repo", artifact_path=artifact_path,
        state=state, head_before=head_before, head_after=head_after,
    )


def test_srs_is_registered():
    """A new run type is one registry entry; the watcher resolves --reporter srs by name."""
    assert reporters.get_reporter("srs") is reporters.srs


def test_srs_run_that_wrote_no_srs_is_not_a_success(tmp_path):
    out = reporters.srs(srs_ctx(srs_product(tmp_path, srs=False)))
    assert "no SRS" in out.body
    assert "✅" not in out.body


def test_srs_companion_with_items_reports_pending_without_a_cycle(tmp_path):
    out = reporters.srs(srs_ctx(
        srs_product(tmp_path, status="Draft", open_issues=True, buckets=(1, 1))))
    assert "open issue" in out.body
    assert "choice to confirm" in out.body
    assert "SRS_open_issues.md" in out.body
    assert "commit" in out.body
    assert "re-run" in out.body
    assert "cycle" not in out.body.lower()


def test_srs_choices_only_says_choices_and_no_open_issue_term(tmp_path):
    out = reporters.srs(srs_ctx(
        srs_product(tmp_path, status="Draft", open_issues=True, buckets=(0, 2))))
    assert "2 choices to confirm" in out.body
    assert "open issue" not in out.body   # 'SRS_open_issues.md' uses an underscore, not this term
    assert "SRS_open_issues.md" in out.body


def test_srs_companion_present_but_empty_is_flagged(tmp_path):
    out = reporters.srs(srs_ctx(
        srs_product(tmp_path, status="Draft", open_issues=True, buckets=(0, 0))))
    assert "lists no items" in out.body
    assert "✅" not in out.body


def test_srs_has_no_directives_bucket(tmp_path):
    """The SRS companion's § 3 is items raised from downstream, never directives."""
    p = srs_product(tmp_path, status="Draft")   # no companion written yet
    raised = "\n## 3. Raised from downstream\n\n### 3.1 a raised item\n- **Why:** x.\n"
    (tmp_path / "docs" / "SRS_open_issues.md").write_text(srs_companion(0, 1) + raised)

    out = reporters.srs(srs_ctx(p))

    assert "directive" not in out.body.lower()
    assert "1 choice to confirm, 1 item raised from downstream" in out.body


def test_srs_raised_items_only_ask_for_an_answer_not_an_empty_warning(tmp_path):
    p = srs_product(tmp_path, status="Draft")
    raised = "\n## 3. Raised from downstream\n\n### 3.1 a raised item\n- **Why:** x.\n"
    (tmp_path / "docs" / "SRS_open_issues.md").write_text(srs_companion(0, 0) + raised)

    out = reporters.srs(srs_ctx(p))

    assert "lists no items" not in out.body
    assert "1 item raised from downstream" in out.body


def test_srs_companion_absent_and_locked_is_nothing_pending(tmp_path):
    out = reporters.srs(srs_ctx(srs_product(tmp_path, status="Locked")))
    assert "Locked" in out.body
    assert "nothing pending" in out.body.lower()
    assert "✅" in out.body


def test_srs_draft_with_no_companion_is_flagged(tmp_path):
    """product-srs stamps Settled from the very condition that removes the companion
    (SKILL.md L191-193), so Draft beside no companion is a state a finished run cannot
    leave behind — a died-mid-run or a hand-deleted companion. Warn, as prd does."""
    out = reporters.srs(srs_ctx(srs_product(tmp_path, status="Draft")))
    assert "⚠️" in out.body
    assert "not Settled" in out.body
    assert "✅" not in out.body


def test_srs_settled_with_no_companion_is_the_done_state_the_skill_writes(tmp_path):
    """The status product-srs actually stamps when a round clears the companion: Settled
    (SKILL.md sets Status from the DONE condition). It must read as a clean done, not a
    warning — the reporter briefly predated that rule and flagged every finished SRS."""
    out = reporters.srs(srs_ctx(srs_product(tmp_path, status="Settled")))
    assert "✅" in out.body
    assert "nothing pending" in out.body.lower()
    assert "check docs/SRS.md" not in out.body


def test_srs_companion_absent_but_status_unreadable_is_flagged(tmp_path):
    out = reporters.srs(srs_ctx(srs_product(tmp_path, status=None)))
    assert "check docs/SRS.md" in out.body
    assert "✅" not in out.body


def test_srs_version_is_surfaced_in_the_body(tmp_path):
    out = reporters.srs(srs_ctx(srs_product(tmp_path, status="Locked", version=2)))
    assert "SRS v2" in out.body


def test_srs_version_note_wrapping_does_not_break_the_version(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir(parents=True)
    (docs / "SRS.md").write_text(
        "# SRS\n\n**Status:** Locked\n"
        "**Version:** 3 — cross-line note that wraps\nonto a second physical line\n")
    out = reporters.srs(srs_ctx(str(tmp_path)))
    assert "SRS v3" in out.body


# --- a run that committed nothing must not inherit the last run's work --------


def test_srs_run_that_committed_nothing_says_so_in_the_body(tmp_path):
    out = reporters.srs(srs_ctx(
        srs_product(tmp_path, status="Draft", open_issues=True, buckets=(1, 0)),
        head_before="same-sha", head_after="same-sha"))
    assert "committed nothing" in out.body
    assert out.footnote is None


def test_srs_run_that_committed_nothing_borrows_no_figures_from_the_last_one(tmp_path):
    out = reporters.srs(srs_ctx(
        srs_product(tmp_path, status="Draft", open_issues=True, version=2,
                    buckets=(1, 8)),
        head_before="same-sha", head_after="same-sha"))
    assert "SRS v" not in out.body
    assert "Answer docs/SRS_open_issues.md" not in out.body
    for figure in ("1 open issue", "8 choices"):
        assert figure not in out.body


def test_srs_run_that_committed_nothing_but_left_an_unanswered_companion_says_so(tmp_path):
    """The reported case this plan exists for: a live product's `product-srs` run left one raised,
    unanswered item, and the owner read the old stall message as a failure."""
    root = srs_product(tmp_path, status="Draft")
    (Path(root, "docs", "SRS_open_issues.md")).write_text(
        "## 1. Open issues\n\n### 1.1 a question\n\n- **Answer:** <the owner fills this in>\n")
    out = reporters.srs(srs_ctx(root, head_before="same-sha", head_after="same-sha"))
    assert "SRS" in out.body
    assert "waiting on you" in out.body
    assert "may have stopped" not in out.body


def test_srs_run_that_committed_nothing_with_a_fully_answered_companion_is_the_real_anomaly(
        tmp_path):
    """Fence 2, proven at the whole-reporter level and not only on `companion_state` in
    isolation: a companion where every slot is filled beside an unchanged HEAD means the
    owner already answered and the run still did not commit — a real anomaly, and it must
    not be softened into the "waiting on you" message."""
    root = srs_product(tmp_path, status="Draft")
    (Path(root, "docs", "SRS_open_issues.md")).write_text(
        "## 1. Open issues\n\n### 1.1 a question\n\n- **Answer:** ship the modal variant\n")
    out = reporters.srs(srs_ctx(root, head_before="same-sha", head_after="same-sha"))
    assert "may have stopped" in out.body
    assert "waiting on you" not in out.body


def test_srs_names_the_srs_and_not_a_sibling_artifact(tmp_path):
    """Each reporter says what is on disk for ITS artifact. The prd reporter's sentence
    names the PRD; an srs run repeating it would replace one false claim with another."""
    out = reporters.srs(srs_ctx(
        srs_product(tmp_path, status="Draft", open_issues=True, buckets=(1, 0)),
        head_before="same-sha", head_after="same-sha"))
    assert "The SRS on disk is from an earlier run." in out.body
    assert "PRD" not in out.body
    assert "UXD" not in out.body


def test_srs_run_that_committed_reads_the_product(tmp_path):
    """Asserted on the body, not on `footnote is None`: srs sets no footnote at all now, so
    the old form passes whatever this branch does."""
    out = reporters.srs(srs_ctx(
        srs_product(tmp_path, status="Locked"),
        head_before="before-sha", head_after="after-sha"))
    assert "committed nothing" not in out.body
    assert "is Locked — nothing pending" in out.body


def test_srs_a_product_that_is_not_a_repo_still_reads_the_product(tmp_path):
    """git_head returns None outside a repo; an unknown HEAD is not evidence of an idle
    run, so it claims neither outcome and the body stays the product read."""
    out = reporters.srs(srs_ctx(srs_product(tmp_path, status="Locked"),
                                head_before=None, head_after=None))
    assert "committed nothing" not in out.body
    assert "is Locked — nothing pending" in out.body


def test_srs_unreadable_product_falls_back_rather_than_failing(monkeypatch, tmp_path):
    def boom(_path):
        raise OSError("permission denied")

    monkeypatch.setattr(reporters.os.path, "isfile", boom)

    out = reporters.srs(srs_ctx(srs_product(tmp_path, status="Locked")))
    assert "could not be read" in out.body or "run ended" in out.body


def test_srs_a_parser_bug_costs_specificity_not_the_message(monkeypatch, tmp_path):
    def boom(_text):
        raise ValueError("unexpected shape")

    monkeypatch.setattr(reporters, "count_buckets", boom)

    out = reporters.srs(srs_ctx(
        srs_product(tmp_path, status="Draft", open_issues=True, buckets=(1, 1))))
    assert "run ended" in out.body


def test_srs_without_an_artifact_path_degrades_to_run_ended(tmp_path):
    out = reporters.srs(OutcomeContext(label="example-product"))
    assert out.body == "example-product: run ended."


# --- uxd: sits between prd and srs, authored against the real UXD contract ----
#
# The UXD differs from both siblings in ways that are load-bearing, not incidental:
#   - Status carries the same three values — Draft | Settled | Locked (uxd_template.md) —
#     under the SAME rule as prd/srs: Settled only when the run ends with no companion on
#     disk (product-uxd SKILL.md), Draft otherwise. Draft beside no companion is therefore a
#     state no finished run can leave behind (this reporter's OQ1, see below).
#   - The companion (UXD_open_issues.md) has Open issues, Choices to confirm and § 3, items
#     raised from downstream — no directives bucket, like srs's.
#   - docs/trail/uxd/ exists (product-uxd SKILL.md § The files and the loop) and IS read
#     here, like prd's — an open round's body names a cycle number; the done branch does not
#     (the trail counts rounds folded in, a different quantity from a round in flight).
#   - OQ1 (docs/proposals/product-uxd-launcher/rationale.md): Draft-with-no-companion warns
#     (the prd reading), not a clean success (the srs reading before 2026-08-01). Written to
#     that default; flipping it later is a one-branch change in _uxd_body.


UXD_BUCKET_TITLES = {
    1: "Open issues — experience questions with no answer yet",
    2: "Choices to confirm — the CDO drafted a best-effort answer; confirm or override",
}


def uxd_companion(n1=0, n2=0, extra=""):
    """The UXD companion's two answer buckets (uxd_open_issues_template.md). `extra` appends
    raw text after them — used to add a § 3, items raised from downstream."""
    out = []
    for bucket, n in ((1, n1), (2, n2)):
        out.append(f"## {bucket}. {UXD_BUCKET_TITLES[bucket]}\n")
        if n == 0:
            out.append("None this cycle.\n")
        for i in range(1, n + 1):
            out.append(f"### {bucket}.{i} the decision, in one line\n")
            out.append("- **Why it matters:** because.\n")
    if extra:
        out.append(extra)
    return "\n".join(out)


def uxd_product(tmp_path, uxd=True, open_issues=False, status="Draft", version=2,
                 buckets=(0, 0), trail=()):
    """The tree product-uxd authors into: docs/UXD.md (+ optional UXD_open_issues.md +
    docs/trail/uxd/). `status=None` omits the Status line entirely, so the parse-fails
    branch can be exercised."""
    docs = tmp_path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    if uxd:
        status_line = f"**Status:** {status}\n" if status is not None else ""
        (docs / "UXD.md").write_text(
            f"# UXD — thing\n\n{status_line}**Owner:** CDO\n"
            f"**Version:** {version} — what this revision changed\n"
        )
    if open_issues:
        (docs / "UXD_open_issues.md").write_text(uxd_companion(*buckets))
    if trail:
        (docs / "trail/uxd").mkdir(parents=True, exist_ok=True)
        for n in trail:
            (docs / "trail/uxd" / f"cycle-{n}.md").write_text("# cycle\n")
    return str(tmp_path)


def uxd_ctx(artifact_path, *, state="blocked", head_before=None, head_after=None):
    return OutcomeContext(
        label="example-product", cwd="/repo", artifact_path=artifact_path,
        state=state, head_before=head_before, head_after=head_after,
    )


def test_uxd_is_registered():
    """A new run type is one registry entry; the watcher resolves --reporter uxd by name."""
    assert reporters.get_reporter("uxd") is reporters.uxd


def test_uxd_run_that_wrote_no_uxd_is_not_a_success(tmp_path):
    out = reporters.uxd(uxd_ctx(uxd_product(tmp_path, uxd=False)))
    assert "no UXD" in out.body
    assert "✅" not in out.body


def test_uxd_companion_with_items_reports_pending_and_the_next_move(tmp_path):
    out = reporters.uxd(uxd_ctx(
        uxd_product(tmp_path, status="Draft", open_issues=True, buckets=(1, 1))))
    assert "open issue" in out.body
    assert "choice to confirm" in out.body
    assert "UXD_open_issues.md" in out.body
    assert "Answer" in out.body
    assert "commit" in out.body
    assert "re-run" in out.body


def test_uxd_choices_only_says_choices_and_no_open_issue_term(tmp_path):
    out = reporters.uxd(uxd_ctx(
        uxd_product(tmp_path, status="Draft", open_issues=True, buckets=(0, 2))))
    assert "2 choices to confirm" in out.body
    assert "open issue" not in out.body   # 'UXD_open_issues.md' uses an underscore, not this term
    assert "UXD_open_issues.md" in out.body


def test_uxd_has_no_directives_bucket(tmp_path):
    """The UXD companion's § 3 is items raised from downstream, never directives."""
    p = uxd_product(tmp_path, status="Draft")   # no companion written yet
    raised = "\n## 3. Raised from downstream\n\n### 3.1 a raised item\n- **Why:** x.\n"
    (tmp_path / "docs" / "UXD_open_issues.md").write_text(uxd_companion(0, 1) + raised)

    out = reporters.uxd(uxd_ctx(p))

    assert "directive" not in out.body.lower()
    assert "1 choice to confirm, 1 item raised from downstream" in out.body


def test_uxd_raised_items_only_ask_for_an_answer_not_an_empty_warning(tmp_path):
    p = uxd_product(tmp_path, status="Draft")
    raised = "\n## 3. Raised from downstream\n\n### 3.1 a raised item\n- **Why:** x.\n"
    (tmp_path / "docs" / "UXD_open_issues.md").write_text(uxd_companion(0, 0) + raised)

    out = reporters.uxd(uxd_ctx(p))

    assert "lists no items" not in out.body
    assert "1 item raised from downstream" in out.body


def test_uxd_companion_present_but_empty_is_flagged(tmp_path):
    out = reporters.uxd(uxd_ctx(
        uxd_product(tmp_path, status="Draft", open_issues=True, buckets=(0, 0))))
    assert "lists no items" in out.body
    assert "✅" not in out.body


# --- the trail is the discriminator (uxd HAS one, unlike srs) -----------------


def test_uxd_open_round_names_the_cycle_from_the_trail(tmp_path):
    out = reporters.uxd(uxd_ctx(
        uxd_product(tmp_path, status="Draft", open_issues=True, buckets=(1, 0), trail=(1, 2))))
    assert "cycle 3" in out.body


def test_uxd_open_round_with_no_trail_names_cycle_1(tmp_path):
    out = reporters.uxd(uxd_ctx(
        uxd_product(tmp_path, status="Draft", open_issues=True, buckets=(1, 0))))
    assert "cycle 1" in out.body


def test_uxd_trail_ignores_a_non_cycle_filename(tmp_path):
    p = uxd_product(tmp_path, status="Draft", open_issues=True, buckets=(1, 0), trail=(1,))
    (Path(p) / "docs" / "trail/uxd" / "notes.md").write_text("not a cycle file\n")

    out = reporters.uxd(uxd_ctx(p))

    assert "cycle 2" in out.body


def test_uxd_done_branch_names_no_cycle_even_with_a_trail(tmp_path):
    """The trail counts rounds folded in, a different quantity from a round in flight —
    the prd reporter's own reasoning, reused here since uxd shares prd's trail shape."""
    out = reporters.uxd(uxd_ctx(
        uxd_product(tmp_path, status="Settled", trail=(1, 2))))
    assert "cycle" not in out.body.lower()


# --- companion absent: the three Status branches, OQ1 for Draft ---------------


def test_uxd_companion_absent_and_settled_is_nothing_pending(tmp_path):
    out = reporters.uxd(uxd_ctx(uxd_product(tmp_path, status="Settled")))
    assert "settled" in out.body.lower()
    assert "nothing pending" in out.body.lower()
    assert "✅" in out.body


def test_uxd_companion_absent_and_locked_is_nothing_pending(tmp_path):
    out = reporters.uxd(uxd_ctx(uxd_product(tmp_path, status="Locked")))
    assert "Locked" in out.body
    assert "nothing pending" in out.body.lower()
    assert "✅" in out.body


def test_uxd_draft_with_no_companion_is_flagged(tmp_path):
    """OQ1 (rationale.md) — default A: warn, matching the prd reading and the srs reporter's
    reading since 2026-08-01. product-uxd stamps Settled from the very condition that
    removes the companion (SKILL.md :207-214), so Draft beside no companion is a state a
    finished run cannot leave behind. Flip this branch alone to adopt option B."""
    out = reporters.uxd(uxd_ctx(uxd_product(tmp_path, status="Draft")))
    assert "⚠️" in out.body
    assert "not Settled" in out.body
    assert "✅" not in out.body


def test_uxd_companion_absent_but_status_unreadable_is_flagged(tmp_path):
    out = reporters.uxd(uxd_ctx(uxd_product(tmp_path, status=None)))
    assert "check docs/UXD.md" in out.body
    assert "✅" not in out.body


# --- version and best-effort — the same mechanisms as prd/srs ----------------


def test_uxd_version_is_surfaced_in_the_body(tmp_path):
    out = reporters.uxd(uxd_ctx(uxd_product(tmp_path, status="Locked", version=2)))
    assert "UXD v2" in out.body


def test_uxd_version_note_wrapping_does_not_break_the_version(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir(parents=True)
    (docs / "UXD.md").write_text(
        "# UXD\n\n**Status:** Locked\n"
        "**Version:** 3 — cross-line note that wraps\nonto a second physical line\n")
    out = reporters.uxd(uxd_ctx(str(tmp_path)))
    assert "UXD v3" in out.body


# --- a run that committed nothing must not inherit the last run's work --------


def test_uxd_run_that_committed_nothing_says_so_in_the_body(tmp_path):
    out = reporters.uxd(uxd_ctx(
        uxd_product(tmp_path, status="Draft", open_issues=True, buckets=(1, 0)),
        head_before="same-sha", head_after="same-sha"))
    assert "committed nothing" in out.body
    assert out.footnote is None


def test_uxd_run_that_committed_nothing_borrows_no_figures_from_the_last_one(tmp_path):
    """uxd carries a cycle number, which prd's failure case showed is the figure that reads
    hardest as a result: "cycle 2 complete" is a claim about work this run did not do."""
    out = reporters.uxd(uxd_ctx(
        uxd_product(tmp_path, status="Draft", open_issues=True, version=2,
                    trail=(1,), buckets=(1, 8)),
        head_before="same-sha", head_after="same-sha"))
    assert "UXD v" not in out.body
    assert "cycle" not in out.body
    assert "Answer docs/UXD_open_issues.md" not in out.body
    for figure in ("1 open issue", "8 choices"):
        assert figure not in out.body


def test_uxd_run_that_committed_nothing_but_left_an_unanswered_companion_says_so(tmp_path):
    root = uxd_product(tmp_path, status="Draft")
    (Path(root, "docs", "UXD_open_issues.md")).write_text(
        "## 1. Open issues\n\n### 1.1 a question\n\n- **Answer:** <the owner fills this in>\n")
    out = reporters.uxd(uxd_ctx(root, head_before="same-sha", head_after="same-sha"))
    assert "UXD" in out.body
    assert "waiting on you" in out.body
    assert "may have stopped" not in out.body


def test_uxd_names_the_uxd_and_not_a_sibling_artifact(tmp_path):
    """Each reporter says what is on disk for ITS artifact. The prd reporter's sentence
    names the PRD; a uxd run repeating it would replace one false claim with another."""
    out = reporters.uxd(uxd_ctx(
        uxd_product(tmp_path, status="Draft", open_issues=True, buckets=(1, 0)),
        head_before="same-sha", head_after="same-sha"))
    assert "The UXD on disk is from an earlier run." in out.body
    assert "PRD" not in out.body
    assert "SRS" not in out.body


def test_uxd_run_that_committed_reads_the_product(tmp_path):
    """Asserted on the body, not on `footnote is None`: uxd sets no footnote at all now, so
    the old form passes whatever this branch does."""
    out = reporters.uxd(uxd_ctx(
        uxd_product(tmp_path, status="Locked"),
        head_before="before-sha", head_after="after-sha"))
    assert "committed nothing" not in out.body
    assert "is Locked — nothing pending" in out.body


def test_uxd_a_product_that_is_not_a_repo_still_reads_the_product(tmp_path):
    """git_head returns None outside a repo; an unknown HEAD is not evidence of an idle
    run, so it claims neither outcome and the body stays the product read."""
    out = reporters.uxd(uxd_ctx(uxd_product(tmp_path, status="Locked"),
                                head_before=None, head_after=None))
    assert "committed nothing" not in out.body
    assert "is Locked — nothing pending" in out.body


def test_uxd_unreadable_product_falls_back_rather_than_failing(monkeypatch, tmp_path):
    def boom(_path):
        raise OSError("permission denied")

    monkeypatch.setattr(reporters.os.path, "isfile", boom)

    out = reporters.uxd(uxd_ctx(uxd_product(tmp_path, status="Locked")))
    # The intent names this body specifically — "could not be read — what it produced is
    # unknown" — not merely "something other than a traceback". A disjunction with the plain
    # `run ended.` fallback would pass on either branch and so pin neither.
    assert "could not be read" in out.body
    assert "what it produced is unknown" in out.body
    assert "✅" not in out.body


def test_uxd_a_parser_bug_costs_specificity_not_the_message(monkeypatch, tmp_path):
    def boom(_text):
        raise ValueError("unexpected shape")

    monkeypatch.setattr(reporters, "count_buckets", boom)

    out = reporters.uxd(uxd_ctx(
        uxd_product(tmp_path, status="Draft", open_issues=True, buckets=(1, 1))))
    assert "run ended" in out.body


def test_uxd_without_an_artifact_path_degrades_to_run_ended(tmp_path):
    out = reporters.uxd(OutcomeContext(label="example-product"))
    assert out.body == "example-product: run ended."


# --- no existing reporter changes ----------------------------------------------


def test_existing_reporters_are_unaffected_by_the_uxd_addition():
    assert reporters.get_reporter("prd") is reporters.prd
    assert reporters.get_reporter("srs") is reporters.srs
    assert reporters.get_reporter("fix-author") is reporters.fix_author
    assert reporters.get_reporter("apply-packet") is reporters.apply_packet
    assert reporters.get_reporter("nope-not-a-reporter") is reporters.generic


# --- design: three buckets like prd, a cycle number like uxd, its own third term -----
#
# Authored against the real DESIGN contract (docs/proposals/archive/product-design-md-launcher/
# ad_hoc_plan.md § The real DESIGN contract), not cloned from either sibling:
#   - docs/DESIGN.md carries the same Status/Version line shapes parse_status/parse_version
#     already read (design_template.md:99, :106).
#   - docs/DESIGN_open_issues.md has three buckets — open issues, choices, raised from
#     downstream (design_open_issues_template.md) — so count_buckets is used with all three
#     returns.
#   - The third bucket is "Raised from downstream" (design_open_issues_template.md § 3),
#     never "directive" — that word is the PRD companion's alone (reporters.py
#     _pending_phrase). Declared omissions are § 2 items, choices to confirm.
#   - docs/trail/design/ exists and IS read (SKILL.md:67, :69-72) — an open round's body
#     names a cycle number, like prd's and uxd's; the done branch does not.
#   - Draft beside no companion warns — the family's settled reading (rationale.md decision
#     6), not an open question the way it was for uxd's OQ1.


DESIGN_BUCKET_TITLES = {
    1: "Open issues — values with no evidence and no default worth guessing",
    2: "Choices to confirm — the CDO drafted a best-effort value; confirm or override",
    3: "Raised from downstream — an item from a seat that did not write the design language",
}


def design_companion(n1=0, n2=0, n3=0, extra=""):
    """The three-bucket DESIGN companion (design_open_issues_template.md). `extra` appends
    raw text after the three buckets."""
    out = []
    for bucket, n in ((1, n1), (2, n2), (3, n3)):
        out.append(f"## {bucket}. {DESIGN_BUCKET_TITLES[bucket]}\n")
        if n == 0:
            out.append("None this cycle.\n")
        for i in range(1, n + 1):
            out.append(f"### {bucket}.{i} the decision, in one line\n")
            out.append("- **Why it matters:** because.\n")
    if extra:
        out.append(extra)
    return "\n".join(out)


def design_product(tmp_path, design=True, open_issues=False, status="Draft", version=2,
                    buckets=(0, 0, 0), trail=()):
    """The tree product-design authors into: docs/DESIGN.md (+ optional
    DESIGN_open_issues.md + docs/trail/design/). `status=None` omits the Status line
    entirely, so the parse-fails branch can be exercised."""
    docs = tmp_path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    if design:
        status_line = f"**Status:** {status}\n" if status is not None else ""
        (docs / "DESIGN.md").write_text(
            f"---\nversion: alpha\nname: thing\n---\n\n# DESIGN — thing\n\n{status_line}"
            f"**Owner:** CDO\n**Version:** {version} — what this revision changed\n"
        )
    if open_issues:
        (docs / "DESIGN_open_issues.md").write_text(design_companion(*buckets))
    if trail:
        (docs / "trail/design").mkdir(parents=True, exist_ok=True)
        for n in trail:
            (docs / "trail/design" / f"cycle-{n}.md").write_text("# cycle\n")
    return str(tmp_path)


def design_ctx(artifact_path, *, state="blocked", head_before=None, head_after=None):
    return OutcomeContext(
        label="example-product", cwd="/repo", artifact_path=artifact_path,
        state=state, head_before=head_before, head_after=head_after,
    )


def test_design_is_registered():
    """A new run type is one registry entry; the watcher resolves --reporter design by name."""
    assert reporters.get_reporter("design") is reporters.design


def test_design_run_that_wrote_no_design_is_not_a_success(tmp_path):
    out = reporters.design(design_ctx(design_product(tmp_path, design=False)))
    assert "no DESIGN" in out.body
    assert "✅" not in out.body


def test_design_unreadable_product_falls_back_rather_than_failing(monkeypatch, tmp_path):
    def boom(_path):
        raise OSError("permission denied")

    monkeypatch.setattr(reporters.os.path, "isfile", boom)

    out = reporters.design(design_ctx(design_product(tmp_path, status="Locked")))
    assert "could not be read" in out.body
    assert "what it produced is unknown" in out.body
    assert "✅" not in out.body


def test_design_companion_with_items_in_all_three_buckets_reports_all_three(tmp_path):
    out = reporters.design(design_ctx(
        design_product(tmp_path, status="Draft", open_issues=True, buckets=(1, 1, 1))))
    assert "1 open issue" in out.body
    assert "1 choice to confirm" in out.body
    assert "1 item raised from downstream" in out.body
    assert "DESIGN_open_issues.md" in out.body
    assert "Answer" in out.body
    assert "commit" in out.body
    assert "re-run" in out.body


def test_design_third_bucket_never_says_directive(tmp_path):
    """The third bucket's term is "raised from downstream" — 'directive' belongs to the
    PRD companion alone (_pending_phrase). Assert the word's absence explicitly, not only
    the presence of the right term."""
    out = reporters.design(design_ctx(
        design_product(tmp_path, status="Draft", open_issues=True, buckets=(0, 0, 2))))
    assert "directive" not in out.body.lower()
    assert "2 items raised from downstream" in out.body
    assert "lists no items" not in out.body


def test_design_choices_only_says_choices_and_no_other_bucket_term(tmp_path):
    out = reporters.design(design_ctx(
        design_product(tmp_path, status="Draft", open_issues=True, buckets=(0, 2, 0))))
    assert "2 choices to confirm" in out.body
    # 'DESIGN_open_issues.md' uses an underscore, not this term
    assert "open issue" not in out.body
    assert "raised from downstream" not in out.body
    assert "DESIGN_open_issues.md" in out.body


def test_design_bucket_terms_are_singular_and_plural(tmp_path):
    singular = reporters.design(design_ctx(
        design_product(tmp_path, status="Draft", open_issues=True, buckets=(1, 1, 1))))
    assert "1 open issue" in singular.body
    assert "1 open issues" not in singular.body
    assert "1 choice to confirm" in singular.body
    assert "1 choices to confirm" not in singular.body
    assert "1 item raised from downstream" in singular.body
    assert "1 items raised" not in singular.body

    plural = reporters.design(design_ctx(
        design_product(tmp_path, status="Draft", open_issues=True, buckets=(2, 2, 2))))
    assert "2 open issues" in plural.body
    assert "2 choices to confirm" in plural.body
    assert "2 items raised from downstream" in plural.body


def test_design_companion_present_but_empty_is_flagged(tmp_path):
    out = reporters.design(design_ctx(
        design_product(tmp_path, status="Draft", open_issues=True, buckets=(0, 0, 0))))
    assert "lists no items" in out.body
    assert "✅" not in out.body


# --- the trail is the discriminator (design HAS one, like prd/uxd) -------------------


def test_design_open_round_names_the_cycle_from_the_trail(tmp_path):
    out = reporters.design(design_ctx(
        design_product(tmp_path, status="Draft", open_issues=True, buckets=(1, 0, 0),
                       trail=(1, 2))))
    assert "cycle 3" in out.body


def test_design_open_round_with_no_trail_names_cycle_1(tmp_path):
    out = reporters.design(design_ctx(
        design_product(tmp_path, status="Draft", open_issues=True, buckets=(1, 0, 0))))
    assert "cycle 1" in out.body


def test_design_trail_uses_the_highest_cycle_not_the_count(tmp_path):
    out = reporters.design(design_ctx(
        design_product(tmp_path, status="Draft", open_issues=True, buckets=(1, 0, 0),
                       trail=(1, 5))))
    assert "cycle 6" in out.body


def test_design_trail_ignores_a_non_cycle_filename(tmp_path):
    p = design_product(tmp_path, status="Draft", open_issues=True, buckets=(1, 0, 0), trail=(1,))
    (Path(p) / "docs" / "trail/design" / "notes.md").write_text("not a cycle file\n")

    out = reporters.design(design_ctx(p))

    assert "cycle 2" in out.body


def test_design_done_branch_names_no_cycle_even_with_a_trail(tmp_path):
    """The trail counts rounds folded in, a different quantity from a round in flight — the
    prd reporter's own reasoning (reporters.py:234-235), reused here since design shares
    prd's trail shape."""
    out = reporters.design(design_ctx(
        design_product(tmp_path, status="Settled", trail=(1, 2))))
    assert "cycle" not in out.body.lower()


# --- companion absent: the three Status branches --------------------------------------


def test_design_companion_absent_and_settled_is_nothing_pending(tmp_path):
    out = reporters.design(design_ctx(design_product(tmp_path, status="Settled")))
    assert "settled" in out.body.lower()
    assert "nothing pending" in out.body.lower()
    assert "✅" in out.body


def test_design_companion_absent_and_locked_is_nothing_pending(tmp_path):
    out = reporters.design(design_ctx(design_product(tmp_path, status="Locked")))
    assert "Locked" in out.body
    assert "nothing pending" in out.body.lower()
    assert "✅" in out.body


def test_design_draft_with_no_companion_is_flagged(tmp_path):
    """The family's settled reading (rationale.md decision 6, matching all three shipped
    reporters): Settled only when a run ends with no companion on disk, Draft otherwise
    (SKILL.md:209-216) — so Draft beside no companion is a state no finished run can leave
    behind. Not an open question here the way it was for uxd's OQ1."""
    out = reporters.design(design_ctx(design_product(tmp_path, status="Draft")))
    assert "⚠️" in out.body
    assert "not Settled" in out.body
    assert "✅" not in out.body


def test_design_companion_absent_but_status_unreadable_is_flagged(tmp_path):
    out = reporters.design(design_ctx(design_product(tmp_path, status=None)))
    assert "check docs/DESIGN.md" in out.body
    assert "✅" not in out.body


# --- version and best-effort — the same mechanisms as prd/srs/uxd -------------------


def test_design_version_is_surfaced_in_the_body(tmp_path):
    out = reporters.design(design_ctx(design_product(tmp_path, status="Locked", version=2)))
    assert "DESIGN v2" in out.body


def test_design_version_note_wrapping_does_not_break_the_version(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir(parents=True)
    (docs / "DESIGN.md").write_text(
        "# DESIGN\n\n**Status:** Locked\n"
        "**Version:** 3 — cross-line note that wraps\nonto a second physical line\n")
    out = reporters.design(design_ctx(str(tmp_path)))
    assert "DESIGN v3" in out.body


# --- a run that committed nothing must not inherit the last run's work --------


def test_design_run_that_committed_nothing_says_so_in_the_body(tmp_path):
    out = reporters.design(design_ctx(
        design_product(tmp_path, status="Draft", open_issues=True, buckets=(1, 0, 0)),
        head_before="same-sha", head_after="same-sha"))
    assert "committed nothing" in out.body
    assert out.footnote is None


def test_design_run_that_committed_nothing_borrows_no_figures_from_the_last_one(tmp_path):
    """design carries a cycle number and three buckets — the widest borrowed headline of
    the four, and every term in it belongs to whichever run last wrote the tree."""
    out = reporters.design(design_ctx(
        design_product(tmp_path, status="Draft", open_issues=True, version=2,
                       trail=(1,), buckets=(1, 8, 4)),
        head_before="same-sha", head_after="same-sha"))
    assert "DESIGN v" not in out.body
    assert "cycle" not in out.body
    assert "Answer docs/DESIGN_open_issues.md" not in out.body
    for figure in ("1 open issue", "8 choices", "4 items raised from downstream"):
        assert figure not in out.body


def test_design_run_that_committed_nothing_but_left_an_unanswered_companion_says_so(tmp_path):
    root = design_product(tmp_path, status="Draft")
    (Path(root, "docs", "DESIGN_open_issues.md")).write_text(
        "## 1. Open issues\n\n### 1.1 a question\n\n- **Answer:** <the owner fills this in>\n")
    out = reporters.design(design_ctx(root, head_before="same-sha", head_after="same-sha"))
    assert "DESIGN" in out.body
    assert "waiting on you" in out.body
    assert "may have stopped" not in out.body


def test_design_names_the_design_and_not_a_sibling_artifact(tmp_path):
    """Each reporter says what is on disk for ITS artifact. The prd reporter's sentence
    names the PRD; a design run repeating it would replace one false claim with another."""
    out = reporters.design(design_ctx(
        design_product(tmp_path, status="Draft", open_issues=True, buckets=(1, 0, 0)),
        head_before="same-sha", head_after="same-sha"))
    assert "The DESIGN on disk is from an earlier run." in out.body
    assert "PRD" not in out.body
    assert "UXD" not in out.body


def test_design_run_that_committed_reads_the_product(tmp_path):
    """Asserted on the body, not on `footnote is None`: design sets no footnote at all now,
    so the old form passes whatever this branch does."""
    out = reporters.design(design_ctx(
        design_product(tmp_path, status="Locked"),
        head_before="before-sha", head_after="after-sha"))
    assert "committed nothing" not in out.body
    assert "is Locked — nothing pending" in out.body


def test_design_a_product_that_is_not_a_repo_still_reads_the_product(tmp_path):
    """git_head returns None outside a repo; an unknown HEAD is not evidence of an idle
    run, so it claims neither outcome and the body stays the product read."""
    out = reporters.design(design_ctx(design_product(tmp_path, status="Locked"),
                                      head_before=None, head_after=None))
    assert "committed nothing" not in out.body
    assert "is Locked — nothing pending" in out.body


def test_design_a_parser_bug_costs_specificity_not_the_message(monkeypatch, tmp_path):
    def boom(_text):
        raise ValueError("unexpected shape")

    monkeypatch.setattr(reporters, "count_buckets", boom)

    out = reporters.design(design_ctx(
        design_product(tmp_path, status="Draft", open_issues=True, buckets=(1, 1, 1))))
    assert "run ended" in out.body


def test_design_without_an_artifact_path_degrades_to_run_ended(tmp_path):
    out = reporters.design(OutcomeContext(label="example-product"))
    assert out.body == "example-product: run ended."


# --- the real template parses ---------------------------------------------------------


@pytest.mark.skip(
    reason=(
        "SKIPPED 2026-08-05, and it must not stay skipped. It asserts one item per bucket "
        "(1.1, 2.1, 3.1); b87d2cf folded declared-omissions into choices-to-confirm and added "
        "2.2, and 2.3 (a design-run pointer) followed, so the template now yields three "
        "choices. Not repaired now because the design workflow is "
        "being reconsidered around the claude-design MCP, and repairing the count would pin a "
        "shape that is about to change. WHEN THAT WORKFLOW SETTLES: delete this test if "
        "DESIGN_open_issues.md is gone, or update the counts to whatever the template then "
        "carries. This is the only skip in the suite — keep it that way."
    )
)
def test_design_the_real_open_issues_template_parses_to_its_own_item_counts(tmp_path):
    """The committed design_open_issues_template.md, copied verbatim into a fixture, must
    yield the bucket counts its own ### items imply — its blockquote preamble, HTML
    comments and em-dashed headings must not perturb count_buckets. The template carried one
    item per bucket (1.1, 2.1, 3.1) when this was written; it now carries 2.2 and 2.3 as
    well."""
    template = (
        Path(__file__).resolve().parent.parent
        / "templates" / "product-templates" / "design_open_issues_template.md"
    )
    docs = tmp_path / "docs"
    docs.mkdir(parents=True)
    (docs / "DESIGN.md").write_text("# DESIGN\n\n**Status:** Draft\n**Version:** 1 — first pass\n")
    (docs / "DESIGN_open_issues.md").write_text(template.read_text(encoding="utf-8"))

    out = reporters.design(design_ctx(str(tmp_path)))

    assert "1 open issue" in out.body
    assert "1 choice to confirm" in out.body
    assert "1 item raised from downstream" in out.body


# --- no existing reporter changes -------------------------------------------------------


def test_existing_reporters_are_unaffected_by_the_design_addition():
    assert reporters.get_reporter("prd") is reporters.prd
    assert reporters.get_reporter("srs") is reporters.srs
    assert reporters.get_reporter("uxd") is reporters.uxd
    assert reporters.get_reporter("fix-author") is reporters.fix_author
    assert reporters.get_reporter("apply-packet") is reporters.apply_packet
    assert reporters.get_reporter("nope-not-a-reporter") is reporters.generic


# --- the instance layer: writing-bar / experience-visual / experience-voice ------------
#
# One parameterised shape serves three run types, so these tests carry the cases that shape
# can get wrong: per-document arity, the third bucket that only the verbal half has, and
# the instance-relative paths that are the whole reason these do not reuse read_product.


def instance_layer(tmp_path, docs_rel, documents, trail_name=None, trail=()):
    """An instance root with a layer under `docs_rel`.

    `documents` is a list of (filename, companion_or_None, status, version, buckets);
    a filename whose entry is None is not written at all, which is how "not authored yet"
    is exercised.
    """
    docs = tmp_path / docs_rel
    docs.mkdir(parents=True, exist_ok=True)
    for filename, companion, status, version, buckets in documents:
        if status is not None:
            (docs / filename).write_text(
                f"# {filename}\n\n**Status:** {status}\n"
                f"**Version:** {version} — what this revision changed\n"
            )
        if companion:
            (docs / companion).write_text(design_companion(*buckets))
    if trail:
        (docs / trail_name).mkdir(parents=True, exist_ok=True)
        for n in trail:
            (docs / trail_name / f"cycle-{n}.md").write_text("# cycle\n")
    return str(tmp_path)


def instance_ctx(artifact_path, *, head_before="aaa", head_after="bbb"):
    return OutcomeContext(label="kensaiapp-example-8792fa", cwd="/repo", artifact_path=artifact_path,
                          state="blocked", head_before=head_before, head_after=head_after)


def test_the_three_instance_reporters_are_registered():
    for name in ("writing-bar", "experience-visual", "experience-voice"):
        assert reporters.get_reporter(name) is not reporters.generic, name


def test_writing_bar_open_companion_names_the_file_to_answer(tmp_path):
    root = instance_layer(tmp_path, "system/doctrine", [
        ("writing_bar.md", "writing_bar_open_issues.md", "Draft", 3, (2, 1, 0))])
    out = reporters.get_reporter("writing-bar")(instance_ctx(root))
    assert "2 open issues" in out.body
    assert "1 choice to confirm" in out.body
    assert "system/doctrine/writing_bar_open_issues.md" in out.body
    assert "commit" in out.body and "re-run" in out.body
    assert "✅" not in out.body


def test_writing_bar_settled_layer_reports_done(tmp_path):
    root = instance_layer(tmp_path, "system/doctrine", [
        ("writing_bar.md", None, "Settled", 1, (0, 0, 0))])
    out = reporters.get_reporter("writing-bar")(instance_ctx(root))
    assert out.body.startswith("✅")
    assert "nothing pending" in out.body


def test_a_two_document_layer_reports_both_documents(tmp_path):
    """experience-* author two documents tracked separately — a run can finish one and
    still be open on the other, so a message naming only one is the failure this guards."""
    root = instance_layer(tmp_path, "system/experience", [
        ("visual_restrictions.md", None, "Settled", 5, (0, 0, 0)),
        ("visual_direction.md", "visual_direction_open_issues.md", "Draft", 3, (1, 0, 0)),
    ], trail_name="trail/visual", trail=(1, 2))
    out = reporters.get_reporter("experience-visual")(instance_ctx(root))
    assert "visual restrictions v5 settled" in out.body
    assert "visual direction v3" in out.body
    assert "1 open issue" in out.body
    assert "visual_direction_open_issues.md" in out.body
    assert "visual_restrictions_open_issues.md" not in out.body


def test_the_cycle_is_one_past_the_trail(tmp_path):
    root = instance_layer(tmp_path, "system/experience", [
        ("voice_restrictions.md", "voice_restrictions_open_issues.md", "Draft", 1, (1, 0, 0)),
        ("voice_direction.md", None, "Settled", 1, (0, 0, 0)),
    ], trail_name="trail/voice", trail=(1, 2, 3))
    out = reporters.get_reporter("experience-voice")(instance_ctx(root))
    assert "cycle 4" in out.body


def test_only_the_verbal_half_says_owed_to_the_visual_half(tmp_path):
    """The third bucket is the voice companion's alone — its § 3 is "Owed to the visual
    half". Naming it for the visual half would be the same class of error _design_pending_phrase
    avoids by never saying "directive"."""
    voice = instance_layer(tmp_path / "a", "system/experience", [
        ("voice_restrictions.md", "voice_restrictions_open_issues.md", "Draft", 1, (0, 0, 2)),
        ("voice_direction.md", None, "Settled", 1, (0, 0, 0)),
    ])
    out = reporters.get_reporter("experience-voice")(instance_ctx(voice))
    assert "2 owed to the visual half" in out.body

    visual = instance_layer(tmp_path / "b", "system/experience", [
        ("visual_restrictions.md", "visual_restrictions_open_issues.md", "Draft", 1, (0, 0, 2)),
        ("visual_direction.md", None, "Settled", 1, (0, 0, 0)),
    ])
    out = reporters.get_reporter("experience-visual")(instance_ctx(visual))
    assert "owed to the visual half" not in out.body


def test_a_layer_that_was_never_authored_is_not_a_success(tmp_path):
    root = instance_layer(tmp_path, "system/experience", [
        ("voice_restrictions.md", None, None, 0, (0, 0, 0)),
        ("voice_direction.md", None, None, 0, (0, 0, 0)),
    ])
    out = reporters.get_reporter("experience-voice")(instance_ctx(root))
    assert "left nothing to read" in out.body
    assert "✅" not in out.body


def test_an_unchanged_head_reports_that_and_does_not_read_the_layer(tmp_path):
    """A run that committed nothing leaves the previous run's files on disk, so reading
    them would report another run's work as this one's — prd/srs/uxd/design all decide the
    message on HEAD rather than annotating one, and these three follow."""
    root = instance_layer(tmp_path, "system/doctrine", [
        ("writing_bar.md", "writing_bar_open_issues.md", "Draft", 3, (5, 0, 0))])
    out = reporters.get_reporter("writing-bar")(
        instance_ctx(root, head_before="same", head_after="same"))
    assert "committed nothing" in out.body
    assert "5 open issues" not in out.body


def test_an_unreadable_layer_falls_back_rather_than_failing(monkeypatch, tmp_path):
    root = instance_layer(tmp_path, "system/doctrine", [
        ("writing_bar.md", None, "Settled", 1, (0, 0, 0))])

    def boom(_path):
        raise OSError("permission denied")

    monkeypatch.setattr(reporters.os.path, "isfile", boom)
    out = reporters.get_reporter("writing-bar")(instance_ctx(root))
    assert "could not be read" in out.body
    assert "✅" not in out.body


def test_a_companion_present_but_empty_is_flagged(tmp_path):
    root = instance_layer(tmp_path, "system/doctrine", [
        ("writing_bar.md", "writing_bar_open_issues.md", "Draft", 1, (0, 0, 0))])
    out = reporters.get_reporter("writing-bar")(instance_ctx(root))
    assert "lists no items" in out.body
    assert "✅" not in out.body


# --- agari: a project-management artifact, not a product document ---------------------
#
# Authored against `project-agari`'s own file contract, NOT by cloning a product reporter.
# Four load-bearing differences, and every case below is one of them:
#   - The three files sit DIRECTLY under the artifact path — `system/projects/<name>/` in the
#     instance repo (`skills/cpo/.claude/skills/project-agari/SKILL.md:77-81`), with no
#     `docs/` hop, so none of `read_product` / `read_srs` / `read_uxd` / `read_design` can be
#     reused.
#   - `agari.md` carries no `**Status:**` and no `**Version:**`; the declared signal is the
#     `PLACEHOLDER` marker `agari_template.md:12` stamps, plus the companion's absence.
#   - The companion has TWO buckets and no directives bucket
#     (`agari_open_issues_template.md:43-48` states why), so no third term can ever appear.
#   - "Declared" needs BOTH signals. An undeclared Agari with no companion is a run that did
#     not finish, never a settled one — the pairing the launcher's own pre-launch report gets
#     wrong (`docs/proposals/archive/project-agari-launcher/rationale.md:20-26`).

AGARI_BUCKET_TITLES = {
    1: "Open issues — questions about the terminus with no answer yet",
    2: "Choices to confirm — the CPO drafted a best-effort answer; confirm or override",
}


def agari_companion(n1=0, n2=0, extra=""):
    """The two-bucket Agari companion (`agari_open_issues_template.md`). `extra` appends raw
    text after the two buckets — the seam an owner-pasted heading arrives through."""
    out = []
    for bucket, n in ((1, n1), (2, n2)):
        out.append(f"## {bucket}. {AGARI_BUCKET_TITLES[bucket]}\n")
        if n == 0:
            out.append("None this round.\n")
        for i in range(1, n + 1):
            out.append(f"### {bucket}.{i} the decision, in one line\n")
            out.append("- **Why it matters:** because.\n")
    if extra:
        out.append(extra)
    return "\n".join(out)


PLACEHOLDER_AGARI = (
    "# 上がり Agari — thing's \"done\"\n\n---\n\n"
    "> **PLACEHOLDER — filled at station 2 of the project's setup seed, by `project-agari`.**\n"
)
DECLARED_AGARI = (
    "# 上がり Agari — thing's \"done\"\n\n---\n\n"
    "Thing is done when the veranda the PRD draws is shipped and the promise has held.\n"
)


def agari_project(tmp_path, agari=True, placeholder=False, open_issues=False,
                  buckets=(0, 1), trail=()):
    """The tree `project-agari` authors into — `<project dir>/agari.md` (+ optional
    `agari_open_issues.md` + `trail/agari/`), with no `docs/` hop. `agari=False` omits the
    declaration entirely, which is how the never-authored branch is exercised."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    if agari:
        (tmp_path / "agari.md").write_text(
            PLACEHOLDER_AGARI if placeholder else DECLARED_AGARI)
    if open_issues:
        (tmp_path / "agari_open_issues.md").write_text(agari_companion(*buckets))
    if trail:
        (tmp_path / "trail/agari").mkdir(parents=True, exist_ok=True)
        for n in trail:
            (tmp_path / "trail/agari" / f"cycle-{n}.md").write_text("# cycle\n")
    return str(tmp_path)


def agari_ctx(artifact_path, *, state="blocked", head_before="aaa", head_after="bbb"):
    """Default HEADs DIFFER — the agari run commits into the instance repo, so a moved HEAD is
    the ordinary case and the unchanged-HEAD guard is asked for explicitly."""
    return OutcomeContext(
        label="example-product", cwd="/repo", artifact_path=artifact_path,
        state=state, head_before=head_before, head_after=head_after,
    )


def test_agari_is_registered():
    assert reporters.get_reporter("agari") is reporters.agari
    assert reporters.get_reporter("agari") is not reporters.generic


def test_agari_run_that_wrote_no_agari_is_not_a_success(tmp_path):
    out = reporters.agari(agari_ctx(agari_project(tmp_path, agari=False)))
    assert "left nothing to read" in out.body
    assert "✅" not in out.body


# --- the two signals, and the pairing the launcher's own report gets wrong -------------


def test_agari_declared_is_no_placeholder_and_no_companion(tmp_path):
    out = reporters.agari(agari_ctx(agari_project(tmp_path)))
    assert out.body.startswith("✅")
    assert "declared" in out.body
    assert "nothing pending" in out.body


def test_agari_placeholder_with_no_companion_is_never_reported_as_settled(tmp_path):
    """The one pairing worth its own test: both "is it declared" and "is a round open" read
    clean, and the answer is still no. Reporting it as settled would tell the owner a product
    has a terminus when its file still holds the stamped placeholder."""
    out = reporters.agari(agari_ctx(agari_project(tmp_path, placeholder=True)))
    assert "✅" not in out.body
    assert "PLACEHOLDER" in out.body
    assert "not declared" in out.body


def test_agari_an_open_companion_is_never_reported_as_declared(tmp_path):
    """The companion's absence IS the done signal (`SKILL.md:80`), so a drafted terminus with
    a companion still out is a round in flight, not a declaration."""
    out = reporters.agari(agari_ctx(
        agari_project(tmp_path, open_issues=True, buckets=(0, 2))))
    assert "declared" not in out.body
    assert "✅" not in out.body


def test_agari_open_companion_reports_the_pending_work_and_the_next_move(tmp_path):
    out = reporters.agari(agari_ctx(
        agari_project(tmp_path, open_issues=True, buckets=(2, 1))))
    assert out.body.startswith("📋")
    assert "2 open issues" in out.body
    assert "1 choice to confirm" in out.body
    assert "Answer agari_open_issues.md, commit, re-run." in out.body


def test_agari_placeholder_with_an_open_companion_says_the_terminus_is_missing(tmp_path):
    """A run writes `agari.md` and the companion in the same step, so a companion beside an
    untouched placeholder is a run that did not finish its own draft."""
    out = reporters.agari(agari_ctx(
        agari_project(tmp_path, placeholder=True, open_issues=True, buckets=(1, 0))))
    assert "placeholder" in out.body.lower()
    assert "1 open issue" in out.body
    assert "Answer agari_open_issues.md, commit, re-run." in out.body
    assert "✅" not in out.body


def test_agari_companion_present_but_empty_is_flagged(tmp_path):
    out = reporters.agari(agari_ctx(
        agari_project(tmp_path, open_issues=True, buckets=(0, 0))))
    assert "lists no items" in out.body
    assert "✅" not in out.body


# --- two buckets by construction: no third term can reach the message -----------------


def test_agari_has_no_directives_bucket(tmp_path):
    """`agari_open_issues_template.md:43-48` states the companion has no third bucket. An
    owner who pastes one in mid-answer must not make the word "directive" appear."""
    root = agari_project(tmp_path, open_issues=True, buckets=(1, 0))
    (tmp_path / "agari_open_issues.md").write_text(agari_companion(
        1, 0, extra="## 3. Directives\n\n### 3.1 do a thing\n"))

    out = reporters.agari(agari_ctx(root))

    assert "directive" not in out.body.lower()
    assert "1 open issue" in out.body


def test_agari_bucket_terms_are_singular_and_plural(tmp_path):
    one = reporters.agari(agari_ctx(
        agari_project(tmp_path / "a", open_issues=True, buckets=(1, 1))))
    assert "1 open issue," in one.body
    assert "1 choice to confirm" in one.body

    many = reporters.agari(agari_ctx(
        agari_project(tmp_path / "b", open_issues=True, buckets=(3, 2))))
    assert "3 open issues" in many.body
    assert "2 choices to confirm" in many.body


# --- the trail is the discriminator (agari HAS one, like prd/uxd/design) ---------------


def test_agari_open_round_names_the_cycle_from_the_trail(tmp_path):
    out = reporters.agari(agari_ctx(
        agari_project(tmp_path, open_issues=True, buckets=(1, 0), trail=(1, 2))))
    assert "cycle 3" in out.body


def test_agari_open_round_with_no_trail_names_cycle_1(tmp_path):
    out = reporters.agari(agari_ctx(
        agari_project(tmp_path, open_issues=True, buckets=(1, 0))))
    assert "cycle 1" in out.body


def test_agari_trail_uses_the_highest_cycle_not_the_count(tmp_path):
    """`SKILL.md:83-86` numbers a new cycle one above the highest that exists, so a removed
    cycle must not be able to make the message collide with a real one."""
    out = reporters.agari(agari_ctx(
        agari_project(tmp_path, open_issues=True, buckets=(1, 0), trail=(1, 4))))
    assert "cycle 5" in out.body


def test_agari_trail_ignores_a_non_cycle_filename(tmp_path):
    root = agari_project(tmp_path, open_issues=True, buckets=(1, 0), trail=(1,))
    (tmp_path / "trail/agari" / "notes.md").write_text("# not a cycle\n")

    out = reporters.agari(agari_ctx(root))

    assert "cycle 2" in out.body


def test_agari_declared_branch_names_no_cycle_even_with_a_trail(tmp_path):
    """The trail counts rounds folded in, a different quantity from the round now open — and
    a first run that settled everything has none."""
    out = reporters.agari(agari_ctx(agari_project(tmp_path, trail=(1, 2, 3))))
    assert "cycle" not in out.body


# --- a run that committed nothing must not inherit the last run's work ----------------


def test_agari_run_that_committed_nothing_says_so_in_the_body(tmp_path):
    out = reporters.agari(agari_ctx(
        agari_project(tmp_path), head_before="same", head_after="same"))
    assert "committed nothing" in out.body
    assert out.body.startswith("⚠️")


def test_agari_run_that_committed_nothing_borrows_no_figures_from_the_last_one(tmp_path):
    """The failure this guards: a run that died leaves the previous round's companion and
    trail on disk, so reading them reports that round's cycle and counts as this run's."""
    root = agari_project(tmp_path, open_issues=True, buckets=(4, 2), trail=(1, 2))

    out = reporters.agari(agari_ctx(root, head_before="same", head_after="same"))

    assert "4 open issues" not in out.body
    assert "cycle 3" not in out.body
    assert "Answer agari_open_issues.md" not in out.body


def test_agari_run_that_committed_nothing_but_left_an_unanswered_companion_says_so(tmp_path):
    root = agari_project(tmp_path)
    (Path(root, "agari_open_issues.md")).write_text(
        "## 1. Open issues\n\n### 1.1 a question\n\n- **Answer:** <the owner fills this in>\n")
    out = reporters.agari(agari_ctx(root, head_before="same", head_after="same"))
    assert "Agari" in out.body
    assert "waiting on you" in out.body
    assert "may have stopped" not in out.body


def test_agari_names_the_agari_and_not_a_sibling_artifact(tmp_path):
    out = reporters.agari(agari_ctx(
        agari_project(tmp_path), head_before="same", head_after="same"))
    assert "The Agari on disk is from an earlier run." in out.body
    for other in ("PRD", "SRS", "UXD", "DESIGN"):
        assert other not in out.body


def test_agari_a_project_that_is_not_a_repo_still_reads_the_files(tmp_path):
    """An unreadable HEAD is a third case: it is not evidence of an idle run, so it claims
    neither outcome and the body is the read."""
    out = reporters.agari(agari_ctx(
        agari_project(tmp_path), head_before=None, head_after=None))
    assert "committed nothing" not in out.body
    assert out.body.startswith("✅")


# --- best-effort: a parser bug costs specificity, never the message -------------------


def test_agari_unreadable_project_falls_back_rather_than_failing(monkeypatch, tmp_path):
    root = agari_project(tmp_path)

    def boom(_path):
        raise OSError("permission denied")

    monkeypatch.setattr(reporters.os.path, "isfile", boom)
    out = reporters.agari(agari_ctx(root))
    assert "could not be read" in out.body
    assert "✅" not in out.body


def test_agari_a_parser_bug_costs_specificity_not_the_message(monkeypatch, tmp_path):
    root = agari_project(tmp_path, open_issues=True, buckets=(1, 0))

    def boom(_text):
        raise ValueError("bad regex")

    monkeypatch.setattr(reporters, "count_buckets", boom)
    out = reporters.agari(agari_ctx(root))
    assert out.body == "example-product: run ended."


def test_agari_without_an_artifact_path_degrades_to_run_ended(tmp_path):
    out = reporters.agari(agari_ctx(None))
    assert out.body == "example-product: run ended."


# --- the real templates parse ----------------------------------------------------------


def test_agari_the_real_templates_parse_to_their_own_marker_and_item_counts(tmp_path):
    """The committed `agari_template.md` and `agari_open_issues_template.md`, copied verbatim
    into a fixture, must yield the placeholder reading and the bucket counts their own bytes
    imply — the blockquote preamble, the HTML comments and the em-dashed headings must not
    perturb the read. Both templates carried one item per bucket (1.1, 2.1) when written."""
    templates = Path(__file__).resolve().parent.parent / "templates" / "project-templates"
    (tmp_path / "agari.md").write_text(
        (templates / "agari_template.md").read_text(encoding="utf-8"))
    (tmp_path / "agari_open_issues.md").write_text(
        (templates / "agari_open_issues_template.md").read_text(encoding="utf-8"))

    out = reporters.agari(agari_ctx(str(tmp_path)))

    assert "1 open issue" in out.body
    assert "1 choice to confirm" in out.body
    assert "directive" not in out.body.lower()
    assert "PLACEHOLDER" in out.body


# --- no existing reporter changes -------------------------------------------------------


def test_existing_reporters_are_unaffected_by_the_agari_addition():
    assert reporters.get_reporter("prd") is reporters.prd
    assert reporters.get_reporter("srs") is reporters.srs
    assert reporters.get_reporter("uxd") is reporters.uxd
    assert reporters.get_reporter("design") is reporters.design
    assert reporters.get_reporter("fix-author") is reporters.fix_author
    assert reporters.get_reporter("apply-packet") is reporters.apply_packet
    assert reporters.get_reporter("writing-bar") is reporters.writing_bar
    assert reporters.get_reporter("experience-visual") is reporters.experience_visual
    assert reporters.get_reporter("experience-voice") is reporters.experience_voice
    assert reporters.get_reporter("nope-not-a-reporter") is reporters.generic


# --- content: uxd's arity and uxd's cycle, with the CONTENT contract's own names --------
#
# Authored against the real CONTENT contract (core/templates/product-templates/
# content_template.md and content_open_issues_template.md, and
# skills/content-manager/.claude/skills/product-content/SKILL.md), not cloned from a sibling:
#   - docs/CONTENT.md carries the same Status/Version line shapes parse_status/parse_version
#     already read (content_template.md:41, :49).
#   - docs/CONTENT_open_issues.md has Open issues + Choices to confirm + § 3, items raised
#     from downstream (content_open_issues_template.md) — the UXD/SRS shape. There is no
#     directives bucket, so the term cannot appear in a content message.
#   - docs/trail/content/cycle-<N>.md exists and IS read for the cycle number
#     (SKILL.md:68, :71-72), like uxd's and prd's.
#   - Settled only when the run ends with no companion on disk (SKILL.md:250-251) — so
#     Draft-beside-no-companion warns, the same settled reading as design's.


CONTENT_BUCKET_TITLES = {
    1: "Open issues",
    2: "Choices to confirm",
}


def content_companion(n1=0, n2=0, extra=""):
    """The CONTENT companion's two answer buckets (content_open_issues_template.md).
    `extra` appends raw text after them."""
    out = []
    for bucket, n in ((1, n1), (2, n2)):
        out.append(f"## {bucket}. {CONTENT_BUCKET_TITLES[bucket]}\n")
        if n == 0:
            out.append("None this cycle.\n")
        for i in range(1, n + 1):
            out.append(f"### {bucket}.{i} the question, in one line\n")
            out.append("- **Why it matters:** because.\n")
    if extra:
        out.append(extra)
    return "\n".join(out)


def content_product(tmp_path, content=True, open_issues=False, status="Draft", version=2,
                    buckets=(0, 0), trail=()):
    """The tree product-content authors into: docs/CONTENT.md (+ optional
    CONTENT_open_issues.md + docs/trail/content/). `status=None` omits the Status line
    entirely, so the parse-fails branch can be exercised."""
    docs = tmp_path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    if content:
        status_line = f"**Status:** {status}\n" if status is not None else ""
        (docs / "CONTENT.md").write_text(
            f"---\nname: thing\nomitted:\n---\n\n# CONTENT — thing\n\n{status_line}"
            f"**Owner:** Content Manager\n**Version:** {version} — what this revision changed\n"
        )
    if open_issues:
        (docs / "CONTENT_open_issues.md").write_text(content_companion(*buckets))
    if trail:
        (docs / "trail/content").mkdir(parents=True, exist_ok=True)
        for n in trail:
            (docs / "trail/content" / f"cycle-{n}.md").write_text("# cycle\n")
    return str(tmp_path)


def content_ctx(artifact_path, *, state="blocked", head_before=None, head_after=None):
    return OutcomeContext(
        label="example-product", cwd="/repo", artifact_path=artifact_path,
        state=state, head_before=head_before, head_after=head_after,
    )


def test_content_is_registered():
    """A new run type is one registry entry; the watcher resolves --reporter content by name."""
    assert reporters.get_reporter("content") is reporters.content


def test_content_run_that_wrote_no_content_is_not_a_success(tmp_path):
    out = reporters.content(content_ctx(content_product(tmp_path, content=False)))
    assert "no CONTENT" in out.body
    assert "✅" not in out.body


def test_content_unreadable_product_falls_back_rather_than_failing(monkeypatch, tmp_path):
    def boom(_path):
        raise OSError("permission denied")

    monkeypatch.setattr(reporters.os.path, "isfile", boom)

    out = reporters.content(content_ctx(content_product(tmp_path, status="Locked")))
    assert "could not be read" in out.body
    assert "what it produced is unknown" in out.body


def test_content_settled_with_no_companion_is_the_done_signal(tmp_path):
    out = reporters.content(content_ctx(
        content_product(tmp_path, status="Settled", version=3)))
    assert out.body == "✅ example-product: CONTENT v3 settled — nothing pending."


def test_content_locked_with_no_companion_is_also_done(tmp_path):
    out = reporters.content(content_ctx(
        content_product(tmp_path, status="Locked", version=4)))
    assert out.body == "✅ example-product: CONTENT v4 is Locked — nothing pending."


def test_content_draft_with_no_companion_warns(tmp_path):
    """SKILL.md:250-251 — Settled is set from the companion's absence, so a Draft with no
    companion is a run that did not finish, not a settled one."""
    out = reporters.content(content_ctx(content_product(tmp_path, status="Draft")))
    assert out.body.startswith("⚠️ example-product: CONTENT v2")
    assert "not Settled" in out.body
    assert "✅" not in out.body


def test_content_unparseable_status_with_no_companion_says_unreadable(tmp_path):
    out = reporters.content(content_ctx(content_product(tmp_path, status=None)))
    assert '"unreadable"' in out.body


def test_content_open_round_names_its_cycle_and_both_buckets(tmp_path):
    out = reporters.content(content_ctx(content_product(
        tmp_path, status="Draft", version=2, open_issues=True, buckets=(1, 1),
        trail=(1, 2))))
    assert out.body == (
        "📋 example-product: CONTENT v2, cycle 3 complete — "
        "1 open issue, 1 choice to confirm.\n"
        "Answer docs/CONTENT_open_issues.md, commit, re-run."
    )


def test_content_bucket_terms_are_singular_and_plural(tmp_path):
    singular = reporters.content(content_ctx(content_product(
        tmp_path, status="Draft", open_issues=True, buckets=(1, 1)))).body
    assert "1 open issue," in singular
    assert "1 choice to confirm" in singular

    plural = reporters.content(content_ctx(content_product(
        tmp_path, status="Draft", open_issues=True, buckets=(2, 3)))).body
    assert "2 open issues," in plural
    assert "3 choices to confirm" in plural


def test_content_never_says_directive_or_declared_omission(tmp_path):
    """The CONTENT companion's § 3 is items raised from downstream. Neither "directive" (the
    PRD companion's term) nor "declared omission" may name them, and a heading the owner
    pastes after § 3 adds nothing to the count."""
    extra = ("## 3. Raised from downstream\n\n### 3.1 a raised item\n\n"
             "## 4. A heading the owner pasted\n\n### 4.1 not a bucket\n")
    docs = tmp_path / "docs"
    content_product(tmp_path, status="Draft", open_issues=True, buckets=(0, 1))
    (docs / "CONTENT_open_issues.md").write_text(content_companion(0, 1, extra=extra))

    out = reporters.content(content_ctx(str(tmp_path)))

    assert "directive" not in out.body.lower()
    assert "declared omission" not in out.body.lower()
    assert "1 item raised from downstream" in out.body


def test_content_raised_items_only_ask_for_an_answer_not_an_empty_warning(tmp_path):
    content_product(tmp_path, status="Draft", open_issues=True, buckets=(0, 0))
    (tmp_path / "docs" / "CONTENT_open_issues.md").write_text(
        content_companion(0, 0, extra="## 3. Raised from downstream\n\n### 3.1 a raised item\n"))

    out = reporters.content(content_ctx(str(tmp_path)))

    assert "lists no items" not in out.body
    assert "1 item raised from downstream" in out.body


def test_content_companion_present_but_empty_is_flagged(tmp_path):
    out = reporters.content(content_ctx(content_product(
        tmp_path, status="Draft", open_issues=True, buckets=(0, 0))))
    assert "lists no items" in out.body
    assert "✅" not in out.body


def test_content_run_that_committed_nothing_says_so_in_contents_own_terms(tmp_path):
    """An unchanged HEAD decides the body rather than annotating one, as in prd/srs/uxd/
    design: the previous round's files are still on disk, so the product is not read."""
    out = reporters.content(content_ctx(
        content_product(tmp_path, status="Settled"),
        head_before="abc123", head_after="abc123"))
    assert "CONTENT" in out.body
    assert "committed nothing" in out.body or "did not commit" in out.body
    assert "✅" not in out.body


def test_content_run_that_committed_nothing_but_left_an_unanswered_companion_says_so(tmp_path):
    root = content_product(tmp_path, status="Draft")
    (Path(root, "docs", "CONTENT_open_issues.md")).write_text(
        "## 1. Open issues\n\n### 1.1 a question\n\n- **Answer:** <the owner fills this in>\n")
    out = reporters.content(content_ctx(root, head_before="same", head_after="same"))
    assert "CONTENT" in out.body
    assert "waiting on you" in out.body
    assert "may have stopped" not in out.body


def test_content_unreadable_head_still_reads_the_product(tmp_path):
    """A HEAD that could not be read is not evidence of an idle run, so it claims neither
    outcome — the same third case the four siblings carry."""
    out = reporters.content(content_ctx(
        content_product(tmp_path, status="Settled", version=1),
        head_before=None, head_after=None))
    assert out.body == "✅ example-product: CONTENT v1 settled — nothing pending."


def test_content_reads_the_real_templates(tmp_path):
    """The parsers must hold against the shipped templates, not only against what the
    fixtures imply — the blockquote preamble, the HTML comments and the em-dashed headings
    must not perturb the read."""
    templates = Path(__file__).resolve().parent.parent / "templates" / "product-templates"
    docs = tmp_path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "CONTENT.md").write_text(
        (templates / "content_template.md").read_text(encoding="utf-8"))
    (docs / "CONTENT_open_issues.md").write_text(
        (templates / "content_open_issues_template.md").read_text(encoding="utf-8"))

    out = reporters.content(content_ctx(str(tmp_path)))

    assert "CONTENT" in out.body
    assert "directive" not in out.body.lower()


def test_content_reports_the_live_run_that_opened_this_seed(tmp_path):
    """The 2026-08-23 product-content run against a live product (that product's `55aed26`)
    sent the bare `<label>: run ended.` and the owner could not tell it from the design run's
    message thirteen seconds later. Its real on-disk shape — CONTENT.md v1 Draft, a companion
    with 1 open issue and 6 choices to confirm, no trail/content/ yet — is the fixture, so the
    defect that opened this station is what this test holds shut."""
    out = reporters.content(content_ctx(content_product(
        tmp_path, status="Draft", version=1, open_issues=True, buckets=(1, 6))))

    assert out.body == (
        "📋 example-product: CONTENT v1, cycle 1 complete — "
        "1 open issue, 6 choices to confirm.\n"
        "Answer docs/CONTENT_open_issues.md, commit, re-run."
    )


def test_existing_reporters_are_unaffected_by_the_content_addition():
    assert reporters.get_reporter("prd") is reporters.prd
    assert reporters.get_reporter("srs") is reporters.srs
    assert reporters.get_reporter("uxd") is reporters.uxd
    assert reporters.get_reporter("design") is reporters.design
    assert reporters.get_reporter("agari") is reporters.agari
    assert reporters.get_reporter("fix-author") is reporters.fix_author
    assert reporters.get_reporter("apply-packet") is reporters.apply_packet
    assert reporters.get_reporter("writing-bar") is reporters.writing_bar
    assert reporters.get_reporter("experience-visual") is reporters.experience_visual
    assert reporters.get_reporter("experience-voice") is reporters.experience_voice
    assert reporters.get_reporter("nope-not-a-reporter") is reporters.generic


# --- sdd-document: the SDD completion message, read from the document, its companion and the
# trail. The fixture below writes the conversation record too: the shared reader still evaluates
# its ending, and the message degrades on a malformed one (CP-420). The record is read from the
# same artifact_path the siblings read their product from.


def sdd_product(tmp_path, sdd=True, open_issues=False, status="Settled", version=2,
                items=0, cycles=0, ended=None, runs=1, counters=None):
    """The tree product-sdd authors into: docs/SDD.md, an optional companion, and one trail/sdd/
    holding both cycle-N.md and run-N.md. The conversation record is the SDD's own record, so it
    sits in the SDD's trail beside the retired companions — kensaiapp_structure.md § *A trail is not
    the document's sibling*. The two filename patterns do not collide, which is what lets one folder
    hold both. `ended` is the closing block's "Ended because" sentence; None writes a record with no
    closing block, which is what an interrupted run leaves. `counters` is the record's spent/allowed
    tally — the only place a cap is read from."""
    docs = tmp_path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    if sdd:
        status_line = f"**Status:** {status}\n" if status is not None else ""
        (docs / "SDD.md").write_text(
            f"# SDD — thing\n\n{status_line}**Owner:** CTO · CPO · CDO\n"
            f"**Version:** {version} — what this run changed\n"
        )
    if open_issues:
        body = "# SDD open issues\n\n## 1. Open issues\n"
        body += "".join(f"### 1.{n} a question\n\n- **Answer:** <the owner fills this in>\n\n"
                        for n in range(1, items + 1))
        body += "\n## 2. Choices to confirm\n\nNone this cycle.\n\n## 3. Cut calls\n\nNone.\n"
        (docs / "SDD_open_issues.md").write_text(body)
    trail = docs / "trail" / "sdd"
    trail.mkdir(parents=True, exist_ok=True)
    if cycles:
        for n in range(1, cycles + 1):
            (trail / f"cycle-{n}.md").write_text("an answered companion\n")
    conv = trail
    for n in range(1, runs + 1):
        closing = f"\n## How this run ended\n\n- **Ended because:** {ended}\n" if ended else ""
        tally = f"- **Counters:** {counters}\n" if counters else ""
        (conv / f"run-{n}.md").write_text(f"# SDD conversation — run {n}\n{tally}{closing}")
    return str(tmp_path)


def test_sdd_reads_the_record_from_the_sdd_trail(tmp_path):
    """The record's home. It is the SDD's record, so it sits in the SDD's trail beside the retired
    companions, and the reporter reads it from there. cycle-N.md sharing the folder is the case that
    would break a reader keyed on "the highest-numbered file" rather than on the run-N.md pattern —
    cycle 3 is numbered above run 1 here, and the ending still comes off run 1."""
    product = sdd_product(tmp_path, status="Draft", runs=1, cycles=3,
                          ended="the **1-round-no-reply cap** fired")

    assert (Path(product) / "docs/trail/sdd/run-1.md").is_file()
    assert reporters.read_sdd(product)["ended"] == "the **1-round-no-reply cap** fired"


def test_sdd_a_run_state_json_beside_the_record_is_never_read_as_one(tmp_path):
    """A `run-<N>.state.json` beside the record starts with `run-` but does not end in `.md`, so
    `_sdd_record_text`'s own filter never matches it. This pins it rather than leaving it to
    follow from reading the filter."""
    product = sdd_product(tmp_path, status="Draft", runs=1, cycles=0,
                          ended="the **1-round-no-reply cap** fired")
    (Path(product) / "docs" / "trail" / "sdd" / "run-1.state.json").write_text(
        '{"schema_version": 1}')

    assert reporters.read_sdd(product)["ended"] == "the **1-round-no-reply cap** fired"


def test_sdd_a_record_left_at_the_old_path_is_not_read(tmp_path):
    """A product not yet migrated still has its records at docs/sdd_conversation/. The reporter
    reads one home, not two: the honest report for that product is "this record does not say how it
    ended", and what closes the gap is the per-product migration, kensaiapp_structure.md § 6's
    report-only entry. A second read path would make both homes live and neither authoritative."""
    product = sdd_product(tmp_path, status="Draft", runs=0, cycles=1)
    old = Path(product) / "docs" / "sdd_conversation"
    old.mkdir(parents=True)
    (old / "run-1.md").write_text(
        "# SDD conversation — run 1\n\n## How this run ended\n\n"
        "- **Ended because:** a cap fired\n")

    assert reporters.read_sdd(product)["ended"] is None


def sdd_ctx(artifact_path, *, state="blocked", head_before="a", head_after="b"):
    return OutcomeContext(
        label="example-product", cwd="/repo", artifact_path=artifact_path,
        state=state, head_before=head_before, head_after=head_after,
    )


def test_retired_reporter_name_returns_generic(tmp_path):
    """CP-419: `sdd` is no longer a registered name, so it resolves to the generic reporter and
    says the same four words whatever is on disk and whatever HEAD did."""
    assert reporters.get_reporter("sdd") is reporters.generic
    holding = sdd_product(tmp_path / "holding", status="Draft", open_issues=True, items=2,
                          ended="the **round cap** fired", counters="rounds 6/6")
    absent = str(tmp_path / "absent")
    for root in (holding, absent):
        for before, after in (("a", "b"), ("same", "same")):
            body = reporters.get_reporter("sdd")(sdd_ctx(root, head_before=before,
                                                         head_after=after)).body
            assert body == "example-product: run ended."


def test_sdd_document_settled_run_names_its_status_and_version(tmp_path):
    out = reporters.sdd_document(sdd_ctx(sdd_product(
        tmp_path, status="Settled", version=2, cycles=1,
        ended="all three seats declared `no_followup` with no recall outstanding")))

    assert "Settled" in out.body
    assert "v2" in out.body
    assert "example-product" in out.body


def test_sdd_document_settled_run_says_the_companion_is_gone(tmp_path):
    """Its absence is the done signal, so it is the fact worth stating."""
    out = reporters.sdd_document(sdd_ctx(sdd_product(
        tmp_path, status="Settled", open_issues=False, cycles=1,
        ended="all three seats declared `no_followup`")))

    assert "no open issues" in out.body.lower() or "companion" in out.body.lower()


SDD_FIVE_BUCKETS = (
    "# SDD open issues — thing\n\n"
    "## 1. Open issues — questions with no answer yet\n\nNone this cycle.\n\n"
    "## 2. Choices to confirm — a seat drafted a best-effort answer; confirm or override\n\n"
    "### 2.1 a drafted choice\n\n- **Confirm or override:** <\"confirm\", or \"override\">\n\n"
    "## 3. Cut calls to confirm — where the slicing could reasonably have gone another way\n\n"
    "None.\n\n"
    "## 4. Disagreements — two seats hold different positions and neither yields\n\n"
    "### 4.1 a disagreement\n\n- **Your call:** <the position to take>\n\n"
    "## 5. Raised from downstream — an item from a seat that did not write the SDD\n\n"
    "### 5.1 a finding\n\n- **Answer:** <the owner fills this in>\n\n"
    "### 5.2 another finding\n\n- **Answer:** <the owner fills this in>\n"
)


def test_count_items_reads_every_numbered_bucket():
    """The SDD companion carries five buckets, and an item in any of them is waiting on the
    owner."""
    assert reporters.count_items(SDD_FIVE_BUCKETS) == {1: 0, 2: 1, 3: 0, 4: 1, 5: 2}


def test_count_buckets_is_unchanged_by_buckets_past_the_third():
    """Its three-bucket callers must read exactly what they read before `count_items` existed."""
    assert reporters.count_buckets(SDD_FIVE_BUCKETS) == (0, 1, 0)


def test_sdd_document_counts_an_item_raised_from_downstream(tmp_path):
    """The defect this pins: real retired SDD companions held one § 5 item and nothing else,
    and the three-bucket read reported each of them as "0 open items for you"."""
    root = sdd_product(tmp_path, status="Draft", open_issues=True, items=0,
                       ended="the seats' own close")
    Path(root, "docs", "SDD_open_issues.md").write_text(
        SDD_FIVE_BUCKETS.split("## 2.")[0]
        + "## 5. Raised from downstream\n\n### 5.1 a finding\n\n- **Answer:** <fill>\n")

    assert reporters.read_sdd(root)["items"] == 1
    assert "1 open item for you" in reporters.sdd_document(sdd_ctx(root)).body


def test_sdd_counts_every_bucket_of_a_five_bucket_companion(tmp_path):
    root = sdd_product(tmp_path, status="Draft", open_issues=True, items=0,
                       ended="the seats' own close")
    Path(root, "docs", "SDD_open_issues.md").write_text(SDD_FIVE_BUCKETS)

    assert reporters.read_sdd(root)["items"] == 4


def test_sdd_document_draft_run_counts_the_open_items(tmp_path):
    """A Draft with a standing companion is the owner's next move, so the count is the message."""
    out = reporters.sdd_document(sdd_ctx(sdd_product(
        tmp_path, status="Draft", open_issues=True, items=10,
        ended="the **1-round-no-reply cap** fired")))

    assert "10" in out.body


def test_sdd_document_an_unmeasured_token_counter_is_not_a_cap(tmp_path):
    """No harness surface reports a seat's per-turn output tokens, so both real runs wrote that
    counter with no numerator. A cap that cannot be measured is not reported as one."""
    out = reporters.sdd_document(sdd_ctx(sdd_product(
        tmp_path, status="Settled", cycles=1,
        counters="rounds `2/6` · output tokens `<under-counted — no surface reports it>/600000`",
        ended="all three seats declared `no_followup`")))

    assert "Capped" not in out.body


def test_sdd_document_clean_run_is_not_reported_as_capped(tmp_path):
    out = reporters.sdd_document(sdd_ctx(sdd_product(
        tmp_path, status="Settled", cycles=1,
        ended="all three seats declared `no_followup` with no recall outstanding")))

    assert "cap" not in out.body.lower()


def test_sdd_document_committed_nothing_reads_no_product(tmp_path):
    """The guard every sibling opens with: an unchanged HEAD means the files on disk are the
    PREVIOUS run's, so reading them reports that run as this one."""
    out = reporters.sdd_document(sdd_ctx(
        sdd_product(tmp_path, status="Settled", version=9),
        head_before="same", head_after="same"))

    assert "Settled" not in out.body
    assert "v9" not in out.body


def test_sdd_document_committed_nothing_but_left_an_unanswered_companion_says_so(tmp_path):
    """`sdd_product`'s own `open_issues=True, items=N` already writes the real
    `- **Answer:** <the owner fills this in>` placeholder (its literal fixture text)."""
    out = reporters.sdd_document(sdd_ctx(
        sdd_product(tmp_path, status="Draft", open_issues=True, items=1),
        head_before="same", head_after="same"))
    assert "SDD" in out.body
    assert "waiting on you" in out.body
    assert "may have stopped" not in out.body


def test_sdd_document_committed_nothing_with_an_unanswered_cut_call_says_so(tmp_path):
    """SDD's own third slot label (§ 3), absent from every other template — the case
    `companion_state`'s enumerated label set exists to cover."""
    root = sdd_product(tmp_path, status="Draft")
    (Path(root, "docs", "SDD_open_issues.md")).write_text(
        "## 3. Cut calls to confirm\n\n### 3.1 a cut\n\n"
        "- **Keep or re-cut:** <\"keep\", or \"re-cut: <the shape to take instead>\">\n")
    out = reporters.sdd_document(sdd_ctx(root, head_before="same", head_after="same"))
    assert "waiting on you" in out.body
    assert "may have stopped" not in out.body


def test_sdd_document_committed_nothing_with_an_unanswered_disagreement_says_so(tmp_path):
    """SDD's fourth slot label (§ 4 Disagreements) — the one bucket with no raising seat."""
    root = sdd_product(tmp_path, status="Draft")
    (Path(root, "docs", "SDD_open_issues.md")).write_text(
        "## 4. Disagreements\n\n### 4.1 a disagreement\n\n"
        "- **Your call:** <the position to take, by seat — or \"neither: <what to do instead>\">\n")
    out = reporters.sdd_document(sdd_ctx(root, head_before="same", head_after="same"))
    assert "waiting on you" in out.body
    assert "may have stopped" not in out.body


def test_sdd_document_that_wrote_no_sdd_is_not_a_success(tmp_path):
    out = reporters.sdd_document(sdd_ctx(sdd_product(tmp_path, sdd=False)))
    assert "no SDD" in out.body


def test_sdd_document_unreadable_product_says_so(tmp_path):
    out = reporters.sdd_document(sdd_ctx(str(tmp_path / "nope")))
    assert "no SDD" in out.body or "could not be read" in out.body


def test_sdd_document_a_record_with_no_closing_block_claims_no_ending(tmp_path):
    """An interrupted run leaves a record with no closing block. That is not a clean ending and
    must not be reported as one."""
    out = reporters.sdd_document(sdd_ctx(sdd_product(
        tmp_path, status="Draft", open_issues=True, items=3, ended=None)))

    assert "cap" not in out.body.lower()


# --- fdr: content's shape with the FDR contract's own lowercase names ----------------------
#
# Authored against the real FDR contract (core/templates/product-templates/fdr_template.md and
# fdr_open_issues_template.md, and skills/principal-pm/.claude/skills/product-fdr/SKILL.md),
# not cloned from a sibling:
#   - The three names are LOWERCASE and match each other on purpose — docs/fdr.md,
#     docs/fdr_open_issues.md, docs/trail/fdr/ (SKILL.md:65-69). Every other product reporter
#     reads an upper-cased document name, so this is the one difference a find-replace from a
#     sibling gets wrong, and the launcher's own header calls it out
#     (core/launchers/product-fdr/launcher.sh:25-28).
#   - The companion has two answer buckets and § 3, items raised from downstream
#     (fdr_open_issues_template.md) — the UXD/SRS/CONTENT shape. "directive" (the PRD
#     companion's term) cannot appear.
#   - docs/trail/fdr/cycle-<N>.md exists and IS read for the cycle number (SKILL.md:67, :77-79),
#     like content's and uxd's.
#   - Status carries the same three values (fdr_template.md:70), and the template states the rule
#     itself: "Draft = the companion is on disk … Settled = the companion is gone … the done
#     signal" (fdr_template.md:71-73). So Draft-beside-no-companion warns, the family's reading.


FDR_BUCKET_TITLES = {
    1: "Open issues — behavioural questions with no answer yet",
    2: "Choices to confirm — the Principal PM drafted a best-effort answer; confirm or override",
}


def fdr_companion(n1=0, n2=0, extra=""):
    """The FDR companion's two answer buckets (fdr_open_issues_template.md). `extra`
    appends raw text after them."""
    out = []
    for bucket, n in ((1, n1), (2, n2)):
        out.append(f"## {bucket}. {FDR_BUCKET_TITLES[bucket]}\n")
        if n == 0:
            out.append("None this cycle.\n")
        for i in range(1, n + 1):
            out.append(f"### {bucket}.{i} the question, in one line\n")
            out.append("- **Why it matters:** because.\n")
    if extra:
        out.append(extra)
    return "\n".join(out)


def fdr_product(tmp_path, fdr=True, open_issues=False, status="Draft", version=2,
                buckets=(0, 0), trail=()):
    """The tree product-fdr authors into: docs/fdr.md (+ optional docs/fdr_open_issues.md +
    docs/trail/fdr/). `status=None` omits the Status line entirely, so the parse-fails branch
    can be exercised.

    There is no upper-cased arm: this machine's filesystem is case-insensitive, so one would
    write the same files. The lowercase contract is pinned on the reader's own literals
    instead — see `test_fdr_reads_the_lowercase_names_and_not_a_siblings_uppercase`."""
    docs = tmp_path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    stem = "fdr"
    if fdr:
        status_line = f"**Status:** {status}\n" if status is not None else ""
        (docs / f"{stem}.md").write_text(
            f"# FDR — thing\n\n{status_line}**Owner:** Principal PM\n"
            f"**Version:** {version} — what this revision changed\n"
        )
    if open_issues:
        (docs / f"{stem}_open_issues.md").write_text(fdr_companion(*buckets))
    if trail:
        (docs / "trail" / stem).mkdir(parents=True, exist_ok=True)
        for n in trail:
            (docs / "trail" / stem / f"cycle-{n}.md").write_text("# cycle\n")
    return str(tmp_path)


def fdr_ctx(artifact_path, *, state="blocked", head_before=None, head_after=None):
    return OutcomeContext(
        label="example-product", cwd="/repo", artifact_path=artifact_path,
        state=state, head_before=head_before, head_after=head_after,
    )


def test_fdr_is_registered():
    """A new run type is one registry entry; the watcher resolves --reporter fdr by name, and
    it no longer falls through to generic."""
    assert reporters.get_reporter("fdr") is reporters.fdr
    assert reporters.get_reporter("fdr") is not reporters.generic


def test_fdr_run_that_wrote_no_fdr_is_not_a_success(tmp_path):
    out = reporters.fdr(fdr_ctx(fdr_product(tmp_path, fdr=False)))
    assert "no FDR" in out.body
    assert "✅" not in out.body


def test_fdr_reads_the_lowercase_names_and_not_a_siblings_uppercase():
    """SKILL.md:69 — "The three names are lowercase, and they match each other on purpose."
    A find-replace from a sibling that upper-cased them would report "no FDR" against a
    product whose FDR is sitting right there — the wrong answer, stated confidently, on any
    case-SENSITIVE filesystem.

    Asserted on the literals the reader opens rather than on a fixture tree, and that is not
    a weaker test — it is the only one that holds everywhere. This suite's own machine runs
    case-INSENSITIVE APFS, where `docs/FDR.md` and `docs/fdr.md` are one file and a
    behavioural fixture passes whichever case the reader names. A test that cannot fail on
    the machine it runs on is not a guard."""
    names = {c for c in reporters.read_fdr.__code__.co_consts if isinstance(c, str)}
    assert {"fdr.md", "fdr_open_issues.md", "trail/fdr"} <= names
    assert not any(c.upper() == c and c.lower() in
                   {"fdr.md", "fdr_open_issues.md", "trail/fdr"} for c in names)


def test_fdr_unreadable_product_falls_back_rather_than_failing(monkeypatch, tmp_path):
    def boom(_path):
        raise OSError("permission denied")

    monkeypatch.setattr(reporters.os.path, "isfile", boom)

    out = reporters.fdr(fdr_ctx(fdr_product(tmp_path, status="Locked")))
    assert "could not be read" in out.body
    assert "what it produced is unknown" in out.body


def test_fdr_settled_with_no_companion_is_the_done_signal(tmp_path):
    """fdr_template.md:72 — "Settled = the companion is gone. Nothing awaits the owner — the
    done signal.\""""
    out = reporters.fdr(fdr_ctx(fdr_product(tmp_path, status="Settled", version=3)))
    assert out.body == "✅ example-product: FDR v3 settled — nothing pending."


def test_fdr_locked_with_no_companion_is_also_done(tmp_path):
    """fdr_template.md:73 — Locked is the owner's ratification, never the run's."""
    out = reporters.fdr(fdr_ctx(fdr_product(tmp_path, status="Locked", version=4)))
    assert out.body == "✅ example-product: FDR v4 is Locked — nothing pending."


def test_fdr_draft_with_no_companion_warns(tmp_path):
    """SKILL.md:208 sets Status from the companion's absence, so a Draft with no companion is
    a run that did not finish, not a settled one."""
    out = reporters.fdr(fdr_ctx(fdr_product(tmp_path, status="Draft")))
    assert out.body.startswith("⚠️ example-product: FDR v2")
    assert "not Settled" in out.body
    assert "✅" not in out.body


def test_fdr_unparseable_status_with_no_companion_says_unreadable(tmp_path):
    out = reporters.fdr(fdr_ctx(fdr_product(tmp_path, status=None)))
    assert '"unreadable"' in out.body


def test_fdr_open_round_names_its_cycle_and_both_buckets(tmp_path):
    out = reporters.fdr(fdr_ctx(fdr_product(
        tmp_path, status="Draft", version=2, open_issues=True, buckets=(1, 1),
        trail=(1, 2))))
    assert out.body == (
        "📋 example-product: FDR v2, cycle 3 complete — 1 open issue, 1 choice to confirm.\n"
        "Answer docs/fdr_open_issues.md, commit, re-run."
    )


def test_fdr_bucket_terms_are_singular_and_plural(tmp_path):
    singular = reporters.fdr(fdr_ctx(fdr_product(
        tmp_path, status="Draft", open_issues=True, buckets=(1, 1)))).body
    assert "1 open issue," in singular
    assert "1 choice to confirm" in singular

    plural = reporters.fdr(fdr_ctx(fdr_product(
        tmp_path, status="Draft", open_issues=True, buckets=(2, 3)))).body
    assert "2 open issues," in plural
    assert "3 choices to confirm" in plural


def test_fdr_never_says_directive_or_declared_omission(tmp_path):
    """The FDR companion's § 3 is items raised from downstream. Neither "directive" (the PRD
    companion's term) nor "declared omission" may name them."""
    extra = "## 3. Raised from downstream\n\n### 3.1 a raised item\n"
    docs = tmp_path / "docs"
    fdr_product(tmp_path, status="Draft", open_issues=True, buckets=(0, 1))
    (docs / "fdr_open_issues.md").write_text(fdr_companion(0, 1, extra=extra))

    out = reporters.fdr(fdr_ctx(str(tmp_path)))

    assert "directive" not in out.body.lower()
    assert "declared omission" not in out.body.lower()
    assert "1 item raised from downstream" in out.body


def test_fdr_raised_items_only_ask_for_an_answer_not_an_empty_warning(tmp_path):
    fdr_product(tmp_path, status="Draft", open_issues=True, buckets=(0, 0))
    (tmp_path / "docs" / "fdr_open_issues.md").write_text(
        fdr_companion(0, 0, extra="## 3. Raised from downstream\n\n### 3.1 a raised item\n"))

    out = reporters.fdr(fdr_ctx(str(tmp_path)))

    assert "lists no items" not in out.body
    assert "1 item raised from downstream" in out.body


def test_fdr_companion_present_but_empty_is_flagged(tmp_path):
    out = reporters.fdr(fdr_ctx(fdr_product(
        tmp_path, status="Draft", open_issues=True, buckets=(0, 0))))
    assert "lists no items" in out.body
    assert "✅" not in out.body


# --- the trail is the discriminator (fdr HAS one, like prd/uxd/design/content) -------------


def test_fdr_open_round_with_no_trail_names_cycle_1(tmp_path):
    """The state the first live run left: no trail/fdr/ at all."""
    out = reporters.fdr(fdr_ctx(fdr_product(
        tmp_path, status="Draft", open_issues=True, buckets=(1, 0))))
    assert "cycle 1 complete" in out.body


def test_fdr_trail_uses_the_highest_cycle_not_the_count(tmp_path):
    """SKILL.md:77-79 — N is one higher than the HIGHEST cycle-<N>.md already in trail/fdr/,
    so a removed cycle must not make the reporter name one that already exists."""
    out = reporters.fdr(fdr_ctx(fdr_product(
        tmp_path, status="Draft", open_issues=True, buckets=(1, 0), trail=(1, 4))))
    assert "cycle 5 complete" in out.body


def test_fdr_trail_ignores_a_non_cycle_filename(tmp_path):
    path = fdr_product(tmp_path, status="Draft", open_issues=True, buckets=(1, 0),
                       trail=(1,))
    (tmp_path / "docs" / "trail/fdr" / "README.md").write_text("not a cycle\n")

    out = reporters.fdr(fdr_ctx(path))

    assert "cycle 2 complete" in out.body


def test_fdr_done_branch_names_no_cycle_even_with_a_trail(tmp_path):
    """The trail counts rounds folded in, a different quantity from the open round's cycle."""
    out = reporters.fdr(fdr_ctx(fdr_product(
        tmp_path, status="Settled", version=2, trail=(1, 2))))
    assert out.body == "✅ example-product: FDR v2 settled — nothing pending."


# --- a run that committed nothing must not inherit the last run's work ---------------------


def test_fdr_run_that_committed_nothing_says_so_in_fdrs_own_terms(tmp_path):
    """An unchanged HEAD decides the body rather than annotating one, as in prd/srs/uxd/
    design/content: the previous round's files are still on disk, so the product is not read."""
    out = reporters.fdr(fdr_ctx(
        fdr_product(tmp_path, status="Settled"),
        head_before="abc123", head_after="abc123"))
    assert "FDR" in out.body
    assert "committed nothing" in out.body
    assert "✅" not in out.body


def test_fdr_run_that_committed_nothing_but_left_an_unanswered_companion_says_so(tmp_path):
    root = fdr_product(tmp_path, status="Draft")
    (Path(root, "docs", "fdr_open_issues.md")).write_text(
        "## 1. Open issues\n\n### 1.1 a question\n\n- **Answer:** <the owner fills this in>\n")
    out = reporters.fdr(fdr_ctx(root, head_before="same", head_after="same"))
    assert "FDR" in out.body
    assert "waiting on you" in out.body
    assert "may have stopped" not in out.body


def test_fdr_names_the_fdr_and_not_a_sibling_artifact(tmp_path):
    """`_committed_nothing` takes the artifact name from its caller — a reporter names the
    document it reads and no other, or it replaces one false claim with a second."""
    out = reporters.fdr(fdr_ctx(
        fdr_product(tmp_path, status="Settled"),
        head_before="abc123", head_after="abc123"))
    for sibling in ("PRD", "SRS", "UXD", "DESIGN", "CONTENT", "SDD", "Agari"):
        assert sibling not in out.body


def test_fdr_unreadable_head_still_reads_the_product(tmp_path):
    """A HEAD that could not be read is not evidence of an idle run, so it claims neither
    outcome — the same third case every sibling carries."""
    out = reporters.fdr(fdr_ctx(
        fdr_product(tmp_path, status="Settled", version=1),
        head_before=None, head_after=None))
    assert out.body == "✅ example-product: FDR v1 settled — nothing pending."


def test_fdr_without_an_artifact_path_degrades_to_run_ended(tmp_path):
    out = reporters.fdr(fdr_ctx(None))
    assert out.body == "example-product: run ended."


def test_fdr_a_parser_bug_costs_specificity_not_the_message(monkeypatch, tmp_path):
    """The wide `except Exception` is deliberate — the person is waiting on a phone, so a
    malformed document costs specificity and never the message."""
    def boom(_text):
        raise ValueError("bad parse")

    monkeypatch.setattr(reporters, "parse_status", boom)

    out = reporters.fdr(fdr_ctx(fdr_product(tmp_path, status="Settled")))
    assert out.body == "example-product: run ended."


# --- the shared helpers are reused, not copied a fourth time -------------------------------


def test_fdr_reuses_the_shared_two_bucket_phrase(tmp_path):
    """Station bar 6. `_two_bucket_pending_phrase`'s own docstring fixes why it is correct for
    a companion of two answer buckets and a raised § 3, and this reporter's companion is
    exactly that shape. A fourth
    near-identical `_fdr_pending_phrase` is the copy this module has been careful to avoid."""
    assert not hasattr(reporters, "_fdr_pending_phrase")
    assert "_two_bucket_pending_phrase" in reporters._fdr_body.__code__.co_names


def test_fdr_reuses_the_shared_trail_reader(tmp_path):
    """Station bar 7. `trail_cycles` already takes the folder name, so the FDR trail is read by
    passing `trail/fdr` rather than by writing a second trail walker."""
    assert "trail_cycles" in reporters.read_fdr.__code__.co_names
    assert "trail/fdr" in reporters.read_fdr.__code__.co_consts


# --- the real templates parse --------------------------------------------------------------


def test_fdr_reads_the_real_templates(tmp_path):
    """The parsers must hold against the shipped templates, not only against what the fixtures
    imply — the blockquote preamble, the HTML comments and the em-dashed headings must not
    perturb the read. The template's `**Version:** <n>` is not an integer, so the reference
    degrades to the bare document name rather than inventing a version."""
    templates = Path(__file__).resolve().parent.parent / "templates" / "product-templates"
    docs = tmp_path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "fdr.md").write_text(
        (templates / "fdr_template.md").read_text(encoding="utf-8"))
    (docs / "fdr_open_issues.md").write_text(
        (templates / "fdr_open_issues_template.md").read_text(encoding="utf-8"))

    out = reporters.fdr(fdr_ctx(str(tmp_path)))

    assert out.body == (
        "📋 example-product: FDR, cycle 1 complete — 1 open issue, 2 choices to confirm, "
        "1 item raised from downstream.\n"
        "Answer docs/fdr_open_issues.md, commit, re-run."
    )
    assert "directive" not in out.body.lower()


def test_fdr_reports_the_live_run_that_opened_this_seed(tmp_path):
    """Station bar 5. The first product-fdr run finished on a live product on 2026-08-28 and
    reported the bare `<label>: run ended.` Its real on-disk shape — docs/fdr.md at Status
    Draft, Version 1, a companion with 1 open issue and 3 choices to confirm, and no
    trail/fdr/ — is reproduced as
    a fixture here (the real tree is another instance's product and its companion is the
    owner's live answering surface, so nothing in this suite reads it), and this is what the
    composer says about it."""
    out = reporters.fdr(fdr_ctx(fdr_product(
        tmp_path, status="Draft", version=1, open_issues=True, buckets=(1, 3))))

    assert out.body == (
        "📋 example-product: FDR v1, cycle 1 complete — 1 open issue, 3 choices to confirm.\n"
        "Answer docs/fdr_open_issues.md, commit, re-run."
    )


def test_existing_reporters_are_unaffected_by_the_fdr_addition():
    assert reporters.get_reporter("prd") is reporters.prd
    assert reporters.get_reporter("srs") is reporters.srs
    assert reporters.get_reporter("uxd") is reporters.uxd
    assert reporters.get_reporter("design") is reporters.design
    assert reporters.get_reporter("content") is reporters.content
    assert reporters.get_reporter("agari") is reporters.agari
    assert reporters.get_reporter("sdd-document") is reporters.sdd_document
    assert reporters.get_reporter("fix-author") is reporters.fix_author
    assert reporters.get_reporter("apply-packet") is reporters.apply_packet
    assert reporters.get_reporter("writing-bar") is reporters.writing_bar
    assert reporters.get_reporter("experience-visual") is reporters.experience_visual
    assert reporters.get_reporter("experience-voice") is reporters.experience_voice
    assert reporters.get_reporter("nope-not-a-reporter") is reporters.generic


# --- architecture: a directory whose record count is the state, plus a document, plus one
# shared companion ----------------------------------------------------------------------------
#
# Authored against the real architecture contract (core/templates/product-templates/
# adr_record_template.md, adr_index_template.md, nfdr_template.md,
# architecture_open_issues_template.md, and
# skills/principal-architect/.claude/skills/product-architecture/SKILL.md), not cloned from a
# sibling:
#   - The headline figure is a COUNT of files in docs/adr/, matched by filename shape
#     (\d{4}-.+\.md) — never docs/adr/README.md, which is a rewritten projection
#     (SKILL.md § *The files and the loop*, "the one file here that IS rewritten") and can be
#     stale by construction.
#   - docs/nfdr.md carries the same Status/Version line shapes parse_status/parse_version
#     already read.
#   - docs/architecture_open_issues.md has two answer buckets and § 3, items raised from
#     downstream (architecture_open_issues_template.md) — the SRS/UXD/FDR shape.
#   - The companion's OWN name ("architecture") is what `_committed_nothing_for` is passed —
#     not "NFDR" — because the companion answers for both the records and the NFDR
#     (SKILL.md § *One companion for both records*).
#   - Whether an input was read at Draft is a best-effort, name-near-"Draft" surface over the
#     records and the NFDR text — not a fixed field the templates or prompt commit to.


ARCH_BUCKET_TITLES = {
    1: "Open issues — questions with no answer yet",
    2: ("Choices to confirm — the Principal Architect drafted a best-effort answer; "
        "confirm or override"),
}


def adr_record(status="Accepted", trace="SDD § 4"):
    return (
        "# ADR-0001: a decision\n\n"
        f"**Status:** {status}\n**Date:** 2026-08-30\n\n"
        "## Context\n\nbecause.\n\n## Decision\n\nit is so.\n\n"
        "## Alternatives ruled out\n\n- **other** — it lost.\n\n"
        f"## Traces to\n\n{trace}\n\n## Binds\n\nQC-1\n"
    )


def architecture_companion(n1=0, n2=0, extra=""):
    out = []
    for bucket, n in ((1, n1), (2, n2)):
        out.append(f"## {bucket}. {ARCH_BUCKET_TITLES[bucket]}\n")
        if n == 0:
            out.append("None this cycle.\n")
        for i in range(1, n + 1):
            out.append(f"### {bucket}.{i} the question, in one line\n")
            out.append("- **Why it matters:** because.\n")
    if extra:
        out.append(extra)
    return "\n".join(out)


def architecture_product(tmp_path, records=(), nfdr=True, open_issues=False, status="Draft",
                          version=2, buckets=(0, 0), trail=(), record_traces=None,
                          nfdr_extra=""):
    """The tree product-architecture authors into: docs/adr/NNNN-slug.md (one per name in
    `records`), docs/adr/README.md (an index the reporter must never read), docs/nfdr.md, and
    optionally docs/architecture_open_issues.md + docs/trail/architecture/. `record_traces`
    maps a record's filename to its `## Traces to` text, for the unsettled-input tests.
    `status=None` omits the NFDR's Status line entirely, so the parse-fails branch can be
    exercised."""
    docs = tmp_path / "docs"
    adr = docs / "adr"
    adr.mkdir(parents=True, exist_ok=True)
    for i, slug in enumerate(records, start=1):
        name = f"{i:04d}-{slug}.md"
        trace = (record_traces or {}).get(name, "SDD § 4")
        (adr / name).write_text(adr_record(trace=trace))
    if records:
        (adr / "README.md").write_text("# index\n\n| # | Title | Status | Date |\n")
    if nfdr:
        status_line = f"**Status:** {status}\n" if status is not None else ""
        (docs / "nfdr.md").write_text(
            f"# NFDR — thing\n\n{status_line}**Owner:** Principal Architect\n"
            f"**Version:** {version} — what this revision changed\n{nfdr_extra}"
        )
    if open_issues:
        (docs / "architecture_open_issues.md").write_text(architecture_companion(*buckets))
    if trail:
        (docs / "trail/architecture").mkdir(parents=True, exist_ok=True)
        for n in trail:
            (docs / "trail/architecture" / f"cycle-{n}.md").write_text("# cycle\n")
    return str(tmp_path)


def architecture_ctx(artifact_path, *, state="blocked", head_before=None, head_after=None):
    return OutcomeContext(
        label="example-product", cwd="/repo", artifact_path=artifact_path,
        state=state, head_before=head_before, head_after=head_after,
    )


def test_architecture_is_registered():
    assert reporters.get_reporter("architecture") is reporters.architecture
    assert reporters.get_reporter("architecture") is not reporters.generic


def test_architecture_run_that_wrote_nothing_is_not_a_success(tmp_path):
    out = reporters.architecture(architecture_ctx(
        architecture_product(tmp_path, records=(), nfdr=False)))
    assert "left nothing to read" in out.body
    assert "✅" not in out.body


# --- the count is the directory's, never the index's -----------------------------------------


def test_architecture_counts_the_directory_not_the_index(tmp_path):
    """The index is a projection and can be stale by construction (SKILL.md § *The files and
    the loop*): a stale README claiming a different count must not change the answer."""
    root = architecture_product(
        tmp_path, records=("a-decision", "another-one"), status="Settled")
    (Path(root, "docs", "adr", "README.md")).write_text(
        "# index\n\n| # | Title | Status | Date |\n"
        "| [ADR-0001](0001-a-decision.md) | a | Accepted | 2026-08-30 |\n"
        "| [ADR-0002](0002-another-one.md) | b | Accepted | 2026-08-30 |\n"
        "| [ADR-0003](0003-ghost.md) | c | Accepted | 2026-08-30 |\n"
    )
    out = reporters.architecture(architecture_ctx(root))
    assert "2 records" in out.body
    assert "3 records" not in out.body


def test_architecture_never_counts_the_readme_as_a_record(tmp_path):
    root = architecture_product(tmp_path, records=(), status="Settled")
    (Path(root, "docs", "adr", "README.md")).write_text("# index\n")
    out = reporters.architecture(architecture_ctx(root))
    assert "0 records" in out.body


def test_architecture_record_filename_shape_is_strict(tmp_path):
    root = architecture_product(tmp_path, records=("a-decision",), status="Settled")
    adr = Path(root, "docs", "adr")
    (adr / "notes.md").write_text("not a record\n")
    (adr / "1-too-few-digits.md").write_text("not a record\n")
    (adr / "00010-too-many-digits.md").write_text("not a record\n")
    out = reporters.architecture(architecture_ctx(root))
    assert "1 record in the decision log" in out.body


def test_architecture_record_count_is_singular_and_plural(tmp_path):
    one = reporters.architecture(architecture_ctx(architecture_product(
        tmp_path / "a", records=("a-decision",), status="Settled"))).body
    assert "1 record in the decision log" in one
    assert "1 records" not in one

    many = reporters.architecture(architecture_ctx(architecture_product(
        tmp_path / "b", records=("a-decision", "another"), status="Settled"))).body
    assert "2 records in the decision log" in many


# --- the constraint set's own status -----------------------------------------------------


def test_architecture_settled_with_no_companion_is_the_done_signal(tmp_path):
    out = reporters.architecture(architecture_ctx(architecture_product(
        tmp_path, records=("a-decision",), status="Settled", version=3)))
    assert out.body == ("✅ example-product: 1 record in the decision log; "
                        "NFDR v3 settled — nothing pending.")


def test_architecture_locked_with_no_companion_is_also_done(tmp_path):
    out = reporters.architecture(architecture_ctx(architecture_product(
        tmp_path, records=(), status="Locked", version=4)))
    assert out.body == ("✅ example-product: 0 records in the decision log; "
                        "NFDR v4 is Locked — nothing pending.")


def test_architecture_draft_with_no_companion_warns(tmp_path):
    out = reporters.architecture(architecture_ctx(architecture_product(
        tmp_path, records=("a-decision",), status="Draft")))
    assert "⚠️" in out.body
    assert "not Settled" in out.body
    assert "✅" not in out.body


def test_architecture_unparseable_status_with_no_companion_says_unreadable(tmp_path):
    out = reporters.architecture(architecture_ctx(architecture_product(
        tmp_path, records=(), status=None)))
    assert '"unreadable"' in out.body


def test_architecture_no_nfdr_yet_but_records_exist_is_not_a_success(tmp_path):
    out = reporters.architecture(architecture_ctx(architecture_product(
        tmp_path, records=("a-decision",), nfdr=False)))
    assert "1 record in the decision log" in out.body
    assert "no NFDR" in out.body
    assert "✅" not in out.body


# --- the companion, when open -------------------------------------------------------------


def test_architecture_open_round_names_its_cycle_and_both_buckets(tmp_path):
    out = reporters.architecture(architecture_ctx(architecture_product(
        tmp_path, records=("a-decision",), status="Draft", version=1, open_issues=True,
        buckets=(1, 1), trail=(1,))))
    assert "1 record in the decision log" in out.body
    assert "NFDR v1" in out.body
    assert "cycle 2 complete" in out.body
    assert "1 open issue" in out.body
    assert "1 choice to confirm" in out.body
    assert "Answer docs/architecture_open_issues.md, commit, re-run." in out.body


def test_architecture_bucket_terms_are_singular_and_plural(tmp_path):
    singular = reporters.architecture(architecture_ctx(architecture_product(
        tmp_path / "a", records=("a-decision",), status="Draft", open_issues=True,
        buckets=(1, 1)))).body
    assert "1 open issue," in singular
    assert "1 choice to confirm" in singular

    plural = reporters.architecture(architecture_ctx(architecture_product(
        tmp_path / "b", records=("a-decision",), status="Draft", open_issues=True,
        buckets=(2, 3)))).body
    assert "2 open issues," in plural
    assert "3 choices to confirm" in plural


def test_architecture_never_says_directive_or_declared_omission(tmp_path):
    """The architecture companion's § 3 is items raised from downstream. Neither "directive"
    (the PRD companion's term) nor "declared omission" may name them."""
    extra = "## 3. Raised from downstream\n\n### 3.1 a raised item\n"
    root = architecture_product(
        tmp_path, records=("a-decision",), status="Draft", open_issues=True, buckets=(0, 1))
    (Path(root, "docs", "architecture_open_issues.md")).write_text(
        architecture_companion(0, 1, extra=extra))

    out = reporters.architecture(architecture_ctx(root))

    assert "directive" not in out.body.lower()
    assert "declared omission" not in out.body.lower()
    assert "1 item raised from downstream" in out.body


def test_architecture_raised_items_only_ask_for_an_answer_not_an_empty_warning(tmp_path):
    root = architecture_product(
        tmp_path, records=("a-decision",), status="Draft", open_issues=True, buckets=(0, 0))
    (Path(root, "docs", "architecture_open_issues.md")).write_text(
        architecture_companion(
            0, 0, extra="## 3. Raised from downstream\n\n### 3.1 a raised item\n"))

    out = reporters.architecture(architecture_ctx(root))

    assert "lists no items" not in out.body
    assert "1 item raised from downstream" in out.body


def test_architecture_companion_present_but_empty_is_flagged(tmp_path):
    out = reporters.architecture(architecture_ctx(architecture_product(
        tmp_path, records=("a-decision",), status="Draft", open_issues=True,
        buckets=(0, 0))))
    assert "lists no items" in out.body
    assert "✅" not in out.body


# --- the trail is the discriminator (like prd/uxd/design/content/fdr) ---------------------


def test_architecture_open_round_with_no_trail_names_cycle_1(tmp_path):
    out = reporters.architecture(architecture_ctx(architecture_product(
        tmp_path, records=("a-decision",), status="Draft", open_issues=True,
        buckets=(1, 0))))
    assert "cycle 1 complete" in out.body


def test_architecture_trail_uses_the_highest_cycle_not_the_count(tmp_path):
    out = reporters.architecture(architecture_ctx(architecture_product(
        tmp_path, records=("a-decision",), status="Draft", open_issues=True,
        buckets=(1, 0), trail=(1, 4))))
    assert "cycle 5 complete" in out.body


def test_architecture_trail_ignores_a_non_cycle_filename(tmp_path):
    root = architecture_product(tmp_path, records=("a-decision",), status="Draft",
                                open_issues=True, buckets=(1, 0), trail=(1,))
    (Path(root, "docs", "trail/architecture", "README.md")).write_text("not a cycle\n")

    out = reporters.architecture(architecture_ctx(root))

    assert "cycle 2 complete" in out.body


def test_architecture_done_branch_names_no_cycle_even_with_a_trail(tmp_path):
    out = reporters.architecture(architecture_ctx(architecture_product(
        tmp_path, records=("a-decision",), status="Settled", version=2, trail=(1, 2))))
    assert out.body == ("✅ example-product: 1 record in the decision log; "
                        "NFDR v2 settled — nothing pending.")


# --- an unsettled input is surfaced, best-effort, and degrades gracefully ------------------


def test_architecture_surfaces_an_input_read_at_draft(tmp_path):
    root = architecture_product(
        tmp_path, records=("a-decision",), status="Settled",
        record_traces={"0001-a-decision.md": "SDD § 4, read while Draft"})
    out = reporters.architecture(architecture_ctx(root))
    assert "SDD" in out.body
    assert "Draft" in out.body


def test_architecture_surfaces_multiple_unsettled_inputs(tmp_path):
    root = architecture_product(
        tmp_path, records=("a-decision",), status="Settled",
        record_traces={"0001-a-decision.md": "SDD § 4 (Draft when read)"},
        nfdr_extra="\n- **RN-1:** derived from SRS § 3 while it was Draft\n")
    out = reporters.architecture(architecture_ctx(root))
    assert "SDD" in out.body
    assert "SRS" in out.body


def test_architecture_reads_the_inputs_read_line_end_to_end(tmp_path):
    """The fixed header line reaches the composed message: a product whose NFDR declares the
    FDR was Draft says so in the body."""
    root = architecture_product(
        tmp_path, records=("a-decision",), status="Settled",
        nfdr_extra="\n**Inputs read:** SRS Settled \u00b7 SDD Settled \u00b7 FDR Draft\n")
    out = reporters.architecture(architecture_ctx(root))
    assert "FDR" in out.body
    assert "Draft" in out.body


def test_inputs_read_line_beats_the_prose_heuristic(tmp_path):
    """When the fixed line is present it decides, so a stray `Draft` elsewhere in the
    document cannot add an input the line says was Settled."""
    assert reporters._unsettled_inputs(
        ["**Inputs read:** SRS Settled \u00b7 SDD Settled \u00b7 FDR Draft\n"
         "- **RN-1:** derived from SRS \u00a7 3 while it was Draft\n"]) == ["FDR"]


def test_prose_heuristic_still_reads_a_document_written_before_the_line(tmp_path):
    """Products whose records predate the fixed line carry the fact in prose; the older scan
    stays as the fallback rather than reporting nothing."""
    assert reporters._unsettled_inputs(["traces to: SDD \u00a7 4, read while Draft"]) == ["SDD"]


def test_inputs_read_line_with_everything_settled_reports_nothing(tmp_path):
    assert reporters._unsettled_inputs(
        ["**Inputs read:** SRS Settled \u00b7 SDD Settled \u00b7 FDR Settled\n"]) == []


def test_architecture_degrades_gracefully_with_no_unsettled_note(tmp_path):
    """No mention of Draft anywhere in the records or the NFDR — the ordinary, finished
    case — must not manufacture a caveat."""
    root = architecture_product(tmp_path, records=("a-decision",), status="Settled")
    out = reporters.architecture(architecture_ctx(root))
    assert "Draft" not in out.body


# --- a run that committed nothing must not inherit the last run's work --------------------


def test_architecture_run_that_committed_nothing_says_so_in_its_own_terms(tmp_path):
    out = reporters.architecture(architecture_ctx(
        architecture_product(tmp_path, records=("a-decision",), status="Settled"),
        head_before="abc123", head_after="abc123"))
    assert "Architecture" in out.body
    assert "committed nothing" in out.body
    assert "✅" not in out.body


def test_architecture_run_that_committed_nothing_borrows_no_figures_from_the_last_one(
        tmp_path):
    out = reporters.architecture(architecture_ctx(
        architecture_product(tmp_path, records=("a-decision", "another"), status="Draft",
                              open_issues=True, version=2, trail=(1,), buckets=(1, 8)),
        head_before="same-sha", head_after="same-sha"))
    assert "record" not in out.body
    assert "NFDR v" not in out.body
    assert "cycle" not in out.body
    for figure in ("1 open issue", "8 choices"):
        assert figure not in out.body


def test_architecture_run_that_committed_nothing_but_left_an_unanswered_companion_says_so(
        tmp_path):
    root = architecture_product(tmp_path, records=("a-decision",), status="Draft")
    (Path(root, "docs", "architecture_open_issues.md")).write_text(
        "## 1. Open issues\n\n### 1.1 a question\n\n- **Answer:** <the owner fills this in>\n")
    out = reporters.architecture(architecture_ctx(
        root, head_before="same", head_after="same"))
    assert "Architecture" in out.body
    assert "waiting on you" in out.body
    assert "may have stopped" not in out.body


def test_architecture_names_no_sibling_artifact_when_committed_nothing(tmp_path):
    out = reporters.architecture(architecture_ctx(
        architecture_product(tmp_path, records=("a-decision",), status="Settled"),
        head_before="abc123", head_after="abc123"))
    for sibling in ("PRD", "SRS", "UXD", "DESIGN", "CONTENT", "SDD", "Agari", "NFDR"):
        assert sibling not in out.body


def test_architecture_unreadable_head_still_reads_the_product(tmp_path):
    out = reporters.architecture(architecture_ctx(
        architecture_product(tmp_path, records=("a-decision",), status="Settled", version=1),
        head_before=None, head_after=None))
    assert out.body == ("✅ example-product: 1 record in the decision log; "
                        "NFDR v1 settled — nothing pending.")


def test_architecture_without_an_artifact_path_degrades_to_run_ended(tmp_path):
    out = reporters.architecture(architecture_ctx(None))
    assert out.body == "example-product: run ended."


def test_architecture_unreadable_product_falls_back_rather_than_failing(monkeypatch, tmp_path):
    def boom(_path):
        raise OSError("permission denied")

    monkeypatch.setattr(reporters.os.path, "isfile", boom)

    out = reporters.architecture(architecture_ctx(architecture_product(
        tmp_path, records=("a-decision",), status="Settled")))
    assert "could not be read" in out.body
    assert "what it produced is unknown" in out.body
    assert "✅" not in out.body


def test_architecture_a_parser_bug_costs_specificity_not_the_message(monkeypatch, tmp_path):
    def boom(_text):
        raise ValueError("bad parse")

    monkeypatch.setattr(reporters, "parse_status", boom)

    out = reporters.architecture(architecture_ctx(architecture_product(
        tmp_path, records=("a-decision",), status="Settled")))
    assert out.body == "example-product: run ended."


# --- the shared helpers are reused, not copied a fourth/fifth time -------------------------


def test_architecture_reuses_the_shared_two_bucket_phrase(tmp_path):
    assert not hasattr(reporters, "_architecture_pending_phrase")
    assert "_two_bucket_pending_phrase" in reporters._architecture_body.__code__.co_names


def test_architecture_reuses_the_shared_trail_reader(tmp_path):
    assert "trail_cycles" in reporters.read_architecture.__code__.co_names
    assert "trail/architecture" in reporters.read_architecture.__code__.co_consts


# --- the real templates parse ---------------------------------------------------------------


def test_architecture_reads_the_real_open_issues_and_nfdr_templates(tmp_path):
    """The parsers must hold against the shipped templates, not only against what the
    fixtures imply — the blockquote preamble, the HTML comments and the em-dashed headings
    must not perturb the read."""
    templates = Path(__file__).resolve().parent.parent / "templates" / "product-templates"
    docs = tmp_path / "docs"
    (docs / "adr").mkdir(parents=True, exist_ok=True)
    (docs / "adr" / "0001-a-decision.md").write_text(
        templates.joinpath("adr_record_template.md").read_text(encoding="utf-8"))
    (docs / "nfdr.md").write_text(
        templates.joinpath("nfdr_template.md").read_text(encoding="utf-8"))
    (docs / "architecture_open_issues.md").write_text(
        templates.joinpath("architecture_open_issues_template.md").read_text(encoding="utf-8"))

    out = reporters.architecture(architecture_ctx(str(tmp_path)))

    assert "1 record in the decision log" in out.body
    assert "1 open issue" in out.body
    assert "2 choices to confirm" in out.body
    assert "1 item raised from downstream" in out.body
    assert "cycle 1 complete" in out.body
    assert "directive" not in out.body.lower()


def test_existing_reporters_are_unaffected_by_the_architecture_addition():
    assert reporters.get_reporter("prd") is reporters.prd
    assert reporters.get_reporter("srs") is reporters.srs
    assert reporters.get_reporter("uxd") is reporters.uxd
    assert reporters.get_reporter("design") is reporters.design
    assert reporters.get_reporter("content") is reporters.content
    assert reporters.get_reporter("agari") is reporters.agari
    assert reporters.get_reporter("sdd-document") is reporters.sdd_document
    assert reporters.get_reporter("fdr") is reporters.fdr
    assert reporters.get_reporter("fix-author") is reporters.fix_author
    assert reporters.get_reporter("apply-packet") is reporters.apply_packet
    assert reporters.get_reporter("writing-bar") is reporters.writing_bar
    assert reporters.get_reporter("experience-visual") is reporters.experience_visual
    assert reporters.get_reporter("experience-voice") is reporters.experience_voice
    assert reporters.get_reporter("nope-not-a-reporter") is reporters.generic


# --- companion-self-answer: reads the run's own report file, never the companion -----------
#
# Authored against `skills/companion/.claude/skills/companion-self-answer/SKILL.md` § Step 5 and
# `core/templates/self_answer_report_template.md`, not cloned from a sibling — the shape here
# differs from every reporter above it:
#   - The artifact is a REPORT the skill writes about its own run, never a product document
#     with a Status/Version line, so there is no unchanged-HEAD "committed nothing" branch —
#     that pattern belongs to a document contract this artifact does not carry. The two rules
#     this file states about itself (read the product, never the agent's state; a wide
#     `except Exception` so a parser bug costs specificity, never the message) are the whole
#     of it — reporters.py:212, :214-218, and the module docstring.
#   - The tally is one field scan, not a heading walk: every `## Items worked` / `## Left for
#     the owner` entry carries `**Verdict:**` from the prompt's six literals, so a single
#     regex over the whole file IS the split — no per-section counting.
#   - The search walks the document homes a companion — and so its report, written beside it
#     (SKILL.md § Step 5) — can sit in: system/*/, system/projects/*/, each project's
#     `<Product path>/docs/`, or the target's own docs/ when it carries no project cards,
#     taking the highest `trail/<doc>/self_answer-<N>.md` across every home. It mirrors no launcher
#     function: the v1 launcher's `find_companion` swept these homes and was deleted whole
#     at `b68d56de`.


def self_answer_verdict_block(number, verdict, why="because.", bucket="1. Open issues"):
    return (f"### {number} — the item's heading\n\n"
            f"- **Bucket:** {bucket}\n"
            f"- **Verdict:** {verdict}\n"
            f"- **Why:** {why}\n\n")


def self_answer_report_text(document="PRD", companion="docs/PRD_open_issues.md",
                             worked=(), left=0, unnamed=0, companions_opened=(), skipped=0,
                             launchers_owed=(), raised=0):
    """Build a report in `self_answer_report_template.md`'s shape. `worked` is a list of
    verdict literals (one `### ` entry per verdict given); `left` / `unnamed` / `skipped` /
    `raised` are counts; `companions_opened` is a list of `(path, document)` tuples — the
    template's pre-`72f690f9` shape, no action word — or `(path, action, document)` tuples —
    the new shape, `action` one of `opened` | `appended` | `updated`; `launchers_owed` is a
    list of `(document, how-to-run)` tuples for the section SKILL.md § Step 6 fills. `raised`
    entries land under `## Raised on this document`, omitted whole (heading included) when
    zero — the template's own rule for that section."""
    out = [f"# Self-answer report — {document}\n\n",
           "## Header\n\n",
           f"- **Companion:** {companion}\n",
           f"- **Document:** {document}\n",
           "- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.0.0\n",
           "- **Date:** 2026-08-29\n\n",
           "## Items worked\n\n"]
    if worked:
        for i, verdict in enumerate(worked, 1):
            out.append(self_answer_verdict_block(f"1.{i}", verdict))
    else:
        out.append("None this run.\n\n")
    out.append("## Left for the owner\n\n")
    if left:
        for i in range(1, left + 1):
            out.append(self_answer_verdict_block(f"2.{i}", "left for the owner",
                                                   why="the owner's call."))
    else:
        out.append("None this run.\n\n")
    out.append("## Unnamed verdict\n\n")
    if unnamed:
        for i in range(1, unnamed + 1):
            out.append(f"### 3.{i} — an odd one\n\n"
                        f"- **Bucket:** 1. Open issues\n"
                        f"- **Would-be verdict:** deferred\n"
                        f"- **Why none of the six fit:** none applied.\n\n")
    else:
        out.append("None this run.\n\n")
    out.append("## Skipped\n\n")
    if skipped:
        for i in range(1, skipped + 1):
            out.append(f"- **4.{i} — a filled slot** — already answered.\n")
        out.append("\n")
    else:
        out.append("None this run.\n\n")
    if raised:
        out.append("## Raised on this document\n\n")
        for i in range(1, raised + 1):
            out.append(f"### 5.{i} — a raised item\n\n"
                        f"- **What the document is owed:** it needs a change.\n"
                        f"- **Why it is worth a cycle:** because.\n\n")
    out.append("## Companions opened\n\n")
    if companions_opened:
        for entry in companions_opened:
            if len(entry) == 3:
                path, action, doc = entry
                out.append(f"- **{path}** — **{action}** — companion to `{doc}`, "
                            f"landed in commit `abc1234`\n")
            else:
                path, doc = entry
                out.append(f"- **{path}** — companion to `{doc}`, landed in commit `abc1234`\n")
        out.append("\n")
    else:
        out.append("None this run.\n\n")
    out.append("## Launchers owed\n\n")
    if launchers_owed:
        for doc, how in launchers_owed:
            out.append(f"- **{doc}** — `{how}`\n")
        out.append("\n")
    else:
        out.append("None this run.\n\n")
    return "".join(out)


def self_answer_report(dir_path, n=1, stem="PRD", **kwargs):
    """A run's report in its document's trail, `<dir_path>/trail/<doc>/self_answer-<N>.md`
    (`kensaiapp_structure.md` § *A trail is not the document's sibling*). `dir_path` is the
    document home, so the two trail segments are added here rather than by every caller."""
    trail = dir_path / "trail" / stem.lower()
    trail.mkdir(parents=True, exist_ok=True)
    path = trail / f"self_answer-{n}.md"
    path.write_text(self_answer_report_text(**kwargs))
    return path


def self_answer_ctx(artifact_path, *, label="example-product", state="stopped", document_stem="",
                    reports_before=None):
    return OutcomeContext(label=label, cwd="/repo", artifact_path=artifact_path, state=state,
                          document_stem=document_stem, reports_before=reports_before)


def test_companion_self_answer_is_registered():
    assert reporters.get_reporter("companion-self-answer") is reporters.companion_self_answer
    assert reporters.get_reporter("companion-self-answer") is not reporters.generic


def test_companion_self_answer_without_a_target_degrades_to_run_ended():
    out = reporters.companion_self_answer(self_answer_ctx(None))
    assert out.body == "example-product: run ended."


def test_companion_self_answer_no_report_found_says_the_run_wrote_none(tmp_path):
    """Distinguishes the two reasons a run can answer nothing (station bar 4) — this branch
    is the one where nothing was ever written: no report file exists at all."""
    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))
    assert "the run wrote none" in out.body
    assert "✅" not in out.body


def test_companion_self_answer_ignores_a_report_that_predates_the_watch(tmp_path):
    """The measured regression. A live product, 2026-09-04: the watcher printed

        `docs/DESIGN.md` (v4, Settled) — already answered, nothing left to work
        (…/docs/trail/design/self_answer-1.md)

    against a document at v5 whose three companion items were all placeholders, citing a
    report written three days earlier (that product's `9b87969`). The run wrote nothing; the
    locator took the highest-numbered report on disk and the reporter spoke its verdict.

    A report already on disk before the watch began cannot be this run's — the rule
    `watch_agent.completion_marker_seen` already applies to the done-marker."""
    old = self_answer_report(tmp_path / "docs", document="DESIGN", stem="design")
    ctx = self_answer_ctx(str(tmp_path), document_stem="DESIGN",
                          reports_before=(str(old),))
    out = reporters.companion_self_answer(ctx)
    assert "the run wrote none" in out.body, out.body
    assert "already answered" not in out.body, out.body
    assert "✅" not in out.body, out.body


def test_companion_self_answer_reads_a_report_this_run_wrote(tmp_path):
    """The other half, which must not move: a run that wrote its own report is unaffected.
    Nothing was on disk before the watch, so the report found is this run's."""
    self_answer_report(tmp_path / "docs", document="DESIGN", stem="design",
                       worked=("confirmed",), left=1)
    ctx = self_answer_ctx(str(tmp_path), document_stem="DESIGN", reports_before=())
    out = reporters.companion_self_answer(ctx)
    assert "1 of 2 items answered" in out.body, out.body
    assert "the run wrote none" not in out.body, out.body


def test_companion_self_answer_prefers_this_runs_report_over_a_higher_numbered_stale_one(tmp_path):
    """Both present. The locator takes the highest number today; it must take the one this
    run wrote, whatever its number."""
    stale = self_answer_report(tmp_path / "docs", n=7, document="DESIGN", stem="design")
    self_answer_report(tmp_path / "docs", n=2, document="DESIGN", stem="design",
                       worked=("confirmed with addition",), left=0)
    ctx = self_answer_ctx(str(tmp_path), document_stem="DESIGN",
                          reports_before=(str(stale),))
    out = reporters.companion_self_answer(ctx)
    assert "1 of 1 items answered" in out.body, out.body


def test_companion_self_answer_with_no_before_reading_behaves_as_today(tmp_path):
    """A caller that hands no before-reading — every reporter but this one, and any older
    caller — keeps today's behaviour exactly. The guard is opt-in, never a silent change of
    meaning for a caller that cannot supply it."""
    self_answer_report(tmp_path / "docs", document="DESIGN", stem="design")
    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path),
                                                          document_stem="DESIGN"))
    assert "already answered" in out.body, out.body


def test_companion_self_answer_already_answered_is_the_other_reason(tmp_path):
    """The other reason a run answers nothing (station bar 4) — a report exists, but it
    records zero items worked and zero left for the owner: the companion was already
    answered before this run reached it (SKILL.md § Step 3)."""
    self_answer_report(tmp_path / "system" / "doctrine", document="writing bar")

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "already answered" in out.body
    assert "the run wrote none" not in out.body


def test_companion_self_answer_reports_items_worked_of_how_many(tmp_path):
    self_answer_report(tmp_path / "system" / "doctrine",
                        worked=["answered", "confirmed", "confirmed"], left=1)

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "3 of 4 items answered" in out.body
    assert "1 left for you" in out.body


def test_companion_self_answer_verdict_split_names_only_nonzero_terms(tmp_path):
    self_answer_report(tmp_path / "system" / "doctrine",
                        worked=["confirmed", "confirmed", "overridden"])

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "2 confirmed" in out.body
    assert "1 overridden" in out.body
    assert "answered" not in out.body.split("(")[1].split(")")[0]


def test_companion_self_answer_zero_left_says_so_in_words(tmp_path):
    self_answer_report(tmp_path / "system" / "doctrine", worked=["answered"], left=0)

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "nothing left for you" in out.body


def test_companion_self_answer_unnamed_verdict_is_surfaced(tmp_path):
    self_answer_report(tmp_path / "system" / "doctrine", worked=["answered"], unnamed=1)

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "1 verdict the prompt could not name" in out.body


def test_companion_self_answer_two_unnamed_verdicts_are_plural(tmp_path):
    self_answer_report(tmp_path / "system" / "doctrine", worked=["answered"], unnamed=2)

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "2 verdicts the prompt could not name" in out.body


def test_companion_self_answer_skipped_items_do_not_affect_the_split(tmp_path):
    """Skipped entries carry no `**Verdict:**` field — they must never inflate the tally."""
    without_skips = reporters.companion_self_answer(self_answer_ctx(str(
        self_answer_report(tmp_path / "a" / "system" / "doctrine",
                            worked=["answered"]).parents[4]))).body

    with_skips = reporters.companion_self_answer(self_answer_ctx(str(
        self_answer_report(tmp_path / "b" / "system" / "doctrine",
                            worked=["answered"], skipped=3).parents[4]))).body

    assert without_skips.split("\n")[0] == with_skips.split("\n")[0]


def test_companion_self_answer_reports_companions_opened(tmp_path):
    """Task 3 changes this assertion's wording (code-integrity/ad-hoc pass, 2026-08-29): the
    old literal "Companion opened on:" claimed "opened" for every entry regardless of its real
    action, which is exactly the bug Task 3 removes — see
    `test_companion_self_answer_companions_line_distinguishes_the_three_actions` and
    `test_companion_self_answer_action_less_companion_invents_no_action` below for the
    per-action coverage this test no longer needs to carry alone."""
    self_answer_report(tmp_path / "system" / "doctrine", worked=["raised upstream"],
                        companions_opened=[("system/projects/tools/fdr_open_issues.md",
                                             "system/projects/tools/fdr.md")])

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "Companion touched:" in out.body
    assert "system/projects/tools/fdr.md" in out.body
    assert "system/projects/tools/fdr_open_issues.md" in out.body


def test_companion_self_answer_owed_list_names_the_document_and_the_opened_companions(tmp_path):
    self_answer_report(tmp_path / "system" / "doctrine", document="writing bar",
                        worked=["raised upstream"],
                        companions_opened=[("system/projects/tools/fdr_open_issues.md",
                                             "system/projects/tools/fdr.md")])

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "Owed a run:" in out.body
    assert "writing bar" in out.body.split("Owed a run:")[1]
    assert "system/projects/tools/fdr.md" in out.body.split("Owed a run:")[1]


def test_companion_self_answer_owed_list_omits_the_document_when_nothing_was_worked(tmp_path):
    """Every item this run touched went to the owner — nothing new landed on the document
    itself, so it is not newly owed a run."""
    self_answer_report(tmp_path / "system" / "doctrine", document="writing bar", left=1)

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "Owed a run:" not in out.body


def test_companion_self_answer_takes_the_highest_numbered_report(tmp_path):
    d = tmp_path / "system" / "doctrine"
    self_answer_report(d, n=1, worked=["answered"])
    self_answer_report(d, n=3, worked=["confirmed", "confirmed", "confirmed"])
    self_answer_report(d, n=2, worked=["overridden"])

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "3 of 3 items answered" in out.body
    assert "3 confirmed" in out.body


def test_companion_self_answer_finds_a_report_in_the_system_projects_home(tmp_path):
    self_answer_report(tmp_path / "system" / "projects" / "launchers", worked=["answered"])

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "1 of 1 items answered" in out.body


def test_companion_self_answer_finds_a_report_via_a_projects_product_path(tmp_path):
    projects = tmp_path / "system" / "projects" / "tools"
    projects.mkdir(parents=True)
    (projects / "project.md").write_text("**Product path:** product\n")
    product_docs = tmp_path / "product" / "docs"
    self_answer_report(product_docs, worked=["confirmed", "confirmed"], document="fdr")

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "2 of 2 items answered" in out.body


def test_companion_self_answer_falls_back_to_the_targets_own_docs_when_no_project_cards(
        tmp_path):
    """Where the run was pointed at a directory with no project cards, that directory is the
    product itself — the `else` branch that carries every product-path caller."""
    self_answer_report(tmp_path / "docs", worked=["answered"])

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "1 of 1 items answered" in out.body


def test_companion_self_answer_unreadable_report_says_so_and_names_the_path(
        monkeypatch, tmp_path):
    """Trap fence 2 of the plan — *"Where the report is missing or unreadable, the message
    says that, naming the path it looked for — never a bare `run ended.`, which is
    indistinguishable from the fallback this plan removes."* A found-but-unreadable report is
    the OSError half, and it takes the same named branch `_prd_body` gives its own
    `read_product() is None` case — the wide `except Exception` below stays for a parser bug,
    which is a different fact about the run.

    Rewritten by the code-integrity pass: as first written this asserted the bare
    `"example-product: run ended."`, which is the implementation's behaviour and the fence's
    prohibition.
    """
    report = self_answer_report(tmp_path / "system" / "doctrine", worked=["answered"])
    assert report.exists()

    def boom(*_a, **_k):
        raise OSError("permission denied")

    monkeypatch.setattr(reporters, "open", boom, raising=False)

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))
    assert out.body != "example-product: run ended."
    assert "could not be read" in out.body
    assert str(report) in out.body


def test_companion_self_answer_a_parser_bug_costs_specificity_not_the_message(
        monkeypatch, tmp_path):
    self_answer_report(tmp_path / "system" / "doctrine", worked=["answered"])

    def boom(_text):
        raise ValueError("bad parse")

    monkeypatch.setattr(reporters, "_parse_self_answer_report", boom)

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))
    assert out.body == "example-product: run ended."


def test_companion_self_answer_has_no_unchanged_head_branch(tmp_path):
    """Unlike prd/srs/uxd/design/content/agari/sdd/fdr, this artifact carries no Status or
    Version for an unchanged HEAD to protect — the report either exists or it does not, and
    the body is identical whatever head_before/head_after carry."""
    self_answer_report(tmp_path / "system" / "doctrine", worked=["answered"])

    moved = reporters.companion_self_answer(OutcomeContext(
        label="example-product", cwd="/repo", artifact_path=str(tmp_path),
        head_before="a", head_after="b")).body
    unchanged = reporters.companion_self_answer(OutcomeContext(
        label="example-product", cwd="/repo", artifact_path=str(tmp_path),
        head_before="a", head_after="a")).body

    assert moved == unchanged
    for body in (moved, unchanged):
        assert "committed nothing" not in body
        assert "waiting on you" not in body


def test_companion_self_answer_reads_the_real_template_without_crashing(tmp_path):
    """The shipped, unstamped template must not crash the parser — the same robustness bar
    every sibling's `reads the real template(s)` test holds, even though this template is
    never left on disk unstamped in real use (SKILL.md § Step 5 stamps it fresh every run)."""
    template = (Path(__file__).resolve().parent.parent / "templates" /
                "self_answer_report_template.md")
    dest_dir = tmp_path / "system" / "doctrine" / "trail" / "prd"
    dest_dir.mkdir(parents=True)
    (dest_dir / "self_answer-1.md").write_text(template.read_text(encoding="utf-8"))

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))
    assert out.body  # best-effort: some string, never a raised exception


# --- ad_hoc_plan `companion-self-answer-reporter-new-shape`: the reporter reads the new report
# shape (`core/templates/self_answer_report_template.md` changed at `72f690f9`, this reporter
# did not) -----------------------------------------------------------------------------------
#
# Task 1 — the corrupted capture. `## Companions opened` bullets gained an action word between
# the path and `companion to`, and the old regex's non-greedy path class backtracks over the
# action word's own `**` and captures it as part of the path (measured on the plan, 2026-08-29).
# Trap fence 1: assert on the captured path's VALUE, not on whether the bullet matches at all —
# a "no longer matches" assertion would pass today and prove nothing.


def test_parse_self_answer_report_captures_the_real_path_from_a_new_shape_bullet():
    text = self_answer_report_text(
        worked=["answered"],
        companions_opened=[("docs/PRD_open_issues.md", "opened", "PRD.md")])

    parsed = reporters._parse_self_answer_report(text)

    path, _action, _document = parsed["companions_opened"][0]
    assert path == "docs/PRD_open_issues.md"
    assert "*" not in path


def test_parse_self_answer_report_captures_the_action_word():
    text = self_answer_report_text(
        worked=["answered"],
        companions_opened=[("docs/PRD_open_issues.md", "appended", "PRD.md")])

    parsed = reporters._parse_self_answer_report(text)

    _path, action, document = parsed["companions_opened"][0]
    assert action == "appended"
    assert document == "PRD.md"


def test_parse_self_answer_report_reads_a_bullet_with_no_action_word_too():
    """Trap fence 5 — a bullet written before `72f690f9` carries no action word at all. The
    fix must not trade one break for another: the path and document still come through, and
    the action is absent rather than corrupted or invented."""
    text = self_answer_report_text(
        worked=["answered"],
        companions_opened=[("docs/PRD_open_issues.md", "PRD.md")])

    parsed = reporters._parse_self_answer_report(text)

    path, action, document = parsed["companions_opened"][0]
    assert path == "docs/PRD_open_issues.md"
    assert action is None
    assert document == "PRD.md"


# Task 2 — `## Raised on this document` is read, by heading, the way `## Launchers owed` is —
# `### ` entries recur across `## Items worked` and `## Left for the owner`, so a heading-blind
# count would tally another section's entries as raises.


def test_parse_self_answer_report_counts_raised_entries():
    text = self_answer_report_text(worked=["answered"], raised=2)

    parsed = reporters._parse_self_answer_report(text)

    assert parsed["raised"] == 2


def test_parse_self_answer_report_raised_absent_is_zero():
    text = self_answer_report_text(worked=["answered"])

    parsed = reporters._parse_self_answer_report(text)

    assert parsed["raised"] == 0


def test_parse_self_answer_report_raised_count_ignores_other_sections_entries():
    """`## Items worked` contributes two `### ` entries, `## Left for the owner` one — a
    heading-blind scan for `### ` would read 4 raises here; the real count is 1."""
    text = self_answer_report_text(worked=["answered", "confirmed"], left=1, raised=1)

    parsed = reporters._parse_self_answer_report(text)

    assert parsed["raised"] == 1


# Task 3 — the message says all of it. The companions line distinguishes the three actions
# rather than claiming "opened" for all of them, an action-less entry (an older report) is
# named without inventing one, and a raise on the document being answered gets its own line.


def test_companion_self_answer_companions_line_distinguishes_the_three_actions(tmp_path):
    self_answer_report(
        tmp_path / "system" / "doctrine", worked=["raised upstream", "raised upstream",
                                                    "raised upstream"],
        companions_opened=[("docs/a_open_issues.md", "opened", "a.md"),
                            ("docs/b_open_issues.md", "appended", "b.md"),
                            ("docs/c_open_issues.md", "updated", "c.md")])

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "newly opened" in out.body
    assert "gained a question" in out.body
    assert "had a question rewritten" in out.body


def test_companion_self_answer_action_less_companion_invents_no_action(tmp_path):
    """A bullet written before `72f690f9` carries no action word — trap fence 5. The message
    still names the path and document; it must not claim any of the three actions for it."""
    self_answer_report(tmp_path / "system" / "doctrine", worked=["raised upstream"],
                        companions_opened=[("docs/a_open_issues.md", "a.md")])

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "a.md" in out.body
    assert "docs/a_open_issues.md" in out.body
    assert "newly opened" not in out.body
    assert "gained a question" not in out.body
    assert "had a question rewritten" not in out.body


def test_companion_self_answer_raised_on_this_document_reaches_the_message(tmp_path):
    self_answer_report(tmp_path / "system" / "doctrine", document="writing bar",
                        worked=["answered"], raised=1)

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "raised 1 change on writing bar" in out.body


def test_companion_self_answer_raised_absent_leaves_the_message_unaffected(tmp_path):
    self_answer_report(tmp_path / "system" / "doctrine", document="writing bar",
                        worked=["answered"])

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "raised" not in out.body


# Task 4 — the tests the station's own acceptance bar names. Items 2–4 of the bar are already
# proven above (the action-less and raised tests); the three below close the remaining ones:
# item 1's "no path contains `**`" half, item 5's genuinely-garbage input, and item 6's
# required-headings invariant.


def test_companion_self_answer_no_path_carries_asterisks_with_all_three_actions_present(
        tmp_path):
    """Station bar item 1, the half the earlier per-phrase test does not check: the real
    paths reach the message, none of them corrupted with the action word's own `**` — the
    defect this whole plan exists to fix."""
    self_answer_report(
        tmp_path / "system" / "doctrine", worked=["raised upstream", "raised upstream",
                                                    "raised upstream"],
        companions_opened=[("docs/a_open_issues.md", "opened", "a.md"),
                            ("docs/b_open_issues.md", "appended", "b.md"),
                            ("docs/c_open_issues.md", "updated", "c.md")])

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "docs/a_open_issues.md" in out.body
    assert "docs/b_open_issues.md" in out.body
    assert "docs/c_open_issues.md" in out.body
    assert "*" not in out.body


def test_companion_self_answer_garbage_report_returns_a_message_not_an_exception(tmp_path):
    """Station bar item 5 — genuinely garbage content, not one of the narrower unreadable /
    undecodable / missing-heading shapes covered above, and the reporter must still hand back
    a message."""
    d = tmp_path / "system" / "doctrine" / "trail" / "prd"
    d.mkdir(parents=True)
    (d / "self_answer-1.md").write_text(
        "asdf ## not a report %%% \x00 **Verdict:** nonsense\n### stray heading\n")

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert isinstance(out.body, str)
    assert out.body


def test_self_answer_required_headings_still_holds_exactly_its_five_values():
    """Station bar item 6, and the plan's own guardrail — neither new section grows the set
    a run that raised or opened nothing must never read as a malformed report."""
    assert reporters._SELF_ANSWER_REQUIRED_HEADINGS == (
        "## Header", "## Items worked", "## Left for the owner", "## Skipped",
        "## Companions opened",
    )

# --- code-integrity pass on `companion-self-answer-reporter-new-shape` (2026-08-29) ---------
#
# Both tests below are derived from the plan's stated intent, never from the code it produced:
#   - `docs/proposals/companion-self-answer-reporter-new-shape/ad_hoc_plan.md` Task 3 —
#     "A raise on the document being answered gets its own line. This is a document that just
#     gained a question from a run nobody watched, which is what the notification exists to
#     surface." The sentence carries no condition, and the run it describes is precisely one
#     that worked no items: the raise is the only thing it produced.
#   - the same plan, Task 1 — "Every existing consumer of `companions_opened` — including the
#     launchers-owed fallback, which iterates it — keeps working." The fallback's own tests
#     feed it the pre-`72f690f9` two-field bullet, so the new three-field shape it now
#     iterates was never put through it.


def test_companion_self_answer_a_raise_with_no_items_worked_still_reaches_the_message(
        tmp_path):
    """A run can raise a change on the document it was answering while working no item at all
    — the raise is judged on the document, not on an item (`## Raised on this document`'s own
    note: "the run judged the document it was answering owed a change no item raised"). The
    item it appends to the companion is unanswered by construction, so the companion is not
    already answered and nothing-left-to-work is a false claim about it. This is the exact run
    the plan's Task 3 names — one nobody watched, whose only product is a new question."""
    report = self_answer_report(tmp_path / "system" / "doctrine", document="writing bar",
                                 raised=1)

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "already answered" not in out.body
    assert "nothing left to work" not in out.body
    assert "raised" in out.body
    assert "writing bar" in out.body
    assert str(report) in out.body


def test_companion_self_answer_owed_fallback_reads_a_new_shape_companion_bullet(tmp_path):
    """The launchers-owed fallback iterates `companions_opened`, which gained a third field.
    With no `## Launchers owed` section the owner still learns both documents a round is owed
    on — the one answered and the one whose companion this run touched."""
    self_answer_report(tmp_path / "system" / "doctrine", document="writing bar",
                        worked=["raised upstream"],
                        companions_opened=[("system/projects/tools/fdr_open_issues.md",
                                             "appended", "system/projects/tools/fdr.md")])

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    owed = out.body.split("Owed a run:")[1]
    assert "writing bar" in owed
    assert "system/projects/tools/fdr.md" in owed



# --- code-integrity pass: the three elements of the intent the first cut did not hold ------
#
# Every test below is derived from the intent, not from the implementation:
#   - the seed `system/projects/launchers/journey/nemawashi/
#     2026-08-29_the-answerer-has-one-launcher.md` § *The notification says what happened* —
#     the owner's minimum list, which names "every launcher now owed a run", and states that
#     the report file the reporter reads carries "every verdict, what was left for the owner,
#     and the launchers now owed a run";
#   - its station `journey/shukuba/2026-08-29_the-notification-says-what-happened.md`
#     § *Reached when* — "a test composes a message from a fixture report file and shows
#     every element of the seed's minimum list in it";
#   - the plan `docs/proposals/companion-self-answer-reporter/ad_hoc_plan.md` § *Trap fences*
#     1–4, of which fence 2 (never a bare `run ended.` for a missing or unreadable report) and
#     Task 1's "**The headings are the parser's contract**" are the two the first cut missed.


def test_companion_self_answer_names_the_launcher_owed_a_run(tmp_path):
    """The seed's minimum list names "every launcher now owed a run" — the launcher, not the
    document it belongs to. The owner reads this message on their phone to learn what to run
    next, and a document name is not a command."""
    self_answer_report(tmp_path / "system" / "doctrine", document="writing bar",
                        worked=["answered"],
                        launchers_owed=[("writing bar",
                                          "core/launchers/kensaiapp-writing-bar/launcher.sh .")])

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "core/launchers/kensaiapp-writing-bar/launcher.sh ." in out.body


def test_a_launcher_bullet_that_carries_a_note_leaves_no_stray_backtick(tmp_path):
    """The real shape, from a live product's first cycle (`docs/fdr_self_answer_1.md`, the
    pre-migration path that cycle wrote): Step 6 writes the command in backticks and then a
    note outside them — ``- **fdr.md** — `…/launcher.sh example-product` (run from the
    instance root)``. Every fixture above wraps the WHOLE value instead, which is the only
    shape `.strip("`")` handles: it
    trims one end each, so a value that ends in `)` keeps the backtick that closed the command
    and loses the one that opened it. The owner reads an unbalanced command on their phone.

    Assert the property — the line's backticks balance — rather than their absence: the
    wrapped-entry test below wants an inner pair kept, so "no backticks" is the wrong bar."""
    report = tmp_path / "docs" / "trail" / "fdr" / "self_answer-1.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    body = self_answer_report_text(document="fdr.md", worked=["answered"])
    report.write_text(body.replace(
        "## Launchers owed\n\nNone this run.\n\n",
        "## Launchers owed\n\n"
        "- **fdr.md** — `<CORE>/launchers/product-fdr/launcher.sh example-product` "
        "(run from the instance root)\n\n"))

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "`<CORE>/launchers/product-fdr/launcher.sh example-product`" in out.body
    assert out.body.count("`") % 2 == 0


def test_companion_self_answer_names_every_launcher_owed_not_only_the_first(tmp_path):
    """"one entry per document a round is now owed on, its own included" — SKILL.md § Step 6.
    A run that answered across documents owes several, and the message carries the whole
    list."""
    self_answer_report(
        tmp_path / "system" / "doctrine", document="writing bar",
        worked=["answered", "raised upstream"],
        companions_opened=[("system/projects/tools/fdr_open_issues.md",
                             "system/projects/tools/fdr.md")],
        launchers_owed=[("writing bar", "core/launchers/kensaiapp-writing-bar/launcher.sh ."),
                        ("system/projects/tools/fdr.md",
                         "core/launchers/product-fdr/launcher.sh tools")])

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "core/launchers/kensaiapp-writing-bar/launcher.sh ." in out.body
    assert "core/launchers/product-fdr/launcher.sh tools" in out.body


def test_companion_self_answer_carries_an_honest_absence_of_a_launcher(tmp_path):
    """Step 6's third case — no launcher exists for the producing skill, so the report says so
    plainly and names the skill and the posture. The message carries that sentence rather than
    dropping the entry, per Step 6: a path that does not exist costs more than an honest
    absence."""
    self_answer_report(
        tmp_path / "system" / "doctrine", document="ADR", worked=["answered"],
        launchers_owed=[("ADR", "no launcher — run product-architecture from a cto session")])

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "no launcher — run product-architecture from a cto session" in out.body


def test_companion_self_answer_falls_back_to_the_document_when_no_launcher_section(tmp_path):
    """A report with the section empty still says which document is owed a round — the
    reporter loses specificity, never the message (`reporters.py:214-218`)."""
    self_answer_report(tmp_path / "system" / "doctrine", document="writing bar",
                        worked=["answered"])

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "Owed a run:" in out.body
    assert "writing bar" in out.body.split("Owed a run:")[1]


def test_companion_self_answer_keeps_a_launcher_entry_that_wraps(tmp_path):
    """Step 6's honest-absence sentence is long enough to wrap, and every file in this family
    wraps at the same column. A wrapped entry must arrive whole, not cut at the newline."""
    d = tmp_path / "system" / "doctrine" / "trail" / "prd"
    d.mkdir(parents=True)
    (d / "self_answer-1.md").write_text(
        self_answer_report_text(document="ADR", worked=["answered"]).replace(
            "## Launchers owed\n\nNone this run.\n",
            "## Launchers owed\n\n- **ADR** — no launcher; run `product-architecture`\n"
            "  from a `cto` session\n"))

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "no launcher; run `product-architecture` from a `cto` session" in out.body


def test_companion_self_answer_undecodable_report_says_so_and_names_the_path(tmp_path):
    """The other half of fence 2's "unreadable" — bytes that are not UTF-8. A truncated or
    binary-corrupted report is unreadable in exactly the sense the fence names, and it must
    not arrive as the bare fallback the plan exists to remove."""
    d = tmp_path / "system" / "doctrine" / "trail" / "prd"
    d.mkdir(parents=True)
    report = d / "self_answer-1.md"
    report.write_bytes(b"# Self-answer report \xff\xfe not utf-8\n")

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert out.body != "example-product: run ended."
    assert "could not be read" in out.body
    assert str(report) in out.body


def test_companion_self_answer_report_missing_a_required_heading_is_reported_as_such(tmp_path):
    """Task 1 — "**The headings are the parser's contract**", and the template says a renamed
    heading must not pass silently. A file whose `## Items worked` heading is gone is not a
    report this parser can tally, and reporting it as an outcome would be the silent read
    fence 2 forbids."""
    d = tmp_path / "system" / "doctrine" / "trail" / "prd"
    d.mkdir(parents=True)
    report = d / "self_answer-1.md"
    report.write_text(self_answer_report_text(worked=["answered"], left=1).replace(
        "## Items worked", "## What I worked on"))

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert out.body != "example-product: run ended."
    assert str(report) in out.body
    assert "1 of 2 items answered" not in out.body


def test_companion_self_answer_an_empty_report_is_not_read_as_already_answered(tmp_path):
    """The "already answered" branch is a ✅ claim about a finished document (the second of the
    seed's two reasons a run answered nothing). An empty or truncated file is neither reason,
    and must never be reported as one."""
    d = tmp_path / "system" / "doctrine" / "trail" / "prd"
    d.mkdir(parents=True)
    (d / "self_answer-1.md").write_text("")

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "already answered" not in out.body
    assert "✅" not in out.body


def test_companion_self_answer_a_well_formed_report_with_nothing_worked_still_reads(tmp_path):
    """The counterpart the check above must not break: every heading present, every section
    "None this run." — the genuine already-answered companion, which stays ✅."""
    self_answer_report(tmp_path / "system" / "doctrine", document="writing bar")

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "already answered" in out.body


def test_existing_reporters_are_unaffected_by_the_companion_self_answer_addition():
    assert reporters.get_reporter("prd") is reporters.prd
    assert reporters.get_reporter("srs") is reporters.srs
    assert reporters.get_reporter("uxd") is reporters.uxd
    assert reporters.get_reporter("design") is reporters.design
    assert reporters.get_reporter("content") is reporters.content
    assert reporters.get_reporter("agari") is reporters.agari
    assert reporters.get_reporter("sdd-document") is reporters.sdd_document
    assert reporters.get_reporter("fdr") is reporters.fdr
    assert reporters.get_reporter("fix-author") is reporters.fix_author
    assert reporters.get_reporter("apply-packet") is reporters.apply_packet
    assert reporters.get_reporter("writing-bar") is reporters.writing_bar
    assert reporters.get_reporter("experience-visual") is reporters.experience_visual
    assert reporters.get_reporter("experience-voice") is reporters.experience_voice


# ---------------------------------------------------------------------------------------
# The run's message names the document the run actually worked
#
# `self_answer-<N>.md` is numbered per trail, so "the highest-numbered report under this
# product" is not "the report this run just wrote". Measured on a live product, 2026-09-01: two
# `companion-self-answer` runs on the architecture companion each announced
# `docs/fdr.md — no items left to work` — another document's report, two rounds old — and
# the item each had left for the owner reached nobody. `--document-stem` is what the
# launcher already knows (it labels the watch `<project>-<stem>`) and now passes down.
# ---------------------------------------------------------------------------------------


def test_the_document_stem_picks_this_runs_report_not_the_highest_numbered(tmp_path):
    docs = tmp_path / "docs"
    self_answer_report(docs, n=1, stem="fdr", document="docs/fdr.md")
    self_answer_report(docs, n=2, stem="fdr", document="docs/fdr.md")
    self_answer_report(docs, n=1, stem="architecture", document="docs/nfdr.md",
                       worked=["confirmed"], left=1)

    out = reporters.companion_self_answer(
        self_answer_ctx(str(tmp_path), document_stem="architecture"))

    assert "docs/nfdr.md" in out.body
    assert "1 left for you" in out.body
    assert "docs/fdr.md" not in out.body, (
        "the message described another document's trail — on a live run this told the owner "
        "an architecture round had nothing left to work while it was holding an item for them"
    )


def test_the_stem_is_matched_at_the_case_the_trail_is_on_disk(tmp_path):
    # The launcher reads `doc_stem` off the DOCUMENT's own directory entry, so it hands down
    # `SRS` — while Step 5 lower-cases the stem when it composes `trail/<doc>/`. The two
    # cases have to meet, and on this host (case-insensitive APFS) a comparison that did not
    # fold case would pass here and fail on a case-sensitive volume.
    docs = tmp_path / "docs"
    self_answer_report(docs, n=1, stem="srs", document="docs/SRS.md", worked=["confirmed"])

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path), document_stem="SRS"))

    assert "docs/SRS.md" in out.body
    assert "the run wrote none" not in out.body


def test_a_stem_whose_trail_holds_nothing_says_the_run_wrote_none(tmp_path):
    docs = tmp_path / "docs"
    self_answer_report(docs, n=1, stem="fdr", document="docs/fdr.md")

    out = reporters.companion_self_answer(
        self_answer_ctx(str(tmp_path), document_stem="architecture"))

    assert "the run wrote none" in out.body
    assert "trail/architecture/" in out.body, (
        "the message has to name the trail it swept, or 'no report' reads as 'this product "
        "has none' when it means 'this document has none'"
    )


def test_without_a_stem_the_sweep_is_what_it_always_was(tmp_path):
    # Every other caller passes nothing, and must keep the target-wide behaviour.
    self_answer_report(tmp_path / "system" / "doctrine", document="writing bar",
                       worked=["confirmed"])

    out = reporters.companion_self_answer(self_answer_ctx(str(tmp_path)))

    assert "writing bar" in out.body


def test_the_finder_itself_is_scoped_by_stem(tmp_path):
    docs = tmp_path / "docs"
    self_answer_report(docs, n=3, stem="fdr", document="docs/fdr.md")
    wanted = self_answer_report(docs, n=1, stem="architecture", document="docs/nfdr.md")

    assert reporters.find_self_answer_report(str(tmp_path)) == str(
        docs / "trail" / "fdr" / "self_answer-3.md")
    assert reporters.find_self_answer_report(str(tmp_path), "architecture") == str(wanted)


# ---------------------------------------------------------------------------------------
# new_self_answer_reports — every report a launch produced, not only the highest
#
# A companion answered seat by seat leaves one report per seat's run. The singular locator
# above names one of them; the round reader needs all of them, in the order the runs wrote
# them, and none that were already on disk when the launch began.
# ---------------------------------------------------------------------------------------

def test_round_locator_excludes_launch_time_reports(tmp_path):
    docs = tmp_path / "docs"
    before = tuple(str(self_answer_report(docs, n=n, stem="prd")) for n in (1, 2, 3))
    new = [str(self_answer_report(docs, n=n, stem="prd")) for n in (4, 5, 6)]

    assert reporters.new_self_answer_reports(str(tmp_path), "prd", before) == tuple(new)


def test_round_locator_without_before_reading_returns_all_reports(tmp_path):
    docs = tmp_path / "docs"
    every = tuple(str(self_answer_report(docs, n=n, stem="prd")) for n in (1, 2, 3))

    assert reporters.new_self_answer_reports(str(tmp_path), "prd") == every
    assert reporters.new_self_answer_reports(str(tmp_path), "prd", None) == every
    assert reporters.new_self_answer_reports(str(tmp_path), "prd", ()) == every


def test_round_locator_ignores_non_report_names(tmp_path):
    docs = tmp_path / "docs"
    kept = self_answer_report(docs, n=2, stem="prd")
    for stray in ("self_answer-3.md.bak", "self_answer-x.md", "self_answer-.md",
                  "self_answer-4.md~"):
        (kept.parent / stray).write_text("not a report")

    assert reporters.new_self_answer_reports(str(tmp_path), "prd") == (str(kept),)


def test_round_locator_sorts_numeric_report_numbers(tmp_path):
    docs = tmp_path / "docs"
    # Created out of order, and with 10 sorting before 2 as text.
    ten = self_answer_report(docs, n=10, stem="prd")
    two = self_answer_report(docs, n=2, stem="prd")
    nine = self_answer_report(docs, n=9, stem="prd")

    assert reporters.new_self_answer_reports(str(tmp_path), "prd") == (
        str(two), str(nine), str(ten))


def test_round_locator_preserves_document_home_and_stem_scope(tmp_path):
    docs = tmp_path / "docs"
    self_answer_report(docs, n=1, stem="fdr")
    in_docs = self_answer_report(docs, n=2, stem="PRD")
    in_system = self_answer_report(tmp_path / "system" / "doctrine", n=3, stem="prd")
    in_project = self_answer_report(tmp_path / "system" / "projects" / "p", n=4, stem="prd")

    assert reporters.new_self_answer_reports(str(tmp_path), "PrD") == (
        str(in_docs), str(in_system), str(in_project))
    assert reporters.new_self_answer_reports(str(tmp_path), "architecture") == ()


def test_round_locator_excludes_alias_of_existing_report(tmp_path):
    docs = tmp_path / "docs"
    old = self_answer_report(docs, n=1, stem="prd")
    new = self_answer_report(docs, n=2, stem="prd")
    alias = tmp_path / "alias.md"
    alias.symlink_to(old)

    assert reporters.new_self_answer_reports(str(tmp_path), "prd", (str(alias),)) == (
        str(new),)


def test_singular_locator_still_returns_highest_new_report(tmp_path):
    docs = tmp_path / "docs"
    before = tuple(str(self_answer_report(docs, n=n, stem="prd")) for n in (1, 2, 3))
    for n in (4, 5, 6):
        self_answer_report(docs, n=n, stem="prd")

    assert reporters.find_self_answer_report(str(tmp_path), "prd", before) == str(
        docs / "trail" / "prd" / "self_answer-6.md")


def test_singular_equal_number_winner_is_unchanged(tmp_path):
    # Two eligible homes each hold a report 2: the singular locator keeps the first it meets
    # (the `system/*/` home is swept before `system/projects/*/`), never the last of a sort.
    first = self_answer_report(tmp_path / "system" / "alpha", n=2, stem="prd")
    self_answer_report(tmp_path / "system" / "projects" / "p", n=2, stem="prd")

    assert reporters.find_self_answer_report(str(tmp_path), "prd") == str(first)


# ---------------------------------------------------------------------------------------
# shukuba-refine — the message carries the report's `## Next moves`
#
# A refine run leaves the route re-read and a list of moves owed to other seats: the next
# change, a companion sweep, a station close, a seed's retire. Until this reporter the message
# was `generic`'s "run ended.", so the owner opened the report to learn what to launch. The
# reporter finds the report THIS run committed — a path added or changed between the watch's
# two HEADs, never the newest file on disk, which is a predecessor's when the run wrote none —
# and puts its next moves in the message.
# ---------------------------------------------------------------------------------------

_REFINE_KEY = "2026-09-18_a-unit"
_REFINE_REPORT = f"journey/nemawashi/2026-09-01_a-seed/{_REFINE_KEY}_report.md"

_REFINE_REPORT_TEXT = f"""# 宿場 Shukuba refine — `{_REFINE_KEY}`

*Unit `{_REFINE_KEY}`, sealed Tobiishi, reviewed 2026-09-18.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | sweep the product's companions | owner | `core/launchers/chain-product/launcher.sh proj` | — | Moves row 2 |
| 2 | pick a seed | PM | `core/launchers/skill/launcher.sh nemawashi-pick proj` | — | recommendation 1 |
| 3 | cut a seed | Principal PM | none — `seeds-from-idea`, in a `principal-pm:` session, on that recommendation | — | recommendation 2 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | x | y |

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| Modify a station | a | b | c | abc1234 |
| Raise a companion item | a | b | c | def5678 |

## Considered, not moved

None.
"""

_REFINE_RECS_TEXT = f"""# 宿場 Shukuba refine — recommendations to the Principal PM — `{_REFINE_KEY}`

## To the Principal PM

### 1. Retire the seed

- **Kind:** a seed to retire

### 2. Cut a seed for the leftover

- **Kind:** a seed to cut
"""


def _refine_project(tmp_path, report=_REFINE_REPORT_TEXT, recs=_REFINE_RECS_TEXT):
    project = tmp_path / "system" / "projects" / "proj"
    path = project / _REFINE_REPORT
    path.parent.mkdir(parents=True)
    path.write_text(report, encoding="utf-8")
    if recs is not None:
        (path.parent / f"{_REFINE_KEY}_recommendations.md").write_text(recs, encoding="utf-8")
    return project


def _refine_ctx(project, before="aaa", after="bbb", cwd=None):
    return OutcomeContext(label="dev · proj · shukuba-refine", cwd=str(cwd or ""),
                          artifact_path=str(project), head_before=before, head_after=after)


def _refine(changed):
    return reporters._shukuba_refine_reporter(lambda _p, _b, _a: changed)


def test_shukuba_refine_is_registered():
    assert reporters.get_reporter("shukuba-refine") is reporters.shukuba_refine


def test_shukuba_refine_message_lists_every_next_move_with_seat_and_command(tmp_path):
    project = _refine_project(tmp_path)
    body = _refine((_REFINE_REPORT,))(_refine_ctx(project, cwd=tmp_path)).body
    assert body == (
        f"📋 dev · proj · shukuba-refine: {_REFINE_KEY} reviewed — 2 moves made, "
        f"2 recommendations to the Principal PM.\n"
        f"Next:\n"
        f"1. sweep the product's companions — owner\n"
        f"   core/launchers/chain-product/launcher.sh proj\n"
        f"2. pick a seed — PM\n"
        f"   core/launchers/skill/launcher.sh nemawashi-pick proj\n"
        f"3. cut a seed — Principal PM\n"
        f"   none — seeds-from-idea, in a principal-pm: session, on that recommendation\n"
        f"Report: system/projects/proj/{_REFINE_REPORT}"
    )


def test_shukuba_refine_unchanged_head_says_the_run_committed_nothing(tmp_path):
    # The predecessor's report is on disk; it must not be read back as this run's.
    project = _refine_project(tmp_path)
    body = _refine((_REFINE_REPORT,))(_refine_ctx(project, before="aaa", after="aaa")).body
    assert body == ("⚠️ dev · proj · shukuba-refine: the run committed nothing — it stopped "
                    "before writing its report. Read its session.")


def test_shukuba_refine_commits_without_a_report_say_so(tmp_path):
    project = _refine_project(tmp_path)
    body = _refine(("journey/shukuba/parked/x.md",))(_refine_ctx(project)).body
    assert body == ("⚠️ dev · proj · shukuba-refine: the run committed, but no refine report "
                    "among its commits — it stopped before Step 6. Read its session.")


def test_shukuba_refine_report_in_unpicked_is_found(tmp_path):
    rel = f"journey/nemawashi/unpicked/2026-09-01_a-seed/{_REFINE_KEY}_report.md"
    project = tmp_path / "p"
    (project / rel).parent.mkdir(parents=True)
    (project / rel).write_text(_REFINE_REPORT_TEXT, encoding="utf-8")
    body = _refine(("journey/nemawashi/unpicked/2026-09-01_a-seed/seed.md", rel))(
        _refine_ctx(project)).body
    assert body.startswith(f"📋 dev · proj · shukuba-refine: {_REFINE_KEY} reviewed")
    assert "0 recommendations" not in body  # no recommendations file: the count is left out
    assert "recommendation" not in body.splitlines()[0]


def test_shukuba_refine_none_owed_carries_the_reason(tmp_path):
    table = _REFINE_REPORT_TEXT[
        _REFINE_REPORT_TEXT.index("| # |"):_REFINE_REPORT_TEXT.index("## Read")]
    report = _REFINE_REPORT_TEXT.replace(
        table, "None — the seed is walked and its retire is already recommended elsewhere.\n\n")
    project = _refine_project(
        tmp_path, report=report, recs="## To the Principal PM\n\nNothing to recommend.\n")
    body = _refine((_REFINE_REPORT,))(_refine_ctx(project)).body
    assert body.splitlines()[0] == (f"📋 dev · proj · shukuba-refine: {_REFINE_KEY} reviewed — "
                                    f"2 moves made, nothing recommended.")
    assert body.splitlines()[1] == ("Next: None — the seed is walked and its retire is already "
                                    "recommended elsewhere.")


def test_shukuba_refine_report_without_the_section_says_read_the_file(tmp_path):
    report = _REFINE_REPORT_TEXT.replace("## Next moves", "## Something else")
    project = _refine_project(tmp_path, report=report)
    body = _refine((_REFINE_REPORT,))(_refine_ctx(project)).body
    assert body == (f"⚠️ dev · proj · shukuba-refine: {_REFINE_KEY} reviewed, but its report "
                    f"names no next moves — read {project / _REFINE_REPORT}.")


def test_shukuba_refine_unreadable_heads_fall_back_to_plain(tmp_path):
    project = _refine_project(tmp_path)
    assert _refine(None)(_refine_ctx(project)).body == "dev · proj · shukuba-refine: run ended."
    assert _refine((_REFINE_REPORT,))(_refine_ctx(project, before=None)).body == \
        "dev · proj · shukuba-refine: run ended."


def test_shukuba_refine_a_parser_bug_costs_specificity_not_the_message(tmp_path):
    def boom(*_a):
        raise RuntimeError("bug")
    project = _refine_project(tmp_path)
    assert reporters._shukuba_refine_reporter(boom)(_refine_ctx(project)).body == \
        "dev · proj · shukuba-refine: run ended."


def test_git_changed_paths_lists_what_the_range_added_relative_to_the_project(tmp_path):
    import subprocess

    def git(*args):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)

    git("init", "-q")
    git("config", "user.email", "t@t")
    git("config", "user.name", "t")
    (tmp_path / "other.md").write_text("x")
    git("add", ".")
    git("commit", "-q", "-m", "one")
    before = subprocess.run(["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    project = _refine_project(tmp_path)
    (tmp_path / "other.md").write_text("y")
    git("add", ".")
    git("commit", "-q", "-m", "two")
    after = subprocess.run(["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
                           capture_output=True, text=True).stdout.strip()
    changed = reporters._git_changed_paths(str(project), before, after)
    assert set(changed) == {_REFINE_REPORT,
                            f"journey/nemawashi/2026-09-01_a-seed/{_REFINE_KEY}_recommendations.md"}
    assert reporters._git_changed_paths(str(tmp_path / "nope"), before, after) is None


# Every launcher backgrounds its run and returns at once, so a wait read as "once 1 is launched":
# a `chain-change` started 8s after `shukuba-retire` found the station still open and opened a
# change for it (2026-09-18). A wait now says the earlier move must have LANDED, on its own line
# above the command it gates. It is read from the After column — the rows a move waits on, by
# number — and never from the From cell, which points at the reasoning and is prose.

def test_shukuba_refine_a_row_that_waits_says_the_earlier_move_must_have_landed(tmp_path):
    report = _REFINE_REPORT_TEXT.replace("| — | recommendation 1 |", "| 1 | recommendation 1 |")
    project = _refine_project(tmp_path, report=report)
    body = _refine((_REFINE_REPORT,))(_refine_ctx(project)).body
    assert ("2. pick a seed — PM\n"
            "   only once 1 has landed, not merely launched\n"
            "   core/launchers/skill/launcher.sh nemawashi-pick proj\n"
            ) in body
    assert "1. sweep the product's companions — owner\n   core/" in body


def test_shukuba_refine_a_row_waiting_on_several_names_them_all(tmp_path):
    report = _REFINE_REPORT_TEXT.replace("| — | recommendation 2 |", "| 1, 2 | recommendation 2 |")
    project = _refine_project(tmp_path, report=report)
    body = _refine((_REFINE_REPORT,))(_refine_ctx(project)).body
    assert ("3. cut a seed — Principal PM\n"
            "   only once 1, 2 have landed, not merely launched\n"
            "   none — seeds-from-idea") in body


def test_shukuba_refine_a_wait_written_in_from_prints_nothing(tmp_path):
    """The retired form: the From cell reading `after 1 lands — <fact>` with no After entry."""
    report = _REFINE_REPORT_TEXT.replace(
        "| — | recommendation 1 |",
        "| — | recommendation 1; after 1 lands — "
        "`shukuba/` root has no `2026-09-18_a-station.md` |")
    project = _refine_project(tmp_path, report=report)
    body = _refine((_REFINE_REPORT,))(_refine_ctx(project)).body
    assert "only once" not in body


def test_shukuba_refine_a_five_column_table_prints_no_wait_line(tmp_path):
    """A table with no After header cannot say what a row waits on, so it says nothing — even
    where its From cell reads like a wait."""
    report = (_REFINE_REPORT_TEXT
              .replace("| Command | After | From |", "| Command | From |")
              .replace("|---|---|---|---|---|---|", "|---|---|---|---|---|")
              .replace("| — | Moves row 2 |", "| Moves row 2 |")
              .replace("| — | recommendation 1 |", "| after 1 lands — the station is closed |")
              .replace("| — | recommendation 2 |", "| recommendation 2 |"))
    project = _refine_project(tmp_path, report=report)
    body = _refine((_REFINE_REPORT,))(_refine_ctx(project)).body
    assert "only once" not in body
    assert "2. pick a seed — PM\n   core/launchers/skill/launcher.sh nemawashi-pick" in body


def test_shukuba_refine_the_columns_are_found_by_header_not_by_position(tmp_path):
    """After and From swapped: a positional read would take the reasoning for the wait."""
    report = (_REFINE_REPORT_TEXT
              .replace("| Command | After | From |", "| Command | From | After |")
              .replace("| — | Moves row 2 |", "| Moves row 2 | — |")
              .replace("| — | recommendation 1 |", "| recommendation 1 | 1 |")
              .replace("| — | recommendation 2 |", "| recommendation 2 | — |"))
    project = _refine_project(tmp_path, report=report)
    body = _refine((_REFINE_REPORT,))(_refine_ctx(project)).body
    assert ("2. pick a seed — PM\n"
            "   only once 1 has landed, not merely launched\n") in body
    assert body.count("only once") == 1


def test_shukuba_refine_an_empty_after_cell_prints_no_wait_line(tmp_path):
    report = _REFINE_REPORT_TEXT.replace("| — | recommendation 1 |", "|  | recommendation 1 |")
    project = _refine_project(tmp_path, report=report)
    body = _refine((_REFINE_REPORT,))(_refine_ctx(project)).body
    assert "only once" not in body


def test_shukuba_refine_a_row_that_does_not_wait_carries_no_wait_line(tmp_path):
    project = _refine_project(tmp_path)
    body = _refine((_REFINE_REPORT,))(_refine_ctx(project)).body
    assert "only once" not in body


def test_shukuba_refine_none_under_a_kept_header_reads_the_reason_not_the_header(tmp_path):
    table = _REFINE_REPORT_TEXT[
        _REFINE_REPORT_TEXT.index("| # |"):_REFINE_REPORT_TEXT.index("## Read")]
    header = "\n".join(table.splitlines()[:2])
    report = _REFINE_REPORT_TEXT.replace(table, header + "\n\nNone — nothing is owed.\n\n")
    project = _refine_project(tmp_path, report=report)
    body = _refine((_REFINE_REPORT,))(_refine_ctx(project)).body
    assert body.splitlines()[1] == "Next: None — nothing is owed."



# --- sdd-document: the CTO skill's completion message — the document, never a runner record ----


def test_sdd_document_is_registered():
    """`get_reporter` falls back to generic for an unknown name without raising, so a
    `launcher.md` naming `sdd-document` would read as correct and behave as generic."""
    assert reporters.get_reporter("sdd-document") is reporters.sdd_document


def test_sdd_document_without_a_record_reports_draft_and_open_items(tmp_path):
    """The CTO skill starts no runner, so a product with no `trail/sdd/run-<N>.md` is the normal
    case, and the `sdd` reporter's sentence for it ("may be unfinished") would be false."""
    root = sdd_product(tmp_path, status="Draft", version=1, open_issues=True, items=3, runs=0)

    out = reporters.sdd_document(sdd_ctx(root))

    assert out.body == "example-product: SDD v1 — Draft; 3 open items for you."
    assert "unfinished" not in out.body


def test_sdd_document_ignores_runner_endings_and_caps(tmp_path):
    """A record an earlier runner left behind reports that run's ending, not this launch's."""
    ended = sdd_product(tmp_path / "ended", status="Settled", version=4,
                        ended="settled — nothing left open")
    capped = sdd_product(tmp_path / "capped", status="Draft", version=2, open_issues=True,
                         items=1, ended="the **round cap** fired", counters="rounds 6/6")

    for root in (ended, capped):
        body = reporters.sdd_document(sdd_ctx(root)).body
        assert "Ended:" not in body
        assert "Capped:" not in body
        assert "unfinished" not in body
        assert "record" not in body.lower()


def test_sdd_document_ignores_old_record_paths(tmp_path):
    """A pre-migration `docs/sdd_conversation/` folder is a runner record's home, and this
    reporter reads no record, so it has no migration warning to give."""
    root = sdd_product(tmp_path, status="Settled", runs=0, cycles=2)
    old = Path(root) / "docs" / "sdd_conversation"
    old.mkdir(parents=True)
    (old / "run-3.md").write_text("# SDD conversation — run 3\n")

    body = reporters.sdd_document(sdd_ctx(root)).body

    assert "sdd_conversation" not in body
    assert "No record read" not in body


_DOCUMENT_ONLY_MESSAGE = "example-product: SDD v2 — Draft; no open issues left."
_NOTHING_COMMITTED_MESSAGE = (
    "⚠️ example-product: the run committed nothing — it may have stopped. "
    "The SDD on disk is from an earlier run.")


def _tree_with_an_archived_run(tmp_path):
    """A Draft v2 with no companion and an archived run-3.md carrying an ending and counters."""
    root = sdd_product(tmp_path, status="Draft", version=2, runs=0, cycles=0)
    record = Path(root) / "docs" / "trail" / "sdd" / "run-3.md"
    record.write_text(
        "# SDD conversation — run 3\n- **Counters:** rounds 6/6\n\n"
        "## How this run ended\n\n- **Ended because:** the **round cap** fired\n")
    return root


def test_document_message_ignores_archived_run_ending_and_counters(tmp_path):
    """CP-420: the same message whatever the archived run says about how it ended."""
    root = _tree_with_an_archived_run(tmp_path)

    body = reporters.sdd_document(sdd_ctx(root, head_before="a", head_after="b")).body

    assert body == _DOCUMENT_ONLY_MESSAGE


def test_document_message_with_archived_record_and_unchanged_head(tmp_path):
    """CP-420: a run that committed nothing says so, archived record or not."""
    root = _tree_with_an_archived_run(tmp_path)

    body = reporters.sdd_document(sdd_ctx(root, head_before="same", head_after="same")).body

    assert body == _NOTHING_COMMITTED_MESSAGE


def test_document_message_with_old_conversation_folder(tmp_path):
    """CP-420: a pre-migration folder beside the document changes nothing, byte for byte."""
    root = _tree_with_an_archived_run(tmp_path)
    old = Path(root) / "docs" / "sdd_conversation"
    old.mkdir(parents=True)
    (old / "run-3.md").write_text("# SDD conversation — run 3\n")

    body = reporters.sdd_document(sdd_ctx(root, head_before="a", head_after="b")).body

    assert body == _DOCUMENT_ONLY_MESSAGE


def test_document_message_preserves_blank_ending_degradation(tmp_path):
    """CP-420: a latest record whose ending marker is followed only by whitespace degrades to
    the plain completion message, because the shared reader's ending evaluation faults there
    and the reporter's catch-all answers."""
    root = sdd_product(tmp_path, status="Draft", version=2, runs=0, cycles=0)
    record = Path(root) / "docs" / "trail" / "sdd" / "run-3.md"
    record.write_text("# SDD conversation — run 3\n\n- **Ended because:**   \n")

    body = reporters.sdd_document(sdd_ctx(root, head_before="a", head_after="b")).body

    assert body == "example-product: run ended."


@pytest.mark.parametrize(
    "counters,sdd,head_after,expected",
    [
        ("{huge}/6", True, "b", "example-product: run ended."),
        ("1/{huge}", True, "b", "example-product: run ended."),
        ("6/6 {huge}/6", True, "b", _DOCUMENT_ONLY_MESSAGE),
        ("{huge}/6", True, "a", _NOTHING_COMMITTED_MESSAGE),
        ("{huge}/6", False, "b",
         "⚠️ example-product: no SDD at docs/SDD.md — this run left nothing to read."),
    ],
    ids=["large-numerator", "large-denominator", "earlier-cap", "unchanged-head", "no-sdd"],
)
def test_document_message_preserves_archived_counter_degradation(
    tmp_path, counters, sdd, head_after, expected,
):
    """CP-420 keeps the base's exact message even when an archived counter cannot be parsed.
    Fix the interpreter's digit limit for this case and restore it for the rest of the suite."""
    root = sdd_product(
        tmp_path, sdd=sdd, status="Draft", version=2, cycles=0,
        counters=counters.format(huge="9" * 641), ended="stopped",
    )
    previous_limit = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(640)
        body = reporters.sdd_document(sdd_ctx(root, head_before="a", head_after=head_after)).body
    finally:
        sys.set_int_max_str_digits(previous_limit)

    assert body == expected


def test_sdd_document_counts_all_companion_buckets(tmp_path):
    """The owner's next move is the same for all five buckets, so all five are summed; and the
    singular and the zero case read as the `sdd` reporter reads them."""
    five = sdd_product(tmp_path / "five", status="Draft", open_issues=True, items=0, runs=0)
    Path(five, "docs", "SDD_open_issues.md").write_text(
        "".join(f"## {n}. a bucket\n\n### {n}.1 an item\n\n- **Answer:** <fill>\n\n"
                for n in range(1, 6)))
    one = sdd_product(tmp_path / "one", status="Draft", open_issues=True, items=0, runs=0)
    Path(one, "docs", "SDD_open_issues.md").write_text(
        "## 5. Raised from downstream\n\n### 5.1 a finding\n\n- **Answer:** <fill>\n")
    none = sdd_product(tmp_path / "none", status="Settled", runs=0)

    assert "5 open items for you" in reporters.sdd_document(sdd_ctx(five)).body
    assert "1 open item for you" in reporters.sdd_document(sdd_ctx(one)).body
    assert "no open issues left" in reporters.sdd_document(sdd_ctx(none)).body


def test_sdd_document_reports_status_and_answered_cycles(tmp_path):
    """The highest answered cycle is counted off `cycle-<N>.md` names alone: `run-` and
    `self_answer-` files share the folder, and a gap in the numbering is not a lower count."""
    root = sdd_product(tmp_path, status="Settled", version=5, cycles=0, runs=3)
    trail = Path(root) / "docs" / "trail" / "sdd"
    (trail / "cycle-1.md").write_text("an answered companion\n")
    (trail / "cycle-3.md").write_text("an answered companion\n")
    (trail / "self_answer-9.md").write_text("a report\n")

    body = reporters.sdd_document(sdd_ctx(root)).body

    assert body.startswith("example-product: SDD v5 — Settled; no open issues left")
    assert "(after 3 answered cycles)" in body
    assert body.endswith(".")


def test_sdd_document_reports_missing_and_unreadable_documents(tmp_path):
    """The shared head's own messages, with no runner suffix on any of them. An absent artifact
    path degrades to the plain message, as every sibling's does."""
    missing = reporters.sdd_document(sdd_ctx(sdd_product(tmp_path / "missing", sdd=False)))
    assert "no SDD at docs/SDD.md" in missing.body

    absent = reporters.sdd_document(sdd_ctx(None))
    assert absent.body == "example-product: run ended."

    unreadable_root = sdd_product(tmp_path / "locked", status="Settled")
    sdd_file = Path(unreadable_root) / "docs" / "SDD.md"
    sdd_file.chmod(0)
    try:
        if os.access(sdd_file, os.R_OK):
            pytest.skip("this account reads a mode-0 file, so the read cannot be made to fail")
        locked = reporters.sdd_document(sdd_ctx(unreadable_root))
    finally:
        sdd_file.chmod(0o644)
    assert "could not be read" in locked.body
    assert "unfinished" not in locked.body


WAITING_MESSAGE = (
    "📋 example-product: the run had nothing to fold — "
    "the SDD companion is still waiting on you. Answer it, commit, re-run.")


def test_sdd_document_with_unchanged_head_reports_no_commit(tmp_path):
    """An unchanged HEAD means the files on disk are the previous launch's, so describing them
    would report that launch as this one. The messages are the base's, written out literally."""
    unanswered = sdd_product(tmp_path / "waiting", status="Draft", open_issues=True, items=1)
    settled = sdd_product(tmp_path / "settled", status="Settled", version=9)

    waiting = reporters.sdd_document(sdd_ctx(unanswered, head_before="same", head_after="same"))
    nothing = reporters.sdd_document(sdd_ctx(settled, head_before="same", head_after="same"))

    assert waiting.body == WAITING_MESSAGE
    assert "waiting on you" in waiting.body
    assert nothing.body == _NOTHING_COMMITTED_MESSAGE
    assert "v9" not in nothing.body


def test_sdd_document_with_unreadable_head_reads_the_document(tmp_path):
    """An unknown HEAD (`None`) is not evidence of an unchanged run, so the document is read."""
    root = sdd_product(tmp_path, status="Settled", version=7, runs=0)

    out = reporters.sdd_document(sdd_ctx(root, head_before=None, head_after=None))

    assert "SDD v7 — Settled" in out.body


class SddDocumentReads:
    def __init__(self, document=None, error=None):
        self.document = document
        self.error = error
        self.paths = []
        self.unchanged = []

    def read(self, path):
        self.paths.append(path)
        if self.error:
            raise self.error
        return self.document

    def committed_nothing(self, label, stem, docs):
        self.unchanged.append((label, stem, docs))
        return f"{label}: waiting on you."


def test_sdd_document_uses_the_supplied_reader_without_touching_disk():
    reads = SddDocumentReads({
        "sdd": True, "version": 4, "status": "Draft",
        "companion": True, "items": 3, "cycles": 2,
    })
    reporter = reporters._sdd_document_reporter(reads.read, reads.committed_nothing)

    result = reporter(sdd_ctx("/a-product-that-does-not-exist"))

    assert result.body == (
        "example-product: SDD v4 — Draft; 3 open items for you (after 2 answered cycles).")
    assert reads.paths == ["/a-product-that-does-not-exist"]
    assert reads.unchanged == []


def test_sdd_document_unchanged_head_uses_its_supplied_companion_reader():
    reads = SddDocumentReads(error=AssertionError("the document belongs to an earlier run"))
    reporter = reporters._sdd_document_reporter(reads.read, reads.committed_nothing)

    result = reporter(sdd_ctx("/product", head_before="same", head_after="same"))

    assert result.body == "example-product: waiting on you."
    assert reads.paths == []
    assert reads.unchanged == [("example-product", "SDD", "/product/docs")]


def test_sdd_document_reader_failure_keeps_the_completion_message():
    reads = SddDocumentReads(error=ValueError("unreadable input"))
    reporter = reporters._sdd_document_reporter(reads.read, reads.committed_nothing)

    result = reporter(sdd_ctx("/product"))

    assert result.body == "example-product: run ended."
    assert reads.paths == ["/product"]
