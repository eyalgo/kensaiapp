#!/usr/bin/env bash
#
# launcher.sh (companion-self-answer) — deterministic, pollution-proof launcher for a
# companion-self-answer run: answering an open-issues companion with nobody in the room.
# Version: 4.9.1 — launchers and launch scripts take a portable mktemp template, so they run on Linux
# Version: 4.9.0 — ollama is a provider — a launch can run on the owner's local Ollama models
# Version: 4.8.0 — the 19 agents load from their groups — agent files move to skills/<agent>/.claude/agents/ and every reader resolves them there
# Version: 4.7.0 — the providers file lives in the instance — each instance reads its own .providers.toml, and a tracked .providers.toml.example is the template
# Version: 4.6.0 — the launchers accept hf — the seven launchers, the run tools and the structure map take hf as a Claude run aimed at Hugging Face's router
# Version: 4.5.3 — rename the Content Editor seat to Content Manager across agent, loaders, prompts, skills, templates and tooling
# Version: 4.5.2 — the old three-seat SDD runner is retired — runner, seats, launcher, agents, template, [sdd] provider section and legacy reporter removed; dependants repointed
# Version: 4.5.1 — product-sdd becomes one CTO skill the chain carries like its siblings
# Version: 4.5.0 — A companion's items are answered per seat — an optional Seat: field, one sequential self-answer run per seat, one combined round
# Version: 4.4.0 — a stop ends the wait — one shared stop that ends a live walk across chain, chain_development and build_idea, marks it ended with a reason and leaves the state file readable
# Version: 4.3.0 — a pinned run sees only its own skill group
# Version: 4.2.0 — the eight skill launchers read their provider from the central providers file and refuse naming the entry when it is missing — no literal claude
# Version: 4.1.0 — the eleven other instrumented launchers stamp provider, model, effort and source through one shared resolution
# Version: 4.0.0 — Grok is removed — the providers are Claude, Codex and Gemini
# Version: 3.5.0 — chain skills carry their own intelligence — model and effort set per skill in intelligence/<provider>.md, no agent pins a model
# Version: 3.4.0 — adapt Google Gemini as fourth model provider
# Version: 3.3.0 — Load Codex skills natively from the current pin across all three launchers
# Version: 3.2.0 — Grok runs as a provider, model and effort
# Version: 3.1.0 — the self-answer seat check reads the global loaders in <CORE>, which every pin carries
# Version: 3.0.0 — the three chains run Claude as a detached claude -p process, not claude --bg
# Version: 2.14.0 — product-sdd and companion-self-answer start every run at --effort high on both providers
# Version: 2.13.0 — a run keeps the version it started on — every launcher enters a pin of core/, .claude/ and skills/
# Version: 2.12.0 — companion-self-answer honors Codex selection and completion callbacks
# Version: 2.11.0 — a consumer satellite gets no root skills/ link — its launchers find skill groups in the host
# Version: 2.10.1 — every product-* skill but product-setup, and the Content Manager's three, move into their seat's group
# Version: 2.10.0 — chain-definition, chain-foundation and the eight product document launchers are retired into chain-product and the skill launcher
# Version: 2.9.0 — companion-self-answer resolves <document> in both of the project's homes
# Version: 2.8.1 — the seat-fallback comment drops scrum-master as its standing case: the seat has an agent file since 946c80af
# Version: 2.8.0 — a launcher may live nested under core/launchers/development/, and its reach resolves <CORE> from its own location instead of counting folders
# Version: 2.7.0 — a launcher-started record says which instance, product and operation it was for — instrument_run stamps them, chain.py ties a walk, and the step-name seed is parked by the owner's ruling
# Version: 2.6.0 — the backgrounded launchers are tagged too — every launcher hands its telemetry to the spawn as --settings; station 2 closes and the seed is set down
# Version: 2.5.0 — station 2's instrument lands — every launcher tags its own run, and the receiver answers only this machine
# Version: 2.4.0 — a launcher's `--agent` value is checked for a loader before it is taken as a seat.
#   a launcher can pass `--agent delegate`, a tool grant with no posture, and the grep alone would
#   have handed a companion to it as a lens.
# Version: 2.3.1 — the vendored layer names no product, and the rule that licensed it is gone
# Version: 2.3.0 — the chain reads the run it made — five fixes off its first live run
# Version: 2.2.0 — a companion with no document behind it resolves. The target was resolved through
#   a document entry that had to exist, so `<project> architecture` refused: product-architecture's
#   companion answers for the ADR and the NFDR together and no docs/architecture.md is ever written.
#   With no document entry the stem is now read off the COMPANION entry instead. Only a stem with
#   neither file is refused, and that message names both paths.
# Version: 2.1.1 — a document's answer-trail is filed under trail/<doc>/ in the document's own directory, not left as its sibling
# Version: 2.0.1 — rebuilt. v1 (`b68d56de`) took a bare `<target>` and is deleted: it could not
#   reach a satellite that does not sit beside this instance, could not take this instance's own
#   `<satellite>/<project>` addressing, and could not name which companion to answer at all — its
#   prompt was fixed at "scoped to the target", while the skill's own Input requires a companion
#   path. This version takes `<project> <document>` instead, resolved like every `product-*`
#   sibling, and derives the document + companion from `<document>` with no sweep and no list.
#   Seat resolution — the one designed part — carries over from v1 unchanged; it was never the
#   defect.
#
# THE MODEL, AND THE ONE PLACE IT ADDS SOMETHING
#   `product-fdr`'s own launcher for the address resolution: the project card lookup, the
#   `Product path:` read stripped through its trailing HTML comment, the absolute/`~`-vs-relative
#   `--add-dir` split, `--instance-root`, `--dry-run`, `--keep-awake`, the sourced detach tail.
#
#   THE ADDITION: seat resolution, kept from v1. Every sibling launcher builds a FIXED
#   `--agent <name>`; this one has no fixed seat to build, because the run it starts answers
#   whichever companion it is handed, and different companions are produced by different skills
#   that hold different seats. So the seat is READ, never mapped, from the companion itself:
#     1. read the companion's header `re-run \`<skill>\`` line;
#     2. read THAT skill's own `launcher.md` `**Agent:**` line — the declaration
#        <CORE>/launchers/skill/launcher.sh starts it from, found through core/tools/skill_path.py;
#     3. for a skill with no `launcher.md`, read its own launcher's `--agent` value — its
#        bare-identity folder first, then the fixed prompt-literal grep the skill's own Step 6
#        names for a folder that does not carry the bare name.
#   No table of skills to seats appears here, ever — a table would drift the day a new producing
#   skill lands, invisibly.
#
#   TWO FALLBACKS, NEITHER A HALT. No companion, no re-run line, no launcher for the named skill,
#   or a seat whose agent file is not on disk — all four land on a seatless session. The fourth also
#   tells the run, in its own fixed prompt, which seat it could not take. Nothing the answerer
#   finds ever blocks the launch — except a producer whose intelligence is broken, below.
#
#   THE MODEL IS THE PRODUCER'S. The producing skill's `intelligence/<provider>.md` — the same skill
#   the `re-run` line names, found through core/tools/skill_path.py — gives `--model <id>` on every
#   provider (core/doctrine/governance/skill_intelligence.md), read through the one resolution
#   every instrumented launcher shares (core/tools/run_intelligence.py). Its `**Effort:**` is not
#   read: the effort is `high` on every run. A producer that cannot be derived, or has no
#   `intelligence/` folder, launches with no `--model` — the provider's own default, never a model
#   this launcher picks. A producer whose folder holds no file for the provider, or a malformed
#   one, refuses the launch naming the file: there is no fallback.
#
# TWO ENV OVERRIDES BEYOND THE USUAL WATCHER/NOTIFIER PAIR
#   Seat resolution reads two directories that are otherwise this launcher's own fixed, real-repo
#   paths — <CORE>/launchers/ (to find a sibling skill's launcher) and the host's skill groups,
#   skills/ (to find a seat's agent file at skills/<group>/.claude/agents/<seat>.md) — and both get
#   the same override `LAUNCH_<X>_<THING>` shape every other stubbable path in this file gets: a
#   test that read the REAL <CORE>/launchers/ or skills/ would pass or fail on whatever this repo
#   happens to hold that day, which is exactly what `LAUNCH_COMPANION_SELF_ANSWER_LAUNCHERS_DIR` /
#   `LAUNCH_COMPANION_SELF_ANSWER_AGENT_GROUPS_DIR` let a fixture tree replace.
#
# USAGE
#   <CORE>/launchers/companion-self-answer/launcher.sh <project> <document> [--provider claude|codex|gemini|hf|ollama] [--dry-run] [--keep-awake]
#     (run from the instance root)
#     <project>     a project under system/projects/<project>/
#     <document>    which document's companion to answer — any document carrying the open-issues
#                   pattern, named as the document is named (FDR, PRD, …); matched against the
#                   docs/ entry case-insensitively, and used at the case the FILE carries
#     --provider    claude, codex, gemini, hf or ollama; else KENSAIAPP_AGENT_PROVIDER, else the
#                   `launchers.companion-self-answer` entry of .providers.toml at the instance
#                   root, else a refusal — there is no default. An hf run is the Claude run,
#                   aimed at Hugging Face's router, and it is refused unless ~/.env holds a
#                   non-empty HF_TOKEN. An ollama run is the Claude run, aimed at the local
#                   Ollama server, and it is refused unless that server answers
#     --dry-run     print the resolved document, companion, seat and provider launch command;
#                   launch nothing
#     --keep-awake  keep the Mac awake (caffeinate) for the run's duration; needs a
#                   notifier/watcher
#     --instance-root <dir>   override the instance root (default: cwd); must come first
#   Both positionals are required — the skill halts without a companion, so a launcher that
#   defaulted either would hand it nothing to answer. Anything after them that is not a known
#   flag is REFUSED, never silently ignored — a caller cannot append prose to what the run
#   receives.
#
#   <document> is a NAME, never a path, and this launcher holds no list of documents. It is
#   resolved against a DIRECTORY ENTRY in one of the project's two document homes —
#   $product_path/docs/ and system/projects/<project>/ — and used at that entry's own case:
#     document  = the <home>/*.md whose stem matches <document> case-insensitively
#     companion = <that stem>_open_issues.md, beside it
#   The home is whichever holds the document or its companion; a name in both is refused.
#   Never composed by re-casing <document>: six of the seven documents are upper-case on disk and
#   the FDR alone is lower (skills/principal-pm/.claude/skills/product-fdr/SKILL.md:68), so no casing rule is right for all
#   seven and any that tried would need the list this file may not hold.
#   An absent companion is not refused — the round report says which was found, and the launch
#   goes ahead; the skill's own Step 1 is what decides what an absent companion means for its run.
#   An absent DOCUMENT is not refused either, since 2026-08-31: a companion may stand alone, and
#   then the stem is read off the companion's entry instead. See THE BARE COMPANION STEM below.
#   Only a stem with NEITHER file, in either home, is refused — there is nothing to answer.
#
# ONE RUN PER SEAT
#   An open item in the companion may carry `- **Seat:** <seat>`. The launcher reads the open items
#   through core/tools/companion_items.py, resolves each tag with the checks it already holds for
#   the producer's seat (a case-insensitive agent-file match, then a loader), and groups the items
#   by RESOLVED seat, in the order each group's first open item appears. An untagged item takes the
#   producer's seat. A tag naming a posture-free agent, or no agent file, is the seatless fallback;
#   the item is kept there, and in the no-agent-file case the run's prompt names the seat it could
#   not take. One group is today's launch, unchanged: one run, today's prompt, no item list. Two or more
#   are one run per group, each carrying `Answer only these items: <n>, <n>.`, every one on the same
#   provider, the producer's model and effort high, handed to core/tools/detached_sequence.py so
#   that run k+1 starts only after run k's process has ended. Every command is validated before
#   anything starts. A companion whose items cannot be read launches once, as today, after one
#   `Grouping:  skipped` line.
#
# COMPLETION NOTIFICATION
#   agent_run.py --background starts the run as one detached process — Claude's `--print
#   --output-format stream-json`, or Codex's `exec --json` — and returns its pid, its run log and,
#   for Claude, its session id. watch_process.py observes it (through the shared home below) until
#   the provider ends the turn, then reports through the notifier and hands the chain's
#   DETACH_WATCHER_ON_COMPLETE hook its outcome. With no executable notifier the watch still runs,
#   so a chain's hook still fires. Override the pair with LAUNCH_COMPANION_SELF_ANSWER_WATCHER /
#   LAUNCH_COMPANION_SELF_ANSWER_NOTIFIER.
#
# THE SHARED COMPLETION-WATCH HOME (core/tools/detach_process_watcher.sh)
#   Sourced, never hand-copied. No env override: unlike $WATCHER, no test or caller ever wants a
#   stub in its place, only the real file at its real relative depth.
#
# THE REPORTER
#   `--reporter companion-self-answer`: `core/tools/reporters.py` reads the run's own report file
#   (highest-numbered `trail/<doc>/self_answer-<N>.md` under the document homes) and composes what the run did,
#   rather than the bare `generic` "run ended." The suite asserts this value against the real
#   REGISTRY, never a literal, because `get_reporter` falls back to `generic` for an unknown name
#   without raising. `--artifact-path` is a ROOT the reporter globs document homes under, never the
#   companion's own file path: the PRODUCT PATH for a document in its docs/, the INSTANCE ROOT for
#   one in system/projects/<project>/.
#
# PERMISSIONS / CONTEXT (identical rationale to the sibling launchers)
#   A Claude run is `claude --print --output-format stream-json`, never `claude --bg`, with
#   --permission-mode auto --permission-prompts none: nobody can answer a prompt in an unattended
#   run, and a --print run with no prompt to fall back to denies the action and keeps working rather
#   than waiting (https://code.claude.com/docs/en/permission-modes.md § When auto mode falls back).
#   NOT a bypass, NOT --dangerously-skip-permissions — see ~/.claude/CLAUDE.md § Permission mode.
#   --add-dir is added only for an external (absolute or `~`) product path.
#
set -euo pipefail

