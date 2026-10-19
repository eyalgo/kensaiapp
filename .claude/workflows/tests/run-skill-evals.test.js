// Scoped test for run-skill-evals.js — the structural/nuanced grading layer, the model pins, and the
// executor declaration.
//
// A workflow script is not an importable module (top-level `await`, injected globals) and the runtime is
// sandboxed with no filesystem access, so this reads the workflow's OWN source and pins the branches
// that actually run — the same technique as eval-fix.test.js, and for the same reason: a
// standalone copy of the predicates would be a copy the workflow never executes.
//
// The failure modes these guard:
//   - a collapsed tier split — the structural/nuanced layer is the point of the instrument: cheap
//     token-presence checks graded cheaply, judgment graded by a senior model. Levelling every grader
//     to one model erases the distinction and the reason the tiers exist. These tests fail if the
//     branch disappears, if structural assertions stop reaching the structural grader, or if the two
//     tiers collapse onto the same model.
//   - a silently overwritten iteration — next_iteration derived from the COUNT of existing dirs rather
//     than the highest number, which returns an occupied number as soon as the sequence has a gap.
//     workspace/ is gitignored, so an overwrite is unrecoverable.
//   - an unrecorded model — a run that cannot say what it measured on cannot be compared to another
//     run, which is what made iterations 1–6 incomparable.
//   - a mandatory executor block — putting `executor` in the schema's `required` would break every
//     other skill's evals.json, none of which declares one.
//   - an unloadable workflow — a `meta` that isn't a pure literal, which the validator rejects before
//     any agent runs.
//
// Run: node --test .claude/workflows/tests/run-skill-evals.test.js

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const WORKFLOW = join(dirname(fileURLToPath(import.meta.url)), '..', 'run-skill-evals.js')
const src = await readFile(WORKFLOW, 'utf8')

// --------------------------------------------------------------------- the structural/nuanced layer

test('the tier branch still selects the grading topology', () => {
  // One tier present → that tier grades straight to grading.json. Both present → structural + nuanced
  // in parallel, then a merge. Lose this branch and every eval pays for a grader it does not use.
  // Pinned on the two named booleans rather than on the inline comparisons they replaced: d242740a
  // renamed those and this assertion went red for 53 minutes on 2026-08-21 (14:18 to 15:11) without
  // failing anything real. An earlier case was longer: f755016d (2026-08-03) left this same file
  // red until 2026-08-20. Same shape twice.
  assert.match(src, /const hasStructural = item\.structural\.length > 0/,
    'the structural tier must still be selected by the presence of structural assertions')
  assert.match(src, /const hasNuanced = item\.nuanced\.length > 0/,
    'the nuanced tier must still be selected by the presence of nuanced assertions')
  assert.match(src, /if \(!hasNuanced\)/,
    'the structural-only fast path must still be selected by the absence of nuanced assertions')
  assert.match(src, /else if \(!hasStructural\)/,
    'the nuanced-only path must still be selected by the absence of structural assertions')
})

test('neither tier is ever spawned with an empty expectation list', () => {
  // The guard d242740a added, and the half nothing covered. A grader handed no expectations does not
  // return an empty set — it invents its own and grades against them, so the totals inflate and the
  // two arms are scored against different fabricated bars (companion-answer iteration 2: a
  // zero-structural case returned 6 and 4 against three declared assertions). Both directions must
  // stay guarded; only the nuanced-empty one existed before that commit.
  assert.match(src, /const nuancedTarget = hasStructural/,
    'the nuanced grader must still write straight to grading.json when it is the only tier')
  assert.match(src, /const targetFile = hasNuanced/,
    'the structural grader must still write straight to grading.json when it is the only tier')
})

test('the two tiers still write to different files before the merge', () => {
  // The split path grades into grading_structural.json and merges; the fast path writes grading.json
  // directly. aggregate_benchmark.py reads grading.json only, so collapsing these loses the nuanced half.
  assert.match(src, /grading_structural\.json/,
    'the split path must still stage the structural half separately')
  assert.match(src, /grading_nuanced\.json|grade-nuanced/,
    'the nuanced half must still exist as its own graded artifact')
})

test('structural and nuanced assertions each reach their own grader', () => {
  assert.match(src, /item\.structural\.map\(/,
    'structural assertion text must still be enumerated into the structural grader prompt')
  assert.match(src, /item\.nuanced\.map\(/,
    'nuanced assertion text must still be enumerated into the nuanced grader prompt')
})

test('the tiers are graded by DIFFERENT models — the split is not levelled', () => {
  // The documented split: README.md:35 and references/schemas.md:48 both specify Haiku for structural
  // and Sonnet for nuanced. Structural is the PREFERRED tier and is cheap because the check is
  // mechanical — levelling it up erases the reason to prefer it.
  assert.match(src, /GRADER_MODELS\s*=\s*\{[^}]*structural:\s*'haiku'/,
    'a structural check is one checkable transformation at volume — the cheap tier')
  assert.match(src, /GRADER_MODELS\s*=\s*\{[^}]*nuanced:\s*'sonnet'/,
    'a nuanced check applies a written criterion no pattern can approximate — the worker tier')

  const models = src.match(/const GRADER_MODELS = \{([^}]*)\}/)
  assert.ok(models, 'GRADER_MODELS must exist')
  const structural = models[1].match(/structural:\s*'(\w+)'/)[1]
  const nuanced = models[1].match(/nuanced:\s*'(\w+)'/)[1]
  assert.notEqual(structural, nuanced,
    'if both tiers run the same model the split has been levelled away and grades nothing differently')
})

test('every grader call site is pinned — none silently inherits the session model', () => {
  const graderCalls = src.match(/phase: 'Grade'[^}]*\}/g) ?? []
  assert.ok(graderCalls.length >= 4, `expected at least 4 grading agents, found ${graderCalls.length}`)
  for (const call of graderCalls) {
    assert.match(call, /model: GRADER_MODELS\.\w+/,
      `a grading agent with no model pin inherits the session model, making the run unreproducible: ${call}`)
  }
})

