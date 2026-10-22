#!/usr/bin/env bash
#
# launcher.sh (launch-eval-fix) — deterministic, pollution-proof launcher for the eval-fix pass.
#
# Version: 1.13.0 — the other six launchers run on the package's turn-on
# Version: 1.12.1 — launchers and launch scripts take a portable mktemp template, so they run on Linux
# Version: 1.12.0 — the providers file lives in the instance — each instance reads its own .providers.toml, and a tracked .providers.toml.example is the template
# Version: 1.11.0 — the eight skill launchers read their provider from the central providers file and refuse naming the entry when it is missing — no literal claude
# Version: 1.10.0 — the eleven other instrumented launchers stamp provider, model, effort and source through one shared resolution
# Version: 1.9.0 — a run keeps the version it started on — every launcher enters a pin of core/, .claude/ and skills/
# Version: 1.8.0 — a launcher may live nested under core/launchers/development/, and its reach resolves <CORE> from its own location instead of counting folders
# Version: 1.7.0 — a launcher-started record says which instance, product and operation it was for — instrument_run stamps them, chain.py ties a walk, and the step-name seed is parked by the owner's ruling
# Version: 1.6.0 — the backgrounded launchers are tagged too — every launcher hands its telemetry to the spawn as --settings; station 2 closes and the seed is set down
# Version: 1.5.0 — station 2's instrument lands — every launcher tags its own run, and the receiver answers only this machine
# Version: 1.4.0 — the resolver capture no longer folds stderr into the value that becomes
#   $skill_dir (was `2>&1`; a future resolver warning on a successful exit would have landed
#   INSIDE the path). Standard error is captured to its own temp file instead, read back only for
#   the ambiguous (exit 4) message, which is what it always fed. $RESOLVER also gains an env
#   override, LAUNCH_EVAL_FIX_RESOLVER, the seam a test needs to stand a stub resolver on this
#   path.
# Version: 1.3.0 — the run this launcher starts is now named to its watcher. `claude --bg`'s
#   launch output is redirected to a file (never a pipe capture, which waits for end-of-file and
#   would block on the detached run) and handed to the completion-watch library as
#   --launch-output; the library parses the id out of it with `capture_agent_id` and passes it to
#   the watcher as --agent-id, the exact handle that stops the name being consulted at all. The
#   output is still echoed through unchanged. A launch line that cannot be read yields no id and
#   the watch falls back to --name exactly as before.
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
#   LAUNCH_EVAL_FIX_KEEPAWAKE_POLL_SECONDS (default 5), sets how often that identity is re-checked.
# Version: 1.0.1 — comment: repoint the retired launch-cold-read.sh to the surviving cold-read entry.
#
# WHAT IT DOES
#   Runs the `eval-fix` workflow (.claude/workflows/eval-fix.js) over ONE settled skill-evals round:
#   the fix-author reads the benchmark and the failing runs' own output and decides, the fixer
#   applies and commits. One pass, not a loop — the check that a fix worked is the next benchmark,
#   which is its own round and costs one.
#
# WHY A LAUNCHER (same reason as ../cold-read/launcher.sh and its siblings)
#   A session asked to "act on the eval results" *composes* the driving prompt, and that is the one
#   place stray context leaks in — last round's numbers, which failures the caller thinks matter,
#   "and while you're there". The prompt below is a FIXED literal; a caller passes only a skill name,
#   and the round it resolves is derived, not typed. Nothing a caller composes reaches the run.
#
# WHY IT REFUSES WHILE A ROUND IS RUNNING
#   This pass EDITS skills. A skill edited while it is being benchmarked corrupts the measurement:
#   the executors read SKILL.md at their own pace, so some cases would run the old text and some the
#   new, and the resulting numbers describe a skill that never existed. It therefore reads the same
#   round lock launch-skill-evals writes (<CORE>/tools/evals_round_lock.py) and stands down while any
#   round holds it. Same lock, opposite side of the same rule.
#
# WHY IT RESOLVES THE ROUND ITSELF
#   The round to act on is the newest iteration that actually has a `benchmark.md`. That is not the
#   same as the newest iteration: a killed or in-flight round leaves a directory with case folders
#   and no numbers, and acting on half a round is worse than not acting. The launcher walks the
#   workspace for settled rounds and takes the highest, so a caller cannot point it at wreckage.
#
# WHY NO --agent HERE
#   The workflow spawns the postures itself — `kaizen-fix-author` (Fable, no Edit tool: it decides
#   and structurally cannot apply) and `kaizen-fixer` (Sonnet, no Write tool: it applies and
#   structurally cannot author). The driving session only invokes the Workflow tool, so its own model
#   is not load-bearing and it inherits, exactly as launch-audit.sh does.
#
# COMPLETION NOTIFICATION / WATCHER LOG / PERMISSIONS
#   Identical in shape and rationale to launch-skill-evals/launcher.sh; read that file's header for
#   the reasoning rather than a copy of it here. In brief: `claude --bg` outlives this script so a
#   detached watch_agent.py reports the ending, its output goes to a per-launch log under
#   system/logs/ because a detached process has nowhere else to put it, and --permission-mode auto is
#   required because a permission prompt in a --bg run is a run that stops forever.
#
# USAGE
#   <CORE>/launchers/launch-eval-fix/launcher.sh <skill> [--dry-run] [--keep-awake] [--force]
#     <skill>       a skill name with at least one settled round
#     --dry-run     print the resolved round + the exact claude command, but do not launch
#     --keep-awake  keep the Mac awake (caffeinate) for the run's duration; needs a notifier/watcher
#     --force       launch even while an eval round holds the lock (you are editing a skill that is
#                   being measured; the numbers from that round become unattributable)
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # <CORE>/launchers/launch-eval-fix
CORE_DIR="${SCRIPT_DIR%/launchers/*}"
[ "$CORE_DIR" != "$SCRIPT_DIR" ] || { echo "launch-eval-fix: no /launchers/ ancestor above $SCRIPT_DIR — refusing to guess <CORE>" >&2; exit 1; }
SCRIPT_PATH="$SCRIPT_DIR/$(basename "${BASH_SOURCE[0]}")"
# shellcheck source=/dev/null
source "$CORE_DIR/tools/pin_run.sh"
pin_enter "$CORE_DIR" "$SCRIPT_PATH" "$@" || exit $?
INSTANCE_ROOT="$PWD"
[ "${1:-}" = "--instance-root" ] && { INSTANCE_ROOT="$2"; shift 2; }
cd "$INSTANCE_ROOT"
INSTANCE_ROOT="$PWD"   # re-resolved absolute, even when --instance-root was given relative

