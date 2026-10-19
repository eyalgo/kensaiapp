# Code integrity report — 2026-10-12_comments-on-the-page

Integrity: pass

This report records the Senior Engineer's integrity review of the comments change. The review
checked the change's code against its intent and added one missing test. The test passed against
the code as it stands, so no bug was found.

**Reviewed at:** `560c28c62` (`developer: 2026-10-12_comments-on-the-page — implementation complete`),
on branch `2026-10-12_comments-on-the-page`. Product root: `products/tracker17/`. Every product path
below is relative to that root.

## Deferrals

None. The newest closing marker, `560c28c62`, carries no `Deferred:` line.

## What was reviewed

Everything the branch changed under the product root, from `git diff --stat 3b5746f91..560c28c62 -- products/`
(22 files):

- production: `domain/comments.py` (new), `domain/tasks.py`, `domain/refusals.py`,
  `domain/__init__.py`, `application/tracker.py`, `application/__init__.py`, `web/pages.py`,
  `web/routes.py` and `web/style.css`;
- every test module the change added or modified, the five new ones included.

## The intent it was checked against

- `tl_instruction.md`: Tasks 1–5, each one's *Behaviours to verify* and *Held by review*, and the
  TL Review Notes.
- `change_spec.md`: CP-240–CP-272, CP-274 and CP-275, and the Examples table.
- `change_design.md`: §§ 2–5, rows T01–T22, and the Architect Review Notes. The Architect set
  CP-273 aside (*Request/spec timing conflict*), so CP-273 was not checked.
- `change_text.md`: every string.
- `docs/SDD.md` § 3 (the parts table), § 4 SEC-4, `docs/fdr.md` R-112, and `docs/DESIGN.md`
  § Layout "Comments" and § Components "The comment textarea", which the instruction holds by review.

## Tests added or fixed

- **Added:** `tests/integration/test_comment_pages.py::test_comment_lines_and_add_name_show_the_title_as_text`,
  with two cases, `failed` and `added`.
  - SDD § 4 SEC-4 says every value the operator typed is escaped when it enters a page, and FDR
    R-112 says it then shows as typed. `change_text.md` says `{title}` is "the task's title as saved,
    shown whole".
  - This change puts the task's title into three new places on the page: the Add button's accessible
    name, the failure line and the completion line. Every comment test used the plain title
    `Set up CI`, so none of them would fail if those three places stopped escaping the title.
  - The new test uses a title holding `<b>`, `&` and both kinds of quote. It asserts the exact
    accessible name, and the exact line that describes the focused element.
  - It is the comment-area match for `test_every_label_outcome_line_shows_typed_text_as_text`,
    which the label change added for the same gap
    (`system/projects/tracker17/journey/tobiishi/trail/2026-10-12_task-labels/code-integrity-report.md`).
  - Proof that it discriminates: I removed the escaping from `_comment_outcome` (in `web/pages.py`)
    and both cases went red. I then removed only the escaping from the Add button's `aria-label`,
    and both went red again. `git checkout` restored `web/pages.py` after each mutation, so it is
    byte-identical to the branch.

No test was fixed. I read every other test the change added or modified against the rule it names.
Each one asserts what the intent says. None was written to match the implementation, and the
CP-274 edits change only the clauses CP-274 releases.

## The finding

No issues. No bug was found, nothing was misplaced, and the one added test passed against the code
as it stands. Before any edit the suite was green: `pytest products/tracker17/tests/` gave
1045 passed, and `pytest products/tracker17/tests/e2e/` gave 33 passed.

The two strings and the stylesheet that the instruction holds by review were read by hand, and they
match their sources:

- Every page string and console string in `web/pages.py` and `web/routes.py` matches `change_text.md`
  word for word, the singular count forms included.
- The `web/style.css` comment rules match `docs/DESIGN.md`: a 1px `--surface-sunk` line between
  comments, and the meta line at 0.875rem, line height 1.4, `--ink-muted`. The textarea has no
  height rule and keeps `resize: vertical`.

## Calls made

1. **Does `conventions.md`'s `__version__` marker bind tracker17's code?** The developer raised this
   and did not settle it.
   - The readings weighed: (a) it binds, so `domain/__init__.py` and the other package
     `__init__.py` files owe a marker; (b) it does not bind product code.
   - I took (b), because the rule's own text names its scope. `core/doctrine/engineering/languages/python/conventions.md:153-154`
     says the marker "is `versioning.md`'s marker for a script, in the spelling Python already has
     for it". `core/doctrine/governance/versioning.md:154-155` lists a product's own artifacts as
     out of scope: "A product's artifacts version by the product's rules, not the instance's."
   - Reading (a) would also add markers to every module in the product, and no module of tracker17
     has one today. That is product-wide scope, which this change did not ask for.
   - This is the owner's to confirm, since doctrine is user-owned (`core/roles/CROSS_ROLE.md` § 3).
     If the owner rules (a), a later change adds a marker to each package's `__init__.py` across
     the product, and nothing in this change needs to be redone.
