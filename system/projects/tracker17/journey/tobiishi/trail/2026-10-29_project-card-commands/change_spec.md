# Change Spec — the project card sets up and runs the suite through uv

**Date:** 2026-10-29
**Category:** nfdr
**Behaviour:** changing
**Request:** Change the two commands on the project card (`system/projects/tracker17/project.md`) that the chain runs in a new change worktree, so the suite is set up and run through uv. The Setup command stops being `none` and makes the suite's environment from `uv.lock` (for example `uv sync --locked --project products/tracker17`). The Test command runs the whole suite through uv (for example `uv run --project products/tracker17 pytest products/tracker17/tests/`) instead of a bare `pytest`. Both commands run from the worktree's root, while `pyproject.toml` and `uv.lock` sit in `products/tracker17`, so each names that directory. If a run of the suite shows the Playwright browser the end-to-end layer needs is not otherwise there, the Setup command makes it ready too. The card's `.venv` must come out under `products/tracker17`. One change, one merge: the two commands are one fact, since the environment the setup makes is the one the test command runs in. What must not be weakened: `pyproject.toml`, `uv.lock`, every test and all tracker code stay as they are, and no pin, test or marker is changed to make the commands pass. The suite is not narrowed: the Test command still runs `products/tracker17/tests/` whole, with no layer excluded. The card's other lines (`Product path:`, `Languages:`, `Execution type:` and the rest) and the template comments on the two lines stay as they are. The README's uv instructions are done and are not re-written. Not here: the review moment (QC-40), the Python 3.11 run (QC-60), the SDD prerequisites wording, and the README `## Status`. Acceptance (the station's reached-when, checked in a fresh clone from its root): (1) the Setup value is not `none` and contains `uv`, the Test value contains `uv` and no bare leading `pytest`; (2) with no `products/tracker17/.venv` beforehand, the Setup command through `/bin/sh` exits 0 and `.venv` exists afterwards; (3) the Test command through `/bin/sh` exits 0 with the unit, integration, architecture and end-to-end layers collected; (4) the diff touches `system/projects/tracker17/project.md` and nothing under `products/tracker17/` beyond a README sentence the edit makes false.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `core/doctrine/engineering/languages/python/README.md` opened

---

## Change Summary

The card's `Setup command:` becomes a uv command that makes `products/tracker17/.venv` from `uv.lock`, and its `Test command:` runs both of the product's suites through uv, so that every later change's worktree is set up and judged on the locked test dependencies rather than on whatever `pytest` the machine has. Only those two values change.

---

## Rules

The product's location is the card's `Product path:` (`products/tracker17`); "the worktree root" is the root of the change's worktree, the directory the suite gate runs `Test command:` in. Every command below is run through `/bin/sh`.

### Setup command

- **CP-685:** The card's `**Setup command:**` value is not `none` and makes the suite's environment with `uv sync --locked` against the project whose `pyproject.toml` and `uv.lock` sit in `products/tracker17` (the command and its flag fixed by ADR-0013 § Decision and SDD § 4 RT-4). Run from a tree with no `products/tracker17/.venv`, it exits 0, `products/tracker17/.venv` exists afterwards, and no `.venv` exists at the worktree root.
- **CP-686:** The Setup command gives CP-685's result from either of two directories: the worktree root, and `products/tracker17`, which is where the chain's worktree creation runs it today (`core/tools/create_change_worktree.py:15`, "runs the card's `Setup command:` once, in the product directory of the new worktree"; `:326`, `:476`). From either, it writes no line beginning `warning:` to its error stream.
- **CP-687:** When `uv.lock` is out of step with `pyproject.toml`, the Setup command exits non-zero and leaves `uv.lock` byte-identical (the refusal ADR-0013 § Decision fixes for `--locked`).

### Test command

