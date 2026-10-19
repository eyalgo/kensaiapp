#!/usr/bin/env bash
#
# launcher.sh (skill) — the one launcher for every skill that declares an unattended launch. It
# reads that skill's own `launcher.md` and starts the run the file describes through the selected
# provider: the one --provider names, else KENSAIAPP_AGENT_PROVIDER, else this launcher's
# `launchers.skill` entry in .providers.toml at the instance root, else a refusal. Whichever
# provider that is, the run is one detached process the provider-neutral agent runner starts and
# one watcher observes.
# Version: 4.8.1 — launchers and launch scripts take a portable mktemp template, so they run on Linux
# Version: 4.8.0 — ollama is a provider — a launch can run on the owner's local Ollama models
# Version: 4.7.0 — the board drops a halt another launcher resumed, and shows a single skill run
# Version: 4.6.0 — the 19 agents load from their groups — agent files move to skills/<agent>/.claude/agents/ and every reader resolves them there
# Version: 4.5.0 — the providers file lives in the instance — each instance reads its own .providers.toml, and a tracked .providers.toml.example is the template
# Version: 4.4.0 — the launchers accept hf — the seven launchers, the run tools and the structure map take hf as a Claude run aimed at Hugging Face's router
# Version: 4.3.0 — a stop ends the wait — one shared stop that ends a live walk across chain, chain_development and build_idea, marks it ended with a reason and leaves the state file readable
# Version: 4.2.0 — a pinned run sees only its own skill group
# Version: 4.1.0 — the eight skill launchers read their provider from the central providers file and refuse naming the entry when it is missing — no literal claude
# Version: 4.0.0 — the providers file is reverted — every provider is back in code, and SDD runs on one provider again
# Version: 3.6.0 — a skill launched on its own reads its provider from providers.toml
# Version: 3.5.0 — experience-voice and experience-visual launch through the skill launcher
# Version: 3.4.0 — kensaiapp-writing-bar launches through the skill launcher
# Version: 3.3.0 — the eleven other instrumented launchers stamp provider, model, effort and source through one shared resolution
# Version: 3.2.1 — Gemini launcher runs are handed the run ID and OTEL settings; agy 1.2.13 cannot emit, so the change is not reached
# Version: 3.2.0 — runs record provider, model, effort and source, and run_provenance.py finds them by run ID
# Version: 3.1.0 — a Codex launcher run emits to the receiver
# Version: 3.0.0 — Grok is removed — the providers are Claude, Codex and Gemini
# Version: 2.4.0 — chain skills carry their own intelligence — model and effort set per skill in intelligence/<provider>.md, no agent pins a model
# Version: 2.3.0 — adapt Google Gemini as fourth model provider
# Version: 2.2.0 — Load Codex skills natively from the current pin across all three launchers
# Version: 2.1.0 — Grok runs as a provider, model and effort
# Version: 2.0.0 — the three chains run Claude as a detached claude -p process, not claude --bg
# Version: 1.8.0 — a launcher.md effort reaches the run — agent_run.py takes --effort, the skill launcher forwards **Effort:**, twenty chain-started declarations carry their levels
# Version: 1.7.2 — the first refactor sweep of core/launchers: four behaviour-neutral packets and its report
# Version: 1.7.1 — a dry run with no pin in force still resolves its agent file
# Version: 1.7.0 — a run keeps the version it started on — every launcher enters a pin of core/, .claude/ and skills/
# Version: 1.6.0 — enable provider-neutral unattended execution with Codex
# Version: 1.5.0 — the skill launcher looks the skill up under the host root, so a satellite needs no skills symlink
# Version: 1.4.0 — nemawashi-unpick launches through the skill launcher, which gains a bounded reason argument
# Version: 1.3.0 — a launcher.md may name its completion reporter, and the eight product declarations do
# Version: 1.2.0 — tobiishi-open moves to the skills/pm/ group, and the skill launcher grants a grouped skill its group
# Version: 1.1.0 — the skill launcher's message names the instance and the project beside the skill
# Version: 1.0.0 — created in place under the bare-identity folder name <CORE>/launchers/skill/
#   (no relocation, no prior name, so no provenance block).
#
# WHAT IS GENERAL HERE, AND WHAT IS THE SKILL'S
#   This file names no skill. What differs from one skill to the next — the agent, the arguments the
#   run takes, the prompt it receives and the reporter its completion message is written by — is
#   read from `<skill dir>/launcher.md`, and the model and effort the run goes at from
#   `<skill dir>/intelligence/<provider>.md` (INTELLIGENCE below).
#   What is the same for every run — resolving <CORE> and the instance, refusing a malformed call
#   before anything spawns, the telemetry tag, `--dry-run`, the detach and the completion
#   notification — lives here, once. A skill gains a launch by gaining a `launcher.md`; neither its
#   SKILL.md nor this file changes.
#
# WHY A LAUNCHER (same reason as every sibling)
#   A session asked to "run this skill" *composes* the run's prompt, and that is the one place
#   stray context leaks in. The prompt is a FIXED literal in launcher.md; a caller passes only the
#   argument values that file declares. Nothing else a caller types reaches the run.
#
# THE launcher.md CONTRACT
#   Found in the skill's directory, which <CORE>/tools/skill_path.py resolves from the name (flat
#   or grouped layout) under the host — the instance whose core/ this launcher lives in — never
#   under the caller's instance: a satellite holds no skills of its own (see THE SKILLS ARE THE
#   HOST'S below). Each field is the first line that BEGINS with its bold label; a trailing
#   `<!-- comment -->` is stripped. Every other line is prose for a reader and is never read here.
#
#     **Agent:**      the `--agent` the run starts under. Its agent file must exist, in a group as
#                     `skills/<group>/.claude/agents/<agent>.md`, or as the instance's own
#                     `.claude/agents/<agent>.md`, which wins by name.
#                     Optional, but a file with no **Agent:** is refused when its skill has no
#                     `intelligence/` folder: such a run has neither a seat nor a declared model.
#     **Arguments:**  the argument shape, space-separated: `<name>` is required, `[<name>]` is
#                     optional, and every optional one follows every required one. Absent means the
#                     run takes no argument.
#     **Prompt:**     the fixed prompt, one line — required. `{name}` becomes that argument's value.
#                     A `[ … ]` segment is dropped whole when a placeholder inside it names an
#                     optional argument the caller did not give; an optional argument's placeholder
#                     outside such a segment is a defect.
#     **Reporter:**   the completion watcher's `--reporter`: a name in REGISTRY in
#                     core/tools/reporters.py. Absent means `generic`, which is what every
#                     declaration written before this field gets, unchanged. Any other reporter
#                     needs **Reads:**, because every one of them reads the thing the run authored.
#     **Reads:**      what that reporter reads, handed to the watcher as `--artifact-path`:
#                       product   the project's Product path, resolved as for the grant below
#                       project   the project's own directory, system/projects/<project>
#                       instance  the instance root the run starts in — for an instance-level
#                                 skill, whose document belongs to no project
#                     The first two need `<project>` in **Arguments:**; `instance` needs no
#                     argument. A **Reads:** with no **Reporter:** is a defect.
#     **Requires:**   programs the run cannot do without, space-separated bare names. Each is
#                     looked up with `command -v` after the caller's values are judged and before
#                     anything spawns, `--dry-run` included, and a missing one refuses the launch
#                     naming it: a run that would reach a step with nothing to run is refused
#                     while someone is still there to install it. Absent means none.
#
#   A declared reporter is best-effort at launch, like the product grant: when the path it reads
#   is not there — no card, no Product path line, no directory, an optional <project> not given —
#   the launcher warns and the watch falls back to `generic`. The message is never why a run is
#   refused.
#
#   What an argument NAME means is fixed here, never in launcher.md:
#     project    a project name: refused when path-shaped or when system/projects/<name>/ does not
#                exist. Its card's `Product path:`, when absolute or `~` and present on disk, is
#                granted with `--add-dir` — best-effort: a missing card, line or directory warns
#                and the launch goes on, because what the product holds is the skill's to read.
#     *path      a path that must exist — absolute, `~`, or relative to the instance root.
#     reason     free text a prompt carries inside double quotes: refused when it is not valid
#                UTF-8, when it is blank, when it holds a line break, any other control character or
#                an invisible format character (a zero-width space, a bidi override), when it holds a
#                double quote (which would close the quoted value and put the rest of the text
#                outside it), or when it is longer than 300 characters — counted as characters,
#                whatever the locale. It is the one argument that may begin with '-': a reason such
#                as "- blocked upstream" is prose.
#     any other  a bare word: refused when path-shaped (contains '/', or begins with '.') or when it
#                begins with '-'.
#
#   A defect in launcher.md is refused naming the file, before any argument value is judged and
#   before anything spawns — it is a fault in the skill's declaration, not in the call.
#   A **Model:** or an **Effort:** line is one: a run's intelligence is its skill's, not its
#   declaration's (INTELLIGENCE below).
#
# INTELLIGENCE — THE MODEL AND EFFORT A RUN GOES AT
#   `<skill dir>/intelligence/<provider>.md` (core/doctrine/governance/skill_intelligence.md) holds
#   `**Model:**` and, optionally, `**Effort:**` for one provider. `<CORE>/tools/run_intelligence.py`
#   is the one resolution every instrumented launcher shares — it reads that file through
#   `intelligence.py`, else a named tier through `model_assignment.py` — and its exit status and
#   `source=` answer are what this launcher acts on:
#     0, `source=intelligence`  the file's model goes on as `--model <id>` and its effort, when
#        declared, as `--effort <level>`, raw, on every provider. No Kensaiapp tier is resolved and
#        no agent file is read for a model.
#     0, `source=default`  the skill has no `intelligence/` folder and no tier was named: no
#        `--model` and no effort, so the run goes at the provider's own default.
#     0, `source=tier`  no folder, and the caller named a tier (MODEL TIER below).
#     4  the folder holds no file for the provider: refused naming the missing path, nothing
#        spawned — there is no fallback.
#     2  the file is malformed: refused naming it and why.
#
# MODEL TIER — A SKILL WITH NO INTELLIGENCE, AT A NAMED TIER
#   `--model-tier fable|opus|sonnet|haiku` is judged right after the provider, through
#   <CORE>/tools/model_assignment.py, which refuses any other tier with one line naming the four. It
#   is refused on a skill that has an `intelligence/` folder — whatever the folder holds, a file,
#   none for the provider, or a malformed one (the resolver's exit 6) — because that skill's model
#   and effort come from its intelligence file, not from a tier. On a skill with none the runner is
#   handed `--model-tier`, never the model and effort it resolves to, so the run and its stamp read
#   the one resolver.
#
# THE RUN'S PROVENANCE, STAMPED
#   The one instrument_run call hands over provider=, model=, effort= and source=, exactly as
#   run_intelligence.py answered them: `intelligence` (the file's values), `tier` (a named tier,
#   model_assignment.py's values) or `default` (neither — no model, no effort). They reach the
#   printed `Telemetry:` line with the rest.
#
# A GROUPED SKILL'S GROUP IS GRANTED
#   A skill at `skills/<group>/.claude/skills/<name>/` is hidden from a session at startup, so a run
#   started without its group never sees the skill it was launched for. When the resolved directory
#   is grouped, `skills/<group>/` is granted with `--add-dir` — on the Codex path. A Claude run
#   reaches the group instead because this launcher grants the skill (`--grant-skill`), which puts
#   the skill's group, and the groups its `depends-on:` names, in the pin's plugin; no group
#   `--add-dir` on that path. The group is read off where the skill lives, never off **Agent:** —
#   a declaration with no **Agent:** still reaches its skill. A flat skill is indexed from cwd and
#   gains no flag.
#
# THE SKILLS ARE THE HOST'S
#   The skill is looked up under the host root, `<CORE>/..`, which this launcher knows from its own
#   path — not under the instance root it was started from. Under a pin, `<CORE>/..` is the pin root,
#   so the skill is looked up in the pin. A satellite binds <CORE> to its host and holds no skills, so
#   looking under the satellite only ever reached the host through a `skills` symlink. In the host
#   itself the two roots are the same directory and nothing changes. The agent file, the project and
#   the cwd stay the instance's. LAUNCH_SKILL_SKILLS_ROOT overrides the host root, for the tests.
#
# NO WORKTREE IS OPENED
#   The run works in the instance root this launcher sets as its working directory; whether the
#   skill opens a worktree of its own is that skill's.
#
# USAGE
#   <CORE>/launchers/skill/launcher.sh <skill> [<argument>...] [--provider claude|codex|gemini|hf|ollama] [--model-tier fable|opus|sonnet|haiku] [--dry-run] [--keep-awake]
#            (run from the instance root)
#     <skill>       a skill NAME whose directory holds a launcher.md — never a path
#     <argument>    the values launcher.md's **Arguments:** declares, in its order
#     --dry-run     print the resolved skill, its arguments and the exact provider command; launch nothing
#     --keep-awake  keep the Mac awake for the observed run's duration, whatever the provider
#     --provider    claude, codex, gemini, hf or ollama; else KENSAIAPP_AGENT_PROVIDER, else the
#                   `launchers.skill` entry of .providers.toml at the instance root, else a
#                   refusal — there is no default. An hf run is the Claude run, aimed at Hugging
#                   Face's router, and it is refused unless ~/.env holds a non-empty HF_TOKEN.
#                   An ollama run is the Claude run, aimed at the local Ollama server, and it is
#                   refused unless that server answers
#     --model-tier  run a skill with no intelligence/ folder at this tier (MODEL TIER above)
#     --instance-root <dir>   override the instance root (default: cwd); must come first
#   The four flags may sit anywhere after <skill>. Any other argument starting with '--', or
#   starting with '-' and holding no space, and any value past the ones launcher.md declares, is
#   REFUSED, never silently ignored. An argument starting with a single '-' and holding a space is
#   a value, which only a <reason> accepts.
#
# COMPLETION NOTIFICATION
#   agent_run.py --background starts the run as a detached process and returns its pid, the log it
#   writes (system/logs/<provider>-<skill>-<UTC stamp>-<pid>.jsonl — Claude's stream-json, Codex's
#   JSONL) and, for Claude, the session id it named the conversation with. watch_process.py observes
#   that process through detach_process_watcher.sh until the provider ends the turn, and reports
#   through KENSAIAPP_NOTIFIER, hands the chain's DETACH_WATCHER_ON_COMPLETE hook its outcome, and
#   owns the reporter and keep-awake contract. With no executable notifier the watch still runs, so
#   a chain's hook still fires. Override the pair with LAUNCH_SKILL_WATCHER / LAUNCH_SKILL_NOTIFIER.
#
# THE SHARED HOMES (<CORE>/tools/agent_run.py, <CORE>/tools/detached_run.sh,
#                   <CORE>/tools/detach_process_watcher.sh, <CORE>/tools/instrument_run.sh,
#                   <CORE>/tools/skill_path.py)
#   Sourced or called, never hand-copied. No env override: no test or caller ever wants a stub in
#   their place, only the real files at their real relative depth.
#
# PERMISSIONS / CONTEXT (identical rationale to the sibling launchers)
#   A Claude run is `claude --print --output-format stream-json`, never `claude --bg`, with
#   --permission-mode auto --permission-prompts none: nobody can answer a prompt in an unattended
#   run, and a --print run with no prompt to fall back to denies the action and keeps working rather
#   than waiting (https://code.claude.com/docs/en/permission-modes.md § When auto mode falls back;
#   https://code.claude.com/docs/en/headless.md § Turn off permission prompts in unattended runs).
#   NOT a bypass, NOT --dangerously-skip-permissions — see ~/.claude/CLAUDE.md § Permission mode.
#
set -euo pipefail

