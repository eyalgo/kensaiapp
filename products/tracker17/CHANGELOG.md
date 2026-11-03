# Changelog — `products/tracker17`

Each entry records a change to what a user of a fresh clone installs, runs, types or reads in `products/tracker17/`. It names the project the change was made under and cites the commits that made it. The format follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Upgrading

- **tracker17** — The tests' dependencies are locked in `products/tracker17/uv.lock`, and `tests/requirements.txt` no longer exists. To run the tests, install uv, then type `uv sync --locked` and `uv run playwright install chromium` inside `products/tracker17`. Type each test command through `uv run`, such as `uv run pytest tests/`. The tracker itself still starts with `python3 main.py` and doesn't need uv. (`3553cf36d`, `a71d23637`)

### Added

- **tracker17** — You can filter a project's task list by status, priority, assignee, label, due-date range or Overdue. Apply keeps your choices in the controls and in the page's address, and Clear shows every task again. A filter that matches nothing says so. (`819f5b37b`)
- **tracker17** — You can sort a project's task list by due date, priority, created time or title, in either direction, whether the list is filtered or not. (`e5eaf28b6`)
- **tracker17** — The All tasks page lists the tasks of every project, with a Project column and the same filter and sort controls a project's list has. Every page's header links to it. (`9f74b3d50`)
- **tracker17** — A project's Summary shows its task counts by status and by priority, its Overdue count, its count of tasks with no due date, and each assignee's open tasks. Each status count, each priority count and the Overdue count opens the project's task list filtered to that one value. (`599dd0fbe`, `54e7bcf44`)
- **tracker17** — You can delete a task from its page after you confirm. The task's comments go with it, and you land on its project with a line naming the task. Delete task and its confirmation are full-size controls. (`e25e527b9`, `b8777bee0`)
- **tracker17** — You can rename a project from its Tasks view. The new name meets the same rules as a new project's name, and the project's tasks, comments and addresses stay as they were. (`1eecb6c0e`)
- **tracker17** — You can delete a project and all of its tasks after you confirm. You land on Projects with a line naming the project and how many tasks went with it. Afterwards the project's addresses show the not-found page, and an action sent for the project or one of its tasks changes nothing. (`ac09e56af`, `2600b3b5e`)
- **tracker17** — A second tracker started on the same saved data is refused with the line "The tracker didn't start, because another tracker is already running on the same saved data. Stop that one first, then start this one." The first tracker carries on, and a tracker that was killed doesn't prevent the next start. The setup instructions describe both. (`281853622`)
- **tracker17** — `products/tracker17/docs/adr/` holds six new decision records, ADR-0011 to ADR-0016. ADR-0013 to ADR-0016 are in force, and they supersede ADR-0002, ADR-0005, ADR-0006 and ADR-0010. ADR-0011 and ADR-0012 are superseded by ADR-0014 and ADR-0015. (`db16374d3`, `d459f69d9`, `909fc536c`, `04c348675`)

### Changed

- **tracker17** — A start on saved data the tracker can't read no longer stops. The tracker prints one line saying so in its terminal, and every address shows one page that says the same thing, with no links and no controls. The start and the page change nothing in the saved data. The line and the page write a byte of the path that isn't text as `\x` and its two hex digits. The setup instructions describe the line and the page. (`cc37b1bde`, `6591e5482`, `1872c3314`)
- **tracker17** — The setup instructions' section on what the start prints names all three lines a start can print. It says which two mean the tracker is running and which one means the start has stopped. (`f9672619d`)
- **tracker17** — The README's account of how tracker17 is built says that uv makes the tests' virtual environment. It cites ADR-0013 for the standard-library rule, and it points at the decision records through their index rather than by a count. (`a71d23637`)
- **tracker17** — The README's Status section lists the filters, the sorts, the All tasks page, the Summary, and deleting and renaming as built, and says that nothing the tracker was defined to do is left to build. `products/tracker17/docs/what_left.md` says that nothing is left to build. (`fbbda3139`, `a23407d94`, `7624eac72`, `4791167d6`, `e91364eaa`, `fe9460977`, `75eb81760`)
- **tracker17** — `products/tracker17/docs/PRD.md`, at version 8, states that tracker17 is public, shipped as an example in every kensaiapp release from v0.1.0. (`b04ddbdfe`)
- **tracker17** — `products/tracker17/docs/SRS.md`, at version 7, carries the PRD's corrected statement that tracker17 is public, as a note that sets no requirement. (`fcb74cf87`)
- **tracker17** — `products/tracker17/docs/UXD.md`, at version 11, states where the page shows the line for a refused move when a filter leaves the task off the list. It does the same for the line for a move that didn't happen. (`ae866ee35`, `6055366de`)
- **tracker17** — `products/tracker17/docs/CONTENT.md`, at version 21, adds the term "killed" for a tracker ended by force and the term "this start has stopped" for a refused start. It adds the words for a start on saved data the tracker can't read, and one form for a path the tracker prints. A row's controls end their accessible names with the row's number on the list, and a project's deletion counts its tasks and not their comments. (`7ca242684`, `952932972`, `759bc4110`, `6effdff29`, `43673f95f`, `4f2fbdb90`)
- **tracker17** — `products/tracker17/docs/fdr.md`, at version 6, states how the tracker behaves on saved data it can't read. It also says that the README's opening paragraph names both of tracker17's purposes, and that the prerequisites name the tool the test suite needs. A return to a confirmation shows what the saved data allows, and a filter or sort value no control can hold is refused. (`3eae92d0c`, `86f97f253`)
- **tracker17** — `products/tracker17/docs/SDD.md`, at version 19, defines a submission as a `post` form and a `get` form as a read. It answers every page that shows a pending confirmation with 202, sets up the test suite with uv, and states how the tracker serves saved data it can't read. (`328b15aaf`, `cb9ef1445`, `0ac110bab`, `3266cb262`, `01d3d925a`, `6f2366ae6`, `78963ba46`, `b70900868`)
- **tracker17** — `products/tracker17/docs/nfdr.md`, at version 24, follows ADR-0011 to ADR-0016. It names the tests behind deleting a task and a project, runs both test suites through uv, and states how a review meets the dependency checks. (`db16374d3`, `d459f69d9`, `66e29daa9`, `909fc536c`, `53ad18603`, `7ed698a82`, `f83e0f3f2`, `1f1ed6101`, `1d11b7047`, `4a646aaf0`, `04c348675`, `3553cf36d`)

### Removed

- **tools** — The `README.md` no longer has a Status section listing what the tracker does and the commit each thing came in with. In its place, it says each change is recorded in `CHANGELOG.md` and what is left to build is listed in `docs/what_left.md`. (`24df0bd54`)

### Fixed

- **tracker17** — A start on readable saved data whose path holds a byte that isn't text prints its ready line and serves. The line writes that byte as `\x` and its two hex digits. (`97783ee64`, `8a4a74dbf`)
- **tracker17** — Ctrl-C pressed after the ready line, before the tracker begins serving or while it closes down, stops the tracker quietly, as Ctrl-C does while it serves. (`5768d462e`, `75771f9f4`, `7b5b4622e`)
- **tracker17** — On the People page, the line shown after you set a name that holds `{` or `}` shows the name as you typed it, whether the name was saved or not. (`fe98ceeb3`, `5f7f950a6`)