# --- resolve the instance root (the caller's cwd) and cd there ----------------------
#   This tool lives in <CORE>/launchers/companion-self-answer/ and is shared across instances, so
#   it CANNOT derive its instance from its own location. The instance is the caller's cwd;
#   --instance-root overrides. The cd is load-bearing: the run inherits THIS shell's cwd.
#   SCRIPT_DIR is a sibling of <CORE>/tools/; the watcher and the shared completion-watch home
#   resolve via CORE_DIR — derived from this folder's own location, not a fixed number of parent
#   steps. The sibling-launchers dir is one hop up. The agent groups are found under the host root,
#   and the loaders under <CORE>.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # <CORE>/launchers/companion-self-answer
CORE_DIR="${SCRIPT_DIR%/launchers/*}"
[ "$CORE_DIR" != "$SCRIPT_DIR" ] || { echo "companion-self-answer: no /launchers/ ancestor above $SCRIPT_DIR — refusing to guess <CORE>" >&2; exit 1; }
SCRIPT_PATH="$SCRIPT_DIR/$(basename "${BASH_SOURCE[0]}")"
# shellcheck source=/dev/null
source "$CORE_DIR/tools/pin_run.sh"
pin_enter "$CORE_DIR" "$SCRIPT_PATH" "$@" || exit $?
SKILLS_ROOT="${LAUNCH_COMPANION_SELF_ANSWER_SKILLS_ROOT:-${CORE_DIR%/core}}"   # the host root: a satellite holds no skills of its own
INSTANCE_ROOT="$PWD"
[ "${1:-}" = "--instance-root" ] && { INSTANCE_ROOT="$2"; shift 2; }
cd "$INSTANCE_ROOT"
INSTANCE_ROOT="$PWD"   # re-resolved absolute, even when --instance-root was given relative

