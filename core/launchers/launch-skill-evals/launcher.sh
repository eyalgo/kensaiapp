#!/usr/bin/env bash
#
# launcher.sh (launch-skill-evals) — deterministic, pollution-proof launcher for one skill-evals round.
#
# Version: 1.15.0 — the other six launchers run on the package's turn-on
# Version: 1.14.2 — launchers and launch scripts take a portable mktemp template, so they run on Linux
# Version: 1.14.1 — the permissions comment names where a pinned run's allow list comes from: settings.local.json, not settings.json
# Version: 1.14.0 — the providers file lives in the instance — each instance reads its own .providers.toml, and a tracked .providers.toml.example is the template
# Version: 1.13.0 — a pinned run sees only its own skill group
# Version: 1.12.0 — the eight skill launchers read their provider from the central providers file and refuse naming the entry when it is missing — no literal claude
# Version: 1.11.0 — the eleven other instrumented launchers stamp provider, model, effort and source through one shared resolution
# Version: 1.10.0 — a run keeps the version it started on — every launcher enters a pin of core/, .claude/ and skills/
# Version: 1.9.0 — a grouped skill-evals has its group admitted with --add-dir, so the run can reach the skill whose steps it follows
# Version: 1.8.0 — a launcher may live nested under core/launchers/development/, and its reach resolves <CORE> from its own location instead of counting folders
# Version: 1.7.0 — a launcher-started record says which instance, product and operation it was for — instrument_run stamps them, chain.py ties a walk, and the step-name seed is parked by the owner's ruling
# Version: 1.6.0 — the backgrounded launchers are tagged too — every launcher hands its telemetry to the spawn as --settings; station 2 closes and the seed is set down
# Version: 1.5.0 — station 2's instrument lands — every launcher tags its own run, and the receiver answers only this machine
# Version: 1.4.0 — the resolver capture no longer folds stderr into the value that becomes
#   $skill_dir (was `2>&1`; a future resolver warning on a successful exit would have landed
#   INSIDE the path). Standard error is captured to its own temp file instead, read back only for
#   the ambiguous (exit 4) message, which is what it always fed. $RESOLVER also gains an env
#   override, LAUNCH_EVALS_RESOLVER, the seam a test needs to stand a stub resolver on this path.
# Version: 1.3.0 — the id parse this launcher owned is now the shared library's
#   `capture_agent_id`, called rather than repeated, and the id it reads goes to the WATCHER as
#   --agent-id as well as to the round lock. It was the only launcher that had ever captured its
#   own id and the only one that never told its watcher. The launch output is redirected to a file
#   rather than captured through a pipe, which waits for end-of-file and would block on the
#   detached run.
# Version: 1.2.0 — the hand-copied detach-and-return tail is gone: this launcher `source`s
#   the shared completion-watch home at <CORE>/tools/detach_watcher.sh and calls
#   `detach_completion_watcher` with its own values. Same behaviour, one exception the move
#   carries deliberately: the else branch now names WHICH half is missing — an unfindable
#   watcher is a launcher bug and an unset notifier is ordinary configuration, and reporting
#   the second when the first is true sends the reader to the wrong end. $DETACH_LIB is the
#   second core-relative path this file resolves and has no env override, so its default is
#   its only path. The poll knob named below keeps its own name and keeps working: it is
#   handed to the library as --keepawake-poll-seconds rather than renamed, which is what made
#   this a refactor instead of a rewrite of nine documented interfaces.
# Version: 1.1.0 — --keep-awake no longer waits on a bare pid number: the watcher's pid is paired
#   with the start time it had when this launcher spawned it, and a detached poller releases
#   caffeinate the moment a live process at that number stops matching both — never the lifetime
#   of whatever unrelated process the kernel later reissues the number to. An internal knob,
#   LAUNCH_EVALS_KEEPAWAKE_POLL_SECONDS (default 5), sets how often that identity is re-checked.
# Version: 1.0.0. Carries the shape every owner-run launcher carries — a folder beside <CORE>/tools/
#   rather than inside it, so the watcher is two levels up then one hop into tools/; a FIXED prompt; a
#   detached watcher (kensaiapp_structure.md § Owner-run launcher folder owns all three). What is new
#   here is the serialisation guard and the driver pin.
#
# WHY THIS EXISTS
#   Same reason as its siblings: a session asked to "run the evals for X" *composes* the driving
#   prompt, and that is the one place stray context leaks in (last round's numbers, which failures you
#   think matter, "and fix the skill while you're there"). The prompt below is a FIXED literal — a
#   caller passes only a skill name. Nothing a caller types reaches the run.
#
#   It also removes two decisions from the caller that were being re-derived, wrongly, every round: how
#   many rounds may run at once, and what model drives them.
#
# WHY IT REFUSES TO RUN TWO AT ONCE
#   A round's cost is dominated by its executors, not its plumbing: one with-skill executor averaged
#   3.6M billed tokens in product-srs iteration-12, so a five-case round is ~30M tokens and two rounds
#   in parallel is ~60M. On 2026-07-26 two were launched together and both died mid-workflow on the
#   account session limit, losing the reasoning as well as the benchmark. Sequencing is therefore not
#   advice in a prompt that has to be retyped — it is a refusal, here, where it cannot be forgotten.
#
#   The guard is deliberately coarse: it blocks on any live eval round, whatever skill it is for and
#   whatever directory it runs in. Skill breadth because two skills' rounds are two full executor
#   fan-outs; directory breadth because the limit that actually stopped them is per-ACCOUNT, and the
#   incident was two rounds in two worktrees of one repo — two different cwds. A guard scoped to the
#   instance root would have watched both start and blocked neither.
#
#   That is why this does not reuse watch_agent.py's --cwd filter: that filter answers "which agent
#   did THIS launch spawn", a question about identity, where two directories genuinely are two
#   things. This asks "is the account already busy", a question about load, and load ignores
#   directories.
#
# WHY A LOCK FILE, AND NOT THE AGENT'S NAME
#   The obvious guard — look for a running agent whose name starts with our fixed prompt — does not
#   work, and fails silently. Claude Code RENAMES a background agent shortly after launch: a round
#   launched with a prompt opening "run the skill-evals benchmark for the ..." was listed minutes
#   later as "run skill-evals benchmark product-prd". Nothing in `claude agents --json` carries the
#   original prompt, so there is no stable string to match on and a name-matching guard reports a
#   clear field about a minute after a round starts. Verified against a live round on 2026-07-27.
#
#   So the launcher records the agent id it actually launched, parsed out of `claude --bg`'s own
#   "backgrounded · <id>" line. Where that lock lives, what it holds, and when it is stale are
#   <CORE>/tools/evals_round_lock.py's — not restated here, because launch-eval-fix reads the same
#   lock (it must not edit a skill while that skill is being benchmarked) and a second copy of the
#   protocol is a second copy free to drift.
#
# WHY A SONNET DRIVER, AND NO --agent
#   model_assignment.md § Runs with no standing slot: a `--bg` session has no slot to inherit from, so
#   the model is a per-run choice made by where the judgment lives. This driver runs an autonomous tool
#   loop — validate, invoke the workflow, run three scripts, read the result — which that section puts
#   at the worker tier ("driving the loop is itself judgment"). It does NOT decide fixes: that is a
#   separate pass, on a separate brain, reading the committed benchmark.
#
#   No --agent, for the same reason § Eval runs gives for the executor: a role slot injects its loader
#   stack, and this session must not carry a posture into a measurement.
#
#   The driver's model is no longer load-bearing for the rest of the run. Until 2026-07-27 the
#   workflow's utility agents were unpinned and inherited it, so a Fable driver silently put fourteen
#   agents per round on the top tier; they now carry their own pins (run-skill-evals.js UTILITY_MODELS).
#
# WHY THE PROMPT SKIPS SKILL-EVALS STEPS 4-5
#   Step 4 starts the eval viewer on a fixed port and opens a browser; step 5 reads the feedback.json a
#   human writes there. Neither survives an unattended run. This is launcher policy rather than skill
#   text because the skill is also driven interactively, where 4-5 are exactly right. If a second
#   unattended entry point ever appears, the rule has earned a home in the skill instead of a second
#   copy here.
#
# WHY IT PRESERVES OUT OF REPO
#   `.claude/skills/*/evals/workspace/` is gitignored, and a round run in a worktree dies with the
#   worktree, so the archive has to be copied somewhere real or the round leaves only its commit.
#   The destination comes from KENSAIAPP_EVAL_HISTORY — no host-global default, per
#   kensaiapp_structure.md § core/tools ("take the notifier from KENSAIAPP_NOTIFIER (no host-global
#   default)"), which binds any machine-local path a shared tool would otherwise bake in. Unset means
#   the preservation clause is simply absent from the prompt and the launcher says so; the round still
#   runs and still commits, it just leaves no out-of-repo copy.
#
# COMPLETION NOTIFICATION
#   `claude --bg` outlives this script — the launcher exits in about a second while the round goes on
#   for tens of minutes. So the launcher's exit says NOTHING about the run. It detaches
#   watch_agent.py, which polls `claude agents --json --all` until this run stops and then reports,
#   with --head-repo pointed at the instance so the report can say whether the round committed.
#   Wholly optional: with no executable notifier the watcher is skipped and the launch is unaffected.
#   Override the pair with LAUNCH_EVALS_WATCHER / LAUNCH_EVALS_NOTIFIER.
#
# WATCHER LOG
#   The watcher's stdout+stderr go to a per-launch file under the instance's system/logs/, not to
#   /dev/null. A detached process has nowhere else to put it — nobody reads its exit code — so a failed
#   send and a crashed watcher would both be perfectly silent otherwise. One file per launch,
#   timestamped, so the next launch cannot overwrite the evidence of the one that went wrong.
#
# PERMISSIONS / CONTEXT
#   The run is pinned, so it reads no project settings of its own: it takes the pin's hook wiring
#   and this instance's .claude/settings.local.json — where the allow list and defaultMode live —
#   merged into one --settings file (agent_run.py). Read that file for what is actually allowed; an
#   enumeration here is a copy free to drift.
#
#   --permission-mode auto — REQUIRED. Nobody can answer a permission prompt in a --bg run, so a prompt
#   is not a pause: it is a run that stops forever. The inherited `acceptEdits` auto-approves file EDITS
#   only; every Bash command that does not match a static allow rule still asks, and a static rule
#   cannot match a command containing a $variable. `auto` puts a classifier on each call instead. NOT a
#   bypass: deny and ask rules still apply, and this is not --dangerously-skip-permissions (see
#   ~/.claude/CLAUDE.md § Permission mode). It must be the flag: `defaultMode: "auto"` is IGNORED in
#   project and local settings.
#
#   --allowedTools — still NOT passed: CLI --allowedTools REPLACES (not merges) the settings allow list
#   and would strip Skill/WebSearch/MCP and break the run. Never pass --bare (that skips settings.json).
#   Use --bg, NOT -p/--print. --print runs headless and never starts the interactive session
#   `claude agents` attaches to. The prompt is the positional argument under --bg.
#
# USAGE
#   <CORE>/launchers/launch-skill-evals/launcher.sh <skill> [--dry-run] [--keep-awake] [--force]
#     <skill>       a skill name carrying evals/evals.json
#     --dry-run     print the round + the exact claude command, but do not launch
#     --keep-awake  keep the Mac awake (caffeinate) for the run's duration; needs a notifier/watcher
#     --force       launch even if another eval round is already live (see the refusal block above)
#
set -euo pipefail

