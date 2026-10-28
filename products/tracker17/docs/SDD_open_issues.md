# SDD open issues — tracker17

> Companion to `SDD.md`. The CTO wrote the SDD; this file holds what that run could not settle from
> its inputs (the PRD, the SRS, the UXD, and any context or constraints), and the calls that are the
> CPO's or the CDO's to make. An item whose call is the CPO's or the CDO's carries that seat's
> `Seat:`; an item whose call is the CTO's carries `cto` or no `Seat:` field.
>
> **Answer inline** — fill each **Answer** / **Confirm or override** / **Keep or re-cut** /
> **Your call** slot — **commit this file**, then re-run `product-sdd`. It folds your answers into
> the SDD and drops the resolved items. When nothing is left open, `product-sdd` **deletes this
> file**: no file = the SDD is done.
>
> Your answers are never thrown away. Each time `product-sdd` folds them in, it first copies this
> file whole to `docs/trail/sdd/` — so what you decided, and why, stays readable and citable for good.
>
> **An item may name the seat that answers it.** Any item in any section carries an optional
> `- **Seat:** <seat>` field beside its other fields. Its value is the name of the agent whose posture
> answers the item — `cto`, `cpo` or `cdo`. An item with no usable value, whether the field is absent,
> empty or still the `<seat>` placeholder, is answered in the seat of the skill that produced this file.
> The field names the *answering* seat. It is not the seat that raised the item (`Raised by:` /
> `Held by:`), and it is not the document an answer belongs to.
>
> **An item in §§ 1–3 names the seat that raised it.** An item the CPO raised is a product call and
> an item the CTO raised is a technical one, and the answer that settles one does not settle the
> other. **§ 4 names two seats and no raiser** — a
> disagreement is not something one seat asked, it is two positions held by different seats, and the
> answer that settles it picks between them.
>
> **§ 5 names a raiser from outside the SDD's lanes entirely.** §§ 1–4 are all the SDD's own three
> lane seats; § 5 is a seat that never held a lane in it, reading it long after it settled and
> finding something only the SDD can fix. Its `Raised by:` therefore takes a wider set than §§ 1–3's,
> which stay fixed to the three lane seats on purpose.

> **No producing run wrote this file.** The PM opened it on 2026-10-28, after reading the product's
> deletion tests against § 4 RT-11 and § 11 R-12, to carry § 5.1. `product-sdd` has no record of writing it.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — a best-effort answer was drafted; confirm or override

### 2.1 § 4 RT-11, § 12 and the header still read the records at ADR-0011 and NFDR version 16
- **Raised by:** CTO
- **Seat:** cto
- **Drafted into the SDD:** nothing yet — the lean is this: RT-11's last sentence names ADR-0012 as
  the record of its boundary and ADR-0010 as superseded by it, the way RT-8 names ADR-0011 over
  ADR-0006, and drops "the record and the obligation for a deletion's pages are theirs to write";
  § 12 counts twelve records, ADR-0001 to ADR-0012; the header's *Inputs read* reads ADR-0012
  Accepted, ADR-0010 Superseded by ADR-0012, and NFDR version 17.
