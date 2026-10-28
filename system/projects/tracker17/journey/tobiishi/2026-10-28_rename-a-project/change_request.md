# Change request — 2026-10-28_rename-a-project

---

**Request:** Let the operator rename a project from its Tasks view. Below the project's list, a Rename field holds the project's current name; Save renames the project, and the operator sees the new name as the project's page title and in the Projects list, with the old name in neither (UXD UX-F10; SDD § 6 S-7). A blank name, or a name another project already uses, is refused under UX-I3 through the same refusal path and naming rules project creation uses (FR-10), and the saved data is unchanged; saving the project's own current name is accepted (FR-12). Renaming leaves the project's tasks the same tasks, with the same identities, fields and comments (FR-12). The timed run gains a project rename (NFDR QC-48). Tests: one that a rename leaves the project's tasks unchanged, and a layer-3 test per refusal, each asserting unchanged saved data. The project-creation validation and refusal wording must not be duplicated or replaced by a second scheme. Deleting a project, the `domain/projects.py` / `domain/tasks.py` docstring bar, changing a project's description (UXD § 10) and moving a task between projects (SRS FR-14) are not part of this change, and existing pages and timed actions must keep working.

**Category:** feature
**Behaviour:** changing
**Classified because:** the station's reached-when adds a Rename action on a project's Tasks view and its refusals to the FDR-level contract (SDD § 6 S-7, UXD UX-F10, SRS FR-12).

---

*Sizing: one capability — renaming a project — with its acceptance in the station's five reached-when items (new name shown, refusals and own-name acceptance, tasks unchanged, suites, timed run); one flow, one merge. Source: SDD § 6 S-7, the station `2026-10-28_rename-a-project`, item 2 of 3 on seed `2026-10-11_delete-and-rename`. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present.*
