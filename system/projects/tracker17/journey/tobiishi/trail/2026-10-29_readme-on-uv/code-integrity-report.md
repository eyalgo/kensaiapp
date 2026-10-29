# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** tracker17 · 2026-10-29_readme-on-uv — the README sets up the test suite with uv.
**Reviewed:** `products/tracker17/README.md`, the one product file the branch changes (merge base
`898e1ccf6` to `<a commit not in the public history>`): the `### Running the tests` section, two `## How it's built` bullets and
the `docs/adr/` line under `## The documents`.
**Intent:** `tl_instruction.md` Task 1 (V1–V14), `change_spec.md` CP-668–CP-684, `change_design.md`
§ 5, `change_text.md`. `docs/fdr.md` read for R-8–R-14 and R-119–R-120 only, as the plan names them.

## Deferrals

None. The closing marker carries no `Deferred:` line and no `Failing:` line.

## Placement

No new logic. The parts table is `docs/SDD.md` § 3; the change adds no Python, only README prose, so
there is nothing to place.

## Tests added or fixed

None. Every rule is checked below instead (Calls made, 1).

## The finding

No issues. The README meets every rule of the spec:

- **CP-668–CP-674 (V1–V6):** the section's six paragraphs and command block are the `change_text.md`
  strings, placed verbatim: all six quoted strings and three fenced blocks found whole in the README,
  and the section holds exactly seven blocks, as the text says. Read against each rule: uv installed
  first, the installation URL, lower-case `uv` everywhere (no other casing in the file), the five-line
  block in order, sync and run explained, the Linux paragraph keeps all its statements, the `.venv`
  and new-terminal paragraphs name no activation step.
- **CP-672:** the bare-pytest pipeline printed nothing, exit 1.
- **CP-675, CP-679, CP-681 (V7, V10):** the setup slice and the Git paragraph are byte-identical to
  the merge base, and the thirteen headings are the same in text, level and order. The setup no-uv
  grep printed nothing, exit 1.
- **CP-676, CP-677 (V8):** the How it's built grep found uv on two lines, exit 0. The first bullet
  links ADR-0013, the file exists, and no ADR-0002 link remains.
- **CP-678 (V9):** the `docs/adr/` line states no count and still names `docs/adr/README.md`.
- **CP-680 (V11):** the whole-README fixed-string grep printed nothing, exit 1.
- **CP-682 (V12):** against the merge base, only `products/tracker17/README.md` differs under the
  product, the project card is identical, and nothing is untracked. Outside the section, the only
  three changed lines are the ADR link, the test bullet's last line and the `docs/adr/` line.
- **CP-683 (V13):** re-run here, in a fresh clone of `<a commit not in the public history>` on macOS, uv 0.11.14: `uv sync
  --locked` exit 0, `uv run playwright install chromium` exit 0, `uv run pytest tests/` 2698 passed
  exit 0, `uv run pytest tests/e2e/` 121 passed exit 0; `.venv` exists and `git check-ignore`
  printed `.venv/`; `uv.lock` matches its committed blob; `git status --short` printed nothing. The
  two pytest lines were run with `-q -p no:cacheprovider` added, which changes output and cache only:
  `.pytest_cache/` is ignored by the product's `.gitignore` either way.
- **CP-684 (V14):** the design's QC-12 and QC-41 verdicts hold for the diff as landed. It adds no
  part, and the only new setup step is installing uv from the named page.

## Calls made

1. **No permanent test for the README rules.** The question: the skill adds a test for every
   behaviour of the intent, and CP-682 says no test changes. Readings weighed: add a test reading the
   README, or prove each rule with the plan's review checks. Taken: the review checks, because
   CP-682 and `change_design.md` § 5 both forbid test edits, and the plan keeps the merge-base
   comparisons out of the suite on purpose. Whose call: the Product Owner's (`change_spec.md` CP-682)
   and the Architect's (`change_design.md` § 5). If they rule the other way, a later change adds a
   README test and none of this change's verdicts move.

## Language resolution

Python, from step 1, the project card's `Languages:`. Read the packet router
`languages/python/README.md` and its seven destinations: `toolchain.md`, `layout.md`,
`quality_gates.md`, `conventions.md`, `errors_logging.md`, `testing_python.md`, `environment.md`. One
rule bore on the change: `toolchain.md:85`, a bare `pytest` gets whatever pytest the machine has.
The README names no bare `pytest` command (CP-672). The rest bore on nothing, as no Python was
written.

## Test evidence

- One full-card run, through the gate tool, on the owner's Mac (no CI found, no environment entry in
  `docs/nfdr.md` § 8): `pytest products/tracker17/tests/` from the instance worktree root, 2698
  passed, exit 0. Its `Environment:` line is the one under the verdict.
- No earlier full-card run was made by this review.