# --- resolve the instance root (the caller's cwd) and cd there ----------------------
#   This tool lives in <CORE>/launchers/launch-skill-evals/ and is shared across instances, so it
#   CANNOT derive its instance from its own location. The instance is the caller's cwd;
#   --instance-root overrides. The cd is load-bearing: `claude --bg` inherits THIS shell's cwd, and
#   stage_fixtures.py writes a repo-RELATIVE Product path that only resolves from the repo root.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # <CORE>/launchers/launch-skill-evals
CORE_DIR="${SCRIPT_DIR%/launchers/*}"
[ "$CORE_DIR" != "$SCRIPT_DIR" ] || { echo "launch-skill-evals: no /launchers/ ancestor above $SCRIPT_DIR — refusing to guess <CORE>" >&2; exit 1; }
SCRIPT_PATH="$SCRIPT_DIR/$(basename "${BASH_SOURCE[0]}")"
# shellcheck source=/dev/null
source "$CORE_DIR/tools/pin_run.sh"
pin_enter "$CORE_DIR" "$SCRIPT_PATH" "$@" || exit $?
INSTANCE_ROOT="$PWD"
[ "${1:-}" = "--instance-root" ] && { INSTANCE_ROOT="$2"; shift 2; }
cd "$INSTANCE_ROOT"
INSTANCE_ROOT="$PWD"   # re-resolved absolute, even when --instance-root was given relative

