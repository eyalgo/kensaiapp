export const meta = {
  name: 'run-skill-evals',
  description: 'Run benchmark evals for any skill. Pass { skillDir, skillEvalsDir } as args.',
  whenToUse: 'Run evals for a skill without entering the full skill-creator flow. Reads evals.json dynamically, auto-detects the next iteration, executes all runs in parallel, grades each as it completes. After the workflow returns, run aggregate_benchmark.py and the viewer in the main session.',
  phases: [
    { title: 'Setup', detail: 'Read evals.json, detect next iteration, write eval_metadata files' },
    { title: 'Stage', detail: 'Stage a private fixture copy per case and configuration, so a skill writes to a real private path instead of the tracked evals/inputs/ tree' },
    { title: 'Execute', detail: 'Run with_skill and without_skill executor agents in parallel pipeline' },
    { title: 'Harvest', detail: 'Diff each run\'s staged product against the pristine fixture and record the delta' },
    { title: 'Grade', detail: 'Grade each run with structural/nuanced graders as it completes' },
  ],
}

// Version: 1.0.3

// args is a JSON string carrying { skillDir, skillEvalsDir } — the same defensive parse
// kaizen-cold-read.js uses, since the Workflow tool hands `args` to the script as a JSON string, not
// the object its docs promise. Both fields are absolute paths, supplied by the one live caller
// (<CORE>/../skills/experimental/.claude/skills/skill-evals/SKILL.md:110-113), which resolves and owns them: `skillDir` is the skill
// under test, wherever it lives; `skillEvalsDir` is skill-evals's own directory, wherever IT lives. The
// two need not share a parent — under a flat layout both sit under the same `.claude/skills/`, but
// under a grouped layout (`skills/<group>/.claude/skills/<name>`) they may sit in different groups
// entirely. This workflow does not derive one from the other's parent; that derivation (a single
// "one level up" split) is exactly what broke the moment they diverge.
const input = typeof args === 'string' ? JSON.parse(args) : (args ?? {})
const skillDir = input.skillDir
const skillEvalsDir = input.skillEvalsDir

const scriptsDir = `${skillEvalsDir}/scripts`

// The utility agents — the plumbing around the measurement. None of them executes the skill or grades
// it: they read a JSON, write strings this script has already composed, or run a script and hand back
// its stdout. model_assignment.md § Runs with no standing slot puts "one checkable transformation at
// volume" on the cheap tier, so that is where they are pinned.
//
// Pinned EXPLICITLY, never inherited, and that is the whole point of this constant. An unpinned agent
// takes the model of whatever session happened to drive the run, so the run's cost depends on its
// launcher rather than on its work — and on the day a Fable session drove one, fourteen agents per run
// silently billed the top tier to call `Write` on a string this file had already built.
//
// `readEvals` is the one exception, and it is deliberate: that agent computes next_iteration as
// HIGHEST + 1, the one utility slip that cannot be undone. workspace/ is gitignored, so an overwritten
// iteration is gone — while every other utility call can simply be re-run. Arithmetic whose failure is
// unrecoverable buys the worker tier; the rest do not need it.
const UTILITY_MODELS = { readEvals: 'sonnet', plumbing: 'haiku' }

const SETUP_SCHEMA = {
  type: 'object',
  properties: {
    skill_name: { type: 'string' },
    next_iteration: { type: 'integer' },
    // Optional. A skill declares the body its executor runs on, so a CTO/CPO-tier skill is measured
    // on the brain that ships it rather than whatever model the session happened to inherit.
    // Deliberately NOT in `required` below — seven other evals.json files carry no executor block.
    executor: {
      type: 'object',
      properties: {
        model: { type: 'string' },
        agentType: { type: 'string' },
      },
    },
    evals: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'integer' },
          name: { type: 'string' },
          prompt: { type: 'string' },
          structural: { type: 'array', items: { type: 'string' } },
          nuanced: { type: 'array', items: { type: 'string' } },
        },
        required: ['id', 'name', 'prompt', 'structural', 'nuanced'],
      },
    },
  },
  required: ['skill_name', 'next_iteration', 'evals'],
}

