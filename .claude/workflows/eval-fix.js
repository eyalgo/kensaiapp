export const meta = {
  name: 'eval-fix',
  description: 'Act on a settled skill-evals benchmark with two hands: a fix-author that reads the benchmark and the failing runs\' own output, answers fix-or-rebuild, and writes the exact replacement text, and a fixer that applies it and commits. One pass, not a loop — the check that a fix worked is the next benchmark, which is its own round. A rebuild verdict, or a finding the author will not settle, stops for the owner.',
  phases: [
    { title: 'decide' },
    { title: 'apply' },
  ],
}

// Version: 1.0.0

// ── What this file owns ───────────────────────────────────────────────────────
// `<CORE>/doctrine/kaizen/skills.md` says a red eval is a finding and stops there; it names no
// mechanism for turning one into a fix. This file is that mechanism, and it borrows its shape rather
// than inventing one: the deciding and the applying are separate hands, for the reason
// `<CORE>/doctrine/kaizen/fix_packet.md` owns (the party that decides must not be the party that
// applies), with the handoff in memory rather than through a packet file, because this runs
// unattended.
//
// WHY ONE PASS AND NOT A LOOP. A cold read can afford to be re-run after every fix because a read
// is one agent over one file. Here the equivalent check is a fresh benchmark: ten executor agents, and
// product-srs iteration-12 measured 3.6M billed tokens for a single with-skill executor. Looping would
// spend a full round to learn whether the last fix took. So this pass fixes once and stops; the next
// benchmark is the verification, run deliberately, as its own round.
//
// WHY THE AUTHOR READS MORE THAN THE BENCHMARK. A grading verdict is a claim about a run. The run's own
// output — run_delta.json, product/, reference/ — is the evidence for it, and the two disagree often
// enough to matter: an assertion can fail because the skill is wrong, or because the assertion is. The
// author is pointed at both and told the difference is its first call.

// ── The author's decision. Fix-or-rebuild first (fix_packet.md § The verdict comes first). Unlike the
// cold-read loop there is no single "file under read" here — a benchmark implicates the skill, its
// evals.json, or the harness — so `target` is REQUIRED on every entry. An entry that cannot name its
// file is not an appliable edit. ──
const DECISION = {
  type: 'object',
  required: ['verdict'],
  properties: {
    verdict: { enum: ['fix', 'rebuild'] },
    entries: {
      type: 'array',
      items: {
        type: 'object',
        required: ['finding', 'target', 'anchor', 'replacement', 'replaces'],
        properties: {
          finding:     { type: 'string' },            // the failing case/assertion this answers
          target:      { type: 'string' },            // repo-relative path of the file this edits
          anchor:      { type: 'string' },            // the exact current text being replaced, unique in `target`
          replacement: { type: 'string' },            // the final text, verbatim, as it will read
          replaces:    { type: 'string' },            // what it deletes or supersedes; "nothing; this can only add" is a confession, not a blank
          class:       { enum: ['assertion', 'skill', 'harness'] },  // which of the three kinds this is
        },
      },
    },
    surfaced: {                                       // a contract-level call the author will not settle
      type: 'array',
      items: {
        type: 'object',
        required: ['finding', 'recommendation'],
        properties: { finding: { type: 'string' }, recommendation: { type: 'string' } },
      },
    },
    declined: {                                       // a failure judged not-a-defect, with its reason on the record
      type: 'array',
      items: {
        type: 'object',
        required: ['finding', 'why'],
        properties: { finding: { type: 'string' }, why: { type: 'string' } },
      },
    },
    rebuild_case: { type: ['string', 'null'] },
  },
}

// ── A fixer's application. Same shape as the cold-read loop's: the deciding is done, the fixer reports
// what landed, what stopped it, and the commit. ──
const APPLY = {
  type: 'object',
  required: ['applied'],
  properties: {
    applied: {
      type: 'array',
      items: { type: 'object', required: ['finding'], properties: { finding: { type: 'string' } } },
    },
    stopped: {
      type: ['object', 'null'],
      properties: { finding: { type: 'string' }, found: { type: 'string' } },
    },
    sha: { type: ['string', 'null'] },
  },
}

