#!/usr/bin/env bash
#
# launcher.sh (cold-read) — one command opens the blind cold reads over a skill's producing stack,
# and stops. It is the whole of move 1 in <CORE>/doctrine/kaizen/skills.md § Running the cold-read;
# moves 2 and 3 - commit the reports, then work the fixes - are the owner's, by hand.
#
# Version: 1.16.0 — the other six launchers run on the package's turn-on
# Version: 1.15.1 — launchers and launch scripts take a portable mktemp template, so they run on Linux
# Version: 1.15.0 — the providers file lives in the instance — each instance reads its own .providers.toml, and a tracked .providers.toml.example is the template
# Version: 1.14.1 — product-setup becomes product-card, and the stamped setup seed becomes define-the-product — so project-setup can name the front door
# Version: 1.14.0 — the eight skill launchers read their provider from the central providers file and refuse naming the entry when it is missing — no literal claude
# Version: 1.13.0 — the eleven other instrumented launchers stamp provider, model, effort and source through one shared resolution
# Version: 1.12.2 — chain skills carry their own intelligence — model and effort set per skill in intelligence/<provider>.md, no agent pins a model
# Version: 1.12.1 — the first refactor sweep of core/launchers: four behaviour-neutral packets and its report
# Version: 1.12.0 — a cold-read reads its pinned stack — the skills root resolves from the running core, not the instance
# Version: 1.11.0 — a run keeps the version it started on — every launcher enters a pin of core/, .claude/ and skills/
# Version: 1.10.1 — ad-hoc-implementation retires, and ad-hoc-flow — the launcher and workflow that ran it — retires with it
# Version: 1.10.0 — the commit instruction's Shukuba: trailer names the open station by its dated stem, per commit_format.md
# Version: 1.9.0 — a launcher may live nested under core/launchers/development/, and its reach resolves <CORE> from its own location instead of counting folders
# Version: 1.8.0 — a launcher-started record says which instance, product and operation it was for — instrument_run stamps them, chain.py ties a walk, and the step-name seed is parked by the owner's ruling
# Version: 1.7.0 — the backgrounded launchers are tagged too — every launcher hands its telemetry to the spawn as --settings; station 2 closes and the seed is set down
# Version: 1.6.0 — station 2's instrument lands — every launcher tags its own run, and the receiver answers only this machine
# Version: 1.5.0 — the resolver capture no longer folds stderr into the value that becomes
#   $skill_dir (was `2>&1`; a future resolver warning on a successful exit would have landed
#   INSIDE the path). Standard error is captured to its own temp file instead, read back only for
#   the ambiguous (exit 4) message, which is what it always fed. $RESOLVER also gains an env
#   override, LAUNCH_COLD_READ_RESOLVER, the seam a test needs to stand a stub resolver on this
#   path.
# Version: 1.4.0 — each reader's watcher is now handed that reader's own id. The launch loop
#   keeps every reader's output BY INDEX — redirected to a file, never a pipe capture, which would
#   wait for end-of-file and make this loop block on each reader in turn — and the detach loop
#   passes the matching one as --launch-output. Every reader launches under one --cwd and shares
#   one --exclude-ids snapshot, so its own id is the only thing that told it apart; a watcher
#   handed the wrong one would report on, and `claude stop`, somebody else's run.
# Version: 1.3.0 — the hand-written per-reader detach is gone: this launcher `source`s the shared
#   completion-watch home at <CORE>/tools/detach_watcher.sh and calls `detach_completion_watcher`
#   once per reader, keeping only the part that is actually about a fan-out — the array of watcher
#   identity pairs and the one keep-awake poller over them. It passes no --keep-awake to the
#   library, because the hold spans the set. Two visible consequences: each reader's own log path
#   is now printed (this launcher printed none), and the reader index sits in front of the
#   timestamp in that log's name rather than after it.
# Version: 1.2.0 — --keep-awake's fan-out poller no longer counts a pid alive by `kill -0` alone: a
#   pid the kernel reissues to an unrelated process keeps answering that check forever, so each
#   watcher's pid is now paired with the start time it had when spawned, and the poller (and the
#   caffeinate bound to it) release the moment every one of them stops matching both.
# Version: 1.1.2 — the reading-scope block drops its bullet on the lens's "read the whole producing
#   stack" clause, which the lens no longer carries.
# Version: 1.1.1 — comment: the `coldread` reporter it contrasted against is retired with the loop.
# Version: 1.1.0 — reports land in a numbered round folder, so a re-read after a fix pass never
#   writes over the round it is meant to be compared against.
#
# WHAT IT DOES
#   Reads the skill's stack.json (the ordered substance set, resolved and named against the skills
#   root — not the instance) through the shared resolver, and detaches N+1 concurrent
#   `kensaiapp-auditor` runs: one blind reader per substance file, given that file and nothing else,
#   plus — when there is more than one file — one seam reader given the whole set, whose only job is
#   what lies BETWEEN the files. Each reader writes one report and commits it. Then this script's job
#   is done. No fixing, no second read, no loop — see the plan's hard constraint
#   (docs/proposals/cold-read-launcher/ad_hoc_plan.md § Hard constraint) for why that is load-bearing,
#   not a scope note: a launcher that grows a fix step IS the retired loop under a new name.
#
# WHY A LAUNCHER (same reason as its siblings)
#   A session asked to "run the cold-read" composes the driving prompt, and that is the one place
#   stray context leaks in. Every prompt below is a FIXED template; only launcher-derived or
#   launcher-validated values are interpolated — never caller prose. Nothing a caller types can be
#   added to what any run receives.
#
# USAGE
#   <CORE>/launchers/cold-read/launcher.sh <skill> --project <project> [--dry-run] [--keep-awake]
#                                                                       (run from the instance root)
#     <skill>            a skill name carrying a stack.json (required — a
#                        single-file skill declares a one-entry manifest; see the guard below)
#     --project <p>      the managing project: derives the output directory
#                        (system/projects/<p>/docs/<skill>-coldread/round-<N>/, N one above the
#                        highest round already there) and the commit's station slug
#                        from the project's one open 宿場 Shukuba station
#     --dry-run          print every command this run would launch, in full, and launch nothing —
#                        every guard below still runs, so a dry run never reports a command it would
#                        actually refuse to run
#     --keep-awake       keep the Mac awake (caffeinate) for as long as ANY reader is still running;
#                        needs a notifier/watcher
#     --instance-root <dir>   override the instance root (default: cwd); must come first
#
# WHY EVERY GUARD IS READ-ONLY AND COSTS MILLISECONDS
#   What they guard is N+1 Opus subagents. Refuse before spending.
#
# PERMISSIONS
#   --permission-mode auto — REQUIRED on every launched run. Nobody can answer a permission prompt in
#   a --bg run, so a prompt is a run that stops forever. `auto` puts a classifier on each Bash call;
#   deny/ask rules still apply. NOT a bypass, NOT --dangerously-skip-permissions — see
#   ~/.claude/CLAUDE.md § Permission mode. No --model: the kensaiapp-auditor agent file pins
#   none since 2026-09-29, so the auditor runs on the provider's default, and which model it should
#   run on is not yet decided (core/doctrine/governance/model_assignment.md). No --allowedTools (CLI
#   --allowedTools REPLACES, not merges, the settings allow list). Use --bg, NOT -p/--print.
#
# COMPLETION NOTIFICATION
#   `claude --bg` outlives this script — its exit says nothing about any run. One completion watcher
#   is detached per reader (N+1 watchers, N+1 pings), each labelled with its own subject, because
#   watch_agent.py matches a run by its (distinct) prompt string and one watcher cannot represent a
#   set. Wholly optional: with no executable notifier every watcher is skipped and the launch is
#   unaffected. Override the pair with LAUNCH_COLD_READ_WATCHER / LAUNCH_COLD_READ_NOTIFIER.
#
set -euo pipefail

