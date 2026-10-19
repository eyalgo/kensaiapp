#!/usr/bin/env bash
#
# launcher.sh (chain-product) — the owner's one command for a product's whole document chain.
# Version: 2.6.0 — ollama is a provider — a launch can run on the owner's local Ollama models
# Version: 2.5.0 — the providers file lives in the instance — each instance reads its own .providers.toml, and a tracked .providers.toml.example is the template
# Version: 2.4.0 — the launchers accept hf — the seven launchers, the run tools and the structure map take hf as a Claude run aimed at Hugging Face's router
# Version: 2.3.1 — the old three-seat SDD runner is retired — runner, seats, launcher, agents, template, [sdd] provider section and legacy reporter removed; dependants repointed
# Version: 2.3.0 — a stop ends the wait — one shared stop that ends a live walk across chain, chain_development and build_idea, marks it ended with a reason and leaves the state file readable
# Version: 2.2.2 — the chain leaves each SDD seat to its own entry — an unforced SDD launch carries no provider variable
# Version: 2.2.1 — the chain launchers state the provider truth and build-idea describe matches start
# Version: 2.2.0 — the providers file is reverted — every provider is back in code, and SDD runs on one provider again
# Version: 2.1.1 — every chain step and document reads its provider from system/providers.toml
# Version: 2.1.0 — a chain step names its provider, and --provider forces the whole walk
# Version: 2.0.0 — Grok is removed — the providers are Claude, Codex and Gemini
# Version: 1.6.0 — adapt Google Gemini as fourth model provider
# Version: 1.5.0 — Grok runs as a provider, model and effort
# Version: 1.4.0 — a run keeps the version it started on — every launcher enters a pin of core/, .claude/ and skills/
# Version: 1.3.0 — enable provider-neutral unattended execution with Codex
# Version: 1.2.0 — the refine report's Next moves gains an After column; build-idea runs that table in After order, and chain-change's end starts it
# Version: 1.1.0 — chain-definition, chain-foundation and the eight product document launchers are retired into chain-product and the skill launcher
# Version: 1.0.0 — created in place under the bare-identity folder name
#   <CORE>/launchers/chain-product/ (no relocation, no prior name, so no provenance block):
#   resolves <project>, declares the product spine as a fixed literal, resolves the completion
#   notifier from the environment, and hands the walk to core/tools/chain.py's --start entry
#   point.
#
# WHY THIS EXISTS
#   A product's companions are opened from downstream as well as by the chain's own rounds — a
#   run working the product raises an item on whichever document owes it, definition tier or
#   foundation tier. Two chains, one per tier, each swept only its own, and one state file per
#   project meant they could not walk a product at once: a companion in the tier nobody started
#   was never answered. One chain over every product document sweeps both, and it replaced them
#   (the owner, 2026-09-17).
#
# THE SPINE
#   PRD -> Agari -> SRS -> UXD -> DESIGN -> CONTENT -> SDD -> FDR -> ADR -> NFDR — both tiers,
#   upstream first, which is the order these documents read each other in. A document on disk
#   with no companion is walked past without launching anything, so a settled product costs a
#   walk and no run. The spine is a literal, not an argument: this launcher spawns no model and
#   holds no prompt, so the spine is what a caller must not reach into.
#
#   The name states the entry and the spine, not the blast radius (the owner's ruling,
#   2026-08-31): an owed bullet naming a launcher outside the spine is walked anyway.
#
# HOW A DOCUMENT IS LAUNCHED
#   Every producer runs as <CORE>/launchers/skill/launcher.sh <skill> <project>, from that
#   skill's own launcher.md, the SDD's included; the answer step is companion-self-answer's.
#   chain.py's header § How a document is launched owns the rule.
#
# USAGE
#   <CORE>/launchers/chain-product/launcher.sh <project> [--provider claude|codex|gemini|hf|ollama]
#                                                   [--on-end <command>] [--dry-run] [--keep-awake]
#     (run from the instance root)
#     <project>     a project under system/projects/<project>/
#     --provider    force every producer and answer run onto one provider, over the one its
#                   document's own entry names in .providers.toml at the instance root.
#                   An exported
#                   KENSAIAPP_AGENT_PROVIDER is the same force; the flag wins. With neither, each
#                   document's runs take their provider from that document's entry in the file,
#                   and an owed item whose path names no document from its [owed-items] entry;
#                   a launch whose entry is missing is refused, naming the entry, and nothing runs
#                   on a provider the file did not name. The force is kept on the walk's state,
#                   so it survives detached completion hooks.
#     --on-end <command>
#                   a command the walk runs once when it ends, sealed or halted, with the end
#                   appended as its last argument. It is how a caller that started this sweep is
#                   told when it is over (<CORE>/launchers/build-idea/launcher.sh starts the
#                   sweep a refine report names). This launcher only carries it to the engine;
#                   core/tools/chain.py runs it. Takes the next argument as its value.
#     --dry-run     print the resolved project, product path, spine and the exact engine
#                   invocation, but start nothing
#     --keep-awake  keep the Mac awake for the chain's duration; passed down to every launcher
#                   the chain runs rather than held here, because this script exits seconds
#                   after the FIRST run is launched and the chain goes on living in the
#                   detached runs the completion hook wakes. Each launcher already owns the
#                   mechanism through core/tools/detach_watcher.sh, so nothing here starts a
#                   caffeinate of its own. Needs a notifier/watcher.
#
#   <CORE>/launchers/chain-product/launcher.sh <project> --stop
#     --stop        stop the walk: the engine stops every run in flight, watcher first, signalling
#                   a process only while its pid still has the start time recorded at launch, ends
#                   the walk `stopped` and keeps its state file. Takes no other flag, and exits with
#                   the engine's status.
#
set -euo pipefail

