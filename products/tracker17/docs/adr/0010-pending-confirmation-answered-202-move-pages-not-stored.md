# ADR-0010: Answer a page that shows a pending confirmation with 202, and store no move page

**Status:** Accepted
**Date:** 2026-10-21

## Context

A move to `cancelled` asks for confirmation on its own page load (ADR-0003, SDD § 4 EX-6), and that
page's address carries the pending step (ADR-0006). UXD UX-F4 has a return to that address through a
reload, Back or a bookmark, once the task is in a final status, show the no-press refusal and never
a stale confirmation. SRS NFR-3 has every page show the data as it stood when it was loaded.

The pinned browser restores a page from its back/forward cache without asking the tracker. A
confirmation restored that way shows a pending step the saved state no longer allows. The two
mechanisms that would normally stop it are closed: no page runs a script (ADR-0003), and the tracker
keeps no cookie or session (ADR-0006).

## Decision

`web` answers a page that shows a pending confirmation of a move to `cancelled` with HTTP status
202, and every other page a move's interaction or outcome lands on with 200. Each of them, the
confirmation included, carries `Cache-Control: no-store`. No move response carries
`Clear-Site-Data`.

The status is read off the page as built, after outcome precedence, task membership and the
workflow's answer against the saved state. An address that asks for a confirmation the page does
not show is answered 200. An address naming a task no task holds is answered with the not-found
page, 404, with no `no-store`, and is outside this decision.

The two headers serve two purposes. The 202 is the history-admission boundary: it keeps the page
out of the browser's back/forward cache, so a return to it is a fresh load of the saved status.
`no-store` keeps the HTTP cache from reusing a move's interaction or outcome page. The meaning taken
for 202 is the standard's, a request accepted for processing that is not complete — here a move
intent awaiting the operator. The GET schedules, saves and records nothing.

This is the CTO's call, settled in SDD § 4 RT-11.

## Alternatives ruled out

- **A page script** that reloads or rewrites a page restored from history. It lost because no page
  runs a script (ADR-0003).
- **A cookie or a session** whose change evicts the page from the history cache. It lost because the
  tracker keeps nothing between requests and sets no cookie (ADR-0006).
- **`Clear-Site-Data: "cache"` on the confirming redirect.** It was built and measured not to evict
  the page from the pinned browser's history cache, and is gone.
- **`Cache-Control: no-store` alone.** Chrome documents that a `no-store` page can be restored from
  the history cache, so the header by itself does not keep the confirmation out.

## Consequences

Easier: a return through Back or Forward to a confirmation's address is a fresh load, and shows the
saved status — UX-F4's no-press refusal once the task is final. No script, cookie or session is
added.

Harder: a reader meets a 202 on a GET that completes nothing, and reads it as a mistake until this
record says why (SDD § 9 TO-8). Setting it back to 200 brings a stale confirmation back on Back on
the pinned browser; `test_real_history_traversal_revalidates_the_confirmation` failed on exactly
that before the change.

Undoing the line costs one line in `web` (SDD § 9 TO-8). Undoing the decision costs more, because
nothing else is left to keep UX-F4's promise: a page script, which supersedes ADR-0003; a cookie or
session, which supersedes ADR-0006; or giving up the no-press refusal on Back, which moves the UXD.
That is why this record exists where NFDR RN-13 refused one to decisions that live in one function.

**Dependence:** Chromium's admission rule. Chromium admits a main document to its back/forward cache
only when its status is exactly 200, not any 2xx
(`content/browser/back_forward_cache/back_forward_cache_impl.cc`, `PopulateReasonsForMainDocument`,
`if (rfh->last_http_status_code() != net::HTTP_OK)` → `kHTTPStatusNotOK`, read 2026-10-20 and
2026-10-21). No standard promises it. RFC 9110 § 15.1 does not list 202 among the status codes a
cache may store heuristically, so the HTTP cache cannot keep the confirmation even without the
header; `no-store` is what protects the 200 outcome pages. The two end-to-end history tests prove
the build the pinned library installs, Chromium 153.0.8010.12 under `playwright==1.63.0`, and not
the operator's current stable Chrome (SRS NFR-13; SDD § 11 R-12). A Chromium release that admits a
non-200 main document un-makes this decision; it shows up as those two tests failing where the pin
moves, and on the operator's browser before then.

## Traces to

- `products/tracker17/docs/SDD.md` § 4 RT-11, RT-7, RT-8; § 9 TO-8, TO-2; § 11 R-12; SDD Review
  Notes RN-49.
- `products/tracker17/docs/trail/sdd/cycle-8.md` § 5.1 — the CTO-seat answer that settled RT-11,
  with its reasoning at `products/tracker17/docs/trail/sdd/self_answer-10.md` § 5.1.
- `products/tracker17/docs/trail/architecture/cycle-12.md` § 2.1 — the owner's confirmation of this
  record with three additions, reasoning at
  `products/tracker17/docs/trail/architecture/self_answer-16.md` § 2.1.
- `products/tracker17/docs/SRS.md` NFR-3, NFR-13; `products/tracker17/docs/UXD.md` § 4, UX-F4,
  UX-I3.
- `products/tracker17/web/routes.py`, `Site._pending_status`, `Site._stored_as_asked` and
  `Site._move_view`, at `9b05680c7`.

## Binds

QC-63.
