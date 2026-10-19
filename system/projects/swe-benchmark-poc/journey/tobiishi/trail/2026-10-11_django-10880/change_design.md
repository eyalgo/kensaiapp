# Change Design — A distinct aggregate over a conditional expression produces valid SQL

**Date:** 2026-10-11
**Category:** bug
**Behaviour:** changing
**Publishes text:** no

---

## 1. Change Summary

`Aggregate.as_sql` (`django/db/models/aggregates.py`) supplies the template's `distinct` value as the
bare word `DISTINCT`. The default template, `'%(function)s(%(distinct)s%(expressions)s)'`, then puts
nothing between that word and the aggregated expression's SQL. The fix puts the separator into the
`distinct` value itself: one trailing space when `distinct=True`, and the empty string as today
otherwise. The template stays as it is. Every rendering path inside `Aggregate.as_sql` reads that one
value: the plain path, the `FILTER (WHERE ...)` path and the `CASE WHEN` fallback for a backend
without `FILTER`. So one site meets CP-9, CP-11, CP-12 and CP-14. CP-10 holds by construction,
because the non-distinct value is unchanged. One product module changes, and the change's tests go
into the `aggregation` test app, the one suite the card's `Test command:` runs.

What crosses to the outside: nothing. The change stores nothing on any device, collects nothing and
sends nothing to a third party. It is a local patch to a clone that is never pushed (`project.md`,
`Manages: none`). No KensaiApp presence surface states this fact, so the change has no blast radius
on another surface and no release step to keep.

---

## 2. Blast Radius

The product has no `docs/SDD.md`, so it has no § 3 parts table to place logic by. The change adds no
new piece of logic. It corrects a value at the one site that already owns it. The rows below are
Django packages, because the product has no `nfdr.md § 1.2` module set.

| Module | Status | What changes |
|---|---|---|
| `django/db/models/` (`aggregates.py`) | Modified | `Aggregate.as_sql`: when `distinct=True`, the value supplied as the template's `distinct` key carries one trailing space. The non-distinct value stays empty. `Aggregate.template` is unchanged. |
| `django/contrib/postgres/aggregates/` | Unchanged | No code edit. `ArrayAgg` and `StringAgg` inherit `Aggregate.as_sql` (through `OrderableAggMixin.as_sql` → `super()`), so with `distinct=True` their rendered SQL also gains the single space after `DISTINCT`. This is the bounded allowance in the spec's Out of Scope, and nothing more. It is not proved here, because `psycopg2` cannot be imported in this environment. |
| `django/contrib/gis/db/models/` (`aggregates.py`) | Unchanged | `GeoAggregate` does not set `allow_distinct`, so the distinct path cannot be reached. |
| `django/db/backends/` | Unchanged | Nothing reads the `distinct` key. `supports_aggregate_filter_clause` and SQLite's `check_expression_support` are untouched. |
| `tests/aggregation/` (`tests.py`) | Modified | New tests in `AggregateTestCase` (§5). |
| `docs/` | Unchanged | The spec asks for no documentation change. The stale `Aggregate.template` default at `docs/ref/models/expressions.txt` line 378 is the spec's found defect, for the PM to carry. |

No public interface changes. The `Aggregate`/`Count` signatures, `template`, `allow_distinct` and the
`distinct` attribute stay as they are. Only the text bound to an internal template key changes, so
no importing module is transitively affected beyond the inheritance reach in the PostgreSQL row.

---

## 3. Sub-jobs

Omitted. One product module changes (`django/db/models/`), at one site. The tests in
`tests/aggregation/` prove that change and are not a second product module. There is no ordering
edge between them beyond red-then-green, and sequencing that is not this artifact's to decide.

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| `django/db/models/aggregates.py` — `Aggregate.as_sql` distinct separator | The seam is the value bound to the `distinct` key at the top of `as_sql`, not `Aggregate.template`. A space added to the template would reach every non-distinct aggregate (breaking CP-10) and would leave subclasses with their own templates unfixed. The value is bound once, before the three branches, and all of them reuse it, so the `CASE WHEN` fallback (CP-12) needs no edit of its own. |

---

## 5. Test Additions

All rows go in `tests/aggregation/tests.py`, class `AggregateTestCase`. Its existing
`setUpTestData` is the spec's Examples data: nine authors, three of them aged 30 or under, holding
two distinct ages. No new fixture is needed. Rendered-SQL rows assert that the aggregate's own
fragment is *contained* in `str(queryset.query)` from an `.annotate()` queryset. They do not compare
the whole statement, so the column list and `GROUP BY` rendering, which are out of scope, stay
uncoupled. Rows marked **red** fail on the unchanged tree and pass with the change. Rows marked
**fence** pass on both, because they pin what must not move.

