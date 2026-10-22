#!/usr/bin/env bash
# product-card — the owner's one move after the foundation step settles: the card, then the skeleton.
#
# Version: 1.13.0 — the other six launchers run on the package's turn-on
# Version: 1.12.3 — Python floor is 3.13 everywhere, product-card --keep-awake runs where caffeinate is absent, and .env.example says its launcher settings come from the environment
# Version: 1.12.2 — re-running the card leaves a built product's code alone — the skeleton places a frame whole or not at all
# Version: 1.12.1 — launchers and launch scripts take a portable mktemp template, so they run on Linux
# Version: 1.12.0 — the providers file lives in the instance — each instance reads its own .providers.toml, and a tracked .providers.toml.example is the template
# Version: 1.11.0 — product-setup becomes product-card, and the stamped setup seed becomes define-the-product
# Version: 1.10.1 — the neutrality check reads fixtures and .claude/, declares platform names, and repairs fixture hits itself; the ratify launcher is deleted
# Version: 1.10.0 — a pinned run sees only its own skill group
# Version: 1.9.0 — the eight skill launchers read their provider from the central providers file and refuse naming the entry when it is missing — no literal claude
# Version: 1.8.0 — the eleven other instrumented launchers stamp provider, model, effort and source through one shared resolution
# Version: 1.7.0 — a run keeps the version it started on — every launcher enters a pin of core/, .claude/ and skills/
# Version: 1.6.0 — a consumer satellite gets no root skills/ link — its launchers find skill groups in the host
# Version: 1.5.0 — kensaiapp-michi, product-setup and project-stamp move to the new interactive-product group, and the product-setup launcher grants that group to its card half
# Version: 1.4.0 — a launcher may live nested under core/launchers/development/, and its reach resolves <CORE> from its own location instead of counting folders
# Version: 1.3.0 — a launcher-started record says which instance, product and operation it was for — instrument_run stamps them, chain.py ties a walk, and the step-name seed is parked by the owner's ruling
# Version: 1.2.0 — the backgrounded launchers are tagged too — every launcher hands its telemetry to the spawn as --settings; station 2 closes and the seed is set down
# Version: 1.1.0 — station 2's instrument lands — every launcher tags its own run, and the receiver answers only this machine
# Version: 1.0.0 — first cut. The card half (the `product-setup` skill in Principal PM posture) runs
#                  in the FOREGROUND and its exit code gates the skeleton half.
#
# WHY THIS EXISTS
#   Between a settled foundation and a cut of seeds sit three moves nobody runs — write the card's
#   architecture-determined fields, write the product's README, place the language frames. The first
#   two are judgment and belong to a model; the third is a byte-for-byte copy and belongs to
#   `product-skeleton`. This script is the one command that does them in the order they depend on.
#
#   IT WAITS, AND THAT IS THE DIVERGENCE FROM EVERY SIBLING HERE. The other launchers fire
#   `claude --bg` and exit in about a second, leaving a detached run and a completion watcher.
#   That shape cannot carry this step: `product-skeleton` reads `Languages:` and `Language roots:`
#   off the card the first half writes, so a backgrounded first half means the second half runs
#   against the card as it stood BEFORE. So the card half runs under `claude -p` and this script
#   blocks on it.
#
#   WHAT THE FOREGROUND BUYS, BEYOND CORRECTNESS. Two fleet-wide guards exist because the detached
#   shape is hard to get right: `core/tools/test_agent_id_handover.py` (a `claude --bg` launcher must
#   hand its watcher the run id, because the name is rewritten under it) and
#   `core/tools/test_keep_awake_binding.py` (a detached `caffeinate` must key its release on an
#   identity, because a pid number is reissued). Neither reaches this file. There is no `--bg` run to
#   name, and `--keep-awake` here is the wrapper form the second of those two names as its one
#   deliberate exemption — `caffeinate -i -s <command>`, holding exactly as long as its own child,
#   with no pid anywhere and nothing to reissue.
#
#   AND THERE IS NO WATCHER AND NO NOTIFIER. Both exist to tell a caller about a run that outlived
#   the script. Nothing here outlives it: the script reports both halves itself and exits.
#
# THE ARGUMENT IS A PROJECT NAME
#   Identity in, file derived. A path would let a caller name a directory this project's card never
#   points at, and the two halves would then act on different products while both looked right.
#
# USAGE
#   <CORE>/launchers/product-card/launcher.sh <project> [--dry-run] [--keep-awake]
#
#     <project>      a bare word — a directory under system/projects/. Not a path, not a product
#                    name, not a card.
#     --dry-run      print what each half would run, and launch neither.
#     --keep-awake   hold the Mac awake for the card half (wrapper-form caffeinate; see above).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CORE_DIR="${SCRIPT_DIR%/launchers/*}"
[ "$CORE_DIR" != "$SCRIPT_DIR" ] || { echo "product-card: no /launchers/ ancestor above $SCRIPT_DIR — refusing to guess <CORE>" >&2; exit 1; }
SCRIPT_PATH="$SCRIPT_DIR/$(basename "$0")"
# shellcheck source=/dev/null
source "$CORE_DIR/tools/pin_run.sh"
pin_enter "$CORE_DIR" "$SCRIPT_PATH" "$@" || exit $?
SKILLS_ROOT="${LAUNCH_PRODUCT_CARD_SKILLS_ROOT:-${CORE_DIR%/core}}"   # the host root: a satellite holds no skills of its own