- **CP-688:** The card's `**Test command:**` value runs its test commands through `uv run`, against the same project in `products/tracker17` (fixed by ADR-0013 § Decision, "Every suite command is typed through `uv run`"). Its first word is not `pytest`.
- **CP-689:** Run from the worktree root after the Setup command, the Test command runs both suites SDD § 6 names, from the card's paths. The first is every test under `products/tracker17/tests/` outside `tests/e2e/`, which is the unit, integration and architecture layers. The second is every test under `products/tracker17/tests/e2e/`, the end-to-end layer. It exits 0 only when both exit 0, which is SDD § 6's "Both suites pass". It exits non-zero when a test in either suite fails or either suite fails to collect. Its output carries each suite's own pytest summary line. Nothing narrows either suite: no test, file, layer or marker is deselected, ignored or skipped by the command.
- **CP-690:** The Test command never rewrites `uv.lock`. When `uv.lock` is out of step with `pyproject.toml`, it exits non-zero before any test runs and leaves `uv.lock` byte-identical. When the two are in step, `uv.lock` and every tracked file under `products/tracker17/` are unchanged after it runs.

### What the change touches

- **CP-691:** On the card, only the values of `**Setup command:**` and `**Test command:**` change. Every other line, and the HTML comment that trails each of the two lines, stays byte-identical.
- **CP-692:** The change's diff touches `system/projects/tracker17/project.md` and, under `products/tracker17/`, at most a README sentence that the card edit makes false. This spec found no such sentence: the README's suite commands are typed from `products/tracker17` (`products/tracker17/README.md:95-101`), and it names neither the card nor the worktree root.

---

## Examples

| Scenario | Expected behavior |
|---|---|
| Fresh clone, worktree root, no `products/tracker17/.venv`: run the Setup command (CP-685) | exits 0; `products/tracker17/.venv` exists; no `.venv` at the root |
| Same fresh state, run from `products/tracker17` instead (CP-686) | exits 0; `.venv` exists in `products/tracker17`; nothing created at `products/tracker17/products/` |
| Either directory: the Setup command's error stream (CP-686) | holds no line beginning `warning:` |
| `pyproject.toml` edited so `uv.lock` is stale, then the Setup command (CP-687) | non-zero exit; `uv.lock` byte-identical |
| The card's two lines read with `grep -nE '^\*\*(Setup\|Test) command:\*\*'` (CP-685, CP-688) | Setup value not `none` and contains `uv`; Test value contains `uv` and does not begin with `pytest` |
| Root, after setup, all tests green: run the Test command (CP-689) | exits 0; two pytest summary lines, today `2698 passed` (unit 622, integration 2012, architecture 64) and `121 passed` (end-to-end) |
| One unit test made to fail in a scratch copy, then the Test command (CP-689) | non-zero exit |
| One end-to-end test made to fail in a scratch copy, the rest green (CP-689) | non-zero exit |
| `pyproject.toml` edited so `uv.lock` is stale, then the Test command (CP-690) | non-zero exit before a test runs; `uv.lock` byte-identical |
| In-step lock, after the Test command (CP-690) | `git status --short -- products/tracker17` shows nothing |
| `git diff` of the card before and after (CP-691) | two changed lines, each differing only in its value; trailing comments unchanged |
| `git diff --stat` of the change (CP-692) | `system/projects/tracker17/project.md`, plus this change folder's own files; nothing under `products/tracker17/` |

---

## Verified Claims

All runs were in a fresh clone of the instance at `858d64443` (`<scratch>/c`), on the owner's Mac (the environment the suite gate reports as `Environment: owners-mac — no CI`), with uv 0.11.14, each command run through `/bin/sh`.