# --- resolve the instance root (the caller's cwd) and cd there ----------------------
#   This launcher lives under <CORE> and is shared across instances, so it CANNOT derive its instance
#   from its own location. The instance is the caller's cwd; --instance-root overrides. The cd is
#   load-bearing: every launched `claude --bg` run inherits THIS shell's cwd, and each reader's
#   `--repo` argument is this resolved, absolute path.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # <CORE>/launchers/cold-read
CORE_DIR="${SCRIPT_DIR%/launchers/*}"
[ "$CORE_DIR" != "$SCRIPT_DIR" ] || { echo "cold-read: no /launchers/ ancestor above $SCRIPT_DIR — refusing to guess <CORE>" >&2; exit 1; }
SCRIPT_PATH="$SCRIPT_DIR/$(basename "${BASH_SOURCE[0]}")"
# shellcheck source=/dev/null
source "$CORE_DIR/tools/pin_run.sh"
pin_enter "$CORE_DIR" "$SCRIPT_PATH" "$@" || exit $?
# The skills root — the directory above the running <CORE>: under a pin, the pin root; from a
# satellite, the host (which holds no skills of its own). Never the instance root, and the two
# can differ. By the time this line runs, pin_enter has already re-exec'd the pin's own copy, so
# CORE_DIR is already the pin's — no pin lookup of its own. Same form as the two sibling
# launchers that already read a skill's stack from here: product-card/launcher.sh:60 and
# companion-self-answer/launcher.sh:144.
SKILLS_ROOT="${LAUNCH_COLD_READ_SKILLS_ROOT:-${CORE_DIR%/core}}"
INSTANCE_ROOT="$PWD"
[ "${1:-}" = "--instance-root" ] && { INSTANCE_ROOT="$2"; shift 2; }
cd "$INSTANCE_ROOT"
INSTANCE_ROOT="$PWD"   # re-resolved absolute, even when --instance-root was given relative