WATCHER="${LAUNCH_EVAL_FIX_WATCHER:-$CORE_DIR/tools/watch_agent.py}"
NOTIFIER="${LAUNCH_EVAL_FIX_NOTIFIER:-${KENSAIAPP_NOTIFIER:-}}"

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
LOCK_TOOL="${LAUNCH_EVALS_LOCK_TOOL:-$CORE_DIR/tools/evals_round_lock.py}"
RESOLVER="${LAUNCH_EVAL_FIX_RESOLVER:-$CORE_DIR/tools/skill_path.py}"

die() { echo "launch-eval-fix: $*" >&2; exit 1; }

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
[ -n "$skill" ] || die "usage: launch-eval-fix <skill> [--dry-run] [--keep-awake] [--force]"
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
provider_err="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-eval-fix-provider.XXXXXX")"
provider="$(python3 "$PROVIDERS_TOOL" launcher launch-eval-fix --instance-root "$INSTANCE_ROOT" --accept claude 2>"$provider_err")" && rc=0 || rc=$?
provider_msg="$(cat "$provider_err")"
rm -f "$provider_err"
[ "$rc" -eq 0 ] || die "${provider_msg:-could not read the provider for the launch-eval-fix launcher}"

resolved_err="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-resolve-err.XXXXXX")"
resolved="$(python3 "$RESOLVER" "$skill" --root "$INSTANCE_ROOT" 2>"$resolved_err")" && rc=0 || rc=$?
case $rc in
  0) skill_dir="$resolved" ;;
  3) die "no skill at $INSTANCE_ROOT (is '$skill' a real skill in this instance?)" ;;
  4) die "'$skill' is ambiguous — $(cat "$resolved_err")" ;;
  *) die "usage: launch-eval-fix <skill> [--dry-run] [--keep-awake] [--force]" ;;
esac
rm -f "$resolved_err"
workspace_root="$skill_dir/evals/workspace"
[ -d "$workspace_root" ] || die "no eval runs under $workspace_root — benchmark '$skill' before fixing it"

# --- resolve the round: the highest iteration that actually SETTLED -----------------
#   "Settled" means it has a benchmark.md. An in-flight or killed round leaves case directories and
#   no numbers, and the fix-author would be reading an absence.
settled=0
for d in "$workspace_root"/iteration-*; do
  [ -f "$d/benchmark.md" ] || continue
  n="${d##*/iteration-}"
  case "$n" in ''|*[!0-9]*) continue ;; esac
  [ "$n" -gt "$settled" ] && settled="$n"
done
[ "$settled" -gt 0 ] || die "no settled round under $workspace_root — every iteration there is missing its benchmark.md (in-flight or aborted). Run a benchmark first."

# The previous settled round, for the author to compare against. Optional: a first-ever round has none.
previous=0
for d in "$workspace_root"/iteration-*; do
  [ -f "$d/benchmark.md" ] || continue
  n="${d##*/iteration-}"
  case "$n" in ''|*[!0-9]*) continue ;; esac
  [ "$n" -lt "$settled" ] && [ "$n" -gt "$previous" ] && previous="$n"