WATCHER="${LAUNCH_EVALS_WATCHER:-$CORE_DIR/tools/watch_agent.py}"
NOTIFIER="${LAUNCH_EVALS_NOTIFIER:-${KENSAIAPP_NOTIFIER:-}}"
RESOLVER="${LAUNCH_EVALS_RESOLVER:-$CORE_DIR/tools/skill_path.py}"

# The shared completion-watch home — the second core-relative path this launcher resolves,
# at the same real depth as WATCHER above. No env override: unlike $WATCHER, no test or
# caller ever wants a stub in its place, only the real file at its real relative depth.
DETACH_LIB="$CORE_DIR/tools/detach_watcher.sh"
# The shared telemetry-instrument home — same real depth as DETACH_LIB above. No env
# override, for the same reason: no test or caller ever wants a stub in its place, only
# the real file at its real relative depth.
INSTRUMENT_LIB="$CORE_DIR/tools/run_telemetry.sh"
# The one resolution of a run's model, effort and source, shared by every instrumented
# launcher — same real depth, and no env override for the same reason.
RUN_INTELLIGENCE="$CORE_DIR/tools/run_intelligence.py"
# The one reader of the provider file — same real depth, and no env override: no caller may point
# a launch at another file.
PROVIDERS_TOOL="$CORE_DIR/tools/providers.py"

