#!/usr/bin/env bash
#
# launcher.sh (seeds-from-idea) — deterministic, pollution-proof launcher for a `seeds-from-idea`
# run: cutting one idea into 根回し Nemawashi seeds from a shell.
#
# Version: 1.8.1 — launchers and launch scripts take a portable mktemp template, so they run on Linux
# Version: 1.8.0 — the providers file lives in the instance — each instance reads its own .providers.toml, and a tracked .providers.toml.example is the template
# Version: 1.7.1 — the flat .claude/skills/ root empties to companion-self-answer: acceptance-fdr removed, shukuba-park to pm (PM-gated, closes a station it finds reached), verify-before-claim to developer, development-audit to a kensaiapp-auditor group, _shared split into core
# Version: 1.7.0 — a pinned run sees only its own skill group
# Version: 1.6.0 — the eight skill launchers read their provider from the central providers file and refuse naming the entry when it is missing — no literal claude
# Version: 1.5.0 — the eleven other instrumented launchers stamp provider, model, effort and source through one shared resolution
# Version: 1.4.0 — a run keeps the version it started on — every launcher enters a pin of core/, .claude/ and skills/
# Version: 1.3.4 — ad-hoc-implementation retires, and ad-hoc-flow — the launcher and workflow that ran it — retires with it
# Version: 1.3.3 — seeds-from-idea and ad-hoc-plan move to the interactive group, so a group answers which session reaches for a skill and not only which seat owns it
# Version: 1.3.2 — every seat-gated skill whose seat has a group now sits in it, and the grouping's own record is corrected where it overclaimed
# Version: 1.3.1 — chain-definition, chain-foundation and the eight product document launchers are retired into chain-product and the skill launcher
# Version: 1.3.0 — a launcher may live nested under core/launchers/development/, and its reach resolves <CORE> from its own location instead of counting folders
# Version: 1.2.0 — the backgrounded launchers are tagged too — every launcher hands its telemetry to the spawn as --settings; station 2 closes and the seed is set down
# Version: 1.1.0 — station 2's instrument lands — every launcher tags its own run, and the receiver answers only this machine
# Version: 1.0.1 — a cut opens no worktree and no branch — both cutters write and commit in the instance, and the seed that asked for this is dropped
# Version: 1.0.0 — created in place under the bare-identity folder name
#   <CORE>/launchers/seeds-from-idea/ (no relocation, no prior name, so no provenance block).
#
# THE MODEL, AND THE ONE PLACE THIS DIVERGES
#   `companion-self-answer/launcher.sh` for the
#   project-card address resolution: the `Product path:` read stripped through its trailing HTML
#   comment, the absolute/`~`-vs-relative `--add-dir` split, `--instance-root`, `--dry-run`,
#   `--keep-awake`, and the sourced detach tail.
#
#   THE DIVERGENCE: this launcher's one positional is a PATH, never a project name. The skill's
#   three inputs are a seed, a file, or a live session — the third has nothing to pass, so only
#   the two path-shaped ones become an argument form (the seed's own § Plan goal). So there is no
#   `<project>` argument to resolve a card from directly. Instead the project is DERIVED from the
#   path: when the idea sits under `system/projects/<project>/…`, that segment names the project
#   whose card supplies `Product path:` for the same external-vs-internal `--add-dir` split every
#   sibling makes. An idea at instance level (`system/nemawashi/…`, or any path outside
#   `system/projects/`) derives no project and gets no `--add-dir` — nothing beyond the instance
#   repo the run's cwd already covers. A project card the derived name does not resolve to (no
#   project.md, or no `Product path:` line) is not a refusal — cutting an idea does not require
#   the idea to already belong to an existing project's product, so this is read best-effort and
#   simply adds no `--add-dir`.
#
# WHY A LAUNCHER (same reason as every sibling)
#   A session asked to "cut this idea into seeds" *composes* the subagent's prompt, and that is
#   the one place stray context leaks in — a lean, a prior round's summary, "and while you're
#   there". The prompt below is a FIXED literal; a caller can only pass the path to the idea.
#   Nothing a caller types can be added to what the run receives.
#
# THE SEAT IS FIXED, NOT RESOLVED
#   Unlike `companion-self-answer`, which reads its seat off the companion it will answer, this
#   run always launches under `--agent principal-pm` — the one posture the `seeds-from-idea`
#   skill gates to (`skills/interactive/.claude/skills/seeds-from-idea/SKILL.md` § Posture). The same fixed seat
#   `product-fdr` uses for the same reason: one skill, one required posture, nothing to read a
#   seat off.
#
# NO WORKTREE IS OPENED — NOT BY THIS LAUNCHER AND NOT BY THE RUN
#   The owner's call, 2026-09-05: a cut opens no worktree and no branch, and works in the instance it
#   was started in (`<CORE>/prompts/principal_pm_cut_seeds_run.md` § Where the run works). This reverses
#   the 2026-08-30 call under which the skill opened one at <main-checkout-root>/.worktrees/<key>.
#   This launcher's own behaviour is unchanged and always was correct: it creates no worktree and no
#   branch, starts the run in the instance root, and passes nothing about a worktree in the prompt
#   below. What changed is that nobody opens one afterwards.
#
#   ONE HAZARD THIS RETIRES. While the skill opened its own, a run started from inside a worktree
#   beneath the instance root would have put <main-checkout-root>/.worktrees/<key> outside both the
#   cwd it inherits and every --add-dir this launcher passes. That was reported here as unexercised
#   and is now moot: the run writes into the tree it was started in, which is the cwd this launcher
#   set, so the writable roots and the tree written to are the same thing by construction.
#
# USAGE
#   <CORE>/launchers/seeds-from-idea/launcher.sh <idea-path> [--dry-run] [--keep-awake]
#            (run from the instance root — the tree the seeds are to land in)
#     <idea-path>   a path to the idea being cut — a seed or a written fragment, wherever it
#                   lives. Must LOOK like a path: hold a '/' or start with '.'. A bare word is
#                   always refused — unlike the retired `ad-hoc-flow`'s slug, there is no per-slug folder
#                   convention for an idea, so nothing stands in for one.
#     --dry-run     print the resolved address and the exact claude command; launch nothing
#     --keep-awake  keep the Mac awake (caffeinate) for the run's duration; needs a
#                   notifier/watcher
#     --instance-root <dir>   override the instance root (default: cwd); must come first
#   The one positional is required. Anything after it that is not a known flag is REFUSED, never
#   silently ignored — a caller cannot append prose to what the run receives, and every refusal
#   happens before any process is spawned.
#
# COMPLETION NOTIFICATION
#   `claude --bg` outlives this script. It detaches watch_agent.py (through the shared home
#   below), which polls `claude agents --json --all` until the run stops and then reports. Wholly
#   optional: with no executable notifier the watcher is skipped and the launch is unaffected.
#   Override the pair with LAUNCH_SEEDS_FROM_IDEA_WATCHER / LAUNCH_SEEDS_FROM_IDEA_NOTIFIER.
#
# THE SHARED COMPLETION-WATCH HOME (core/tools/detach_watcher.sh)
#   Sourced, never hand-copied. No env override: unlike $WATCHER, no test or caller ever wants a
#   stub in its place, only the real file at its real relative depth.
#
# PERMISSIONS / CONTEXT (identical rationale to the sibling launchers)
#   --permission-mode auto — REQUIRED. Nobody can answer a permission prompt in a --bg run. NOT a
#   bypass, NOT --dangerously-skip-permissions — see ~/.claude/CLAUDE.md § Permission mode. Use
#   --bg, NOT -p/--print. --add-dir is added only for an external (absolute or `~`) derived
#   product path.
#
set -euo pipefail

