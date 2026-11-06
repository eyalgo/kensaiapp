# Changelog

What each release of KensaiApp changed, newest first, in the format of
[Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/). Releases are numbered 0.x until v1;
a 0.x release makes no promise of stability, as the README's note on what KensaiApp does not promise
says.

An entry that starts with **Front door** is about the README and its guides, and one that starts
with **tracker17** is about the example app. Every other entry is about KensaiApp itself. Where a
clone of the release before must act, the release says so first, under *Upgrading from*.

## [Unreleased]

## [0.5.1] - 2026-11-06

### Fixed

- **Front door.** The README's version badge names this release. In 0.5.0 it still read 0.4.0.

## [0.5.0] - 2026-11-06

### Upgrading from 0.4.0

- Install uv. KensaiApp's hooks, launchers, skills' commands and test suites now run their Python
  through uv, on the Python that `.python-version` at the instance root names, through
  `core/tools/locked_python.sh`. They stop without uv rather than fall back to `python3`: a hook
  prints the runner's install message and does nothing, and a launcher names itself and exits 1.
  Install uv with `brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`.
- The four chain launchers are renamed, and their old folders are gone. Type
  `core/launchers/change/launcher.sh` in place of `core/launchers/chain-development/launcher.sh`,
  `core/launchers/walk/launcher.sh` in place of `core/launchers/chain-change/launcher.sh`,
  `core/launchers/product-docs/launcher.sh` in place of `core/launchers/chain-product/launcher.sh`,
  and `core/launchers/prd-and-finish-line/launcher.sh` in place of
  `core/launchers/chain-agari/launcher.sh`.
- Before you take the `change` and `walk` renames, let every walk end and remove the
  `chain-development-<project>-*` and `chain-change-<project>-*` files under `system/logs/`. The
  `change` launcher now keeps its records as `chain-change-<project>-*`, the name the `walk`
  launcher used before, and the `walk` launcher keeps its own as `chain-walk-<project>-*`.
- KensaiApp runs on ka-telemetry 0.3.0, installed from PyPI. Upgrade the copy in KensaiApp's own
  environment with `~/.kensaiapp/venv/bin/pip install ka-telemetry==0.3.0`, then restart a receiver
  that is running so it picks up the new code.
- Run `shukuba-refine`, or `nemawashi-refine`, again for a route report written before this release.
  The `build-idea` queue refuses a row whose command names an old launcher path, `nemawashi-pick` or
  `readme-status`, before anything launches.
- A project's "done", the Agari, is now its finish line, and the old names are not read anywhere.
  Let every PRD or Agari walk end before you take it. Then rename each project's `agari.md` to
  `finish_line.md`, `agari_open_issues.md` to `finish_line_open_issues.md` and `trail/agari/` to
  `trail/finish_line/`. Change each project card's `**Definition:**` value `prd-agari` to
  `prd-and-finish-line`: the walk and build-idea refuse the old one. Write `Finish-line: <project> —
  progress: …` where you wrote `Agari: <project> — progress: …`: the builder does not refuse an old
  line, it passes it unchecked, so change any script or prompt that still writes one. Type
  `finish_line` where you passed `Agari` to the companion-self-answer launcher, and name the
  reporter `finish-line` where a skill's `launcher.md` or a `watch_agent.py --reporter` named
  `agari`.
- In a clone's own `.providers.toml`, as `.providers.toml.example` now has it: rename `Agari` under
  `[documents]` to `FINISH_LINE`, rename the `change` entry under `[steps]` to `open`, and add
  `changelog = "claude"` under `[steps]`. The step that opens a change is named `open` now, and the
  change chain runs a new step, `changelog`, after implementation and before code integrity. A walk
  is refused when `.providers.toml` lacks the entry one of its steps needs. A `readme-status` row
  may stay: it no longer stops anything.
- Where you type `chain_development.py --steps`, type `--steps change` in place of `--steps
  development` for the change launcher's steps, and `--steps walk` in place of `--steps change` for
  the walk launcher's steps. `change` is the default.
- `commit_builder.py merge` refuses a merge into `main` whose branch adds no entry under `##
  [Unreleased]` in a `CHANGELOG.md`, and `merge --check-only` gives the same answer. Add the
  change's entry under `## [Unreleased]` on the branch, or pass `--user-invisible "<reason>"` when
  the merge changes nothing a user sees; the reason is recorded in the merge commit as
  `User-invisible: <reason>`. The seal's delivery takes the same declaration as a `user_invisible`
  field in a role's merge record.
- Type `project-finish-line` where you typed `project-agari`: the CPO skill that declares a
  project's finish line is renamed, and the old name is not kept. That covers its launcher call
  (`launcher.sh project-finish-line <project>`) and setup seeds that name it.
