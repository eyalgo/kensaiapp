# tracker17

This is tracker17, a small task tracker you run on your own machine and use in your browser, built entirely by kensaiapp. It exists so someone curious about kensaiapp can read and run a whole product kensaiapp built. They can also judge what it takes to set up. It is also kensaiapp's own testing ground: building tracker17 is how problems in kensaiapp are found and fixed.

It is published before it is done, so each release shows how far its development has come. The record of how each change was made ships with it, in `system/projects/tracker17`.

## Status

You can start the tracker with `python3 main.py`. You can create projects in your browser. Your projects are still listed after the tracker stops and starts again. You can open the tracker from a fresh copy in 2 commands. The setup instructions say where the saved data is kept. The setup instructions say how to set saved data aside. The setup instructions say what to do when your browser can't reach the tracker. You can add names to the assignee list and remove them on the People page. The first paragraph you read says the tracker is also kensaiapp's own testing ground. You can add a task to a project. You can give a task a priority of low, medium, high or critical, and a task added without one gets medium. You can assign a task to a name on the assignee list when you add it. You can give a task a due date when you add it, and the project's task list marks an open task past its due date Overdue. A project with no tasks invites you to add its first task. You can edit a task's title, priority, assignee and due date on its page. You can add labels to a task and remove them one at a time. You can set your name on the People page. You can add a comment to a task under your name, and each comment shows the time it was written. You can move a task along the status workflow, and the tracker refuses a move the workflow doesn't allow. A task's row and page offer only the moves its status allows, and a task in `done` or `cancelled` offers none. You are asked to confirm a move to `cancelled` before it happens, and you can back out of it. You can filter a project's task list by status, priority, assignee, label, due-date range or overdue. A filter that matches nothing says so. You can sort a project's task list by due date, priority, created time or title, in either direction. You can filter a task list across all projects by status, priority, assignee, label, due-date range or overdue. You can open a project's Summary to see its task counts by status and by priority, its overdue count, its count of tasks with no due date and each assignee's open tasks. From the Summary, you can open a project's task list filtered by any one status or priority, or by overdue, by selecting that count. You can delete a task from its page after you confirm. You can rename a project. You can delete a project and all of its tasks after you confirm.

Nothing that the tracker was defined to do is left to build.

## Setup instructions

These are tracker17's setup instructions. Read them in order, and type each command in a terminal exactly as shown.

### What you need

The tracker needs Python 3.11 or later. To see which version you have, type this command.

```
python3 --version
```

If it shows a version lower than 3.11, or the terminal can't find `python3`, install Python 3.11 or later. Get it from https://www.python.org/downloads/. Then type the command again.

The tracker runs on macOS and Linux. It has been checked on macOS only. Windows isn't supported.

The tracker needs no network connection to set up or run. Setting up the tests needs one, once, to fetch their dependencies and the browser the end-to-end tests drive.

### From a fresh copy to the tracker in your browser

Open a terminal at the top of your copy, the directory that holds `products`. Then type these commands.

```
cd products/tracker17
python3 main.py
```

The first command moves into `products/tracker17`, the tracker's directory, and the second starts the tracker. Neither command installs anything or needs a network connection.

### What the start prints

When the tracker is ready, the terminal shows one line like this one.

```
The tracker is running. Open http://127.0.0.1:8017 in your browser. Saved data is kept at /Users/sam/copy/products/tracker17/data.
```

That line means the tracker is running. With that line, open http://127.0.0.1:8017 in your browser to see the Projects page. Your own copy's location appears in place of `/Users/sam/copy/products/tracker17/data`.

When the tracker starts on saved data it can't read, the line starts with `The tracker couldn't read` instead. The tracker is still running when that line shows. To start fresh on purpose, follow Setting saved data aside in these setup instructions.

After either `The tracker is running` or `The tracker couldn't read`, the tracker keeps running until you stop it. To stop it, press Ctrl-C in its terminal.

A line that starts with `The tracker didn't start` means this start has stopped. The line says why and what to do next.

### Where the saved data is kept

The tracker keeps its saved data in `data/`, inside `products/tracker17`, the directory that holds `main.py`. It's the same directory whichever directory you start the tracker from, and the start prints its full location.

Git ignores `data/`, so the saved data isn't committed with your changes. For the same reason, a clean that removes ignored files deletes the saved data. Both `git clean -dX` and `git clean -dx` delete it.

### Starting the tracker again

If your browser says it can't reach http://127.0.0.1:8017, the tracker isn't running. To start it again, open a new terminal at the top of your copy and type these commands.

```
cd products/tracker17
python3 main.py
```

The tracker reads its saved data as it starts. If it can read the data, every project you created before it stopped is still listed.

If it can't read the data, the tracker starts anyway. It shows this one line in its terminal.

```
The tracker couldn't read its saved data at /Users/sam/copy/products/tracker17/data, and nothing in it was changed. Open http://127.0.0.1:8017 in your browser to read this on a page. To start fresh on purpose, follow Setting saved data aside in the setup instructions.
```

Your own copy's location appears in place of `/Users/sam/copy/products/tracker17/data`. In your browser, every address shows one page that says the same thing. The page has no links and no controls. The start and the page change nothing in the saved data. The tracker keeps showing the page until you stop it, even if you repair the saved data.

If another tracker is already running on the same saved data, a second start is refused. It shows this one line in its terminal and exits.

