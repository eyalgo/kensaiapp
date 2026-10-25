#!/usr/bin/env bash
#
# launcher.sh (chain-development) — the owner's one command for the change pipeline, walked
# as a chain of step launchers.
#
# Version: 1.10.0 — the gate tool reads a walk's owner's-Mac ask itself, so a run cannot drop it
# Version: 1.9.0 — a gate run states its environment — gate_suite tool, environment declaration gate, owner-ask option
# Version: 1.8.1 — launchers and launch scripts take a portable mktemp template, so they run on Linux
# Version: 1.8.0 — ollama is a provider — a launch can run on the owner's local Ollama models
# Version: 1.7.0 — the providers file lives in the instance — each instance reads its own .providers.toml, and a tracked .providers.toml.example is the template
# Version: 1.6.0 — the launchers accept hf — the seven launchers, the run tools and the structure map take hf as a Claude run aimed at Hugging Face's router
# Version: 1.5.1 — the content seat split states what it made false, and the content step is audited
# Version: 1.5.0 — a stop ends the wait — one shared stop that ends a live walk across chain, chain_development and build_idea, marks it ended with a reason and leaves the state file readable
# Version: 1.4.1 — the chain launchers state the provider truth and build-idea describe matches start
# Version: 1.4.0 — the providers file is reverted — every provider is back in code, and SDD runs on one provider again
# Version: 1.3.1 — every chain step and document reads its provider from system/providers.toml
# Version: 1.3.0 — a chain step names its provider, and --provider forces the whole walk
# Version: 1.2.1 — the chain halts a TDD-lane task that landed without its red commit
# Version: 1.2.0 — a run keeps the version it started on — every launcher enters a pin of core/, .claude/ and skills/
# Version: 1.1.2 — ad-hoc-plan hands off to the chain; the station's five paths name the chain as their caller
# Version: 1.1.1 — chain-definition, chain-foundation and the eight product document launchers are retired into chain-product and the skill launcher
# Version: 1.1.0 — the development chain's dry run names the change and the entry step, and fails where a start would be refused
# Version: 1.0.0 — created in place under the bare-identity folder name
#   <CORE>/launchers/chain-development/ (no relocation, no prior name, so no provenance block):
#   resolves <project>, resolves the completion notifier from the environment, and hands the walk
#   to core/tools/chain_development.py's --start entry point.
#
# WHY THIS EXISTS
#   The change pipeline carries a change from change_request.md to sealed on main. This command
#   walks it deterministically, and no model decides what runs next: the engine starts each step
#   as its own `claude` run through <CORE>/launchers/skill/launcher.sh, reading that skill's
#   launcher.md, and starts the next step only when the previous run has ended and its artifact is
#   on disk.
#
# WHY IT PASSES NO SPINE
#   Its sibling chain-product hands chain.py a spine, because that engine
#   walks whatever documents it is given. The development pipeline is one fixed sequence with a
#   audit fan-out inside it (four runs, five when the change publishes text), so the step table lives in the engine as a literal it is
#   handed by its own composition root, and there is nothing here for a caller to reach into.
#
# WHY ITS STATE FILE IS ITS OWN
#   chain-product keeps system/logs/chain-<project>-state.json, one walk per project. A
#   development walk keeps chain-development-<project>-state.json, so it can carry a change on a
#   project whose definition documents are being walked at the same time.
#
# USAGE
#   <CORE>/launchers/chain-development/launcher.sh <project> [--provider claude|codex|gemini|hf|ollama] [--dry-run] [--keep-awake] [--gate-owners-mac]
#     (run from the instance root)
#     <project>     a project under system/projects/<project>/ with one active change folder
#     --provider    force every step of the walk onto one provider, over the one its own entry
#                   names in .providers.toml at the instance root. An exported
#                   KENSAIAPP_AGENT_PROVIDER is the
#                   same force; the flag wins. With neither, each step runs on its own entry in
#                   that file; a step whose entry is missing is refused, naming the entry, and
#                   nothing runs on a provider the file did not name.
#     --dry-run     ask the engine which change a start would carry and the step it would enter
#                   at, print those with the resolved project, product path and the exact engine
#                   invocation, and start nothing — or fail with the reason a start would be
#                   refused
#     --keep-awake  keep the Mac awake for the walk; passed down to every step launcher the engine
#                   runs rather than held here, because this script exits once the first step is
#                   launched and the walk goes on in the detached runs. Each step launcher already
#                   owns the mechanism through core/tools/detach_watcher.sh.
#     --gate-owners-mac
#                   the owner's ask to run the card's test command on the owner's Mac in the walk's developer, code-integrity, security and seal runs, in place of the environment the product resolves to. Without it, those runs use the owner's Mac only when the product has no CI. No card field, product record or exported variable sets it. The ask is kept on the walk's state, so an advance, a resume or a recovery keeps it.
#
#   <CORE>/launchers/chain-development/launcher.sh <project> --stop
#     --stop        stop the walk: the engine stops every run in flight, watcher first, signalling
#                   a process only while its pid still has the start time recorded at launch, ends
#                   the walk `stopped` and keeps its state file. Takes no other flag, and exits with
#                   the engine's status.
#
set -euo pipefail