| # | Rule | Test file | What to add / modify |
|---|---|---|---|
| 1 | CP-9 | `tests/aggregation/tests.py` | **red** — rendered SQL of `Author.objects.annotate(n=Count(Case(When(age__lte=30, then='age')), distinct=True))` contains `COUNT(DISTINCT CASE WHEN`. |
| 2 | CP-9 | `tests/aggregation/tests.py` | **red** — rendered SQL of `annotate(n=Count('age', distinct=True))` contains `COUNT(DISTINCT "aggregation_author"."age")`. |
| 3 | CP-10 | `tests/aggregation/tests.py` | **fence** — rendered SQL of `annotate(n=Count('age'))` contains `COUNT("aggregation_author"."age")`, and that of `annotate(n=Count(Case(When(age__lte=30, then='age'))))` contains `COUNT(CASE WHEN`. |
| 4 | CP-11 | `tests/aggregation/tests.py` | **red** — the issue's case: `Author.objects.aggregate(n=Count(Case(When(age__lte=30, then='age')), distinct=True))` == `{'n': 2}`. In the same test, the same aggregate without `distinct=True` == `{'n': 3}`, so the test cannot pass if `DISTINCT` is dropped (CP-15's second bullet). |
| 5 | CP-11 | `tests/aggregation/tests.py` | **red** — a `Case` with a `default`: `aggregate(n=Count(Case(When(age__lte=30, then=Value(1)), default=Value(0), output_field=IntegerField()), distinct=True))` == `{'n': 2}`. |
| 6 | CP-11 | `tests/aggregation/tests.py` | **red** — the per-group form: `Author.objects.annotate(n=Count(Case(When(age__lte=30, then='age')), distinct=True))`. `n` is 1 for the three authors aged 30 or under (`a4`, `a6`, `a7`) and 0 for the other six. Assert the whole name→`n` mapping, so row order does not matter. |
| 7 | CP-12 | `tests/aggregation/tests.py` | **red** — `aggregate(n=Count('age', distinct=True, filter=Q(age__lte=30)))` == `{'n': 2}`. On SQLite this goes through the `CASE WHEN` fallback. Needs `Q` added to the module's imports, along with `Case` and `When` (and `Aggregate` for row 9). |
| 8 | CP-13 | `tests/aggregation/tests.py` | **fence** — `aggregate(n=Count('age', distinct=True))` == `{'n': 8}`. The existing `test_count` covers `rating`, not this Example. |
| 9 | CP-14 | `tests/aggregation/tests.py` | **red** — a subclass of `Aggregate` defined in the test, with `function = 'COUNT'`, `allow_distinct = True` and no `template`. `aggregate(n=<it>(Case(When(age__lte=30, then='age')), distinct=True))` == `{'n': 2}`, and the rendered SQL of the same expression in `.annotate()` contains `COUNT(DISTINCT CASE WHEN`. |

**Every Example is mapped.** CP-9 → rows 1–2. CP-10 → row 3. The four CP-11 Examples → rows 4
(the issue's case together with its non-distinct twin), 5 and 6. CP-12 → row 7. CP-13 → row 8.
CP-14 → row 9. CP-15 (fails on base, passes with the change) → the **red** rows 1, 2, 4, 5, 6, 7 and
9. CP-16 is the card's `Test command:` itself, run over `aggregation` with the change. It is a gate,
not a row.

**Rule-implied edges.** CP-11's "with or without a `default`" → rows 4 and 6 (no default) and row 5
(default). CP-11's "for `.aggregate()` and for `.annotate()`" → rows 4 and 6. CP-11's "distinct
non-NULL values": the `ELSE NULL` rows of row 6 count to 0, and NULL is not counted in row 4 (2,
not 3 with NULL). CP-12 "on a backend that has no `FILTER` clause" → row 7 on SQLite, which is the
only backend the gate runs (spec Gap 6). Non-distinct `filter=` rendering is left as it is by
construction (§4) and fenced by the existing `test_filter_argument.py` suite.

**What the change stops proving:** nothing. No existing test asserts rendered SQL containing an
aggregate's `DISTINCT` (spec, Verified Claims), so no assertion is retired.

---

## Records this change makes false

None. Read `$PROJECT_DOCS` (the product's `docs/`): it holds no `adr/`, `nfdr.md`, `fdr.md` or
`SDD.md`, so nothing in them goes false, and the gate sweep found no entry delegating a review to
`development-design`. The stale default at `docs/ref/models/expressions.txt` line 378 is product
documentation, not a decision record. It is already false today, and the spec carries it as a found
defect for the PM.

---

## Architect Review Notes

- **(b) Where the separator lives:** in the `distinct` context value in `Aggregate.as_sql`, not in
  `Aggregate.template`. This realizes CP-9 and CP-10 together by construction: the space exists if
  and only if `distinct=True`. A template change would be met by CP-10 only if the non-distinct
  value also changed to compensate, and the documented `template` attribute would move with it. It
  also realizes CP-14 for every `allow_distinct` subclass, whatever its template, rather than only
  for those on the default.
- **(b) What that placement reaches beyond the spec's proof:** the PostgreSQL `ArrayAgg` and
  `StringAgg` gain the same single space through inheritance. This takes up the spec's Out of Scope
  allowance ("the same single space after `DISTINCT`, and nothing else"), with no edit to
  `contrib/postgres`. A user subclass whose own template already writes a space after
  `%(distinct)s` will now render two spaces. That is still valid SQL, and the rendered text moves.
  No such template exists in the tree. It is named here because it is a reach of the change that no
  test pins.
- **(a) CP-15 "they fail on the unchanged tree" against CP-10 / CP-13:** a test that proves "renders
  exactly as today" or "returns the same value as today" passes on base by its nature. The design
  reads CP-15 as binding the change's tests together. The red property is carried by rows 1, 2, 4,
  5, 6, 7 and 9, and rows 3 and 8 are fences, marked as such in §5.
- **(b) Test placement:** every row goes in `tests/aggregation/tests.py` `AggregateTestCase`,
  including CP-12. The other file in the app, `test_filter_argument.py`, would be the conventional
  home for a `filter=` test, but its fixture (ages 40, 60, 100) has no repeated value, so a distinct
  count and a plain count cannot differ there. The spec's CP-12 Example (`{'n': 2}`) is stated on the
  nine-author data.
- **(d) No §3 though two trees change:** the skill decomposes when two or more modules are affected.
  Here the second tree is the change's own tests, not a product module, and the only edge between
  them is red-then-green.