// Phase 1: Read evals.json, detect iteration, write metadata
phase('Setup')
const setup = await agent(
  `You have two tasks:

1. Read ${skillDir}/evals/evals.json. Extract:
   - skill_name (top-level field)
   - executor (top-level field) — OPTIONAL. If the file has a top-level "executor" object, return it verbatim (its "model" and/or "agentType" strings). If there is no such field, omit it entirely; do not invent one.
   - For each eval: id, name, prompt, and split assertions into two string arrays:
     - structural: the description field of assertions where tier == "structural"
     - nuanced: the description field of assertions where tier == "nuanced"

2. Use Glob with pattern ${skillDir}/evals/workspace/iteration-* to find existing iteration directories. Read the trailing number off each one and set next_iteration = (highest number found) + 1, or 1 if there are none.

   Take the HIGHEST number, never the count. The two differ whenever the sequence has a gap — with iteration-1, 2, 4, 5 on disk the count is 4, so counting would return 5 and the run would overwrite an existing iteration. Never reuse or overwrite an iteration directory; a run archive is the only record of what a past run did, and workspace/ is gitignored so an overwrite is unrecoverable.

Return all data as structured output.`,
  { label: 'read-evals', phase: 'Setup', schema: SETUP_SCHEMA, model: UTILITY_MODELS.readEvals }
)

const workspace = `${skillDir}/evals/workspace/iteration-${setup.next_iteration}`

// The brains this run uses for the measurement itself — the executor and the graders — recorded into
// the workspace so the benchmark can say what it measured on; a run whose model is unknown cannot be
// compared against another run. The plumbing's pins are UTILITY_MODELS, declared at the top of this
// file because the first utility agent runs before this point.
//
// Executor: the skill's own declaration, or nothing (inherit the session model, as before). Pinning the
// model WITHOUT an agentType is deliberate for a posture-gated skill: a real role slot would inject its
// loader stack, and for product-srs that stack restates the skill's own contract — which would hand the
// blind baseline the answer.
//
// Graders are tiered by the KIND of check: a structural check is one checkable transformation at volume
// (Haiku); a nuanced check applies a written criterion that no pattern can approximate (Sonnet); the
// merge is a mechanical fold (Haiku, and it should be a script, not an agent). This is the split
// README.md and references/schemas.md have always documented.
//
// Haiku is right for structural even though a Haiku grading once emitted malformed JSON: that was a
// serialization failure, not a wrong verdict, and the defect it exposed is downstream —
// aggregate_benchmark.py dropped the unreadable file with a warning instead of failing loudly, so a
// whole arm vanished from a benchmark. Fix the silent drop; do not buy a bigger model to hide it.
//
// Holding the graders where iteration-6 had them also keeps the grader constant across the executor
// change, so a 6-to-7 diff attributes to the executor model rather than to a more generous grader.
//
// This map is NOT a quality ranking, and must not be read as one. `structural` is the PREFERRED tier —
// skill-evals-creator/SKILL.md § tiers owns that rule and the justification an assertion owes before it
// may be nuanced. Structural is preferred precisely because it is mechanically verifiable, which is why
// it wants a reliable model rather than a clever one. A nuanced check gets the senior tier because no
// pattern can approximate it — never because nuanced is the better kind of assertion to write.
//
// The direction this points: an assertion that is genuinely structural should not need a model at all.
// Today's descriptions are prose ("contains exactly the two bucket labels…"), so a grader must
// interpret them; machine-readable patterns would let a script grade the structural tier
// deterministically — no model, no variance, no malformed JSON. That is the strongest possible form of
// the structural feature, and it is a separate station.
// Empty values are dropped rather than passed through. `executor`'s properties are declared but not
// required, so the Setup agent may return `agentType: ""` instead of omitting the key — on 2026-08-03
// (run wf_3456bd10-9c0, product-uxd iteration-1) that "" reached the spread into the executor's agent
// options below and killed all ten runs with `agent type '' not found`, while runManifest's `|| null`
// collapsed "" and absent to the same recorded value, so the manifest showed nothing wrong. A real pin
// is truthy and passes through untouched.
const EXECUTOR_OPTS = Object.fromEntries(
  Object.entries(setup.executor || {}).filter(([, value]) => value)
)
const GRADER_MODELS = { structural: 'haiku', nuanced: 'sonnet', merge: 'haiku' }

