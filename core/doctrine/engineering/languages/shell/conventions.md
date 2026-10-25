---
version: "1.1.10"
---

# Shell — conventions

How bash is named and shaped here. Nothing in this file is enforced by a tool —
`quality_gates.md` § What is not installed says why, and that is what makes these conventions rather
than gates. What the code does at a failure or an event is `errors_logging.md`.

Every measurement below was taken on 2026-08-23 over the twenty tracked bash files: the eighteen
`git ls-files '*.sh'` returns, plus `core/githooks/commit-msg` and `core/githooks/pre-commit`.

## The opening three lines

**`#!/usr/bin/env bash`, then a header comment block, then `set -euo pipefail`.** All twenty files
open this way, and nothing else sits between the shebang and the options line.

- **`set -euo pipefail`, in 19 of 20.** The single exception is
  `core/tools/detach_watcher.sh`, which carries no top-level `set` line at all — and it is also the
  only file in the corpus that is sourced rather than run, describing itself as "**sourced**, never run
  directly — a launcher `source`s it and calls `detach_completion_watcher`". The rule the corpus
  supports is that correspondence: **a script sets the options, a sourced library sets none**, because
  a sourced `set -e` would change the shell options of whatever sourced it. The mechanism is this
  authoring run's reading, 2026-08-23; the one-to-one match between "is sourced" and "carries no
  `set`" is measured.
- **`pipefail` is load-bearing and interacts with the guard style.** Under it, a `grep` that matches
  nothing inside a command substitution ends the script before the next line can report anything
  useful — which is why the corpus writes `|| true` on that substitution and puts the real check on
  the following line. `errors_logging.md` § A guard reports; it does not merely fail owns that pattern.

## Surface style

- **Two-space indent, and no tabs.** Of 895 indented lines of code, 889 sit at a multiple of two —
  452 at two columns, 334 at four, and the rest deeper. `git grep -P '^\t'` returns nothing. The six
  exceptions are alignment columns inside a `USAGE` heredoc in three sibling launchers
  (`core/launchers/experience-visual/launcher.sh`, `experience-voice/` and
  `kensaiapp-writing-bar/`, all three retired 2026-09-30),
  where the odd indent lines up a table of argument forms.
- **Comments wrap at 100 columns; code does not wrap at all.** 2,922 of the 3,030 comment lines are
  within 100 columns and exactly one exceeds 120. Code is the opposite: 168 lines exceed 100, and
  **every one of them is a string literal or a heredoc body** — a `die` message, a fixed `claude --bg`
  prompt, or the prompt text in `core/launchers/cold-read/launcher.sh`. Nothing wraps a command to
  meet a column.
