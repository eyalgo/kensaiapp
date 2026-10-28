# Change request — 2026-10-28_delete-a-task

---

**Request:** Let the operator delete a task from its page. Delete task on a task's page opens the in-place confirmation (the existing `confirm_strip`), and confirming removes the task together with its comments, then lands on the task's project with a line naming the deleted task (SDD § 6 S-7; UXD UX-F9, UX-S6). The deleted task is in no list of its project or of all projects, and its address shows the not-found page (UX-S10). A comment-add, edit or status move sent for it from another tab is refused through the existing refusal path and changes nothing in the saved data (AC-12). A deleted task's identity is never issued again (FR-15), so after deleting the task with the highest identity the next task added gets a new one, and its comments are gone from the saved data (FR-17). The timed run gains a task delete (NFDR QC-48). Tests: a layer-3 test per deleted-target refusal of AC-12 for a task, each asserting unchanged saved data, and a test that the identity is not reissued. The existing confirmation mechanism and refusal wording must not be duplicated or replaced. Renaming a project, deleting a project, the `domain/projects.py` / `domain/tasks.py` docstring bar, and moving a task to another project (SRS FR-14) are not part of this change, and existing pages and timed actions must keep working.

**Category:** feature
**Behaviour:** changing
**Classified because:** the station's reached-when adds a Delete task action, a deleted-task not-found address and deleted-target refusals to the FDR-level contract (SDD § 6 S-7, AC-12, FR-15, FR-17).

---

*Sizing: one capability — deleting a task — with its acceptance in the station's five reached-when items (confirmation and landing, not-found and refusals, identity and comments, suites, timed run); one flow, one merge. Source: SDD § 6 S-7, the station `2026-10-28_delete-a-task`, item 1 of 3 on seed `2026-10-11_delete-and-rename`. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present.*