- **Rationale:** three facts in the document are false on disk. RT-11 says "The Principal Architect
  records the move's boundary as `adr/0010-…` … the record and the obligation for a deletion's
  pages are theirs to write (§ 12)" (`docs/SDD.md:L474-L478`); § 12 says "ADR-0001 to ADR-0011"
  (`:L1581-L1582`); the header's *Inputs read* says "ADR-0001 to ADR-0011 … NFDR Settled (version 16"
  (`:L6`). `adr/README.md` lists ADR-0012, Accepted 2026-10-28, and ADR-0010 "Superseded by
  ADR-0012"; ADR-0012 § Context says it follows SDD version 13 RT-11; `nfdr.md` is at version 17,
  its header naming ADR-0012. All three landed at `d459f69d9`. The obligation for a deletion's pages
  is written (QC-63 names the task deletion's `no-store` and 404 verifiers); what QC-63 still gets
  wrong is the Principal Architect's, carried on `docs/architecture_open_issues.md` § 3.1, not this
  document's.
- **If overridden:** nothing moves in any slice, fence or edge. The three lines stay false, and a
  reader of RT-11 is sent to a superseded record and told a record exists that has been written.
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

> **No producing run wrote this item.** A `companion-self-answer` run raised it on 2026-10-28 while
> answering § 5.1, after reading RT-11's last sentence, § 12 and the header against `adr/README.md`
> and `nfdr.md`'s header. `product-sdd` has no record of writing it. The fold's own input catch-up
> may reach the same lines unprompted; the item is here so that it is not missed.

## 3. Cut calls to confirm — where the slicing could reasonably have gone another way

None.

---

## 4. Disagreements — two seats hold different positions and neither yields

None.

## 5. Raised from downstream — an item from a seat that did not write the SDD

### 5.1 RT-11's test list and R-12's trigger still wait on deletion history tests that now exist
- **Raised by:** PM — 2026-10-28
- **Seat:** cto
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_delete-and-rename`
- **What it blocks:** nothing is blocked. A reader tracing RT-11 or R-12 to the suite is told a test
  is missing that is present.
- **Where it shows:** § 4 RT-11's *Tests* names "a deletion history test beside
  `tests/e2e/test_delete_task.py`'s `test_completion_survives_actual_reload_back_and_forward`, …
  which does not exist at `4a9ff47d2`" (`docs/SDD.md:L470-L474`), and § 11 R-12's *shows up as*
  names "the deletion history test `delete-and-rename`'s command half names once it exists"
  (`docs/SDD.md:L1564-L1565`). Both deletions' history tests now exist:
  `tests/e2e/test_delete_task.py`, `test_confirmation_is_loaded_afresh_after_confirming` (L182), and
  `tests/e2e/test_delete_project.py`, `test_project_confirmation_is_loaded_afresh_after_confirming`
  (L290). RT-11's list also names no project-deletion response test, and one exists:
  `tests/integration/test_delete_project_routes.py`,
  `test_project_delete_response_policy_matches_rendered_state` (L268). `test_delete_routes.py`'s
  `test_live_delete_views_have_their_response_policy` now asserts 202 on `?delete_confirm` (L455).
  RT-11's list and R-12's trigger should name these tests rather than a test to come.
- **If a document has to be written:** `SDD.md` itself, by `product-sdd`.
- **Answer:** RT-11's *Tests* names the tests on disk in place of the one to come. They landed with
  `delete-a-project`, merged at `ac09e56af`: `tests/integration/test_delete_routes.py`,
  `test_live_delete_views_have_their_response_policy`, which now asserts 202 on `?delete_confirm`
  and `no-store` on all four of a task deletion's pages; `tests/integration/test_delete_project_routes.py`,
  `test_project_delete_response_policy_matches_rendered_state`, which asserts 202 on a shown project
  deletion confirmation, 200 on its back-out, failure and Projects landing, `no-store` on each, and
  404 with no cache header for the deleted address under any query; and the two history tests,
  `tests/e2e/test_delete_task.py`, `test_confirmation_is_loaded_afresh_after_confirming`, and
  `tests/e2e/test_delete_project.py`, `test_project_confirmation_is_loaded_afresh_after_confirming`,
  each asserting that Back to the confirmation after confirming, and Forward then Back again, issues
  a new request, shows the not-found page and restores nothing from history. The sentence "which
  `delete-and-rename`'s command half names and which does not exist at `4a9ff47d2`" goes. § 11
  R-12's *shows up as* names those two history tests beside `test_moves.py`'s, and its "once it
  exists" goes. RN-56's line that a task deletion's confirmation is 200 at `4a9ff47d2` is a dated
  record and stays as written, as RN-49 does; the round's own note records the divergence closed.
  The two integration modules pass in a fresh clone at `958a36c7c` (85 passed); the end-to-end pair
  is read on disk this round, not run. Reasoning: `products/tracker17/docs/trail/sdd/self_answer-14.md`.

**How it closes.** `product-sdd` folds it on its next run like every other item in this file, and
the trail copy and the delete-when-empty behaviour are unchanged.
