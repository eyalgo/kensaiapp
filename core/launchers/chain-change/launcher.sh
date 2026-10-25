#!/usr/bin/env bash
#
# launcher.sh (chain-change) — the owner's one command for a change unit's whole life, from the
# station that names it to the seal that lands it on main, and on to the shukuba-refine run after
# it when the unit serves a station.
# Version: 2.10.0 — the owner's Mac ask carries from a walk to the next change's walk
# Version: 2.9.0 — the gate tool reads a walk's owner's-Mac ask itself, so a run cannot drop it
# Version: 2.8.0 — a gate run states its environment — gate_suite tool, environment declaration gate, owner-ask option
# Version: 2.7.3 — the queue ends clean after a walk with no station
# Version: 2.7.2 — a walk with no station ends sealed — the chain's end-of-walk rule, its tests and the walk's text
# Version: 2.7.1 — launchers and launch scripts take a portable mktemp template, so they run on Linux
# Version: 2.7.0 — ollama is a provider — a launch can run on the owner's local Ollama models
# Version: 2.6.0 — the providers file lives in the instance — each instance reads its own .providers.toml, and a tracked .providers.toml.example is the template
# Version: 2.5.0 — chain-change reads the card's Definition line and runs the definition chain it names before the change walk
# Version: 2.4.0 — the launchers accept hf — the seven launchers, the run tools and the structure map take hf as a Claude run aimed at Hugging Face's router
# Version: 2.3.1 — the content seat split states what it made false, and the content step is audited
# Version: 2.3.0 — a stop ends the wait — one shared stop that ends a live walk across chain, chain_development and build_idea, marks it ended with a reason and leaves the state file readable
# Version: 2.2.1 — the chain launchers state the provider truth and build-idea describe matches start
# Version: 2.2.0 — the providers file is reverted — every provider is back in code, and SDD runs on one provider again
# Version: 2.1.1 — every chain step and document reads its provider from system/providers.toml
# Version: 2.1.0 — a chain step names its provider, and --provider forces the whole walk
# Version: 2.0.1 — the chain halts a TDD-lane task that landed without its red commit
# Version: 2.0.0 — Grok is removed — the providers are Claude, Codex and Gemini
# Version: 1.8.0 — adapt Google Gemini as fourth model provider
# Version: 1.7.0 — Grok runs as a provider, model and effort
# Version: 1.6.0 — a run keeps the version it started on — every launcher enters a pin of core/, .claude/ and skills/
# Version: 1.5.0 — enable provider-neutral unattended execution with Codex
# Version: 1.4.0 — the PM drops a halted unit inside the refine — tobiishi-drop moves to the PM, the chain edits are reverted
# Version: 1.3.0 — the PM decides the drop — a halted walk runs shukuba-refine, which can name a drop row that build-idea runs as tobiishi-drop
# Version: 1.2.0 — a developer past the context cap pauses at a task boundary, and the chain relaunches a fresh one at the next task — --context-cap on chain-change and build-idea, default 250000
# Version: 1.1.0 — the refine report's Next moves gains an After column; build-idea runs that table in After order, and chain-change's end starts it
# Version: 1.0.1 — chain-change refines the route after the seal
# Version: 1.0.0 — created in place under the bare-identity folder name
#   <CORE>/launchers/chain-change/ (no relocation, no prior name, so no provenance block):
#   resolves <project>, resolves the completion notifier from the environment, and hands the walk
#   to core/tools/chain_development.py's --start entry point, naming the change table.
#
# WHY THIS EXISTS
#   chain-development enters the walk at development-specs, which presumes two PM moves already
#   made by hand: a station open at journey/shukuba/, and a change request placed at
#   journey/tobiishi/<key>/. This command makes either move that is not made yet, then walks the
#   same pipeline to the seal, so a project goes from "a seed is picked and its route is cut" to
#   "a change unit is sealed on main" without the owner stepping in between. A unit serves a
#   station when a commit it landed carries a Shukuba: trailer, or when a station file names its
#   key, whether that station is open, closed or parked. When the sealed unit serves a station,
#   the walk goes on to re-read the route after it with shukuba-refine. When it serves none, the
#   walk ends sealed at the seal, because shukuba-refine would find no station and stop without a
#   report.
#
# WHY IT NAMES A TABLE AND STILL PASSES NO SPINE
#   chain-product hands chain.py a spine, because that engine walks whatever documents it is
#   given. This walk is a fixed sequence with an audit fan-out inside it, so both step
#   tables live in the engine as literals. --steps says WHICH of the two this walk is; it does not
#   compose one, and there is still nothing here for a caller to reach into.
#
# WHY IT SHARES ITS SIBLING'S ENGINE
#   The two walks differ by two steps at the front and agree everywhere after. A second engine
#   would be a third copy of the state store, the live-walk refusal, the launch environment and
#   the shim write — machinery two engines already duplicate between them, which is a reason to
#   add no third copy of it here.
#
# WHY ITS STATE FILE IS ITS OWN
#   One state file IS one project's walk. chain-product keeps chain-<project>-state.json and
#   chain-development keeps chain-development-<project>-state.json; this walk keeps
#   chain-change-<project>-state.json, so it can run beside either.
#
# WHERE A RELAUNCH PICKS UP
#   Nowhere is a step named to this launcher. The engine reads the disk and enters at the first
#   step whose evidence is missing — no station, no change request, no change_spec.md, and so on
#   — so starting it again after a stop continues rather than restarts, and starting it on a
#   project already mid-change enters exactly where chain-development would. On a project with
#   no change open whose CONTEXT_PM.md names a sealed unit with no shukuba-refine report yet, it
#   carries that unit's key and enters at refine when two things hold: a station is still open,
#   and the unit serves a station. A unit that serves no station is owed no refine, so the walk
#   does not carry its key. It starts with no key at the first step whose evidence is missing, as
#   it does once a unit is refined.
#
# WHERE THE LOOP CLOSES
#   The walk's end starts <CORE>/launchers/build-idea/launcher.sh <project> --chain-ended <end>: the
#   engine runs that command once when the walk ends, sealed or halted, with the end appended.
#   build-idea starts the next queue only on sealed, from the unit's refine report, and says it
#   started nothing on any other end. A walk whose unit serves no station ends sealed with no
#   refine report, because such a unit is owed none. build-idea then starts nothing, says that the
#   unit serves no station, and exits 0. A unit that serves a station and has no refine report is
#   still refused. A walk started with --gate-owners-mac puts that flag before --chain-ended, so
#   the queue it starts puts the ask on the next change's walk. The command is not an argument:
#   nothing here lets a caller point the end somewhere else.
#
# WHAT RUNS BEFORE THE CHANGE WALK
#   Every start reads the card's **Definition:** line and runs the definition walk it names
#   before the change walk, never in its place. full runs chain-product's walk, prd-agari runs
#   chain-agari's, and none runs no definition walk, so the change walk starts at once, as it did
#   before the line existed. The order is the owner's ruling of 2026-10-05: the definition
#   finishes, then the change is walked.
#
#   The definition walk is started through its own launcher,
#   <CORE>/launchers/chain-product/launcher.sh or <CORE>/launchers/chain-agari/launcher.sh, so
#   each spine stays written in one place. That launcher exits seconds after its first run is
#   launched, so only the definition walk's end knows when it has finished. This launcher
#   therefore hands it an --on-end naming this launcher's own end-hook form, and the change walk
#   is started from there. It starts only when the definition walk ended settled or
#   left_for_the_owner, the two ends of a walk that walked its whole spine. Every other end, and
#   a definition start that is refused, starts no change walk. An end the engine adds later
#   starts none either until a spec says otherwise.
#
#   The definition walk runs on every start, even when every product document is already settled
#   or the change is already part-walked. Skipping it would be a judgement on the documents'
#   state, and this launcher does not make one. A --dry-run starts neither walk.
#
#   The line is read on every start, --dry-run included. It is the card's one line beginning
#   exactly **Definition:**, and its value is the text after the label, up to any <!-- comment.
#   No flag and no environment variable sets the value, and the card's **Type:** is never read
#   for it.
#
# WHY THE RULE OVER STEPS="change" CHANGED
#   The STEPS literal below was stated as the whole walk: "not composed from an argument and not
#   read from the caller's environment". The change walk's table is still that literal. A launch
#   no longer walks only that table, because the definition walk in front of it is read from the
#   project card, by the owner's ruling of 2026-10-05. So the literal now fixes the change walk
#   alone, and the card fixes what runs before it.
#
# A CARD WITHOUT THE LINE IS REFUSED
#   A card with no **Definition:** line is refused before anything starts, and it is never given a
#   default: not none, not full, and nothing read off **Type:**. Every card is meant to carry the
#   line, so a missing one is a mistake to catch, not a state to run (the owner's ruling,
#   2026-10-05: "yes. refuse."). A value other than exactly full, prd-agari or none is refused the
#   same way, and so is a card that carries the line twice. Each refusal is one line on stderr
#   naming the card, with exit 1, and no engine is asked anything. A --stop is never refused over
#   the line.
#
# THE PENDING-LAUNCH RECORD
#   Under full and prd-agari, a start writes system/logs/chain-change-<project>-pending.<token>
#   before the definition launcher runs. It is written first because a walk with nothing to
#   launch ends inside its own start and runs its end hook before that launcher returns. The
#   record holds what the change walk needs and the end hook cannot carry: the product path, the
#   provider force, --keep-awake, --context-cap, the notifier and the owner's ask. The end hook rebuilds the change
#   walk from those values the same way a none start builds it, so the change walk it starts is
#   the one this launch would have started under none. Each launch writes its own record, never
#   one per project, so a second launch whose definition start is refused cannot remove the first
#   launch's record.
#
#   Three things remove a record, and nothing else does: the launch itself when its definition
#   start is refused; the end hook, which claims the record once; and --stop, which removes every
#   record the project has.
#
# THE DEVELOPER'S CONTEXT CAP
#   --context-cap <tokens> is the context past which the developer's run is told to pause at a task
#   boundary, and a fresh developer takes the change over from the next task. It is passed to the
#   engine's --start only when given: the default (250000) lives in the engine alone, so this
#   launcher cannot drift from it. It is refused here, before the engine or its --describe runs,
#   unless it is a positive integer — the same rule the engine applies, said where the owner is
#   looking. It reaches the implementation step's run and no other.
#   It is never handed to a definition walk.
#
# USAGE
#   <CORE>/launchers/chain-change/launcher.sh <project> [--provider claude|codex|gemini|hf|ollama] [--dry-run] [--keep-awake]
#                                             [--context-cap <tokens>] [--gate-owners-mac]
#     (run from the instance root)
#     <project>     a project under system/projects/<project>/ with an active seed, whose card
#                   carries one **Definition:** line reading full, prd-agari or none
#     --provider    force every step of the walk onto one provider, over the one its own entry
#                   names in .providers.toml at the instance root. An exported
#                   KENSAIAPP_AGENT_PROVIDER is the
#                   same force; the flag wins. With neither, each step runs on its own entry in
#                   that file; a step whose entry is missing is refused, naming the entry, and
#                   nothing runs on a provider the file did not name. The force is kept on the
#                   walk's state, so it survives the detached completion hooks and reaches
#                   build-idea when the walk ends.
#                   The force reaches a definition walk's runs too.
#     --dry-run     ask the engine which change a start would carry and the step it would enter
#                   at, print those with the resolved project, product path and the exact engine
#                   invocation, and start nothing — or fail with the reason a start would be
#                   refused. Before tobiishi-open there is no change yet, and the change reads
#                   (none yet) rather than failing the dry run.
#                   The definition= line is printed, and no definition walk is started.
#     --keep-awake  keep the Mac awake for the walk; passed down to every step launcher the engine
#                   runs rather than held here, because this script exits once the first step is
#                   launched and the walk goes on in the detached runs. Each step launcher already
#                   owns the mechanism through core/tools/detach_watcher.sh.
#                   It reaches a definition walk too.
#     --context-cap <tokens>
#                   the context, in tokens, past which the developer's run pauses and a fresh one
#                   continues; a positive integer. Applies to the developer's run only. Omitted, the
#                   engine's own default applies.
#                   Never handed to a definition walk.
#     --gate-owners-mac
#                   the owner's ask to run the card's test command on the owner's Mac in the walk's developer, code-integrity, security and seal runs, in place of the environment the product resolves to. Without it, those runs use the owner's Mac only when the product has no CI. No card field, product record or exported variable sets it. The ask is kept on the walk's state, so an advance, a resume or a recovery keeps it. The walk's end hands it to build-idea, which puts it on the next change's walk. Never handed to a definition walk. A start that waits on a definition walk keeps the ask in its pending-launch record, so the change walk started after it has the ask.
#
#   <CORE>/launchers/chain-change/launcher.sh <project> --stop
#     --stop        stop the walk: the engine stops every run in flight, watcher first, signalling
#                   a process only while its pid still has the start time recorded at launch, ends
#                   the walk `stopped` and keeps its state file. Takes no other flag, and exits with
#                   the engine's status.
#                   It also removes every pending-launch record the project has, so no change walk
#                   waiting on a definition walk starts afterwards. It does not stop the definition
#                   walk itself. chain-product's or chain-agari's own --stop ends that walk. A stop
#                   is never refused over the card's Definition: line.
#
#   <CORE>/launchers/chain-change/launcher.sh <project> --after-definition <token> --definition-ended <end>
#     the definition walk's end hook, not a command to type. A start under full or prd-agari
#     hands it to the definition walk, which runs it once when it ends, with how it ended
#     appended. --after-definition names the start's pending-launch record and --definition-ended
#     carries the end. Each needs the other, and neither takes another flag. It starts the change
#     walk only on settled or left_for_the_owner, and only while the record is still there.
#     Otherwise it starts nothing and exits 0. It does not read the card's Definition: line.
#
set -euo pipefail