# Completion-notification pair (see the watcher block at the bottom).
WATCHER="${LAUNCH_COMPANION_SELF_ANSWER_WATCHER:-$CORE_DIR/tools/watch_process.py}"
NOTIFIER="${LAUNCH_COMPANION_SELF_ANSWER_NOTIFIER:-${KENSAIAPP_NOTIFIER:-}}"
DETACH_LIB="$CORE_DIR/tools/detach_process_watcher.sh"
# The launch half of the process path — required, unlike the watcher home: nothing launches without it.
RUN_LIB="$CORE_DIR/tools/detached_run.sh"
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

# Seat resolution reads two more paths — both stubbable, per the header note above.
LAUNCHERS_DIR="${LAUNCH_COMPANION_SELF_ANSWER_LAUNCHERS_DIR:-$SCRIPT_DIR/..}"
GROUPS_DIR="${LAUNCH_COMPANION_SELF_ANSWER_AGENT_GROUPS_DIR:-$SKILLS_ROOT/skills}"
# The global loaders live in <CORE>, so they are in every pin the launcher runs from; an instance's
# system/loaders/ is not, and a pin holds no system/ for a path beside the script to reach.
LOADERS_DIR="${LAUNCH_COMPANION_SELF_ANSWER_LOADERS_DIR:-$CORE_DIR/roles/loaders}"

die() { echo "companion-self-answer: $*" >&2; exit 1; }

usage="usage: <CORE>/launchers/companion-self-answer/launcher.sh <project> <document> [--provider claude|codex|gemini|hf|ollama] [--dry-run] [--keep-awake]"

# --provider overrides KENSAIAPP_AGENT_PROVIDER; absent both, the launcher's entry in
# .providers.toml at the instance root decides, and a missing entry is refused.
# Every provider's run goes through agent_run.py and the structured process observer,
# including chain callbacks.
# --- args --------------------------------------------------------------------------
#   Positionals first (project, document), each refused with its own message when absent or
#   flag-shaped; flags after them, and an unknown one is REFUSED rather than silently ignored.
project="${1:-}"
case "$project" in
  ""|--*) die "$usage
    <project> is required — a project under system/projects/<project>/" ;;
esac
document="${2:-}"
case "$document" in
  ""|--*) die "$usage
    <document> is required — which document's companion to answer (e.g. FDR, PRD)" ;;
esac
shift 2

dry_run=""
keep_awake=""
provider=""
provider_given=""   # --provider was on the command line, whatever its value (an empty one is refused)
while [ "$#" -gt 0 ]; do
  arg="$1"
  case "$arg" in
    --dry-run)    dry_run=1 ;;
    --keep-awake) keep_awake=1 ;;
    --provider) [ "$#" -ge 2 ] || die "--provider needs claude, codex, gemini, hf or ollama"
                provider="$2"; provider_given=1; shift ;;
    --provider=*) provider="${arg#--provider=}"; provider_given=1 ;;
    *) die "unknown argument: $arg" ;;
  esac
  shift
done

