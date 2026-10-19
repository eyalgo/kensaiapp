# Change Design — A not-found page for an address with no project

**Date:** 2026-10-07
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the not-found page: its message, its link to Projects, and its page title

---

## 1. Change Summary

This is the structural plan for `change_spec.md` in this folder (CP-30 to CP-38). It places the not-found page and names the tests that prove it.

Today a `GET` for an address with no page answers 404 with an empty body (`web/routes.py:108-109`, `:130-131`). After this change, that request gets a whole HTML page, still with status 404. The page says there is no project at the address and links to Projects.

Only the `web` part changes. Paths in this document are relative to the product root, `products/tracker17/`, which is what `system/projects/tracker17/project.md` names in `Product path:`.

---

## 2. Blast Radius

Every new piece of logic is placed by `docs/SDD.md` § 3's parts table:

- **Building the not-found page** is owned by `web`, whose `Owns` cell holds "building each whole HTML page" (`docs/SDD.md:194`).
- **Deciding which requests get it** is also owned by `web`, which owns "the addresses of pages and actions" (same row).
- **Knowing whether a project exists** is already `application`'s, through `Tracker.project(identity)` (`web/routes.py:140`). This change does not touch that answer.

| Module | Status | What changes |
|---|---|---|
| `web/` | Modified | `web` part. `web/pages.py` gains the not-found page builder. `web/routes.py` answers a `GET` with no page with that page and status 404. This covers a `GET` that matches no route, and a project address naming no project. `web/listener.py` and `web/style.css` do not change. |
| `application/` | Unchanged | — |
| `domain/` | Unchanged | — |
| `persistence/` | Unchanged | — |
| `main.py` | Unchanged | — |
| `errors.py` | Unchanged | — |

**No transitive blast radius.** `web`'s public surface (`web/__init__.py`: `Listener`, `Response`, `Site`, `listen`) keeps its names and signatures. `main.py` is the only importer of `web` (`docs/nfdr.md` QC-17), and it is unaffected. No module imports from `web` in a new way, and `web` imports nothing new (QC-16).

---

## 3. Sub-jobs

The change touches one module, `web/`. It holds two separate seams with an ordering edge between them, so this section cuts two sub-jobs below module level. `web/routes.py` calls the page builder that `web/pages.py` must first expose. Each sub-job leaves the suite green when it lands.

### Sub-job W1 — `web/pages.py`, the not-found page

**Scope:** One new page builder. It returns the whole not-found page through the same `_document` frame every other page uses. That frame supplies the header with its one Projects link (CP-34) and the stylesheet link.

The page body has the following structure:

- The page's one `h1` is the sentence saying there is no project at this address. `docs/DESIGN.md:327` makes the UX-S10 message the page's `h1`.
- A paragraph directly in `main` follows it. The paragraph gives Projects as the place to go, as a link to `/`.
- Nothing else: no form, no other control, and no other link.

Every string, including the page title, comes from `change_text.md`. The module writes none of its own (`web/pages.py:5-7`).

**Exposes:** `pages.not_found_page()`. It takes no argument and returns `str`, a whole HTML document. Because it takes nothing, the page is the same for every address and can show no part of one. This is CP-33's "the same for every address" and "shows no part of the address", realized by construction.

**Depends on:** none.

### Sub-job W2 — `web/routes.py`, which requests get the page

**Scope:** `Site.handle` answers with W1's page, status 404, `Content-Type` HTML and the page policy, in exactly two places:

1. A request whose method is `GET` and that matches no route (CP-31). This place is new.
2. A `GET` that matches the project route but whose identity names no project (CP-30). This place exists today.

Both places come after the host check and the `Sec-Fetch-Site` check, so the 403 refusals are unchanged (CP-32). A request that matches no route and is not a `GET` keeps today's empty 404 (CP-32). `ROUTES` is unchanged, because it lists the addresses that have a page and the not-found page is not one of them. Nothing on this path saves, and nothing writes to the console (CP-36).

**Exposes:** nothing new. `Site.handle`'s signature is unchanged.

**Depends on:** W1 (`pages.not_found_page()`).

**Build sequence:**
```
W1
After W1: W2
```

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| W1 — `web/pages.py`, the not-found page | `web/style.css` already styles this structure: `h1` at `web/style.css:66`, and a paragraph directly in `main` as a sheet at `:79-82`. The page should need no new selector. |
| W2 — `web/routes.py`, which requests get the page | The not-found page is a fallback for `GET`, not an entry in `ROUTES`. Gate the no-route branch on the method, so `HEAD` and every other method keep the empty body. The HTML response helper builds status 200 only today, so it has to take the status. |

