# Behave starter

This folder, `.behave`, holds a product's behaviour scenarios and everything they need to run.
Behave runs scenarios whose steps are plain sentences, and it matches each step to a step definition
written in Python. The folder carries its own Python setup, so the scenarios run the same way in
every product, whatever language the product is written in. A run leaves the product's own
`pyproject.toml` and `uv.lock`, where the product has them, as they were.

## Run the scenarios

Run this command from inside this folder:

```
uv run --locked behave
```

The command needs `uv` on the machine. Its first run builds this folder's own environment from
`uv.lock`, and later runs reuse it. `--locked` makes `uv` stop with an error when `uv.lock` does not
match `pyproject.toml`, so every machine runs the same versions. The command exits 0 when every
scenario passes. When a step fails, the command exits non-zero, and Behave's report shows that
scenario as failed.

What a run creates, the environment and Python's caches, is ignored by this folder's own
`.gitignore`, so a run leaves `git status` as it was.

## Install the browser once

The browser way in drives Chromium through Playwright, and `uv.lock` does not carry the browser
itself. Run `uv run --locked playwright install chromium` once on each machine, from inside this
folder. Until it has run, the browser scenario fails.

Chromium and Playwright's driver also load system libraries that a bare Linux machine may lack. The
browser scenario then fails saying so. Run `uv run --locked playwright install-deps chromium` once on
that machine, as root, from inside this folder.

## The three ways in

A scenario's steps reach a product through one of three ways in. Each is a Python file of its own
under `features/`:

- **A command** — `features/command_way_in.py` runs a program and gives the step its exit status and
  its output. It uses Python's standard library only.
- **A server** — `features/server_way_in.py` sends HTTP requests and gives the step the responses,
  through `httpx`.
- **A browser** — `features/browser_way_in.py` opens a page in headless Chromium and gives the step
  what the page shows, through Playwright for Python.

A product's scenarios use one of the three. The starter ships one scenario through each way in, in
`features/`. Each of those scenarios proves only that its way in works: it starts the program, the
server or the page it reaches itself, on this machine, and it tests nothing of a product.

## What you add

- New scenarios go in `features/`, in files ending `.feature`.
- Their step definitions go in `features/steps/`, as Python files. Behave loads every file there as
  step definitions.
- The product's own setup goes in `features/environment.py`, Behave's environment hook: the file
  whose code Behave runs before and after the scenarios.
