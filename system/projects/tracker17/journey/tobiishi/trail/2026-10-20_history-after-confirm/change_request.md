# Change request — 2026-10-20_history-after-confirm

**Request:** Going Back in the browser after confirming a move to `cancelled` must not show the old confirmation again. Today it does: the browser keeps the confirmation page in its history cache, shows it on Back, and the strip with its confirming control comes back to life. The previous change tried `Clear-Site-Data: "cache"` to push the page out of that cache, and it was measured not to evict the page from the pinned browser, so `tests/e2e/test_moves.py::test_real_history_traversal_revalidates_the_confirmation` still fails (`1 failed, 56 passed` in the browser folder). Find a way to meet that case that is not that header, still with no page script on the pages (ADR-0003), and make the case pass on the real browser. The confirmation must still revalidate against the saved status: Back after confirming shows the saved-status refusal and no strip, a second tab's successful ordinary move leaves no usable old confirmation, and a reload, Back and Forward before confirming save nothing.

Then do what the previous change deferred behind it: review the change's file fence and the assertions it retained in the browser tests, so nothing outside the pages and routes that offer or confirm moves was touched and no assertion is kept that no longer checks anything. And record the history mechanism that gets settled on, as a record owed (an ADR or an SDD line), because no architecture record names either response header `web/routes.py` sends today (`Cache-Control: no-store` and `Clear-Site-Data: "cache"`).

Sizing decision: the acceptance boundary is the station's reached-when 5 — `pytest products/tracker17/tests/e2e/` exits 0 where layer 5 runs — whose one unmet obligation is the Back-after-confirm case (SDD § 4 EX-6, UXD UX-I2, change_spec CP-326/CP-331/CP-337 of the previous change). The mechanism, the fence review and the record owed are one capability's acceptance obligations, kept together; the station's other reached-when items already hold and are not reopened.

Must not be weakened: the workflow rule stays written once in `domain/workflow.py`; no page script; no out-of-date-move handling and no `tests/timed_run.py` change; the saved data format is unchanged; no confirmation on deleting a task or project; files other than the pages and routes that offer or confirm moves, and their tests, stay as they are; `pytest products/tracker17/tests/` keeps exiting 0.

**Category:** bug
**Behaviour:** changing
**Classified because:** the station's reached-when 3 and 5 already state that a confirmation is revalidated on Back, and the shipped pages violate it (`test_moves.py:423` fails); a violated contract is a `bug`. Behaviour is `changing` because a response header the pages send, and what Back shows after confirming, change observably.

---

**Sealed:** 2026-10-20 — accepted; merged to `main` via `--no-ff`.
Environment: owners-mac — no CI
