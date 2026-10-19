---
version: "1.1.3"
---

# Shell — quality gates

The checks a tool can fail the build on, and the exact command for each. A rule only a reader can
apply is not here — it is in `conventions.md`, per `languages/README.md` § The seven concerns.

## The two gates

| Gate | Command | Passes when |
|---|---|---|
| Parse | `bash -n <path>` | exit status 0 |
| Suite | the run command in `testing.md` | exit status 0 |

Both ship with the machine and need no installed package — which is why these two are the gates and a
linter and a formatter are not (§ What is not installed).

**Parse.** `bash -n` reads the script and executes nothing. Measured 2026-08-23 against all twenty
tracked bash files, it reported nothing and exited 0 for every one. Two things about it are worth
knowing before a gate is built on it, both measured the same day in a scratch directory:

- **A failure exits `2`, not `1`.** A file whose `if` is never closed produced
  `syntax error: unexpected end of file` and exit status **2**. A gate keyed on `1` passes a file that
  does not parse; key it on `!= 0`.
- **It is a parser, so a great deal that looks like syntax is not.** A test command missing its closing
  bracket — `if [ -n "$x" ; then` — parsed clean and exited 0, because `[` is an ordinary command and
  its missing `]` is a runtime complaint from that command. Running the same file printed
  ``[: missing `]' `` and still exited 0. An unbound variable under `set -u` behaved the same way:
  `bash -n` exited 0, and running the file printed `unbound variable` and exited 1.

So Parse passing is not evidence a script runs, and it catches nothing about a wrong path, a missing
program or a variable that is never set. The suite carries that weight.

**This gate has two in-repo consumers already.** The `development-code-integrity` reviewer of
`9fad21f4` ran it — `core/launchers/ad-hoc-flow/code-integrity-report.md` (at `a01eb180`; the
launcher retired 2026-09-18) records
"`bash -n core/launchers/ad-hoc-flow/launcher.sh` → exit 0" and says plainly it reached for the command
"because the two packets made the shape of the question obvious, not because anything named it". And
`core/tools/test_language_packets.py` runs each of the family's own audit commands through
`subprocess.run(["bash", "-n"], …)` to prove each is recoverable as one command. This file is what
names it.

**Suite.** The layer model, the tool and the run command are `testing.md`'s; the bar is here, and it is
total: **a red test is a failed gate, and a suite that does not run is a failed gate.** The second half
is not rhetorical — the suite is pytest, which exits `5` for "No tests were collected", so a gate that
treats only `1` as a failure passes a run that tested nothing. `python/quality_gates.md` carries that
same exit-code note against the vendor's own table, and it applies here unchanged because it is the same
runner.

## What is not installed

**No linter and no formatter runs over shell here, and none is configured anywhere.** `command -v
shellcheck` exited 1 on 2026-08-23 and `command -v shfmt` did the same. No `.shellcheckrc`, `.editorconfig`
or `shfmt` configuration is tracked — `git ls-files` matching those names returned nothing — and a
repo-wide search for `shellcheck`, `shfmt`, `bashate` and `bats` outside the shell files themselves
returns only prose about the absence, one archived plan, and the test named below.

That follows from the dependency position in `toolchain.md`, not from an oversight: this house installs
nothing for shell.

**So every rule in `conventions.md` is reader-applied.** None of them is a gate, and a change that
breaks one fails no command. That is the cut `languages/README.md` draws, at its sharpest: with two
gates this narrow, almost all of this packet's practice is convention.

## The one open decision — ShellCheck

**Whether ShellCheck becomes a gate here is the owner's to answer, and it is open** — a tool nobody
has installed is a decision, not a lookup. This file states what the house does today and settles
nothing.

**What makes it a live question rather than a hypothetical one: the corpus is already annotated for a
tool nobody runs.** Every file that `source`s another shell file carries a `# shellcheck source=`
directive above the `source` line — seventeen of the twenty, and the three without it are the three
that source nothing (`core/tools/detach_watcher.sh`, which is the library being sourced, and the two
git hooks). In all 22 sourcing `core/launchers/*/launcher.sh` the directive is
`# shellcheck source=/dev/null`: since a launcher's `<CORE>` is resolved at runtime (`CORE_DIR`, a
prefix strip from the launcher's own location, not a fixed relative path), no static relative path can
name where the sourced file actually sits, and `/dev/null` is shellcheck's own documented answer for
exactly that case. The three flat `core/tools/launch-*.sh` still name a relative path, and correctly
so — they sit beside the file they source. One suite pinned the
annotation as a contract: `core/launchers/ad-hoc-flow/test_ad_hoc_flow.py` (at `a01eb180`, retired
2026-09-18) asserted
`src.count("# shellcheck source=/dev/null") == 2`, and its own docstring gave the reason the count
matters — a directive that stopped matching the line below it would be exactly as broken as a wrong
walk, which counting (rather than merely checking presence) still catches.

Two candidate resolutions, neither taken here:

- **Adopt it**, install it, and this file gains a third gate with its exact invocation — at which point
  the seventeen directives start being read, and whatever ShellCheck says about the corpus becomes a
  finding list somebody owns.
- **Decline it**, and the seventeen directives are documentation for a reader rather than input to a
  tool — which is what they are today, and worth saying so where a reader meets them.

Writing a gate for an uninstalled tool would be the worse third option: it would state a check that
fails the moment anyone runs it.
