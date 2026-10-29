# Security report

Security: reported

**Change:** `tracker17 · tobiishi · 2026-10-29_operator-name-with-a-brace` · reviewed 2026-10-29 by the
Senior Engineer (`development-security`, after the code-integrity pass `ce8fbd2d0`). Both worktrees are
one: the product lives inside the instance (`project.md` `Product path: products/tracker17`).

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names none — QC-40's `verified by:` says "no audit
  command exists for this product: the Python packet names none and tracker17 installs none"
  (`products/tracker17/docs/nfdr.md` § 2, QC-40), and § 10's map lists QC-40 among the review gates with
  no row. No advisory was answered. Detailed under *Dependency audit*.

## Dependency audit
skipped — the NFDR names no dependency audit. QC-40 (`docs/nfdr.md` § 2) holds the supply-chain
obligation and verifies it by review at `development-design`, not by a command; § 10 ("QC-12, QC-25,
QC-26, QC-27, QC-40, QC-41 and QC-60 are review gates and have no row") confirms it. Per the shared
rules no command was invented and no tool reached for. The change moves no pin: `pyproject.toml` and
`tests/requirements.txt` are untouched on the branch (`git diff --stat main...HEAD`).

## Advisories
| Advisory | Dependency | Answer | What was done | Commit |
|---|---|---|---|---|
| none — no audit ran | — | — | — | — |

## Exceptions and upkeep rows
none written by this run. For the PM's bearings: the product's one standing exception is the owner's,
recorded by hand in NFDR RN-33 (Chromium `153.0.8010.12`, under QC-40's 30-day window), with its row
already in `system/upkeep.md`, next due **2026-11-07**. It is inside its window today and this run did
not touch it. The product has no `checks/deps/advisory_exceptions.toml`; none was created, because no
advisory was answered.

## Holes in the code
none.

The product is one artifact class — a loopback web service that serves, stores and shows typed text
(`main.py`, `domain`, `application`, `persistence`, `web`; `git ls-files products/tracker17` holds no
skill, prompt, agent or launcher file) — so the OWASP Top 10:2025 list was applied and the agentic
list was not. Boundaries read from NFDR § 2 (B-1 listener, B-2 saved data, B-3 typed text shown back,
B-4 setup) and § 3 (one operator on loopback; a local program is an accepted caller).

The diff's one product-code change is `web/pages.py:2819-2830`, `_your_name_section`. Trace of the
typed name: `routes.py:1253` `_first(form, "name")` → `_line_feeds` → `tracker.set_operator_name`
(domain rule) → `_redirect` with `operator_saved` / `operator_typed` in the query →
`routes.py:805-817` `_operator_area(query)` → `pages.py:2793-2803` `_operator_line`, which passes the
name through `_escape` (`pages.py:452-454`, `html.escape(value, quote=True)`, the SEC-4 one function)
→ the f-string paragraph at `:2820`. The class attribute now comes from a two-value constant chosen off
the `_OperatorOutcome` enum (`:2819`), and the built paragraph is no longer passed through `.format`.

Candidates considered and dropped under the sceptical pass:

- **Format-string evaluation of typed text** (`.format` on a string holding the escaped name, A05/A10)
  — this is the defect the change removes. On the branch the path no longer exists; `grep -n
  '\.format(' web/pages.py` shows every remaining call fills a module-held template and passes typed
  text only as an argument. Not a hole on the branch.
- **A page line driven by the address** (`/people?operator_saved=<text>` shows "You set your name
  to '<text>'" without a save having happened; A01-shaped, already on `main`) — the value is escaped,
  the page changes no state, the only callers are the operator's own browser or a local program the
  NFDR § 3 declaration accepts. Confidence 2/10. Below the floor; not reported.
- **Typed name written to the console on a failed save** (`routes.py:1273`, via `_report_failure`)
  — logging of a non-sensitive value, an exclusion. Not a hole.

No fix was made, so no suite run was owed and none was issued through the gate tool; the branch's
suite stands as the code-integrity report records it (`2651 passed` through `gate_suite.py`).

## Not checked
- The resolved dependency set and the browser build against published advisories: no audit command
  exists for this product (above), and the review gate that watches them is `development-design`'s,
  not this step's.
- The e2e suite (`tests/e2e/`): not re-run here — nothing was changed by this run. Its last run is the
  code-integrity report's (`121 passed`).