# --- resolve the instance root (the caller's cwd) and cd there ----------------------
#   This tool lives in <CORE>/launchers/skill/ and is shared across instances, so it CANNOT derive
#   its instance from its own location. The instance is the caller's cwd; --instance-root
#   overrides. The cd is load-bearing: the selected provider inherits THIS shell's cwd.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # <CORE>/launchers/skill
CORE_DIR="${SCRIPT_DIR%/launchers/*}"
[ "$CORE_DIR" != "$SCRIPT_DIR" ] || { echo "skill: no /launchers/ ancestor above $SCRIPT_DIR — refusing to guess <CORE>" >&2; exit 1; }
SCRIPT_PATH="$SCRIPT_DIR/$(basename "${BASH_SOURCE[0]}")"
# shellcheck source=/dev/null
source "$CORE_DIR/tools/pin_run.sh"
pin_enter "$CORE_DIR" "$SCRIPT_PATH" "$@" || exit $?
INSTANCE_ROOT="$PWD"
[ "${1:-}" = "--instance-root" ] && { INSTANCE_ROOT="$2"; shift 2; }
cd "$INSTANCE_ROOT"
INSTANCE_ROOT="$PWD"   # re-resolved absolute, even when --instance-root was given relative
SKILLS_ROOT="${LAUNCH_SKILL_SKILLS_ROOT:-${CORE_DIR%/core}}"   # the host root — THE SKILLS ARE THE HOST'S

