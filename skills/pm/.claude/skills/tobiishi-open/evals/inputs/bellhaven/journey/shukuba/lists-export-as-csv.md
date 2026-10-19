# 宿場 Shukuba — a list exports as CSV

*Item 1 on the active 根回し Nemawashi `lists-leave-the-app`. Slug: `lists-export-as-csv`.*

## What it is

A user downloads a shopping list as a CSV file. There is no export today.

## Reached when

- `app/export.py` defines `export_csv(list_id: int) -> str`, returning a header row `item,quantity`
  and one line per item.
- `GET /lists/<id>/export.csv` returns 200 with `Content-Type: text/csv`.
- `pytest tests/` exits 0.

## Guardrail

- Every existing list page renders exactly as it does today.
