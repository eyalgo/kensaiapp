# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Sealed

`2026-10-28_rename-a-project` — the one change for station `2026-10-28_rename-a-project` (seed `2026-10-11_delete-and-rename`, item 2 of 3). Rename on a project's Tasks view, below the list, holding the current name; Save shows the new name as the page title and in the Projects list; a blank name or one another project uses is refused under UX-I3 through project creation's own validation (FR-10) with data unchanged; the project's own name is accepted; its tasks, identities, fields and comments are unchanged (FR-12); the timed run gains a project rename (QC-48). Sizing: one capability, one merge. Scope boundary: no project delete, no docstring bar, no description change (UXD § 10), no moving tasks (FR-14). FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `feature` / `changing`: adds a rename action and its refusals to the contract.
