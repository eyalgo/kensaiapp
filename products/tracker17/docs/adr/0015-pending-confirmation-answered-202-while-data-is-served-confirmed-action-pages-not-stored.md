# ADR-0015: While the saved data is served, answer a page that shows a pending confirmation of any confirmed action with 202, and store no page of a confirmed action

**Status:** Accepted
**Date:** 2026-10-30

## Context

Three actions ask for confirmation on their own page load: a move to `cancelled`, a task deletion
and a project deletion. SDD § 4 EX-6 defines them as one mechanism (ADR-0003), and each
confirmation's address carries the pending step (ADR-0014). UXD UX-F4 has a return to a move's
confirmation through a reload, Back or a bookmark, once the task is in a final status, show the
no-press refusal and never a stale confirmation. The address of a deleted task or project shows the
not-found page (SDD § 4 EX-13; UXD UX-S10). SRS NFR-3 has every page show the data as it stood when
it was loaded.

The pinned browser restores a page from its back/forward cache without asking the tracker. A
confirmation restored that way shows a pending step the saved state no longer allows: a move the
status no longer offers, or a task already deleted, shown as held and offered for deletion again.
The two mechanisms that would normally stop it are closed: no page runs a script (ADR-0003), and the
tracker keeps no cookie or session (ADR-0014).

ADR-0010 decided this on 2026-10-21 for a move to `cancelled` alone, and its words — "a move's
interaction or outcome", "No move response" — reach no deletion page. The task deletion then landed,
and SDD version 13 § 4 RT-11 widened the boundary to every confirmation EX-6 names (SDD RN-56).
ADR-0012 followed it on 2026-10-28.

A tracker that starts on saved data it cannot read now stays up and shows one page at every address
(SDD § 4 EX-13). In that mode an address ADR-0012 answers 404 or 202 answers 503. This record carries
ADR-0012 with its rules qualified to the mode they hold in.

## Decision

Every rule in this Decision holds while the tracker serves its saved data.

`web` answers a page that shows a pending confirmation of any action SDD § 4 EX-6 confirms — a move
to `cancelled`, a task deletion, a project deletion — with HTTP status 202. It answers every other
page a confirmed action's interaction or outcome lands on with 200: a move's outcome, a deletion's
back-out, its failure, and the landing that names the deleted task or project. Each of them, the
confirmation included, carries `Cache-Control: no-store`. No response of an action EX-6 confirms
carries `Clear-Site-Data`: neither its submissions nor its confirmation, back-out, failure or
outcome pages.

The status is read off the page as built, after outcome precedence, task membership and the
workflow's answer against the saved state. An address that asks for a confirmation the page does
not show is answered 200. The address of a deleted task or project, with any query, and an address
naming a task no task ever held, is answered with the not-found page, 404, with no cache header,
never 202, and is outside the 202 and `no-store` clauses. The HTTP cache may keep that 404: an
identity is never issued twice (SRS DR-2; ADR-0008), so a kept 404 for a deleted address stays true.

The two headers serve two purposes. The 202 is the history-admission boundary: it keeps the page
out of the browser's back/forward cache, so a return to it is a fresh load of the saved state. That
load shows what is true now — the no-press refusal once the task is final, the not-found page once
the task or project is deleted. `no-store` keeps the HTTP cache from reusing an interaction or
outcome page. The meaning taken for 202 is the standard's, a request accepted for processing that
"might or might not eventually be acted upon, as it might be disallowed when processing actually
takes place" (RFC 9110 § 15.3.3) — here an intent awaiting the operator. The GET schedules, saves and
records nothing.

This is the CTO's call, settled in SDD § 4 RT-11 at version 13.

While the saved data is unreadable, those addresses answer as ADR-0014 says. No confirmation page is
added for that mode.

## Alternatives ruled out

- **A page script** that reloads or rewrites a page restored from history. It lost because no page
  runs a script (ADR-0003).
- **A cookie or a session** whose change evicts the page from the history cache. It lost because the
  tracker keeps nothing between requests and sets no cookie (ADR-0014).
- **`Clear-Site-Data: "cache"` on the confirming redirect.** It was built and measured not to evict
  the page from the pinned browser's history cache, and is gone.
- **`Cache-Control: no-store` alone.** Chrome documents that a `no-store` page can be restored from
  the history cache, so the header by itself does not keep the confirmation out.
- **Keeping the boundary for a move only**, and answering a deletion's confirmation 200 with
  `no-store`. It lost because Back after confirming a deletion would restore a confirmation that
  shows the deleted task as held and offers to delete it again, where a fresh load shows UXD UX-S10's
  page. SDD § 9 TO-8 already states the boundary for "a page that shows a pending confirmation", with
  no move in its words, and two boundaries for one mechanism reopen with the project deletion (SDD
  RN-56).
- **A record beside ADR-0010 for the deletions, leaving ADR-0010 in force.** It lost because two
  Accepted records would state one mechanism, and ADR-0010's title, "store no move page", would still
  read as the whole rule.