# --- resolve the instance root (the caller's cwd) and cd there ----------------------
#   This tool lives in <CORE>/launchers/seeds-from-idea/ and is shared across instances, so it
#   CANNOT derive its instance from its own location. The instance is the caller's cwd;
#   --instance-root overrides. The cd is load-bearing: `claude --bg` inherits THIS shell's cwd.
#   SCRIPT_DIR is a sibling of <CORE>/tools/; the watcher and the shared completion-watch home
#   resolve via CORE_DIR — derived from this folder's own location, not a fixed number of
#   parent steps.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # <CORE>/launchers/seeds-from-idea
CORE_DIR="${SCRIPT_DIR%/launchers/*}"
[ "$CORE_DIR" != "$SCRIPT_DIR" ] || { echo "seeds-from-idea: no /launchers/ ancestor above $SCRIPT_DIR — refusing to guess <CORE>" >&2; exit 1; }
SCRIPT_PATH="$SCRIPT_DIR/$(basename "${BASH_SOURCE[0]}")"
# shellcheck source=/dev/null
source "$CORE_DIR/tools/pin_run.sh"
pin_enter "$CORE_DIR" "$SCRIPT_PATH" "$@" || exit $?
INSTANCE_ROOT="$PWD"
[ "${1:-}" = "--instance-root" ] && { INSTANCE_ROOT="$2"; shift 2; }
cd "$INSTANCE_ROOT"
INSTANCE_ROOT="$PWD"   # re-resolved absolute, even when --instance-root was given relative