INSTANCE_ROOT="$PWD"
[ "${1:-}" = "--instance-root" ] && { INSTANCE_ROOT="$2"; shift 2; }
cd "$INSTANCE_ROOT"
INSTANCE_ROOT="$PWD"   # re-resolved absolute, even when --instance-root was given relative

# The deterministic half. An override so the suite can put a recording stub in its place; the default
# is the real launcher at its real relative depth, one folder over.
SKELETON="${LAUNCH_PRODUCT_CARD_SKELETON:-$SCRIPT_DIR/../product-skeleton/launcher.sh}"

# The shared telemetry-instrument home — at the same real depth every sibling launcher resolves
# it at, though this is the one file with no DETACH_LIB beside it to anchor the comment on: there
# is no watcher and no notifier here (see the header), but the card half still runs `claude -p`
# and still deserves to be tagged. No env override, for the same reason the siblings carry none:
# no test or caller ever wants a stub in its place, only the real file at its real relative depth.
INSTRUMENT_LIB="$CORE_DIR/tools/run_telemetry.sh"
# The one resolution of a run's model, effort and source, shared by every instrumented
# launcher — same real depth, and no env override for the same reason.
RUN_INTELLIGENCE="$CORE_DIR/tools/run_intelligence.py"
# The one reader of the provider file — same real depth, and no env override: no caller may point
# a launch at another file.
PROVIDERS_TOOL="$CORE_DIR/tools/providers.py"

die() { echo "product-card: $*" >&2; exit 1; }

USAGE="usage: <CORE>/launchers/product-card/launcher.sh <project> [--dry-run] [--keep-awake]"

# --- args ----------------------------------------------------------------------------------------
#   An unknown argument is REFUSED rather than ignored. The sibling launchers fall through a `case`
#   with no default branch, which is the defect the `launchers` seedbed records as "an unknown flag
#   is accepted in silence"; a new file has no reason to inherit it.
project=""
dry_run=""
keep_awake=""
for arg in "$@"; do
  case "$arg" in
    --dry-run)    dry_run=1 ;;
    --keep-awake) keep_awake=1 ;;
    -*)           die "unknown argument '$arg'. $USAGE" ;;
    */*)          die "'$arg' looks like a path; this takes a project name — a bare directory name under system/projects/. $USAGE" ;;
    *)
      [ -z "$project" ] || die "more than one project named ('$project' and '$arg'). $USAGE"
      project="$arg"
      ;;
  esac
done
[ -n "$project" ] || die "$USAGE"

project_md="$INSTANCE_ROOT/system/projects/$project/project.md"
[ -f "$project_md" ] || die "no project card at system/projects/$project/project.md (is '$project' a real project?)"

# --- the provider: this launcher's entry in .providers.toml at the instance root ---
#   Read right after the arguments and the project card, before the product path, the skeleton half
#   or the card half is touched, so a launch the file cannot serve is refused before anything runs,
#   and a dry run is refused exactly where the launch would be. The card half is a Claude run: the
#   reader is asked to accept `claude` and refuses any other entry by name. No force is read — an
#   exported KENSAIAPP_AGENT_PROVIDER is ignored here. The key is this launcher's own folder name as
#   a literal. `providers.py` imports the intelligence resolver, so both are checked before the
#   reader is run.
[ -f "$PROVIDERS_TOOL" ] || die "no provider reader at $PROVIDERS_TOOL"
[ -f "$RUN_INTELLIGENCE" ] || die "no intelligence resolver at $RUN_INTELLIGENCE"
provider_err="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-product-card-provider.XXXXXX")"
provider="$(python3 "$PROVIDERS_TOOL" launcher product-card --instance-root "$INSTANCE_ROOT" --accept claude 2>"$provider_err")" && rc=0 || rc=$?
provider_msg="$(cat "$provider_err")"
rm -f "$provider_err"
[ "$rc" -eq 0 ] || die "${provider_msg:-could not read the provider for the product-card launcher}"

# --- resolve the Product path -----------------------------------------------------------------
#   Both halves resolve every file they touch from this one field, so a card that cannot supply it
#   stops the run HERE — before the card half, which costs a model run.
#
#   `|| true` on the substitution, and the real check on the next line: under `pipefail` a `grep`
#   that matches nothing would end the script before the guard could name what was missing.
raw_path="$(grep -m1 -E '^\*\*Product path:\*\*' "$project_md" \
  | sed -E 's/^\*\*Product path:\*\*[[:space:]]*//; s/[[:space:]]*<!--.*$//; s/[[:space:]]*$//' || true)"
