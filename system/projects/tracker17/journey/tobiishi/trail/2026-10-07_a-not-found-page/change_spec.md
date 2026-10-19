# Change Spec — A not-found page for an address with no project

**Date:** 2026-10-07
**Category:** feature
**Behaviour:** changing
**Request:** the **Request** of `change_request.md` in this folder, verbatim:

> Make an address for a project that does not exist show the not-found page instead of an empty 404. Run from `products/tracker17/` under `python3 main.py`. Today an unknown address answers 404 with an empty body (`tests/integration/test_routes.py:351-364`, `tests/integration/test_listener.py:88-110`). After this change the browser shows a page that says the project does not exist and links to Projects, and speaks of a project only: it names no task and offers no All tasks link, because tasks do not exist yet (SDD § 6 S-1; UXD UX-S10). The same page answers an address whose project identity is too long to read as a number, and the status stays 404. Nothing is written to `data/` by any of these requests. The page is built through the same parts and seams as the pages already there, with its words taken from the product's content record and no string invented in code.
>
> Tests ship with it: an end-to-end test that an address with no project shows the page with its one link to Projects and that following the link lands on the Projects page, and an integration test per route that answers it, replacing the empty-body checks that no longer hold. `pytest tests/` and `pytest tests/e2e/` each exit 0.
>
> **Must not be weakened or added:** the SDD's seams are used as written; no tasks, add-task form, People or All tasks links, rename or delete; no unreadable-data page and no second-tracker refusal; the one plain message when the address is taken is the next unit; the setup README is not touched beyond what the tests need; project creation, its refusals and saved data keep behaving as sealed in `2026-10-07_create-a-project-that-stays`.

---

## Change Summary

Today a browser that follows an address the tracker has nothing at, a project identity no project holds included, gets status 404 with an empty body, so the operator gets no page from the tracker and no way back. After this change the tracker answers such an address with its own not-found page, still with status 404, which says there is no project at this address and links to Projects.

The paths below are relative to the product root, which is the directory `system/projects/tracker17/project.md` names in `Product path:`. The FDR rules cited as `R-n` and `PD-n` are `docs/fdr.md`'s. The SDD, UXD and CONTENT sections cited are `docs/SDD.md`, `docs/UXD.md` and `docs/CONTENT.md` under that root. `CP-1` to `CP-29` are the rules of the sealed change spec `system/projects/tracker17/journey/tobiishi/trail/2026-10-07_create-a-project-that-stays/change_spec.md`. Every word a page shows is `docs/CONTENT.md`'s (SDD § 4 EX-11), so the rules below state what the page must say and leave its wording to the content step.

**Sizing.** The acceptance boundary is one operator action: following an address that names no project and being told so, with a way back (SDD § 6 S-1, *Behaviour*; UXD UX-S10; R-105). The page, its status, every address it answers and its tests are that one capability's acceptance obligations, so they stay together under `<CORE>/prompts/pm_right_size.md` § *Right-size to one honest merge*. The console message when something else holds the address reports a failed start, a different system responsibility with its own boundary, and the request leaves it to the next change unit.

---

## Rules

### Which requests get the not-found page

- **CP-30:** A `GET` request for `/projects/<id>`, where `<id>` is one or more ASCII digits and names no project, is answered with the not-found page and status 404. This holds for an identity of any number of digits, one of thousands of digits included, which is too long to read as a number. Today each such request answers 404 with an empty body (`tests/integration/test_routes.py:348-366`, the targets `/projects/0` and `/projects/99`, and the 5,000-digit identity). Which `<id>` values name an existing project is unchanged by this change. *(R-105; SDD § 4 EX-13; UXD UX-S10)*
- **CP-31:** A `GET` request whose path, the part of the address before any `?`, is one the tracker has no page at gets the same not-found page and status 404. The tracker has a page at three paths: `/`, `/style.css`, and `/projects/<id>` for an `<id>` that names a project. Every other path is in this rule, for example `/nowhere`, `/x/y`, `/projects`, `/projects/abc` and `/projects/1/`. Today each answers 404 with an empty body (`tests/integration/test_routes.py:348-356`; `/projects` at `tests/integration/test_routes.py:371`). *(UXD UX-S10, "or the address is wrong"; CONTENT § Message patterns, Error, "An address with nothing at it")*
- **CP-32:** CP-30 and CP-31 change only answers that are status 404 to a `GET` today. Every other answer a request gets today is unchanged. In particular, a request refused today for its host or its `Sec-Fetch-Site` mark is still refused with status 403 and an empty body. A request with any method other than `GET` that no route answers, `HEAD` included, still gets status 404 with an empty body. *(R-110; SDD § 4 SEC-2)*

