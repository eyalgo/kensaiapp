# SRS — quillmark

**Status:** Settled · **Version:** 5

## Functional requirements

### FR-1 — Submission
A writer submits one manuscript file (.docx or .odt) with a title and a pen name.

### FR-2 — Word count
A manuscript's word count excludes its front matter. A count outside 40,000–120,000 words is refused,
and the refusal states the count.

### FR-3 — Format
A file that is not .docx or .odt is refused, and the refusal names the accepted formats.

### FR-4 — Editors' list
Editors see every accepted submission, newest first, with its title, pen name and word count.