- Type `seed-pick` where you typed `nemawashi-pick`: the skill that picks a project's next seed is
  renamed, and the old name is not kept. That covers its launcher call (`launcher.sh seed-pick
  <project>`) and its `--skill` and `--prompt seed-pick/thin` names.
- **tracker17.** The tests' dependencies are locked in `products/tracker17/uv.lock`, and
  `tests/requirements.txt` no longer exists. To run the tests, install uv, then type `uv sync
  --locked` and `uv run playwright install chromium` inside `products/tracker17`. Type each test
  command through `uv run`, such as `uv run pytest tests/`. The tracker itself still starts with
  `python3 main.py` and doesn't need uv.

### Added

- The session-start hook wires the git commit hooks into each product repository outside the
  instance that a project card names. A commit made by hand in that repository meets the same checks
  as one made in the instance.
- `core/doctrine/governance/records_name_no_machine.md` states that a record names no machine. No
  line in a record names the home folder, a path under it or the login name of the machine a run is
  on, and the file gives the placeholders to write instead. `core/doctrine/task_map.md` routes a run
  to it.
- `core/doctrine/engineering/testing_doctrine.md` § *A test reads nothing of the machine it runs on*
  states that a test reads only what is committed beside it or what it makes itself. It names the
  commit check and the empty home folder that hold the rule, and says that whoever sees a test break
  the rule fixes it.
- `core/doctrine/setup/kensaiapp_structure.md` § *The changelog — one file per product path records
  what changed for a user of a fresh clone* states where a product path's changelog sits, what earns
  an entry and which project an entry names. It says which root files are logged in
  `core/tools/CHANGELOG.md`, what goes under `### Upgrading`, and what a release cut does to the
  entries.
- `core/doctrine/engineering/testing_doctrine.md` § *A unit test hands its unit fakes and touches
  nothing real* states that a unit test hands the unit a fake for every collaborator, through the
  seam production wires the real one through, and touches no real process, network, clock or file
  outside a temporary folder the test makes. `core/doctrine/governance/found_while_walking.md`
  states that a change which edits a module that builds its own collaborators, or whose unit tests
  touch a real resource, brings that module up to the standard in the same change.
  `core/doctrine/engineering/languages/README.md` states that the port and fake modules such a fix
  needs are not a topology decision, so the stage that meets the conflict makes the fix instead of
  handing it on. The JavaScript, TypeScript and Shell guides state how their language hands a
  collaborator in and fakes it in a unit test.
- `core/doctrine/engineering/arch_defaults.md` § *The four layers* states four layers a product's
  SDD may draw on, what each holds and may import, and that `domain` and `ports` reach no process,
  network, filesystem, environment variable or clock. Each language guide's `conventions.md` under
  `core/doctrine/engineering/languages/` states that language's form of the layers and points there.
- `core/doctrine/engineering/testing_doctrine.md` § *A fake is verified against its port's contract*
  states that a port has one fake and one contract suite, run against the real adapter and against
  the fake, and that a fake failing it fails the suite. Each language's testing file states its form
  of a contract suite, or that it has none for want of a layer 2, and says that no language has a
  unit-tier sandbox yet. Both runs of a contract suite are layer 2, and a port's fake lives in a
  test-support module owned with the port.
- When a `specs`, `design` or `plan` run of the change chain stops with a `halt_report.md` whose
  halt reason is `records-owed`, the chain answers it on a project whose card reads `**Definition:**
  full`. It launches `product-docs` once to fold the items the report's `Raised item:` lines name.
  Once the sweep ends `sealed` with every item folded, it removes the change's old worktree and
  branch and starts the change again at `specs`. Where an item stays open, or the sweep ends any
  other way, the walk halts and its reason says why. On any other card, a `records-owed` report
  halts the walk as any halt report did before.
- A test in KensaiApp's own suites, under `core/tools/` and `core/launchers/`, now fails when it
  tries to open a network connection to another host or to look one up, and its failure says it
  opened a real network connection. A server the test starts on `127.0.0.1`, and a Unix socket,
  still work. No setting turns this off.
- `chain_development.py --check-commit-shape` answers whether a draft closing-marker body would pass
  the chain's commit-shape check, in the chain's own words. It reads the product path off the
  project card, and refuses with exit 2 an input that names no change.
- A Codex run can run a product's gate in the macOS guest. The run makes the one gate call outside
  its sandbox by approval, and `core/tools/gate_suite.py` puts each command it starts back into a
  sandbox with the internet closed.