# --- resolve the instance root (the caller's cwd) and cd there ----------------------
#   CORE_DIR strips this script's own resolved directory at the /launchers/ boundary, so it
#   reaches <CORE> from any nesting depth. The instance is the caller's cwd.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # <CORE>/launchers/chain-change
INSTANCE_ROOT="$PWD"
cd "$INSTANCE_ROOT"
CORE_DIR="${SCRIPT_DIR%/launchers/*}"
[ "$CORE_DIR" != "$SCRIPT_DIR" ] || { echo "chain-change: no /launchers/ ancestor above $SCRIPT_DIR — refusing to guess <CORE>" >&2; exit 1; }
SCRIPT_PATH="$SCRIPT_DIR/$(basename "${BASH_SOURCE[0]}")"
# shellcheck source=/dev/null
source "$CORE_DIR/tools/pin_run.sh"
pin_enter "$CORE_DIR" "$SCRIPT_PATH" "$@" || exit $?

# The engine's own CLI entry point. A test points this at a recording stub so a real --start —
# which would open a station and launch a real run — is never reached from the suite.
CHAIN_SCRIPT="${LAUNCH_CHAIN_CHANGE_SCRIPT:-$CORE_DIR/tools/chain_development.py}"

# Resolved HERE, from the environment, and PASSED to the engine as a parameter — the engine reads
# no environment for it, because every advance re-enters as a fresh detached process. An unset
# notifier is skipped, never an error.
NOTIFIER="${KENSAIAPP_NOTIFIER:-}"