# --- resolve the instance root (the caller's cwd) and cd there ----------------------
#   Same model as the sibling launchers: CORE_DIR strips this script's own resolved directory
#   at the /launchers/ boundary, so it reaches <CORE> from any nesting depth rather than by
#   counting a fixed two levels. The instance is the caller's cwd — this launcher derives no
#   instance identity of its own.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # <CORE>/launchers/chain-product
INSTANCE_ROOT="$PWD"
cd "$INSTANCE_ROOT"
CORE_DIR="${SCRIPT_DIR%/launchers/*}"
[ "$CORE_DIR" != "$SCRIPT_DIR" ] || { echo "chain-product: no /launchers/ ancestor above $SCRIPT_DIR — refusing to guess <CORE>" >&2; exit 1; }
SCRIPT_PATH="$SCRIPT_DIR/$(basename "${BASH_SOURCE[0]}")"
# shellcheck source=/dev/null
source "$CORE_DIR/tools/pin_run.sh"
pin_enter "$CORE_DIR" "$SCRIPT_PATH" "$@" || exit $?

# The engine's own CLI entry point. A path a caller may need to stub gets an override; a test
# points this at a recording fake so the real chain.py — which would try to launch a real
# producer launcher.sh for a missing document — is never reached from this suite. No caller
# ever wants a stub in production, only the real file at its real depth.
CHAIN_SCRIPT="${LAUNCH_CHAIN_PRODUCT_SCRIPT:-$CORE_DIR/tools/chain.py}"

# KENSAIAPP_NOTIFIER is resolved HERE, from the environment, and PASSED to the engine as a
# parameter — chain.py's own notifier port reads no environment for it
# (core/launchers/companion-self-answer/launcher.sh is the same layering). An unset notifier is
# skipped, never an error: the flag is simply omitted below.
NOTIFIER="${KENSAIAPP_NOTIFIER:-}"

# The product spine — a literal, not composed from an argument and not read from the
# caller's environment. This is the whole of what this launcher's own tests pin: a change to
# it is a test change and cannot pass unnoticed.
PRODUCT_SPINE="PRD,Agari,SRS,UXD,DESIGN,CONTENT,SDD,FDR,ADR,NFDR"

# The chain's own name — a literal beside the spine, on the same rule: not composed from an
# argument, not read from the environment. Lets the owner's completion channel tell this walk
# from a concurrent `chain-development` one, and lets a settled message name which walk stopped without reading
# the state file (the-chains-stop-announces-itself, leg 6).
CHAIN_NAME="product"

die() { echo "chain-product: $*" >&2; exit 1; }