# --- the provider: the flag, else the variable, else the launcher's entry in .providers.toml ---
# The reader (core/tools/providers.py) owns that rule and is handed the force; a force is never
# looked up in the file. An exported-but-empty variable is no force, and an explicitly given empty
# --provider is no force either — it falls through to the check below and is refused as unknown.
# `providers.py` imports the intelligence resolver, so both are checked before the reader is run.
if [ -n "$provider_given" ]; then
  forced="$provider"
else
  forced="${KENSAIAPP_AGENT_PROVIDER:-}"
fi
if [ -z "$provider_given" ] || [ -n "$forced" ]; then
  [ -f "$PROVIDERS_TOOL" ] || die "no provider reader at $PROVIDERS_TOOL"
  [ -f "$RUN_INTELLIGENCE" ] || die "no intelligence resolver at $RUN_INTELLIGENCE"
  provider_err="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-self-answer-provider.XXXXXX")"
  provider="$(python3 "$PROVIDERS_TOOL" launcher companion-self-answer --instance-root "$INSTANCE_ROOT" --forced "$forced" 2>"$provider_err")" && rc=0 || rc=$?
  provider_msg="$(cat "$provider_err")"
  rm -f "$provider_err"
  [ "$rc" -eq 0 ] || die "${provider_msg:-could not read the provider for the companion-self-answer launcher}"
fi
case "$provider" in claude|codex|gemini|hf|ollama) ;; *) die "provider must be claude, codex, gemini, hf or ollama (got '$provider')" ;; esac
export KENSAIAPP_AGENT_PROVIDER="$provider"

project_md="$INSTANCE_ROOT/system/projects/$project/project.md"
[ -f "$project_md" ] || die "no project card at $project_md (is '$project' a real project?)"

# --- resolve the Product path (strip the '**Product path:**' label + trailing comment)
raw_path="$(grep -m1 -E '^\*\*Product path:\*\*' "$project_md" \
  | sed -E 's/^\*\*Product path:\*\*[[:space:]]*//; s/[[:space:]]*<!--.*$//; s/[[:space:]]*$//' || true)"
[ -n "$raw_path" ] || die "no 'Product path:' line in $project_md"   # `|| true` above: pipefail would otherwise exit before this guard reports

# absolute / ~ → external; otherwise relative to the instance repo -------------------
add_dir=""
case "$raw_path" in
  "~"/*) product_path="${HOME}/${raw_path#\~/}"; add_dir=1 ;;
  /*)    product_path="$raw_path";              add_dir=1 ;;
  *)     product_path="$INSTANCE_ROOT/$raw_path" ;;   # internal: covered by cwd, no --add-dir
esac

# --- resolve the document + companion from <document>, at the case the file carries -------
#   A NAME, never a path, and no list of documents anywhere in this file: the match is against
#   a DIRECTORY ENTRY in one of the two document homes, never membership in an enumeration.
#
#   WHY THE CASE IS READ AND NEVER COMPOSED. Six of the seven documents are upper-case on disk
#   and the FDR alone is lower — skills/principal-pm/.claude/skills/product-fdr/SKILL.md:68 says it outright: "The three
#   names are lowercase, and they match each other on purpose." So neither lower-casing nor upper-casing <document> is right for all seven, and
#   a rule that picked one would need a list of exceptions — the one thing this file may never
#   hold. Reading the entry needs no rule and no list: whatever docs/ is named, that is the name.
#   And composing it cannot be caught downstream: this host is case-insensitive (APFS), so the
#   -f guard passes on a mis-cased path and nothing is refused — the wrong string just reaches
#   the prompt, which is the one thing this launcher exists to compose.
# THE DOCUMENT HOMES. A project's documents do not all live in its product's docs/: the Agari is
# written into the instance, at system/projects/<project>/agari.md, and its companion beside it
# (kensaiapp_structure.md § 2, Per-project). A launcher that looked in docs/ alone refused a
# live Agari companion, 2026-09-17. So <document> is resolved in both of the project's homes —
# the same two `core/tools/reporters.py`'s `self_answer_reports_present` walks for it — and in
# nothing else: two DIRECTORIES, never a list of which document lives where. The home that holds
# the document or its companion is the one used; neither is refused, and both is refused too,
# because picking one would be a guess.
product_home="$product_path/docs"
project_home="$INSTANCE_ROOT/system/projects/$project"

# The <dir>/*.md whose stem equals the wanted stem case-insensitively, printed at its OWN case.
# The one case-resolution both the document and its companion go through: a stem in, the
# matching entry's REAL path out. Never compose a name from another name's case.
resolve_docs_entry() {
  local wanted="$1" dir="${2:-$docs_dir}" candidate stem
  wanted="$(printf '%s' "$wanted" | tr '[:upper:]' '[:lower:]')"
  for candidate in "$dir"/*.md; do
    [ -f "$candidate" ] || continue          # an unmatched glob is the literal pattern itself
    stem="${candidate##*/}"
    stem="${stem%.md}"
    [ "$(printf '%s' "$stem" | tr '[:upper:]' '[:lower:]')" = "$wanted" ] || continue
    printf '%s' "$candidate"
    return 0
  done
  return 1
}

resolve_document_stem() {
  local path
  path="$(resolve_docs_entry "$1")" || return 1
  path="${path##*/}"
  printf '%s' "${path%.md}"
}

# THE BARE COMPANION STEM. A companion may stand alone, with no document entry behind it:
# product-architecture's is `docs/architecture_open_issues.md` — "named for neither document it
# answers for", because one run writes both the ADR records
# and the NFDR and one companion carries the unsettled items for both. No `docs/architecture.md`
# is ever written, so the document lookup below cannot succeed for it.
#
# The document file was never the RUN's requirement, only this guard's: the skill reads what it
# needs off the companion's own header (SKILL.md:62-63, "This skill knows no list of producing
# skills, documents, or companion paths, and must never grow one"), and the prompt this launcher
# composes names the companion and never the document. So the guard relaxes (owner, 2026-08-31):
# with no document entry, the stem is read off the COMPANION entry instead and the launch goes
# ahead against the companion alone.
#
# `architecture` appears here in prose and nowhere in a `case` arm or a lookup — it is the case
# that forced the change, not a document this file knows. Any stem behaves the same way.
#
# NEITHER FILE STILL REFUSES: there is nothing to answer. That refusal composes both paths,
# because there is no entry to read a case off, and it spells <document> exactly as the caller
# gave it rather than showing them a re-cased guess.
holds_document() {
  resolve_docs_entry "$document" "$1" >/dev/null || resolve_docs_entry "${document}_open_issues" "$1" >/dev/null
}
docs_dir=""
for home in "$product_home" "$project_home"; do
  holds_document "$home" || continue
  [ -z "$docs_dir" ] \
    || die "'$document' is in both of the project's homes — $docs_dir and $home — and which one to answer is not this launcher's to guess"
  docs_dir="$home"
