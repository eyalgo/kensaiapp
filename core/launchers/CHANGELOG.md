# Changelog — `core/launchers`

Each entry records a change to what a user of a fresh clone installs, runs, types or reads in `core/launchers/`. It names the project the change was made under and cites the commits that made it. The format follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Upgrading

- **launchers** — Type `core/launchers/change/launcher.sh` in place of `core/launchers/chain-development/launcher.sh`, and `core/launchers/walk/launcher.sh` in place of `core/launchers/chain-change/launcher.sh`. The two old folders are gone. (`8ec5d752c`, `eaea638ae`, `7ebc2d82c`)
- **launchers** — Type `core/launchers/product-docs/launcher.sh` in place of `core/launchers/chain-product/launcher.sh`, and `core/launchers/prd-and-dod/launcher.sh` in place of `core/launchers/chain-agari/launcher.sh`. The two old folders are gone. (`36fb2dd25`)
- **launchers** — Before you take the `change` and `walk` renames, let every walk end and remove the `chain-development-<project>-*` and `chain-change-<project>-*` files under `system/logs/`. The `change` launcher now keeps its records as `chain-change-<project>-*`, the name the `walk` launcher used before, and the `walk` launcher keeps its own as `chain-walk-<project>-*`. (`423e6aef6`, `7ebc2d82c`)
- **tools** — Install uv for any launcher under `core/launchers/` to run. A launch checks for uv at its entry, before it makes a pin or starts any Python. Without uv, it prints a message naming the launcher and exits 1. (`4e80b5534`, `70f7d75da`, `416487af6`)

### Changed

- **launchers** — The `walk` launcher's messages call its own walk `walk`, and name the `product-docs` or `prd-and-dod` walk that runs before it on a project with a definition. (`423e6aef6`, `36fb2dd25`, `333051e69`)
- **launchers** — The `walk` launcher reads `full`, `prd-and-dod` or `none` from a card's `**Definition:**` line, and prints `definition=prd-and-dod` for the PRD-and-Agari walk. A card reading `prd-agari` is refused. (`dc70038d1`)

### Fixed

- **tools** — The `walk` launcher writes its end hooks so that a core path holding a tab or a newline stays one word, and the next walk starts. (`7f3a3f7e0`)