- `core/tools/check_record_privacy.py` runs from the pre-commit hook. It refuses a commit that adds
  a line naming the committing machine's home folder or login name to a record, which is a file
  under `system/projects/` or in any `docs/` folder.
- `core/tools/check_test_isolation.py` runs from the pre-commit hook. It refuses a commit whose test
  files read the machine they run on: the home folder, a private project's folder from a test that
  travels without it, or a real commit handed to git. The refusal says to fix those lines on the
  branch. A pinned Codex run's commits meet the git hooks too.
- Each test in KensaiApp's own suites runs with an empty home folder made for it, and the gate runs
  a product's suite on the host Mac with one too.
- `/bin/bash core/tools/doctor.sh` reports whether the machine has the six tools KensaiApp runs on
  (uv, git, podman, tart, gh and claude), each at its minimum version. It exits 1 when one is
  missing or too old, and `--help` lists the minimum versions.
- The instance root carries `.python-version`, `pyproject.toml` and `uv.lock`. Together they fix
  Python 3.14 and the exact pytest and pytest-xdist versions that `uv run --locked pytest
  core/tools/ core/launchers/` runs the suites on.
- `development-implementation` asks the chain's commit-shape check about its closing marker's body
  before it commits the marker, and answers each task the check names.
- `changelog-line` is a Content Editor skill that the change chain runs on a change's branch, after
  implementation and before code integrity. It writes the change's entry under `## [Unreleased]` in
  the `CHANGELOG.md` at the change's product path. It removes the `docs/what_left.md` entries whose
  whole want the change completes. A part-complete entry stays. Where the product path keeps no
  `CHANGELOG.md`, it writes nothing there and the step still finishes.
- This changelog. The entries of 0.1.0 to 0.4.0 moved into it from `RELEASE_NOTES.md`.
- **tracker17.** You can filter a project's task list by status, priority, assignee, label, due-date
  range or Overdue. Apply keeps your choices in the controls and in the page's address, and Clear
  shows every task again. A filter that matches nothing says so.
- **tracker17.** You can sort a project's task list by due date, priority, created time or title, in
  either direction, whether the list is filtered or not.
- **tracker17.** The All tasks page lists the tasks of every project, with a Project column and the
  same filter and sort controls a project's list has. Every page's header links to it.
- **tracker17.** A project's Summary shows its task counts by status and by priority, its Overdue
  count, its count of tasks with no due date, and each assignee's open tasks. Each status count,
  each priority count and the Overdue count opens the project's task list filtered to that one
  value.
- **tracker17.** You can delete a task from its page after you confirm. The task's comments go with
  it, and you land on its project with a line naming the task. Delete task and its confirmation are
  full-size controls.
- **tracker17.** You can rename a project from its Tasks view. The new name meets the same rules as
  a new project's name, and the project's tasks, comments and addresses stay as they were.
- **tracker17.** You can delete a project and all of its tasks after you confirm. You land on
  Projects with a line naming the project and how many tasks went with it. Afterwards the project's
  addresses show the not-found page, and an action sent for the project or one of its tasks changes
  nothing.
- **tracker17.** A second tracker started on the same saved data is refused with the line "The
  tracker didn't start, because another tracker is already running on the same saved data. Stop that
  one first, then start this one." The first tracker carries on, and a tracker that was killed
  doesn't prevent the next start. The setup instructions describe both.
- **tracker17.** `products/tracker17/docs/adr/` holds six new decision records, ADR-0011 to
  ADR-0016. ADR-0013 to ADR-0016 are in force, and they supersede ADR-0002, ADR-0005, ADR-0006 and
  ADR-0010. ADR-0011 and ADR-0012 are superseded by ADR-0014 and ADR-0015.
- **tracker17.** The repository's history carries every commit made to tracker17 since 0.4.0 was
  cut, so you can follow how KensaiApp builds an app, change by change and step by step. Its history
  before that is not published.
- **Front door.** Under the hood, a new guide for software and AI engineers, says how KensaiApp
  works: why, the change and the walk, how each change is isolated, context, the rules code holds,
  the layers, models and providers, languages, telemetry, satellites, and how KensaiApp is
  engineered.
- **Front door.** Background, a new page, says where KensaiApp came from, what inspired it and who
  made it.

### Changed

- The Bash approval hook approves a command that starts `core/tools/locked_python.sh` on the same
  terms as one that starts `python3`. When the command hands the runner inline code with `-c` or
  `-`, Claude Code asks about it instead.
- The `records-owed` row of `core/doctrine/flow/step_outcome_contract.md` § *The halts* states that,
  on a `full` card, the chain copies each named item the main checkout's companion does not hold
  open from the change worktree's companion onto the main checkout's, and commits it there, before
  it launches `product-docs`. It names the halts the chain gives when it cannot make that copy.