done
[ -n "$docs_dir" ] \
  || die "no document at $product_home/$document.md or $project_home/$document.md, and no companion at $product_home/${document}_open_issues.md or $project_home/${document}_open_issues.md (is '$document' a real document for this project?)"
# The root the reporter walks document homes under: the product for its docs/, the instance for
# system/projects/<project>/, which a product path does not contain.
if [ "$docs_dir" = "$product_home" ]; then report_root="$product_path"; else report_root="$INSTANCE_ROOT"; fi

document_path=""
if doc_stem="$(resolve_document_stem "$document")"; then
  document_path="$docs_dir/${doc_stem}.md"
else
  # The companion's own entry, at its own case — the same read the document half does, for the
  # same reason (see WHY THE CASE IS READ above): composing `${document}_open_issues.md` from the
  # argument's case names a file no directory entry matches, and a case-insensitive volume opens
  # it anyway rather than refusing.
  bare_companion="$(resolve_docs_entry "${document}_open_issues")"   # the home was chosen for holding it
  bare_companion="${bare_companion##*/}"
  doc_stem="${bare_companion%_open_issues.md}"
  # Only the STEM is carried out of this branch, not the path: the companion resolution below is
  # left as the single place a companion path is produced, so the two branches cannot drift.
fi
# The companion's case is read off disk too, for the same reason the document's is — and it is
# NOT safe to derive from the document's own case. Measured 2026-08-30 on a live product: the document
# is docs/SRS.md and its companion on disk is docs/srs_open_issues.md, because the run that
# opened it took the stem from the lowercase TEMPLATE filename. Composing `${doc_stem}_open_...`
# names a file that does not exist, and a case-insensitive volume hides that by opening it
# anyway — so the path handed to the run is one no directory entry matches.
# `|| companion_path=""` on the ASSIGNMENT, not on a following line: an absent companion is an
# ordinary state here (the run still launches), but the lookup exits non-zero to say so, and
# under `set -e` an unguarded assignment would take the whole script down with it.
companion_path="$(resolve_docs_entry "${doc_stem}_open_issues")" || companion_path=""
# No entry to read a case off, so the absent one is composed — it is named in a message, never
# opened, and it spells the stem the document actually carries.
[ -n "$companion_path" ] || companion_path="$docs_dir/${doc_stem}_open_issues.md"

if [ -n "$document_path" ]; then
  echo "Document:  $document_path"
else
  echo "Document:  none — no $docs_dir/$document.md; answering a companion that stands alone"
fi
if [ -f "$companion_path" ]; then
  echo "Companion: present — $companion_path"
else
  echo "Companion: absent — no open-issues file at $companion_path (the skill halts without one)"
fi

# --- resolve the seat, from the companion — read, never mapped ---------------------
#   Three functions kept from v1: they were never the defect (see the header). No table of
#   skills to seats appears anywhere in this file, ever.
read_producing_skill() {
  grep -m1 -o 're-run `[^`]*`' "$1" 2>/dev/null | sed -E 's/^re-run `//; s/`$//' || true
}

# Bare-identity folder first; the fixed prompt-literal grep second, for a folder that does not
# carry the skill's bare name (the skill's own Step 6 § naming a launcher).
find_skill_launcher() {
  local skill="$1"
  if [ -f "$LAUNCHERS_DIR/$skill/launcher.sh" ]; then
    printf '%s' "$LAUNCHERS_DIR/$skill/launcher.sh"
    return 0
  fi
  local hit
  hit="$(grep -rl "invoke the $skill skill" "$LAUNCHERS_DIR"/*/launcher.sh 2>/dev/null | head -1 || true)"
  [ -n "$hit" ] || return 1
  printf '%s' "$hit"
}

# Anchored on the adjacent `--permission-mode` so a comment mentioning `--agent` in prose
# (`# WHY NO --agent`, "no `--agent` is ever passed") can never be misread as a value — only the
# real `--agent <name> --permission-mode` invocation line matches.
read_seat_from_launcher() {
  grep -m1 -oE -- '--agent [A-Za-z0-9_-]+ --permission-mode' "$1" 2>/dev/null \
    | awk '{print $2}' || true
}

# A launcher's `--agent` value is not proof of a seat. Some agents carry a tool grant and a model
# pin and no posture at all — `delegate` is one — and taking one as this run's seat would answer a
# companion under a lens that does not exist. What separates them is a loader: every seat has
# `<CORE>/roles/loaders/<role_file>_global.md` and a posture-free agent has none.
# `<CORE>/doctrine/setup/authoring_layers.md` § *The carriers* states the rule this checks.
# The role_file spelling is the hyphenated name underscored — `tech-lead` -> `tech_lead_global.md`.
seat_has_loader() {
  [ -f "$LOADERS_DIR/$(printf '%s' "$1" | tr '-' '_')_global.md" ]
}

# The agent file a name resolves to, across every group — `$GROUPS_DIR/<group>/.claude/agents/<name>.md`
# — printed at its own case, or nothing and a non-zero exit when no group holds it. Exact by default,
# for the producer seat; with `fold` as the second argument the stem match is case-insensitive, for an
# item's `Seat:` tag, the same `tr` fold `resolve_docs_entry` applies to a docs stem. The groups are
# read in sorted order, so a name two groups hold answers the same file on every run.
resolve_group_agent() {
  local wanted="$1" mode="${2:-exact}" candidate stem
  [ "$mode" = fold ] && wanted="$(printf '%s' "$wanted" | tr '[:upper:]' '[:lower:]')"
  for candidate in "$GROUPS_DIR"/*/.claude/agents/*.md; do
    [ -f "$candidate" ] || continue          # an unmatched glob is the literal pattern itself
    stem="${candidate##*/}"
    stem="${stem%.md}"
    [ "$mode" = fold ] && stem="$(printf '%s' "$stem" | tr '[:upper:]' '[:lower:]')"
    [ "$stem" = "$wanted" ] || continue
    printf '%s' "$candidate"
    return 0
  done
  return 1
}