die() { echo "launch-skill-evals: $*" >&2; exit 1; }

# --- args --------------------------------------------------------------------------
skill="${1:-}"
dry_run=""
keep_awake=""
force=""
for arg in "${@:2}"; do
  case "$arg" in
    --dry-run)    dry_run=1 ;;
    --keep-awake) keep_awake=1 ;;
    --force)      force=1 ;;
  esac
done
[ -n "$skill" ] || die "usage: launch-skill-evals <skill> [--dry-run] [--keep-awake] [--force]"
case "$skill" in
  */*|.*) die "'$skill' is a skill NAME, not a path" ;;
esac

# --- the provider: this launcher's entry in .providers.toml at the instance root ---
#   Read before the skill or any round is looked at, so a launch the file cannot serve is refused
#   before anything else, and a dry run is refused exactly where the launch would be. The run is a
#   Claude workflow: the reader is asked to accept `claude` and refuses any other entry by name. No
#   force is read — an exported KENSAIAPP_AGENT_PROVIDER is ignored here. The key is this
#   launcher's own folder name as a literal. `providers.py` imports the intelligence resolver, so
#   both are checked before the reader is run.
[ -f "$PROVIDERS_TOOL" ] || die "no provider reader at $PROVIDERS_TOOL"
[ -f "$RUN_INTELLIGENCE" ] || die "no intelligence resolver at $RUN_INTELLIGENCE"
provider_err="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-skill-evals-provider.XXXXXX")"
provider="$(python3 "$PROVIDERS_TOOL" launcher launch-skill-evals --instance-root "$INSTANCE_ROOT" --accept claude 2>"$provider_err")" && rc=0 || rc=$?
provider_msg="$(cat "$provider_err")"
rm -f "$provider_err"
[ "$rc" -eq 0 ] || die "${provider_msg:-could not read the provider for the launch-skill-evals launcher}"

resolved_err="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-resolve-err.XXXXXX")"
resolved="$(python3 "$RESOLVER" "$skill" --root "$INSTANCE_ROOT" 2>"$resolved_err")" && rc=0 || rc=$?
case $rc in
  0) skill_dir="$resolved" ;;
  3) die "no skill at $INSTANCE_ROOT (is '$skill' a real skill in this instance?)" ;;
  4) die "'$skill' is ambiguous — $(cat "$resolved_err")" ;;
  *) die "usage: launch-skill-evals <skill> [--dry-run] [--keep-awake] [--force]" ;;
esac
rm -f "$resolved_err"
evals_json="$skill_dir/evals/evals.json"
[ -f "$evals_json" ] || die "no evals at $evals_json — there is nothing to benchmark for '$skill'"

# --- derive + report the round (READ-ONLY; never passed into the run) ---------------
#   The workflow numbers from the HIGHEST existing iteration, never the count — the two differ the
#   moment the sequence has a gap, and workspace/ is gitignored so an overwrite is unrecoverable. This
#   report derives the same number the same way, so the caller sees what N will be before spending it.
workspace="$skill_dir/evals/workspace"
highest=0
if [ -d "$workspace" ]; then
  for d in "$workspace"/iteration-*; do
    [ -d "$d" ] || continue
    n="${d##*/iteration-}"
    case "$n" in ''|*[!0-9]*) continue ;; esac
    [ "$n" -gt "$highest" ] && highest="$n"
  done