- `core/doctrine/flow/step_outcome_contract.md` § *The halts* has a `records-owed` row. It states
  when the chain reads a `records-owed` halt report from `specs`, `design` or `plan`, when it
  launches `product-docs` and starts the change again, and each halt that route can end in.
  `core/doctrine/setup/kensaiapp_structure.md` states that the chain answers such a report rather
  than only halting on it.
- The doctrine calls a project's "done" its finish line, in place of the Agari 上がり. The directional
  trailer for a project with no open station is `Finish-line:`.
- The doctrine names the `change`, `walk`, `product-docs` and `prd-and-finish-line` launchers in
  place of `chain-development`, `chain-change`, `chain-product` and `chain-agari`.
  `core/doctrine/setup/kensaiapp_structure.md` lists each old launcher path among its reference-only
  migrations, beside the path that replaced it.
- `core/doctrine/setup/kensaiapp_structure.md` names the two step tables
  `core/tools/chain_development.py --steps` takes `change`, for the `change` launcher, and `walk`,
  for the `walk` launcher. It states that the `change` launcher keeps its records as
  `chain-change-<project>-*` and the `walk` launcher keeps its own as `chain-walk-<project>-*`.
- `core/doctrine/engineering/languages/swift/environment.md` states that the gate reads the macOS
  guest's name and shares from the guest's login job, and that a gate's caller gives none. It also
  states that the gate stops every guest process running from a copy before it removes the copy.
- `core/doctrine/flow/step_outcome_contract.md` states that a saved-red note, `- Task <N> red saved
  as <commit> — <reason>`, counts as a task's red when the commit it names is a non-landing commit
  of that task, older than its landing, with a pause of the change between the two.
