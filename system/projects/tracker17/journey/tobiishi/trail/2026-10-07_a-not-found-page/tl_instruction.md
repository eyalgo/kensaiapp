# Tech Lead instruction — a-not-found-page: a not-found page for an address with no project

**Product root:** products/tracker17 — every path below is relative to it.
**Category:** feature
**Behaviour:** changing
**Scope:** `web` only. A `GET` with no page, or for a project that does not exist, answers the not-found page with status 404 (CP-30 to CP-38). Nothing else changes.

---

## Project layout

```
products/tracker17/
  web/
    pages.py                 ← modified (not_found_page)
    routes.py                ← modified (404 fallback for GET; _html takes a status)
  tests/
    integration/
      test_pages.py          ← modified
      test_routes.py         ← modified
      test_listener.py       ← modified
    e2e/
      test_first_project.py  ← modified
```

No new files, directories or `__init__.py`. `web/listener.py`, `web/style.css`, `ROUTES`, `application/`, `domain/`, `persistence/`, `main.py` and `errors.py` do not change.

`docs/SDD.md` § 3 places "building each whole HTML page" and "the addresses of pages and actions" in `web`; both tasks stay in `web/`.

## TL Review Notes

Decisions that diverged from, or locked what was left implicit in, `change_design.md` / `change_spec.md`:

