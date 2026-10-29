# Change request — 2026-10-29_readme-on-uv

*The PM-minted intake for one **飛び石 Tobiishi** — the single change the chain
(`core/launchers/chain-development/launcher.sh <project>` → `core/tools/chain_development.py`) carries
through the pipeline. Lives at `system/projects/<name>/journey/tobiishi/<key>/change_request.md` (`<key>` =
`<YYYY-MM-DD>_<slug>`). The PM writes this when opening the Tobiishi, through `tobiishi-open`; `development-specs`
reads it as the pipeline's first input — it does **not** coin the key or scan a queue. **No `Project:`
field** — the project is implied by which project's `journey/tobiishi/` this sits in.*

---

**Request:** Make the product README tell the reader to set up the test suite with uv. Today its "Running the tests" section (`products/tracker17/README.md`, L93-L109) has the reader make a `venv`, activate it and `pip install -r tests/requirements.txt`, a file the last change deleted, so those instructions no longer work. SDD § 4 RT-4 and ADR-0013 already give the uv path. After this change:

- "Running the tests" says uv has to be installed first, and where to get it. Its command block is `cd products/tracker17`, `uv sync --locked`, `uv run playwright install chromium`, `uv run pytest tests/` and `uv run pytest tests/e2e/`. The Linux paragraph says to type `uv run playwright install --with-deps chromium` in place of the install command. The `.venv` paragraph and the "new terminal, `source .venv/bin/activate`" paragraph are reworded to match uv (no activation step; `uv sync --locked` makes `.venv`). The `pytest tests/` and `pytest tests/e2e/` prose names the `uv run` forms.
- The "How it's built" test line says the suite's environment is made by uv, in place of "Python's `venv`".
- `grep -nF -e 'python3 -m venv' -e 'pip install' -e 'requirements.txt' -e 'activate' -e 'python -m playwright' -e '`venv`' README.md` prints nothing and exits 1.
- The tracker's own setup text (`## Setup instructions` down to `### Running the tests`) names uv nowhere, and the tracker's start path stays `python3 main.py` with nothing installed. That text changes only for a sentence this edit makes false.

Each command is the one SDD § 4 RT-4 gives, and works from `products/tracker17` on `main`. No tracker code, test, record under `docs/`, or project card line changes: the card's Setup and Test commands are the next station's.

**Classified because:** the station's reached-when changes the setup instructions a reader follows (uv must now be installed, and the commands are `uv sync --locked` and `uv run …`), a new thing the README tells the reader to act on, and it is build and test-environment tooling that ADR-0013 and NFDR QC-39 drive; no tracker behaviour moves. So `nfdr`, `changing`.

---

*Sizing (`pm_right_size.md`): one capability, one merge. Acceptance boundary: the station's four reached-when items, source `journey/shukuba/2026-10-29_readme-on-uv.md`. The two README places state one fact and must not disagree, so they move together.*