```
The tracker didn't start, because another tracker is already running on the same saved data. Stop that one first, then start this one.
```

The first tracker carries on, and the refused start changes nothing in the saved data. To stop the first tracker, press Ctrl-C in its terminal.

A tracker that was killed doesn't prevent the next start. There's nothing to do first. In a terminal at the top of your copy, type the same commands, `cd products/tracker17` and `python3 main.py`. The tracker reads its saved data as the killed tracker left it.

### Setting saved data aside

Setting saved data aside moves it out of the tracker's reach and deletes nothing, so the next start is empty. Do it to start fresh, or when the tracker couldn't read its saved data.

Stop the tracker first if it's running, by pressing Ctrl-C in its terminal. Then open a terminal at the top of your copy and type these commands.

```
cd products/tracker17
mkdir -p ~/tracker17-set-aside
mv data ~/tracker17-set-aside/$(date +%Y-%m-%d-%H%M%S)
```

Your saved data is in a new directory inside `tracker17-set-aside`, in your home directory. The new directory is named for the date and time you set the data aside, such as `2026-10-08-143205`. To list everything you've set aside, type `ls ~/tracker17-set-aside`.

If `mv` says there's no such file or directory, or the new directory is empty, there was no saved data.

Start the tracker again with `python3 main.py`. It starts empty, with no projects.

### Running the tests

The tests need uv, which the tracker itself doesn't. Install uv first. Get it from https://docs.astral.sh/uv/getting-started/installation/. Setting up the tests needs a network connection, for `uv sync --locked` and `uv run playwright install chromium` only. Open a terminal at the top of your copy and type these commands.

On Linux, where the commands say `uv run playwright install chromium`, type `uv run playwright install --with-deps chromium` instead. That command also installs the system libraries the browser needs, using the operating system's package manager. It asks for administrator rights. The tracker and `uv run pytest tests/` need none of what it installs. On Linux, the end-to-end tests need Debian 12 or 13, or Ubuntu 22.04, 24.04 or 26.04, on x86-64 or arm64.

```
cd products/tracker17
uv sync --locked
uv run playwright install chromium
uv run pytest tests/
uv run pytest tests/e2e/
```

`uv sync --locked` makes the tests' virtual environment and installs the test dependencies into it. Every test command is then typed through `uv run`, which runs it in that virtual environment. `uv run pytest tests/` runs every test except the end-to-end ones. `uv run pytest tests/e2e/` runs the end-to-end tests, which drive Chromium.

Keep the virtual environment in `.venv`, inside `products/tracker17`, where `uv sync --locked` makes it. The tests read the Python in `products/tracker17` as the tracker's own, except in directories whose names start with a dot. A virtual environment anywhere else inside `products/tracker17` stops them passing.

In a new terminal, run the tests again inside `products/tracker17` with `uv run pytest tests/` or `uv run pytest tests/e2e/`. They use the virtual environment `uv sync --locked` already made.

For every test to pass, your copy needs to be a Git repository, with `git` on the path. If either is missing, as in a copy unpacked from a download, 1 test doesn't pass. That test checks that Git ignores the saved data. The tracker itself needs neither a Git repository nor `git`.

## Where it came from

kensaiapp built tracker17, and wrote much of its definition too. It began as tracker16-X, a small command-line tracker made as a proof of concept. Once kensaiapp was mature enough, its author moved the tracker to the browser. kensaiapp has gone on building it since. kensaiapp itself was built by working on tracker17 and the versions before it. Each problem that work turns up is fixed in kensaiapp.

## How it's built

- **Python 3.11 or later, and nothing outside its standard library.** There's no web framework and no
  template engine, and the tracker needs no network connection to run
  ([ADR-0013](docs/adr/0013-standard-library-only-no-web-framework-suite-environment-made-by-uv.md)).
- **macOS and Linux.** Windows isn't supported
  ([ADR-0009](docs/adr/0009-one-unix-lock-no-windows.md)).
- **Whole pages, built on the server.** No page runs a script
  ([ADR-0001](docs/adr/0001-rule-core-behind-server-rendered-pages.md),
  [ADR-0003](docs/adr/0003-no-script-in-any-page.md)).
- **Five parts, all at the product root** (`docs/SDD.md` § 3):
  - `domain/` holds every task rule, and touches no file, clock or network.
  - `application/` holds the actions you take, and applies a `domain` rule for each one.
  - `persistence/` reads and writes the saved data, one file in `data/`.
  - `web/` listens on your own machine's address and builds every page.
  - `main.py` wires the four together, and is the start command.
- **Tests in pytest**, at three layers: unit, integration and end-to-end. The end-to-end tests drive
  Chromium. Only the tests have dependencies, each fixed to an exact version, installed into a
  virtual environment made by uv (`docs/SDD.md` § 4 RT-4, TS-1).

## The documents

Every decision tracker17 is built against is in `docs/`:

- `docs/PRD.md` — what tracker17 is, who it's for, and what counts as done.
- `docs/SRS.md` — the requirements and their acceptance criteria.
- `docs/UXD.md`, `docs/DESIGN.md` and `docs/CONTENT.md` — the experience, the look and the words.
- `docs/SDD.md` — the parts, and the slices the work is cut into.
- `docs/fdr.md` — the behaviour every change is built against.
- `docs/nfdr.md` — the quality constraints, and the check behind each one.
- `docs/adr/` — the architecture decisions, indexed in `docs/adr/README.md`.