| Claim | Verified by | What came back |
|---|---|---|
| The chain's worktree creation runs `Setup command:` in the product's directory inside the worktree, not at the worktree root (CP-686) | `uv run --locked pytest -q core/tools/test_create_change_worktree.py -k setup_runs_in_the_in_repo_product_directory`, the test asserting the marker lands in `<worktree>/prod` and not at `<worktree>` | `1 passed`; source `core/tools/create_change_worktree.py:15`, `:326`, `:476` |
| The suite gate runs `Test command:` from the worktree root for an in-repo product (CP-689) | read `core/tools/gate_suite.py:2146-2149`, `cwd = paths["product_worktree"]`, with `development_path.py resolve` for this change giving `product_worktree` = the instance worktree | the worktree root |
| The request's example Setup form makes `.venv` in the product from the root (CP-685) | from `<scratch>/c`: `uv sync --locked --project products/tracker17` | exit 0; "Creating virtual environment at: products/tracker17/.venv"; no root `.venv` |
| The same form, run from `products/tracker17`, passes only through a fallback uv warns about (CP-686) | from `<scratch>/c/products/tracker17`, `.venv` removed first: the same command | exit 0, `.venv` made in `products/tracker17`, and stderr line 1: "warning: Project directory `products/tracker17` does not exist. This will become an error in a future release." |
| CP-686 can be met: a form that names the product from the repository's top level works from both directories with no warning | from the root and from `products/tracker17`, `.venv` removed before each: `uv sync --locked --project "$(git rev-parse --show-toplevel)/products/tracker17"` | exit 0 both times; 0 `warning:` lines; `.venv` only in `products/tracker17` |
| One pytest run of `products/tracker17/tests/` leaves out the end-to-end layer (CP-689) | `uv run --project products/tracker17 pytest --collect-only -q products/tracker17/tests/`; the rule is `pytest_ignore_collect` in `products/tracker17/tests/conftest.py:53` | exit 0; 2698 collected: architecture 64, integration 2012, unit 622, end-to-end 0 |
| Naming `tests/e2e/` in the same pytest run breaks collection, so both suites cannot be one invocation without changing tests (CP-689) | `uv run --project products/tracker17 pytest --collect-only -q products/tracker17/tests/ products/tracker17/tests/e2e/` | exit 2; "5 errors during collection", each "import file mismatch": `tests/unit/` and `tests/e2e/` share `test_comments.py`, `test_labels.py`, `test_sorting.py`, `test_summary.py`, `test_tasks.py` |
| Both suites run as two uv commands from the root pass, with no browser fetch first (CP-689) | after the setup above: `uv run --project products/tracker17 pytest -q products/tracker17/tests/ && uv run --project products/tracker17 pytest -q products/tracker17/tests/e2e/` | exit 0; `2698 passed in 275.75s`, then `121 passed in 54.52s`; 5 min 31 s in all |
| The pinned Playwright's browser is already on this machine, outside the clone (Locked Answer, Gap 5) | `uv run --project products/tracker17 playwright install --dry-run chromium` | Chromium v1243 and its headless shell at `<home>/Library/Caches/ms-playwright/chromium-1243` and `chromium_headless_shell-1243`, both present |
| A plain `uv run` rewrites a stale `uv.lock` and passes; `--locked` refuses it (CP-690) | `requires-python` set to `>=3.12` in the clone's `pyproject.toml`, then `uv run --locked --project products/tracker17 pytest -q products/tracker17/tests/unit/test_tasks.py`, then the same without `--locked`, with `shasum` of `uv.lock` after each; the clone restored with `git checkout` | `--locked`: exit 2, "The lockfile at `uv.lock` needs to be updated, but `--locked` was provided", hash unchanged (`0fb98cc6…`). Plain: exit 0, hash changed (`3baff1eb…`), `M products/tracker17/uv.lock` |
| A locked `uv run` on an in-step lock runs and writes nothing (CP-690) | `uv run --locked --project products/tracker17 pytest -q products/tracker17/tests/architecture/` on the restored clone | `64 passed`; `git status --short` empty; `uv.lock` hash `0fb98cc6…` |
| `uv sync --locked` refuses a stale lock (CP-687) | `requires-python` set to `>=3.12` in the clone's `pyproject.toml`, then from the root `uv sync --locked --project "$(git rev-parse --show-toplevel)/products/tracker17"`, with `shasum` of `uv.lock` after; the clone restored with `git checkout` | exit 1; `uv.lock` hash unchanged (`0fb98cc6…`) |
| No README sentence is made false by the card edit (CP-692) | read `products/tracker17/README.md` whole; `grep -n 'project.md\|worktree\|Test command\|Setup command'` on it | no match; suite commands at `:95-101` are typed, after `cd products/tracker17` at `:96` from `products/tracker17` |

---

## Out of Scope

