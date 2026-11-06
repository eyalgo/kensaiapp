# Eval inputs — changelog-line

Every case builds its own synthetic fixture with `build_fixture.sh <empty-dir> <scenario>`: a fabricated
instance repository, a fabricated product ("widget") under a fabricated project ("demo"), a change folder,
and a change worktree on the change's branch holding real commits. Nothing here is a real product, and no
case reads the owner's home, a live service or a primary checkout.

The script prints the instance root, the project and the change key, one per line. A case names its
scenario in its prompt; the run builds the fixture first, then invokes the skill as `content-editor` with
the printed project and key. The `core` the skill resolves is the running session's own.

Scenarios: `entry`, `upgrading`, `tests-only`, `tests-only-removal`, `no-changelog`, `unreleased-none`,
`unreleased-two`, `removals`, `last-removal`, `already-empty`, `no-what-left`, `malformed-none`,
`malformed-both`, `external`, `hook-refuses`, `external-report-refused`, `wrong-branch`, `no-worktree`,
`dirty-target`.

The script is the fixture. A comment about what a scenario is meant to prove stays in this file and in the
script's header, never in a fixture file the skill reads, because a run's grader reads those files too.
