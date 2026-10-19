# Change Spec — A distinct aggregate over a conditional expression produces valid SQL

**Date:** 2026-10-11
**Category:** bug
**Behaviour:** changing
**Request:** "Fix the issue below in the product, the repository that the project card's
`Product path:` names (`django/django`). The repository stands at the commit before the issue was
fixed. Make the change the issue asks for, with tests of your own that show it, and leave the rest of
the product's behaviour as it is." The issue is `django__django-10880`, quoted in full in this
folder's `change_request.md` § *The issue*. Its constraints are that file's § *What must not be done*.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened, and every concern it routes was read

---

## Change Summary

An aggregate called with `distinct=True` renders `DISTINCT` directly against the SQL of the
expression it aggregates, with no space between them. When that SQL begins with a word, as a `Case`
does, the query is invalid. `Count(Case(When(...)), distinct=True)` renders
`COUNT(DISTINCTCASE WHEN ...)` and fails on SQLite with `near "WHEN": syntax error`. After this
change `DISTINCT` is separated from the aggregated expression by one space. Such queries run and
return the distinct count, and an aggregate without `distinct=True` renders exactly as it does today.

**Terms used below.** *Rendered SQL* is the text `str(queryset.query)` returns, which shows the SQL
Django generates for a queryset. A *distinct aggregate* is an aggregate expression constructed with
`distinct=True`. The *aggregated expression* is the expression passed to the aggregate as its first
positional argument: a field name, an `F()`, a `Case`, a `Value` and so on.

---

## Rules

### Rendering

- **CP-9:** In the rendered SQL of a distinct aggregate, the keyword `DISTINCT` is followed by
  exactly one space and then the aggregated expression's SQL. The issue's case renders as
  `COUNT(DISTINCT CASE WHEN <condition> THEN <value> ELSE NULL END)`, and a distinct count of a column
  renders as `COUNT(DISTINCT "<table>"."<column>")`. A present defect makes this a rule. Today
  `django/db/models/aggregates.py` line 71 supplies the bare word `DISTINCT` to the template at line
  17, `'%(function)s(%(distinct)s%(expressions)s)'`, which puts nothing between them. The rendered
  SQL today is `COUNT(DISTINCTCASE WHEN ...` and `COUNT(DISTINCT"<table>"."<column>")` (Verified
  Claims).
- **CP-10:** An aggregate *without* `distinct=True` renders exactly as it does today. No space or
  other character is added inside its parentheses. For example
  `Count('age')` still renders `COUNT("aggregation_author"."age")`, and `Count(Case(...))` still
  renders `COUNT(CASE WHEN ...)`.

### Query results

- **CP-11:** A query whose aggregate is `Count(<conditional expression>, distinct=True)` executes
  without a database error. It returns the number of distinct non-NULL values the conditional
  expression takes over the aggregated rows. This holds for `.aggregate()`, which gives one value
  for the whole queryset, and for `.annotate()`, which gives one value per group. A *conditional
  expression* here is a `Case` with one or more `When` clauses, with or without a `default`.
- **CP-12:** A distinct aggregate with a `filter=` argument executes without a database error on a
  backend that has no SQL `FILTER (WHERE ...)` clause, and SQLite is one. It returns the number of
  distinct non-NULL values of the aggregated expression among the rows the filter keeps. On such a
  backend the filter is rendered as a `CASE WHEN` inside the aggregate (Verified Claims), so today
  it fails the same way the issue's case does.
- **CP-13:** A distinct aggregate over a plain field, such as `Count('age', distinct=True)`, returns
  the same value as today. It works today, and CP-9 changes only its rendered text.

### Which aggregates

- **CP-14:** CP-9 to CP-12 hold for `django.db.models.Count`, the one aggregate in
  `django.db.models` that accepts `distinct=True`. They also hold for any user-defined subclass of
  `django.db.models.Aggregate` that sets `allow_distinct = True` and does not override `template`.
  Both attributes are public, documented API (`docs/ref/models/expressions.txt`, § *Aggregate()
  expressions*). The rules hold on every database backend. The proof (CP-15) runs on SQLite, which
  is the backend the card's `Test command:` uses.