// What was ASKED FOR, which is all a spawner can honestly claim. commit_format.md § Filling the model:
// a model literal handed to an agent is the spawner's request, not proof of what ran — only the running
// agent knows its own identity. An absent executor pin is recorded as null, never guessed.
// schema_version 2 adds the two utility pins below. The bump is not ceremony: this manifest exists so
// that "a run whose models are unknown cannot be compared", and a reader holding an iteration from
// before the pins needs to tell "this run left its plumbing unpinned" apart from "this run did not
// record it". Every consumer reads through .get(), so the added fields are backward-safe.
const runManifest = {
  schema_version: 2,
  skill_name: setup.skill_name,
  iteration: setup.next_iteration,
  models_requested: {
    executor: EXECUTOR_OPTS.model || null,
    executor_agent_type: EXECUTOR_OPTS.agentType || null,
    grader_structural: GRADER_MODELS.structural,
    grader_nuanced: GRADER_MODELS.nuanced,
    grader_merge: GRADER_MODELS.merge,
    utility_read_evals: UTILITY_MODELS.readEvals,
    utility_plumbing: UTILITY_MODELS.plumbing,
  },
  runs_per_configuration: 1,
}

const metadataInstructions = setup.evals.map(ev =>
  `File: ${workspace}/${ev.name}/eval_metadata.json\n${JSON.stringify({ eval_id: ev.id, eval_name: ev.name, prompt: ev.prompt }, null, 2)}`
).join('\n\n')

await agent(
  `Write these ${setup.evals.length + 1} files exactly as specified. Do NOT include assertions in any eval_metadata.json. Use the Write tool only — no Bash.

File: ${workspace}/run_manifest.json
${JSON.stringify(runManifest, null, 2)}

${metadataInstructions}`,
  { label: 'write-metadata', phase: 'Setup', model: UTILITY_MODELS.plumbing }
)

log(`${setup.skill_name} — iteration ${setup.next_iteration} — workspace: ${workspace}`)
log(`executor: ${JSON.stringify(EXECUTOR_OPTS)} · graders: ${JSON.stringify(GRADER_MODELS)} · utility: ${JSON.stringify(UTILITY_MODELS)}`)

// Build run items: one entry per (eval × config) combination
const RUN_ITEMS = []
for (const ev of setup.evals) {
  RUN_ITEMS.push({ ...ev, config: 'with_skill' })
  RUN_ITEMS.push({ ...ev, config: 'without_skill' })
}

// Phase: stage a private, writable fixture copy for every (case × configuration) this run will execute,
// so a skill that resolves its own paths from a fixture's Product path: writes somewhere real and
// private instead of the tracked evals/inputs/ tree fixture_guard.py protects. See stage_fixtures.py's
// module docstring for why this closes the sandboxing-vs-guard contradiction: until now every archived
// with-skill executor sandboxed itself instead of obeying the skill, which means assertions about where
// a file lands were passing for the wrong reason.
phase('Stage')

const STAGE_SCHEMA = {
  type: 'object',
  properties: {
    schema_version: { type: 'integer' },
    repo_root: { type: 'string' },
    fixture_root: { type: ['string', 'null'] },
    cases: { type: 'object' },
  },
  required: ['cases'],
}

const STAGED = await agent(
  `Stage a private, writable fixture copy for every (case × configuration) this run will execute.

Invoke via Bash:
  python3 "${scriptsDir}/stage_fixtures.py" --skill-dir "${skillDir}" --workspace "${workspace}"

The script prints exactly one JSON object to its stdout. Return that JSON verbatim as your structured output — do not summarize, paraphrase, reshape, or drop any field. A skill with no evals/inputs/ fixture tree is a clean no-op: the script still prints valid JSON with an empty "cases" object and a null "fixture_root" — return that verbatim too, do not treat it as an error.`,
  { label: 'stage-fixtures', phase: 'Stage', schema: STAGE_SCHEMA, model: UTILITY_MODELS.plumbing }
)

log(`staged ${Object.keys(STAGED.cases || {}).length} case(s), fixture_root: ${STAGED.fixture_root}`)