# Completion-notification pair (both optional — see the watcher block near the bottom). WATCHER
# defaults to <CORE>/tools/watch_agent.py, reached via CORE_DIR — resolved from this folder's own
# location, not by counting a fixed number of parent steps. NOTIFIER carries no host-global default
# (a core tool must not hard-code a machine-local path — kensaiapp_structure.md § core/tools), so it
# comes from the environment and every ping is skipped when unset.
WATCHER="${LAUNCH_COLD_READ_WATCHER:-$CORE_DIR/tools/watch_agent.py}"
NOTIFIER="${LAUNCH_COLD_READ_NOTIFIER:-${KENSAIAPP_NOTIFIER:-}}"
# How often the fan-out keep-awake poller below re-checks every watcher's identity. The per-reader
# spawn now happens in the shared home, but the poller over the SET of them is this launcher's own,
# so this knob stays here and is read directly rather than handed to the library. Not a documented
# flag — an internal knob a test overrides to poll faster than the 5s default a real run needs.
KEEPAWAKE_POLL_SECONDS="${LAUNCH_COLD_READ_KEEPAWAKE_POLL_SECONDS:-5}"
# The second (non-silent) reach into <CORE>: manifest.py, a package under <CORE>/tools/. The
# CORE_DIR guard at the top already refused a bad resolution before this line is ever reached.
MANIFEST_LIB_DIR="$CORE_DIR/tools"
RESOLVER="${LAUNCH_COLD_READ_RESOLVER:-$CORE_DIR/tools/skill_path.py}"
# The shared completion-watch home — the third core-relative path this launcher resolves, at the
# same real depth as the two above. No env override: unlike $WATCHER, no test or caller ever wants
# a stub in its place, only the real file at its real relative depth.
DETACH_LIB="$CORE_DIR/tools/detach_watcher.sh"
# The shared telemetry-instrument home — same real depth as DETACH_LIB above. No env override,
# for the same reason: no test or caller ever wants a stub in its place, only the real file at
# its real relative depth.
INSTRUMENT_LIB="$CORE_DIR/tools/run_telemetry.sh"
# The one resolution of a run's model, effort and source, shared by every instrumented launcher —
# same real depth, and no env override for the same reason.
RUN_INTELLIGENCE="$CORE_DIR/tools/run_intelligence.py"
# The one reader of the provider file — same real depth, and no env override: no caller may point
# a launch at another file.
PROVIDERS_TOOL="$CORE_DIR/tools/providers.py"

die() { echo "cold-read: $*" >&2; exit 1; }

USAGE="usage: <CORE>/launchers/cold-read/launcher.sh <skill> --project <project> [--dry-run] [--keep-awake] [--instance-root <dir>]"

# --- args ----------------------------------------------------------------------------
#   One positional (skill) and one required flag (--project). Unknown arguments are refused, never
#   ignored — a silently ignored --dryrun would launch the full unattended fan-out the caller
#   explicitly asked not to launch.
skill=""
project=""
dry_run=""
keep_awake=""
while [ $# -gt 0 ]; do
  case "$1" in
    --project)
      case "${2:-}" in
        ""|--*) die "$USAGE" ;;
      esac
      project="$2"
      shift 2
      ;;
    --dry-run)    dry_run=1; shift ;;
    --keep-awake) keep_awake=1; shift ;;
    --*) die "unknown argument: $1 - $USAGE" ;;
    *)
      if [ -z "$skill" ]; then
        skill="$1"
        shift
      else
        die "unknown argument: $1 - $USAGE"
      fi
      ;;
  esac
done
[ -n "$skill" ] || die "$USAGE"
[ -n "$project" ] || die "$USAGE"