- **Leaving ADR-0012 as it stands and relying on SDD § 12** to say that § 4 wins. It lost because the
  delivery tier reads an Accepted record as fixed.

## Consequences

Easier: a return through Back or Forward to any confirmation's address is a fresh load, and shows
the saved state — UX-F4's no-press refusal once the task is final, UX-S10's not-found page once the
task or project is deleted. A deletion never offers itself again from history. No script, cookie or
session is added, and the project deletion is built to the same rule as the two built
confirmations.

Harder: a reader meets a 202 on a GET that completes nothing, and reads it as a mistake until this
record says why (SDD § 9 TO-8). Setting it back to 200 brings a stale confirmation back on Back on
the pinned browser; `test_real_history_traversal_revalidates_the_confirmation` failed on exactly
that for a move before ADR-0010's change. One case is accepted and left: a 404 for an identity not
yet issued, reached only by a typed address and kept by a cache outside SRS NFR-13's bound, goes
stale once that identity is issued (SDD § 4 RT-11).

Undoing the line costs one line in `web` (SDD § 9 TO-8). Undoing the decision costs more, because
nothing else is left to keep UX-F4's promise or to keep a deleted task's confirmation off Back: a
page script, which supersedes ADR-0003; a cookie or session, which supersedes ADR-0014; or giving up
the fresh load on Back, which moves the UXD.

**Dependence:** Chromium's admission rule and HTTP's cacheability rules. Chromium admits a main
document to its back/forward cache only when its status is exactly 200, not any 2xx
(`content/browser/back_forward_cache/back_forward_cache_impl.cc`, `PopulateReasonsForMainDocument`,
`if (rfh->last_http_status_code() != net::HTTP_OK)` → `kHTTPStatusNotOK`, read 2026-10-20,
2026-10-21 and 2026-10-28). No standard promises it. RFC 9110 § 15.1 does not list 202 among the
status codes a cache may store heuristically, so the HTTP cache cannot keep the confirmation even
without the header; `no-store` is what protects the 200 pages. RFC 9110 § 15.5.5 lets a cache keep a
404 heuristically. Chromium gives a 404 zero freshness — it computes a heuristic lifetime only for
200, 203 and 206 with a `Last-Modified` (`net/http/http_response_headers.cc`,
`GetFreshnessLifetimes`, read 2026-10-28) — and the listener sends neither `Date` nor
`Last-Modified` (`web/listener.py`, `_write`). The history tests prove the build the pinned library
installs, Chromium 153.0.8010.12 under `playwright==1.63.0`, and not the operator's current stable
Chrome (SRS NFR-13; SDD § 11 R-12). A Chromium release that admits a non-200 main document un-makes
this decision; it shows up as those tests failing where the pin moves, and on the operator's browser
before then.

## Traces to

- Supersedes `products/tracker17/docs/adr/0012-pending-confirmation-answered-202-confirmed-action-pages-not-stored.md`,
  whose decision, alternatives and consequences this record carries whole, as ADR-0012 carried
  `products/tracker17/docs/adr/0010-pending-confirmation-answered-202-move-pages-not-stored.md`. It
  names ADR-0014 where ADR-0012 named ADR-0011.
- `products/tracker17/docs/trail/architecture/cycle-22.md` § 3.4 — the answer that settled this
  supersession, raised by the PM, with its reasoning at
  `products/tracker17/docs/trail/architecture/self_answer-26.md` § 3.4.
- `products/tracker17/docs/SDD.md` § 4 RT-11, RT-7, RT-8, EX-6, EX-13; § 6 S-7; § 9 TO-8, TO-2;
  § 11 R-12; SDD Review Notes RN-49, RN-56, RN-69, which reads RT-11's 404 as reached only while data
  is served.
- `products/tracker17/docs/trail/sdd/cycle-10.md` § 5.1 — the CTO-seat answer that widened RT-11,
  with its reasoning at `products/tracker17/docs/trail/sdd/self_answer-13.md` § 5.1; the move's
  boundary, `products/tracker17/docs/trail/sdd/cycle-8.md` § 5.1 and `self_answer-10.md` § 5.1.
- `products/tracker17/docs/trail/architecture/cycle-15.md` § 2.1 — the confirmation of ADR-0012
  with three additions, reasoning at
  `products/tracker17/docs/trail/architecture/self_answer-19.md` § 2.1; ADR-0010's,
  `products/tracker17/docs/trail/architecture/cycle-12.md` § 2.1.
- `products/tracker17/docs/SRS.md` NFR-3, NFR-13, DR-2; `products/tracker17/docs/UXD.md` § 4, UX-F4,
  UX-I2, UX-I3, UX-S9, UX-S10.
- `products/tracker17/web/routes.py`, `Site._pending_status`, `Site._stored_as_asked`,
  `Site._task_page` and `Site._delete_area`; `products/tracker17/web/listener.py`, `_write`; read
  2026-10-28 at `035b97cd1`. `products/tracker17/web/routes.py`, `UnreadableSite`, and
  `products/tracker17/tests/integration/test_unreadable_routes.py`, read 2026-10-30 at `b13b5e86b`.

## Binds

QC-63.
