---
version: "2.5.0"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

# Change Design — <title>

**Date:** YYYY-MM-DD
**Category:** <bug | refactor | nfdr>
**Behaviour:** preserving
**Publishes text:** no
<!-- A preserving change adds no words, so the line is always `no`. Moving existing text is placement, and placement is the Developer's. -->

---

## 1. Change Summary

<one paragraph: what relocates, which modules, why. Behaviour is unchanged — this is a pure structural relocation; no new behaviour, no public-surface change.>

---

## 2. Blast Radius

No transitive blast radius — public surfaces are unchanged, so no importing module is affected.

| Module | Status | What changes (file location only) |
|---|---|---|
| `pkg/<layer>/` | Modified (relocation only) | Implementation moves from `__init__.py` into named module(s); `__init__.py` becomes re-export-only |
| ... | ... | ... |

---

## 3. Layout Plan

The module layout the spec deferred. For each affected module: the named module(s) the implementation moves into, the symbol → module mapping (account for *every* implementation symbol, including underscore helpers and constants), and the exact `__init__.py` re-exports — identical to today's public surface.

> **Where, not how.** The mapping table is exactly `Symbol | Kind | Target module` — no internal-imports column, no stdlib-dependency annotations, no per-symbol import wiring. Imports travel with the moved code and are the developer's to write. Cross-layer import stability is stated once in prose in §1/§2, never per-symbol. Circular-import risk routes to the hint on that module's §4 row — never into this table.

Sub-jobs are independent: preserved public surfaces mean no module consumes another's new contract, so there is **no build sequence** — all relocations are parallel.

### `pkg/<layer>/`

- **New named module(s):** `<layer>/<name>.py` [, `<layer>/<name2>.py`]
- **Symbol → module:**

  | Symbol | Kind | Target module |
  |---|---|---|
  | `<ClassName>` | class | `<layer>/<name>.py` |
  | `<func_name>` | function | `<layer>/<name>.py` |
  | `_<helper>` | private helper | `<layer>/<name>.py` |
  | `_<CONST>` | constant | `<layer>/<name>.py` |

- **`<layer>/__init__.py` re-exports:** `<Symbol1>, <Symbol2>, ...` — unchanged public surface, nothing added or removed.

### `pkg/<layer2>/`

<repeat per affected module>

---

## 4. Code Strategy

| Module | Hint |
|---|---|
| `<layer>/` | None — mechanical move + re-export |
| ... | ... |

(A pure relocation is mechanical, so the row almost always reads `None`. A hint applies only where a move is non-obvious — e.g. a circular-import risk introduced by the re-export — and it is then the move mapping, never task ordering. There is no `Complexity` column: retired 2026-09-09, the owner's call.)

---

## 5. Test Continuity

No new-behaviour tests — this change introduces none. The existing suite is the characterization contract and passes unchanged (TDD-under-green: baseline green → relocate → green). Where the change repairs a standard an existing test already enforces, that test is red at baseline; name it here and in `change_spec.md`, and it must be green after.

| Affected public surface | Existing coverage | Characterization test to add? |
|---|---|---|
| `from <pkg>.<layer> import <Symbol>` | covered by `tests/<...>` | No |
| ... | ... | ... |

(Add a characterization test **only** where a touched public surface is currently uncovered — it tightens the regression fence without changing behaviour. If the suite already covers the surface: "No test additions — the existing suite is the characterization contract." Never add a test for new behaviour.)

---

## Records this change makes false

<!-- Always present. Every sentence in a product record — `adr/`, `nfdr.md`, `fdr.md`, `SDD.md` § 3 under the product's docs/ — that goes false when this change lands; a relocation that adds a module `nfdr.md § 1.2` does not list is the usual one. This skill never edits a record; development-plan carries each line into its "Owed outside this change's reach" correction. The zero form names what was read. -->

- `<record>` — <what this change makes false> → <what it should say once this change has landed>.

(or: `None — read <records>; nothing in them goes false.`)

---

## Architect Review Notes

<!-- The divergence record. A preserving relocation deciding the layout the spec deferred is the EXPECTED handoff, not a divergence — do not log it. Log only a genuine departure from the spec (each with its reason): a resolved spec contradiction — never one with the `Behaviour` label: a changed importable symbol or signature is a STOP for reclassification, not a note — or an upstream recommendation overridden, or a departure from this skill's own stated shape for a Layout Plan. Usually omitted entirely for a clean relocation. -->

- **<label>:** <decision> — <reason>
