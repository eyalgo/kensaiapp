# SDD open issues — tracker17

> Companion to `SDD.md`. The CTO wrote the SDD; this file holds what that run could not settle from
> its inputs (the PRD, the SRS, the UXD, and any context or constraints), and the calls that are the
> CPO's or the CDO's to make. An item whose call is the CPO's or the CDO's carries that seat's
> `Seat:`; an item whose call is the CTO's carries `cto` or no `Seat:` field.
>
> **Answer inline** — fill each **Answer** / **Confirm or override** / **Keep or re-cut** /
> **Your call** slot — **commit this file**, then re-run `product-sdd`. It folds your answers into
> the SDD and drops the resolved items. When nothing is left open, `product-sdd` **deletes this
> file**: no file = the SDD is done.
>
> Your answers are never thrown away. Each time `product-sdd` folds them in, it first copies this
> file whole to `docs/trail/sdd/` — so what you decided, and why, stays readable and citable for good.
>
> **An item may name the seat that answers it.** Any item in any section carries an optional
> `- **Seat:** <seat>` field beside its other fields. Its value is the name of the agent whose posture
> answers the item — `cto`, `cpo` or `cdo`. An item with no usable value, whether the field is absent,
> empty or still the `<seat>` placeholder, is answered in the seat of the skill that produced this file.
> The field names the *answering* seat. It is not the seat that raised the item (`Raised by:` /
> `Held by:`), and it is not the document an answer belongs to.
>
> **An item in §§ 1–3 names the seat that raised it.** An item the CPO raised is a product call and
> an item the CTO raised is a technical one, and the answer that settles one does not settle the
> other. **§ 4 names two seats and no raiser** — a
> disagreement is not something one seat asked, it is two positions held by different seats, and the
> answer that settles it picks between them.
>
> **§ 5 names a raiser from outside the SDD's lanes entirely.** §§ 1–4 are all the SDD's own three
> lane seats; § 5 is a seat that never held a lane in it, reading it long after it settled and
> finding something only the SDD can fix. Its `Raised by:` therefore takes a wider set than §§ 1–3's,
> which stay fixed to the three lane seats on purpose.

> **No producing run wrote this file.** The PM opened it on 2026-10-08, in a route review, to carry
> item § 5.1. `product-sdd` has no record of writing it. It exists because § 11 R-9 has shown up on a
> Linux machine and the SDD still reads it as unchecked.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — a best-effort answer was drafted; confirm or override

None.

## 3. Cut calls to confirm — where the slicing could reasonably have gone another way

None.

---

## 4. Disagreements — two seats hold different positions and neither yields

None.

## 5. Raised from downstream — an item from a seat that did not write the SDD

### 5.1 § 11 R-9 has shown up: on Linux the end-to-end suite cannot start its browser, and a copy that is not a Git repository fails one test
- **Raised by:** PM — 2026-10-08
- **Seat:** cto
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_first-project`
- **What it blocks:** nothing on macOS. On Linux, the setup instructions' "Running the tests" section leads to a red `pytest tests/e2e/`, while the prerequisites say the tracker runs on macOS and Linux and say nothing more about Linux.
- **Where it shows:** § 11 R-9 (`SDD.md:1170-1175`) says "One run of the setup instructions and both suites on Linux would settle it". That run happened on 2026-10-08, on Debian 12 (bookworm), aarch64, following the README's "Running the tests" commands in a fresh copy. `python3 main.py` started and served. `pytest tests/` gave 224 passed. `pytest tests/e2e/` gave `1 failed, 1 passed, 10 errors`: `chrome-headless-shell: error while loading shared libraries: libglib-2.0.so.0: cannot open shared object file`. So the tracker needs no code of its own for Linux, as § 4 RT-3 (`SDD.md:268-272`) expects, but the browser the end-to-end layer drives needs system libraries the prerequisites do not name. Separately, in a copy that is not a Git repository, `pytest tests/` fails one test, the one that checks Git ignores `data/` (`pytest tests/` gave `1 failed, 223 passed`, the failure `test_data_is_ignored_by_version_control`). The README now says so under "Running the tests". § 6 S-1 *Artifact* (`SDD.md:655-660`) lists what the prerequisites hold, and names neither Git nor a Linux system library. The question for RT-3, R-9 and S-1 *Artifact*: should the prerequisites say what the end-to-end suite needs on Linux (for example `python -m playwright install --with-deps chromium`, which installs system packages and needs administrator rights), or should Linux be named for the tracker and not the end-to-end suite? And should Git be named as a prerequisite for the suite?
- **If a document has to be written:** none — the fold is an edit to `SDD.md`, by `product-sdd`. A changed prerequisite reaches the README through a later change.
- **Answer:** Both, and each bounded. **(1) Linux and the end-to-end suite.** The prerequisites say what the end-to-end suite needs on Linux, and Linux stays named for the tracker and for the suite. On Linux the browser the end-to-end layer drives needs system libraries an operating system does not ship by default; the instructions' section on running the suite gives, for Linux, `python -m playwright install --with-deps chromium` in place of `python -m playwright install chromium`, says it runs the distribution's package manager and asks for administrator rights, and says the tracker and `pytest tests/` need none of this. The bound: on Linux the end-to-end suite is supported where the pinned browser-driving library is, and its documentation lists Debian 12 and 13 and Ubuntu 22.04, 24.04 and 26.04, on x86-64 or arm64 (https://playwright.dev/python/docs/intro, read 2026-10-08, for the 1.63.0 pin, which PyPI listed as its newest the same day). Another Linux runs the tracker and `pytest tests/`, and `pytest tests/e2e/` is a missing prerequisite there. The list is the pin's, so it moves only when the pin does (SRS C-8); the system libraries are the operating system's, like Python, and are not declared dependencies under C-8. Where it lands: § 4 RT-3 keeps "checked on macOS only" for the instructions, because the Agari's check still reaches only macOS and no end-to-end run has passed on Linux; § 4 RT-4 adds that the one-time network step also fetches, on Linux, the system libraries the browser needs; § 6 S-1 *Artifact* adds the Linux line to what the suite section holds; § 11 R-9 is narrowed, not closed — the 2026-10-08 run on Debian 12 aarch64 settled the tracker (`python3 main.py` served) and the non-browser suite (224 passed), what remains unsettled is a green `pytest tests/e2e/` on Linux with the named libraries installed, no slice requires that run, and a Linux failure that needs code of its own is still a re-cut under § 10. **(2) Git.** Git is named as a prerequisite of the suite, not of the tracker: the full suite needs the copy to be a Git repository with `git` on the path, because the test behind NFDR QC-47 (`tests/integration/test_start.py`, `test_data_is_ignored_by_version_control`) runs `git check-ignore` and can pass only in one. The instructions say so and name the one test that does not pass otherwise, which `README.md` already does under "Running the tests", and S-1 *Artifact* records that. The test is not made to skip outside a repository, because that would read green in exactly the copy where QC-47 cannot be checked. The tracker's own setup and its three-command bound (SRS C-7) are untouched by both. Reasoning: `products/tracker17/docs/trail/sdd/self_answer-6.md` § 5.1.

**How it closes.** `product-sdd` folds it on its next run like every other item in this file, and
the trail copy and the delete-when-empty behaviour are unchanged.
