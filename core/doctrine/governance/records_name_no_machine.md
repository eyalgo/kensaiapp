---
version: "1.1.0"
---

# A record names no machine — no home folder, no login name, no repository address

Governs every line written into a record, and what that line may say about the machine it was written
on, and about the repository it is committed to. A record ships with that repository, so a home
folder or a login name written into one publishes the person whose machine wrote it, and the
repository's own address publishes where the work lives and, with a command's answer, what that
repository is and allows.

> **Owns:** what a record is, for this rule; that no line written into one names the home folder or
> the login name of the machine that wrote it, or the address of the repository it is committed to;
> what is written instead; and where the check that holds
> the rule runs. **Does not own:** what a test may read of the machine it runs on
> (`engineering/testing_doctrine.md` § *A test reads nothing of the machine it runs on*), how a record
> cites its sources (`single_source.md`), or where a record is filed (`setup/kensaiapp_structure.md`).

---

## What a record is

A record is a file whose repo-relative path begins `system/projects/`, or has a `docs/` folder
anywhere in it. That covers the journey, the trails, halt reports, designs, plans, specs, the
definition chain's answer files and a product's `docs/`. It holds in whichever repository the file is
committed to: any instance, a satellite included, or a product's own repository.

## What a line in a record never names

**No line written into a record names the home folder of the machine that wrote it, or that
machine's login name.** The home folder counts wherever it appears: on its own, at the head of a path,
or inside a link. The login name counts where it stands as a word, so a longer word that contains it
does not.

The rule names nobody. Its subject is whichever machine is writing, so the same line can be clean on
one machine and break the rule on another. A made-up home such as `/Users/sam/…`, written as an
example, names no machine.

**No line names the address of the repository the record is committed to** — its `<owner>/<name>`
on the hosting service, which its `origin` remote carries. It counts wherever it appears: in a
command, a URL or a sentence, in any letter case, and with a suffix such as `.git` or `.wiki` after
it, since those still name the repository. A longer name that only begins with it, such as
`<owner>/<name>-fork`, is another repository and does not count. The bare
name on its own is not the address and is not forbidden: a record names its own instance in prose all
the time, and it is the address that a command against the hosting service's API writes, and that
command's answer that says what the repository is and allows. The owner's call, 2026-11-02, on a
release scan that found tracker17's records quoting such commands.

## What is written instead

| Where it would appear | Write |
|---|---|
| A path under the home folder | `<home>/…` |
| A path inside the instance | `<the instance>/…`, or the path relative to the instance's root |
| The login name | `<user>` |
| The repository's own `<owner>/<name>` | `<owner>/<repository>` |

A product checked out outside the instance is written the same way where its checkout sits under the
home folder: `<home>/…`, the rest of the path unchanged.

## Where a home folder, a login name or the address slips in

- **Pasted terminal output.** A tool's output, an error, a traceback or a listing of worktrees prints
  full paths, and a report that keeps the output keeps the paths.
- **Evidence commands.** A command quoted in an evidence line or a table of verified claims carries the
  folder it ran in, or the cache it read.
- **A page a check opened.** A browser or file check names the file it loaded by its full path.
- **A location written out.** An instruction or a report names a checkout or a worktree by its full
  path.
- **A call to the hosting service.** A check that asks the service about the repository writes the
  command it ran (`gh api repos/<owner>/<repository>/…`) and keeps its answer. The command keeps its
  shape with the address replaced, and the answer keeps what it showed, without restating the
  address.

Each is copied with the home folder, the login name and the address replaced by the forms above, and
with nothing else in it changed.

## A line already written

The rule binds the line being written. A line already committed is not refused when a commit carries
it forward unchanged, as a move into `trail/`, a rename or an edit elsewhere in the file does. Removing
one is a privacy scrub, and a scrub may edit a record anywhere, `trail/` included. **Privacy outranks
the rule that a trail is frozen** (the owner's call, 2026-10-29). The frozen rule is
`setup/kensaiapp_structure.md` § *A trail is not the document's sibling*.

## Where the rule is held

`core/tools/check_record_privacy.py` holds the rule at commit. `core/githooks/pre-commit` runs it on
every ordinary commit, in whichever repository git is committing in, beside the hook's two other
checkers. It reads only the lines the commit adds to records, with renames detected, so a record
carried forward unchanged adds none. It refuses the commit when an added line names the home folder or
the login name of the machine committing, or the address of the repository being committed to. It
reads the first two off that machine as it runs, and the address off that repository's `origin`
remote. Only a remote on a hosting service gives an address: a repository with no `origin`, or whose
`origin` is a local folder, has none to look for, and another remote, such as the `upstream` a fork
carries, is a different repository's address. A home folder
that is empty or `/`, and an empty login name, are not looked for, because neither names anyone.

**No line is excused.** The test-isolation checker accepts a marker on a line it would otherwise
refuse. This check accepts none, because a record has no reason to carry the real home folder, login name or
repository address.

**Why a check and not only a note.** Writing runs were told to keep the paths they write relative, and
lines naming the machine landed in records anyway. The owner's call, 2026-10-29, is that the rule is
held at commit.