- `core/doctrine/governance/versioning.md` states that the entry a merge adds to a shell file's `#
  Version:` lines carries the merge's description without a change's key or a path into one of the
  instance's projects, the parts the vendor-neutrality check would report.
- The Python and shell toolchain packets under `core/doctrine/engineering/languages/`,
  `core/doctrine/setup/kensaiapp_structure.md`, `setup_scope.md` and `shared_core_instance.md` state
  that KensaiApp's hooks, launchers, skills' commands and test suites run on the Python that
  `.python-version` names, through uv and `core/tools/locked_python.sh`. The structure map states
  that a pin carries the root's `.python-version`, `pyproject.toml` and `uv.lock`.
- `core/doctrine/governance/records_name_no_machine.md` states that a record names no repository
  address either. No line names the `<owner>/<name>` of the repository the record is committed to,
  which its `origin` remote carries, and the file gives `<owner>/<repository>` to write in its
  place.
- `core/doctrine/setup/setting_up_a_project.md` states which part of the definition sequence each
  `Definition:` value walks and which setup seed it stamps, and that a no-code product is never
  `full`. `kensaiapp_structure.md` and `setup_scope.md` name the second seed template,
  `setup_seed_prd_and_finish_line_template.md`.
- `core/doctrine/flow/development_flow.md` § *The stages* has a row for `changelog-line`, the
  Content Editor step after implementation and before code integrity.
  `core/doctrine/flow/folder_state_handoff.md` and `step_outcome_contract.md` state that the step is
  done once its report is committed on the change's branch, whether or not it changed a product
  file. `core/doctrine/setup/kensaiapp_structure.md` § *The what-left file — the one place a product
  states what is still to build* states that `changelog-line` removes an entry on the change's
  branch, so the removal reaches `main` in the merge that carries the wanted thing. The `Merged in`
  line of a removal's commit names a commit on the change's branch at which the product does the
  wanted thing.
- `core/doctrine/setup/kensaiapp_structure.md` names `changelog-line` as the one run that removes a
  what-left entry, and no longer names `readme-status` or its row in the `build-idea` queue. § *The
  changelog* says a product's state is read from its `CHANGELOG.md` and its `docs/what_left.md`, and
  that a product keeps no release-notes file. `core/doctrine/README.md` says each change in
  `core/doctrine/` is recorded in its `CHANGELOG.md`.
- `core/doctrine/engineering/testing_doctrine.md` § *A test reads nothing of the machine it runs on*
  states that a test depends on nothing else of the machine it runs on. It names four more things a
  test may not depend on, each with what the test does instead: who runs it, the system's own tools,
  the system's terminal and the network. A table shows which of the section's seven rules the
  commit-time check and the guards that run while tests run each check, and the section says neither
  place checks the four new ones.
- The `walk` launcher's messages call its own walk `walk`, and name the `product-docs` or
  `prd-and-finish-line` walk that runs before it on a project with a definition.
- The `walk` launcher and build-idea read `full`, `prd-and-finish-line` or `none` from a card's
  `**Definition:**` line, and name those three in their refusals. The launcher prints
  `definition=prd-and-finish-line` for the PRD-and-finish-line walk. A card reading `prd-agari` is
  refused.
- On a project whose card reads `**Definition:** full`, a `records-owed` halt now copies each raised
  item the step wrote in the change's worktree onto the product's main checkout before
  `product-docs` launches, so the sweep can fold it. The item goes to the end of the companion's
  *Raised from downstream* section in one commit on `main`, and an item `main` already holds is not
  copied again. The walk stops without writing when that checkout does not have `main` out or the
  companion has uncommitted changes, and when the commit fails it puts the companion back as it was.
- The chain board and the KensaiApp panel name the `product-docs`, `prd-and-finish-line`, `change`
  and `walk` launchers. The panel's line for the change a walk is on is the change's title, with no
  label in front, and a change not opened yet reads `next change`. `.providers.toml.example` names
  the new launchers too.
- The gate reads the macOS guest's name and shares from the guest's login job each time it runs, and
  a plan names no guest. Every path the gate reports writes the home folder as `<home>`.
- Without uv, the runner's message names everything that stops (hooks, skills' commands and
  launches) and says that a commit the git hooks check is refused.
- A launch that makes a new pin prepares the pin's own environment with the source host's Python
  before it starts, through `locked_python.sh --prepare-pin`. It installs no package and downloads
  no Python. A failed preparation stops the launch before it is announced.
- The launch entry in `core/tools/pin_run.sh`, the launch helpers and the three kaizen launch
  scripts (`launch-audit.sh`, `launch-fix-author.sh` and `launch-apply-packet.sh`) run their Python
  through `core/tools/locked_python.sh`. `locked_python.sh --check <launcher>` is the one look for
  uv a launch makes at its entry.
- The `Containerfile` builds on `ghcr.io/astral-sh/uv:python3.14-bookworm-slim`, the Python the
  instance pins, in place of Python 3.13.
- Claude Code's hooks and the git hooks run through `core/tools/locked_python.sh`, on the Python the
  instance pins, rather than on the first `python3` the shell finds. A pin carries the root's
  `.python-version`, `pyproject.toml` and `uv.lock`, and a satellite's hook commands name the host's
  runner.
- A walk's notifications name it after its launcher, `walk chain` for the `walk` launcher's walk and
  `change chain` for the `change` launcher's.
- `core/tools/check_record_privacy.py` also refuses a commit that adds a line naming the
  repository's own address to a record. The address is the `<owner>/<name>` read off the
  repository's `origin` remote, when that remote is on a hosting service, in any letter case.
- The skills name the `change`, `walk`, `product-docs` and `prd-and-finish-line` launchers in place
  of `chain-development`, `chain-change`, `chain-product` and `chain-agari`.
- `development-specs` runs every rule a spec calls unchanged against the change's base commit and
  records the result in Verified Claims. A rule that does not hold at the base is restated.
- `nemawashi-retire` reads a folder seed's paths off the index. When its commit is refused only over
  files the retire itself moved, it declares them and commits once more.
- `development-implementation` saves a task's failing tests under `— red`, whatever the reason for
  saving them. A red that an earlier run saved under another label gets a saved-red note in place of
  a rewrite. A pause names the last task that landed.
- The skills that write a record into a change folder, and the plan's instruction template, point at
  the rule that a record names no machine.
- `stations-from-seed` reads each test a station's bar requires to fail today against the product's
  code, and confirms that the defect can make the test fail.
- `shukuba-refine` also reads the `change` launcher's record when it checks that no walk is in
  flight on a change.
- The skills that write a record, and the plan's instruction template, state that a record names no
  repository address. That address is the `<owner>/<name>` of the repository the record is committed
  to.
- `project-setup` asks how much is written down before the work starts. Software offers everything,
  just what it is and when it's done, or nothing; a product without code offers the last two. Under
  nothing, setup asks no product questions, writes no answer files and starts no walk.
- `project-stamp` stamps the setup seed the card's `Definition:` names: `full` the whole definition
  chain, `prd-and-finish-line` a seed that ends at the finish line, and `none` no seed. It refuses
  `--type no-code --definition full`, and a no-code product defaults to `prd-and-finish-line`.
- `stations-from-seed` reads the product's SDD when it has one. Each station takes a whole slice,
  and a station that takes only part of one is cut only together with an item raised on the SDD's
  companion asking for the slice to be split. A product with no SDD is cut as before.
- `dependency-repair` runs the commit builder's changelog check, `merge --check-only`, on each of
  its merges to `main` before any merge lands. When one check refuses, it merges nothing. Each merge
  carries a `CHANGELOG.md` entry that the skill writes on the branch, or a `--user-invisible` reason
  that the paths the branch changes decide.
- `changelog-line` writes a change's entry in the `CHANGELOG.md` of each product path the change's
  branch changes, not only in the one at the change's own product path. A change to a root file a
  fresh clone gets is logged in `core/tools/CHANGELOG.md`. It still removes what-left entries at the
  change's own product path only.
- `test-driven-development` no longer ranks a real collaborator above a fake for a unit test, and
  names the testing doctrine and the product's language guide as the standard its tests meet.
  `development-code-integrity` checks code against the language guide, `arch_defaults.md` and
  `testing_doctrine.md`, and repairs code that builds its own collaborators, or a unit test that
  touches a real resource, instead of passing it. `development-implementation` brings a module it
  edits up to that standard in the same change. `development-design` and the plan's instruction
  template state each new test's layer and the fakes it hands in. The `test-driven-development`
  references hand a collaborator in instead of patching the module that holds it, and the
  deferred-decisions template no longer counts those two conflicts as a packet departure.
- **tracker17.** A start on saved data the tracker can't read no longer stops. The tracker prints
  one line saying so in its terminal, and every address shows one page that says the same thing,
  with no links and no controls. The start and the page change nothing in the saved data. The line
  and the page write a byte of the path that isn't text as `\x` and its two hex digits. The setup
  instructions describe the line and the page.
- **tracker17.** The setup instructions' section on what the start prints names all three lines a
  start can print. It says which two mean the tracker is running and which one means the start has
  stopped.
- **tracker17.** The README's account of how tracker17 is built says that uv makes the tests'
  virtual environment. It cites ADR-0013 for the standard-library rule, and it points at the
  decision records through their index rather than by a count.
- **tracker17.** The README's Status section lists the filters, the sorts, the All tasks page, the
  Summary, and deleting and renaming as built, and says that nothing the tracker was defined to do
  is left to build. `products/tracker17/docs/what_left.md` says that nothing is left to build.
- **tracker17.** `products/tracker17/docs/PRD.md`, at version 8, states that tracker17 is public,
  shipped as an example in every KensaiApp release from v0.1.0.
- **tracker17.** `products/tracker17/docs/SRS.md`, at version 7, carries the PRD's corrected
  statement that tracker17 is public, as a note that sets no requirement.
- **tracker17.** `products/tracker17/docs/UXD.md`, at version 11, states where the page shows the
  line for a refused move when a filter leaves the task off the list. It does the same for the line
  for a move that didn't happen.
- **tracker17.** `products/tracker17/docs/CONTENT.md`, at version 21, adds the term "killed" for a
  tracker ended by force and the term "this start has stopped" for a refused start. It adds the
  words for a start on saved data the tracker can't read, and one form for a path the tracker
  prints. A row's controls end their accessible names with the row's number on the list, and a
  project's deletion counts its tasks and not their comments.
- **tracker17.** `products/tracker17/docs/fdr.md`, at version 6, states how the tracker behaves on
  saved data it can't read. It also says that the README's opening paragraph names both of
  tracker17's purposes, and that the prerequisites name the tool the test suite needs. A return to a
  confirmation shows what the saved data allows, and a filter or sort value no control can hold is
  refused.
- **tracker17.** `products/tracker17/docs/SDD.md`, at version 19, defines a submission as a `post`
  form and a `get` form as a read. It answers every page that shows a pending confirmation with 202,
  sets up the test suite with uv, and states how the tracker serves saved data it can't read.
- **tracker17.** `products/tracker17/docs/nfdr.md`, at version 24, follows ADR-0011 to ADR-0016. It
  names the tests behind deleting a task and a project, runs both test suites through uv, and states
  how a review meets the dependency checks.
- **swe-benchmark-poc.** The `README.md` says each change in this folder is recorded in its
  `CHANGELOG.md`.
- **Front door.** The README is written anew, to say what KensaiApp does rather than how. It covers
  the software factory, its coding standards and practices, the finish line and the route, the
  commands that walk a project, the panel, one instance with several projects, installation, the
  human in the loop, the interactive session, the examples and what is built with KensaiApp, its
  purpose, its limits and what is being worked on. How it works moves to Under the hood.
- **Front door.** What is in it replaces How it works, and keeps only how the work is decided.
- **Front door.** The how-to gives each task one line, then how to do it in a session and from the
  terminal. It takes the operations guide's tasks, and a new entry, How to run KensaiApp's own
  tests, says what the suite needs and what to expect.
- **Front door.** The glossary calls a project's "done" its finish line, and adds the changelog line
  and CHANGELOG entries.

### Removed

- `core/doctrine/setup/kensaiapp_structure.md` no longer allows a change-pipeline step a launcher of
  its own, in a folder nested below the change pipeline's launcher. Each step starts through the
  skill launcher.
- The `build-idea` queue no longer runs `readme-status` after it closes a reached station, and
  `.providers.toml.example` no longer lists a `readme-status` row. A `.providers.toml` that still
  lists one does not stop the queue.
- The `readme-status` skill is removed, so `launcher.sh readme-status <project>` no longer starts a
  run. `shukuba-refine` no longer writes a `readme-status` row in its `## Next moves` table.