# A skill argument containing '/' or starting with '.' is a path, not a name — refused, never
# resolved.
case "$skill" in
  */*|.*) die "'$skill' is a skill name, not a path. $USAGE" ;;
esac

# --- the provider: this launcher's entry in .providers.toml at the instance root ---
#   Read before any skill, project, lock, lens or idea state is, so a launch the file cannot serve
#   is refused before anything is looked at, and a dry run is refused exactly where the launch
#   would be. The readers run Claude only: the reader is asked to accept `claude` and refuses any
#   other entry by name. No force is read — an exported KENSAIAPP_AGENT_PROVIDER is ignored here.
#   The key is this launcher's own folder name as a literal, never derived from SCRIPT_DIR, since
#   the script is run from other folders too. `providers.py` imports the intelligence resolver, so
#   both are checked before the reader is run.
[ -f "$PROVIDERS_TOOL" ] || die "no provider reader at $PROVIDERS_TOOL"
[ -f "$RUN_INTELLIGENCE" ] || die "no intelligence resolver at $RUN_INTELLIGENCE"
provider_err="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-cold-read-provider.XXXXXX")"
provider="$(python3 "$PROVIDERS_TOOL" launcher cold-read --instance-root "$INSTANCE_ROOT" --accept claude 2>"$provider_err")" && rc=0 || rc=$?
provider_msg="$(cat "$provider_err")"
rm -f "$provider_err"
[ "$rc" -eq 0 ] || die "${provider_msg:-could not read the provider for the cold-read launcher}"

# --- the skill + its manifest ---------------------------------------------------------
resolved_err="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-resolve-err.XXXXXX")"
resolved="$(python3 "$RESOLVER" "$skill" --root "$SKILLS_ROOT" 2>"$resolved_err")" && rc=0 || rc=$?
case $rc in
  0) skill_dir="$resolved" ;;
  3) die "no skill at $SKILLS_ROOT (is '$skill' a real skill?)" ;;
  4) die "'$skill' is ambiguous — $(cat "$resolved_err")" ;;
  *) die "$USAGE" ;;
esac
rm -f "$resolved_err"
# The skill's own directory, relative to the skills root (not the instance) — one derivation, used
# both by the no-manifest example below and by the fixed prompt's manifest sentence (:299/near)
# further down.
skill_rel="${skill_dir#"$SKILLS_ROOT"/}"

manifest_path="$skill_dir/stack.json"
[ -f "$manifest_path" ] || die "no stack.json at $manifest_path - this skill declares no substance set. A single-file skill needs a one-entry manifest, e.g.: { \"version\": 1, \"substance\": [\"$skill_rel/SKILL.md\"] }"

# Reuse manifest.py rather than re-implementing its schema/containment/existence checks in bash.
# stdout carries one validated, ordered substance path per line on success; on failure nothing goes
# to stdout, ManifestError's own text goes to stderr, and both streams are captured together below
# (safe: the two branches never write to the same stream, so the combined capture is unambiguous).
# Values cross as argv, never interpolated into the Python source: the skills root is the pin's or
# the host's path, not one this script chose, and a quote in it must stay data.
if substance_raw="$(python3 -c '
import sys
lib_dir, skill_dir, skills_root = sys.argv[1:4]
sys.path.insert(0, lib_dir)
from coldread.manifest import load_stack, ManifestError
try:
    stack = load_stack(skill_dir, root=skills_root)
except ManifestError as exc:
    print(str(exc), file=sys.stderr)
    sys.exit(1)
for path in stack.substance:
    print(path)
' "$MANIFEST_LIB_DIR" "$skill_dir" "$SKILLS_ROOT" 2>&1)"; then
  :
else
  die "$substance_raw"
fi

substance=()
while IFS= read -r line; do
  [ -n "$line" ] && substance+=("$line")
done <<SUBSTANCE_EOF
$substance_raw
SUBSTANCE_EOF
substance_count=${#substance[@]}

# --- the project + its one open station -----------------------------------------------
project_md="$INSTANCE_ROOT/system/projects/$project/project.md"
[ -f "$project_md" ] || die "no project card at $project_md (is '$project' a real project?)"

# Containment: system/projects/<project> must resolve inside the instance root (rejects a
# symlink-out project).
root_real="$(cd "$INSTANCE_ROOT" && pwd -P)"
project_real="$(cd "$INSTANCE_ROOT/system/projects/$project" && pwd -P)"
case "$project_real/" in
  "$root_real"/*) : ;;
  *) die "project '$project' resolves outside the instance root ($root_real) via a symlink; refusing" ;;
esac

# The station is the single *.md file at depth 1 of the project's shukuba folder that is not
# README.md — trail/ and parked/ are directories and are excluded by the depth-1 file match.
shukuba_dir="$project_real/journey/shukuba"
stations=()
if [ -d "$shukuba_dir" ]; then
  while IFS= read -r f; do
    [ -n "$f" ] && stations+=("$f")
  done < <(find "$shukuba_dir" -maxdepth 1 -type f -name '*.md' ! -name 'README.md' 2>/dev/null | sort)
fi
station_count=${#stations[@]}
[ "$station_count" -ge 1 ] || die "no station is open under $shukuba_dir - the commit's directional trailer needs one open station to derive its slug from"
if [ "$station_count" -gt 1 ]; then
  offenders="$(printf '%s, ' "${stations[@]}")"
  die "$station_count stations open under $shukuba_dir (expected exactly one): ${offenders%, }"
fi
station_file="${stations[0]}"
# The whole filename stem, date included: commit_format.md § Directional trailer names a station by
# its dated stem, since one project may hold two stations under one bare slug.
station_slug="$(basename "$station_file" .md)"

# --- the round (derived, not chosen) --------------------------------------------------
#   A cold-read is re-run after every fix pass, so round N's reports and round N-1's are
#   different evidence about different text — the comparison between them IS the answer to
#   "did the fix land?". One path per skill would destroy the earlier round silently and
#   leave nothing to compare. So each run gets its own numbered folder.
#
#   Numbered from the HIGHEST existing round, never the count: a round removed by hand must
#   not let this run reuse a number a real round already carries. Same rule, same reason, as
#   <CORE>/launchers/launch-skill-evals/launcher.sh's iteration numbering and
#   <CORE>/tools/auditrun/rounds.py's refuse-to-overwrite guard.
#
#   A name that is not `round-<digits>` is not a round — an owner's own folder sitting
#   beside them is ignored rather than being a reason to fail.
coldread_dir="$project_real/docs/${skill}-coldread"
highest_round=0
if [ -d "$coldread_dir" ]; then
  for d in "$coldread_dir"/round-*; do
    [ -d "$d" ] || continue
    n="${d##*/round-}"
    case "$n" in
      ''|*[!0-9]*) continue ;;
    esac
    [ "$((10#$n))" -gt "$highest_round" ] && highest_round=$((10#$n))
  done
fi
round=$((highest_round + 1))

# --- output directory + report filenames (derived, not chosen) ------------------------
output_dir="$coldread_dir/round-${round}"
report_rel="system/projects/$project/docs/${skill}-coldread/round-${round}"

report_paths=()
for i in "${!substance[@]}"; do
  idx=$((i + 1))
  base="$(basename "${substance[$i]}")"
  base_noext="${base%.*}"
  base_lower="$(printf '%s' "$base_noext" | tr '[:upper:]' '[:lower:]')"
  nn="$(printf '%02d' "$idx")"
  # relative to $INSTANCE_ROOT, matching every other derived path this script uses
  report_paths+=("$report_rel/${nn}_${base_lower}.md")
done

with_seam=""
seam_report=""
if [ "$substance_count" -gt 1 ]; then
  with_seam=1
  seam_report="$report_rel/seam.md"
fi

# --- report (READ-ONLY; never passed into any run) -------------------------------------
seam_note=""
[ -n "$with_seam" ] && seam_note=", plus one seam reader"
echo "Cold-read: skill '$skill', project '$project', station '$station_slug' - round ${round}, ${substance_count} substance file(s)${seam_note}."
for i in "${!substance[@]}"; do
  f="${substance[$i]}"
  # $f is a substance path, repo-relative to SKILLS_ROOT (manifest.py's `root=`, Task 1) — the
  # skill's own copy is the one whose starting version this reports, never the instance's.
  f_abs="$SKILLS_ROOT/$f"
  ver="$(grep -m1 -E '^[[:space:]]*version:' "$f_abs" | sed -E 's/^[[:space:]]*version:[[:space:]]*"?([^"]*)"?[[:space:]]*$/\1/' || true)"
  echo "  [$((i + 1))] $f  (starting v${ver:-unknown}) -> ${report_paths[$i]}"
done
[ -n "$with_seam" ] && echo "  [seam] all $substance_count substance file(s) -> $seam_report"

# --- the three fixed prompts ------------------------------------------------------------
#   Names the job, the subject, the scope adaptation, where the report goes, and how it commits.
#   Never restates the lens or the contract (the kensaiapp-auditor agent loads both itself) and
#   never asks for a fix — the hard constraint this whole launcher exists to hold
#   (ad_hoc_plan.md § Hard constraint). Every interpolated value below is Task 1's own derived or
#   validated output; no caller argv reaches either template.
#
# The commit instruction + retry rule are identical in both templates but for the --add path and
# --subject wording, so they are built once and appended to whichever body calls for them.
_commit_and_retry_block() {
  # arg: <report-path> <subject-topic>
  local report_path="$1" topic="$2"
  cat <<COMMIT_EOF
Then commit that ONE file, and nothing else, through the builder:
    python3 "$CORE_DIR/tools/commit_builder.py" --repo "$INSTANCE_ROOT" commit --add "$report_path" --actor kensaiapp-auditor --directional "Shukuba: $station_slug — progress: <one line of your own, about what you found>" --subject "<a short subject line you write, about $topic>" --body "<a short body you write>" --surface "Claude Code" --co-authored-by "Claude <noreply@anthropic.com>"
Compose the --subject, the --body, and the text after "progress:" yourself, in your own words, about your own read. Everything else in that command is fixed exactly as shown.

Other readers may be committing to this same repo at this same moment. If that command is refused, and the refusal names a path that is not $report_path, that means another reader staged in between — this is expected, not an error. Re-run the IDENTICAL command again, unchanged. A refusal makes no commit and leaves your own staging exactly where it was, so retrying is safe. Wait a different number of seconds before each retry — never the same interval twice, and never immediately — and retry at most 5 times total. Never add any extra flag to that command, especially not one that would skip the check keeping your commit scoped to your own report: the builder calls that check the staged-set guard, and its --take-index flag is exactly the waiver for it — do not pass it, ever. If all 5 attempts are refused, report the last refusal's text verbatim and stop.

Then stop.
COMMIT_EOF
}

compose_file_prompt() {
  # args: <index 1-based> <substance-path> <report-path>
  local idx="$1" path="$2" report_path="$3"
  local seam_note="" other_reader_note=""
  if [ -n "$with_seam" ]; then
    # with_seam is set exactly when substance_count > 1, i.e. exactly when other readers exist —
    # a single-substance skill has one reader total, so there is no "other reader" to mention.
    seam_note=" — and a third reader is comparing this file against the others at the seam, if one is running for this stack"
    other_reader_note=" Do not read another reader's report, including the seam reader's if one is running — every reader in this run is blind to every other reader's report."
  fi
  cat <<FILE_PROMPT_EOF
You are doing a blind cold-read, as one of several independent readers over the '$skill' skill's producing stack — a kaizen step 2 read. Load your own contract and your own lens first, exactly as your agent instructions already tell you to; nothing here restates either of them.

YOUR SUBJECT — the ONE file under judgment, and the only file you inventory or rank findings in:
    $SKILLS_ROOT/$path
This is entry $idx of $substance_count in $skill_rel/stack.json.

READING SCOPE — hold this line exactly:
  - One file is under judgment: the path above. Any OTHER file in the instance may be opened and read AS EVIDENCE about it — to resolve a path, field or flag it references, or to name the owner of a fact it states (the lens requires this: "name the owner, or you have no finding"). Doing that is expected, not a deviation.
  - No other file is a subject. Do not inventory it, do not rank findings in it, do not judge it, and do not treat it as the ruler your subject is measured against.
  - The counterpart substance file(s) of this same stack.json are not read for content at all — existence and how they are named, nothing more. A different reader is judging each of them right now, blind to you as you are to them${seam_note}.
  - No sibling comparison: do not ask which mechanics THIS skill's stack carries that a different skill's does not — that is a separate question for a separate moment, never this round. The one allowance: once you have already named the owner of a fact, naming a further file that also carries it is ownership evidence, and that is fine.

Report what you opened: your report needs a resolution table naming every file you opened beyond your subject and what you checked in it there — that is what makes the line above auditable rather than assumed.

Open your report with a header naming: the absolute target above, with its version and line count; the lens and contract versions you loaded; the reading-scope line above, in your own words; and that no artifact, product, prior round or suspicion was supplied to you.

Do not fix anything. Do not read your subject a second time.${other_reader_note}

Write your report to exactly: $INSTANCE_ROOT/$report_path

FILE_PROMPT_EOF
  _commit_and_retry_block "$report_path" "this file's read"
}

compose_seam_prompt() {
  # arg: <seam-report-path>
  local report_path="$1"
  local subject_lines=""
  local i
  for i in "${!substance[@]}"; do
    subject_lines="${subject_lines}  - $SKILLS_ROOT/${substance[$i]}
"
  done
  cat <<SEAM_PROMPT_EOF
You are doing a blind cold-read, as the SEAM reader over the '$skill' skill's producing stack — a THIRD, DIFFERENT job from the per-file cold reads running concurrently with you right now. Your instructions here are NOT the same as theirs; do not assume they are, and do not read theirs to find out. Load your own contract and your own lens first, exactly as your agent instructions already tell you to; nothing here restates either of them.

YOUR SUBJECT SET — read together, as evidence about each other:
${subject_lines}
THE ONLY QUESTION YOU ARE ANSWERING: does anything in this stack contradict something else in it, or does one file assume a rule, field or behaviour that only a DIFFERENT file in this stack actually states? A rule one file assumes without the other stating it. A place the two disagree. That is your whole job, and nothing else is.

THE TEST for whether a finding is yours: if the finding does NOT need BOTH files to state it — if a reader holding only one of them could have found it alone — it is not yours. Leave it; a per-file reader already holds that file.

PROHIBITIONS — none of the per-file readers carry these in this form, because their job is different from yours:
  - Do not inventory either file. You are not producing a per-file finding list for either one.
  - Do not re-rank or restate anything a reader holding only one of these files would already have found alone.
  - Do not treat either file as the ruler the other is measured against, and do not treat either file as a subject in the per-file sense — your subject is the RELATIONSHIP between them, not either file itself.
  - No sibling comparison against a different skill's stack.

READING SCOPE — the same line the per-file readers hold, drawn for your job: any OTHER file in the instance may be opened and read AS EVIDENCE about the relationship between the files above — to resolve a path, field or flag one of them references, or to name the owner of a fact one of them states (the lens requires this: "name the owner, or you have no finding"). Doing that is expected, not a deviation. What it never becomes is a subject: nothing you open that way is inventoried, ranked, judged, or used as the ruler this stack is measured against.

Report what you opened: your report needs a resolution table naming every file you opened beyond the subject set above and what you checked in it there — that is what makes the line above auditable rather than assumed.

The per-file readers are reading these same files right now, one per file, blind to you and to each other. Their reports will land beside yours. Do not read either of their reports — you are blind to their findings exactly as they are to yours and to each other.

Do not fix anything. Do not re-read a file a second time once you have read it once.

Open your report with a header naming: each of the absolute targets above, with its version and line count; the lens and contract versions you loaded; that your job is the seam between them, not either file alone; and that no artifact, product, prior round or suspicion was supplied to you.

Write your report to exactly: $INSTANCE_ROOT/$report_path

SEAM_PROMPT_EOF
  _commit_and_retry_block "$report_path" "the seam"
}

prompts=()
targets=()
labels=()
for i in "${!substance[@]}"; do
  idx=$((i + 1))
  prompts+=("$(compose_file_prompt "$idx" "${substance[$i]}" "${report_paths[$i]}")")
  targets+=("${report_paths[$i]}")
  labels+=("$(basename "${substance[$i]}")")
done
if [ -n "$with_seam" ]; then
  prompts+=("$(compose_seam_prompt "$seam_report")")
  targets+=("$seam_report")
  labels+=("seam")
fi

#   Each prompt is a long structured document, not a short copy-paste one-liner (unlike the sibling
#   launchers' single-line prompts), so --dry-run prints it RAW rather than `%q`-escaped — that is
#   what "prints every command it would run, in full" means for a prompt shaped like this, and it is
#   what lets a reader (human or test) grep the actual text instead of an escaped blob. The real
#   launch below passes the same text as a plain argv string; nothing about its content changes.

# --- the run's provenance, from the one resolution ---------------------------------
#   The readers are handed no model and no effort, and the audited skill's own intelligence is
#   never read: that skill is the reading's subject, not its seat, and its model would put the
#   audit at the audited skill's intelligence. So the resolver is asked with no skill and no tier,
#   and answers `default` with an empty pair — asked rather than assumed, so the stamp below is the
#   one answer every instrumented launcher's stamp comes from.
resolution="$(python3 "$RUN_INTELLIGENCE" --provider "$provider")" \
  || die "could not resolve the run's intelligence through $RUN_INTELLIGENCE"
run_model="$(printf '%s\n' "$resolution" | sed -n 's/^model=//p')"
run_effort="$(printf '%s\n' "$resolution" | sed -n 's/^effort=//p')"
run_source="$(printf '%s\n' "$resolution" | sed -n 's/^source=//p')"

# --- tag this fan-out before it spawns (the shared instrument home) ----------------
#   Called ONCE, before the loop below. It leaves one --settings value and every reader's spawn
#   line carries it — an exported variable never reaches a `claude --bg` session (measured
#   2026-09-10) — so one call tags the whole fan-out rather than one call per reader.
#   Unconditional and ahead of the dry-run branch too, so a dry run states the arm it would run
#   under rather than hiding the instrument.
if [ -f "$INSTRUMENT_LIB" ]; then
  # shellcheck source=/dev/null
  source "$INSTRUMENT_LIB"
  run_telemetry skill="$skill" project="$project" provider="$provider" model="$run_model" effort="$run_effort" source="$run_source"
else
  echo "          (no instrument library at $INSTRUMENT_LIB — run uninstrumented)"
fi

# The Claude argv for one reader, built through the one adapter (Task 17) — never assembled here.
# The pin was entered right after the CORE_DIR guard above; --agent stays kensaiapp-auditor for
# every reader, and INSTRUMENT_RUN_SETTINGS (set once, above) is handed to the adapter as the
# caller's own --settings rather than appended a second time, since it folds into the pin's one
# merged document. Result lands in the global READER_ARGV array — a function return value would
# need to be re-split on some delimiter, which is exactly the ambiguity a prompt carrying
# embedded newlines and NULs cannot survive.
_reader_argv() {
  local prompt="$1"
  local cmd=(python3 "$CORE_DIR/tools/agent_run.py" --provider "$provider" --shape background --pin auto
    --instance-root "$INSTANCE_ROOT" --prompt "$prompt" --agent kensaiapp-auditor)
  [ -n "${INSTRUMENT_RUN_SETTINGS:-}" ] && cmd+=(--settings "$INSTRUMENT_RUN_SETTINGS")
  cmd+=(--print-argv)
  READER_ARGV=()
  while IFS= read -r -d '' a; do
    READER_ARGV+=("$a")
  done < <("${cmd[@]}")
}

if [ -n "$dry_run" ]; then
  echo "DRY RUN - would launch ${#prompts[@]} run(s):"
  for i in "${!prompts[@]}"; do
    echo "----- [${labels[$i]}] -> ${targets[$i]} -----"
    # The real argv, built through the one adapter (Task 17) — carries the pin delivery this
    # launcher never assembles by hand. The prompt token is shown as a placeholder here and
    # printed RAW on its own line below, exactly as before: these prompts are long structured
    # documents, not a copy-paste one-liner, and %q-escaping one would turn it into a blob no
    # reader (human or test) could grep.
    _reader_argv "${prompts[$i]}"
    line=""
    next_is_agents_json=""
    for a in "${READER_ARGV[@]}"; do
      if [ "$a" = "${prompts[$i]}" ]; then
        line="${line}<prompt below> "
      elif [ -n "$next_is_agents_json" ]; then
        # --agents carries the whole instance's agent roster inline, as JSON text — not a path.
        # Printed raw it would swamp the block with unrelated agent names and descriptions this
        # reader's own prompt never mentions, which is exactly what this dry run must not lie
        # about containing (the real value is what a real launch sends; proven separately by
        # test_cold_read_every_reader_carries_the_delivery).
        line="${line}<agents json> "
        next_is_agents_json=""
      else
        [ "$a" = "--agents" ] && next_is_agents_json=1
        line="${line}$(printf '%q' "$a") "
      fi
    done
    echo "${line% }"
    echo "${prompts[$i]}"
    echo "----- end [${labels[$i]}] -----"
  done
  exit 0
fi

# Created once the guards pass, before any run launches — but only on a real launch. A dry run
# reports what would happen and touches nothing, so this waits until past the --dry-run exit above
# (an improvement over the plan's own named-resources table, which reads "before any launch" as
# unconditional; a directory materializing on disk from a run that launched nothing is a dry run
# with a side effect, which is the one thing "dry" promises not to have).
mkdir -p "$output_dir"

# --- launch, one completion watcher per reader, and --keep-awake ----------------------
#   Snapshotted BEFORE the first launch — captured after, the newest run would sit inside its own
#   exclusion set and a watcher could match a stale one instead. One list-ids call for the whole fan-out; every watcher below is handed
#   the same exclusion set.
ids_before="$(python3 "$WATCHER" --list-ids --cwd "$INSTANCE_ROOT" 2>/dev/null || true)"

# `claude --bg` returns at launch, not at completion, so firing
# these sequentially in the foreground does not make the launcher wait on any of them — each call
# returns almost immediately, the actual run continues detached. There is no --wait and no
# sequencing between readers: they are blind to each other by construction (Task 2), and nothing
# here makes one depend on another.
# Each launch's stdout is captured and kept BY INDEX, then echoed through unchanged so the caller
# still sees `claude`'s own attach/stop hints. The index is the whole point: every reader launches
# under the same `--cwd` and shares one `--exclude-ids` snapshot, so nothing but its own id tells
# a reader apart, and a watcher handed the wrong one would report on — and `claude stop` —
# somebody else's run. The parse is the shared library's; nothing here reads the line.
launch_outs=()
for i in "${!prompts[@]}"; do
  # Redirected to a FILE, never captured through a pipe: `$( … )` waits for end-of-file on the
  # pipe rather than for the command to exit, and `claude --bg` leaves a detached reader holding
  # the inherited descriptor — so a pipe capture would make this loop wait on each reader in turn,
  # which is the one thing the fan-out promises not to do.
  _reader_argv "${prompts[$i]}"
  launch_log="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-launch-out.XXXXXX")"
  "${READER_ARGV[@]}" >"$launch_log" 2>&1
  launch_out="$(cat "$launch_log")"
  rm -f "$launch_log"
  printf '%s\n' "$launch_out"
  launch_outs+=("$launch_out")
done
echo "Launched ${#prompts[@]} cold-read run(s) for skill '$skill'."
echo "Watch/attach: claude agents        (interactive view — logs, stop, resume live here)"
echo "          Script it:    claude agents --json --all   (machine-readable run state)"

# One watcher per run, not one for all: watch_agent.py matches a run by its (distinct, per Task 2)
# prompt string, so a single watcher cannot represent a set of N+1 runs. Each gets its own log file
# — a detached process has nowhere else to put its output and nobody reads its exit code, so a
# failed send and a crashed watcher would both be silent otherwise. `--reporter generic`: the report
# is the entire product here (a committed file), and this shape produces no run-outcome sentinel for
# any other reporter to read.
#
# The per-reader spawn, its log naming and its two report lines are the shared home's
# (<CORE>/tools/detach_watcher.sh), called once per reader — the split that file's own header
# describes. What stays here is the only part that is actually about a fan-out: the array of
# identity pairs and the ONE keep-awake poller over them, below. So `--keep-awake` is deliberately
# NOT passed to the library: the hold this launcher wants spans the set, not any one member of it.
#
# The reader index moves in FRONT of the timestamp in the log name (the library builds
# `watch-<stem>-<ts>.log`, so the stem is the only place it can go). It is not decoration: `labels`
# are `basename` values, so a stack holding two same-named files produces two readers with one
# subject, and the index is what keeps their logs apart.
watcher_pids=()
watcher_starts=()
if [ -f "$DETACH_LIB" ]; then
  # shellcheck source=/dev/null
  source "$DETACH_LIB"
  for i in "${!prompts[@]}"; do
    subject="${labels[$i]}"
    detach_completion_watcher \
      --watcher "$WATCHER" --notifier "$NOTIFIER" \
      --instance-root "$INSTANCE_ROOT" --prompt "${prompts[$i]}" \
      --label "cold-read $skill $subject" \
      --log-stem "cold-read-${skill}-${subject//\//_}-${i}" \
      --reporter generic \
      --exclude-ids "$ids_before" \
      --launch-output "${launch_outs[$i]}"
    # Collected as a PAIR. The pid alone is not a handle — the kernel reissues pid numbers — so the
    # library publishes the start time it captured at the spawn beside it, which is the half this
    # launcher could not safely re-derive: a `ps` run out here would already be inside the reissue
    # window. An else-branch call publishes both empty, which is what leaves these arrays empty and
    # sends the keep-awake below down its "no completion watcher" path.
    [ -n "$DETACH_WATCHER_PID" ] || continue
    watcher_pids+=("$DETACH_WATCHER_PID")
    watcher_starts+=("$DETACH_WATCHER_START")
  done
else
  echo "          (no completion-watch library at $DETACH_LIB - completion watch skipped)"
fi

# --keep-awake binds ONE caffeinate to the WHOLE fan-out, not one per reader (the fan-out is the
# unit whose duration matters). The watcher pids are children of THIS shell, and `wait <pid>` only
# works on a shell's own direct children — a freshly forked subshell cannot wait on a sibling's
# children — so a detached poller (not `wait`) is what stays alive for exactly as long as any
# watcher does.
#
# The poller's OWN liveness test used to be `kill -0 <pid>` — blind to identity: once a reader's
# watcher exits and the kernel reissues its pid to an unrelated process, `kill -0` keeps answering
# true and the poller (and the caffeinate bound to it) never release. Each watcher's pid is paired
# with the start time it had when this fan-out spawned it — a value a reissued pid cannot forge —
# and the poller counts a pid alive only while a live process still answers to both.
if [ -n "$keep_awake" ]; then
  if [ ${#watcher_pids[@]} -eq 0 ]; then
    echo "          (keep-awake needs a completion watcher — set KENSAIAPP_NOTIFIER — not staying awake)"
  elif command -v caffeinate >/dev/null 2>&1; then
    records=""
    for idx in "${!watcher_pids[@]}"; do
      records+="${watcher_pids[$idx]}::${watcher_starts[$idx]}"$'\n'
    done
    nohup caffeinate -i -s >/dev/null 2>&1 &
    keepawake_pid=$!
    nohup bash -c '
      keepawake_pid="$1"; poll_seconds="$2"; records="$3"
      while true; do
        alive=0
        while IFS= read -r line; do
          [ -z "$line" ] && continue
          p="${line%%::*}"
          start="${line#*::}"
          current="$(ps -o lstart= -p "$p" 2>/dev/null || true)"
          [ -n "$current" ] && [ "$current" = "$start" ] && alive=1
        done <<< "$records"
        [ "$alive" -eq 0 ] && break
        sleep "$poll_seconds"
      done
      kill "$keepawake_pid" 2>/dev/null
    ' bash "$keepawake_pid" "$KEEPAWAKE_POLL_SECONDS" "$records" >/dev/null 2>&1 &
    echo "          Keep-awake:   caffeinate -i -s held until the whole fan-out stops"
  else
    echo "          (keep-awake: caffeinate not found — not macOS? — skipped)"
  fi
fi