# Completion-notification pair (see the watcher block at the bottom).
WATCHER="${LAUNCH_SKILL_WATCHER:-$CORE_DIR/tools/watch_process.py}"
NOTIFIER="${LAUNCH_SKILL_NOTIFIER:-${KENSAIAPP_NOTIFIER:-}}"
DETACH_LIB="$CORE_DIR/tools/detach_process_watcher.sh"
RUN_LIB="$CORE_DIR/tools/detached_run.sh"
INSTRUMENT_LIB="$CORE_DIR/tools/instrument_run.sh"
RESOLVER="$CORE_DIR/tools/skill_path.py"
AGENT_RUN="$CORE_DIR/tools/agent_run.py"
RUN_INTELLIGENCE="$CORE_DIR/tools/run_intelligence.py"
PROVIDERS_TOOL="$CORE_DIR/tools/providers.py"
MODEL_ASSIGNMENT="$CORE_DIR/tools/model_assignment.py"
PIN_TOOL="$CORE_DIR/tools/pin.py"

# The one path an agent name resolves to. The instance's own `.claude/agents/<name>.md` wins when
# it holds one. Otherwise it is the group file `skills/<group>/.claude/agents/<name>.md`: the pin's,
# or with no pin in force, the instance's and then the host's. Echoes the path on stdout, or nothing
# (and a non-zero exit) when none holds it.
resolve_agent_file() {
  # `${KENSAIAPP_PIN:-}` — a `--dry-run` before any pin exists on this host makes none and sets
  # nothing, and `set -u` would abort the dry run on the bare name. `pin.py` reads an empty value
  # as "no pin in force" and answers from the instance (its own file, then its groups) and then
  # from the host's groups.
  python3 "$PIN_TOOL" agent-file --pin "${KENSAIAPP_PIN:-}" --instance-root "$INSTANCE_ROOT" --name "$1"
}