- `RELEASE_NOTES.md`, which this changelog replaces.
- **tracker17.** The `README.md` no longer has a Status section listing what the tracker does and
  the commit each thing came in with. In its place, it says each change is recorded in
  `CHANGELOG.md` and what is left to build is listed in `docs/what_left.md`.
- **Front door.** The operations guide. Its tasks are in the how-to, and the rest is in the README
  and Under the hood.

### Fixed

- The `walk` launcher writes its end hooks so that a core path holding a tab or a newline stays one
  word, and the next walk starts.
- `test_suite_map.py` passes in a clone of this repository, which holds a `.github/` folder. The
  suite map matches `.github/**` and runs no suite for it, as for `docs/**` and `about/**`.
- `test_gate_suite.py` no longer fails by timing on a machine where the consumer of a pipe exits
  before its producer writes. A pipe in `gate_suite.py` whose producer is ended by a broken pipe,
  because its consumer failed first, now reports the consumer's status in place of `-13`.
- Nine tests in `core/tools/` no longer fail on a Linux machine that has no Python at
  `/usr/bin/python3`, or no `npx` and `node`. The pin-preparation tests in `test_locked_python.py`
  and `test_pin_run.py` run on the suite's own Python, and the skill-launcher dry run in
  `test_chain.py` puts stand-ins for the programs a skill requires on PATH.