### What the not-found page shows

- **CP-33:** The not-found page's message is one sentence saying there is no project at this address, followed by the Projects page as the place to go, given as a link. It names no cause, so it never says the project was deleted. It names no task and points to no place other than Projects. The page is the same for every address CP-30 and CP-31 cover, and it shows no part of the address. Its page title names it as the not-found page. The words of the message and of the title are CONTENT's: § Message patterns, Error, "An address with nothing at it", with its task sentence and its All tasks link left out, and § Accessibility's page-title pattern. *(UXD UX-S10; SDD § 6 S-1, *Behaviour*; CONTENT RN-11)*
- **CP-34:** The not-found page carries the header every page carries, which links to Projects and to no other area (SDD § 4 EX-12; CP-9). Every link on the page leads to the Projects page. The page has no All tasks link, no People link, no form, and no control that changes data. Following the message's link shows the Projects page.
- **CP-35:** The not-found page meets every condition CP-23 sets for a page: it loads nothing from outside the machine, runs no script, and shows no error text produced by Python. Its response carries, as a header, the same page policy every other page's response carries (SDD § 4 SEC-3). The browser shows it as a page.

### What such a request changes

- **CP-36:** A request answered with the not-found page changes nothing. When saved data exists, its bytes are the same after the request as before. When no saved data exists, the request creates none, and no `data/` directory appears. The tracker's console shows nothing for the request. *(R-106; SDD § 4 OB-1)*

### How it is built

- **CP-37:** The page is built by the `web` part, behind the seams SDD § 3 names, as the Projects page and a project's page are. The change adds no part, no seam and no dependency outside Python's standard library (SDD § 3; `docs/adr/0001-rule-core-behind-server-rendered-pages.md`; `docs/adr/0002-standard-library-only-no-web-framework.md`; PD-6). Every word the page shows is taken from `docs/CONTENT.md` through the content step, and no word on the page is one CONTENT does not hold (SDD § 4 EX-11).

### Its tests

- **CP-38:** `pytest tests/` and `pytest tests/e2e/`, each typed from the product root inside the virtual environment that holds the test dependencies, each exit 0 (SDD § 6, "Both suites pass"). They include:
  - an end-to-end test in which the browser, against a tracker started by `main`, opens an address naming no project. It finds the not-found page with its link to Projects, and no link that leads anywhere but the Projects page. It follows the message's link and lands on the Projects page (CP-33, CP-34);
  - an integration test for each route that answers with the not-found page: a project address naming no project, one with an identity too long to read as a number included (CP-30), and an address no page has (CP-31). Each finds status 404, the page's message, its link to Projects, and the page policy in the response header (CP-35);
  - a test that requests answered with the not-found page leave existing saved data's bytes unchanged and, where no saved data exists, create no `data/` (CP-36);
  - a test that the refused and non-`GET` requests CP-32 names keep their answers.

  The empty-body checks this change makes false are replaced, not deleted without a replacement: `tests/integration/test_routes.py:348-356` and `:359-366`, the `("GET", "/projects")` case at `tests/integration/test_routes.py:371`, and the empty-body assertion of `tests/integration/test_listener.py:93-101`. The checks that still hold stay and pass unchanged. These are the non-`GET` checks at `tests/integration/test_routes.py:369-379` (the `GET` case aside) and `tests/integration/test_listener.py:104-111`, and the status and console checks at `tests/integration/test_listener.py:83-90`.

---

## Examples