---

## 5. Test Additions

The new tests go into existing modules. `tests/architecture/test_trace.py` requires every test module's docstring to name an SRS identifier. No SRS requirement covers the not-found page: FDR R-105 takes it from SDD EX-13 (`docs/fdr.md:547`). Each touched module's docstring adds CP-30 to CP-38 to the change-spec rules it names.

| Sub-job | Test file | What to add / modify |
|---|---|---|
| W1 | `tests/integration/test_pages.py` | Add `"not found": pages.not_found_page()` to `all_pages()` (`:121-136`). Two existing tests then cover the page. The header test (`:155`) proves CP-34's header, that every link goes to `/` or a project, and that the page has no All tasks, People, rename or delete words. The no-script test (`:260`) proves CP-35's half for the page. |
| W1 | `tests/integration/test_pages.py` | New test for the not-found page (CP-33, CP-34): it has exactly one `h1`, and `main` holds exactly one link, to `/`. Every `a` on the page has `href="/"`. It has no `form`, `input`, `textarea` or `button`, and `main`'s text holds no "task". The `title` is not the Projects page's title and ends with " - tracker17". |
| W2 | `tests/integration/test_routes.py` | **Replace** `test_an_unknown_address_gets_404_with_an_empty_body` (`:348-356`), with `Alpha` created first. Targets: `/nowhere`, `/x/y`, `/projects`, `/projects/abc`, `/projects/0`, `/projects/99`, `/projects/99?created`, `/projects/1/` and `/nowhere?x=1`. Each answers 404 with an HTML `Content-Type`, the page policy, and a body equal to `pages.not_found_page()` encoded (CP-30, CP-31, CP-33, CP-35). |
| W2 | `tests/integration/test_routes.py` | **Replace** `test_a_project_identity_too_long_to_read_as_a_number_gets_404_with_an_empty_body` (`:359-366`). `/projects/` followed by 5,000 nines answers 404 with the not-found page and the policy, and the body holds no run of four nines (CP-30, CP-33). |
| W2 | `tests/integration/test_routes.py` | **Modify** `test_a_method_not_in_routes_gets_404_with_an_empty_body` (`:369-379`). Move `("GET", "/projects")` into the first replacement row, and add `("HEAD", "/projects/99")` and `("PUT", "/projects/99")`. These are CP-32's non-`GET` requests, and they keep an empty body. |
| W2 | `tests/integration/test_routes.py` | New test (CP-32): `GET /projects/99` and `GET /nowhere`, each marked `Sec-Fetch-Site: cross-site`, then each with a wrong `Host`. Each answers 403 with an empty body. |
| W2 | `tests/integration/test_routes.py` | New test (CP-36, state half): with a `RecordingSaver` and `Alpha` created, send every target from the first replacement row. The saver records nothing more, `tracker.projects()` is unchanged, and `capsys` shows nothing on either stream. |
| W2 | `tests/integration/test_listener.py` | **Replace** the empty-body assertion of `test_a_project_address_too_long_to_read_as_a_number_gets_404_and_writes_nothing` (`:93-101`). Over a real socket, the body is the not-found page, and the status and console checks stay. `:83-90`, the status and console check for `/nowhere`, and `:104-111`, the methods on `/` with an empty body, stay unchanged and pass. |
| W2 | `tests/e2e/test_first_project.py` | New test (CP-33, CP-34): run a tracker started by `main`. The browser opens `/projects/99`. The response status is 404, `main` shows the page's `h1`, there is no form, and every link on the page resolves to the tracker's `/`. The test then follows the link in `main` and lands on the Projects page. |
| W2 | `tests/e2e/test_first_project.py` | New test (CP-36, saved-data half): first start, no saved data. Open `/projects/99` and `/nowhere`, and `tracker.location` still does not exist. Then create `Alpha`, read the saved file's bytes, open both addresses again, and the bytes are unchanged. |

**Covered by existing rows:**

- **CP-30, `/projects/1` showing `Alpha`'s page:** `test_a_project_page_answers_with_the_project` in `tests/integration/test_routes.py`, unchanged.
- **CP-36, console half:** the `tests/integration/test_listener.py` rows above.
- **CP-37, no new part, seam or dependency:** `tests/architecture/test_imports.py`, unchanged (QC-13 to QC-19). CP-37's words half is the content step's, and the diff carries it.
- **CP-38:** both suites run.