- An approved Codex gate runs its test commands without adding a second sandbox, allowing
  localhost-based test setup to execute. Codex still requests approval for the gate invocation.
- A product's browser suite that the gate runs on the host Mac finds Playwright's browsers. The
  empty home keeps `PLAYWRIGHT_BROWSERS_PATH` at its default unless the caller set it.
- Before the gate removes a copy of a product in the macOS guest, it stops every process running
  from that copy, with each one's direct children. It says on standard error how many it stopped.
- The `build-idea` queue counts a journey move as landed only once the move is in the instance's
  last commit, not when it shows on disk. That covers a retire, a station close, a pick, a route cut
  and a docs cut.
- The chain accepts a task's red that an earlier run saved under another label when a saved-red note
  names it. The named commit must be a non-landing commit of that task, older than its landing, with
  a pause of the change between the two.
- `core/tools/locked_python.sh` refuses by name a root that holds no `pyproject.toml`, since that
  root is not a KensaiApp instance.
- A walk started from a checkout whose path holds a space no longer ends `no_runnable_command`. The
  chain keeps the core's path as one word in the launch commands it builds.
- The chain engine advances each launch once. Starting, advancing and stopping a walk each hold a
  lock on its state file, and two saves made at once both complete.
- A Codex run sets `UV_CACHE_DIR` to a folder its sandbox can write, so the runner no longer exits 2
  inside every Codex step.
- `commit_builder.py merge --bump` writes a shell file's `# Version:` note without the parts the
  vendor-neutrality check would report, such as a change's key. A merge's description can no longer
  turn `main` red through that note.
- `changelog-line` writes its report with no `version:` line, so the change chain's changelog step
  commits again. Each report had copied its template's marker, and the commit builder refuses a new
  file whose marker is not `1.0.0`.
- **tracker17.** A start on readable saved data whose path holds a byte that isn't text prints its
  ready line and serves. The line writes that byte as `\x` and its two hex digits.
- **tracker17.** Ctrl-C pressed after the ready line, before the tracker begins serving or while it
  closes down, stops the tracker quietly, as Ctrl-C does while it serves.
- **tracker17.** On the People page, the line shown after you set a name that holds `{` or `}` shows
  the name as you typed it, whether the name was saved or not.

### Security

- The Bash approval hook, `.claude/hooks/development-bash-approve.py`, stops approving commands
  whose effect it never read, and Claude Code asks about each of them instead. They include an awk
  or sed program that can run a command or write a file, an unquoted heredoc carrying a
  substitution, a git subcommand outside an allowed list, an `rg` option outside an allowed list, a
  `case` branch's command, and a quote or escape the shell reads differently from the hook. Any read
  of a `.env` file, or of a credentials folder such as `.aws` or `.config/gh`, is asked about too,
  except listing the key names in `~/.env`. The hook's header states that it does not guard the
  process environment.