# A skill started through <CORE>/launchers/skill/launcher.sh declares its seat in its own
# launcher.md — the **Agent:** line, read exactly as that launcher reads it — and has no launcher
# folder of its own. So the declaration is read first; a launcher folder is read only for a skill
# that has none.
find_skill_declaration() {
  local dir
  dir="$(python3 "$CORE_DIR/tools/skill_path.py" "$1" --root "$SKILLS_ROOT" 2>/dev/null)" || return 1
  [ -f "$dir/launcher.md" ] || return 1
  printf '%s' "$dir/launcher.md"
}

read_seat_from_declaration() {
  grep -m1 -E '^\*\*Agent:\*\*' "$1" 2>/dev/null \
    | sed -E 's/^\*\*Agent:\*\*[[:space:]]*//; s/[[:space:]]*<!--.*$//; s/[[:space:]]*$//' || true
}

producing_skill=""
skill_launcher=""
seat=""
if [ -f "$companion_path" ]; then
  producing_skill="$(read_producing_skill "$companion_path")"
  if [ -n "$producing_skill" ]; then
    if skill_launcher="$(find_skill_declaration "$producing_skill")"; then
      seat="$(read_seat_from_declaration "$skill_launcher")"
    elif skill_launcher="$(find_skill_launcher "$producing_skill")"; then
      seat="$(read_seat_from_launcher "$skill_launcher")"
    fi
  fi
fi

# --- the run's model: the producing skill's own intelligence (THE MODEL IS THE PRODUCER'S) ---
#   Resolved through the one resolution, with the producer's dir when one is derived and none
#   otherwise, so an underivable producer and a producer with no folder both answer `default`.
#   The answer's effort is dropped: `run_effort` is this launcher's own `high`, the one value
#   every provider branch below is handed and the stamp records.
run_effort=high
producer_dir=""
if [ -n "$producing_skill" ]; then
  producer_dir="$(python3 "$CORE_DIR/tools/skill_path.py" "$producing_skill" --root "$SKILLS_ROOT" 2>/dev/null)" || producer_dir=""
fi
resolution_args=(--provider "$provider")
[ -z "$producer_dir" ] || resolution_args+=(--skill-dir "$producer_dir")
resolution_err="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-self-answer-intelligence.XXXXXX")"
resolution="$(python3 "$RUN_INTELLIGENCE" "${resolution_args[@]}" 2>"$resolution_err")" && rc=0 || rc=$?
resolution_msg="$(cat "$resolution_err")"
rm -f "$resolution_err"
case "$rc" in
  0) ;;
  4|2) die "$resolution_msg" ;;
  *) die "could not read the intelligence of '${producing_skill:-the producer}' — $resolution_msg" ;;
esac
run_model="$(printf '%s\n' "$resolution" | sed -n 's/^model=//p')"
run_source="$(printf '%s\n' "$resolution" | sed -n 's/^source=//p')"
if [ "$run_source" = intelligence ]; then
  echo "Intelligence: $producer_dir/intelligence/$provider.md"
elif [ -n "$producer_dir" ]; then
  echo "Intelligence: none — $producing_skill has no intelligence/ folder; provider default model"
else
  echo "Intelligence: none — no producing skill derivable; provider default model"
fi

# --- build the launch command: FIXED prompt, only launcher-DERIVED values interpolated ----
base_prompt="invoke the companion-self-answer skill for the companion at ${companion_path}."

# The producer's own outcome: a seat, or the seatless fallback with the sentence that says why.
producer_group="seatless"
producer_cause=""
seat_file=""
[ -z "$seat" ] || seat_file="$(resolve_group_agent "$seat")" || seat_file=""
if [ -n "$seat_file" ] && seat_has_loader "$seat"; then
  echo "Seat:      $seat (from ${skill_launcher})"
  producer_group="seat:$seat"
else
  if [ -n "$seat_file" ]; then
    echo "Seat:      $seat named by ${skill_launcher} is a posture-free agent, not a seat — no loader at $LOADERS_DIR/… — falling back to a seatless session"
  elif [ -n "$seat" ]; then
    echo "Seat:      $seat named by ${skill_launcher}, but no agent file for it in any group — falling back to a seatless session"
    producer_cause="In your report, say that this run could not take the '$seat' seat named by the companion's producing skill's launcher — no agent file exists for it."
  else
    echo "Seat:      none derivable — falling back to a seatless session"
  fi
fi

# --- group the companion's open items by the seat each resolves to ---------------------------
#   `core/tools/companion_items.py` lists the open items and their raw `Seat:` tags and resolves
#   nothing: this launcher owns the resolution, because `resolve_docs_entry` and `seat_has_loader`
#   have one owner here. An untagged item takes the producer's outcome above, unchanged. A tag is
#   matched case-insensitively against the agent files and used at the file's own spelling; one that
#   names an agent with a loader is that seat, and one that names a posture-free agent or no agent
#   file at all is the seatless fallback — the item is kept either way. Groups are keyed on the
#   RESOLVED seat, in the order each group's first open item appears. Parallel indexed arrays and a
#   linear lookup: this runs on bash 3.2, which has no associative array and no mapfile.
group_keys=()          # `seat:<name>` or `seatless`
group_items=()         # the group's item numbers, ", "-joined, in companion order
group_causes=()        # the fallback sentences the group's prompt carries, space-joined, no repeats
group_reasons=()       # why the group's items are here, "; "-joined, no repeats
group_untagged=()      # "1" once an item with no usable tag joined the group

# Append "$2" to "$1" with separator "$3" unless it is already a part of it.
append_unique() {
  case "$3$1$3" in
    *"$3$2$3"*) printf '%s' "$1" ;;
    *) if [ -z "$1" ]; then printf '%s' "$2"; else printf '%s%s%s' "$1" "$3" "$2"; fi ;;
  esac
}

# add_to_group <key> <item number> <fallback sentence> <reason> <untagged: 1|"">
add_to_group() {
  local key="$1" number="$2" cause="$3" reason="$4" untagged="$5" i=0 n="${#group_keys[@]}"
  while [ "$i" -lt "$n" ]; do
    [ "${group_keys[$i]}" = "$key" ] && break
    i=$((i + 1))
  done
  if [ "$i" -eq "$n" ]; then
    group_keys[$i]="$key"; group_items[$i]=""; group_causes[$i]=""; group_reasons[$i]=""
    group_untagged[$i]=""
  fi
  group_items[$i]="$(append_unique "${group_items[$i]}" "$number" ", ")"
  [ -z "$cause" ] || group_causes[$i]="$(append_unique "${group_causes[$i]}" "$cause" " ")"
  group_reasons[$i]="$(append_unique "${group_reasons[$i]}" "$reason" "; ")"
  [ -z "$untagged" ] || group_untagged[$i]=1
  return 0
}