# Which of the engine's two step tables this walk is — a literal here, like chain-product's spine:
# not composed from an argument and not read from the caller's environment. A change to it is a
# test change and cannot pass unnoticed. It fixes the change walk alone; what runs before it is the
# card's (the header's WHY THE RULE OVER STEPS="change" CHANGED).
STEPS="change"

die() { echo "chain-change: $*" >&2; exit 1; }

# --- args --------------------------------------------------------------------------
project="${1:-}"
[ $# -eq 0 ] || shift
dry_run=""
keep_awake=""
context_cap=""
context_cap_given=""
gate_owners_mac=""
stop=""
other_flag=""
after_given=""
after_token=""
ended_given=""
ended=""
# The force: the flag, else an exported KENSAIAPP_AGENT_PROVIDER, else none. Passed to the engine
# as a parameter and kept on its state — the engine sets the variable for each run it launches,
# so nothing here exports it.
provider="${KENSAIAPP_AGENT_PROVIDER:-}"
while [ $# -gt 0 ]; do
  case "$1" in
    --stop)        stop=1 ;;
    --after-definition) after_given=1
                   { [ $# -ge 2 ] && [ -n "$2" ]; } || die "--after-definition needs the pending-launch token the start wrote"
                   after_token="$2"; shift ;;
    --definition-ended) ended_given=1
                   { [ $# -ge 2 ] && [ -n "$2" ]; } || die "--definition-ended needs the end the definition walk reported (settled, left_for_the_owner, ...)"
                   ended="$2"; shift ;;
    --dry-run)     dry_run=1; other_flag=1 ;;
    --keep-awake)  keep_awake=1; other_flag=1 ;;
    --gate-owners-mac) gate_owners_mac=1; other_flag=1 ;;
    --context-cap) context_cap_given=1; other_flag=1
                   # `[ $# -ge 2 ]` and not `${2:-}`: a missing value and an empty one are both
                   # refused below, but only the first has no $2 to shift past.
                   [ $# -ge 2 ] || die "--context-cap needs a value: a positive integer of tokens"
                   context_cap="$2"; shift ;;
    --provider)    [ $# -ge 2 ] || die "--provider needs claude, codex, gemini, hf or ollama"
                   provider="$2"; other_flag=1; shift ;;
    --provider=*)  provider="${1#--provider=}"; other_flag=1 ;;
    --*)           die "unknown flag: $1" ;;
    *)             die "unexpected argument: $1 — the station and the change are discovered on disk, never named" ;;
  esac
  shift
