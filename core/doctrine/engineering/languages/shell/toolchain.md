---
version: "1.2.2"
---

# Shell — toolchain

The runtime a shell file here targets, and what it may depend on. Where a file of a given kind goes is
`kensaiapp_structure.md`'s (`README.md` § The seven concerns names the sections); which checks run over it
is `quality_gates.md`'s.

Every measurement below was taken on 2026-08-23 over the twenty tracked bash files — the eighteen
`git ls-files '*.sh'` returns, plus `core/githooks/commit-msg` and `core/githooks/pre-commit`.

## There is no build system and no package manager

A shell file here is run as it sits. Nothing compiles it, nothing bundles it, nothing installs it, and
there is no manifest or lockfile to declare it in. `git ls-files '*.bash' '*.zsh' '*.ksh' '*.bats'`
returned 0, and no shell package tool of any kind is configured anywhere in the tree.

**The file is committed executable.** `git ls-files -s` reports mode `100755` for all twenty, with no
`100644` among them. A shell file landing non-executable is a defect, because every caller invokes it by
path rather than through an interpreter argument.

## The runtime is bash 3.2, and that is a ceiling rather than a floor

**`#!/usr/bin/env bash`, in all twenty files.** Never `/bin/bash`, never `#!/bin/sh`. `env` resolves
bash through `PATH`, so a machine carrying a newer bash ahead of the system one runs that instead —
which is exactly why the ceiling matters and the shebang does not relax it.

**The ceiling is macOS's system bash: 3.2.** `bash --version` on this machine prints
`GNU bash, version 3.2.57(1)-release (arm64-apple-darwin25)`, and `/bin/bash --version` prints the same.
`core/tools/launch-audit.sh` states the constraint in its own body — "bash 3.2 (macOS's system bash) has
no `mapfile` — pull each line out by number instead" — and works around it rather than requiring a
newer bash.

The corpus holds to that ceiling without exception. Measured across all twenty files: zero uses of
`declare -A` or `local -A`, zero uses of `${var,,}` or `${var^^}`, zero `mapfile` or `readarray` calls,
and zero `&>>` or `|&` redirections. Indexed arrays, which bash 3.2 has, are used freely —
`core/launchers/cold-read/launcher.sh` builds nine of them, and `core/tools/detach_watcher.sh` builds
its watcher argv as one.

**So a bash-4 construct is not available**, whatever the machine running the file happens to have
installed. A file that needs one has reached the boundary below.

## When bash is not enough, the work crosses to `python3`

The house's answer to a job bash 3.2 cannot do well is not a newer bash and not a GNU coreutils
dependency — it is `python3`, which eighteen of the twenty files already reach for: every launcher
detaches a Python completion watcher, and each git hook `exec`s a Python checker.

`core/tools/launch-fix-author.sh` states the criterion where it applies it: sorting version folders
"by component (python3, not `sort -V`, which is GNU and unreliable on macOS) so v3.17.0 beats v3.4.0 —
a lexical sort gets that pair backwards". The same file reaches for `python3 -c` there rather than
adding a tool.

**Values cross the boundary as `argv`, never interpolated into the Python source, and a heredoc is
quoted.** `core/tools/launch-audit.sh` states both halves at the call site — "Values cross the boundary
as argv (never interpolated into the Python source), so nothing here can inject through a
caller-supplied version string. A quoted heredoc (`<<'PY'`) keeps the script text itself free of shell
expansion" — and the two forms in the corpus are that quoted heredoc and `python3 -c "…" "$arg"`.

## What may be depended on, and how a new dependency is admitted

**Nothing is installed for shell.** There is no dependency to add, pin or lock, so the question a
toolchain file usually answers becomes a narrower one: which programs a file may assume are present.

Three tiers, all visible in the corpus:

1. **Assumed present, unguarded** — the BSD userland macOS ships and `python3`. Counted over the
   eighteen `.sh` files: `grep` on 34 lines, `sed` on 31, `python3` on 29, `dirname` on 20, `cat` on 20,
   `mktemp` on 17, `basename` on 8, `tr` on 6, `nohup` on 5, `git` on 4, `ps` on 3. None is guarded and
   none needs to be.
2. **Required for the run, guarded before anything launches** — a program without which the run would
   fail later, checked with `command -v` and refused loudly. `core/launchers/skill/launcher.sh` does it
   for a skill whose `launcher.md` declares `**Requires:**`. Two do, both `**Requires:** npx node`,
   because each skill's lint step shells out to `npx @google/design.md`:
   `skills/cdo/.claude/skills/experience-visual/launcher.md` and
   `skills/cdo/.claude/skills/product-design/launcher.md`. Each skill's own launcher carried the same
   `command -v` pair until it was retired — `product-design`'s on 2026-09-17, `experience-visual`'s on
   2026-09-30.
3. **Optional, guarded and skipped** — a program whose absence degrades the run rather than ending it.
   `caffeinate` is the case: `core/tools/detach_watcher.sh` wraps it in
   `if command -v caffeinate >/dev/null 2>&1; then` and, when it is missing, prints
   `(keep-awake: caffeinate not found — not macOS? — skipped)` and carries on.

**A new external program is admitted by choosing tier 2 or tier 3 explicitly and writing the guard.**
The guard is `command -v <name> >/dev/null 2>&1`, and nothing deeper — `product-design`'s own header
says "The check is `command -v npx` + `command -v node`, nothing deeper". Which tier it is follows from
one question: can the run produce its result without the program? If not, tier 2 and `die`. If it can,
tier 3 and a skipped-with-a-reason line.

**A GNU-only flag is not a dependency; it is a defect.** BSD userland is what these files get, so
`sed -i` (which takes a mandatory argument on BSD and not on GNU) appears nowhere in the corpus, and
`sort -V` is rejected by name at `core/tools/launch-fix-author.sh`. `languages/README.md` § Audit
records the same trap one level up for `find -printf`.

## Versioning

A shell file here carries `# Version: x.y.z` as a header comment. `versioning.md` § Where the test
lands fixes that form for launchers and for shell scripts and hooks, and all twenty files carry one.
The header is a stack, newest first, each entry saying what that version changed. What the three digits
mean, and which commit moves them, is `versioning.md`'s and is not restated here.
