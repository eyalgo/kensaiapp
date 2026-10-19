// Scoped test for eval-fix.js — the driver's entries/surfaced handling.
//
// A workflow script is not an importable module (top-level `await`, injected globals) and the runtime
// is sandboxed with no filesystem access, so this reads the workflow's OWN source and pins the
// branches that actually run — the same technique as run-skill-evals.test.js and
// run-skill-evals.test.js, and for the same reason: a standalone copy of the predicates would be a
// copy the workflow never executes.
//
// The failure mode these guard: the pass used to return before the fixer ran the moment
// `decision.surfaced` was non-empty, discarding every unrelated decided entry in the same pass and
// reporting the discard count as `entries_withheld`. `entries` and `surfaced` answer different
// findings (the author is told a surfaced finding is "never authored as an edit"), so withholding one
// for the other bought no safety — it only cost the safe work. After the fix, only an EMPTY entries
// set stops before the fixer; a non-empty entries set applies and returns the surfaced calls alongside
// it, so the owner's decision is never lost because other, unrelated work succeeded.
//
// Run: node --test .claude/workflows/tests/eval-fix.test.js

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const WORKFLOW = join(dirname(fileURLToPath(import.meta.url)), '..', 'eval-fix.js')
const src = await readFile(WORKFLOW, 'utf8')

// ------------------------------------------------------------------- entries apply alongside surfaced

test('the surfaced check runs only after entries is known, not before', () => {
  // The old defect checked `surfaced.length` and returned before `entries` was even read — an
  // unconditional all-or-nothing stop. Proving the first `surfaced.length` check now comes AFTER
  // entries is known is what proves entries can no longer be discarded on the strength of surfaced
  // alone: the driver must consult entries.length before any surfaced-only stop is possible.
  const entriesIdx = src.indexOf('const entries = decision?.entries')
  const firstSurfacedCheckIdx = src.indexOf('if (surfaced.length)')
  assert.ok(entriesIdx > -1, 'const entries = decision?.entries must still be declared')
  assert.ok(firstSurfacedCheckIdx > -1, 'a surfaced.length check must still exist')
  assert.ok(
    firstSurfacedCheckIdx > entriesIdx,
    'a surfaced check that runs before entries is known re-introduces the old all-or-nothing stop',
  )
})

test('a non-empty entries set reaches the apply phase regardless of surfaced', () => {
  // With entries present, the driver must fall through past the entries-empty gate to phase('apply') —
  // there must be no unconditional `if (surfaced.length)` return standing between them.
  const gateIdx = src.indexOf('if (!entries.length) {')
  const applyPhaseIdx = src.indexOf("phase('apply')")
  assert.ok(gateIdx > -1, 'the entries-empty gate must still exist')
  assert.ok(applyPhaseIdx > gateIdx, "phase('apply') must be reachable after the entries-empty gate")
})

// ------------------------------------------------------------------------ surfaced-only still escalates

test('an empty entries set with a surfaced call escalates before any fixer is spawned', () => {
  assert.match(
    src,
    /if \(!entries\.length\) \{[\s\S]{0,400}if \(surfaced\.length\) \{[\s\S]{0,400}escalate:[\s\S]{0,200}surfaced,/,
    'a surfaced call with empty entries must still escalate, nested inside the entries-empty gate',
  )
})

test('the clean pass (no entries, nothing surfaced) is untouched', () => {
  assert.match(
    src,
    /if \(!entries\.length\) \{[\s\S]{0,1200}clean: true/,
    'no entries and nothing surfaced must still return { clean: true }',
  )
})

// -------------------------------------------------------------------------- entries_withheld is gone

test('entries_withheld is gone', () => {
  assert.doesNotMatch(
    src,
    /entries_withheld/,
    'the field named the removed behaviour (discarding entries) and must not remain — it would report 0 forever',
  )
})

// ---------------------------------------------------------------- surfaced always rides in the result

test('the surfaced calls and the escalation marker are attached to the post-apply result too', () => {
  const applyPhaseIdx = src.indexOf("phase('apply')")
  const afterApply = src.slice(applyPhaseIdx)
  assert.match(
    afterApply,
    /if \(surfaced\.length\) \{[\s\S]{0,400}result\.escalate[\s\S]{0,150}result\.surfaced = surfaced/,
    'after a successful apply, a non-empty surfaced set must still attach escalate + surfaced to the returned result',
  )
})

// ------------------------------------------------------------------------------ untouched code paths

test('the rebuild verdict keeps its early return, before entries/surfaced are even read', () => {
  const rebuildIdx = src.indexOf("decision?.verdict === 'rebuild'")
  const entriesIdx = src.indexOf('const entries = decision?.entries')
  assert.ok(rebuildIdx > -1 && entriesIdx > -1)
  assert.ok(rebuildIdx < entriesIdx, 'the rebuild check must still short-circuit before entries is read')
  assert.match(
    src,
    /verdict === 'rebuild'[\s\S]{0,300}rebuild_case: decision\.rebuild_case \?\? null/,
    'the rebuild path must still return its rebuild_case and spawn no fixer',
  )
})

test("the fixer's prompt does not mention surfaced calls", () => {
  const match = src.match(/function applierPrompt\([^)]*\) \{[\s\S]*?\n\}/)
  assert.ok(match, 'applierPrompt function body not found')
  assert.doesNotMatch(
    match[0],
    /surfaced/,
    'the fixer must not be told about surfaced calls — re-deciding is its defining failure',
  )
})

test("the author's prompt is unchanged — a surfaced finding is still never authored as an edit", () => {
  assert.match(
    src,
    /goes in `surfaced` with[\s\S]{0,60}never authored as an edit/,
    'the rule that keeps entries and surfaced disjoint by instruction must still be stated to the author',
  )
})
