# 根回し Nemawashi seed — a writer's submission is accepted or refused at once

## What it is

A writer submits one file and learns at once whether it meets the press's rules; the editors see what
was accepted. Done: FR-1 to FR-4 hold end to end.

## Source

The SRS, FR-1 to FR-4 (`docs/SRS.md`), cut by the Principal PM.

## Stations — dynamic checklist

- [x] a-file-is-received — a writer uploads one file with a title and a pen name
- [x] format-is-checked — a file that is not .docx or .odt is refused, naming the formats
- [x] word-count-is-checked — a count outside the range is refused, stating the count
- [ ] refusals-name-the-rule — every refusal names the FR it applies
- [ ] editors-see-the-list — editors see accepted submissions, newest first
- [ ] submissions-survive-a-restart — an accepted submission is still listed after a restart