done
[ -n "$project" ] || die "usage: <CORE>/launchers/chain-change/launcher.sh <project> [--provider claude|codex|gemini|hf|ollama] [--dry-run] [--keep-awake] [--context-cap <tokens>] [--gate-owners-mac] | <project> --stop"
# The end-hook form is not checked here: it starts the change walk with the force its record saved
# and never uses the provider in its own environment, so a value there cannot refuse it.
if [ -z "$after_given" ] && [ -z "$ended_given" ]; then
  case "$provider" in ""|claude|codex|gemini|hf|ollama) ;; *) die "provider must be claude, codex, gemini, hf or ollama (got '$provider')" ;; esac
fi

[ -z "$stop" ] || [ -z "$other_flag" ] || die "usage: <CORE>/launchers/chain-change/launcher.sh <project> --stop — a stop takes no other flag"

# --- the end-hook form: both flags or neither -------------------------------------------------
if [ -n "$after_given" ] || [ -n "$ended_given" ]; then
  { [ -n "$after_given" ] && [ -n "$ended_given" ]; } || die "--after-definition and --definition-ended go together — they are the definition walk's end hook, which passes both"
  { [ -z "$stop" ] && [ -z "$other_flag" ]; } || die "--after-definition and --definition-ended are the definition walk's end hook and take no other flag"
