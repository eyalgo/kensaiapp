# Changelog — `skills`

Each entry records a change to what a user of a fresh clone installs, runs, types or reads in `skills/`. It names the project the change was made under and cites the commits that made it. The format follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Upgrading

- **dev-skills** — Type `project-finish-line` where you typed `project-dod`: the CPO skill that declares a project's finish line is renamed, and the old name is not kept. That covers its launcher call (`launcher.sh project-finish-line <project>`) and setup seeds that name it. (`950438dee`, `436ce1bf9`)
- **dev-skills** — Type `project-dod` where you typed `project-agari`: the CPO skill that declares a project's Definition of Done is renamed, and the old name is not kept. That covers its launcher call (`launcher.sh project-dod <project>`) and setup seeds that name it. (`da89cda94`)
- **tools** — Install uv for skills' commands to run. A skill command that ran `python3` starts `<CORE>/tools/locked_python.sh` in its place, which runs the command on the Python the instance pins, through uv, and stops without uv rather than falling back to `python3`. (`98a82927a`)
- **dev-skills** — Type `seed-pick` where you typed `nemawashi-pick`: the skill that picks a project's next seed is renamed, and the old name is not kept. That covers its launcher call (`launcher.sh seed-pick <project>`) and its `--skill` and `--prompt seed-pick/thin` names. Run `shukuba-refine` or `nemawashi-refine` again for a route report written before the rename: the `build-idea` queue refuses a pick row that names `nemawashi-pick`. (`128b8c3d0`)

### Added

- **tools** — `development-implementation` asks the chain's commit-shape check about its closing marker's body before it commits the marker, and answers each task the check names. (`2d932b698`, `1d05f0ac1`)
- **tools** — `changelog-line` is a Content Editor skill that the change chain runs on a change's branch, after implementation and before code integrity. It writes the change's entry under `## [Unreleased]` in the `CHANGELOG.md` at the change's product path. It removes the `docs/what_left.md` entries whose whole want the change completes. A part-complete entry stays. Where the product path keeps no `CHANGELOG.md`, it writes nothing there and the step still finishes. (`d8755a31b`)

### Changed

- **dev-skills** — The skills name the `change`, `walk`, `product-docs` and `prd-and-dod` launchers in place of `chain-development`, `chain-change`, `chain-product` and `chain-agari`. (`8ec5d752c`, `7ebc2d82c`, `36fb2dd25`)
- **product-definition** — `development-specs` runs every rule a spec calls unchanged against the change's base commit and records the result in Verified Claims. A rule that does not hold at the base is restated. (`aa4d9422c`, `2d6b88329`)
- **tools** — `nemawashi-retire` reads a folder seed's paths off the index. When its commit is refused only over files the retire itself moved, it declares them and commits once more. (`1bcdea3f6`, `f32374252`)
- **dev-skills** — `development-implementation` saves a task's failing tests under `— red`, whatever the reason for saving them. A red that an earlier run saved under another label gets a saved-red note in place of a rewrite. A pause names the last task that landed. (`6d8016036`, `f4f137a3c`, `0ee2a13bc`)
- **tools** — The skills that write a record into a change folder, and the plan's instruction template, point at the rule that a record names no machine. (`7ed8e9e0e`)
- **dev-skills** — `stations-from-seed` reads each test a station's bar requires to fail today against the product's code, and confirms that the defect can make the test fail. (`c63eb2e72`, `adfd158db`, `4b89070fd`)
- **dev-skills** — `shukuba-refine` also reads the `change` launcher's record when it checks that no walk is in flight on a change. (`333051e69`)
- **dev-skills** — The skills that write a record, and the plan's instruction template, state that a record names no repository address. That address is the `<owner>/<name>` of the repository the record is committed to. (`068b8be3c`, `b7b25d2ef`)
- **dev-skills** — `project-setup` asks how much is written down before the work starts. Software offers everything, just what it is and when it's done, or nothing; a product without code offers the last two. Under nothing, setup asks no product questions, writes no answer files and starts no walk. (`2de6fae45`, `2fcd9747f`)
- **dev-skills** — `project-stamp` stamps the setup seed the card's `Definition:` names: `full` the whole definition chain, `prd-and-dod` a seed that ends at the Agari, and `none` no seed. It refuses `--type no-code --definition full`, and a no-code product defaults to `prd-and-dod`. (`2de6fae45`, `2fcd9747f`)
- **product-development** — `stations-from-seed` reads the product's SDD when it has one. Each station takes a whole slice, and a station that takes only part of one is cut only together with an item raised on the SDD's companion asking for the slice to be split. A product with no SDD is cut as before. (`af553f48f`)
- **tools** — `dependency-repair` runs the commit builder's changelog check, `merge --check-only`, on each of its merges to `main` before any merge lands. When one check refuses, it merges nothing. Each merge carries a `CHANGELOG.md` entry that the skill writes on the branch, or a `--user-invisible` reason that the paths the branch changes decide. (`a1dc5a723`, `eca03a01a`, `8b967dad6`)
- **tools** — `changelog-line` writes a change's entry in the `CHANGELOG.md` of each product path the change's branch changes, not only in the one at the change's own product path. A change to a root file a fresh clone gets is logged in `core/tools/CHANGELOG.md`. It still removes what-left entries at the change's own product path only. (`bb01ee97a`)
- **product-development** — `test-driven-development` no longer ranks a real collaborator above a fake for a unit test, and names the testing doctrine and the product's language guide as the standard its tests meet. `development-code-integrity` checks code against the language guide, `arch_defaults.md` and `testing_doctrine.md`, and repairs code that builds its own collaborators, or a unit test that touches a real resource, instead of passing it. `development-implementation` brings a module it edits up to that standard in the same change. `development-design` and the plan's instruction template state each new test's layer and the fakes it hands in. The `test-driven-development` references hand a collaborator in instead of patching the module that holds it, and the deferred-decisions template no longer counts those two conflicts as a packet departure. (`676753b27`, `74a2ea7ff`, `6a237a23e`, `18034fd5a`, `92b140213`, `598c2a9e0`)

### Removed

- **tools** — The `readme-status` skill is removed, so `launcher.sh readme-status <project>` no longer starts a run. `shukuba-refine` no longer writes a `readme-status` row in its `## Next moves` table. (`a3fcb00e5`)

### Fixed

- **tools** — `changelog-line` writes its report with no `version:` line, so the change chain's changelog step commits again. Each report had copied its template's marker, and the commit builder refuses a new file whose marker is not `1.0.0`. (`5120cb790`)