test('a staged prompt that names the wrong arm throws before any executor runs', () => {
  // product-prd iteration-7, measured. stage_fixtures.py was NOT at fault — its stage_manifest.json
  // recorded the correct path for every arm that round. The value changed in the relay: the script
  // prints one JSON object, an agent reads that stdout and hands it back, and that object feeds both
  // the executor prompt and eval_metadata.json. A workflow has no filesystem, so an agent is the only
  // way the data can travel, which makes the relay a place a field can silently change.
  //
  // Unchecked, the arm works in its sibling's tree, its own stays empty, it grades 0 for a reason
  // that has nothing to do with the skill, and ~30M executor tokens measure nothing.
  assert.match(src, /const siblingArm = configName === 'with_skill'/,
    'the guard must derive the sibling from the config being checked, not assume one')
  assert.match(src, /stagedPrompt\.includes\(siblingArm\) \|\| !stagedPrompt\.includes\(ownArm\)/,
    'both directions: naming the sibling is wrong, and failing to name its own arm is equally wrong')
  const guard = src.match(/does not name its own arm[\s\S]{0,400}/)
  assert.ok(guard, 'the throw must say which arm the prompt should have named')
  assert.match(guard[0], /stage_manifest\.json is the authority/,
    'the message must point at the file that settles it, or the next reader re-derives the diagnosis')
})

test('the own-arm check is skipped for a case whose authored prompt never named the fixture tree', () => {
  // product-srs iteration-14, measured: case "posture-halt-outside-cto" has no project path in its
  // authored prompt at all (it deliberately tests behavior OUTSIDE any project context). stage_fixtures.py's
  // rewrite_prompt() only replaces a substring match, so a prompt with nothing to match comes back
  // byte-identical for both arms — correctly, since there is nothing to rewrite. Without this
  // exemption the own-arm check above trips on every such case in ANY skill with a fixture tree,
  // aborting the whole round before an executor runs, for a "corruption" that never happened.
  assert.match(src, /authoredReferencesFixture/,
    'the check must gate on whether the AUTHORED prompt (not the staged one) named the fixture tree')
  assert.match(src, /if \(!authoredReferencesFixture\) continue/,
    'a case with no fixture reference in its authored prompt must skip the per-arm check entirely')
  // The exemption must sit strictly between the tracked-fixture-tree check and the own-arm check —
  // skipping too early would also skip the "still names the tracked fixture tree" guard.
  const order = src.match(/still names the tracked fixture tree[\s\S]*?if \(!authoredReferencesFixture\) continue[\s\S]*?does not name its own arm/)
  assert.ok(order, 'the exemption must run after the tracked-fixture-tree check and before the own-arm check')
})

// --------------------------------------------------------------------- the parallel-arm fence

test('the executor is fenced to its own staged tree, and told the siblings are live', () => {
  // The failure this answers, measured: in product-prd iteration-6 the without_skill executor for
  // tag-external-source-with-locator read the with_skill arm's binding and wrote its PRD there. Its
  // staged prompt named its own arm correctly — staging was not at fault. The prompt asserted the
  // tree was "private to this run" and never forbade touching a sibling, and all (case × arm) runs
  // execute in parallel against sibling directories under one workspace.
  //
  // arm_isolation.py detects a crossing AFTER a round has run, which costs ~30M executor tokens to
  // learn. This is the prevention half; neither substitutes for the other.
  assert.match(src, /belong to OTHER runs executing in parallel/,
    'the executor must be told the sibling directories are live runs, not spare scratch space')
  assert.match(src, /never read a binding or a fixture from one, and never write into one/,
    'a prohibition, not an assertion of privacy — "private to this run" is what failed')
  assert.match(src, /you resolved the wrong binding — stop and re-read/,
    'the executor needs a recovery instruction, or it improvises when a path looks wrong')
})

test('the fence is conditional on there being a staged tree to fence', () => {
  // A skill with no evals/inputs/ tree stages nothing, so naming a staged path at it would point the
  // run at a directory that does not exist. Same gating as the staged-prompt fallback above.
  const fence = src.match(/\$\{STAGED\.fixture_root \? `[\s\S]*?` : ''\}/)
  assert.ok(fence, 'the fence must be gated on STAGED.fixture_root, not emitted unconditionally')
  assert.match(fence[0], /staged tree/,
    'the gated block must be the fence itself, not some other conditional')
})

// --------------------------------------------------------------------- the utility (plumbing) layer