- `pyproject.toml`, `uv.lock`, every test and all tracker code, including `tests/conftest.py`'s collection rule and the five test file names that `tests/unit/` and `tests/e2e/` share. The Test command works with them as they are.
- The card's other lines and the two trailing comments (CP-691). Adding a `**Dependencies command:**` line is out too. The card has none, and a card without one reads as none (`core/templates/project_template.md:12`).
- The README: its uv instructions, already done, and its `## Status` section.
- NFDR QC-40's review moment for `uv.lock` alerts.
- NFDR QC-60's run on Python 3.11 (`uv run --python 3.11 pytest tests/`, SDD § 11 R-8). This spec states no rule on which interpreter the Test command runs on.
- The SDD's wording on what the setup instructions' prerequisites section names.
- Getting the Playwright browser ready on a machine whose Playwright cache lacks Chromium v1243, and Linux's `--with-deps` step. See Locked Answer Gap 5.
- `products/tracker17/docs/nfdr.md:633-634`, "run with the project card's `Test command:`; typed from the product root, as every row here is, that command is `pytest tests/`. SDD § 6 names `pytest tests/e2e/` beside it as the second suite". After this change the card's command runs both suites through uv, so that sentence no longer describes it. The request's diff stops at the card, and the NFDR is not this change's to edit. Handed on in `deferred_decisions.md`.
- Where the chain's worktree creation runs `Setup command:`. The card template's comment says "in the directory Test command: runs in" (`core/templates/project_template.md:11`), and the suite gate runs `Test command:` from the worktree root (`core/tools/gate_suite.py:2146-2149`). Worktree creation runs it in the product's directory instead (`core/tools/create_change_worktree.py:15`, `:476`). That disagreement is in kensaiapp's core, not in tracker17. CP-686 holds whichever way core settles it.

---

## Locked Answers (the divergence record — self-review 2026-10-29)

- **Gap 1 — where the Setup command runs (b):** CP-686 requires the Setup command to work from both the worktree root and `products/tracker17`. The request says "Both commands run from the worktree's root". That holds for the Test command (`core/tools/gate_suite.py:2149`). It does not hold for the Setup command, which the chain runs in `products/tracker17` (Verified Claims, row 1). The station's check (2) runs it from the clone's root. A command that works in only one of the two places fails either the chain or the station's check.
- **Gap 2 — no warning (b):** CP-686 bars a `warning:` line. The request's example form passes from `products/tracker17` only through a fallback that uv says "will become an error in a future release" (Verified Claims, row 4). A uv upgrade would then halt every tracker17 change when its worktree is made. A form with no warning passes in both places today (row 5).
- **Gap 3 — both suites, as SDD § 6 counts them (c):** CP-689 asks for two suite runs, not the request's example of one pytest run over `products/tracker17/tests/`. That example exits 0 with the end-to-end layer not collected (Verified Claims, row 6), which fails the station's check (3). A single run naming both directories fails collection (row 7). The request keeps every test as it is, so the conftest rule and the shared file names cannot change. That leaves two runs, which is how SDD § 6 already defines "Both suites pass", and row 8 shows both pass.
- **Gap 4 — the Test command never rewrites `uv.lock` (b):** The request says nothing on a stale lock. A plain `uv run`, the request's example form, rewrote a stale `uv.lock` and still exited 0 (Verified Claims, row 10). The suite gate would then pass a change whose lock file had quietly moved, and leave the product's tree changed. ADR-0013 turns down a plain `uv sync` for the same reason: SRS C-8 asks for the versions the suite last passed with. CP-690 is the safe choice and can be undone later. It changes nothing when the lock is in step (row 11).
- **Gap 5 — the browser (b):** The request makes readiness conditional: "If a run of the suite shows the Playwright browser … is not otherwise there". The run showed it is there. The pinned Playwright's Chromium v1243 is in the machine's own Playwright cache, outside any worktree (Verified Claims, row 9), and the end-to-end suite passed with no fetch first (row 8). So no rule requires the Setup command to fetch it. Design may still add the readiness step SDD § 4 RT-4 names. If it does, CP-685 to CP-687 still bind it.
