# Self-answer report — SRS.md

## Header

- **Companion:** products/tracker17/docs/SRS_open_issues.md
- **Document:** products/tracker17/docs/SRS.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-11
- **Sources re-read:** `task-tracker-X/tasktracker16x/domain/priority.py`, line 9, which reads
  `VALID_PRIORITIES: frozenset[str] = frozenset({"low", "medium", "high"})`. The predecessor's set is
  three values, as `PRD.md:129-131` says. The answer's change to C-5 rests on this.

## Items worked

### 3.1 — The SRS states three priorities; the PRD now states four, `critical` included

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write the SRS
- **Verdict:** answered
- **Why:** The SRS takes PRD v5's four priorities, with `critical` the highest. FR-15 names the set,
  FR-36 orders it `low`, `medium`, `high`, `critical` ascending, FR-38 counts four, and C-5 carries
  the PRD's one exception to the predecessor rule.

  *This is a correction, not a widening.* The SRS derives from the PRD, and the PRD moved:
  `PRD.md:128` (v5, Settled) reads "A task is `low`, `medium`, `high` or `critical`". The owner made
  that call (`trail/prd/cycle-5.md` § 1.1). The SRS's three-value statements are now false against
  their input, so the rule that a widening item waits for an occurrence does not apply.

  *Seat (check 1).* Mine, in the owner's seat. Every edit lands in `SRS.md`. The order binds nobody
  outside the product. The one call in the item, where `critical` sits in the order, is a question
  the owner has already given the reason for. I can name no ground I cannot see.

  *The question (check 2).* There was no draft, so I read the question. It holds two parts: whether
  the SRS takes `critical` (the PRD settles that), and where `critical` sorts (no document states
  it). Both parts have the same seat, so I answer both in the one slot. On the order: the owner
  confirmed `low` → `high` ascending because "ascending means rising, and `high` is more than `low`"
  (`trail/srs/cycle-1.md` § 2.4). `critical` is more than `high`, and `PRD.md:128` lists the four in
  that rising order. So `critical` comes last ascending and first descending. The item names
  `SRS.md:231` and RN-20, but the set reaches further. FR-38 says "each of the three priorities".
  And C-5, "task rules are tracker16-X's wherever both cover a rule", is where the three-value set
  enters the SRS today: `fdr.md:175-176` traces R-51's refusal to "SRS § 7 C-5". With FR-15
  naming four values, C-5 would contradict it unless C-5 carries the exception that `PRD.md:115-116`
  now states. So the answer names C-5 even though the item does not.

  *Settled record (check 3).* PRD v5 is Settled, and the exception is in its preamble. UXD, DESIGN and
  SDD state no priority values: `grep -n -E '\`low\`|three priorit|\`high\`'` over the three printed no
  line. So none of them is owed a change. The FDR does state three values, in R-51 (`fdr.md:175`),
  R-90 (`fdr.md:278-279`) and R-96 (`fdr.md:294-295`), and no other channel carries the change there.
  So it is raised on the FDR (§ Companions opened). CONTENT's terminology bans the word "critical"
  (`CONTENT.md:150`). That is already raised in `CONTENT_open_issues.md` § 3.1, so I raise nothing
  further there. The RN-20 § 2.4 summary records the three-value call as it was made. I leave it as a
  record and ask the fold to add a note for `critical`, rather than rewriting what the owner confirmed.

  *Failure paths (check 4).*
  - Empty: a project with no `critical` task shows `critical` 0 in the summary, under FR-38's zero
    rule. A filter on `critical` that matches nothing says so, under FR-37.
  - Absent: nothing depends on an unreachable source.
  - Stale: saved data written with three values still loads, because the set only grows, so no
    migration is needed. Saved data holding `critical`, started by a build that knows only three
    values, breaks DR-6 ("an unknown status or priority"). FR-8 then shows the plain message and
    leaves the bytes unchanged, which is a safe outcome and needs no new requirement.
  - Concurrent: a priority edit from a stale page is NFR-3's plain field edit, and that does not
    change.
  - Refused: a priority outside the four, sent by a request the tracker's own field did not make,
    is refused at the FDR's R-51 and at load by DR-6. FR-39's list of refusals says "include", so
    I add no entry to it.
  - The default stays `medium`, as `PRD.md:128` says.

  No acceptance criterion changes. AC-14 already covers "each sort field in both directions" and
  checks the summary rows "on a project built to exercise each row", and the `critical` count is one
  of those rows. AC-7 tests an unknown priority, which now means a value outside the four.

  *Close call.* I weighed asking the fold to also add a FR-39 refusal for a priority outside the set.
  What decided against it: nothing in the PRD or this item asks for it, and the refusal already exists
  at R-51 and DR-6.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

- **products/tracker17/docs/fdr_open_issues.md** — **opened** — companion to `fdr.md`, item 2.1,
  landed in commit `b472b3b15`

*What the FDR is owed, and why it is worth a cycle.* The grounds are "A fact in it is now false" and
"Something upstream moved and it has not seen it" (`prompts/rich.md` § *The items are not the whole of
what a document is owed*). R-51 refuses any priority other than `low`, `medium` or `high`, so it now
refuses a value PRD v5 requires. R-90 and R-96 leave `critical` out of the sort and the summary. The
item traces to PRD v5 directly, so it holds whichever of `product-srs` and `product-fdr` folds first.

## Launchers owed

- **products/tracker17/docs/SRS.md** — `<CORE>/launchers/skill/launcher.sh product-srs tracker17`
- **products/tracker17/docs/fdr.md** — `<CORE>/launchers/skill/launcher.sh product-fdr tracker17`