test('every utility agent is pinned — none inherits the session model', () => {
  // These five neither execute the skill nor grade it: they read a JSON, write strings the workflow has
  // already composed, or run a script and hand back its stdout. Unpinned, each takes the model of
  // whatever session drove the run — so a Fable-driven round silently put fourteen agents per run on the
  // top tier to call Write. The cost of a run must follow its work, not its launcher.
  //
  // Anchored past `phase:` rather than on the label for harvest: its label is a template literal, and
  // the `}` closing `${item.id}` ends a `[^}]*` slice before it can reach the model key.
  const sites = [
    /label: 'read-evals'[^}]*model:/,
    /label: 'write-metadata'[^}]*model:/,
    /label: 'stage-fixtures'[^}]*model:/,
    /label: 'write-staged-metadata'[^}]*model:/,
    /phase: 'Harvest'[^}]*model:/,
  ]
  for (const site of sites) {
    assert.match(src, site,
      `a utility agent matching ${site} carries no model pin — it inherits the session model`)
  }
})

test('the utility pins are the cheap tier, and read-evals is the one deliberate exception', () => {
  // model_assignment.md § Runs with no standing slot: "one checkable transformation at volume → the
  // cheap tier". read-evals buys the worker tier for one reason only — it computes next_iteration as
  // HIGHEST + 1, and workspace/ is gitignored, so an overwritten iteration cannot be recovered. Every
  // other utility call can simply be re-run. If that asymmetry ever disappears, the exception should go
  // with it rather than quietly become the norm.
  const models = src.match(/const UTILITY_MODELS = \{([^}]*)\}/)
  assert.ok(models, 'UTILITY_MODELS must exist')
  const plumbing = models[1].match(/plumbing:\s*'(\w+)'/)[1]
  const readEvals = models[1].match(/readEvals:\s*'(\w+)'/)[1]
  assert.equal(plumbing, 'haiku',
    'plumbing is one checkable transformation at volume — the cheap tier')
  assert.notEqual(readEvals, plumbing,
    'read-evals is pinned above plumbing because its arithmetic slip is unrecoverable; levelling them erases that reason')
})

test('UTILITY_MODELS is its own const — it does not ride on GRADER_MODELS', () => {
  // model_assignment.md scopes GRADER_MODELS to graders and justifies its tiers by the KIND of check.
  // Folding plumbing into it would put two unrelated policies behind one name, and the next reader
  // levelling the grader tiers would move the plumbing with them.
  const graders = src.match(/const GRADER_MODELS = \{([^}]*)\}/)
  assert.ok(graders, 'GRADER_MODELS must exist')
  assert.doesNotMatch(graders[1], /plumbing|readEvals/,
    'the utility pins must not live inside GRADER_MODELS — different policy, different const')
})

test('the run records the utility pins it asked for', () => {
  // Same reason the executor and grader pins are recorded: a run whose models are unknown cannot be
  // compared to another run. The plumbing is part of what a round cost, so it belongs in the manifest.
  const manifest = src.match(/const runManifest = \{[\s\S]*?\n\}/)
  assert.ok(manifest, 'the run manifest literal must exist')
  for (const field of ['utility_read_evals', 'utility_plumbing']) {
    assert.match(manifest[0], new RegExp(`${field}:`),
      `models_requested lost the field "${field}" — the round's plumbing cost becomes unattributable`)
  }
  assert.match(manifest[0], /schema_version: 2/,
    'adding fields to models_requested is a shape change; a reader must be able to tell an unpinned old run from an unrecorded one')
})

// --------------------------------------------------------------------- the executor declaration

test('the executor declaration is optional, and spread into the executor call', () => {
  assert.match(src, /executor:\s*\{\s*\n\s*type: 'object'/,
    'evals.json may declare the body its executor runs on')
  assert.match(src, /Object\.entries\(setup\.executor \|\| \{\}\)/,
    'a skill that declares nothing must keep the previous inherit-the-session behaviour')
  assert.match(src, /\.filter\(\(\[, value\]\) => value\)/,
    'an empty value must be DROPPED, not spread — a "" agentType reached the spawn and killed all ten runs of one iteration on 2026-08-03 (f755016d)')
  assert.match(src, /phase: 'Execute', \.\.\.EXECUTOR_OPTS/,
    'the declaration must actually reach the executor spawn')
})

test('executor is NOT required — other skills declare none', () => {
  const required = src.match(/required: \['skill_name'[^\]]*\]/)
  assert.ok(required, 'the top-level required list must exist')
  assert.doesNotMatch(required[0], /executor/,
    'requiring an executor block would break every evals.json that has none')
})

test('both arms get the same body, so the delta still isolates the skill', () => {
  // EXECUTOR_OPTS is spread once, outside the with/without branch. The only arm difference must remain
  // the skillPart ternary — otherwise the measured delta conflates the model with the skill.
  const spreads = src.match(/\.\.\.EXECUTOR_OPTS/g) ?? []
  assert.equal(spreads.length, 1, 'exactly one executor spawn, shared by both arms')
  assert.match(src, /item\.config === 'with_skill'\s*\n?\s*\?/,
    'the arm difference must remain the skill-reading ternary')
})

// --------------------------------------------------------------------- recording and numbering

test('the run records the models it asked for', () => {
  assert.match(src, /models_requested/, 'the manifest must name the pins the run used')
  assert.match(src, /run_manifest\.json/, 'the manifest must be written into the workspace')
  assert.match(src, /executor: EXECUTOR_OPTS\.model \|\| null/,
    'an absent pin is recorded as null, never guessed')
})