2. **Is `comment_added=02` a malformed position?** `change_design.md` § 3 D says malformed positions
   produce the ordinary area, and `web/routes.py` `_position` reads `02` as position 2.
   - The readings weighed: zero-padded digits are malformed, or they are a well-formed decimal
     number.
   - I took "well-formed". The tracker itself only writes `str(len(task.comments))`. The address
     authorizes nothing (Architect Review Notes, *Mixed address outcomes*), so the only effect of a
     padded value is that focus goes to the comment it names.
   - No code or test changed for this. This is the Architect's to confirm. If they rule
     "malformed", `_position` refuses a leading zero, and one case is added to
     `test_comment_query_accepts_only_recognized_outcomes`.

## Placement

Checked against `docs/SDD.md` § 3. Each piece of new logic is already in the part that owns it, so
nothing was moved and there is no placement commit.

- `domain`: the frozen `Comment` value, `check_comment_text`, `create_comment`,
  `check_saved_comment` and `check_saved_comments` (`domain/comments.py`); `add_task_comment` and
  the restore check that `restore_task` hands to them (`domain/tasks.py`); `BlankComment`,
  `OperatorNameNotSet` and `TextField.COMMENT` (`domain/refusals.py`). The domain row owns "every
  rule that accepts or refuses a change" and "one typed refusal per refused condition".
- `application`: `Tracker.add_task_comment` (`application/tracker.py`). It reads one instant, then
  saves the new state before making it current, which is the application row's "Each action".
- `web`:
  - `web/routes.py` holds the route, `_position`, `_comment_area`, `_add_comment` (it reads the
    form, calls one action and maps each refusal by its type) and `_comment_failure_line`.
  - `web/pages.py` holds `CommentRefusal`, `CommentArea` and the rendering helpers, `_written`
    among them.
  - `_written` turns the stored instant into the machine's local time. That needs the time zone,
    not the injected clock, and `change_design.md` § 3 D puts local-time formatting in `web`.
  - No rule, text-length check or state comparison is in `web`.

## Language resolution

- **Language:** Python. Chain step 1 answered it: `system/projects/tracker17/project.md` `Languages: Python`.
- **Packet read:** `core/doctrine/engineering/languages/python/README.md` and the three entries this
  skill reviews against: `conventions.md`, `quality_gates.md` and `core/doctrine/engineering/testing_python.md`.
- **Results for the line this review added:**
  - It stays within 100 columns (`conventions.md:17`). I measured every added line, because the
    product's ruff does not check line width.
  - It uses double quotes.
  - It hands in no fake and patches nothing (`testing_python.md`, "The seam is a hand-written fake").
- **The code against the same entries:** I found no divergence beyond the one the developer raised.
  That one is settled as Call 1 above.

## Verification

All results below come from runs in this review. They use the pinned environment
`/private/tmp/tracker17-venv`, which matches `tests/requirements.txt`. The main suite ran under a
pty, because `tests/integration/test_start.py` sends SIGINT.

- In the worktree, with the added test:
  - `pytest products/tracker17/tests/`: 1047 passed.
  - `pytest products/tracker17/tests/e2e/`: 33 passed.
  - From the product root, each of these exited 0: `python3 -m compileall -q domain application persistence web main.py errors.py`,
    `ruff format --check .`, `ruff check .`, `mypy main.py errors.py domain application persistence web`
    and `python3 tests/timed_run.py`.
  - `git diff --exit-code 3b5746f91 -- products/tracker17/tests/timed_run.py products/tracker17/tests/integration/test_timed_run.py`
    exited 0, so both timing files are byte-identical.
- In a fresh clone (CP-275, `core/roles/CROSS_ROLE.md` § *Every seat*):
  - The clone is `/private/tmp/tracker17-cir.3VfGYM`, checked out at `560c28c62`, with this
    commit's one test file copied in. Nothing else in the clone differs from that commit.
  - Results: `pytest products/tracker17/tests/` gave 1047 passed, and `pytest products/tracker17/tests/e2e/`
    gave 33 passed.
