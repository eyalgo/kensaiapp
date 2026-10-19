# Tech Lead instruction — django-10880: a distinct aggregate over a conditional expression produces valid SQL

**Product root:** <the issue's clone>/.worktrees/2026-10-11_django-10880 — every path below is relative to it.
**Category:** bug
**Behaviour:** changing
**Scope:** `Aggregate.as_sql` binds the template's `distinct` value as `DISTINCT` followed by one space; the change's own tests go in `tests/aggregation/tests.py`. Nothing else changes.

**What this task may bring in:** no new third-party origin, no dependency, no device storage, no documentation edit. The only new imports are names from `django.db.models` in the test module (Task 1).

---

## Project layout

```
<product-root>/
  django/db/models/
    aggregates.py            ← modified (Aggregate.as_sql, one value)
  tests/aggregation/
    tests.py                 ← modified (new tests in AggregateTestCase; imports extended)
```

No parts table — placement follows change_design.md §2. No directory or `__init__.py` is created.

## TL Review Notes

Decisions that diverged from `change_design.md` / `change_spec.md` (each with its reason):
- **Single task kept:** design §3 is omitted, and the plan keeps it one task. One product module changes at one site; the tests prove that site, and the only edge between them is red-then-green, which the test-first lane already carries.
- **Imports pinned:** design row 7 says `Q`, `Case` and `When` (and `Aggregate` for row 9) must be imported. The module already imports `Value` and `IntegerField`, which rows 5 uses, so only `Aggregate`, `Case`, `Q` and `When` are added. Without it the developer meets `NameError` instead of the real red.
- **Behaviour made explicit:** that NULL branches are not counted is stated in the issue's-case test (2, not 3), as design's *Rule-implied edges* paragraph says, rather than left as a separate test.
- **Behaviour added:** row 9's subclass renders without a `template`, so the rendered-SQL check there runs through `.annotate()` only, as the design says. No separate non-distinct row for the subclass is added; CP-10 is fenced by row 3.
- **Held by review, not by a test:** the design's reach on PostgreSQL `ArrayAgg`/`StringAgg` and on a user template that already puts a space after `%(distinct)s` is pinned by no test (design Architect Review Notes (b)). The plan carries it as a review item.

## Corrections owed while there

- Owed outside this change's reach: `docs/ref/models/expressions.txt` line 378 — the documented default of `Aggregate.template` reads `'%(function)s( %(expressions)s )'` while the code's default is `'%(function)s(%(distinct)s%(expressions)s)'`. It is already false today and this change does not make it worse → the line should state the code's default. The request asks for no documentation change, and the spec carries this as a found defect for the PM.

### Task 1: Distinct separator in `Aggregate.as_sql` (`django/db/models/aggregates.py`, `tests/aggregation/tests.py`)

**Dependencies:** None

**What to build:** the value `Aggregate.as_sql` binds to the template's `distinct` key is `DISTINCT` plus one trailing space when `self.distinct` is true, and stays the empty string when it is not. `Aggregate.template` does not change. All three rendering paths read that one value: the plain path, the `FILTER (WHERE ...)` path and the `CASE WHEN` fallback for a backend without `FILTER`. The tests are added to `AggregateTestCase` in `tests/aggregation/tests.py`, using its existing `setUpTestData` (nine authors, three aged 30 or under holding two distinct ages). No new fixture. Add `Aggregate`, `Case`, `Q` and `When` to the module's `django.db.models` import.

#### Behaviours to verify (developer adds tests to `tests/aggregation/tests.py`, class `AggregateTestCase`)

Rendered-SQL tests assert that the aggregate's fragment is *contained* in `str(queryset.query)` of an `.annotate()` queryset. They never compare the whole statement.