test('next_iteration is the highest number, never the count', () => {
  assert.match(src, /highest number found/,
    'counting returns an occupied number as soon as the sequence has a gap')
  assert.doesNotMatch(src, /next_iteration = count \+ 1/,
    'the count form overwrites an existing run archive, and workspace/ is gitignored')
})

test('meta is a pure literal so the workflow can register and load', () => {
  const meta = src.match(/export const meta = \{[\s\S]*?\n\}/)
  assert.ok(meta, 'meta must be a single object literal')
  assert.doesNotMatch(meta[0], /`|\+ |\$\{/,
    'a computed meta is rejected by the validator before any agent runs')
})

// --------------------------------------------------------------------- fixture staging (Task 1)
//
// stage_fixtures.py and harvest_run.py exist and are tested, but until the workflow calls them an eval
// run cannot measure a skill's real filesystem contract — the executor is told to sandbox into
// outputs/ while the skill under test resolves its own paths from a fixture's Product path:, and every
// archived executor resolved that contradiction by sandboxing itself. These tests pin the wiring that
// closes it.

test('a Stage phase exists, declared in meta.phases, and meta stays a pure literal', () => {
  assert.match(src, /title: 'Stage'/, 'meta.phases must declare the Stage phase')
  const meta = src.match(/export const meta = \{[\s\S]*?\n\}/)
  assert.ok(meta, 'meta must be a single object literal')
  assert.doesNotMatch(meta[0], /`|\+ |\$\{/,
    'the Stage entry must stay a pure literal like every other phase entry')
})

test('the Stage phase runs after Setup and before Execute', () => {
  const setupIdx = src.indexOf(`phase('Setup')`)
  const stageIdx = src.indexOf(`phase('Stage')`)
  const executeIdx = src.indexOf(`phase('Execute')`)
  assert.ok(setupIdx >= 0 && stageIdx >= 0 && executeIdx >= 0, 'all three phase() calls must exist')
  assert.ok(setupIdx < stageIdx, 'Stage must come after Setup\'s work')
  assert.ok(stageIdx < executeIdx, 'Stage must come before Execute')
})

test('a Stage agent invokes stage_fixtures.py with --skill-dir and --workspace, requesting cases back structured', () => {
  assert.match(src, /stage_fixtures\.py/, 'the staging script must be invoked')
  assert.match(src, /--skill-dir/)
  assert.match(src, /--workspace/)
  assert.match(src, /cases:\s*\{\s*type:\s*'object'\s*\}/,
    'the Stage agent\'s schema must accept the cases object stage_fixtures.py returns')
})

test('the Stage agent is told to return the script\'s stdout JSON verbatim, not a summary', () => {
  // One pre-existing "verbatim" already lives in the Setup prompt (the optional executor field) — this
  // pins that the Stage prompt adds its OWN, not that the word merely appears somewhere in the file.
  const mentions = src.match(/verbatim/gi) ?? []
  assert.ok(mentions.length >= 2,
    `expected at least 2 "verbatim" mentions (the pre-existing one plus the Stage prompt's own), found ${mentions.length}`)
  assert.match(src, /stdout[\s\S]{0,200}verbatim/i,
    'the Stage prompt must tell the agent to return the script\'s stdout JSON verbatim')
})

test('the staged result is bound to a module-level const the executor stage reads', () => {
  assert.match(src, /const STAGED = await agent\(/,
    'STAGED must be a module-level const, not scoped inside the pipeline')
})

// --------------------------------------------------------------------- staged prompt reaches the
// --------------------------------------------------------------------- executor, resolved paths win (Task 2)

test('the executor composes its prompt from the staged case, not the raw item.prompt', () => {
  assert.doesNotMatch(src, /\$\{item\.prompt\}\$\{skillPart\}/,
    'the old direct interpolation of the unstaged prompt must be gone')
  assert.match(src, /STAGED\.cases(?:\?\.)?\[item\.name\]/,
    'the executor must look up its staged case by item.name')
  assert.match(src, /\[item\.config\]/,
    'the executor must look up its staged case by item.config too — with_skill and without_skill are staged separately')
})

test('the executor is told a skill-resolved file is written at its resolved location, not redirected', () => {
  assert.match(src, /Product path:/,
    'the executor prompt must name the resolved-path contract the fixture\'s project.md carries')
  assert.match(src, /redirect/i,
    'the executor must be told not to redirect a skill-resolved file into the outputs directory')
})

test('the literal "Input files: none" no longer appears anywhere in the workflow', () => {
  assert.doesNotMatch(src, /Input files: none/,
    'a staged run has real input files at a resolved product path — this literal is now false')
})

test('a "Save all output files to:" instruction still exists, scoped to the transcript and non-skill-placed output', () => {
  assert.match(src, /Save all output files to:/,
    'the outputs-directory instruction must still exist for files the skill does not itself place')
  assert.match(src, /transcript/i)
})

test('phase: \'Execute\', ...EXECUTOR_OPTS still appears exactly once — one spawn shared by both arms', () => {
  const spawns = src.match(/phase: 'Execute', \.\.\.EXECUTOR_OPTS/g) ?? []
  assert.equal(spawns.length, 1, 'the with/without arms must still share one executor spawn')
})

test('the with/without arm difference remains the skill-reading ternary and nothing else', () => {
  assert.match(src, /item\.config === 'with_skill'\s*\n?\s*\?/)
})

// --------------------------------------------------------------------- harvest before grading (Task 3)

test('an agent invokes harvest_run.py with --config-dir before grading', () => {
  assert.match(src, /harvest_run\.py/, 'the harvest script must be invoked')
  assert.match(src, /--config-dir/, 'harvest must be pointed at the run\'s <case>/<config> directory')
})

test('the harvest agent uses a phase name other than \'Grade\', and that phase is declared in meta.phases', () => {
  const harvestCalls = src.match(/label: `harvest-[^}]*\}/g) ?? []
  assert.ok(harvestCalls.length >= 1, `expected at least one harvest agent call, found ${harvestCalls.length}`)
  for (const call of harvestCalls) {
    assert.doesNotMatch(call, /phase: 'Grade'/,
      'a harvest agent must not carry phase: \'Grade\' — it is not a grader and must not be scanned as one')
  }
  assert.match(src, /title: 'Harvest'/, 'the Harvest phase must be declared in meta.phases')
})

test('both grading prompts point the grader at run_delta.json, product/, and reference/', () => {
  const deltaMentions = src.match(/run_delta\.json/g) ?? []
  assert.ok(deltaMentions.length >= 1, 'the grading prompt(s) must name run_delta.json')
  assert.match(src, /product\//, 'the grading prompt must name the product/ copy of what the run wrote')
  assert.match(src, /reference\//, 'the grading prompt must name the reference/ pristine copy')
  // The structural fast-path and the split-path structural call share one structuralPrompt const, so one
  // shared note (interpolated into both) covers both; the nuanced branch has its own separate inline
  // prompt and must interpolate the same note into ITS OWN template too.
  assert.match(src, /run_delta\.json exists at the top of[\s\S]{0,400}reference\//,
    'a shared note defining the run_delta.json / product/ / reference/ contract must exist')
  const structuralPromptSrc = src.match(/const structuralPrompt = `Read \$\{graderMd\}[\s\S]*?Required JSON schema/)
  assert.ok(structuralPromptSrc, 'the structural grading prompt must exist')
  assert.match(structuralPromptSrc[0], /runDeltaNote/,
    'the structural grading prompt must interpolate the run_delta.json note')
  const nuancedCallSrc = src.match(/Grade NUANCED assertions only\.[\s\S]*?Required JSON schema/)
  assert.ok(nuancedCallSrc, 'the nuanced grading call must exist')
  assert.match(nuancedCallSrc[0], /runDeltaNote/,
    'the nuanced grading prompt must ALSO interpolate the run_delta.json note — it has its own separate literal')
})

test('every grader call site is still pinned after adding the harvest agent (regression guard)', () => {
  const graderCalls = src.match(/phase: 'Grade'[^}]*\}/g) ?? []
  assert.ok(graderCalls.length >= 4, `expected at least 4 grading agents, found ${graderCalls.length}`)
  for (const call of graderCalls) {
    assert.match(call, /model: GRADER_MODELS\.\w+/,
      `a grading agent with no model pin inherits the session model, making the run unreproducible: ${call}`)
  }
})