# The bounds on a <reason> value, judged in Python so a character is a character in any locale.
# Prints why a value is refused and exits 1; prints nothing and exits 0 for a value in bounds.
REASON_BOUNDS='
import sys, unicodedata
v = sys.argv[1]
line_breaks = "\n\r\v\f\x1c\x1d\x1e\x85\u2028\u2029"
if any(unicodedata.category(c) == "Cs" for c in v):
    print("is not valid UTF-8"); sys.exit(1)
if not "".join(c for c in v if unicodedata.category(c) != "Cf").strip():
    print("is blank"); sys.exit(1)
if any(c in line_breaks for c in v):
    print("must be one line"); sys.exit(1)
if any(unicodedata.category(c) == "Cc" for c in v):
    print("holds a control character"); sys.exit(1)
if any(unicodedata.category(c) == "Cf" for c in v):
    print("holds an invisible format character"); sys.exit(1)
if chr(34) in v:
    print("holds a double quote, which would close the quoted value in the prompt"); sys.exit(1)
if len(v) > 300:
    print("is %d characters — at most 300" % len(v)); sys.exit(1)
'

die() { echo "skill: $*" >&2; exit 1; }

usage="usage: <CORE>/launchers/skill/launcher.sh <skill> [<argument>...] [--provider claude|codex|gemini|hf|ollama] [--model-tier fable|opus|sonnet|haiku] [--dry-run] [--keep-awake]"

# --- args ----------------------------------------------------------------------------
skill="${1:-}"
case "$skill" in
  ""|-*) die "$usage
    <skill> is required — a skill whose directory holds a launcher.md" ;;
esac
shift

case "$skill" in
  */*|.*) die "'$skill' looks like a path — this launcher takes a SKILL NAME, and the launcher.md it reads is derived from it, never typed directly. $usage" ;;
esac

dry_run=""
keep_awake=""
provider=""
provider_given=""   # --provider was on the command line, whatever its value (an empty one is refused)
model_tier=""
values=()
while [ $# -gt 0 ]; do
  arg="$1"
  case "$arg" in
    --dry-run)    dry_run=1 ;;
    --keep-awake) keep_awake=1 ;;
    --provider)
      [ $# -ge 2 ] || die "--provider needs claude, codex, gemini, hf or ollama. $usage"
      provider="$2"
      provider_given=1
      shift ;;
    --model-tier)
      [ $# -ge 2 ] || die "--model-tier needs fable, opus, sonnet or haiku. $usage"
      model_tier="$2"
      shift ;;
    --*) die "unknown argument: $arg — the prompt is fixed; the only flags are --provider, --model-tier, --dry-run and --keep-awake. $usage" ;;
    -*[[:space:]]*) values+=("$arg") ;;
    -*) die "unknown argument: $arg — the prompt is fixed; the only flags are --provider, --model-tier, --dry-run and --keep-awake. $usage" ;;
    *)  values+=("$arg") ;;
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
if [ -n "$provider_given" ] && [ -z "$forced" ]; then
  provider=""
else
  [ -f "$PROVIDERS_TOOL" ] || die "no provider reader at $PROVIDERS_TOOL"
  [ -f "$RUN_INTELLIGENCE" ] || die "no intelligence resolver at $RUN_INTELLIGENCE"
  provider_err="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-skill-provider.XXXXXX")"
  provider="$(python3 "$PROVIDERS_TOOL" launcher skill --instance-root "$INSTANCE_ROOT" --forced "$forced" 2>"$provider_err")" && rc=0 || rc=$?
  provider_msg="$(cat "$provider_err")"
  rm -f "$provider_err"
  [ "$rc" -eq 0 ] || die "${provider_msg:-could not read the provider for the skill launcher}"
fi
case "$provider" in
  claude|codex|gemini|hf|ollama) ;;
  *) die "unknown provider '$provider' — available providers: claude, codex, gemini, hf, ollama. $usage" ;;
esac
echo "Provider:  $provider"

# A caller-named tier is judged here, right after the provider and before the skill: which tiers
# exist is a property of the call, not of the skill (MODEL TIER above). model_assignment.py owns
# the vocabulary and says what it is when it refuses. What the tier resolves to is not kept here:
# run_intelligence.py resolves it again below, as the one answer the run and its stamp share.
if [ -n "$model_tier" ]; then
  [ -f "$MODEL_ASSIGNMENT" ] || die "no model-tier resolver at $MODEL_ASSIGNMENT"
  tier_err="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-skill-tier.XXXXXX")"
  python3 "$MODEL_ASSIGNMENT" --provider "$provider" --tier "$model_tier" >/dev/null 2>"$tier_err" && rc=0 || rc=$?
  tier_msg="$(cat "$tier_err")"
  rm -f "$tier_err"
  [ "$rc" -eq 0 ] || die "--model-tier '$model_tier' refused — ${tier_msg#model-assignment: }"
fi

# --- the skill must resolve, and must declare a launch --------------------------------
resolved_err="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-skill-resolve.XXXXXX")"
resolved="$(python3 "$RESOLVER" "$skill" --root "$SKILLS_ROOT" 2>"$resolved_err")" && rc=0 || rc=$?
resolve_msg="$(cat "$resolved_err")"
rm -f "$resolved_err"
case $rc in
  0) skill_dir="$resolved" ;;
  3) die "no skill named '$skill' under $SKILLS_ROOT" ;;
  4) die "'$skill' is ambiguous — $resolve_msg" ;;
  *) die "could not resolve '$skill' — $resolve_msg" ;;
esac

launcher_md="$skill_dir/launcher.md"
[ -f "$launcher_md" ] || die "no launcher.md at $launcher_md — '$skill' declares no unattended launch"

group_dir=""
case "$skill_dir" in
  "$SKILLS_ROOT/skills/"*"/.claude/skills/$skill") group_dir="${skill_dir%"/.claude/skills/$skill"}" ;;
esac

echo "Skill:     $skill"
echo "Launcher:  $launcher_md"
[ -z "$group_dir" ] || echo "Group:     $group_dir"

# --- read the declaration -------------------------------------------------------------
defect() { die "$launcher_md: $*"; }

field() {
  grep -m1 -E "^\*\*$1:\*\*" "$launcher_md" \
    | sed -E "s/^\*\*$1:\*\*[[:space:]]*//; s/[[:space:]]*<!--.*$//; s/[[:space:]]*$//" || true
}

