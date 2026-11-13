# Flow Findings — development-design  (audited 2026-11-13)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Lenses 1 (coverage), 3 (classification, copied verbatim: `nfdr` / `preserving`), 5, 6 and 8 walked against `change_spec.md` I-1 to I-11 and `docs/nfdr.md` QC-64. All 46 stand-ins (44 `save` definitions plus the two `OnlySaves` subclasses) are mapped to a fake configuration, in 20 modules. Lenses 2, 7, 9 and 10 do not apply to this step.

- **[non-blocking · change-local · divergence-record]** The two `HeldSaver` rows with a `holding` switch, which holds every save once switched on, are replaced by a fake that holds one numbered call. The table's reason, "once `release` is set, no later save waits", holds only because the tracker serializes saves (the one-action-at-a-time rule). No Architect Review Note states that dependency, so the narrowing rests on an invariant the record never names. Where: `change_design.md §3` (Stand-in → fake configuration, `HeldSaver` with a `holding` switch ×2) against `§Architect Review Notes`. Add a note naming the serialization the equivalence depends on, or the held-call rule that does not.
- **[non-blocking · change-local · enacted-constraint]** The design prescribes where the Developer records the I-5 mutation ("the change's Developer Review Notes") and says `tests/fakes.py` "lands first in practice". The first decides a downstream role's record. The second is a sequencing property that development-plan owns. State the property, which is that the suite and the 20 modules import the fake, and leave the record and the order to those owners. Where: `change_design.md §5` (I-5, the recorded mutation) and `§3` (last paragraph).

_No other flow-issues found._