// --------------------------------------------------------------------- the wiring guard (Task 4)

test('the workflow throws after staging if a staged prompt still names this skill\'s fixture root', () => {
  assert.match(src, /throw new Error/,
    'a wiring bug — a prompt still pointing at the tracked fixture tree — must halt the run, not silently grade')
})

test('the guard keys on THIS skill\'s resolved fixture root, not the bare substring evals/inputs', () => {
  assert.doesNotMatch(src, /includes\(['"]evals\/inputs['"]\)/,
    'a bare literal substring would also trip on another instance\'s ~/-rooted fixture path')
  assert.match(src, /STAGED\.fixture_root/,
    'the guard must key on the fixture root stage_fixtures.py resolved for THIS skill')
})

test('the guard runs after staging and before the guard-tripping prompt reaches an executor', () => {
  const stageIdx = src.indexOf('const STAGED = await agent(')
  const throwIdx = src.indexOf('throw new Error')
  const executeIdx = src.indexOf(`phase('Execute')`)
  assert.ok(stageIdx >= 0 && throwIdx >= 0 && executeIdx >= 0)
  assert.ok(stageIdx < throwIdx, 'the guard must read STAGED, so it runs after staging')
  assert.ok(throwIdx < executeIdx, 'the guard must run before Execute — catch the bug before an executor runs on it')
})

test('the thrown error names the offending case and configuration', () => {
  const guardBlock = src.slice(src.indexOf('throw new Error'), src.indexOf('throw new Error') + 400)
  assert.match(guardBlock, /caseName/, 'the error must reference the offending case')
  assert.match(guardBlock, /configName/, 'the error must reference the offending configuration')
})

test('a skill with no fixture tree (staging returns no cases) passes the guard without throwing', () => {
  // STAGED.fixture_root is null for a no-fixture skill (stage_fixtures.py's documented no-op) — the
  // guard must gate on it (or iterate an empty STAGED.cases), never throw unconditionally.
  assert.match(src, /if \(STAGED\.fixture_root\)/,
    'the guard must be gated on a truthy fixture_root, so a no-fixture skill (fixture_root: null) is a clean no-op')
})

// --------------------------------------------------------------------- the archive records the prompt
// --------------------------------------------------------------------- that actually ran (Task 5)

test('a per-config eval_metadata.json write carries the staged prompt AND the authored prompt distinctly', () => {
  assert.match(src, /authored_prompt/,
    'the authored (pre-staging) prompt must be recorded under a distinct key from the staged one')
  assert.match(src, /\$\{workspace\}\/\$\{ev\.name\}\/\$\{config\}\/eval_metadata\.json/,
    'the per-config write must target <eval-name>/<config>/eval_metadata.json — the path the viewer\'s build_run() already checks first, ahead of the eval-level file')
})

test('the per-config write happens after staging, so the recorded prompt is what the executor actually received', () => {
  const stageIdx = src.indexOf('const STAGED = await agent(')
  const perConfigIdx = src.indexOf('authored_prompt')
  assert.ok(stageIdx >= 0 && perConfigIdx >= 0)
  assert.ok(stageIdx < perConfigIdx, 'the staged prompt must be known before it can be recorded')
})

test('the eval-level run_manifest.json write is unchanged — same fields, same models_requested shape', () => {
  // Regression guard: Task 5 adds a NEW per-config file; it must not touch the pre-existing
  // run_manifest.json / eval-level eval_metadata.json write that aggregate_benchmark.py still reads.
  assert.match(src, /models_requested/)
  assert.match(src, /run_manifest\.json/)
  assert.match(src, /executor: EXECUTOR_OPTS\.model \|\| null/)
})

// ===================================================================== code-integrity additions
//
// Added by development-code-integrity, derived from the eval-staging-wiring plan's per-task
// `#### Behaviours to verify` — not from the implementation. Each test below covers a stated behaviour
// that had no test, or one whose existing guard was satisfiable without the behaviour actually holding
// (e.g. a lookup that exists in the file but never reaches the prompt that runs).
//
// The honest limit, same as the whole file: these are regexes over the workflow's source text. They
// prove a line is present and positioned; they cannot prove the wiring executes. That is the
// established technique here — the runtime has no filesystem and the script is not importable — so a
// behaviour asserted this way is pinned against deletion and reordering, not verified end to end.

// ------------------------------------------------- Task 1 — staging, more precisely than "it appears"

test('the Stage agent requests structured output through its schema, in the Stage phase', () => {
  // Task 1: "requests structured output through a schema whose properties include `cases`". The
  // pre-existing test proves a schema with `cases` exists in the file; this proves it reaches the agent.
  // A schema declared but never passed leaves the Stage agent returning free prose, and every
  // downstream STAGED.cases lookup silently undefined — which falls back to the unstaged prompt.
  assert.match(src, /label: 'stage-fixtures'[^}]*schema: STAGE_SCHEMA/,
    'the staging agent must be handed the schema, not merely have one declared nearby')
  assert.match(src, /label: 'stage-fixtures'[^}]*phase: 'Stage'/,
    'the staging agent must run in the Stage phase it declared in meta.phases')
})