# --- args --------------------------------------------------------------------------
project="${1:-}"
dry_run=""
keep_awake=""
on_end=""
stop=""
other_flag=""
# The force: the flag, else an exported KENSAIAPP_AGENT_PROVIDER, else none. Passed to the engine
# as a parameter and kept on its state — the engine sets the variable for each run it launches,
# so nothing here exports it.
provider="${KENSAIAPP_AGENT_PROVIDER:-}"
[ $# -eq 0 ] || shift
while [ $# -gt 0 ]; do
  case "$1" in
    --stop)       stop=1 ;;
    --dry-run)    dry_run=1; other_flag=1 ;;
    --keep-awake) keep_awake=1; other_flag=1 ;;
    --provider)   [ $# -ge 2 ] || die "--provider needs claude, codex, gemini, hf or ollama"
                  provider="$2"; other_flag=1; shift ;;
    --provider=*) provider="${1#--provider=}"; other_flag=1 ;;
    --on-end)     { [ $# -ge 2 ] && [ -n "$2" ]; } || die "--on-end needs a command"
                  on_end="$2"; other_flag=1; shift ;;
    --*)          die "unknown flag: $1" ;;
    *)            die "unexpected argument: $1" ;;
  esac
  shift
done
[ -n "$project" ] || die "usage: <CORE>/launchers/chain-product/launcher.sh <project> [--provider claude|codex|gemini|hf|ollama] [--on-end <command>] [--dry-run] [--keep-awake] | <project> --stop"
case "$provider" in ""|claude|codex|gemini|hf|ollama) ;; *) die "provider must be claude, codex, gemini, hf or ollama (got '$provider')" ;; esac

project_md="$INSTANCE_ROOT/system/projects/$project/project.md"
[ -f "$project_md" ] || die "no project card at $project_md (is '$project' a real project?)"

# --- resolve the Product path (strip the '**Product path:**' label + trailing comment)
raw_path="$(grep -m1 -E '^\*\*Product path:\*\*' "$project_md" \
  | sed -E 's/^\*\*Product path:\*\*[[:space:]]*//; s/[[:space:]]*<!--.*$//; s/[[:space:]]*$//' || true)"
[ -n "$raw_path" ] || die "no 'Product path:' line in $project_md"   # `|| true` above: pipefail would otherwise exit before this guard reports

# absolute / ~ → external; otherwise relative to the instance repo -------------------
case "$raw_path" in
  "~"/*) product_path="${HOME}/${raw_path#\~/}" ;;
  /*)    product_path="$raw_path" ;;
  *)     product_path="$INSTANCE_ROOT/$raw_path" ;;
esac

log_dir="$INSTANCE_ROOT/system/logs"
state_path="$log_dir/chain-$project-state.json"

# --- the owner's brake: handed to the engine, which stops the walk's runs and ends it --------
#   --stop stands alone. Another flag beside it names a start, and a start beside a stop means
#   neither, so it is refused before the engine runs.
if [ -n "$stop" ]; then
  [ -z "$other_flag" ] || die "usage: <CORE>/launchers/chain-product/launcher.sh <project> --stop — a stop takes no other flag"
  set -- python3 "$CHAIN_SCRIPT" --stop "$state_path"
  [ -n "$NOTIFIER" ] && set -- "$@" --notifier "$NOTIFIER"
  "$@" && rc=0 || rc=$?
  exit "$rc"
fi
shim_path="$log_dir/chain-$project.sh"

echo "chain-product: project=$project"
echo "chain-product: product path=$product_path"
echo "chain-product: spine=$PRODUCT_SPINE"
if [ -n "$provider" ]; then
  echo "chain-product: provider=$provider (forced on every document)"
else
  echo "chain-product: provider=each document's own"
fi

# --- hand the walk to the engine, through its --start CLI ---------------------------
#   set -- / "$@" is the corpus's own way of building a command so --dry-run can print
#   exactly what would run.
set -- python3 "$CHAIN_SCRIPT" --start "$state_path" \
  --instance-root "$INSTANCE_ROOT" --product-path "$product_path" \
  --project "$project" --core-dir "$CORE_DIR" --shim-path "$shim_path" \
  --spine "$PRODUCT_SPINE" --chain-name "$CHAIN_NAME"
[ -n "$NOTIFIER" ] && set -- "$@" --notifier "$NOTIFIER"
[ -n "$keep_awake" ] && set -- "$@" --keep-awake
[ -n "$on_end" ] && set -- "$@" --on-end "$on_end"
[ -n "$provider" ] && set -- "$@" --provider "$provider"

if [ -n "$dry_run" ]; then
  echo "DRY RUN — would run:"
  printf '  %q' "$@"; echo
  exit 0
fi

"$@"