fi

if [ -n "$context_cap_given" ]; then
  case "$context_cap" in
    ""|*[!0-9]*) die "--context-cap '$context_cap' is not a positive integer of tokens" ;;
  esac
  [ "$((10#$context_cap))" -gt 0 ] || die "--context-cap '$context_cap' is not a positive integer of tokens"
fi

project_md="$INSTANCE_ROOT/system/projects/$project/project.md"
[ -f "$project_md" ] || die "no project card at $project_md (is '$project' a real project?)"

# --- resolve the Product path (strip the '**Product path:**' label + trailing comment)
raw_path="$(grep -m1 -E '^\*\*Product path:\*\*' "$project_md" \
  | sed -E 's/^\*\*Product path:\*\*[[:space:]]*//; s/[[:space:]]*<!--.*$//; s/[[:space:]]*$//' || true)"
[ -n "$raw_path" ] || die "no 'Product path:' line in $project_md"   # `|| true` above: pipefail would otherwise exit before this guard reports

case "$raw_path" in
  "~"/*) product_path="${HOME}/${raw_path#\~/}" ;;
  /*)    product_path="$raw_path" ;;
  *)     product_path="$INSTANCE_ROOT/$raw_path" ;;
esac

log_dir="$INSTANCE_ROOT/system/logs"
state_path="$log_dir/chain-change-$project-state.json"

# --- the owner's brake: handed to the engine, which stops the walk's runs and ends it --------
#   --stop stands alone. Another flag beside it names a start, and a start beside a stop means
#   neither, so it is refused before the engine runs.
if [ -n "$stop" ]; then
  [ -z "$other_flag" ] || die "usage: <CORE>/launchers/chain-change/launcher.sh <project> --stop — a stop takes no other flag"
  # Every pending launch of this project is cancelled, not only the newest: a stop names no launch,
  # and the owner's brake should leave no change walk waiting. This runs BEFORE the engine's stop,
  # so a definition walk ending in between finds no record to claim. It never reads the card's
  # Definition line, and it does not stop the definition walk itself.
  cancelled=""
  for pending_record in "$log_dir/chain-change-$project-pending."*; do
    [ -f "$pending_record" ] || continue
    rm "$pending_record" 2>/dev/null && cancelled=1 || true
  done
  if [ -n "$cancelled" ]; then
    echo "chain-change: no change walk waiting on a definition walk will start now. This stop leaves the definition walk alone. chain-product's or chain-agari's own --stop ends it."
  fi
  set -- python3 "$CHAIN_SCRIPT" --stop "$state_path"
  [ -n "$NOTIFIER" ] && set -- "$@" --notifier "$NOTIFIER"
  "$@" && rc=0 || rc=$?
  exit "$rc"
fi

# The one place the change walk's engine command is built — for a start that walks the change at
# once and for the end hook that continues a definition-first launch alike — so the change walk the
# hook starts is the one the same launch would start under none, by construction. Arguments: product
# path, provider force, keep-awake, context cap, notifier, the owner's ask. An empty value omits its
# flag. Fills `change_argv`.
build_change_argv() {
  local product="$1" force="$2" awake="$3" cap="$4" notifier="$5" ask="${6:-}" on_end
  # The command the walk's end runs, as ONE string the engine splits the way a shell does. Each
  # word is quoted for that split — printf '%q' is the quoting shlex.split undoes — so a <CORE>
  # whose path holds a space arrives as one word and not as two, the second a command that does
  # not exist. The trailing space printf leaves is stripped, and the engine appends the end after
  # it, so the ask goes before --chain-ended. The ask is handed on, so the next change's walk the
  # queue starts has it; it is built here from the ask given, because the definition walk's end
  # hook is a fresh invocation that takes the ask from the pending-launch record, not a flag.
  if [ -n "$ask" ]; then
    on_end="$(printf '%q ' "$CORE_DIR/launchers/build-idea/launcher.sh" "$project" \
      --gate-owners-mac --chain-ended)"
  else
    on_end="$(printf '%q ' "$CORE_DIR/launchers/build-idea/launcher.sh" "$project" --chain-ended)"
  fi
  on_end="${on_end% }"
  change_argv=(python3 "$CHAIN_SCRIPT" --start "$state_path"
    --instance-root "$INSTANCE_ROOT" --product-path "$product"
    --project "$project" --core-dir "$CORE_DIR" --shim-dir "$log_dir" --steps "$STEPS"
    --on-end "$on_end")
  [ -z "$notifier" ] || change_argv+=(--notifier "$notifier")
  [ -z "$awake" ] || change_argv+=(--keep-awake)
  [ -z "$cap" ] || change_argv+=(--context-cap "$cap")
  [ -z "$force" ] || change_argv+=(--provider "$force")
  [ -z "$ask" ] || change_argv+=(--gate-owners-mac)
}

# --- the definition walk's end hook: starts the change walk, once, from a pending launch --------
#   Hook-only: the definition walk runs it once when it ends, with the end appended. It reads the
#   record the start wrote, not the card, so it never reads the Definition line and a card edited in
#   the meantime changes nothing about the launch it continues.
if [ -n "$after_given" ]; then
  # The token is the suffix mktemp wrote, which is letters and digits and nothing else. Anything
  # else is refused before a path is formed, so no file outside system/logs/ is ever read or
  # claimed.
  case "$after_token" in
    *[!A-Za-z0-9]*) die "'$after_token' is not a pending-launch token — refusing to read a file for it" ;;
  esac
  record="$log_dir/chain-change-$project-pending.$after_token"
  # An absent record is ordinary: a --stop cancelled it, another firing claimed it, or it never
  # existed. The hook cannot tell which, so it says none of them and exits 0 — a non-zero exit
  # would make the engine report a second failure for an end it has already announced.
  no_record() {
    echo "chain-change: the definition walk ended $ended, and no change walk is waiting on it — nothing to start"
    exit 0
  }
  saved() { sed -n "s/^$1=//p" "$record"; }
  [ -f "$record" ] || no_record
  saved_product_path="$(saved product_path)" || no_record
  saved_provider="$(saved provider)" || no_record
  saved_keep_awake="$(saved keep_awake)" || no_record
  saved_context_cap="$(saved context_cap)" || no_record
  saved_notifier="$(saved notifier)" || no_record
  # An older record has no such line, which reads as no ask; only the 1 a start wrote is an ask.
  saved_gate_owners_mac="$(saved gate_owners_mac)" || no_record
  [ "$saved_gate_owners_mac" = 1 ] || saved_gate_owners_mac=""
  # Claim the record with a plain rm, and go on only if that rm succeeded: a stop racing this hook
  # wins or loses cleanly, and a second firing finds nothing.
  rm "$record" 2>/dev/null || no_record
  case "$ended" in
    settled|left_for_the_owner)
      build_change_argv "$saved_product_path" "$saved_provider" "$saved_keep_awake" \
        "$saved_context_cap" "$saved_notifier" "$saved_gate_owners_mac"
      echo "chain-change: the definition walk ended $ended — starting the change walk"
      "${change_argv[@]}" ;;
    *)
      echo "chain-change: the definition walk ended $ended — the change walk did not start. Run chain-change again to walk the definition and then the change."
      exit 0 ;;
  esac
  exit 0
fi

# --- the card's Definition line: read on every start, --dry-run included -----------------------
#   The count decides missing (0) and duplicated (more than one) before the value is read; -m1
#   alone would hide the second line. `|| true`: grep -c prints 0 and exits 1 when nothing matches,
#   and pipefail would otherwise exit before the refusal reports.
definition_count="$(grep -c -E '^\*\*Definition:\*\*' "$project_md" || true)"
[ "$definition_count" -ne 0 ] || die "no 'Definition:' line in $project_md — add **Definition:** full, prd-agari or none"
[ "$definition_count" -eq 1 ] || die "$project_md carries $definition_count 'Definition:' lines — it must carry one"
definition="$(grep -m1 -E '^\*\*Definition:\*\*' "$project_md" \
  | sed -E 's/^\*\*Definition:\*\*[[:space:]]*//; s/[[:space:]]*<!--.*$//; s/[[:space:]]*$//' || true)"