- `test_distinct_count_over_case_renders_space_after_distinct` — `annotate(n=Count(Case(When(age__lte=30, then='age')), distinct=True))` renders a query containing `COUNT(DISTINCT CASE WHEN`. (CP-9; red on base)
- `test_distinct_count_over_column_renders_space_after_distinct` — `annotate(n=Count('age', distinct=True))` renders a query containing `COUNT(DISTINCT "aggregation_author"."age")`. (CP-9; red on base)
- `test_non_distinct_count_renders_unchanged` — `annotate(n=Count('age'))` contains `COUNT("aggregation_author"."age")`, and `annotate(n=Count(Case(When(age__lte=30, then='age'))))` contains `COUNT(CASE WHEN`. (CP-10; fence, green on base and after)
- `test_distinct_count_over_case_returns_distinct_value` — the issue's case: `aggregate(n=Count(Case(When(age__lte=30, then='age')), distinct=True))` equals `{'n': 2}`; in the same test the same aggregate without `distinct=True` equals `{'n': 3}`, so the test cannot pass if `DISTINCT` is dropped. The NULL branches (`ELSE NULL`) must not be counted. (CP-11; red on base)
- `test_distinct_count_over_case_with_default` — `aggregate(n=Count(Case(When(age__lte=30, then=Value(1)), default=Value(0), output_field=IntegerField()), distinct=True))` equals `{'n': 2}`. (CP-11; red on base)
- `test_distinct_count_over_case_per_group` — `Author.objects.annotate(n=Count(Case(When(age__lte=30, then='age')), distinct=True))`: `n` is 1 for the three authors aged 30 or under and 0 for the other six. Assert the whole name→`n` mapping so row order does not matter. (CP-11; red on base)
- `test_distinct_count_with_filter_on_backend_without_filter_clause` — `aggregate(n=Count('age', distinct=True, filter=Q(age__lte=30)))` equals `{'n': 2}`. On SQLite this goes through the `CASE WHEN` fallback. (CP-12; red on base)
- `test_distinct_count_over_column_unchanged` — `aggregate(n=Count('age', distinct=True))` equals `{'n': 8}`. (CP-13; fence)
- `test_distinct_aggregate_subclass_over_case` — a subclass of `Aggregate` defined in the test with `function = 'COUNT'`, `allow_distinct = True` and no `template`: `aggregate(n=<it>(Case(When(age__lte=30, then='age')), distinct=True))` equals `{'n': 2}`, and the rendered SQL of the same expression in `.annotate()` contains `COUNT(DISTINCT CASE WHEN`. (CP-14; red on base)

#### Held by review (omit when every rule of this task reaches a test)

- The reach beyond `Aggregate`: `ArrayAgg` and `StringAgg` in `django/contrib/postgres/aggregates/` inherit `Aggregate.as_sql`, so with `distinct=True` they also gain the single space. Covered by no test, because `psycopg2` cannot be imported here. Held by reading the diff: the diff edits no file under `contrib/postgres`, and the one changed value is the one they inherit.
- A user subclass whose own template already writes a space after `%(distinct)s` now renders two spaces. No such template exists in the tree, and no test pins it. Held by reading the diff: `Aggregate.template` is unchanged.
- The diff adds nothing to the value bound for a non-distinct aggregate: it stays `''`. Rows 3 and 8 fence the rendering and the value; the reading confirms no other aggregate path was touched.

#### Implement

Infer from failing tests.

# Hint: The seam is the value bound to the `distinct` key at the top of `as_sql`, not `Aggregate.template`. A space added to the template would reach every non-distinct aggregate (breaking CP-10) and would leave subclasses with their own templates unfixed. The value is bound once, before the three branches, and all of them reuse it, so the `CASE WHEN` fallback (CP-12) needs no edit of its own.

#### Verification gate

Run `/home/kensai/issue-test.sh` from the product root (the card's `Test command:`; it runs the issue's scoped suite and passes only when every failing test already failed at base).

Pass criteria: this task's new tests pass; the command exits 0 with no failing test. At base it runs 65 tests with the baseline of known failures empty, so a failure of any test is a new failure. The red rows (1, 2, 4, 5, 6, 7, 9) fail on the unchanged tree.