[ -n "$raw_path" ] || die "no 'Product path:' line in system/projects/$project/project.md — both halves resolve every file from that field"

# A card still carrying what `project-stamp` stamped has never been pointed at a product. The angle
# brackets are the template still speaking, and they are checked because the path they make is a real
# directory name a run would otherwise create.
case "$raw_path" in
  *"<"*|*">"*) die "'Product path:' in system/projects/$project/project.md is still the stamped placeholder ($raw_path) — point it at the product first" ;;
esac

case "$raw_path" in
  "~"/*) product_path="${HOME}/${raw_path#\~/}" ;;
  /*)    product_path="$raw_path" ;;
  *)     product_path="$INSTANCE_ROOT/$raw_path" ;;
esac

# --- the card half: build the command, FIXED prompt, only $project interpolated -----------------
#   The prompt is a fixed literal so nothing a caller composes reaches the run. A session asked to
#   spawn a run composes its prompt, and that is the one place stray context leaks in — the reason
#   every launcher here builds its prompt rather than accepting one.
#
#   `-p` and not `--bg`: see the header. `--permission-mode auto` is the siblings' value, and this is
#   not `--dangerously-skip-permissions`.
prompt="invoke the product-card skill for the ${project} project."

# --- the run's own skill: grant its group when product-card is grouped ------------------------
#   A skill at `skills/<group>/.claude/skills/<name>/` is hidden from a session at startup, so a
#   run launched to invoke product-card by name never sees it unless its group is granted — the
#   same rule, read off the resolved path the same way, as <CORE>/launchers/skill/launcher.sh.
#   Best-effort: a name that does not resolve grants nothing, and the run reports its own miss.
#   Unlike the skill launcher's own Claude path (Task 13), this --add-dir is NOT dropped for the
#   pin's plugin — the design (Sub-job I) names only product-sdd, launch-audit and the experience/
#   writing-bar seat groups for that drop; this one passes through as today.
setup_dir="$(python3 "$CORE_DIR/tools/skill_path.py" product-card --root "$SKILLS_ROOT" 2>/dev/null || true)"
add_dir=""
case "$setup_dir" in
  "$SKILLS_ROOT/skills/"*"/.claude/skills/product-card") add_dir="${setup_dir%/.claude/skills/product-card}" ;;
esac

# --- the run's provenance, from the one resolution ---------------------------------
#   This run is the launcher's own skill, so that skill's intelligence/ folder is consulted first,
#   as the skill launcher does (its dir is the one resolved above).
#   The run goes at the file's model and effort, and the stamp below records the same pair from the
#   same answer. A skill that does not resolve is not a refusal: no skill dir, so the answer is
#   `default` and the run goes at the provider's own.
own_skill_dir="$setup_dir"
resolution_args=(--provider "$provider")
[ -z "$own_skill_dir" ] || resolution_args+=(--skill-dir "$own_skill_dir")
resolution_err="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-product-card-intelligence.XXXXXX")"
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
#   before anything is spawned. The card half is `claude -p`, not `--bg`, but it is still a run
#   this launcher spawns, so it is still tagged.
if [ -f "$INSTRUMENT_LIB" ]; then
  # shellcheck source=/dev/null
  source "$INSTRUMENT_LIB"
  run_telemetry project="$project" provider="$provider" model="$run_model" effort="$run_effort" source="$run_source"
else
  echo "          (no instrument library at $INSTRUMENT_LIB — run uninstrumented)"
fi

# --- build the card half's command: the fixed prompt, the fixed seat, and the pin's delivery ---
#   The Claude argv comes from the one adapter, never assembled here (Task 15) — shape print, for
#   `claude -p` (see the header for why this half runs in the foreground). The pin was entered
#   right after the CORE_DIR guard above. INSTRUMENT_RUN_SETTINGS is handed to the adapter as the
#   caller's own --settings rather than appended a second time, since it folds into the pin's one
#   merged document.
claude_cmd=(python3 "$CORE_DIR/tools/agent_run.py" --provider "$provider" --shape print --pin auto
  --instance-root "$INSTANCE_ROOT" --prompt "$prompt" --agent principal-pm
  --grant-skill product-card)
[ -z "$run_model" ] || claude_cmd+=(--model "$run_model")
[ -z "$run_effort" ] || claude_cmd+=(--effort "$run_effort")
[ -n "$add_dir" ] && claude_cmd+=(--add-dir "$add_dir")
[ -n "${INSTRUMENT_RUN_SETTINGS:-}" ] && claude_cmd+=(--settings "$INSTRUMENT_RUN_SETTINGS")
claude_cmd+=(--print-argv)

claude_argv=()
while IFS= read -r -d '' a; do
  claude_argv+=("$a")
done < <("${claude_cmd[@]}")
set -- "${claude_argv[@]}"

# The wrapper form: caffeinate holds exactly as long as its own child and is never detached, so there
# is no pid to reissue and nothing to release. `core/tools/test_keep_awake_binding.py` names this form
# as its one deliberate exemption.
# caffeinate is macOS-only; where it is absent the card half still runs, and says it held nothing.
if [ -n "$keep_awake" ]; then
  if command -v caffeinate >/dev/null 2>&1; then
    set -- caffeinate -i -s "$@"
  else
    echo "(keep-awake: caffeinate not found — not macOS? — skipped)"
  fi
fi

if [ -n "$dry_run" ]; then
  echo "DRY RUN — the card half would run:"
  printf '  %q' "$@"
  echo
  echo "DRY RUN — then the skeleton half would dry-run: $SKELETON $project"
  exit 0
fi

echo "Card half — running the product-card skill as principal-pm. This waits."
# The exit code of this half GATES the next one, and the message says which half failed. Under
# `set -e` a bare failure would exit with the right code and say nothing, leaving a caller to guess
# between two halves that ran in one command.
"$@" || die "the card half failed (exit $?). The skeleton half was NOT reached — it reads the card this half writes, so running it now would place frames against the card as it stood before."
echo "Card half — done."

# --- the skeleton half: dry-run first, and let that decide whether to run it for real ------------
#   "Run the skeleton only where there is none" (owner, 2026-09-05) is a REPORT, not a repair.
#   `product-skeleton` already never overwrites, and it places a frame whole or not at all, so a
#   frame with any of its files already in the product is left as built. A second guard here would
#   restate a guarantee that already holds. What is actually missing is that somebody notices and
#   says so.
#
#   The dry run is the only thing that can tell the two apart. It lists what it WOULD create; an
#   empty list means the product already carries its frame, and the disk looks identical in both
#   cases because of that same never-overwrite guarantee.
#
#   A frame already sitting at the wrong root is named and left. Moving it is a skeleton change, and
#   the owner ruled against those on the same day.
echo "Skeleton half — checking what this product already carries."
planned="$("$SKELETON" "$project" --dry-run)" || die "the skeleton half's dry run failed (exit $?). Nothing was placed."
echo "$planned"

if echo "$planned" | grep -qE '^[[:space:]]*(file|dir): '; then
  echo "Skeleton half — placing the frames the dry run listed."
  "$SKELETON" "$project" || die "the skeleton half failed (exit $?) after its dry run had succeeded."
  echo "Skeleton half — placed."
else
  echo "Skeleton half — the product already carries its skeleton; nothing to place, and nothing here moves what is there."
fi
