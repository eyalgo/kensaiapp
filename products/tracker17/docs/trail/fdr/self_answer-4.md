# Self-answer report — products/tracker17/docs/fdr.md

## Header

- **Companion:** products/tracker17/docs/fdr_open_issues.md
- **Document:** products/tracker17/docs/fdr.md (version 5)
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-30
- **Sources re-read:** Chromium's source, `content/browser/back_forward_cache/back_forward_cache_impl.cc`, `PopulateReasonsForMainDocument`, on its `main` branch: "if (rfh->last_http_status_code() != net::HTTP_OK)", so exactly 200, as SDD § 4 RT-11 says. Chrome DevTools' own string, `BackForwardCacheStrings.ts`, reads "Only pages with a status code of 2XX can be cached", which is looser than the check. The code is what runs, so this answer rests on the code. Read for R-127, the one rule here whose "never" depends on a browser.

## Items worked

### 2.1 — The inputs moved after FDR version 4 read them, and the FDR now follows them

- **Bucket:** 2. Choices to confirm — the Principal PM drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** Every rule in the draft stands as written, and one sentence of its reasoning does not hold. The rationale says SDD RT-4 has the prerequisites section name uv "on the owner's own call" and cites `products/tracker17/docs/trail/sdd/cycle-12.md` § 5.1. That answer chose uv and nothing more. Naming it in the prerequisites section was an answer in the CTO's seat, at `products/tracker17/docs/trail/sdd/cycle-13.md` § 5.1, and SDD RN-65 says the owner's call "said nothing about where the README names it". R-124 still holds, because RT-4 now says it, so the conclusion survives on the real reason. No line of the FDR repeats the wrong attribution, RN-15 included, so the document owes no change for it.

  The rest of the draft checks out at its sources. SRS FR-41 states the three things R-121, R-122 and R-123 carry, and AC-21 checks them. README line 3 names both purposes and no earlier version, which meets "names only tracker16-X" as AC-21 reads it. RT-4 states what R-124, R-125 and R-126 say. RT-11 and TO-8 state R-127, and RT-8 names "a value its control cannot hold", which is R-128. The *Inputs read* versions match the four headers: PRD 7, SRS 6, SDD 18, UXD 11. The tests the rationale names exist, and `test_a_refused_sort_changes_nothing_on_disk_and_lists_nothing` shows R-128 reaches sort values as well as filter values. The choice to leave uv's name to the SDD is consistent with R-4, PD-10 and R-120, which leave a value there the same way. I was close to overriding this one, since the FDR does name Python and Chromium. Those two are product decisions, while uv is the suite's and the owner chose it knowing it could change, so it stays out.

  The seat is this document's: each rule traces to a settled input, and nothing here binds a person or an outside party. The owner's own calls in the chain were already made upstream.

  Against the settled record, R-124 does not disturb R-13's three commands on "only the stated prerequisites". R-126 keeps the tracker's setup free of uv, and SRS C-7 bounds the tracker's setup alone (SDD RN-65). PD-6 and PD-7 hold, because uv is not a declared dependency.

  On the failure paths:

  - **Absent, uv:** the tracker still runs, and R-125 says how to install uv.
  - **Refused, no network:** R-11 covers the suite's one-time need.
  - **Unreadable data:** R-127 and R-128 need no scoping of the kind R-20 and R-105 needed. R-25 and R-105 give every address the one page, which offers no confirmation and no list, so neither rule says anything false in that mode.
  - **A missing project with a bad filter value:** it stays not-found under R-105 (`test_missing_project_wins_over_invalid_filter_choices`).
  - **Stale, one case left uncovered:** R-127's "never" is shown on the Chromium build the suite pins. Should a later browser release admit a non-200 page to its history cache, the rule would fail until `web` changes. SDD § 11 R-12 names that case and the tests that catch it, and RN-11 keeps risks out of the rules, so the FDR takes no change.

  **Still owed, and not by this document.** The draft is right that confirming R-124 does not write the README's sentence. `products/tracker17/README.md` § What you need still does not name uv, and SDD RN-65 leaves the unit that carries it to the PM. No seed carries it today. The active seed's two open items are about unreadable data and the start's printed lines, `unpicked/` is empty, and no station is parked. So R-124 will be a rule the product fails, with nothing on the route to fix it. The README has no companion and no template, so this run writes nothing there. `what_left.md` takes no entry either, since it holds only what the PRD or Agari wants and only a change to those adds one. The PM needs to pick this up.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/fdr.md** — `<CORE>/launchers/skill/launcher.sh product-fdr tracker17`