# Completion-notification pair (both optional — see the watcher block at the bottom).
WATCHER="${LAUNCH_SEEDS_FROM_IDEA_WATCHER:-$CORE_DIR/tools/watch_agent.py}"
NOTIFIER="${LAUNCH_SEEDS_FROM_IDEA_NOTIFIER:-${KENSAIAPP_NOTIFIER:-}}"
DETACH_LIB="$CORE_DIR/tools/detach_watcher.sh"
# The shared telemetry-instrument home — same real depth as DETACH_LIB above. No env
# override, for the same reason: no test or caller ever wants a stub in its place, only
# the real file at its real relative depth.
INSTRUMENT_LIB="$CORE_DIR/tools/instrument_run.sh"
# The one resolution of a run's model, effort and source, shared by every instrumented
# launcher — same real depth, and no env override for the same reason.
RUN_INTELLIGENCE="$CORE_DIR/tools/run_intelligence.py"
# The one reader of the provider file — same real depth, and no env override: no caller may point
# a launch at another file.
PROVIDERS_TOOL="$CORE_DIR/tools/providers.py"

die() { echo "seeds-from-idea: $*" >&2; exit 1; }

usage="usage: <CORE>/launchers/seeds-from-idea/launcher.sh <idea-path> [--dry-run] [--keep-awake]"

# --- args --------------------------------------------------------------------------
#   One positional: the path to the idea. Everything after it that is not a known flag is
#   REFUSED, never silently ignored — a caller cannot append prose to what the run receives.
idea_arg="${1:-}"
case "$idea_arg" in
  ""|--*) die "$usage
    <idea-path> is required — a path to the idea being cut" ;;
esac
shift

