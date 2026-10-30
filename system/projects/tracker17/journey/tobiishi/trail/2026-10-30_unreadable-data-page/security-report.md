# Security report

Security: reported

**Change:** `tracker17 · tobiishi · 2026-10-30_unreadable-data-page` · **Date:** 2026-10-30 · **Branch head reviewed:** `f2fef62f6`

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names no dependency audit — `products/tracker17/docs/nfdr.md` § 2 QC-40, *verified by:* "No command can measure a window, and no audit command exists for this product: the Python packet names none and tracker17 installs none". No advisory was answered on this branch; the standing dated exception (QC-40, RN-33, Chromium `153.0.8010.12`, lapsing 2026-11-07) is tracked by the row already in `system/upkeep.md` and was neither renewed nor removed here. Detailed under *Dependency audit*.
- QC-40's package feed (Dependabot alerts on the repository) is recorded in the NFDR as down since 2026-10-29; this run could not check it and did not try, since the NFDR holds the check to the `development-design` review. Noted, not acted on.

## Dependency audit
skipped — the NFDR names no dependency audit (`products/tracker17/docs/nfdr.md` § 2 QC-40, *verified by:* tail, quoted above; § 10 projects no audit row). No command was invented and no tool run in its place, per `<CORE>/prompts/senior_engineer_repair_dependencies.md` § *The audit command is the product's, not yours*. The change moves no pin: `pyproject.toml` and `uv.lock` are not in the branch's diff (`git diff --stat main...HEAD`).

## Advisories
| Advisory | Dependency | Answer | What was done | Commit |
|---|---|---|---|---|
| none | — | — | no audit ran | — |

## Exceptions and upkeep rows
none — no exception written, renewed or removed; `system/upkeep.md` exists and is unchanged.

## Holes in the code
none.

Threat lists applied: the product is code that serves and processes input on a loopback listener (NFDR § 2 boundaries B-1 the listener, B-2 the saved data at start, B-3 typed text shown back; § 3 declares no identity or authorization), so the OWASP Top 10:2025 web list was applied over the diff. The agentic list does not apply: the product holds no skill, prompt or launcher.

Scope read: `git diff main...HEAD` over `products/tracker17/` outside `tests/`, every file it touches in full (`main.py`, `persistence/saved_data.py`, `web/__init__.py`, `web/listener.py`, `web/pages.py`, `web/routes.py`), and the paths traced from it (`_respond`, `_escape`, `_address`, `LocationUse.mark_started`, `_Handler._serve` and `_write`).

Candidates traced, each scored on the sceptical pass and dropped below the floor of 8:

- **New entry point — `UnreadableSite.handle` (`web/routes.py:1347-1362`), A01/A07.** Runs the same `_refused_before_routing` check as `Site.handle` first (Host must equal the bound `host:port`; `Sec-Fetch-Site` `cross-site`/`same-site` refused), so DNS-rebinding and cross-site requests are refused before anything else, as QC-31 and QC-32 require. Every POST not marked `same-origin` is refused — stricter than `Site`, which refuses only submission routes. Score 1.
- **Redirect target on POST (`web/routes.py:1356`), open redirect.** `Location` is `_address(PROJECTS_ADDRESS)`, a constant `/`; no request value reaches it. Score 1.
- **Location shown in the page (`web/pages.py:2647-2662`), A05 / A02 disclosure.** The saved data's absolute path enters the page through `_escape` (`html.escape(..., quote=True)`), the one function QC-36 names; it is the operator's own path, already printed on the console, served only to the loopback caller NFDR § 3 accepts. Score 1.
- **Stylesheet on the unreadable site (`web/routes.py:1358-1359`), A05 path traversal.** `STYLESHEET_FILE` is a fixed path resolved from the module (`routes.py:63`); the request path is only compared to a constant. Score 1.
- **Response headers on the new responses, A02.** Every `UnreadableSite` answer goes through `_respond` (`routes.py:159-160`), which appends `Content-Security-Policy: <PAGE_POLICY>` with `frame-ancestors 'none'` and `script-src 'none'` (QC-33, QC-34); the page carries `Cache-Control: no-store`. Score 1.
- **Saved data reached from the page, A01.** `UnreadableSite` holds the location text and the pre-built page bytes only — no tracker, reader or saver (`routes.py:1350-1352`); `LocationUse.mark_started` sets a flag on an `flock` of the directory and writes no file (`persistence/location_use.py:4-6`, `:73-75`). Score 1.
- **Reader hardening (`persistence/saved_data.py:77-80`, `:98-100`, `:112`), A08 / A10.** The lone-surrogate check (`json.dumps(...).encode("utf-8")`, whose `UnicodeEncodeError` is a `ValueError`), the `OverflowError` on `astimezone` and the `RecursionError` catch each turn one more malformed file into `UnreadableData` rather than a traceback; the reader still executes nothing (QC-37). The deep-nesting case is resource exhaustion, an exclusion. Score 1.
- **Request body read before `handle` (`web/listener.py:55`), already on `main`.** `_Handler._serve` reads `Content-Length` bytes into memory for every handler, the unreadable one included, which never uses them. Resource consumption only, an exclusion; already on `main`. Not counted.

## Not checked
- The dependency audit — none exists for this product, as above.
- The suite was not run by this step: no fix and no bump was made, so there was nothing to keep on a green run (`SKILL.md` § *The suite*). The integrity step's green run stands as the branch's last suite evidence (`code-integrity-report.md`, `Integrity: pass`, `Environment: owners-mac — no CI`, at `f2fef62f6`).
- The test modules the change adds or rewrites were not reviewed for holes: a file that only tests is an exclusion.