fi
next=$((highest + 1))
if [ "$highest" -eq 0 ]; then
  echo "Round: iteration-1 (first ever) — no iterations under $workspace"
else
  echo "Round: iteration-$next — highest existing is iteration-$highest"
  echo "      (the workflow derives this itself; this line is just for you)"
fi

PROMPT_PREFIX="run the skill-evals benchmark for the "

# --- the round lock ----------------------------------------------------------------
#   The lock's location, shape and staleness rule live in <CORE>/tools/evals_round_lock.py, which
#   launch-eval-fix reads too — one protocol, one file. This launcher only asks it questions.
LOCK_TOOL="${LAUNCH_EVALS_LOCK_TOOL:-$CORE_DIR/tools/evals_round_lock.py}"

# --- refuse to run two rounds at once ----------------------------------------------
#   Matched on the fixed prompt prefix below, so it catches an eval round for ANY skill under this
#   instance — see the refusal block at the top for why that breadth is the point. Filtered to live
#   states: a `stopped` or `blocked` agent is a finished round and must not block the next one.
if [ -z "$force" ] && [ -z "$dry_run" ]; then
  # `holder` prints the holding round or nothing, and clears a stale lock as it goes — so a killed
  # launcher, a crashed round or a rebooted Mac all leave a lock the next launch heals by itself.
  held="$(python3 "$LOCK_TOOL" --repo "$INSTANCE_ROOT" holder 2>/dev/null || true)"
  if [ -n "$held" ]; then
    echo "launch-skill-evals: an eval round is already running — $held" >&2
    die "rounds are run one at a time — two parallel fan-outs is what exhausted the session window on 2026-07-26. Wait for it, or pass --force if you mean it."
  fi
fi

# --- build the launch command: FIXED prompt, only $skill and the archive dir interpolated ---
#   Both interpolated values are launcher-derived and validated above; a caller cannot reach the
#   prompt. The preservation sentence is present only when KENSAIAPP_EVAL_HISTORY is set.
#   Kept to ASCII on purpose: --dry-run echoes the argv through `printf %q`, which renders a
#   non-ASCII byte as an escape that is no longer valid UTF-8, and any caller decoding that output
#   (the test suite does) fails on it.
prompt="${PROMPT_PREFIX}${skill} skill, whose directory is ${skill_dir}."
prompt="$prompt this run is unattended: nobody can answer a question, so decide and act."
prompt="$prompt do the skill's steps 1, 1b, 2, 2b, 2c and 3, and skip steps 4 and 5. the viewer binds a port and waits for a human to write feedback.json, and there is nobody here."
if [ -n "${KENSAIAPP_EVAL_HISTORY:-}" ]; then
  # The full destination, spelled out rather than left to be inferred. Every existing skill in the
  # history vault is keyed <skill>/evals/workspace/iteration-N — the run's path relative to its skill
  # directory, preserved — and an agent handed only the vault root has to guess at that. It guessed
  # right on 2026-07-27, which is not the same as being told.
  archive="${KENSAIAPP_EVAL_HISTORY%/}/${skill}/evals/workspace"
  prompt="$prompt then copy the run's whole iteration directory into ${archive}/, creating that directory if needed, so it lands as ${archive}/iteration-<N>/. evals/workspace/ is gitignored and does not survive this checkout, so this copy is the only lasting record of the run."