# A bare word (no '/' and no leading '.') is refused outright. There is no per-slug folder
# convention for an idea the way the retired `ad-hoc-flow` had one for a proposal, so nothing stands in for
# one — the shape check is the whole rule, and it never consults the filesystem.
case "$idea_arg" in
  */*|.*) : ;;
  *) die "'$idea_arg' does not look like a path — a bare word is refused; there is no per-slug folder convention for an idea. $usage" ;;
esac

dry_run=""
keep_awake=""
for arg in "$@"; do
  case "$arg" in
    --dry-run)    dry_run=1 ;;
    --keep-awake) keep_awake=1 ;;
    *) die "unknown argument: $arg - the prompt is fixed and takes only the idea path. $usage" ;;
  esac
done

# --- the provider: this launcher's entry in .providers.toml at the instance root ---
#   Read right after the arguments are checked, before the idea or anything it names is looked at,
#   so a launch the file cannot serve is refused before anything else, and a dry run is refused
#   exactly where the launch would be. The cutting run is a Claude run: the reader is asked to
#   accept `claude` and refuses any other entry by name. No force is read — an exported
#   KENSAIAPP_AGENT_PROVIDER is ignored here. The key is the literal `seeds-from-idea`, never
#   derived from SCRIPT_DIR: this script is also run from development/specs/. `providers.py`
#   imports the intelligence resolver, so both are checked before the reader is run.
[ -f "$PROVIDERS_TOOL" ] || die "no provider reader at $PROVIDERS_TOOL"
[ -f "$RUN_INTELLIGENCE" ] || die "no intelligence resolver at $RUN_INTELLIGENCE"
provider_err="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-seeds-from-idea-provider.XXXXXX")"
provider="$(python3 "$PROVIDERS_TOOL" launcher seeds-from-idea --instance-root "$INSTANCE_ROOT" --accept claude 2>"$provider_err")" && rc=0 || rc=$?
provider_msg="$(cat "$provider_err")"
rm -f "$provider_err"
[ "$rc" -eq 0 ] || die "${provider_msg:-could not read the provider for the seeds-from-idea launcher}"

# --- resolve the idea path, then require it land inside the instance root -----------
#   An idea is cut from inside the repository — the owner's ruling, 2026-08-30. Not a
#   convenience: the trace-back line every seed carries has to mean something to a reader on
#   another machine or after the file moves, which a path outside the repo cannot do. So there is
#   one resolution, not three arms (`~/`, absolute, relative) that each accepted a different shape
#   and always succeeded — whatever the caller typed is expanded and joined against the instance
#   root in one step (`os.path.join` drops the root when the joined piece is already absolute,
#   `os.path.expanduser` handles `~/`), normalized, and the result must sit inside the instance
#   root or the run refuses, naming why and what to do.
idea_path="$(python3 -c '
import os, sys
root, arg = sys.argv[1], os.path.expanduser(sys.argv[2])
print(os.path.normpath(os.path.join(root, arg)))
' "$INSTANCE_ROOT" "$idea_arg")"

case "$idea_path" in
  "$INSTANCE_ROOT"|"$INSTANCE_ROOT"/*) : ;;
  *) die "'$idea_arg' resolves outside the instance root ($INSTANCE_ROOT) — an idea is cut from
    inside the repository, since a seed must cite it by a path that outlives it. Bring it in first
    — copy it into system/nemawashi/ or a project's journey/nemawashi/unpicked/ — then cut from
    that path." ;;
esac
[ -e "$idea_path" ] || die "no file at $idea_path (does '$idea_arg' exist?)"

echo "Idea: $idea_path"

# repo-relative form — cited in the prompt below and reused for the project derivation next,
# rather than computed twice.
rel="${idea_path#$INSTANCE_ROOT/}"

# --- derive the owning project from the idea path, and its product's --add-dir ------
#   Only when the idea sits under `system/projects/<project>/…` — the segment right after
#   `system/projects/` names the project. An idea at instance level (or any path outside
#   `system/projects/`) derives no project at all: `${rel#pattern}` leaves `rel` unchanged when
#   the pattern does not match, and the case below then falls through to the empty-project arm.
project=""
case "$rel" in
  system/projects/*)
    project="${rel#system/projects/}"
    project="${project%%/*}"
    ;;
esac

add_dir=""
product_path=""
if [ -n "$project" ]; then
  project_md="$INSTANCE_ROOT/system/projects/$project/project.md"
  # Best-effort: cutting an idea does not require it to already belong to an existing project's
  # product, so a missing card or a missing `Product path:` line adds no --add-dir rather than
  # refusing the run.
  if [ -f "$project_md" ]; then
    raw_path="$(grep -m1 -E '^\*\*Product path:\*\*' "$project_md" \
      | sed -E 's/^\*\*Product path:\*\*[[:space:]]*//; s/[[:space:]]*<!--.*$//; s/[[:space:]]*$//' || true)"
    if [ -n "$raw_path" ]; then
      case "$raw_path" in
        "~"/*) product_path="${HOME}/${raw_path#\~/}"; add_dir=1 ;;
        /*)    product_path="$raw_path";              add_dir=1 ;;
        *)     product_path="$INSTANCE_ROOT/$raw_path" ;;   # internal: covered by cwd, no --add-dir
      esac
    fi
  fi
  echo "Project:   $project"
  [ -n "$product_path" ] && echo "Product:   $product_path"
fi

# --- build the launch command: FIXED prompt, only the resolved idea path interpolated ----
#   Nothing a caller composes reaches the run: the prompt names the skill and the resolved path,
#   and anything the caller typed past the one positional was already refused above. The
#   repo-relative form is what's cited — the run resolves it again against the instance it was
#   started in (SKILL.md § Step 1), which is the cwd this launcher set.
prompt="invoke the seeds-from-idea skill for the idea at ${rel}."

# --- the run's provenance, from the one resolution ---------------------------------
#   This run is the launcher's own skill, so that skill's intelligence/ folder is consulted first,
#   as the skill launcher does (found under the host root, which holds the skills).
#   The run goes at the file's model and effort, and the stamp below records the same pair from the
#   same answer. A skill that does not resolve is not a refusal: no skill dir, so the answer is
#   `default` and the run goes at the provider's own.
own_skill_dir="$(python3 "$CORE_DIR/tools/skill_path.py" seeds-from-idea --root "${CORE_DIR%/core}" 2>/dev/null || true)"
resolution_args=(--provider "$provider")
[ -z "$own_skill_dir" ] || resolution_args+=(--skill-dir "$own_skill_dir")
resolution_err="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-seeds-from-idea-intelligence.XXXXXX")"
resolution="$(python3 "$RUN_INTELLIGENCE" "${resolution_args[@]}" 2>"$resolution_err")" && rc=0 || rc=$?
resolution_msg="$(cat "$resolution_err")"
rm -f "$resolution_err"
[ "$rc" -eq 0 ] || die "${resolution_msg:-$RUN_INTELLIGENCE answered no model, effort or source}"
run_model="$(printf '%s\n' "$resolution" | sed -n 's/^model=//p')"
run_effort="$(printf '%s\n' "$resolution" | sed -n 's/^effort=//p')"
run_source="$(printf '%s\n' "$resolution" | sed -n 's/^source=//p')"

# --- tag this run before it spawns (the shared instrument home) -------------------
#   Unconditional, not behind a flag — the caller sets no argument and exports no variable.
#   Called ahead of the adapter build below, so INSTRUMENT_RUN_SETTINGS is ready to hand it as
#   the caller's own --settings; the exports made here die with this script when --dry-run exits
#   before anything is spawned.
if [ -f "$INSTRUMENT_LIB" ]; then
  # shellcheck source=/dev/null
  source "$INSTRUMENT_LIB"
  instrument_run provider="$provider" model="$run_model" effort="$run_effort" source="$run_source"
else
  echo "          (no instrument library at $INSTRUMENT_LIB — run uninstrumented)"
fi

# --- build the launch command: the fixed prompt, the fixed seat, and the pin's delivery -----
#   The Claude argv comes from the one adapter, never assembled here (Task 15) — the pin was
#   entered right after the CORE_DIR guard above. INSTRUMENT_RUN_SETTINGS is handed to the
#   adapter as the caller's own --settings rather than appended a second time, since it folds
#   into the pin's one merged document.
claude_cmd=(python3 "$CORE_DIR/tools/agent_run.py" --provider "$provider" --shape background --pin auto
  --instance-root "$INSTANCE_ROOT" --prompt "$prompt" --agent principal-pm
  --grant-skill seeds-from-idea)
[ -z "$run_model" ] || claude_cmd+=(--model "$run_model")
[ -z "$run_effort" ] || claude_cmd+=(--effort "$run_effort")
[ -n "$add_dir" ] && claude_cmd+=(--add-dir "$product_path")
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

# --- snapshot existing agent ids BEFORE launching ----------------------------------
#   The launched agent is identified by (name, cwd, id-not-seen-before). Captured before the
#   launch, or the new agent would be in its own exclusion set.
ids_before="$(python3 "$WATCHER" --list-ids --cwd "$INSTANCE_ROOT" 2>/dev/null || true)"

echo "Launching seeds-from-idea run for the idea at '$idea_path' (background)…"
# Redirected to a FILE, never captured through a pipe — `$( … )` waits for end-of-file on the
# pipe, not for the command to exit, and `claude --bg` leaves a detached run holding the
# inherited descriptor, which would block this launcher for the whole run it just backgrounded.
launch_log="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-launch-out.XXXXXX")"
"$@" >"$launch_log" 2>&1
launch_out="$(cat "$launch_log")"
rm -f "$launch_log"
printf '%s\n' "$launch_out"
echo "Launched. Watch/attach: claude agents        (interactive view — logs, stop, resume live here)"
echo "          Script it:    claude agents --json --all   (machine-readable run state)"

# --- background the completion watcher, through the shared home --------------------
#   `claude --bg` outlives this script, so the script's exit says nothing about the run. The
#   shared home (core/tools/detach_watcher.sh) does the detach, the logging, and --keep-awake's
#   caffeinate bind — this launcher only resolves the values and calls it. A missing library is
#   reported and skipped, never fatal — the primary run has already launched by this point.
if [ -f "$DETACH_LIB" ]; then
  # shellcheck source=/dev/null
  source "$DETACH_LIB"
  detach_completion_watcher \
    --watcher "$WATCHER" --notifier "$NOTIFIER" \
    --instance-root "$INSTANCE_ROOT" --prompt "$prompt" \
    --label "seeds-from-idea" --log-stem "seeds-from-idea" --reporter generic \
    --exclude-ids "$ids_before" \
    --launch-output "$launch_out" \
    ${keep_awake:+--keep-awake}
else
  echo "          (no completion-watch library at $DETACH_LIB — completion watch skipped)"
fi