## [0.4.0] - 2026-10-25

### Upgrading from 0.3.0

- If you set up a clone of an earlier release, add `security = "claude"` under `[steps]` in your
  `.providers.toml`, as `.providers.toml.example` now has it: a step with no entry is refused by
  name.

### Added

- A new step in every change, Security, between Prove and Audit: the senior engineer runs the
  product's dependency audit and reads the change's code for security holes. It fixes what its rules
  allow, writes an exception for an advisory the product does not reach, and reports the rest for the
  PM. It stops the walk only when a fix needs a move it may not make. It is a first iteration.
- `dependency-repair`: when a product's main branch turns red with no commit behind it, because its
  dependency audit reads an advisory published since the last green run, the chain repairs it once on
  a branch and merges it before it stops the walk.
- A new stop, `environment-not-ready`, when a test environment cannot install the product's languages
  or dependencies, before any test runs.
- The panel shows how long a walk and its step have run, and which task of the plan the build is on.
- **Front door.** A new guide, How it works: the three checks on a change, where what they find goes,
  the PM's review of the route, the two kinds of finding, when a walk stops for you, and what a change
  costs.

### Changed

- Where a product's CI runs a matrix, each version gets its own test container.
- `--gate-owners-mac` carries from a walk to the queue after it, and `build-idea` takes it.
- `seeds-from-idea` runs in a session, from the `principal-pm` group, and has no launcher. An idea
  arrives as a brief you confirm, with the files it rests on quoted and checked.
- `ad-hoc-plan` starts from a brief you confirm, and every run leaves a report beside it.
- **Front door.** The pipeline in the README and the overview diagram show the Security step.
- **Front door.** The audit is described as what it is: a check of how well each of KensaiApp's steps
  did its job, not of the product, which is why it does not stop a change.
- **Front door.** What KensaiApp does not promise is said more plainly, and the README says it may
  support other workflows with the right adjustments.
- **Front door.** ka-telemetry's entry links what building it cost.

## [0.3.0] - 2026-10-22

### Added

- The panel shows each project's route as a tree.
- A walk's gates stop before implementation when a product still owes a decision on where its tests
  run.
- **Front door.** The README carries a version badge.
- **Front door.** A new README section, Built with KensaiApp, lists ka-telemetry.
- **Front door.** The how-to guide names the check to run after a Python upgrade, and the stop a walk
  makes when a product owes that decision on where its tests run.
- **tracker17.** A task in `todo` or `in-progress` has a `cancelled` move on its list row and its
  page. The first press opens a confirmation in place, and only confirming saves the move.
- **tracker17.** The timed run covers a status move at 1,000 tasks of 20 comments each.

### Changed

- Telemetry and the context cap run on [ka-telemetry](https://github.com/eyalgo/ka-telemetry), an
  open-source package KensaiApp built, on PyPI as `ka-telemetry`. The package is installed once into
  `~/.kensaiapp/venv`, and `.telemetry.env` names its command.
- **Front door.** The Python badge reads 3.13+.
- **Front door.** Getting started lists pytest and pytest-xdist in step 1, with their install
  command. Setting up your first project is step 4, and the two optional steps, the panel and
  telemetry, follow it.
- **Front door.** Telemetry's setup moved to a new how-to section, How to collect telemetry.
- **tracker17.** A move pressed on a page whose task has since changed status saves nothing, and the
  page says the status has changed and which moves it now allows.

### Removed

- The bundled telemetry receiver and its settings script. ka-telemetry takes their place.

### Fixed

- **tracker17.** Going Back in the browser after confirming no longer brings the old confirmation
  back to life.

## [0.2.0] - 2026-10-19

### Added

- **tracker17.** A task can be moved through its status workflow.

### Changed

- **Front door.** The README is reordered for a first-time reader: what KensaiApp is, who it is for,
  how one change moves, how the work is kept in check and how to start, with an overview diagram and
  one shipped change walked through its files.
- **Front door.** The reference material moved, word for word, into two new guides, the architecture
  overview and the operations guide.

## [0.1.0] - 2026-10-19

### Added

- The first release: the shared core, the roles, the skills, the tools, the launchers, the hooks and
  the templates a fresh clone needs, with two example projects, tracker17 and swe-benchmark-poc.

[unreleased]: https://github.com/eyalgo/kensaiapp/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/eyalgo/kensaiapp/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/eyalgo/kensaiapp/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/eyalgo/kensaiapp/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/eyalgo/kensaiapp/releases/tag/v0.1.0