case "$definition" in full|prd-agari|none) ;; *) die "'Definition:' in $project_md reads '$definition' — it must be full, prd-agari or none" ;; esac

echo "chain-change: project=$project"
echo "chain-change: product path=$product_path"
case "$definition" in
  full)      echo "chain-change: definition=full — chain-product's walk runs first, then the change walk" ;;
  prd-agari) echo "chain-change: definition=prd-agari — chain-agari's walk runs first, then the change walk" ;;
  *)         echo "chain-change: definition=none — the change walk alone" ;;
esac
if [ -n "$provider" ]; then
  echo "chain-change: provider=$provider (forced on every step)"
else
  echo "chain-change: provider=each step's own"
fi

# --- full and prd-agari: the definition walk first, the change walk from its end hook -----------
#   The record is written, complete, BEFORE the definition launcher runs: a walk with nothing to
#   launch ends inside its own --start and runs its end hook before that launcher returns. It is
#   plain key=value data — nothing executable is stored, because the hook rebuilds the command.
#   mktemp makes it atomic and unique, so two launches never share a record; its suffix is the
#   token.
if [ -z "$dry_run" ] && [ "$definition" != "none" ]; then
  case "$definition" in full) sibling="chain-product" ;; *) sibling="chain-agari" ;; esac
  mkdir -p "$log_dir"
  record="$(mktemp "$log_dir/chain-change-$project-pending.XXXXXX")"
  token="${record##*.}"
  {
    printf 'product_path=%s\n' "$product_path"
    printf 'provider=%s\n' "$provider"
    printf 'keep_awake=%s\n' "$keep_awake"
    printf 'context_cap=%s\n' "$context_cap"
    printf 'notifier=%s\n' "$NOTIFIER"
    printf 'gate_owners_mac=%s\n' "$gate_owners_mac"
  } > "$record"
  hook="$(printf '%q ' "$CORE_DIR/launchers/chain-change/launcher.sh" "$project" \
    --after-definition "$token" --definition-ended)"
  hook="${hook% }"
  # --context-cap is the developer's alone and is never handed to the definition walk.
  set -- "$CORE_DIR/launchers/$sibling/launcher.sh" "$project"
  [ -n "$provider" ] && set -- "$@" --provider "$provider"
  [ -n "$keep_awake" ] && set -- "$@" --keep-awake
  set -- "$@" --on-end "$hook"
  "$@" && rc=0 || rc=$?
  if [ "$rc" -ne 0 ]; then
    rm -f "$record"
    echo "chain-change: the definition walk did not start, so the change walk will not start either" >&2
    exit "$rc"
  fi
  exit 0