COMPANION_ITEMS="$CORE_DIR/tools/companion_items.py"
if [ -f "$companion_path" ]; then
  if [ -f "$COMPANION_ITEMS" ] && open_items="$(python3 "$COMPANION_ITEMS" open-items "$companion_path" 2>/dev/null)"; then
    while IFS=$'\t' read -r item_number item_tag; do
      [ -n "$item_number" ] || continue
      if [ -z "$item_tag" ]; then
        add_to_group "$producer_group" "$item_number" "$producer_cause" \
          "no Seat field — the producing skill's seat" 1
        continue
      fi
      tag_file="$(resolve_group_agent "$item_tag" fold)" || tag_file=""
      if [ -z "$tag_file" ]; then
        add_to_group seatless "$item_number" \
          "In your report, say that this run could not take the '$item_tag' seat named by an item's Seat field — no agent file exists for it." \
          "Seat: $item_tag names no agent file" ""
        continue
      fi
      tag_seat="${tag_file##*/}"
      tag_seat="${tag_seat%.md}"
      if seat_has_loader "$tag_seat"; then
        add_to_group "seat:$tag_seat" "$item_number" "" "Seat: $item_tag" ""
      else
        add_to_group seatless "$item_number" "" \
          "Seat: $item_tag is a posture-free agent, not a seat" ""
      fi
    done <<<"$open_items"
  else
    echo "Grouping:  skipped — the open items of $companion_path could not be read; launching one run as today"
  fi
fi

group_count="${#group_keys[@]}"
group_seat() { [ "${group_keys[$1]}" = seatless ] || printf '%s' "${group_keys[$1]#seat:}"; }

if [ "$group_count" -eq 0 ]; then
  # No open item, an absent companion, or an unreadable one: today's launch, the producer's outcome.
  run_seat=""
  [ "$producer_group" = seatless ] || run_seat="${producer_group#seat:}"
  run_prompt_text="$base_prompt${producer_cause:+ $producer_cause}"
elif [ "$group_count" -eq 1 ]; then
  # One group is one run with today's prompt and no item list, under that group's seat.
  run_seat="$(group_seat 0)"
  run_prompt_text="$base_prompt${group_causes[0]:+ ${group_causes[0]}}"
  if [ -z "${group_untagged[0]}" ]; then
    if [ -n "$run_seat" ]; then
      echo "Seat:      $run_seat (from the Seat field of ${group_items[0]})"
    else
      echo "Seat:      none — ${group_reasons[0]} — falling back to a seatless session"
    fi
  fi
fi

# --- the run's command: one function, called once per group ---------------------------------
#   The Claude command comes from the one adapter (Task 19), never assembled here — the pin was
#   entered right after the CORE_DIR guard above. `--shape turn` is `claude --print --output-format
#   stream-json`, named up front with a session id. The two forms — a resolved seat's --agent, and
#   the seatless fallback — stay distinct, matching the seat resolution above. The model is the
#   producer's on either (`run_model`), and absent when the producer declares none. Every group is
#   built with the same provider, model and effort: no seat has a provider or model of its own.
#   Sets `run_cmd`.
build_run_command() {
  local run_seat="$1" prompt="$2" log="$3" skill_dir agent_file run_prompt codex_prompt
  if [ "$provider" = claude ] || [ "$provider" = hf ] || [ "$provider" = ollama ]; then
    # `hf` and `ollama` are the Claude run aimed at another endpoint: the same command, with
    # the runner's `--provider "$provider"` picking the adapter.
    set -- python3 "$CORE_DIR/tools/agent_run.py" --provider "$provider" --shape turn --pin auto \
      --instance-root "$INSTANCE_ROOT" --prompt "$prompt" \
      --effort "$run_effort" --grant-skill companion-self-answer
    [ -z "$run_seat" ] || set -- "$@" --agent "$run_seat"
    [ -z "$run_model" ] || set -- "$@" --model "$run_model"
    [ -z "$add_dir" ] || set -- "$@" --add-dir "$product_path"
  elif [ "$provider" = gemini ]; then
    skill_dir="$(python3 "$CORE_DIR/tools/skill_path.py" companion-self-answer --root "$SKILLS_ROOT")" \
      || die "cannot resolve companion-self-answer under $SKILLS_ROOT"
    [ -f "$skill_dir/SKILL.md" ] || die "no SKILL.md at $skill_dir"
    run_prompt="$prompt"
    if [ -n "$run_seat" ]; then
      agent_file="$(resolve_group_agent "$run_seat")"
      run_prompt="You are running as the $run_seat agent. Read $agent_file in full and follow it as your agent identity before doing this task: $prompt"
    fi
    set -- python3 "$CORE_DIR/tools/agent_run.py" --provider gemini --prompt "$run_prompt" \
      --core-dir "$CORE_DIR" \
      --add-dir "$skill_dir" --effort "$run_effort"
    [ -z "$run_model" ] || set -- "$@" --model "$run_model"
    [ -z "$add_dir" ] || set -- "$@" --add-dir "$product_path"
  else
    skill_dir="$(python3 "$CORE_DIR/tools/skill_path.py" companion-self-answer --root "$SKILLS_ROOT")" \
      || die "cannot resolve companion-self-answer under $SKILLS_ROOT"
    [ -f "$skill_dir/SKILL.md" ] || die "no SKILL.md at $skill_dir"
    codex_prompt="You are running a Kensaiapp unattended companion-self-answer task. For every instruction, <CORE> resolves to: $CORE_DIR. The instance root is: $INSTANCE_ROOT. "
    if [ -n "$run_seat" ]; then
      agent_file="$(resolve_group_agent "$run_seat")"
      codex_prompt+="Take the $run_seat seat. Before doing anything else, read and follow $agent_file. "
    fi
    [ "$provider" = codex ] || codex_prompt+="Read and follow $skill_dir/SKILL.md. "
    codex_prompt+="Execute this fixed task: $prompt"
    set -- python3 "$CORE_DIR/tools/agent_run.py" --provider "$provider" --prompt "$codex_prompt" \
      --core-dir "$CORE_DIR" \
      --add-dir "$SKILLS_ROOT" --effort "$run_effort"
    [ -z "$run_model" ] || set -- "$@" --model "$run_model"
    [ "$provider" != codex ] || set -- "$@" --skill-name companion-self-answer --skill-path "$skill_dir/SKILL.md"
    [ -z "$add_dir" ] || set -- "$@" --add-dir "$product_path"
  fi
  # Handed to a Claude run as --settings, folded into the pin's one merged document — the same
  # channel every sibling uses (measured 2026-09-10 on a `claude --bg` session, which an exported
  # variable never reached).
  case "$provider" in
    claude|hf|ollama) [ -z "${INSTRUMENT_RUN_SETTINGS:-}" ] || set -- "$@" --settings "$INSTRUMENT_RUN_SETTINGS" ;;
  esac
  set -- "$@" --background --log "$log"
  run_cmd=("$@")
}

