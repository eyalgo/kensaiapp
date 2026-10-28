# Self-answer report — `adr/` and `nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-28
- **Sources re-read:** None. The answer rests on the product's own tests at `HEAD`, run in a clone,
  and on SDD version 14. It leans on no source outside this repository. The browser behaviour the
  history tests prove is the pinned build's, and the tests were run against it, not taken from a
  record.

## Items worked

### 3.1 — QC-63 still carries the task deletion's 202 as unmet and the project deletion's pages as unbound

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** confirmed with addition
- **Why:** The PM is right. QC-63's *verified by:* should name the four deletion tests and drop
  both "unmet" lines. The obligation itself does not change. The item came with a proposal ("QC-63
  should name these as its verifiers and drop the unmet line"), so I weighed it as a draft rather
  than answering from scratch.
  - **Seat: mine.** The edit lands in `nfdr.md`, which is this companion's own document. It binds
    only the record's agreement with the product. No person, money or risk is committed, so the
    owner does not need to decide it. This is not a widening either. The item corrects two
    statements that are now false and adds no case, so the "not until it occurs" rule does not
    apply.
  - **The claims hold, checked at the source.** `ac09e56af`, the merge of the project deletion,
    is on `main`. In the same merge, `test_live_delete_views_have_their_response_policy` changed
    from asserting 200 to asserting 202 on `?delete_confirm`
    (`tests/integration/test_delete_routes.py:455`). The item's other line references match the
    files: `test_delete_project_routes.py:268`, `test_delete_task.py:182` and
    `test_delete_project.py:290`. I ran the two integration modules and the two history tests in a
    throwaway clone at `0ac110bab`, using the product's own pinned tools (`uv run --group dev
    pytest`): 87 passed. I did not re-run the whole suite. The item's 2556 count is the PM's.
  - **Addition 1: name each project deletion clause, not just "the pages".** I read
    `test_project_delete_response_policy_matches_rendered_state` line by line. It covers every
    project deletion clause QC-63 states:
    - 202 on a shown confirmation;
    - 200 on back-out, on failure, and on failure combined with confirmation;
    - `no-store` on all four pages and on the landing;
    - plain project pages keep no cache header;
    - neither press carries `Clear-Site-Data` or a cache header, and no page does;
    - the deleted project's address answers 404 with no cache header, whatever the query, and so
      does a never-held one (`/projects/777`).

    So that one test is the layer-3 verifier for the whole project deletion, the 404 clause
    included. QC-63's tail names verifiers clause by clause, so it should say so in the same way.
  - **Addition 2: the history clause covers both deletions, on the pinned build.** Both e2e tests
    go Back to the confirmation after confirming, and Forward then Back again. Each asserts that
    the browser makes a new request, that the not-found heading shows and no confirmation strip
    does, and that the saved bytes do not change. Both also assert `PINNED_BROWSER`. So QC-63's
    existing sentence — that layer 5 proves the pinned Chromium build and not the operator's
    current Chrome — covers them as it covers the move's tests. It needs no new caveat.
  - **Addition 3: what follows in the record.** RN-50 says "this note closes when it lands". It
    has landed, so the fold records the close in a new note and leaves RN-50 as written, the way
    RN-44 and RN-48 are kept. Its line that the project deletion "is not built" was true when
    dated, so it is not edited either. ADR-0012 needs no change. I read it, and it states the
    boundary with no product state, which is what RN-50 designed it to do. The § 10 row for QC-63
    stays as it is, because its commands (`pytest tests/` layer 3, `pytest tests/e2e/` layer 5)
    already reach all four tests. `Inputs read:` moves from SDD version 13 to version 14. That
    version names the same four tests in § 4 RT-11's *Tests* and § 11 R-12, so the NFDR and the
    SDD agree.
  - **Failure paths.** *Stale:* the verifier names are checked at `HEAD`, and the obligation text
    is unchanged, so a later rename of a test is QC-11's pointer-test concern, not this one's.
    *Absent:* if the e2e tools are not installed, layer 5 does not run, and the layer-3 tests still
    bind every status and header clause. *Concurrent:* the double-press tests sit beside the history
    tests in both e2e modules, but QC-63 does not cite them and does not need to.
  - **Close to another verdict?** Only to "confirmed". The proposal as written names the four tests
    and drops the unmet line. It does not say that the project test also carries the project's 404
    and `Clear-Site-Data` clauses, or what becomes of RN-50, ADR-0012 and `Inputs read:`. Without
    those, the fold would have to re-derive them.
  - **Seen, not raised.** `docs/what_left.md` still lists project rename and deletion as missing at
    `<a commit not in the public history>`. Both change units are sealed. That file shrinks only through the `readme-status`
    row after a station closes (`kensaiapp_structure.md` § *The what-left file*). It is not a
    companion's to carry, and the fold does not read a build state from it for this answer.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **`products/tracker17/docs/nfdr.md`** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
