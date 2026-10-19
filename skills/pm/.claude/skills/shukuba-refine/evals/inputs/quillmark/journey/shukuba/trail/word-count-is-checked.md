# 宿場 Shukuba — a manuscript's word count is checked at submission

*Item 3 on the active 根回し Nemawashi `submissions-are-accepted`. Slug: `word-count-is-checked`.*

## What it is

A submitted manuscript's words are counted without its front matter, and a count outside
40,000–120,000 is refused with the count stated (FR-2). Walked as the change unit
`word-count-on-submit`.

## Reached when

- `pytest tests/` exits 0.
- `tests/test_word_count.py::test_front_matter_excluded` and `::test_out_of_range_states_count` pass.

## Guardrail

- Refusal wording beyond stating the count is `refusals-name-the-rule`'s.
- **Not here:** `editors-see-the-list`.
