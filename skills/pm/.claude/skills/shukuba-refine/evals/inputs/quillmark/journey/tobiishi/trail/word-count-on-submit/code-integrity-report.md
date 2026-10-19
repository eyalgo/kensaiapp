# Code integrity report — word-count-on-submit

**Skill:** development-code-integrity · **Outcome:** clean pass (no bug found) · **Suite:** green

## What was reviewed

- `src/quillmark/manuscript/front_matter.py` — which sections are left out of the count.

## The intent it was checked against

- `tl_instruction.md` (the two tasks and their behaviours).
- `change_spec.md` (WC1–WC3).
- `docs/SRS.md` FR-2.

## Tests added

None — every behaviour already had a correct test.

## Tests fixed

None.

## The finding

No issues — the code matches its intent. One thing surfaced and not fixed, because it is not a code
defect: which sections count as front matter is stated only in the docstring of
`src/quillmark/manuscript/front_matter.py:1-9`. The SRS's FR-2 uses the term and never states the set.

## Language resolution

Python, from `project.md`'s `Test command:`; the Python packet was read with its testing concern file.
