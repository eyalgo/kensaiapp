# 宿場 Shukuba — the formatting helpers leave the views

*Item 1 on the active 根回し Nemawashi `views-read-in-one-sitting`. Slug: `formatting-helpers-leave-the-views`.*

## What it is

`app/views.py` holds three private helpers — `_money`, `_date` and `_pad` — beside its two views.
Move them into a new private module, `app/_format.py`, and have the views import them from there.

## Reached when

- `grep -n "^def _" app/views.py` returns no line. It returns three today.
- `app/_format.py` defines `_money`, `_date` and `_pad` with the signatures they have today.
- `list_page` and `detail_page` keep their signatures, and `app/__init__.py` exports the same names.
- `pytest tests/` exits 0 with no test edited.

## Guardrail

- Every view's output is byte-identical before and after.