| Rule | Scenario | Expected behaviour |
|---|---|---|
| CP-30 | `Alpha` is project 1. The browser opens `/projects/99` | The not-found page, status 404. |
| CP-30 | The browser opens `/projects/` followed by 5,000 nines | The same not-found page, status 404. No part of the 5,000 digits shows on it. |
| CP-30 | `Alpha` is project 1. The browser opens `/projects/1` | `Alpha`'s page, as before this change. |
| CP-31 | The browser opens `/nowhere` | The not-found page, status 404. |
| CP-31 | The browser opens `/projects/abc` | The not-found page, status 404. |
| CP-31 | The browser opens `/projects/1/` with project 1 existing | The not-found page, status 404. |
| CP-31 | The browser opens `/nowhere?x=1` | The not-found page, status 404. |
| CP-32 | `GET /projects/99` marked `Sec-Fetch-Site: cross-site` | Status 403 with an empty body, as today. |
| CP-32 | `PUT /` or `HEAD /projects/99` | Status 404 with an empty body, as today. |
| CP-33 | Any address CP-30 or CP-31 covers | One sentence saying there's no project at this address, then a link to Projects. No mention of a task, of deletion, or of All tasks. The page title names it as not found. |
| CP-34 | The links on the not-found page | The header's Projects link and the message's Projects link. Nothing else. |
| CP-34 | Follow the message's link | The Projects page. |
| CP-35 | The response to `/projects/99` | Carries the page-policy header every page carries. No script and no Python error text on the page. |
| CP-36 | Saved data holds `Alpha`. Open `/projects/99`, then `/nowhere` | The saved data's bytes are unchanged, and the console shows nothing. |
| CP-36 | A first start with no saved data. Open `/projects/99` | No `data/` directory exists afterwards. |
| CP-37 | Reading the change's diff | No new part, seam or outside dependency. Every word the page shows is one `docs/CONTENT.md` holds. |
| CP-38 | `pytest tests/`, then `pytest tests/e2e/`, from the product root | Both exit 0, and the tests CP-38 lists are among those run. |

---

## Verified Claims

All commands ran on 2026-10-07 against commit `9e915896e`, in a disposable copy of the product made with `git archive HEAD products/tracker17` (`<CORE>/roles/CROSS_ROLE.md` § *Every seat*), from its product root, under Python 3.14.

| Claim | Verified by | What came back |
|---|---|---|
| Today a `GET` for a project address naming no project, of any length, answers 404 with an empty body (CP-30) | `Site.handle` from `tests/integration/test_routes.py`'s own `make_site`, with `Alpha` created first, `GET` with the same-origin marks | `/projects/99` 404, 0 bytes. `/projects/0` 404, 0 bytes. `/projects/` + 5,000 nines 404, 0 bytes. |
| Today a `GET` for a path with no page answers 404 with an empty body (CP-31) | Same harness | `/nowhere`, `/projects/abc`, `/projects/1/`, `/x/y` and `/projects` each 404, 0 bytes. |
| The same holds under a real start, and nothing is written to the data location (CP-30, CP-31, CP-36) | `main.start(("127.0.0.1", 0), <empty temp dir>/data)` in a child process, then `curl` with `Sec-Fetch-Site: none` to `/projects/99`, `/nowhere` and `/projects/` + 5,000 nines | The ready message printed. Each answered `404` with 0 bytes. `ls <temp>/data` afterwards: "No such file or directory". |
| A refused request and a non-`GET` request answer as CP-32 keeps them | Same `Site.handle` harness | `PUT`, `HEAD` and `DELETE` `/projects/99` each 404, 0 bytes. `GET /projects/99` marked `Sec-Fetch-Site: cross-site` 403, 0 bytes. |
| Which `<id>` names a project is the existing reading, which this change leaves alone (CP-30) | Same harness, `GET /projects/001` with `Alpha` as project 1 | 200, the same 439-byte page `/projects/1` returns. |
| The checks this change replaces and the ones it keeps pass today (CP-38) | `python3 -m pytest -p no:cacheprovider -q tests/integration/test_routes.py tests/integration/test_listener.py` | `57 passed`. |
| The tracker has a page at `/`, `/style.css` and `/projects/<id>`, and at no other `GET` path (CP-31) | Reading `web/routes.py` `ROUTES`, then the harness rows above | `GET /`, `GET /projects/[0-9]+`, `GET /style.css` and `POST /projects`. `/projects/1` answered 200; every other `GET` path probed answered 404. |
| The header every page carries links to Projects only (CP-34) | Reading `web/pages.py` `_document` | The header holds the product name and one `<a href="/">Projects</a>` in its `nav`. |
| CONTENT's not-found formula names project and task and two links, and the page title is "Not found - tracker17" (CP-33) | Reading `docs/CONTENT.md:225-230` and `:348-352` | "one sentence that says there is no project or no task at this address, then the two places to go as links. It names no cause." The title example list holds "Not found - tracker17". |
| The highest `CP-<n>` in the project's record is CP-29, so this series starts at CP-30 | `grep -rhoE 'CP-[0-9]+' system/projects/tracker17/ products/tracker17`, numbers sorted | Highest is `29`. |