# --- tag this run before it spawns (the shared instrument home) -------------------
#   Unconditional, not behind a flag — the caller sets no argument and exports no variable.
#   Called ahead of the dry-run branch too, so a dry run states the arm it would run under
#   rather than hiding the instrument; the exports it makes here die with this script when
#   --dry-run exits before anything is spawned.
if [ -f "$INSTRUMENT_LIB" ]; then
  # shellcheck source=/dev/null
  source "$INSTRUMENT_LIB"
  instrument_run project="$project" document="$document" provider="$provider" model="$run_model" effort="$run_effort" source="$run_source"
else
  echo "          (no instrument library at $INSTRUMENT_LIB — run uninstrumented)"
fi

[ -f "$RUN_LIB" ] || die "no detached-run library at $RUN_LIB"
# shellcheck source=/dev/null
source "$RUN_LIB"

run_log_base="$INSTANCE_ROOT/system/logs/$provider-self-answer-$project-$doc_stem-$(date -u +%Y%m%d-%H%M%S)-$$"
watch_log=""

if [ "$group_count" -le 1 ]; then
  # --- one run: today's launch, whichever the provider (the shared home) ----------------
  run_log="$run_log_base.jsonl"
  watch_log="$run_log"
  build_run_command "$run_seat" "$run_prompt_text" "$run_log"
  set -- "${run_cmd[@]}"

  if [ -n "$dry_run" ]; then
    echo "DRY RUN — would launch:"
    print_detached_run "$@" || die "the $provider launch was refused — nothing would launch"
    exit 0
  fi

  mkdir -p "$INSTANCE_ROOT/system/logs"
  echo "Launching companion-self-answer for '$project'/'$document' through $provider (background)…"
  start_detached_run "$@" || die "the $provider launch did not start — nothing launched"
  announce_detached_run "$run_log"
else
  # --- several runs: one per seat, one after another, through one detached sequence ------
  #   Every command is built and validated before anything starts — a refusal on any one refuses
  #   the whole launch, as one refused run does today, rather than reaching the chain as a failed
  #   hook after earlier seats had committed. The plan lines are JSON arrays written through
  #   python: a prompt cannot be quoted into JSON from bash.
  if [ -n "$dry_run" ]; then
    echo "DRY RUN — would launch $group_count runs, one after another:"
  fi
  plan_lines=""
  run_logs=()
  k=0
  while [ "$k" -lt "$group_count" ]; do
    n=$((k + 1))
    group_run_seat="$(group_seat "$k")"
    run_prompt_text="$base_prompt Answer only these items: ${group_items[$k]}.${group_causes[$k]:+ ${group_causes[$k]}}"
    run_logs[$k]="$run_log_base-$n.jsonl"
    build_run_command "$group_run_seat" "$run_prompt_text" "${run_logs[$k]}"
    if [ -n "$dry_run" ]; then
      echo "Run $n of $group_count: seat ${group_run_seat:-seatless} — items ${group_items[$k]}"
      echo "  Why: ${group_reasons[$k]}"
      print_detached_run "${run_cmd[@]}" || die "the $provider launch of run $n was refused — nothing would launch"
    else
      print_detached_run "${run_cmd[@]}" >/dev/null \
        || die "the $provider launch of run $n was refused — nothing launched"
    fi
    plan_lines+="$(python3 -c 'import json, sys; print(json.dumps(sys.argv[1:]))' "${run_cmd[@]}")"$'\n'
    k=$n
  done
  [ -z "$dry_run" ] || exit 0

  mkdir -p "$INSTANCE_ROOT/system/logs"
  plan_file="$run_log_base-plan.jsonl"
  sequence_log="$run_log_base-sequence.log"
  watch_log="$run_log_base-completion.jsonl"
  printf '%s' "$plan_lines" > "$plan_file"
  echo "Launching companion-self-answer for '$project'/'$document' through $provider (background): $group_count runs, one after another…"
  start_detached_run python3 "$CORE_DIR/tools/detached_sequence.py" \
    --plan "$plan_file" --log "$sequence_log" --completion-log "$watch_log" \
    || die "the $provider launch did not start — nothing launched"
  echo "Launched. Sequence log: $sequence_log"
  printf '          Run log: %s\n' "${run_logs[@]}"
fi

# --- background the completion watcher, through the shared home --------------------
#   The run outlives this script, so the script's exit says nothing about the run. The shared home
#   (core/tools/detach_process_watcher.sh) does the detach, the logging, and --keep-awake's
#   caffeinate bind — this launcher only resolves the values and calls it. A missing library is
#   reported and skipped, never fatal — the primary run has already launched by this point.
#   For several runs the pid is the sequence runner's and the log is the completion log it fills
#   once the last run's process is dead: a watcher on the last seat's own log would end at that
#   seat's terminal event, before its process has.
if [ -f "$DETACH_LIB" ]; then
  # shellcheck source=/dev/null
  source "$DETACH_LIB"
  detach_process_watcher \
    --watcher "$WATCHER" --provider "$provider" --notifier "$NOTIFIER" \
    --instance-root "$INSTANCE_ROOT" --label "$project-$doc_stem" --log-stem "$project-$doc_stem" \
    --reporter companion-self-answer --artifact-path "$report_root" --document-stem "$doc_stem" \
    --pid "$DETACHED_RUN_PID" --run-log "$watch_log" \
    ${keep_awake:+--keep-awake}
else
  echo "          (no completion-watch library at $DETACH_LIB — completion watch skipped)"
fi

# --- record who this launch is, for the engine that named a file for it ---------------------
#   After the watcher block, so its pid is known. A no-op when the engine named no file, and it
#   never fails the launch (`core/tools/detached_run.sh`).
record_detached_run_identity