test('stage_fixtures.py is invoked with the run\'s own skill dir and workspace', () => {
  // Task 1: "invokes stage_fixtures.py passing both --skill-dir and --workspace". Pinned as one
  // invocation with both flags carrying the run's own values — the pre-existing test matches the two
  // flag names anywhere in the file, which a half-wired call would also satisfy.
  assert.match(src, /stage_fixtures\.py"\s+--skill-dir\s+"\$\{skillDir\}"\s+--workspace\s+"\$\{workspace\}"/,
    'staging must be pointed at the skill under test and this iteration\'s workspace')
})

test('staging runs after Setup\'s work, not merely after the phase() marker', () => {
  // Task 1: the Stage phase is "positioned after the Setup phase's work". The pre-existing ordering
  // test compares phase() markers; staging's real dependency is Setup's OUTPUT — `workspace` is derived
  // from setup.next_iteration, so a Stage placed before the setup agent returns would stage into
  // `iteration-undefined`.
  const setupAgentIdx = src.indexOf('const setup = await agent(')
  const writeMetadataIdx = src.indexOf(`label: 'write-metadata'`)
  const stagedIdx = src.indexOf('const STAGED = await agent(')
  assert.ok(setupAgentIdx >= 0 && writeMetadataIdx >= 0 && stagedIdx >= 0,
    'the setup agent, the metadata write, and the staging agent must all exist')
  assert.ok(setupAgentIdx < stagedIdx,
    'staging must read setup\'s result — the workspace path is derived from setup.next_iteration')
  assert.ok(writeMetadataIdx < stagedIdx, 'staging must follow the whole of Setup\'s work')
})

// ------------------------------------------------- Task 2 — the staged prompt is the one that runs