function authorPrompt(skill, root, workspace, previous) {
  return [
    `You are the fix-author for the skill \`${skill}\`, acting on a settled eval benchmark.`,
    '**Read `<CORE>/doctrine/kaizen/skills.md` § *A fix subtracts or trades* and § *The shape that',
    'cannot see an absence* first. They bind you, and this prompt does not restate them.**',
    '',
    '**You are in the eval-fix pass, not kaizen step 5.** Emit your decision as the structured return',
    'below — do NOT write or commit a `fix_packet.md` file. The fixer applies your decision and commits;',
    'the handoff here is in-memory. Everything the fix_packet doctrine says about *deciding* still binds',
    'you: the verdict, the subtract-or-trade rule, and surfacing what is not yours to settle.',
    '',
    `Repo root: ${root}. The round to act on:`,
    `  ${workspace}/benchmark.md   — the summary, with-skill against without-skill`,
    `  ${workspace}/benchmark.json — the same numbers, per case and per assertion`,
    previous ? `  ${previous}/benchmark.md    — the previous complete round, for comparison` : '  (no previous complete round to compare against)',
    '',
    '**Read the evidence, not only the verdict.** For every assertion that failed in either arm, open',
    `that run's own output under \`${workspace}/<case>/<arm>/outputs/\` — \`run_delta.json\` records the`,
    'created / modified / deleted product paths, `product/` holds what the run wrote and `reference/`',
    'the pristine version of anything it changed. A grading verdict is a claim; those files are the',
    'evidence for it. Establish what actually happened before deciding what it means.',
    '',
    '**Your first call on every failure is which of three things it is** — and they take different fixes:',
    '  - `assertion` — the assertion is wrong: it fails for a reason other than the behaviour it names,',
    '    or it passes for the wrong reason. The fix edits `evals/evals.json`.',
    '  - `skill` — the skill genuinely fails to do something it promises. The fix edits the skill\'s own',
    '    substance (its `SKILL.md`, or the authoring prompt its `stack.json` names).',
    '  - `harness` — the run measured the wrong thing (staging, fixtures, wiring). The fix edits that.',
    'Prefer the cheapest true reading, in that order: a wrong assertion is a far more common cause of a',
    'red eval than a wrong skill, and "fix the skill" is the expensive mistake if the assertion was the',
    'defect. But do not reach for `assertion` to avoid a real skill defect — that is how a skill rots',
    'while its benchmark stays green.',
    '',
    '**A clean benchmark is a real answer.** If nothing failed, or every failure is a genuine non-defect,',
    'return `verdict: "fix"` with no entries and your reasoning in `declined`. Do not invent a fix to',
    'have something to return.',
    '',
    '**Decide, in order:**',
    '- **Fix or rebuild — the verdict comes first.** If the right move is to stop patching and rebuild',
    '  the skill from its harvested principles (the conditions are in § *A fix subtracts or trades*),',
    '  return `verdict: "rebuild"` with the case in `rebuild_case` and NO entries. A rebuild is the',
    '  owner\'s to authorize: this pass stops and hands them the case.',
    '- **Otherwise `verdict: "fix"`.** For each failure you will fix, author one entry:',
    '  - `target` — the repo-relative path of the file the edit lands in. Required: this pass has no',
    '    default file, because a benchmark can implicate the skill, its evals, or the harness.',
    '  - `anchor` — the exact current text you are replacing, quoted long enough to be unique in',
    '    `target`. A line number is not an anchor.',
    '  - `replacement` — the final text, verbatim, as it will read. Not an instruction, not a summary of',
    '    intent. For `evals/evals.json` this means valid JSON in situ.',
    '  - `replaces` — the rule this removes or supersedes. **Subtract or trade.** If a fix genuinely only',
    '    adds, say so there in those words — it is itself a finding, never a field to leave blank.',
    '  - `class` — `assertion`, `skill` or `harness`, per your call above.',
    '- **Surface what is not yours to settle.** A failure that rests on a call the owner has not made —',
    '  a different done-signal, a different bucket set, a promised behaviour dropped, anything that',
    '  changes what the skill CONTRACTS to do rather than fixing a defect in it — goes in `surfaced` with',
    '  your recommendation, never authored as an edit. Any surfaced finding stops this pass for the owner.',
    '- **Decline a genuine non-defect** in `declined`, with your reason.',
    '',
    'Return ONLY: { verdict, entries: [{ finding, target, anchor, replacement, replaces, class }],',
    'surfaced: [{ finding, recommendation }], declined: [{ finding, why }], rebuild_case }. Author the',
    'text, not a description of the edit. You do not touch any file and you do not commit.',
  ].join('\n')
}