agent="$(field Agent)"
arguments="$(field Arguments)"
prompt="$(field Prompt)"

# Judged by the line's presence, not its value: a bare `**Model:**` is as much a stale declaration.
for label in Model Effort; do
  ! grep -q -E "^\*\*$label:\*\*" "$launcher_md" \
    || defect "**$label:** belongs in intelligence/<provider>.md beside the skill, not here — a launcher.md carries no model and no effort"
done
[ -n "$prompt" ] || defect "no **Prompt:** line — the run's fixed prompt is required"

# The run's model and effort: the one resolution (INTELLIGENCE above) — the skill's intelligence
# file for this provider, else the named tier, else neither.
resolution_args=(--provider "$provider" --skill-dir "$skill_dir")
[ -z "$model_tier" ] || resolution_args+=(--tier "$model_tier")
intelligence_err="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-skill-intelligence.XXXXXX")"
intelligence_out="$(python3 "$RUN_INTELLIGENCE" "${resolution_args[@]}" 2>"$intelligence_err")" && rc=0 || rc=$?
intelligence_msg="$(cat "$intelligence_err")"
rm -f "$intelligence_err"
# The resolver's status is what this file acts on, and this file never tests the directory. 6 is a
# tier named for a skill that HAS an intelligence/ folder, refused whatever that folder holds — a
# file for this provider, none, or a malformed one: the folder existing is the skill declaring its
# own intelligence, and a tier must not silently win over it or lose to it. 4 and 2 carry
# intelligence.py's own message. There is no 3: an absent folder is answered as `tier` or
# `default` by the resolver itself (5, an unknown tier, was refused above before the skill).
case "$rc" in
  0) ;;
  6) die "--model-tier is refused for '$skill' — its model and effort come from its intelligence file, not from a tier ($skill_dir/intelligence/)" ;;
  4) die "$intelligence_msg" ;;
  2) defect "$intelligence_msg" ;;
  *) die "could not read the intelligence for '$skill' — $intelligence_msg" ;;
esac
model="$(printf '%s\n' "$intelligence_out" | sed -n 's/^model=//p')"
effort="$(printf '%s\n' "$intelligence_out" | sed -n 's/^effort=//p')"
source="$(printf '%s\n' "$intelligence_out" | sed -n 's/^source=//p')"
case "$source" in
  intelligence) echo "Intelligence: $skill_dir/intelligence/$provider.md" ;;
  tier)         echo "Intelligence: none — tier $model_tier: $model${effort:+ at $effort}" ;;
  default)      echo "Intelligence: none — provider default" ;;
  *) die "could not read the intelligence for '$skill' — the resolver answered no source" ;;
esac
[ -n "$agent" ] || [ "$source" = intelligence ] \
  || defect "no **Agent:** and no intelligence/ folder — a run with no seat and no declared model has nothing to say what it is"
case "$agent" in
  *[[:space:]/]*|.*) defect "**Agent:** '$agent' is not an agent name" ;;
esac
agent_file=""
if [ -n "$agent" ]; then
  agent_file="$(resolve_agent_file "$agent")" \
    || defect "**Agent:** $agent has no agent file in any group (skills/<group>/.claude/agents/$agent.md)"
fi
reporter="$(field Reporter)"
reads="$(field Reads)"
case "$reads" in
  ""|product|project|instance) ;;
  *) defect "**Reads:** '$reads' is not product, project or instance" ;;
esac
[ -z "$reads" ] || [ -n "$reporter" ] \
  || defect "**Reads:** $reads names no **Reporter:** to read it"
if [ -n "$reporter" ]; then
  # Read off the registry's source, never imported: a declaration is judged without running the
  # reporters, and an unknown name would otherwise fall back to `generic` without a word.
  python3 - "$CORE_DIR/tools/reporters.py" "$reporter" <<'PY' \
    || defect "**Reporter:** '$reporter' is not a name in REGISTRY in $CORE_DIR/tools/reporters.py"
import ast, sys
try:
    tree = ast.parse(open(sys.argv[1]).read())
except OSError:
    sys.exit(1)
names = {
    k.value
    for node in ast.walk(tree)
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "REGISTRY" for t in node.targets)
    for k in node.value.keys
    if isinstance(k, ast.Constant)
}
sys.exit(0 if sys.argv[2] in names else 1)
PY
  [ "$reporter" = generic ] || [ -n "$reads" ] \
    || defect "**Reporter:** $reporter needs **Reads:** — it reads the thing the run authored"
fi

