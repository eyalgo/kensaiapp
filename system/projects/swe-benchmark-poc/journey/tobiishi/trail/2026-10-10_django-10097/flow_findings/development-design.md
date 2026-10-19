# Flow Findings — development-design  (audited 2026-10-10)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Audited: `change_design.md` against `change_spec.md` and the product tree at `base_commit`
(`django/core/validators.py`, `tests/validators/tests.py`). No `docs/adr/`, `nfdr.md`, `fdr.md` or
`SDD.md` exist (`Definition: none`), so those cross-checks were skipped and lens 9 does not apply.

Checked and held: Category/Behaviour copied verbatim (`bug` / `changing`); CP-5 by construction
(a failed regex match goes to the fallback path, whose `urlsplit` `ValueError` is already caught);
`TEST_DATA[156]`/`[157]` stay put because both fixture loaders run after the inline list; the line-51
ordering edge and the CP-8 placement are stated as properties, with no downstream role named; the
divergences (line 51 moved, CP-5 not wrapped, lone `[` surfaced and left to the owner) are recorded
with reasons.

- **[non-blocking · change-local · evidence]** The CP-7 coverage line says "the appended invalid rows, the suffixed loader entries and the new method each fail on the unchanged tree". For the suffixed entries that is false. The spec's own Examples row says 17 of the 59 `invalid_urls.txt` entries with the suffix are rejected today, so those generated tests already pass at base. Where: `change_design.md §5 Coverage map, CP-7`. Direction: say the suffixed set contains cases that fail today (the 41 accepted and the 1 `ValueError`), not that each one does. Left as written, a reader takes the 17 as proof of the change.
- **[non-blocking · change-local · coverage]** CP-3 names the lower-case encodings `%3a` and `%2f` as accepted. No design test row has `%3a` (the appended valid rows use `%2F`, `%3A`, `%40`; line 51 carries `%2f` but not `%3a`). Where: `change_design.md §5` rows for CP-3. Direction: one lower-case-encoded row would map the spec's stated edge. It is a fence only, since the character class is case-blind and passes today. Code-integrity's commit message says it later added a lower-case `%3a` case in the product (b7539b2), so the gap was closed downstream, not by the design.

_No blocking findings. No skill-general findings._