test('the executor prompt template interpolates the staged prompt', () => {
  // Task 2: "The executor agent() composes its prompt from the staged prompt". The pre-existing tests
  // prove the OLD interpolation is gone and that a staged lookup exists somewhere; neither proves the
  // template that reaches the executor uses the staged value. A dead lookup plus any other spelling of
  // the authored prompt would pass both and silently re-open the contradiction staging exists to close.
  assert.match(src, /`\$\{stagedPrompt\}\$\{skillPart\}/,
    'the prompt handed to the executor must be built from the staged prompt')
})

// ------------------------------------------------- Task 3 — harvest, its target and its position

test('harvest is pointed at the run\'s own <case>/<config> directory', () => {
  // Task 3: harvest_run.py is invoked "with --config-dir pointing at that run's
  // <workspace>/<case>/<config> directory". The pre-existing test proves the flag name appears; this
  // proves what it points at. harvest_run.py resolves inputs/, outputs/ and staged_manifest.json
  // relative to that directory, so a wrong root makes it a silent no-op or a hard error.
  assert.match(src, /const gradingBase = `\$\{workspace\}\/\$\{item\.name\}\/\$\{item\.config\}`/,
    'the config directory must be composed from workspace, case name, and configuration')
  assert.match(src, /--config-dir "\$\{gradingBase\}"/,
    'harvest must be pointed at that config directory, not at outputs/ or the case root')
})

test('harvest runs after the executor and before any grading agent', () => {
  // Task 3: "After the executor completes and before grading". Harvesting before the run has written
  // anything records an empty delta; harvesting after grading records it too late to be read.
  const executorSpawnIdx = src.indexOf(`phase: 'Execute', ...EXECUTOR_OPTS`)
  const harvestIdx = src.indexOf('harvest_run.py')
  const firstGradeIdx = src.indexOf(`phase: 'Grade'`)
  assert.ok(executorSpawnIdx >= 0 && harvestIdx >= 0 && firstGradeIdx >= 0,
    'the executor spawn, the harvest call, and at least one grading agent must all exist')
  assert.ok(executorSpawnIdx < harvestIdx,
    'harvest diffs what the run wrote, so it must follow the executor spawn')
  assert.ok(harvestIdx < firstGradeIdx,
    'harvest must precede grading — the grader reads run_delta.json')
})

test('harvest runs for every run item, not only the with-skill arm', () => {
  // Task 3: "Harvest runs for every run item, not only the with-skill arm." Untested until now. The
  // baseline arm's delta is what makes a where-did-it-land assertion a comparison rather than an
  // assertion about one run in isolation.
  const harvestLabel = src.match(/label: `harvest-[^`]*`/)
  assert.ok(harvestLabel, 'the harvest agent must carry a label')
  assert.match(harvestLabel[0], /\$\{item\.config\}/,
    'the harvest label must vary by configuration, so one harvest exists per arm')
  const beforeHarvest = src.slice(src.indexOf('async (_, item) =>'), src.indexOf('harvest_run.py'))
  assert.doesNotMatch(beforeHarvest, /if \([^)]*with_skill/,
    'harvest must not sit behind a with_skill-only conditional')
})

// ------------------------------------------------- Task 4 — the guard checks both spellings

test('the guard checks both the absolute and the repo-relative spelling of the fixture root', () => {
  // Task 4: the workflow throws when a staged prompt still contains the fixture root "in either its
  // absolute or its repo-relative spelling". stage_fixtures.py rewrites exactly those two spellings, so
  // a guard that checks only one leaves the other able to reach an executor un-rewritten.
  const guardStart = src.indexOf('if (STAGED.fixture_root)')
  const throwIdx = src.indexOf('throw new Error')
  assert.ok(guardStart >= 0 && throwIdx > guardStart, 'the guard block must exist and reach a throw')
  const guard = src.slice(guardStart, throwIdx)
  assert.match(guard, /STAGED\.repo_root/,
    'the repo-relative spelling must be derived from the repo root staging reported')
  const spellingChecks = guard.match(/\.includes\(/g) ?? []
  assert.ok(spellingChecks.length >= 2,
    `the guard must test both spellings, found ${spellingChecks.length} check(s)`)
})

// ------------------------------------------------- Task 5 — `prompt` is the staged one

test('the per-config eval_metadata.json records the STAGED prompt under `prompt`', () => {
  // Task 5: "eval_metadata.json carries the staged prompt under `prompt`, so the viewer displays what
  // ran." The pre-existing test proves `authored_prompt` exists and the path is right, but not that the
  // key the viewer reads holds the staged value — which is the whole point of the task. Verified
  // against the viewer: generate_review.py's build_run() reads `prompt` from the config-level file
  // first, falling back to the eval-level parent.
  assert.match(src, /prompt: stagedPrompt/,
    'the `prompt` key — the one the viewer displays — must hold the staged prompt')
  assert.match(src, /authored_prompt: ev\.prompt/,
    'the authored prompt must be kept under its own distinct key')
})

test('run_manifest.json keeps every field it had before staging was wired', () => {
  // Task 5: "run_manifest.json keeps every field it already has." The pre-existing regression guard
  // checks three tokens out of nine fields, so five could vanish with it still green. The field list is
  // the pre-change manifest at 458b20d — the baseline the behaviour names, not the new code.
  const manifest = src.match(/const runManifest = \{[\s\S]*?\n\}/)
  assert.ok(manifest, 'the run manifest literal must exist')
  for (const field of ['schema_version', 'skill_name', 'iteration', 'models_requested', 'runs_per_configuration']) {
    assert.match(manifest[0], new RegExp(`${field}:`),
      `run_manifest.json lost the top-level field "${field}"`)
  }
  for (const field of ['executor', 'executor_agent_type', 'grader_structural', 'grader_nuanced', 'grader_merge']) {
    assert.match(manifest[0], new RegExp(`${field}:`),
      `models_requested lost the field "${field}" — a run that cannot say what it measured on is incomparable`)
  }
})

// --------------------------------------------------------------------- the fallback is scoped

test('the staged-prompt fallback is keyed on fixture_root, not on the lookup succeeding', () => {
  // `stagedCase?.prompt ?? item.prompt` swallows the one failure that matters: a fixture-having skill
  // whose case did not stage sends the run at the TRACKED tree with the suite green — the exact defect
  // staging exists to close. Keying the branch on fixture_root makes the no-fixture case the only one
  // that may take the authored prompt.
  assert.match(src, /STAGED\.fixture_root \? stagedCase\.prompt : item\.prompt/,
    'the executor must choose its prompt on whether a fixture tree exists, not on a missing key')
  assert.doesNotMatch(src, /stagedCase\?\.prompt \?\? item\.prompt/,
    'the ?? form silently falls back for a staged skill — that is the hole, not the fix')
})

test('an unstaged case in a fixture-having skill throws before any executor runs', () => {
  // The fixture-root guard inspects what WAS staged and is structurally blind to what was not. This is
  // the other direction: every eval × config must have a staged prompt once fixture_root is truthy.
  // Reachable whenever stage_fixtures.py and the Setup agent disagree about a case's name.
  assert.match(src, /has no staged prompt, but this skill HAS a fixture tree/,
    'a fixture-having skill with an unstaged case must fail loudly, naming the case and config')

  const guardIdx = src.indexOf('has no staged prompt')
  const executeIdx = src.indexOf(`phase('Execute')`)
  assert.ok(guardIdx > 0 && guardIdx < executeIdx,
    'the completeness check must run before Execute — catch it before spending an agent on the wrong tree')

  // It must walk the authored eval list, not the staged map: walking STAGED.cases could never notice an
  // absence, which is the whole point of this second check.
  const block = src.slice(guardIdx - 900, guardIdx)
  assert.match(block, /for \(const ev of setup\.evals\)/,
    'completeness must be checked against the authored evals, not against what happened to stage')
})

// --------------------------------------------------------------------- the executor may delete

test('the executor may delete, scoped to its own staged product, and only via rm -f', () => {
  // iteration-9 proved the gap: run_delta.json came back with `deleted: []` because the executor had
  // Read and Write only, so a skill whose done signal is REMOVING a file could not perform the behaviour
  // under test. Before staging that went unnoticed — the companion never existed in outputs/, so
  // "absent" was free. A real fixture turned a free pass into an honest impossibility.
  assert.match(src, /Bash is permitted for exactly one thing/,
    'the executor must be allowed to delete, or a removal-as-done-signal contract is untestable')
  assert.match(src, /inside this run's own staged product/,
    'the capability must be scoped to the staged copy, never the tracked fixture tree')

  // The form is load-bearing, not style: plain `rm` hits this shell's -i and hangs forever, and
  // `/bin/rm` is not in the approve-hook's SAFE set so it defers to a prompt nobody can answer.
  assert.match(src, /rm -f <one path>/,
    'only `rm -f` on a single file both escapes the -i prompt and clears the approve hook')
  assert.match(src, /never a glob, never a path outside your staged product/,
    'a recursive or globbed delete defers to a permission prompt and would hang the run')
})

test('only the executor gained Bash — the graders did not', () => {
  // Graders read outputs and write a grading file. Nothing they do needs a shell, and a grader that can
  // delete could quietly alter the evidence it is judging.
  const bans = src.match(/Do not use Bash\. Use only Read and Write tools\./g) ?? []
  assert.ok(bans.length >= 2,
    `expected the grading prompts to keep their blanket Bash ban, found ${bans.length}`)
})

// --------------------------------------------------------------------- skill-evals's own root is an input

test('skillDir and skillEvalsDir both come from parsed args, not a bare string', () => {
  // The Workflow tool hands args to the script as a JSON string (the same caveat kaizen-cold-read.js
  // documents), so this workflow now parses it the same defensive way rather than treating `args` as
  // the bare skillDir string it used to be.
  assert.match(src, /const input = typeof args === 'string' \? JSON\.parse\(args\) : \(args \?\? \{\}\)/,
    'args must be defensively parsed, matching kaizen-cold-read.js\'s handling')
  assert.match(src, /const skillDir = input\.skillDir/,
    'skillDir must come from the parsed input, not from the raw args value')
  assert.match(src, /const skillEvalsDir = input\.skillEvalsDir/,
    'skillEvalsDir must be a distinct input field — the caller\'s own resolution, not derived here')
})

test('scriptsDir and graderMd are built from skillEvalsDir, never from a root split off skillDir', () => {
  // The old derivation split skillDir and took "one level up" as skillsRoot, assuming skill-evals sits
  // directly beside the skill under test. Under a grouped layout
  // (skills/<group>/.claude/skills/<name>) the skill under test and skill-evals can sit in DIFFERENT
  // groups, so that split silently points scriptsDir/graderMd at a directory that does not exist.
  assert.doesNotMatch(src, /skillDir\.replace\(\/\\\/\+\$\/, ''\)\.split\('\/'\)\.slice\(0, -1\)/,
    'the one-level-up split off skillDir must be gone — it assumed the two skills share a parent')
  assert.match(src, /const scriptsDir = `\$\{skillEvalsDir\}\/scripts`/,
    'scriptsDir must be built from the caller-supplied skillEvalsDir')
  assert.match(src, /const graderMd = `\$\{skillEvalsDir\}\/agents\/grader\.md`/,
    'graderMd must be built from the caller-supplied skillEvalsDir, not a skillsRoot split off skillDir')
})