fi

# --- hand the walk to the engine, through its --start CLI ---------------------------
build_change_argv "$product_path" "$provider" "$keep_awake" "$context_cap" "$NOTIFIER" \
  "$gate_owners_mac"
set -- "${change_argv[@]}"

if [ -n "$dry_run" ]; then
  # Ask the engine what a start would do before printing the command, so a dry run never reports
  # a walk the real start refuses. --describe runs the same checks --start makes and writes,
  # launches and sends nothing. It is given the product path the start is given, because for a
  # product in its own repo the per-task commits it judges are there and not on the instance.
  # Its output goes to a FILE, never through a pipe, the same descriptor rule
  # core/launchers/skill/launcher.sh states at its launch.
  describe_out="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-chain-describe.XXXXXX")"
  python3 "$CHAIN_SCRIPT" --describe "$state_path" \
    --instance-root "$INSTANCE_ROOT" --product-path "$product_path" \
    --project "$project" --steps "$STEPS" ${provider:+--provider "$provider"} \
    >"$describe_out" 2>&1 && rc=0 || rc=$?
  describe_text="$(cat "$describe_out")"
  rm -f "$describe_out"
  [ "$rc" -eq 0 ] || die "a start would be refused — ${describe_text#chain_development: }"
  change_key="$(printf '%s\n' "$describe_text" | sed -n 's/^key=//p')"
  entry_step="$(printf '%s\n' "$describe_text" | sed -n 's/^entry=//p')"
  step_providers="$(printf '%s\n' "$describe_text" | sed -n 's/^providers=//p')"
  # The ENTRY is what says the engine answered; the key is not, because a walk that has not
  # reached tobiishi-open has none and is exactly the walk this command exists to start. An
  # exit 0 naming no step is not an answer, and a DRY RUN block after it would report a walk
  # nothing checked.
  [ -n "$entry_step" ] || die "the engine's --describe named no entry step — it said: ${describe_text:-nothing}"
  echo "chain-change: change=${change_key:-(none yet)}"
  echo "chain-change: entry step=$entry_step"
  [ -z "$step_providers" ] || echo "chain-change: step providers=$step_providers"
  echo "DRY RUN — would run:"
  printf '  %q' "$@"; echo
  exit 0
fi

"$@"