# The argument shape. `[<name>]` is a glob pattern, so the split runs with globbing off — it must
# never expand against whatever the instance root happens to hold.
names=()
optional=()
seen_optional=""
set -f
for token in $arguments; do
  case "$token" in
    "[<"*">]")
      name="${token#"[<"}"; name="${name%">]"}"
      is_optional=1; seen_optional=1 ;;
    "<"*">")
      name="${token#"<"}"; name="${name%">"}"
      [ -z "$seen_optional" ] || defect "**Arguments:** the required $token follows an optional argument"
      is_optional="" ;;
    *) defect "**Arguments:** '$token' is neither <name> nor [<name>]" ;;
  esac
  # Classes, never ranges: under a collating locale `[a-z]` matches upper case too.
  case "$name" in
    ""|-*|*[![:lower:][:digit:]-]*) defect "**Arguments:** '$token' — a name is lowercase letters, digits and '-'" ;;
  esac
  for existing in ${names[@]+"${names[@]}"}; do
    [ "$existing" != "$name" ] || defect "**Arguments:** <$name> is declared twice"
  done
  names+=("$name")
  optional+=("$is_optional")
done
set +f

# Echoes the index of a declared argument, or nothing.
declared_index() {
  local i=0
  while [ "$i" -lt "${#names[@]}" ]; do
    if [ "${names[$i]}" = "$1" ]; then echo "$i"; return 0; fi
    i=$((i + 1))
  done
  return 0
}

# The prompt's `[ … ]` segments: balanced, never nested. `outside` is the prompt with every
# segment taken out, which is where an optional placeholder must not be.
outside=""
rest="$prompt"
while case "$rest" in *"["*) true ;; *) false ;; esac; do
  outside="$outside${rest%%"["*}"
  rest="${rest#*"["}"
  case "$rest" in *"]"*) ;; *) defect "**Prompt:** a '[' is never closed" ;; esac
  segment="${rest%%"]"*}"
  case "$segment" in *"["*) defect "**Prompt:** '[' segments do not nest" ;; esac
  rest="${rest#*"]"}"
done
outside="$outside$rest"
case "$outside" in *"]"*) defect "**Prompt:** a ']' closes no '['" ;; esac

# Every placeholder names a declared argument.
rest="$prompt"
while case "$rest" in *"{"*) true ;; *) false ;; esac; do
  rest="${rest#*"{"}"
  case "$rest" in *"}"*) ;; *) defect "**Prompt:** a '{' is never closed" ;; esac
  placeholder="${rest%%"}"*}"
  rest="${rest#*"}"}"
  [ -n "$(declared_index "$placeholder")" ] \
    || defect "**Prompt:** {$placeholder} names no argument that **Arguments:** declares"
done

# Every declared argument is used, and an optional one only inside a segment.
required_count=0
declares_project=""
i=0
while [ "$i" -lt "${#names[@]}" ]; do
  n="${names[$i]}"
  case "$prompt" in *"{$n}"*) ;; *) defect "**Prompt:** never uses <$n>, which **Arguments:** declares" ;; esac
  [ "$n" != project ] || declares_project=1
  if [ -z "${optional[$i]}" ]; then
    required_count=$((required_count + 1))
  else
    case "$outside" in *"{$n}"*) defect "**Prompt:** the optional {$n} sits outside a [ … ] segment" ;; esac
  fi
  i=$((i + 1))
done
# `instance` reads the root the run starts in, which no argument names.
[ -z "$reads" ] || [ "$reads" = instance ] || [ -n "$declares_project" ] \
  || defect "**Reads:** $reads needs <project> in **Arguments:**"

# --- judge the caller's values against the declaration ------------------------------------
if [ "${#values[@]}" -gt "${#names[@]}" ]; then
  die "unexpected argument: ${values[${#names[@]}]} — '$skill' takes ${arguments:-no argument}. $usage"
fi
if [ "${#values[@]}" -lt "$required_count" ]; then
  die "'$skill' needs <${names[${#values[@]}]}> — it takes $arguments. $usage"
fi

project=""
i=0
while [ "$i" -lt "${#values[@]}" ]; do
  n="${names[$i]}"
  v="${values[$i]}"
  [ -n "$v" ] || die "<$n> is empty. $usage"
  case "$n" in
    project)
      case "$v" in
        */*|.*) die "<project> '$v' looks like a path — it is a PROJECT NAME under system/projects/" ;;
      esac
      [ -d "$INSTANCE_ROOT/system/projects/$v" ] \
        || die "no system/projects/$v/ at $INSTANCE_ROOT (is '$v' a real project?)"
      project="$v" ;;
    *path)
      case "$v" in
        "~"/*) p="${HOME}/${v#\~/}" ;;
        /*)    p="$v" ;;
        *)     p="$INSTANCE_ROOT/$v" ;;
      esac
      [ -e "$p" ] || die "<$n> '$v' does not exist" ;;
    reason)
      why="$(PYTHONIOENCODING=utf-8 python3 -c "$REASON_BOUNDS" "$v")" || die "<reason> $why. $usage" ;;
    *)
      case "$v" in
        */*|.*) die "<$n> '$v' looks like a path — it is a bare name" ;;
        -*) die "<$n> '$v' begins with '-' — only a <reason> may. $usage" ;;
      esac ;;
  esac
  echo "Argument:  <$n> $v"
  i=$((i + 1))
done