// Refuse to proceed if staging left any prompt still pointing at the tracked fixture tree — a run
// graded against that prompt would still be measuring the sandboxing hack this staging step replaces,
// not the skill's real filesystem contract. That is a wiring bug, not a run to grade.
//
// Keys on THIS skill's resolved fixture root (both spellings stage_fixtures.py's own rewrite targets:
// the absolute path and that path relative to the repo), never the bare substring "evals/inputs" — a
// prompt naming another instance's `~/`-rooted fixture path must not trip it. Gated on a truthy
// fixture_root, so a skill with no evals/inputs/ tree at all (fixture_root: null, cases: {}) is a
// clean no-op — there is nothing to check.
if (STAGED.fixture_root) {
  const fixtureRootAbs = STAGED.fixture_root
  const fixtureRootRel = STAGED.repo_root && fixtureRootAbs.startsWith(STAGED.repo_root)
    ? fixtureRootAbs.slice(STAGED.repo_root.length).replace(/^\/+/, '')
    : fixtureRootAbs

  // Keyed by case name so the arm check below can tell "never referenced the fixture tree" apart
  // from "referenced it and got corrupted in the relay" — the two need different verdicts.
  const authoredPromptByCase = Object.fromEntries(setup.evals.map(ev => [ev.name, ev.prompt]))

  for (const [caseName, configs] of Object.entries(STAGED.cases || {})) {
    // A case whose AUTHORED prompt never named the fixture tree (e.g. a posture-halt prompt with no
    // project path at all) is never touched by stage_fixtures.py's rewrite — both arms legitimately
    // stay byte-identical to the authored prompt. There is no arm for such a prompt to name, so the
    // per-arm check below does not apply to it; only a case that DID name the fixture tree can have
    // that naming corrupted in the relay.
    const authoredPrompt = authoredPromptByCase[caseName] || ''
    const authoredReferencesFixture =
      authoredPrompt.includes(fixtureRootAbs) || authoredPrompt.includes(fixtureRootRel)

    for (const [configName, data] of Object.entries(configs || {})) {
      const stagedPrompt = data?.prompt || ''
      if (stagedPrompt.includes(fixtureRootAbs) || stagedPrompt.includes(fixtureRootRel)) {
        throw new Error(`run-skill-evals: staged prompt for case "${caseName}" (${configName}) still names the tracked fixture tree (${fixtureRootRel}) after staging. That is a wiring bug, not a run to grade — fix stage_fixtures.py's rewrite or the eval's authored prompt, then re-run.`)
      }

      if (!authoredReferencesFixture) continue

      // Each arm's prompt must name ITS OWN arm, and never its sibling's.
      //
      // Measured in product-prd iteration-7: this arm's prompt named the sibling. stage_fixtures.py
      // was NOT at fault — its own stage_manifest.json records the correct path for every arm in
      // that round, verified after the fact. The corruption happened in the relay: the script prints
      // one large JSON object, an agent reads that stdout and hands it back as structured output,
      // and this object is what feeds BOTH the executor's prompt and eval_metadata.json. A workflow
      // has no filesystem, so an agent is the only way that data can travel — which makes the relay
      // a place a value can silently change, and one field did.
      //
      // The cost of not catching it is the whole round: the arm works in its sibling's tree, its own
      // tree stays empty, it grades 0 for a reason that has nothing to do with the skill, and the
      // sibling finds a stray product and re-enters over it. That is ~30M executor tokens spent
      // measuring nothing. Checked here because the data is already in hand — pure JS, no agent, no
      // cost — and thrown rather than repaired, since a relay that corrupted one field has no claim
      // to be trusted about the others.
      const ownArm = `/${configName}/`
      const siblingArm = configName === 'with_skill' ? '/without_skill/' : '/with_skill/'
      if (stagedPrompt.includes(siblingArm) || !stagedPrompt.includes(ownArm)) {
        throw new Error(`run-skill-evals: staged prompt for case "${caseName}" (${configName}) does not name its own arm — it must contain "${ownArm}" and must not contain "${siblingArm}". stage_fixtures.py's stage_manifest.json is the authority; compare it against this value. The prompt reached here through an agent relaying the script's stdout, which is where the value changed in product-prd iteration-7. Not a run to grade.`)
      }
    }
  }

  // Completeness, the other direction. The check above inspects what WAS staged; this one catches what
  // was not. A fixture-having skill with a case missing from STAGED.cases would fall through to the
  // authored prompt at the executor and read the tracked tree — and the check above cannot see it,
  // because it only walks staged entries. Reachable whenever the two sides disagree about a case's
  // name: stage_fixtures.py keys on the name in evals.json, the workflow keys on the name the Setup
  // agent reported. Fail here rather than spend an agent on a run that measures the wrong tree.
  for (const ev of setup.evals) {
    for (const config of ['with_skill', 'without_skill']) {
      if (!STAGED.cases?.[ev.name]?.[config]?.prompt) {
        throw new Error(`run-skill-evals: case "${ev.name}" (${config}) has no staged prompt, but this skill HAS a fixture tree (${fixtureRootRel}). Falling back to the authored prompt would point the run at the tracked fixtures, which is the failure staging exists to close. Check that stage_fixtures.py and the Setup agent agree on the case name.`)
      }
    }
  }
}

