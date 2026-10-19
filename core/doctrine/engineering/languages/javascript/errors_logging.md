---
version: "1.2.0"
---

# JavaScript — errors and logging

What the code does at a failure and at an event. How code is named and shaped the rest of the time is
`conventions.md`.

## The cut: a stopping condition is returned, a wiring bug is thrown

Both exist in this house and they are not alternatives.

- **An expected stopping condition is a return value.** `eval-fix.js` returns
  `{ halted: true, reason: 'missing-skill-or-workspace' }` (`.claude/workflows/eval-fix.js:232`) for a
  bad invocation, and returns the same shape of thing — a plain object the caller reads and decides
  on — for every other stop: `{ applied: false, escalate: …, rebuild_case, skill }` (`:243-248`),
  `{ applied: false, escalate: …, surfaced, declined, skill }` (`:264-271`) and
  `{ applied: false, clean: true, declined, skill }` (`:277`). Nothing unwinds.
- **A condition the run cannot grade is thrown.** Three `throw` sites exist in the repo
  (`grep -nHE '(^|[;{}[:space:]])throw new ' $(git ls-files '*.js')`, 2026-09-18), all in
  `.claude/workflows/run-skill-evals.js`, and one of them — `:258` — says so in the message itself:
  "That is a wiring bug, not a run to grade."

The test is who can act on it. A stopping condition has a caller who knows what to do next, so it
travels as data. A wiring bug has none, so it travels as an exception and takes the process down.

## Raising

- **`throw new Error(<template literal>)`.** Never a string, never a plain object, never a
  non-`Error` value — a thrown non-`Error` carries no stack, and every `catch` downstream has to
  test for it.
- **No `Error` subclass, and none is needed until a caller branches on the type.** All three throws use
  a plain `Error` and open with the module's own name as a prefix:
  `` `run-skill-evals: case "${ev.name}" (${config}) has no staged prompt, …` ``
  (`.claude/workflows/run-skill-evals.js:296`) — what tells a reader which module raised it, in a
  runtime with no logger to stamp that on.
- **The message carries three things: what is wrong, why the run must not continue, and the one thing
  to fix.** `run-skill-evals.js:296` names the wrong state ("has no staged prompt, but this skill HAS a
  fixture tree"), the consequence ("Falling back to the authored prompt would point the run at the
  tracked fixtures, which is the failure staging exists to close") and the fix ("Check that
  `stage_fixtures.py` and the Setup agent agree on the case name"). A message that stops at the first
  is a message the reader has to re-derive the other two from. All three throws in the repo carry this
  shape.
- **Wrapping preserves the original: `throw new Error(message, { cause: err })`.** The vendor's own
  words for the option: "When catching and re-throwing an error with a more-specific or useful error
  message, this property can be used to pass the original error"
  (`https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Error/Error`),
  and it has been widely available across browsers since September 2021
  (`https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Error/cause`). No
  wrap exists in the repo today — nothing here catches — so this rule is the language's idiom rather
  than an observed house practice.

## Emitting

**Plain lines on one channel. There is no logger, no JSON output and no level API**, and no `console.*`
call exists anywhere: `grep -c 'console\.'` returned `0` for all eight tracked `.js` files on
2026-08-21. A workflow script emits through the `log()` function its runner injects; a test file emits
nothing, because the test runner owns that output.

**The level ladder is a literal marker at the head of the line.** Four levels, sorted by what the
reader has to do about them, all readable by scanning the first character of a transcript:

| Marker | Means | Example |
|---|---|---|
| `HALT` | the run stopped here | `.claude/workflows/eval-fix.js:229` |
| `⚠` | something did not come back and the run continues anyway | no file shows it today |
| `✓` | a step completed | no file shows it today |
| no marker | a fact recorded in passing | `.claude/workflows/run-skill-evals.js:185` |

`HALT` is the one level with a corpus behind it: fifteen lines across three scripts
(`grep -n "log(\`HALT\|log('HALT" .claude/workflows/*.js`, 2026-08-21) follow one shape — the
marker, where it stopped, an em dash, and the reason. The one `HALT` line left,
`eval-fix.js:229`, carries the marker, the em dash and the reason, and no stage name, because it stops
before any stage runs: `log('HALT — invoke with { skill: "<name>", workspace: "<abs path to
iteration-N>" }.')`. `⚠`
and `✓` are read off no line in either staying script (`grep -n "⚠\|✓" .claude/workflows/eval-fix.js
.claude/workflows/run-skill-evals.js` prints nothing, 2026-09-18) — the ladder past `HALT` is this
authoring run's reading of the shape, not a rule with a corpus behind every row the way `HALT` has
one.

**Not every stopping line carries `HALT`.** Three do not:
`.claude/workflows/eval-fix.js:242`, `:263` and `:276` each log a plain, unmarked line immediately
before the `return` that stops the run — "the fix-author returned verdict: rebuild. Stopping for the
owner.", "the fix-author surfaced … call(s) it will not settle. Stopping for the owner." and "the
fix-author authored no entry — the benchmark warranted no change." A reader scanning for `HALT`
alone misses all three.

**A `HALT` line is written beside the return that causes it, never instead of it.** `eval-fix.js`
logs and returns on the same condition at `:229-232`. The log is for the person watching; the return
is for the caller. Neither substitutes for the other.