done

workspace="$workspace_root/iteration-$settled"
previous_ws=""
[ "$previous" -gt 0 ] && previous_ws="$workspace_root/iteration-$previous"

echo "Round: iteration-$settled (the newest with a benchmark.md)"
if [ "$previous" -gt 0 ]; then
  echo "       comparing against iteration-$previous"
else
  echo "       no earlier settled round to compare against"
fi

# --- stand down while a benchmark round is running ----------------------------------
if [ -z "$force" ] && [ -z "$dry_run" ]; then
  held="$(python3 "$LOCK_TOOL" --repo "$INSTANCE_ROOT" holder 2>/dev/null || true)"
  if [ -n "$held" ]; then
    echo "launch-eval-fix: an eval round is running — $held" >&2
    die "this pass edits skills, and a skill edited mid-benchmark makes that round's numbers describe a skill that never existed. Wait for it, or pass --force if you mean it."
  fi
fi

# --- build the launch command: FIXED prompt, only derived values interpolated -------
#   ASCII only: --dry-run echoes the argv through `printf %q`, which renders a non-ASCII byte as an
#   escape that is no longer valid UTF-8, and any caller decoding that output fails on it.
if [ -n "$previous_ws" ]; then
  wf_args="{ skill: \"${skill}\", workspace: \"${workspace}\", previous: \"${previous_ws}\", root: \"${INSTANCE_ROOT}\" }"
else
  wf_args="{ skill: \"${skill}\", workspace: \"${workspace}\", root: \"${INSTANCE_ROOT}\" }"
fi
prompt="Run the saved workflow named 'eval-fix' by invoking the Workflow tool with { name: \"eval-fix\", args: ${wf_args} }. Do only that, then report only the workflow's returned result."

# --- the run's provenance, from the one resolution -------------------------------
#   The workflow run is handed no model and no effort, and the skill it fixes is its subject, not
#   its seat, so that skill's intelligence is never read. The resolver is asked with no skill and
#   no tier and answers `default` with an empty pair — asked rather than assumed, so the stamp
#   below is the one answer every instrumented launcher's stamp comes from.
resolution="$(python3 "$RUN_INTELLIGENCE" --provider "$provider")" \
  || die "could not resolve the run's intelligence through $RUN_INTELLIGENCE"
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

# --- build the launch command: the fixed prompt and the pin's delivery -------------
#   The Claude argv comes from the one adapter, never assembled here (Task 17) — the pin was
#   entered right after the CORE_DIR guard above. No --agent (see WHY NO --agent ABOVE): the
#   workflow spawns its own postures, so none is passed to the adapter either.
claude_cmd=(python3 "$CORE_DIR/tools/agent_run.py" --provider "$provider" --shape background --pin auto
  --instance-root "$INSTANCE_ROOT" --prompt "$prompt")
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
  exit 0
fi

ids_before="$(python3 "$WATCHER" --list-ids --cwd "$INSTANCE_ROOT" 2>/dev/null || true)"

echo "Launching eval-fix pass for '$skill' over iteration-$settled (background)…"
# stdout is captured so the id `claude --bg` prints at launch can be read off it, then echoed
# through unchanged so the caller still sees `claude`'s own attach/stop hints. The parse is the
# completion-watch library's `capture_agent_id`, reached below via --launch-output; nothing here
# reads the line itself.
# Redirected to a FILE, never captured through a pipe. `$( … )` waits for end-of-file on the
# pipe, not for the command to exit — and `claude --bg` leaves a detached run holding the
# inherited descriptor, so a pipe capture would block this launcher for the whole run it just
# backgrounded. That is the one thing every launcher here promises not to do.
launch_log="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-launch-out.XXXXXX")"
"$@" >"$launch_log" 2>&1
launch_out="$(cat "$launch_log")"
rm -f "$launch_log"
printf '%s\n' "$launch_out"
echo "Launched. Watch/attach: claude agents        (interactive view — logs, stop, resume live here)"
echo "          Script it:    claude agents --json --all   (machine-readable run state)"

if [ -f "$DETACH_LIB" ]; then
  # shellcheck source=/dev/null
  source "$DETACH_LIB"
  detach_completion_watcher \
    --watcher "$WATCHER" --notifier "$NOTIFIER" \
    --instance-root "$INSTANCE_ROOT" --prompt "$prompt" \
    --label "eval-fix ${skill} iteration-${settled}" --log-stem "evalfix-${skill}" --reporter generic \
    --head-repo "$INSTANCE_ROOT" \
    --noun pass \
    --exclude-ids "$ids_before" \
    --launch-output "$launch_out" \
    --keepawake-poll-seconds "${LAUNCH_EVAL_FIX_KEEPAWAKE_POLL_SECONDS:-5}" \
    ${keep_awake:+--keep-awake}
else
  echo "          (no completion-watch library at $DETACH_LIB — completion watch skipped)"
fi
