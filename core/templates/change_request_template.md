# Change request — <key>

*The PM-minted intake for one **飛び石 Tobiishi** — the single change the chain
(`core/launchers/chain-development/launcher.sh <project>` → `core/tools/chain_development.py`) carries
through the pipeline. Lives at `system/projects/<name>/journey/tobiishi/<key>/change_request.md` (`<key>` =
`<YYYY-MM-DD>_<slug>`). The PM writes this when opening the Tobiishi, through `tobiishi-open`; `development-specs`
reads it as the pipeline's first input — it does **not** coin the key or scan a queue. **No `Project:`
field** — the project is implied by which project's `journey/tobiishi/` this sits in.*

---

**Request:** <casual natural-language description of the change to make>
**Category:** <feature | bug | refactor | nfdr>   <!-- set by the PM; refactor only when Behaviour is preserving, feature only when it is changing -->
**Behaviour:** <preserving | changing>   <!-- set by the PM; changing if the FDR-level contract (the behaviours the suite pins, or for a product with no code what its documents state), any public name, or what one accepts or returns changes or is added to; touching nothing existing does not make a change preserving — and, for nfdr, if what an enforcement command reports changes: a check that gains a rule, a new check, or a new CI job is changing even where no product behaviour moves -->
**Classified because:** <the station or request line the two labels rest on>

---

> **PLACEHOLDER — the PM fills this when opening the Tobiishi.** One change = one `change_request.md`.
> The chain finds the single active `journey/tobiishi/<key>/` and carries it: spec → design → plan →
> content → implement → code-integrity → audit → seal (sealed to `journey/tobiishi/trail/` on merge).