# --- the programs the run cannot do without -----------------------------------------------
#   After the caller's values: a mistyped argument is the caller's error and is reported first;
#   the toolchain is the machine's.
#   Split with `read -a`, never an unquoted expansion, so a value is never globbed.
read -r -a required <<< "$(field Requires)"
for program in "${required[@]+"${required[@]}"}"; do
  case "$program" in */*|.*|-*) defect "**Requires:** '$program' is not a bare program name" ;; esac
  command -v "$program" >/dev/null 2>&1 \
    || die "$program not found on PATH — '$skill' requires it ($launcher_md). Install it before launching."
done

# --- a project's product directory, granted best-effort -----------------------------------
add_dir=""
product_path=""
if [ -n "$project" ]; then
  project_md="$INSTANCE_ROOT/system/projects/$project/project.md"
  if [ ! -f "$project_md" ]; then
    echo "          (warning: no project card at $project_md — no product directory granted)"
  else
    raw_path="$(grep -m1 -E '^\*\*Product path:\*\*' "$project_md" \
      | sed -E 's/^\*\*Product path:\*\*[[:space:]]*//; s/[[:space:]]*<!--.*$//; s/[[:space:]]*$//' || true)"
    if [ -z "$raw_path" ]; then
      echo "          (warning: no 'Product path:' line in $project_md — no product directory granted)"
    else
      case "$raw_path" in
        "~"/*) product_path="${HOME}/${raw_path#\~/}"; add_dir=1 ;;
        /*)    product_path="$raw_path";              add_dir=1 ;;
        *)     product_path="$INSTANCE_ROOT/$raw_path" ;;   # internal: covered by cwd, no --add-dir
      esac
      if [ -n "$add_dir" ] && [ ! -d "$product_path" ]; then
        echo "          (warning: Product path: $product_path does not exist — no product directory granted)"
        add_dir=""
      fi
      echo "Product:   $product_path"
    fi
  fi
fi

# --- the completion message's reporter, and what it reads -------------------------------
#   Best-effort, as the grant above: a path that is not there warns and falls back to `generic`.
watch_reporter="${reporter:-generic}"
artifact_path=""
if [ -n "$reads" ]; then
  case "$reads" in
    product) artifact_path="$product_path" ;;
    project) [ -z "$project" ] || artifact_path="$INSTANCE_ROOT/system/projects/$project" ;;
    instance) artifact_path="$INSTANCE_ROOT" ;;
  esac
  if [ -z "$artifact_path" ] || [ ! -d "$artifact_path" ]; then
    echo "          (warning: nothing for the $reporter reporter to read${artifact_path:+ at $artifact_path} — the completion message falls back to generic)"
    watch_reporter="generic"
    artifact_path=""
  fi
fi
echo "Reporter:  $watch_reporter${artifact_path:+ reads $artifact_path}"

# --- render the fixed prompt ------------------------------------------------------------
# Echoes a declared argument's value, or nothing when the caller did not give it.
value_of() {
  local idx
  idx="$(declared_index "$1")"
  if [ "$idx" -lt "${#values[@]}" ]; then printf '%s' "${values[$idx]}"; fi
}

rendered=""
rest="$prompt"
while case "$rest" in *"["*) true ;; *) false ;; esac; do
  rendered="$rendered${rest%%"["*}"
  rest="${rest#*"["}"
  segment="${rest%%"]"*}"
  rest="${rest#*"]"}"
  keep=1
  for n in ${names[@]+"${names[@]}"}; do
    case "$segment" in
      *"{$n}"*) [ -n "$(value_of "$n")" ] || keep="" ;;
    esac
  done
  [ -z "$keep" ] || rendered="$rendered$segment"
done
rendered="$rendered$rest"

# One left-to-right pass, so a value is never itself scanned for a placeholder.
run_prompt=""
rest="$rendered"
while case "$rest" in *"{"*) true ;; *) false ;; esac; do
  run_prompt="$run_prompt${rest%%"{"*}"
  rest="${rest#*"{"}"
  placeholder="${rest%%"}"*}"
  rest="${rest#*"}"}"
  run_prompt="$run_prompt$(value_of "$placeholder")"
done
run_prompt="$run_prompt$rest"

# --- tag this run before it spawns (the shared instrument home) -------------------
#   Unconditional, not behind a flag. Called ahead of the dry-run branch too, so a dry run states
#   the arm it would run under; the exports it makes die with this script when --dry-run exits.
if [ -f "$INSTRUMENT_LIB" ]; then
  # shellcheck source=/dev/null
  source "$INSTRUMENT_LIB"
  instrument_run skill="$skill" project="$project" provider="$provider" model="$model" effort="$effort" source="$source"
else
  echo "          (no instrument library at $INSTRUMENT_LIB — run uninstrumented)"
fi

# --- build the launch command: the declared prompt, agent and provider ------------------
# What the run goes at, handed to the runner the same way on every provider branch below. A tier is
# handed over AS the tier, never as the --model/--effort it resolved to: agent_run.py refuses a raw
# `--effort xhigh` for a non-Claude provider, yet runs Codex's own `fable` tier at xhigh, so the
# resolved pair would refuse a legal tier. An intelligence file's model and effort go on raw.
intelligence_args=()
if [ "$source" = tier ]; then
  intelligence_args=(--model-tier "$model_tier")
else
  [ -z "$model" ] || intelligence_args+=(--model "$model")
  [ -z "$effort" ] || intelligence_args+=(--effort "$effort")
fi
[ -f "$AGENT_RUN" ] || die "no provider runner at $AGENT_RUN"
[ -f "$RUN_LIB" ] || die "no detached-run library at $RUN_LIB"
# shellcheck source=/dev/null
source "$RUN_LIB"

run_log="$INSTANCE_ROOT/system/logs/$provider-$skill-$(date -u +%Y%m%d-%H%M%S)-$$.jsonl"
if [ "$provider" = claude ] || [ "$provider" = hf ] || [ "$provider" = ollama ]; then
  # `hf` and `ollama` are the Claude run aimed at another endpoint, so they take this branch and
  # the runner's `--provider "$provider"` picks the adapter; the Codex and Gemini branches below
  # stay as they are.
  # The adapter builds the whole command (Task 13) — `--shape turn` is `claude --print
  # --output-format stream-json`, named up front with a session id. The group `--add-dir` is
  # absent on this path (the skill is granted with --grant-skill, so its group reaches the run
  # through the pin's plugin); the product `--add-dir` rides through --add-dir below, and
  # INSTRUMENT_RUN_SETTINGS is handed to the adapter as the caller's own --settings rather than
  # appended a second time (it folds into the pin's one merged document).
  set -- python3 "$AGENT_RUN" --provider "$provider" --shape turn --pin auto \
    --instance-root "$INSTANCE_ROOT" --prompt "$run_prompt" --grant-skill "$skill"
  [ -z "$agent" ] || set -- "$@" --agent "$agent"
  set -- "$@" ${intelligence_args[@]+"${intelligence_args[@]}"}
  [ -z "$add_dir" ] || set -- "$@" --add-dir "$product_path"
  [ -z "${INSTRUMENT_RUN_SETTINGS:-}" ] || set -- "$@" --settings "$INSTRUMENT_RUN_SETTINGS"
else
  if [ "$provider" = gemini ]; then
    set -- python3 "$AGENT_RUN" --provider gemini --prompt "$run_prompt" \
      --core-dir "$CORE_DIR" --instance-root "$INSTANCE_ROOT" \
      --add-dir "$skill_dir"
    set -- "$@" ${intelligence_args[@]+"${intelligence_args[@]}"}
    [ -z "$agent" ] || set -- "$@" --agent "$agent"
    [ -z "$group_dir" ] || set -- "$@" --add-dir "$group_dir"
    [ -z "$add_dir" ] || set -- "$@" --add-dir "$product_path"
    # The run's telemetry, handed over as the Codex branch below does. `agy` takes no settings
    # file, so the adapter turns the document's `env` into the leading `env` prefix that carries
    # the printed run ID; without it a Gemini dry run printed a run ID its command never held.
    [ -z "${INSTRUMENT_RUN_SETTINGS:-}" ] || set -- "$@" --settings "$INSTRUMENT_RUN_SETTINGS"
  else
    codex_prompt="You are running a Kensaiapp unattended skill${agent:+ as the $agent agent}. "
    codex_prompt+="For every instruction in this run, <CORE> resolves to: $CORE_DIR. "
    codex_prompt+="The instance root is: $INSTANCE_ROOT. "
    if [ -n "$agent" ]; then
      codex_prompt+="Before doing anything else, read and follow the agent instructions in: $agent_file. "
      [ "$provider" = codex ] || codex_prompt+="Then read and follow the skill instructions in: $skill_dir/SKILL.md. "
    else
      [ "$provider" = codex ] || codex_prompt+="Before doing anything else, read and follow the skill instructions in: $skill_dir/SKILL.md. "
    fi
    codex_prompt+="Execute this fixed task: $run_prompt"

    set -- python3 "$AGENT_RUN" --provider "$provider" --prompt "$codex_prompt" \
      --core-dir "$CORE_DIR"
    set -- "$@" ${intelligence_args[@]+"${intelligence_args[@]}"}
    [ "$provider" != codex ] || set -- "$@" --skill-name "$skill" --skill-path "$skill_dir/SKILL.md"
    [ -n "$group_dir" ] && set -- "$@" --add-dir "$group_dir"
    [ -n "$add_dir" ] && set -- "$@" --add-dir "$product_path"
    # The run's telemetry, as the Claude branch hands it over: the adapter turns it into the
    # `env` prefix that carries the printed run ID and Codex's own exporter config.
    [ -z "${INSTRUMENT_RUN_SETTINGS:-}" ] || set -- "$@" --settings "$INSTRUMENT_RUN_SETTINGS"
  fi
fi
set -- "$@" --background --log "$run_log"

if [ -n "$dry_run" ]; then
  echo "DRY RUN — would launch:"
  print_detached_run "$@" || die "the $provider launch was refused — nothing would launch"
  exit 0
fi

# --- the message's headline: where the run happened ---------------------------------
common_dir="$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"
if [ -n "$common_dir" ]; then
  instance="$(basename "$(dirname "$common_dir")")"
else
  instance="$(basename "$INSTANCE_ROOT")"
fi
label="$instance · ${project:+$project · }$skill"

# --- launch: one detached process, whichever the provider (the shared home) --------------
mkdir -p "$INSTANCE_ROOT/system/logs"

# --- a run no engine started names its own identity, so the board can see it ---------------
#   An engine's launch writes into the engine's state file, which `chain_board.py` reads. A single
#   run has none, so it records its identity and a run record beside the state files, one pair per
#   skill and project, each run overwriting the last. `chain_board.py` reads the record and shows the
#   run while its identity is live.
skill_run_record=""
skill_run_started="$(date -u +%Y-%m-%dT%H:%M:%S+00:00)"
if [ -z "${DETACHED_RUN_IDENTITY_FILE:-}" ]; then
  skill_run_stem="$INSTANCE_ROOT/system/logs/skill-$skill${project:+@$project}"
  DETACHED_RUN_IDENTITY_FILE="$skill_run_stem.identity.json"
  skill_run_record="$skill_run_stem.run.json"
fi

echo "Launching $skill run through $provider (background)…"
start_detached_run "$@" || die "the $provider launch did not start — nothing launched"
announce_detached_run "$run_log"

# --- background the completion watcher, through the shared home --------------------
#   A missing library is reported and skipped, never fatal — the primary run has already launched.
if [ -f "$DETACH_LIB" ]; then
  # shellcheck source=/dev/null
  source "$DETACH_LIB"
  detach_process_watcher \
    --watcher "$WATCHER" --provider "$provider" --notifier "$NOTIFIER" \
    --instance-root "$INSTANCE_ROOT" --label "$label" --log-stem "$skill" \
    --reporter "$watch_reporter" --pid "$DETACHED_RUN_PID" --run-log "$run_log" \
    ${artifact_path:+--artifact-path "$artifact_path"} \
    ${keep_awake:+--keep-awake}
else
  echo "          (no completion-watch library at $DETACH_LIB — completion watch skipped)"
fi

# --- record who this launch is, for the engine that named a file for it ---------------------
#   After the watcher block, so its pid is known. A no-op when the engine named no file, and it
#   never fails the launch (`core/tools/detached_run.sh`).
record_detached_run_identity

# --- the run record the board reads, for a run no engine started --------------------------------
#   Written beside its target and moved into place, so the board never reads half a file. A record
#   that cannot be written costs a note, never the launch.
if [ -n "$skill_run_record" ]; then
  python3 -c 'import json, sys; print(json.dumps(dict(zip(("skill", "project", "started_at", "identity"), sys.argv[1:]))))' \
    "$skill" "$project" "$skill_run_started" "$DETACHED_RUN_IDENTITY_FILE" >"$skill_run_record.tmp" \
    && mv -f "$skill_run_record.tmp" "$skill_run_record" \
    || echo "(could not write the run record at $skill_run_record — the board will not show this run)" >&2
fi