function applierPrompt(skill, root, entries, workspace) {
  const addFiles = [...new Set(entries.map(e => e.target).filter(Boolean))]
  return [
    `You are the fixer for the skill \`${skill}\`, applying a decided eval fix.`,
    '**Read `<CORE>/doctrine/kaizen/skills.md` § *A fix subtracts or trades* first. It binds the shape of',
    'what you apply, and this prompt does not restate it.**',
    '',
    '**The fix-author already decided.** These entries are authoritative — re-deciding is the failure,',
    'exactly as with an approved packet (`<CORE>/doctrine/kaizen/fix_packet.md`). You have an editor; you',
    'do not have a vote. Apply each entry: find its `anchor` in its `target` file and replace it with',
    '`replacement`, verbatim.',
    '',
    `Repo root: ${root}. The benchmark these answer: ${workspace}/benchmark.md`,
    '',
    'The decided entries, in order:',
    ...entries.map((e, i) => [
      `  ${i + 1}. Finding: ${e.finding}`,
      `     Class: ${e.class || 'unstated'}`,
      `     Target file: ${e.target}`,
      `     Replaces: ${e.replaces}`,
      `     Anchor (find this exact text):\n${indent(e.anchor, '       | ')}`,
      `     Replacement (write this exact text):\n${indent(e.replacement, '       | ')}`,
    ].join('\n')),
    '',
    '**If an anchor does not match its target file exactly, STOP — do not infer where the text was meant',
    'to go** (fix_packet.md § When the packet does not fit). Leave what already applied in place, report',
    'which entry stopped you and what you found in place of its anchor in `stopped`, and commit what',
    'landed. A wrong guess is the right words in the wrong passage, committed, with nobody to catch it.',
    '',
    '**If any entry edited a skill\'s own substance** (its `SKILL.md` or the authoring prompt its',
    '`stack.json` names), **bump that skill\'s version** — the `version:` under `metadata:` in its',
    'frontmatter, one minor step. Evidence is keyed by producing version, so a substance edit without a',
    'bump keys the next round to text that did not produce it. An edit that only touched `evals.json` or',
    'the harness changes no skill behaviour and takes no bump.',
    '',
    '**If any entry edited a JSON file, verify it still parses** before committing. A malformed',
    '`evals.json` fails the next round at its first step, long after this pass is gone.',
    '',
    '**Commit through the builder — never raw git.** One commit:',
    `  python3 <CORE>/tools/commit_builder.py --repo ${root} commit \\`,
    `    --subject "eval-fix(${skill}): <what this pass fixed>" \\`,
    '    --body "<what the benchmark showed, and how each fix subtracted or traded>" \\',
    '    --actor kaizen-fixer \\',
    `    --directional "<the directional trailer this instance uses>" \\`,
    '    --surface "Claude Code" \\',
    '    --co-authored-by "<your running model> <noreply@anthropic.com>" \\',
    `    --add ${addFiles.join(' ')}`,
    'Pass every path in ONE `--add` — the flag takes many paths, and repeating it keeps only the last,',
    'silently dropping the rest. The builder stages with `git -C` and writes the trailers;',
    '`commit_format.md` owns their meaning. You are the `kaizen-fixer` actor: pass `--actor kaizen-fixer`',
    'and the builder derives `Role:` from it — never state a `Role:` here. For `--co-authored-by` write',
    'your OWN running model as a display name, read from your runtime — never hardcode a model token',
    '(commit_format.md § Filling the model). Take nothing else about the trailers from this prompt.',
    '',
    'Return ONLY: { applied: [{ finding }], stopped, sha }.',
  ].join('\n')
}