### Proof

- **CP-15:** The change carries tests of its own that the card's `Test command:` runs. They fail on
  the unchanged tree and pass with the change. Together they cover at least:
  - `Count(Case(When(...)), distinct=True)` used in a query, asserting the returned **value** and
    not only that the query runs (CP-11);
  - a case where the distinct count and the plain count of the same conditional expression differ,
    so a test cannot pass if `distinct` is dropped (CP-11).
- **CP-16:** The card's `Test command:` exits 0 with the change, and no test fails. Today it runs 65
  tests with no failure (`change_request.md` § *What must not be done*), and so the baseline of known
  failures is empty.

---

## Examples

Data for the rows below: nine `Author` rows aged 34, 35, 45, 29, 37, 29, 25, 57 and 46. Three are
30 or under, and those three hold two distinct ages, 29 and 25. These are the `aggregation` test
app's models, on SQLite 3.46.0. "Today" is the result at `base_commit` on 2026-10-11 (Verified
Claims).

| Rule | Scenario | Today | Expected behavior |
|---|---|---|---|
| CP-9 | rendered SQL of `Author.objects.annotate(n=Count(Case(When(age__lte=30, then='age')), distinct=True))` | `COUNT(DISTINCTCASE WHEN "aggregation_author"."age" <= 30 THEN "aggregation_author"."age" ELSE NULL END)` | `COUNT(DISTINCT CASE WHEN "aggregation_author"."age" <= 30 THEN "aggregation_author"."age" ELSE NULL END)` |
| CP-9 | rendered SQL of `annotate(n=Count('age', distinct=True))` | `COUNT(DISTINCT"aggregation_author"."age")` | `COUNT(DISTINCT "aggregation_author"."age")` |
| CP-10 | rendered SQL of `annotate(n=Count('age'))` | `COUNT("aggregation_author"."age")` | unchanged |
| CP-10 | rendered SQL of `annotate(n=Count(Case(When(age__lte=30, then='age'))))` | `COUNT(CASE WHEN "aggregation_author"."age" <= 30 THEN "aggregation_author"."age" ELSE NULL END)` | unchanged |
| CP-11 | `Author.objects.aggregate(n=Count(Case(When(age__lte=30, then='age')), distinct=True))` (the issue's case) | `OperationalError: near "WHEN": syntax error` | `{'n': 2}` |
| CP-11 | the same without `distinct=True` | `{'n': 3}` | `{'n': 3}` (unchanged; shows distinct and plain differ) |
| CP-11 | `aggregate(n=Count(Case(When(age__lte=30, then=Value(1)), default=Value(0), output_field=IntegerField()), distinct=True))` | `OperationalError` | `{'n': 2}`, the distinct values being 1 and 0 |
| CP-11 | `Author.objects.annotate(n=Count(Case(When(age__lte=30, then='age')), distinct=True))`, one row per author | `OperationalError` | `n` is 1 for the three authors aged 30 or under and 0 for the other six |
| CP-12 | `aggregate(n=Count('age', distinct=True, filter=Q(age__lte=30)))` on SQLite | `OperationalError: near "WHEN": syntax error` | `{'n': 2}` |
| CP-13 | `aggregate(n=Count('age', distinct=True))` | `{'n': 8}` | `{'n': 8}` |
| CP-14 | a subclass `MyCount(Aggregate)` with `function = 'COUNT'`, `allow_distinct = True`, no `template`, used as `aggregate(n=MyCount(Case(When(age__lte=30, then='age')), distinct=True))` | `OperationalError`; renders `COUNT(DISTINCTCASE WHEN ...` | `{'n': 2}`; renders `COUNT(DISTINCT CASE WHEN ...` |
| CP-15 | the change's own tests, run on the unchanged tree | — | they fail |
| CP-15 | the change's own tests, run with the change | — | they pass |
| CP-16 | the card's `Test command:` run with the change | `Ran 65 tests`, `OK`, exit 0 | exit 0, no failing test |

---

## Verified Claims

All runs below were made on 2026-10-11 in disposable copies of the product, at commit `838e432e`
(the product's change worktree for this key, unchanged). Each copy was made with `git archive` and
extracted under `/tmp`. They used the card's interpreter, `/home/kensai/issue-venv/bin/python`
(Python 3.8.20), and SQLite 3.46.0, through `tests/runtests.py` with its default SQLite settings,
the same settings the card's `Test command:` runs under. A scratch test module was placed in the
copy's `tests/aggregation/` and never in the product's worktree. Nothing outside the repository was
consulted: no upstream history, no pull request and no benchmark copy.

| Claim | Verified by | What came back |
|---|---|---|
| Today a distinct `Count` over a `Case` fails, in `.aggregate()` and in `.annotate()` (CP-11) | ran each CP-11 query from the Examples in the base copy | each raised `OperationalError: near "WHEN": syntax error` |
| Today the rendered SQL has no space after `DISTINCT` (CP-9) | printed `str(qs.query)` for each CP-9/CP-10 row in the base copy | `COUNT(DISTINCTCASE WHEN ...` and `COUNT(DISTINCT"aggregation_author"."age")`; the non-distinct rows read as in the *Today* column |
| The defect site is `django/db/models/aggregates.py` lines 17 and 71 (CP-9) | read the file | line 17: `template = '%(function)s(%(distinct)s%(expressions)s)'`; line 71: `extra_context['distinct'] = 'DISTINCT' if self.distinct else ''` |
| Today `filter=` with `distinct=True` fails on SQLite the same way (CP-12) | ran the CP-12 query in the base copy; read `supports_aggregate_filter_clause` in `django/db/backends/*/features.py` and `Aggregate.as_sql` lines 73–86 | `OperationalError: near "WHEN": syntax error`; rendered `COUNT(DISTINCTCASE WHEN ...`. The flag is `False` in `base/features.py` line 236 and `True` only in `postgresql/features.py` line 54, so on SQLite the filter is rendered as a `CASE WHEN` |
| `Count('age', distinct=True)` works today and returns 8 (CP-13) | ran it in the base copy | `{'n': 8}` |
| A user subclass with `allow_distinct = True` and the default template fails today (CP-14) | ran the CP-14 row in the base copy | `OperationalError`; rendered `COUNT(DISTINCTCASE WHEN ...` |
| `Count` is the only aggregate in `django.db.models` that accepts `distinct=True` (CP-14) | `grep -n allow_distinct django/db/models/aggregates.py` | `allow_distinct = False` on `Aggregate` (line 22) and `allow_distinct = True` only on `Count` (line 108) |
| `allow_distinct` and `template` are documented public API (CP-14) | read `docs/ref/models/expressions.txt` lines 370–431 | both are documented attributes of `Aggregate` |
| The rules can all be met together, without moving any other test verdict | a probe copy that differed from base only by putting one space after `DISTINCT` (`aggregates.py` line 71). This shows the rules are compatible and is not a design. Ran the scratch probe there, then the card's `Test command:` from that copy's root, then `tests/runtests.py aggregation_regress expressions expressions_case annotations db_functions queries` in both copies | every *Expected behavior* row of the Examples matched, including CP-10's unchanged renderings. Card command: `Ran 65 tests`, `OK`, exit 0, in both copies. The six neighbouring suites: `Ran 945 tests`, `OK (skipped=26, expected failures=2)`, the same in both copies |
| The card's `Test command:` passes at base with no failing test (CP-16) | ran `/home/kensai/issue-test.sh` from the base copy's root, with the scratch module removed | `Ran 65 tests`, `OK`, exit 0; `/home/kensai/issue-baseline.txt` is empty |
| No test in the tree asserts rendered SQL containing `DISTINCT` against an aggregate | `grep -rn DISTINCT tests --include=*.py` | two matches, both message strings about other features (`tests/backends/sqlite/tests.py` line 43, `tests/backends/base/test_operations.py` line 133) |
| The PostgreSQL aggregates cannot be loaded in this environment (Out of Scope) | `python -c "import django.contrib.postgres.aggregates"` with the card's interpreter | `ModuleNotFoundError: No module named 'psycopg2'` |

Language rendering: no rule pins output that renders a Python language-level fact. The SQL text,
the counts and the error are all produced by the product or the database, so no rendering row is
owed.

---

## Out of Scope

- **`ArrayAgg` and `StringAgg` in `django.contrib.postgres.aggregates`.** Both accept
  `distinct=True` and have the same defect. Their own templates (`general.py` lines 13 and 54) put
  `%(distinct)s` directly before `%(expressions)s`. They are not part of this change's proof:
  they run only on PostgreSQL, and this environment cannot even import them (Verified Claims). The
  change may give their rendered SQL the same single space after `DISTINCT`, and nothing else. It is
  not required to. This is a found defect, and the PM may carry it as its own change.
- **The stale default in the documentation.** `docs/ref/models/expressions.txt` line 378 gives
  `Aggregate.template`'s default as `'%(function)s( %(expressions)s )'`, while the code's default is
  `'%(function)s(%(distinct)s%(expressions)s)'` (line 17). The request asks for no documentation
  change, and this one is a found defect for the PM to carry. Release notes and topic guides were not
  looked at.
- **Every other rendering.** `FILTER (WHERE ...)` on PostgreSQL, the shape of `CASE WHEN` itself,
  `GROUP BY`, and how other expressions render are not changed.
- **Other aggregates' acceptance of `distinct`.** Which aggregates allow `distinct=True` does not
  change: `Sum`, `Avg`, `Max`, `Min` and the rest still raise `TypeError` when passed it.
- **Backend-specific restrictions.** For example SQLite still refuses a distinct aggregate over more
  than one expression (`tests/backends/sqlite/tests.py` line 43).
- **Anything outside the local clone.** The patch is not pushed (`project.md`, `Manages: none`), and
  nothing is published. Per the request, no record, grade or benchmark file is produced. No public
  surface of KensaiApp states this fact, and none is touched.

---

## Locked Answers (the divergence record — self-review 2026-10-11)

- **Gap 1: a distinct count over a plain column also gains the space (CP-9, CP-13).** The issue
  names only the `Case` case. A rule that left `COUNT(DISTINCT"t"."c")` as it is would need the
  rendering to depend on what follows `DISTINCT`, and the request asks for no such distinction.
  `DISTINCT` followed by one space is one uniform output, and it is valid SQL for every aggregated
  expression. The result for a plain column does not change (CP-13). The neighbouring suites
  showed that no test checks the old text (Verified Claims). The change is reversible, because it
  moves rendered text and no data.
- **Gap 2: the `filter=` fallback is in scope (CP-12).** The issue says "a Case condition", and the
  filter form on a backend without `FILTER` renders exactly that Case, so it fails the same way
  (Verified Claims). Leaving it out would keep one way to write the issue's query broken. It is the
  same capability, a distinct aggregate rendering valid SQL, so it does not make a second change.
- **Gap 3: non-distinct rendering is pinned as unchanged (CP-10).** The request says "leave the rest
  of the product's behaviour as it is". That rules out a fix that adds a space or other character to
  every aggregate's rendered SQL, so the spec states it as a rule a test can check.
- **Gap 4: which aggregates the rules cover, closed by domain (CP-14).** The issue names `Count`.
  The domain is "aggregates whose rendering goes through `Aggregate`'s documented default template
  with `allow_distinct` set". In `django.db.models` that is `Count` alone, and user subclasses join
  it through public API. The PostgreSQL aggregates, which use their own templates, are named in Out
  of Scope with a bounded allowance, and not left undecided.
- **Gap 5: the proof asserts a value where distinct and plain differ (CP-15).** The request asks for
  "tests of your own" and does not say what they show. A test that only checks the query runs would
  still pass if the fix dropped `DISTINCT` altogether. Fixture data where the distinct count (2) and
  the plain count (3) differ closes that gap. Where the tests go and what data they use is
  development-design's decision. The property is all the spec fixes.
- **Gap 6: the backend for the proof is SQLite (CP-14, CP-16).** The issue says "whatever the db
  backend". The card's `Test command:` runs on SQLite only, so the rules are stated for every backend
  and proved on the one the gate runs.
