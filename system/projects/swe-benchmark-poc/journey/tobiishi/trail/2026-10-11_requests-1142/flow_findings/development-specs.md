# Flow Findings — development-specs  (audited 2026-10-11)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Audited `change_spec.md` against `change_request.md` (the casual request and the issue) and, since the
product has no `docs/fdr.md` (Definition: none), against the product's own code at `base_commit`.
Lens 3 (classification copied verbatim: `bug` / `changing`, in vocabulary), lens 4 (each load-bearing
choice — GET+HEAD, `body is None`, dropping the caller's header, redirects, tests' home — has a Locked
Answers entry with its reason), lens 5, lens 6 and lens 8 found nothing. Lenses 9 and 10 do not apply to
this step.

- **[non-blocking · change-local · altitude]** Rules and rationale carry mechanism anchors. CP-9 and
  CP-11 justify themselves by the function and line that set the header (`prepare_content_length`,
  `requests/models.py` lines 389, 380, 411); CP-14 names the exact `TypeError` and the
  `connectionpool.py` line 196; Gap 4's rationale rests on how the followed request is built from the
  original's headers. Where: `change_spec.md §Rules` (CP-9, CP-11, CP-14), `§Locked Answers` (Gap 4).
  Each rule's observable content (the prepared request's `headers`) already stands without the anchor,
  and the anchors tie the rules to today's implementation and name the cause the design is meant to
  choose. Direction: keep the cause in `## Verified Claims`, state the rules by what the prepared
  request shows.
- **[non-blocking · change-local · evidence]** Three behaviours are asserted as observed in `## Out of
  Scope` and appear nowhere in `## Verified Claims`: a generator body is prepared with
  `Content-Length: 'None'`; an `io.BytesIO` body raises `io.UnsupportedOperation: fileno`; a `PUT`
  answered `303` is followed as a bodiless `PUT` with `Content-Length: 0`. CP-13 also relies on the
  generator claim ("keeps what it gets today"). Where: `change_spec.md §Out of Scope`, `§Rules` (CP-13).
  The section's zero form is "the command, the tree, the conditions, what came back", and these have
  none of the four; the `303` item even sits beside a read-only reason (`is` comparison at
  `sessions.py` line 108). Direction: add run rows, or drop the claim of observed behaviour.
- **[non-blocking · change-local · coverage]** CP-11 states the rule for "a `(user, pass)` tuple or an
  auth object", but every Example and the Verified Claims run only the tuple. An auth object takes
  the other path through `prepare_auth` (`auth(self)` then the recompute) and is a rule-implied case
  with no row. Likewise a `HEAD` with a body (CP-13's `GET`-or-`HEAD` body axis) has no Example.
  Where: `change_spec.md §Examples` (CP-11, CP-13). Direction: add the rows, or narrow CP-11's wording to
  what was run.