function indent(text, prefix) {
  return String(text ?? '').split('\n').map(line => `${prefix}${line}`).join('\n')
}

// ── Driver ───────────────────────────────────────────────────────────────────
// The Workflow tool hands `args` to the script as a JSON string, not the object its docs promise.
const input = typeof args === 'string' ? JSON.parse(args) : (args ?? {})

const skill = (input?.skill || '').trim()
const workspace = (input?.workspace || '').trim()
const previous = (input?.previous || '').trim() || null
const root = input?.root || '.'

if (!skill || !workspace) {
  log('HALT — invoke with { skill: "<name>", workspace: "<abs path to iteration-N>" }.')
  log('The workspace must be a settled round: one that has a benchmark.md. An in-flight or aborted')
  log('iteration has no numbers to act on, and acting on half a round is worse than not acting.')
  return { halted: true, reason: 'missing-skill-or-workspace' }
}

phase('decide')
log(`${skill} — the fix-author reads ${workspace}/benchmark.md`)
const decision = await agent(authorPrompt(skill, root, workspace, previous), {
  agentType: 'kaizen-fix-author', schema: DECISION, phase: 'decide', label: `decide ${skill}`,
})

if (decision?.verdict === 'rebuild') {
  log('the fix-author returned verdict: rebuild. Stopping for the owner.')
  return {
    applied: false,
    escalate: 'fix-author verdict: rebuild — stop patching, rebuild from harvested principles (owner authorizes)',
    rebuild_case: decision.rebuild_case ?? null,
    skill,
  }
}

// `entries` and `surfaced` answer different findings (the author is told a surfaced finding is "never
// authored as an edit") — so a surfaced call no longer withholds every unrelated decided entry in the
// same pass. Only an EMPTY entries set stops before the fixer; when entries exist, the apply phase
// runs regardless, and the surfaced calls ride along in the result returned after it.
const surfaced = decision?.surfaced ?? []
const entries = decision?.entries ?? []

if (!entries.length) {
  // A contract-level call is the owner's. With nothing to apply, it stops the pass rather than
  // spawning a fixer with no work — and unlike the cold-read loop there is no next round here to
  // carry the rest, so stopping with the surfaced calls named is the whole answer.
  if (surfaced.length) {
    log(`the fix-author surfaced ${surfaced.length} call(s) it will not settle. Stopping for the owner.`)
    return {
      applied: false,
      escalate: 'fix-author surfaced a contract-level call — owner adjudication',
      surfaced,
      declined: decision?.declined ?? [],
      skill,
    }
  }

  // No entries and nothing surfaced is a real and good outcome here, unlike in the cold-read loop: a
  // benchmark with nothing wrong in it should produce no edit. Reported as a clean pass, not an escape
  // hatch.
  log('the fix-author authored no entry — the benchmark warranted no change.')
  return { applied: false, clean: true, declined: decision?.declined ?? [], skill }
}

phase('apply')
log(`${skill} — the fixer applies ${entries.length} decided entr(ies)`)
const apply = await agent(applierPrompt(skill, root, entries, workspace), {
  agentType: 'kaizen-fixer', schema: APPLY, phase: 'apply', label: `apply ${skill}`,
})

const applied = apply?.applied ?? []
log(`${applied.length} of ${entries.length} entr(ies) landed${apply?.sha ? ` — ${apply.sha}` : ''}`)
const result = {
  applied: applied.length > 0,
  entries: entries.length,
  landed: applied.length,
  stopped: apply?.stopped ?? null,
  declined: decision?.declined ?? [],
  sha: apply?.sha ?? null,
  skill,
}
if (surfaced.length) {
  // The owner's decision must not be lost because other, unrelated work succeeded — a caller reading
  // `applied: true` must still see that something needs them.
  log(`${surfaced.length} call(s) also surfaced this pass — returned alongside the applied entries.`)
  result.escalate = 'fix-author surfaced a contract-level call — owner adjudication'
  result.surfaced = surfaced
}
return result