# --- resolve the instance root (the caller's cwd) and cd there ----------------------
#   CORE_DIR strips this script's own resolved directory at the /launchers/ boundary, so it
#   reaches <CORE> from any nesting depth. The instance is the caller's cwd.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # <CORE>/launchers/chain-development
INSTANCE_ROOT="$PWD"
cd "$INSTANCE_ROOT"
CORE_DIR="${SCRIPT_DIR%/launchers/*}"
[ "$CORE_DIR" != "$SCRIPT_DIR" ] || { echo "chain-development: no /launchers/ ancestor above $SCRIPT_DIR — refusing to guess <CORE>" >&2; exit 1; }
SCRIPT_PATH="$SCRIPT_DIR/$(basename "${BASH_SOURCE[0]}")"
# shellcheck source=/dev/null
source "$CORE_DIR/tools/pin_run.sh"
pin_enter "$CORE_DIR" "$SCRIPT_PATH" "$@" || exit $?

# The engine's own CLI entry point. A test points this at a recording stub so a real --start —
# which would discover a change and launch a real run — is never reached from the suite.
CHAIN_SCRIPT="${LAUNCH_CHAIN_DEVELOPMENT_SCRIPT:-$CORE_DIR/tools/chain_development.py}"

# Resolved HERE, from the environment, and PASSED to the engine as a parameter — the engine reads
# no environment for it, because every advance re-enters as a fresh detached process. An unset
# notifier is skipped, never an error.
NOTIFIER="${KENSAIAPP_NOTIFIER:-}"

die() { echo "chain-development: $*" >&2; exit 1; }

# --- args --------------------------------------------------------------------------
project="${1:-}"
[ $# -eq 0 ] || shift
dry_run=""
keep_awake=""
gate_owners_mac=""
stop=""
other_flag=""
# The force: the flag, else an exported KENSAIAPP_AGENT_PROVIDER, else none. Passed to the engine
# as a parameter and kept on its state — the engine sets the variable for each run it launches,
# so nothing here exports it.
provider="${KENSAIAPP_AGENT_PROVIDER:-}"
while [ $# -gt 0 ]; do
  case "$1" in
    --stop)       stop=1 ;;
    --dry-run)    dry_run=1; other_flag=1 ;;
    --keep-awake) keep_awake=1; other_flag=1 ;;
    --gate-owners-mac) gate_owners_mac=1; other_flag=1 ;;
    --provider)   [ $# -ge 2 ] || die "--provider needs claude, codex, gemini, hf or ollama"
                  provider="$2"; other_flag=1; shift ;;
    --provider=*) provider="${1#--provider=}"; other_flag=1 ;;
    --*)          die "unknown flag: $1" ;;
    *)            die "unexpected argument: $1 — the change is discovered on disk, never named" ;;
  esac
  shift
done
[ -n "$project" ] || die "usage: <CORE>/launchers/chain-development/launcher.sh <project> [--provider claude|codex|gemini|hf|ollama] [--dry-run] [--keep-awake] [--gate-owners-mac] | <project> --stop"
case "$provider" in ""|claude|codex|gemini|hf|ollama) ;; *) die "provider must be claude, codex, gemini, hf or ollama (got '$provider')" ;; esac

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
state_path="$log_dir/chain-development-$project-state.json"

# --- the owner's brake: handed to the engine, which stops the walk's runs and ends it --------
#   --stop stands alone. Another flag beside it names a start, and a start beside a stop means
#   neither, so it is refused before the engine runs.
if [ -n "$stop" ]; then
  [ -z "$other_flag" ] || die "usage: <CORE>/launchers/chain-development/launcher.sh <project> --stop — a stop takes no other flag"
  set -- python3 "$CHAIN_SCRIPT" --stop "$state_path"
  [ -n "$NOTIFIER" ] && set -- "$@" --notifier "$NOTIFIER"
  "$@" && rc=0 || rc=$?
  exit "$rc"
fi

echo "chain-development: project=$project"
echo "chain-development: product path=$product_path"
if [ -n "$provider" ]; then
  echo "chain-development: provider=$provider (forced on every step)"
else
  echo "chain-development: provider=each step's own"
fi

# --- hand the walk to the engine, through its --start CLI ---------------------------
set -- python3 "$CHAIN_SCRIPT" --start "$state_path" \
  --instance-root "$INSTANCE_ROOT" --product-path "$product_path" \
  --project "$project" --core-dir "$CORE_DIR" --shim-dir "$log_dir"
[ -n "$NOTIFIER" ] && set -- "$@" --notifier "$NOTIFIER"
[ -n "$keep_awake" ] && set -- "$@" --keep-awake
[ -n "$gate_owners_mac" ] && set -- "$@" --gate-owners-mac
[ -n "$provider" ] && set -- "$@" --provider "$provider"

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
    --project "$project" ${provider:+--provider "$provider"} \
    >"$describe_out" 2>&1 && rc=0 || rc=$?
  describe_text="$(cat "$describe_out")"
  rm -f "$describe_out"
  [ "$rc" -eq 0 ] || die "a start would be refused — ${describe_text#chain_development: }"
  change_key="$(printf '%s\n' "$describe_text" | sed -n 's/^key=//p')"
  entry_step="$(printf '%s\n' "$describe_text" | sed -n 's/^entry=//p')"
  step_providers="$(printf '%s\n' "$describe_text" | sed -n 's/^providers=//p')"
  # An exit 0 that names no change or no step is not an answer, and a DRY RUN block printed after
  # it would report a walk nothing checked.
  [ -n "$change_key" ] && [ -n "$entry_step" ] || die "the engine's --describe named no change and entry step — it said: ${describe_text:-nothing}"
  echo "chain-development: change=$change_key"
  echo "chain-development: entry step=$entry_step"
  [ -z "$step_providers" ] || echo "chain-development: step providers=$step_providers"
  echo "DRY RUN — would run:"
  printf '  %q' "$@"; echo
  exit 0
fi

"$@"