**What this change stops proving.** The retired assertions are the `body == b""` checks at `tests/integration/test_routes.py:355` and `:365`, the `("GET", "/projects")` case of `:378` (its parameter at `:371`), and `tests/integration/test_listener.py:99`. Their clause, an empty 404 for a `GET` with no page, is gone. The replacements re-prove the status, the policy header and the console silence those tests also asserted. The empty-body clause still holds for non-`GET` requests, and the modified `:369-379` keeps proving it there.

---

## Records this change makes false

None. I read `docs/adr/` (0001 to 0009, all Accepted), `docs/nfdr.md`, `docs/fdr.md` and `docs/SDD.md` § 3, and nothing in them goes false. No record states that an unknown address answers with an empty body: `grep -n -i 'empty body\|404' docs/*.md docs/adr/*.md` returned nothing.

---

## Architect Review Notes

- **(b) The page's structure.** The sentence is the page's one `h1`, and the link to Projects sits in a paragraph after it. The spec says "one sentence … followed by … a link" (CP-33) and does not name the elements. `docs/DESIGN.md:327` makes the UX-S10 message the page's `h1`, and `docs/DESIGN.md:433` puts the message on a sheet, which `web/style.css:79-82` gives to a paragraph directly in `main`. The words in each element are the content step's.
- **(b) CP-31 and CP-32 are realized by the method, not by a list of paths.** Any `GET` that no route matches gets the page, and any other method keeps the empty 404. A list of paths could not cover "every other path" (CP-31). Gating on the method is what keeps `HEAD /projects/99` empty (CP-32).
- **(b) CP-33's "same page, no part of the address" is realized by construction.** `pages.not_found_page()` takes no argument, so it can show no part of an address. The tests compare the body byte for byte across every target.
- **(b) The tests go into existing modules.** QC-11's pointer test (`tests/architecture/test_trace.py`) fails a test module whose docstring names no SRS identifier. The not-found page traces to FDR R-105 and SDD EX-13 only, so a new module would have to name an SRS requirement it does not check.

**Reviews `docs/nfdr.md` delegates to `development-design`**

This change touches `web` only, so the reviews for a change to `web`, to page building, and every review apply.

| QC | Verdict |
|---|---|
| QC-8 | Pass. The page builder takes nothing and keeps nothing. A `Site` still holds only the tracker, the host and the lock. |
| QC-12 | Pass. The change adds one function and two branches, and no part. |
| QC-23 | Pass. `web` decides no rule. It asks `application` whether the project exists (`Tracker.project`) and shows the answer. |
| QC-27 | Pass. HTML and request detail stay in `web`. `domain`, `application` and `persistence` do not change. |
| QC-36 | Pass. The page puts no typed value and no part of the address into the page. The title goes through `_document`, which escapes it. |
| QC-41 | Pass. The change reads, holds and writes no secret. |
| QC-60 | Pass on a condition, because the harness gap stands. The new code must use nothing newer than Python 3.11. |
| QC-5, QC-20 to QC-22, QC-24 to QC-26, QC-46 | Not applicable. The change adds no refusal, saved field or saving change, and it does not touch `domain`, `application`, `persistence` or `main.py`. |
| QC-40 | **Packages:** Pass. I sent all 15 pins in `tests/requirements.txt` to `https://api.osv.dev/v1/querybatch` on 2026-10-07, and it returned no advisory for any of them. **Browser:** Pass today, failing tomorrow. Playwright 1.63.0 installs Chromium `153.0.8010.12` (its `browsers.json`, revision 1243). The Chrome Releases blog's "Stable Channel Update for Desktop" of 2026-09-08 fixes critical CVEs in `153.0.8010.36` (CVE-2026-87464, CVE-2026-87488, CVE-2026-87438 and two more). Those advisories are 29 days old today and pass 30 days on 2026-10-08. PyPI's newest Playwright is 1.63.0 (released 2026-09-15), so no newer pin exists to move to. From 2026-10-08, QC-40 leaves the owner two ways out: replace the browser, or record a dated exception in `docs/nfdr.md`'s Review Notes. I don't know whether the critical CVEs fixed in `152.0.7977.75` (published 2026-09-01) also affect `153.0.8010.12`. Chromium's fixed-in branch data for those CVE IDs would settle it. |