// Per-(case × config) metadata, carrying the STAGED prompt the executor actually received — distinct
// from the authored prompt already recorded in the eval-level eval_metadata.json above (Setup phase,
// still read by aggregate_benchmark.py's eval_id lookup — left untouched). The viewer's build_run()
// already prefers a config-level eval_metadata.json over its eval-level parent, so this needs no change
// on the read side: the archive now says which prompt ran, not only which prompt was authored.
const stagedMetadataInstructions = setup.evals.flatMap(ev =>
  ['with_skill', 'without_skill'].map(config => {
    const stagedPrompt = STAGED.cases?.[ev.name]?.[config]?.prompt ?? ev.prompt
    return `File: ${workspace}/${ev.name}/${config}/eval_metadata.json\n${JSON.stringify(
      { eval_id: ev.id, eval_name: ev.name, prompt: stagedPrompt, authored_prompt: ev.prompt },
      null, 2
    )}`
  })
).join('\n\n')

await agent(
  `Write these ${setup.evals.length * 2} files exactly as specified. Do NOT include assertions in any eval_metadata.json. Use the Write tool only — no Bash.

${stagedMetadataInstructions}`,
  { label: 'write-staged-metadata', phase: 'Stage', model: UTILITY_MODELS.plumbing }
)

// Phase 2+3: Execute all runs, grade each immediately as it completes
phase('Execute')
await pipeline(
  RUN_ITEMS,

  // Stage 1 — Execute the run
  (item) => {
    const outputsDir = `${workspace}/${item.name}/${item.config}/outputs`
    // The staged prompt for THIS (case, config) — rewritten by stage_fixtures.py to point at this run's
    // own private fixture copy rather than the tracked evals/inputs/ tree.
    //
    // The fallback is scoped to the ONLY case that may legitimately take it: a skill with no fixture
    // tree at all, where there is nothing to stage and the authored prompt is already self-contained.
    // It is keyed on `fixture_root` rather than on the lookup succeeding, because `?? item.prompt`
    // silently swallows the one failure that matters — a fixture-having skill whose case did not stage —
    // and sends the run at the tracked tree with the suite green. That case now throws at the guard
    // above; here the code says which branch it is taking instead of leaving it to a missing key.
    const stagedCase = STAGED.cases?.[item.name]?.[item.config]
    const stagedPrompt = STAGED.fixture_root ? stagedCase.prompt : item.prompt
    const skillPart = item.config === 'with_skill'
      ? `\n\nRead the skill at ${skillDir}/SKILL.md before executing.`
      : `\n\nExecute without any skill guidance. Do NOT read any skill files, SKILL.md, or any file under any skills/ directory. You are the baseline agent — produce output using only your own judgment and role context, with no skill guidance.`

    return agent(
      `${stagedPrompt}${skillPart}

Any file you resolve from a fixture's own Product path: (or a location the skill itself derives from its own contract) is real and private to this run — write it there, at that resolved location. Do NOT redirect a skill-resolved file into the outputs directory below; that path is real, not a sandbox.
${STAGED.fixture_root ? `
This run's own staged tree is ${workspace}/${item.name}/${item.config}/ — the binding path named in your task above lives under its inputs/. Follow that binding path literally. Sibling directories under ${workspace} belong to OTHER runs executing in parallel right now: never read a binding or a fixture from one, and never write into one. If a path you resolved does not sit under your own staged tree, you resolved the wrong binding — stop and re-read the task's binding path.
` : ''}

You are an executor agent. Write ALL files the skill's output references — at the location the skill itself resolves one, or in the outputs directory when it does not. Do not omit files because their content seems report-like. Your job is to produce files.

Save all output files to: ${outputsDir}

That means your transcript, and anything the skill's own contract does not already place at a resolved path.

Do NOT create .keep or .gitkeep placeholder files. The outputs directory is created when you write your first file there.

Use Read and Write for everything you produce. Bash is permitted for exactly one thing: **deleting a file the skill's own contract tells you to remove**, and only inside this run's own staged product. Nothing else — no reading, no listing, no moving, no writing through the shell.

When you delete, the form is \`rm -f <one path>\`. Plain \`rm\` hangs (this shell's \`rm\` is interactive and there is nobody to answer it) and \`/bin/rm\` stalls on a permission prompt; \`rm -f\` on a single file is the only form that completes unattended. Never \`-r\`, never a glob, never a path outside your staged product.

If a skill's contract says a file's removal is its done signal, actually remove it — that is a behaviour under test, and a run that leaves the file in place has not exercised it.

Save a transcript of your work (what you did, decisions made) to: ${outputsDir}/transcript.md`,
      { label: `run-${item.id}-${item.config}`, phase: 'Execute', ...EXECUTOR_OPTS }
    )
  },

  // Stage 2 — Harvest what the run did to its staged product, then grade it
  async (_, item) => {
    const gradingBase = `${workspace}/${item.name}/${item.config}`
    const outputsDir = `${gradingBase}/outputs`

    // Harvest BEFORE grading — diffs the run's staged product against the pristine fixture and writes
    // run_delta.json (plus product/ + reference/ copies) into outputsDir, so a "where did the file
    // land" assertion reads a recorded fact instead of guessing from a directory walk. Runs for every
    // item this pipeline processes — with_skill and without_skill alike, not only the with-skill arm.
    await agent(
      `Record what this run did to its staged product, for the grader to read.

Invoke via Bash:
  python3 "${scriptsDir}/harvest_run.py" --config-dir "${gradingBase}"

The script writes run_delta.json, plus product/ and reference/ copies, into ${outputsDir}. It prints a short created/modified/deleted summary to stdout — return that summary as plain text; there is nothing to parse.`,
      { label: `harvest-${item.id}-${item.config}`, phase: 'Harvest', model: UTILITY_MODELS.plumbing }
    )

    // A tier writes straight to grading.json when it is the ONLY tier present; the split
    // files exist only so the merge below has two halves to join.
    const hasStructural = item.structural.length > 0
    const hasNuanced = item.nuanced.length > 0
    const targetFile = hasNuanced
      ? `${gradingBase}/grading_structural.json`
      : `${gradingBase}/grading.json`
    const nuancedTarget = hasStructural
      ? `${gradingBase}/grading_nuanced.json`
      : `${gradingBase}/grading.json`
    const structuralList = item.structural.map((s, i) => `${i + 1}. ${s}`).join('\n')
    // grader.md lives in skill-evals's own directory — supplied by the caller as skillEvalsDir (above),
    // never derived from skillDir's parent.
    const graderMd = `${skillEvalsDir}/agents/grader.md`
    const jsonSchema = `{ "eval_id": ${item.id}, "eval_name": "${item.name}", "configuration": "${item.config}", "summary": {"pass_rate":0.0,"passed":0,"failed":0,"total":0}, "expectations": [{"text":"...","passed":true,"evidence":"..."}], "execution_metrics":{"tool_calls":0,"errors":0}, "claims":[], "user_notes_summary":{}, "eval_feedback":{"suggestions":[],"overall":""} }`

    // Handed to every grading prompt (structural and nuanced both) so an assertion about WHERE a file
    // landed or WHAT changed reads run_delta.json / product/ / reference/ instead of a directory walk.
    const runDeltaNote = `run_delta.json exists at the top of ${outputsDir} and records the created / modified / deleted product paths this run produced, relative to the staged product root. ${outputsDir}/product/ holds the files the run wrote, path preserved; ${outputsDir}/reference/ holds the pristine, pre-run version of anything the run modified or deleted. Read these for any assertion about where a file landed or what changed.`

    const structuralPrompt = `Read ${graderMd} and grade this run.

Grade STRUCTURAL assertions only. Examine output files directly. Do NOT read the transcript. Skip grader.md Steps 4–6 — leave claims, user_notes_summary, and eval_feedback empty.

${runDeltaNote}

Do not use Bash. Use only Read and Write tools.

Eval: ${item.name} (${item.config})

Expectations (structural):
${structuralList}

Outputs dir: ${outputsDir}
Save to: ${targetFile}

Required JSON schema: ${jsonSchema}`

    // NEVER spawn a grader with an empty expectation list. A grader handed no expectations
    // does not return an empty set — it invents its own and grades against them, so the
    // totals inflate and the two arms are scored against different fabricated bars. Measured
    // 2026-08-21 on companion-answer iteration 2: a case with zero structural assertions came
    // back with 3 fabricated structural expectations in one arm and 1 in the other. It is
    // intermittent — two other zero-structural cases in the same run graded 0 correctly —
    // which is why the guard is here rather than in a prompt telling the grader to return [].
    // A case that is entirely about what the run SAYS legitimately has no structural half.
    if (!hasNuanced) {
      await agent(structuralPrompt, { label: `grade-${item.id}-${item.config}`, phase: 'Grade', model: GRADER_MODELS.structural })
    } else if (!hasStructural) {
      const nuancedList = item.nuanced.map((s, i) => `${i + 1}. ${s}`).join('\n')
      await agent(
        `Read ${graderMd} and grade this run.

Grade NUANCED assertions only. Read both the transcript and the output files. Perform full grader.md Steps 4–6.

${runDeltaNote}

Do not use Bash. Use only Read and Write tools.

Eval: ${item.name} (${item.config})

Expectations (nuanced):
${nuancedList}

Transcript: ${outputsDir}/transcript.md
Outputs dir: ${outputsDir}
Save to: ${nuancedTarget}

Required JSON schema: ${jsonSchema}`,
        { label: `grade-${item.id}-${item.config}`, phase: 'Grade', model: GRADER_MODELS.nuanced }
      )
    } else {
      const nuancedList = item.nuanced.map((s, i) => `${i + 1}. ${s}`).join('\n')

      await parallel([
        () => agent(structuralPrompt, { label: `grade-struct-${item.id}-${item.config}`, phase: 'Grade', model: GRADER_MODELS.structural }),
        () => agent(
          `Read ${graderMd} and grade this run.

Grade NUANCED assertions only. Read both the transcript and the output files. Perform full grader.md Steps 4–6.

${runDeltaNote}

Do not use Bash. Use only Read and Write tools.

Eval: ${item.name} (${item.config})

Expectations (nuanced):
${nuancedList}

Transcript: ${outputsDir}/transcript.md
Outputs dir: ${outputsDir}
Save to: ${nuancedTarget}

Required JSON schema: ${jsonSchema}`,
          { label: `grade-nuanced-${item.id}-${item.config}`, phase: 'Grade', model: GRADER_MODELS.nuanced }
        ),
      ])

      // Merge structural + nuanced grading files into a single grading.json
      await agent(
        `Read ${gradingBase}/grading_structural.json and ${gradingBase}/grading_nuanced.json.

Merge them into ${gradingBase}/grading.json:
- expectations array: structural expectations first, then nuanced
- summary: recalculate total/passed/failed/pass_rate across both sets

Do not use Bash. Use only Read and Write tools.`,
        { label: `merge-${item.id}-${item.config}`, phase: 'Grade', model: GRADER_MODELS.merge }
      )
    }

    return item
  }
)

log(`All runs executed and graded. Workspace: ${workspace}`)
return { workspace, skill_name: setup.skill_name, iteration: setup.next_iteration }