else
  archive=""
fi
prompt="$prompt then commit the round on the current branch, reporting in the commit body what the benchmark showed against the previous complete iteration. do not commit the workspace. change no skill file: deciding what a failure means is a separate pass."

# --- skill-evals's own group is no longer admitted with --add-dir (Task 17) --------
#   The prompt hands the run the skill-evals steps, and a grouped skill
#   (skills/<group>/.claude/skills/<name>/) used to be out of a session's index until its group
#   was admitted here. A Claude run reaches `skill-evals` because this launcher grants it
#   (`--grant-skill`), which puts the skill's group in the pin's plugin (agent_run.py's pin
#   delivery) instead of a directory this launcher names.

# --- the run's provenance, from the one resolution -------------------------------
#   The driver goes at the fixed tier `sonnet` (WHY A SONNET DRIVER above), so the resolver is
#   asked for that tier and its answer is both what the run is handed and what it is stamped with
#   (`source=tier`). The evaluated skill is the run's subject, not its seat: no --skill-dir, so its
#   own intelligence is never read and never moves the driver off `sonnet`.
resolution="$(python3 "$RUN_INTELLIGENCE" --provider "$provider" --tier sonnet)" \
  || die "could not resolve tier sonnet through $RUN_INTELLIGENCE"
run_model="$(printf '%s\n' "$resolution" | sed -n 's/^model=//p')"
run_effort="$(printf '%s\n' "$resolution" | sed -n 's/^effort=//p')"
run_source="$(printf '%s\n' "$resolution" | sed -n 's/^source=//p')"

# --- tag this run before it spawns (the shared instrument home) -------------------
#   Unconditional, not behind a flag — the caller sets no argument and exports no variable.
#   Called ahead of the dry-run branch too, so a dry run states the arm it would run under
#   rather than hiding the instrument; the exports it makes here die with this script when
#   --dry-run exits before anything is spawned.
if [ -f "$INSTRUMENT_LIB" ]; then
  # shellcheck source=/dev/null
  source "$INSTRUMENT_LIB"
  run_telemetry skill="$skill" provider="$provider" model="$run_model" effort="$run_effort" source="$run_source"
else
  echo "          (no instrument library at $INSTRUMENT_LIB — run uninstrumented)"
fi

# --- build the launch command: the fixed prompt, the model, and the pin's delivery -------
#   The Claude argv comes from the one adapter, never assembled here (Task 17) — the pin was
#   entered right after the CORE_DIR guard above. The model is tier sonnet's, as resolved above
#   (see WHY A SONNET DRIVER) — an explicit model choice, not a seat/agent grant the pin's plugin
#   replaces — and it is the same variable the stamp carries, so the two cannot disagree.
claude_cmd=(python3 "$CORE_DIR/tools/agent_run.py" --provider "$provider" --shape background --pin auto
  --instance-root "$INSTANCE_ROOT" --prompt "$prompt" --model "$run_model"
  --grant-skill skill-evals)
[ -z "$run_effort" ] || claude_cmd+=(--effort "$run_effort")
[ -n "${INSTRUMENT_RUN_SETTINGS:-}" ] && claude_cmd+=(--settings "$INSTRUMENT_RUN_SETTINGS")
claude_cmd+=(--print-argv)

claude_argv=()
while IFS= read -r -d '' a; do
  claude_argv+=("$a")
