# Self-answer report — `adr/` and `nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-29
- **Sources re-read:** None. The one answer rests on files in this repository: the NFDR, the
  product's tree and the Developer skill.

## Items worked

### 2.1 — QC-39 was rewritten by a delivery-tier commit, with no Review Note and no new version

- **Bucket:** 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** RN-57 is the right record, and its facts hold. It also needs to say why the edit happened,
  because the cause is still there.
  1. *Whose it is.* The change lands in `nfdr.md` RN-57, which is this seat's. It records who
     changed a constraint and who checked it, and binds no person or outside party. Whether a
     delivery change may edit a definition document is a rule about the machinery, not about this
     product. The answer names that rule and doesn't decide it, so nothing here is the owner's call
     and nothing splits.
  2. *Is the draft sound?* Yes, for the reason it gives. The constraint set changes only under
     provenance. Version 19's header and RN-54 said QC-39 starts unmet, and the entry now says it is
     met with no note between them. No fact in the entry is false, so a note closes the gap and the
     words stay. The draft leaves one thing out: why a delivery run edited this document. The
     Developer's commit `79a743286` gives the reason, and that reason is a rule in
     `development-implementation`. Its `SKILL.md:131` says a product record under `docs/` is a
     record the change may not edit. Then it says a correction line "naming a file tracked on this
     branch is mislabelled, and the label does not bind you". tracker17's `docs/` is tracked in the
     same repository, so the second sentence wins. The code-integrity report on that change kept
     the edit and named the same contradiction for the owner. A note that records the edit without
     its cause reads as a one-off, and it isn't.
  3. *Settled record.* I re-read what RN-57 relies on, in the main checkout, without running
     anything. `uv.lock` sits beside `pyproject.toml`. `tests/architecture/test_pins.py:44` holds
     `test_uv_lock_fixes_every_declared_dependency_at_its_declared_version`, which fails when
     `uv.lock` is missing and on a declared dependency the lock doesn't fix at its pin.
     `test_every_declared_dependency_is_pinned_exactly` covers the `==` half of QC-39's layer-6
     check. Since `1bfb63f7f`, where RN-57 measured, only `docs/` has changed under the product, so
     its clone run still describes the tree. Nothing else in the SDD, the SRS, the ADRs or
     `what_left.md` still says QC-39 starts unmet. ADR-0013 binds QC-39 and is unchanged.
  4. *Failure paths.* **Stale:** "is met" is a state claim inside an obligation. If `uv.lock` goes
     missing or drifts, the layer-6 test and `uv lock --check` fail, so the claim can't silently go
     false. The tail's "686 passed" is the Developer's dated observation, and RN-57 already says it
     wasn't re-run. **Concurrent:** the next delivery change whose plan names a line in this
     document will edit it the same way. Nothing refuses that commit, and the next
     `product-architecture` run's diff of its inputs is the only thing that catches it. That is the
     addition, named instead of covered: the fix belongs to the skill, filed as
     `docs/findings/2026-10-29_the-developer-skill-puts-a-same-repo-product-record-in-reach.md` at
     the instance root, in its own commit `<a commit not in the public history>`. **Empty, absent, refused:** none apply to a
     provenance note.
  - *What would have tipped it.* If the owner had already ruled that a delivery change may correct
    a definition document in place, the "never patched in place" premise would fall. The verdict
    would then be "confirmed", with RN-57 citing that ruling. The Principal Architect's loader says
    the opposite, and I found no such ruling.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **`products/tracker17/docs/nfdr.md`** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
