# Code integrity report — 2026-10-11_django-10880

Integrity: pass

A clean pass. The code already does what its intent says. One test was added, for a behaviour the
intent states and no test proved, and it is green on the change and red on base. No code was
fixed and nothing was moved.

## Deferrals

**None.** The newest closing marker, `daa655e developer: 2026-10-11_django-10880 — implementation
complete`, read off the instance branch, carries no `Deferred:` line and no `Failing:` line, so
there is nothing to check against the four checks and no case is set aside.

## What was reviewed

The product's change worktree,
`<the issue's clone>/.worktrees/2026-10-11_django-10880`
(the path contract's `code_worktree`), from base `838e432e` to the Developer's green commit
`61a96a8e`:

- `django/db/models/aggregates.py`: one value in `Aggregate.as_sql`, line 71. The template's
  `distinct` key is now bound to `'DISTINCT '` (with one trailing space) when `self.distinct` is
  true, and to `''` when it is not.
- `tests/aggregation/tests.py`: nine tests added to `AggregateTestCase`, and four names added to
  the module's `django.db.models` import (`Aggregate`, `Case`, `Q`, `When`).

## The intent it was checked against

- `tl_instruction.md`, Task 1. Its *Behaviours to verify* (nine rows) and its *Held by review*
  items.
- `change_spec.md`, CP-9 to CP-16, with its Examples table and Locked Answers.
- `change_request.md`, the issue `django__django-10880` and its *What must not be done*.
- `docs/fdr.md` does not exist. The card reads `Definition: none`, so it is not owed and was not
  looked for further.

## Tests added or fixed

**Fixed: none.** Each of the Developer's nine tests was read against the rule it cites, and each
asserts what the rule says, not what the code happens to do:

| Test | Rule | Would it go red if the code were wrong? |
|---|---|---|
| `test_distinct_count_over_case_renders_space_after_distinct` | CP-9 | yes; red on base (FAIL) |
| `test_distinct_count_over_column_renders_space_after_distinct` | CP-9 | yes; red on base (FAIL) |
| `test_non_distinct_count_renders_unchanged` | CP-10 | yes, against a fix that adds the space to `Aggregate.template` (probe (a) below). Green on base, as the guard it is |
| `test_distinct_count_over_case_returns_distinct_value` | CP-11, CP-15 | yes; red on base (ERROR); asserts 2 against a plain twin of 3 |
| `test_distinct_count_over_case_with_default` | CP-11 | yes; red on base (ERROR); a dropped `DISTINCT` gives 9, not 2 |
| `test_distinct_count_over_case_per_group` | CP-11 (`.annotate()`) | yes; red on base (ERROR); author names are unique in the fixture, so the name→`n` mapping loses no row |
| `test_distinct_count_with_filter_on_backend_without_filter_clause` | CP-12 | yes; red on base (ERROR); a dropped `DISTINCT` gives 3, not 2 |
| `test_distinct_count_over_column_unchanged` | CP-13 | it is a guard on unchanged behaviour by design (8 before and after) |
| `test_distinct_aggregate_subclass_over_case` | CP-14 | yes; red on base (ERROR), and red against a fix made on `Count` alone (probe (b) below) |

**Added: one** — commit `5934ed36` in the product's change worktree.

- `test_distinct_count_over_case_with_several_whens`. CP-11 defines a conditional expression as
  "a `Case` with one or more `When` clauses, with or without a `default`". The tests covered
  *with and without a default*, but every one used a single `When`, so "or more" had no proof. The
  new test aggregates `Case(When(age__lte=29, then='age'), When(age__gte=50, then='age'))` over the
  existing nine authors. It asserts a distinct count of 3 (ages 29, 25 and 57) and a plain count
  of 4. The two differ, so the test cannot pass if `DISTINCT` is dropped. On base it errors with
  `OperationalError`, the issue's failure.

**Mutation probes.** I wanted to know whether any test would still pass if the code were wrong.
In a disposable copy of base (`git archive 838e432e`, under `/tmp`, removed afterwards), I tried
two plausible wrong fixes and ran the whole `aggregation` suite against each:

- (a) A space in `Aggregate.template` instead of in the bound value. Red:
  `test_non_distinct_count_renders_unchanged` (CP-10) and the existing `test_count_star`.
- (b) A template override with the space, on `Count` alone. Red:
  `test_distinct_aggregate_subclass_over_case` (CP-14), plus the two from (a).

## Runs

- The card's `Test command:` (`/home/kensai/issue-test.sh`), from the change worktree's root,
  after commit `5934ed36`: `Ran 75 tests`, `OK`, exit 0. The baseline file is empty, so any
  failure would have been new. CP-16 holds.
- The new tests on base, in the disposable copy, with
  `tests/runtests.py aggregation.tests.AggregateTestCase`: 8 red (2 FAIL, 6 ERROR). Those are
  every CP-9, CP-11, CP-12 and CP-14 row, the added one included. The CP-10 and CP-13 guards are
  green. This is the CP-15 *fail on the unchanged tree* half.
- Compile gate: `python -m compileall -q tests/aggregation/tests.py` with the card's interpreter,
  exit 0.

## Held by review

Each of the plan's three *Held by review* items was read against the diff and the tree:

- **The reach beyond `Aggregate`.** `ArrayAgg` and `StringAgg`
  (`django/contrib/postgres/aggregates/general.py` lines 13 and 54) put `%(distinct)s` directly
  before `%(expressions)s` and inherit `Aggregate.as_sql`. With `distinct=True` they now render one
  space after `DISTINCT`, which the spec's Out of Scope allows and does not require. No file under
  `contrib/postgres` is edited. No test reaches them, because `psycopg2` cannot be imported here.
- **A template that already has a space after `%(distinct)s`.** A grep of `django/` for
  `%(distinct)s` finds three templates, and none has a space after it, so nothing in the tree
  renders two spaces. A user subclass with such a template would, and no test pins that.
- **The value for a non-distinct aggregate.** It stays `''`. The only other `distinct` binding in
  the file, `options['distinct']` at line 93, belongs to the repr and is untouched.

## The finding

**No issues.** Every behaviour of the intent now has a test that asserts the intended value. The
one behaviour that had none, CP-11's "or more `When` clauses", got its test, and the test passed
against the code. No bug was found, no test was wrong, and nothing was misplaced.

**Carried forward, already recorded upstream, and not this change's to fix:**
`docs/ref/models/expressions.txt` line 378 still gives a stale default for `Aggregate.template`,
and the PostgreSQL aggregates have no proof. Both are listed as found defects for the PM in
`change_spec.md` § *Out of Scope* and `tl_instruction.md` § *Corrections owed while there*.

## Calls made

1. **Quote style in the added tests.** The question was whether the Python packet's
   double-quote rule (`conventions.md`, *Surface style*) binds the tests written into this
   Django checkout. The Developer's marker records single quotes as a divergence the packet
   outranks.
   - *Readings weighed.* (i) The packet wins over the file's habit
     (`languages/README.md` § *Precedence*, second paragraph), so the tests change to double
     quotes. (ii) The product has its own written rule, which outranks the packet under the same
     section's first paragraph: "A packet never overrides the product's own records".
   - *Taken: (ii).* Django's `docs/internals/contributing/writing-code/coding-style.txt` line 51
     reads "Use single quotes for strings, or a double quote if the string contains a single
     quote". That is a rule the product wrote down, not the file's habit, so single quotes are
     right, and the added test follows them too. The Developer's choice stands, but the reason is
     this record, not a divergence from the packet. The line-length bar does not conflict:
     Django's `setup.cfg` sets 119, the packet sets 100, and every added line is within 100.
   - *Whose call.* The owner's, as owner of the language doctrine, on whether a managed
     product's coding-style document counts among the "project decision files" that the
     precedence chain names as ADR / NFDR / FDR.
   - *If ruled the other way.* The new strings in `tests/aggregation/tests.py` (ten tests) would
     change to double quotes. Behaviour does not change.

## Placement

**No parts table.** The product has no `docs/SDD.md`, because the card reads `Definition: none`,
so there is nothing to place against and Step 0 was skipped. For the record, the change added no
new logic: it changed one existing value inside `Aggregate.as_sql`, where the defect was.

## Language resolution

- **Python.** Step 1 of the chain answered: `project.md` `Languages: Python`.
- Packet read: `<CORE>/doctrine/engineering/languages/python/README.md`, with its Conventions
  (`conventions.md`), Quality gates (`quality_gates.md`) and Testing
  (`<CORE>/doctrine/engineering/testing_python.md`) entries, plus `layout.md` for where a managed
  product's tests go.
- Applied: the Compile gate passed (exit 0). The Suite gate is the card's command, since the
  product runs Django's `runtests.py` and not pytest, and it passed (exit 0, 75 tests).
  `testing_python.md`'s seam rule holds, because the tests run real queries on the test database
  with no monkeypatch and no mock. Line length is within 100. Quote style is settled by the
  product's own record (*Calls made* 1). The `from __future__ import annotations` and
  `__version__` rules bear on no added module.

## The instance's domain

This instance's overlay asks about device storage, canonical addresses, LinkedIn and public claims
(`system/loaders/senior_engineer.md` § *The domain*). None of them applies here. The product is a
local Django checkout with no page, no form and no third-party script. No test reaches LinkedIn,
and no fixture states anything about KensaiApp or Eyal: the fixture data is Django's own
`aggregation` test data. Nothing is pushed or published (`Manages: none`).