done < <("${claude_cmd[@]}")
set -- "${claude_argv[@]}"

if [ -n "$dry_run" ]; then
  echo "DRY RUN — would launch:"
  printf '  %q' "$@"; echo
  [ -n "$archive" ] && echo "  archive: $archive" || echo "  archive: (KENSAIAPP_EVAL_HISTORY unset — no out-of-repo copy)"
  exit 0
fi

[ -n "$archive" ] || echo "Note: KENSAIAPP_EVAL_HISTORY is unset — the round will not be archived out of repo."

# --- snapshot existing agent ids BEFORE launching ----------------------------------
#   The launched agent is identified by (name, cwd, id-not-seen-before). Name alone is ambiguous:
#   relaunching the same skill reuses the same fixed prompt. Captured before the launch, or the new
#   agent would be in its own exclusion set.
ids_before="$(python3 "$WATCHER" --list-ids --cwd "$INSTANCE_ROOT" 2>/dev/null || true)"

echo "Launching skill-evals round for '$skill' → iteration-$next (background)…"
#   stdout is captured so the launched agent's id can be recorded in the lock AND handed to the
#   watcher, then echoed through unchanged so the caller still sees `claude`'s own attach/stop
#   hints. What the launch line looks like, and the escape-stripping it needs, are the shared
#   library's problem now — see `capture_agent_id` in `<CORE>/tools/detach_watcher.sh`.
# Redirected to a FILE, never captured through a pipe. `$( … )` waits for end-of-file on the
# pipe, not for the command to exit — and `claude --bg` leaves a detached run holding the
# inherited descriptor, so a pipe capture would block this launcher for the whole run it just
# backgrounded. That is the one thing every launcher here promises not to do.
launch_log="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-launch-out.XXXXXX")"
"$@" >"$launch_log" 2>&1
launch_out="$(cat "$launch_log")"
rm -f "$launch_log"
printf '%s\n' "$launch_out"
# The parse used to live here and was the fleet's only copy; it is now the shared library's
# `capture_agent_id`, called rather than repeated. This launcher needs the VALUE before the
# detach call is reached — the round lock below is written from it — so it sources the library
# here and passes the id on as --agent-id, where a launcher that only wants a watch hands over
# --launch-output and never names the function.
agent_id=""
if [ -f "$DETACH_LIB" ]; then
  # shellcheck source=/dev/null
  source "$DETACH_LIB"
  agent_id="$(capture_agent_id "$launch_out")"
fi
if [ -n "$agent_id" ]; then
  python3 "$LOCK_TOOL" --repo "$INSTANCE_ROOT" write \
      --agent-id "$agent_id" --skill "$skill" --cwd "$INSTANCE_ROOT" --iteration "$next" \
    && echo "          Round lock:   held by agent $agent_id"
else
  # Not fatal: the round is already running and killing it would be worse than losing the guard for
  # one launch. Say so, because a silent miss here is a guard that looks armed and is not.
  echo "          (could not read the agent id from the launch output — the next launch will NOT be blocked)" >&2
fi
echo "Launched. Watch/attach: claude agents        (interactive view — logs, stop, resume live here)"
echo "          Script it:    claude agents --json --all   (machine-readable run state)"

if [ -f "$DETACH_LIB" ]; then
  # shellcheck source=/dev/null
  source "$DETACH_LIB"
  detach_completion_watcher \
    --watcher "$WATCHER" --notifier "$NOTIFIER" \
    --instance-root "$INSTANCE_ROOT" --prompt "$prompt" \
    --label "evals ${skill} iteration-${next}" --log-stem "evals-${skill}" --reporter generic \
    --head-repo "$INSTANCE_ROOT" \
    --noun round \
    --exclude-ids "$ids_before" \
    --agent-id "$agent_id" \
    --keepawake-poll-seconds "${LAUNCH_EVALS_KEEPAWAKE_POLL_SECONDS:-5}" \
    ${keep_awake:+--keep-awake}
else
  echo "          (no completion-watch library at $DETACH_LIB — completion watch skipped)"
fi
