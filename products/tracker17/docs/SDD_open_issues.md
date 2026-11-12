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

> **No producing run wrote this file.** A `companion-self-answer` run opened it on 2026-11-12, in the
> Principal Architect's seat, while answering `products/tracker17/docs/architecture_open_issues.md`
> § 2.2. That item widens NFDR QC-39 to name the scenario folder's own pins and lock file, and QC-39
> traces to § 4 RT-4, which says every test dependency sits in `pyproject.toml` and one `uv.lock`.
> § 12 has § 4 win where the two disagree, so the file exists to keep them agreeing.
> `product-sdd` has no record of writing it. The run's reasoning is
> `products/tracker17/docs/trail/architecture/self_answer-28.md`.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — a best-effort answer was drafted; confirm or override

### 2.1 § 4 RT-4 says every test dependency is declared in `pyproject.toml` and locked in one `uv.lock`, while `.behave/` declares and locks its own
- **Raised by:** Principal Architect — outside the three lane seats, because the run that found it was answering the architecture companion
- **Seat:** cto
- **Drafted into the SDD:** nothing yet. The lean is two sentences at the end of RT-4's first paragraph: "The Behave scenario folder, `.behave/`, is test code with its own Python setup: its dependencies are declared at exact versions in `.behave/pyproject.toml` and locked in `.behave/uv.lock`, outside the suite's environment, and C-8 holds them as it holds the suite's. The rest of this condition is the suite's." Nothing else in RT-4 moves, and no slice, fence or § 7 edge moves.
- **Rationale:** `SDD.md:335-337`, RT-4, reads "They are declared in `pyproject.toml`, in its `dev` dependency group, and locked, with every dependency they pull in, in one committed file, `uv.lock`, beside `pyproject.toml`." Its heading, "Only the tests have dependencies", still holds, because `.behave/` is test code (NFDR QC-1). The sentence after it does not. `.behave/pyproject.toml` pins `behave==1.3.3`, `httpx==0.28.1` and `playwright==1.63.0`, and `.behave/uv.lock` locks them with what they pull in. The root `pyproject.toml` declares neither `behave` nor `httpx`. The folder is the Behave starter. The start-of-run Behave check writes it whole from core and commits it for a card that reads `Behave: behave` (`<CORE>/doctrine/setup/kensaiapp_structure.md` § Templates layer), and its README says a run "leaves the product's own `pyproject.toml` and `uv.lock` … as they were". So RT-4 describes the suite's set and is silent on a second one the product now holds. The NFDR is widening QC-39 to name both sets (`products/tracker17/docs/architecture_open_issues.md` § 2.2, answered), and QC-39 traces to RT-4. § 12 has § 4 win where the two disagree, so this item keeps them agreeing whichever fold runs first. RN-77 records that the round before this read the folder against § 3's units paragraph. It did not read the folder against RT-4.
- **If overridden:** RT-4 goes on saying the product holds one lock file while it holds two, and QC-39's widened words disagree with a § 4 condition that § 12 says wins. No code changes either way.
- **Confirm or override:** confirm, with three additions. The two sentences land as drafted, and C-8 holds the folder's pins as it holds the suite's: `uv run --locked behave`, the one command that runs the scenarios, stops with an error on a lock file out of step with `.behave/pyproject.toml`, as `uv sync --locked` does at the root (https://docs.astral.sh/uv/concepts/projects/sync/, "Automatic lock and sync", read 2026-11-12). (1) The sentence "No module outside `tests/` imports a test dependency" is false for the same folder and moves with it. `.behave/features/server_way_in.py` imports `httpx`, `.behave/features/browser_way_in.py` imports `playwright`, and `.behave/features/environment.py` and every module under `.behave/features/steps/` import `behave`. It reads "No module outside `tests/` and `.behave/` imports a test dependency", the scope NFDR QC-19 already carries and traces to RT-4. The draft's "Nothing else in RT-4 moves" misses that sentence. (2) The scope is stated where the claim is made, not at the paragraph's end: the condition's second sentence opens "The suite's are declared in `pyproject.toml`" in place of "They are declared in `pyproject.toml`", so a reader who stops at that sentence does not read "one committed file" as every test dependency's. (3) The folder's own environment and browser are fetched by its own commands, typed inside `.behave/`: `uv run --locked behave` builds the environment on its first run, and `uv run --locked playwright install chromium` fetches the browser, as `.behave/README.md` gives them. The setup instructions name neither, because the folder is not the suite and no stage runs it, so "Setting up the suite is the one step that needs a network connection" stays true of the suite. No slice, fence or § 7 edge moves, § 3's units paragraph stands, and no code changes. Reasoning: `products/tracker17/docs/trail/sdd/self_answer-22.md`.

## 3. Cut calls to confirm — where the slicing could reasonably have gone another way

None.

---

## 4. Disagreements — two seats hold different positions and neither yields

None.

## 5. Raised from downstream — an item from a seat that did not write the SDD

None.