---

## Out of Scope

- The not-found page speaking of a task, and its All tasks link. Tasks and All tasks do not exist yet, and SDD § 6 S-1 *Behaviour* and § 4 EX-12 keep both off every page until their slices.
- The console message when something else holds the address (R-4, second sentence). The next change unit of this station delivers it.
- Tasks, the add-task form, the People and All tasks links, renaming a project and deleting one. The request excludes each.
- The page for saved data that cannot be read (UXD UX-S9; R-25, R-26) and the refusal of a second tracker (R-5). The request excludes both. While the saved data is unreadable the tracker does not serve (CP-7), so no not-found page is shown then.
- Requests with a method other than `GET`, and requests refused for their host or their `Sec-Fetch-Site` mark. Their answers stay as they are (CP-32).
- Which forms of `<id>` name an existing project, such as `/projects/001` showing project 1. This change does not alter that reading.
- The setup instructions in `README.md`, beyond what the tests need. The next station delivers them.
- Project creation, its refusals and the saved data's behaviour, which stay as `CP-1` to `CP-29` sealed them.

---

## Locked Answers (the divergence record — self-review 2026-10-07)

- **Gap 1 — addresses that name no project identity at all:** `/nowhere`, `/projects/abc` and every other `GET` path the tracker has no page at get the not-found page too (CP-31). The request's first sentence names "an address for a project that does not exist". Its own account of today, though, cites the check that covers `/nowhere`, `/x/y` and `/projects/abc` as the behaviour this change replaces. It also asks for "an integration test per route that answers it", in the plural. UXD UX-S10 includes the case "the address is wrong", and CONTENT's pattern is "An address with nothing at it". The page's one sentence, that there is no project at this address, is true at every such address. Without this rule, a mistyped address would still get an empty answer with no way back, which is the dead end this change removes. The choice is reversible.
- **Gap 2 — methods other than `GET`, and requests refused today:** their answers are unchanged (CP-32). The request speaks of addresses a browser follows, and a browser follows an address with `GET`. The checks guarding these answers are not among the ones the request says no longer hold. The 403 refusal is R-110's protection against another origin, which this change has no reason to touch.
- **Gap 3 — "its one link to Projects" beside the header's Projects link:** the page carries both, and every link on it leads to Projects (CP-34). SDD § 4 EX-12 puts the header on every page but the unreadable-data page. CONTENT's pattern puts the place to go in the message, as a link. The station's reached-when 2 and SDD § 6 S-1 say the page "links to Projects only", which names the destination, not a count of links. So the end-to-end test checks the destination of every link, and follows the message's link.
- **Gap 4 — the CONTENT formula's second place:** the message gives Projects as its only place to go and leaves out All tasks (CP-33). CONTENT's formula names "the two places to go", and its examples name All tasks. The request and SDD § 6 S-1 drop the All tasks link until that area exists, and SDD § 4 EX-12 forbids a page pointing to an area that does not exist yet.
- **Gap 5 — the page shows no part of the address:** the page is the same for every address it answers (CP-33). The request does not say. CONTENT's formula carries no address, and a page repeating the address would show thousands of digits for CP-30's longest case. The choice is reversible.
- **Gap 6 — the page title:** it names the page as not found (CP-33). The request does not mention a title. CONTENT § Accessibility gives every page a title naming its subject, and its examples hold "Not found - tracker17".
- **Gap 7 — the console:** a request answered with the not-found page shows nothing in the console (CP-36). The request names only `data/`. SDD § 4 OB-1, and `tests/integration/test_listener.py:83-90` today, keep the console free of per-request output, and an address with nothing at it is not a failure R-107 reports.
- **Gap 8 — the page policy header:** the not-found response carries it (CP-35). The request does not name it. SDD § 4 SEC-3 puts the policy on every response, and today's 404 answers already carry it (`tests/integration/test_routes.py:356`, `:366`).