- **A long command is broken with a trailing `\`, not with a temporary variable.** 165 continuations
  across 17 files. `core/tools/detach_watcher.sh` calls the watcher this way, and the launchers call
  `detach_completion_watcher` this way.
- **Every expansion is quoted.** Measured across the corpus: 196 single-bracket tests of the form
  `[ -n "$x" ]` / `[ -f "$x" ]` and **zero** with an unquoted operand; `"$@"` 44 times and **zero**
  bare `$@`. The only expansions sitting outside quotes are inside heredoc bodies and multi-line
  string literals, where quoting would be wrong.

## Constructs

- **`[ … ]`, not `[[ … ]]`.** 261 single-bracket test openings against **one** `[[`, at
  `core/launchers/cold-read/launcher.sh`, and it is there for the one thing `[` cannot do — a regex
  match, `if [[ "$station_base" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}_(.+)$ ]]`. **`=` for string equality,
  never `==`** — `git grep -E '\[ [^]]*=='` returns nothing.
- **`$( … )`, never backticks.** 196 command substitutions, all in the `$( )` form. Backticks appear
  only inside comments and message strings, where they are markdown quoting rather than substitution.
- **`name() { … }`, never the `function` keyword.** 28 function definitions in the corpus and zero
  uses of `function`. All 28 are `snake_case`, and two carry a leading underscore to mark them
  file-internal — `_resolved_line` in `core/tools/launch-audit.sh` and `_commit_and_retry_block` in
  `core/launchers/cold-read/launcher.sh`. Seventeen of the 28 are `die` (§ Naming below);
  `local` for a variable that is the function's own is used 23 times, concentrated in
  `core/tools/detach_watcher.sh` and `core/launchers/cold-read/launcher.sh`, the two files with real
  functions rather than a lone `die`.
- **`case` for dispatch on a value, `if` for a condition.** 50 `case` statements. The argument loop is
  the canonical one: `for arg in "${@:2}"` around a
  `case "$arg" in --dry-run) … ;; --keep-awake) … ;; esac`, in 12 of the `.sh` files counted
  before `core/launchers/ad-hoc-flow/launcher.sh` was retired on 2026-09-18 — that one used
  `for arg in "$@"` after its own `shift`. A file
  taking more than one flag with a value uses `while [ $# -gt 0 ]` and an explicit `shift` instead —
  three do, `core/launchers/cold-read/launcher.sh` among them.
- **`set -- <argv>` to build a command, then `"$@"` to run it.** 16 launchers build the `claude --bg`
  invocation this way — `set -- claude --bg "$prompt" --agent <name> --permission-mode auto`, then
  `[ -n "$add_dir" ] && set -- "$@" --add-dir "$product_path"`. It is what lets `--dry-run` print
  exactly what would run, with `printf '  %q' "$@"`.
- **An array where the argv is conditional.** `core/tools/detach_watcher.sh` builds `watcher_args` and
  appends with `watcher_args+=( --agent-id "$agent_id" )` only when the value is non-empty; the file
  says why an unconditional append would be wrong — it "would hand the watcher `--agent-id ""`, which
  reads as a falsy id there".
- **No `eval`, anywhere.** Zero uses in the corpus.

## Naming

- **UPPERCASE for a resolved configuration value, lowercase for a working variable.** 106 uppercase
  assignments against 251 lowercase, and the uppercase set is a small closed list set once near the
  top of a file: `SCRIPT_DIR`, `INSTANCE_ROOT`, `WATCHER`, `NOTIFIER` and `DETACH_LIB` each assigned
  in 17 files, then `CORE_DIR` — assigned in all 27 launchers, the one name every launcher resolves
  `<CORE>` through — then `REFERENCE_ROOT`, `LOCK_TOOL` and a handful more. Everything derived after
  the argument parse — `project`, `dry_run`, `keep_awake`, `product_path`, `raw_path` — is lowercase.
- **An environment override is `${LAUNCH_<X>_<THING>:-<default>}`**, and the default is written out in
  the same expansion rather than assigned elsewhere:
  `WATCHER="${LAUNCH_CONTENT_WATCHER:-$CORE_DIR/tools/watch_agent.py}"`. The `<X>` is the
  launcher's own short name, so two launchers never share an override. `KENSAIAPP_NOTIFIER` is the one
  cross-launcher name, nested inside the per-launcher one:
  `NOTIFIER="${LAUNCH_CONTENT_NOTIFIER:-${KENSAIAPP_NOTIFIER:-}}"`. All 18 `.sh` files name it.
- **A path a caller may need to stub gets an override; a path nobody would stub gets none.**
  `core/launchers/launch-eval-fix/launcher.sh` states the rule where it applies it: the shared library
  path has "No env override: unlike $WATCHER, no test or caller ever wants a stub in its place, only
  the real file at its real relative depth."

## The header comment block

Every file opens with one, and it is the largest single body of prose in the corpus — 3,030 of the
5,288 lines are comment.

1. **`# Version: x.y.z — <what changed>`, newest first**, immediately under the file's one-line
   description. All twenty carry it; the form is `versioning.md`'s and `toolchain.md` § Versioning
   points at it. Older entries stay below the new one, so the header is the file's own changelog.
2. **ALL-CAPS section headings inside the block.** `# WHY THIS EXISTS` in 15 of 18 `.sh` files and
   `# USAGE` in 17. Others in use: `# COMPLETION NOTIFICATION`, `# THE CONTRACT`, `# PERMISSIONS /
   CONTEXT`, `# WATCHER LOG`, `# THE REPORTER`. The heading names what is under it; a block with more
   than one topic gets more than one heading.
3. **`# WHY THIS EXISTS` carries the reasoning the floor asks for.**
   `<CORE>/doctrine/engineering/languages/developer_standards.md` § Clean code makes a comment recording *why* the
   code is shaped this way the one sanctioned exception, and hands this file the question of which
   form carries it: "Which doc-comment form carries that exception in a given language is that
   language's `conventions.md` to state." **In bash it is this heading**, and the floor names the
   model in the same sentence — "`product-card/launcher.sh`". That block,
   `core/launchers/product-card/launcher.sh` § WHY THIS EXISTS, records why the script blocks on
   its first half where every sibling backgrounds: the second half reads the card the first half
   writes, so "a backgrounded first half means the second half runs against the card as it stood
   BEFORE."

## Body comments

- **`# --- <what this stretch does> ---` banners the sections of the body.** 126 of them across 17
  files, padded with dashes to a uniform width. `# --- args ---` and
  `# --- resolve the instance root (the caller's cwd) and cd there ---` are two.
- **A `#` block immediately above one construct, naming what was rejected or what would break.** This
  is the second half of the floor's one exception. `core/launchers/companion-self-answer/launcher.sh` above
  the launch line is the shape: the launch output is "Redirected to a FILE, never captured through a
  pipe", because a pipe capture "would block this launcher for the whole run it just backgrounded".
- **A comment that says what the line does, rather than why, is the smell** — that rule is the floor's
  and is not restated here.