- **Behaviour locked — the words.** `change_design.md` §3 says every string comes from `change_text.md`. No `change_text.md` exists in this change folder, and `web/pages.py` today holds its words as literals taken from `docs/CONTENT.md`. Task 1 takes them from CONTENT the same way, and the content step may replace them: the sentence `There's no project at this address.` (`docs/CONTENT.md:225-230`, the message pattern, task sentence and All tasks link left out per CP-33), the place to go `Open Projects.` with `Projects` as the link to `/`, and the title `Not found - tracker17` (`docs/CONTENT.md:352`). Tests assert structure, the link and the title, and that `main` text holds no "task"; they never assert the whole sentence, so a content-step rewording does not break them.
- **Behaviour added:** `test_not_found_page_is_the_same_for_every_target` is made explicit in Task 2 (body equals `pages.not_found_page()` encoded for each target, which is the design's byte-for-byte rule), and the page's `Content-Type` is asserted HTML for each target. Implied by CP-33 and CP-35, and by design §5's rows, but not named test by test.
- **Behaviour added:** `GET /projects/99?created` and `GET /nowhere?x=1` in Task 2 prove the query never changes the answer (CP-31 "before any `?`"); the existing `created` flag must not leak into the not-found answer.
- **Behaviour added:** `test_non_get_requests_with_no_route_keep_an_empty_404` also keeps `DELETE /projects/99`, which the spec's Verified Claims probed (CP-32).
- **Hint kept as written:** §4's two hints are carried unchanged. The W2 hint's "HTML response helper takes the status" is the approach; the signature is the developer's.
- **Dependencies:** Task 2 lists Task 1 because it calls `pages.not_found_page()`; Task 1 uses nothing from Task 2. No order-only edge.
- **Atomicity:** the design's two sub-jobs stay two tasks. Each leaves the suite green when it lands (W1 adds a builder and a test that covers it; W2 changes the answer and replaces the checks that no longer hold).

## Corrections owed while there

- `tests/integration/test_pages.py` (module docstring) — names CP-1 to CP-29 only → add CP-30 to CP-38 to the change-spec rules it names (`tests/architecture/test_trace.py` reads the docstring). Rides Task 1.
- `tests/integration/test_routes.py` and `tests/integration/test_listener.py` (module docstrings) → add CP-30 to CP-38 likewise. Rides Task 2.
- `tests/e2e/test_first_project.py:1-7` (module docstring) → add CP-30 to CP-38 to the rules it names. Rides Task 2.

### Task 1: Not-found page builder (`web/pages.py`, `tests/integration/test_pages.py`)

**Dependencies:** None

**What to build:** `pages.not_found_page()`, taking no argument and returning the whole HTML document through the existing `_document` frame, so the header's one Projects link and the stylesheet link come with it. Body: one `h1` holding the sentence that there is no project at this address, then one paragraph directly in `main` that gives Projects as the place to go, as a link to `/`. No form, no other control, no other link, no part of an address.

#### Behaviours to verify (developer adds tests to `tests/integration/test_pages.py`)

- `all_pages()` gains a `"not found"` entry built from `pages.not_found_page()`, so the existing header test (every link goes to `/` or a project; no All tasks, People, rename or delete words) and the existing no-script / no-outside-address test cover the page (CP-34, CP-35).
- `test_the_not_found_page_has_one_heading_and_one_link_to_projects` — exactly one `h1`; `main` holds exactly one link and its `href` is `/`; every `a` on the page has `href="/"`.
- `test_the_not_found_page_has_no_form_or_control` — no `form`, `input`, `textarea` or `button`.
- `test_the_not_found_page_says_nothing_of_a_task` — `main` text does not contain "task" (case-insensitive) and does not say anything was deleted.
- `test_the_not_found_page_title_names_it` — the title is not the Projects page's title and ends with ` - tracker17`.
- `test_the_not_found_page_takes_no_address` — calling it with an argument raises `TypeError`, so no part of an address can reach it.

#### Implement

Infer from failing tests.

# Hint: `web/style.css` already styles this structure — `h1` at `:66`, and a paragraph directly in `main` as a sheet at `:79-82`. The page should need no new selector and no `web/style.css` change.

#### Verification gate

`pytest products/tracker17/tests/` from the worktree root (the card's `Test command:`, which collects 184 tests today), and `pytest tests/` from the product root.

Pass criteria: this task's tests pass; no new failures elsewhere.

### Task 2: Which requests get the page (`web/routes.py`, `tests/integration/test_routes.py`, `tests/integration/test_listener.py`, `tests/e2e/test_first_project.py`)

**Dependencies:** Task 1 (calls `pages.not_found_page()`)

**What to build:** `Site.handle` answers the not-found page, status 404, HTML `Content-Type` and the page policy, in exactly two places: a `GET` that matches no route, and a `GET` for a project address whose identity names no project, including an identity too long to read as a number. Both come after the host and `Sec-Fetch-Site` checks, so the 403 refusals are unchanged. A non-`GET` request with no route keeps its empty 404. `ROUTES` is unchanged. Nothing on this path saves or writes to the console.

#### Behaviours to verify (developer edits the three files named)

In `tests/integration/test_routes.py`, with `Alpha` created first:

- `test_a_get_with_no_page_gets_the_not_found_page` — replaces `test_an_unknown_address_gets_404_with_an_empty_body` (`:348-356`). Targets `/nowhere`, `/x/y`, `/projects`, `/projects/abc`, `/projects/0`, `/projects/99`, `/projects/99?created`, `/projects/1/`, `/nowhere?x=1`. Each: status 404, an HTML `Content-Type`, the page policy header, and a body equal to `pages.not_found_page()` encoded (CP-30, CP-31, CP-33, CP-35).
- `test_a_project_identity_too_long_to_read_as_a_number_gets_the_not_found_page` — replaces `:359-366`. `/projects/` followed by 5,000 nines: 404, the page policy, the same body as above, and the body holds no run of four nines (CP-30, CP-33).
- `test_a_method_not_in_routes_gets_404_with_an_empty_body` (`:369-379`) is modified: `("GET", "/projects")` moves out to the first replacement's targets; `("HEAD", "/projects/99")`, `("PUT", "/projects/99")` and `("DELETE", "/projects/99")` are added. Each keeps status 404 and an empty body (CP-32).
- `test_a_refused_get_stays_refused` — `GET /projects/99` and `GET /nowhere`, each marked `Sec-Fetch-Site: cross-site`, then each with a wrong `Host`: 403 with an empty body (CP-32).
- `test_requests_answered_with_the_not_found_page_change_nothing` — with a `RecordingSaver`, send every target of the first replacement. The saver records nothing more, `tracker.projects()` is unchanged, and `capsys` shows nothing on either stream (CP-36).
- `test_a_project_page_answers_with_the_project` is unchanged and still passes (`/projects/1` shows `Alpha`).

In `tests/integration/test_listener.py`:

- The empty-body assertion of `test_a_project_address_too_long_to_read_as_a_number_gets_404_and_writes_nothing` (`:93-101`) is replaced: over a real socket the body is the not-found page; the status and console checks stay. `:83-90` and `:104-111` stay and pass unchanged.

In `tests/e2e/test_first_project.py`:

- `test_an_address_with_no_project_shows_the_not_found_page` — a tracker started by `main`; the browser opens `/projects/99`; status 404; `main` shows the page's `h1`; no form; every link on the page resolves to the tracker's `/`; following the link in `main` lands on the Projects page (CP-33, CP-34).
- `test_not_found_requests_write_nothing` — first start with no saved data: open `/projects/99` and `/nowhere`; `tracker.location` still does not exist. Then create `Alpha`, read the saved file's bytes, open both addresses again; the bytes are unchanged (CP-36).

#### Held by review

- `CP-37` (no new part, seam or dependency; every word from CONTENT) — `tests/architecture/test_imports.py` covers the imports unchanged; the words half is held by reading the diff against `docs/CONTENT.md`.
- `CP-38`'s "the checks that still hold stay and pass unchanged" — held by reading the diff: only the lines listed above change.

#### Implement

Infer from failing tests.

# Hint: the not-found page is a fallback for `GET`, not an entry in `ROUTES`. Gate the no-route branch on the method, so `HEAD` and every other method keep the empty body. The HTML response helper builds status 200 only today, so it has to take the status.

#### Verification gate

`pytest products/tracker17/tests/` from the worktree root, then from the product root `pytest tests/` and `pytest tests/e2e/`.

Pass criteria: this task's tests pass; both product-root suites exit 0; no new failures elsewhere.
