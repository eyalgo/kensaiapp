# Delegate report — the Playwright pin moves (2026-11-13)

## 1. Assignment

The owner ruled answer (a) to the architecture companion's § 3.1 (QC-40 browser exception, lapsed
2026-11-07). The job: pick the newest Playwright release whose Chromium build has no Critical advisory
more than 30 days old, move every pin to it, relock each, install and test, list the product-doc lines
the move makes stale, and commit on branch `2026-11-13_playwright-pin-moves`, not merging.
Writable: pins, locks, tests that pin the build, this report. Read-only: `products/tracker17/docs/`,
every `journey/` and `trail/`, version markers, other worktrees.
Model: Opus (claude-opus-5-5). The brief named the tier.

## 2. What was searched, and what it settled

| Source (read 2026-11-13 UTC, unless noted) | For | Settled |
|---|---|---|
| `products/tracker17/docs/nfdr.md:L450-L492` (QC-40), `:L1189-L1201` (RN-33) | the rule | the 30-day window counts from the day the advisory is published. A Critical advisory more than 30 days old blocks the review |
| companion § 3.1, in the other worktree, `products/tracker17/docs/architecture_open_issues.md:L31-L60` | the item | options (a)/(b)/(c). Read only |
| `products/tracker17/docs/trail/architecture/cycle-7.md:L49`, `self_answer-10.md:L60-L98` | how the last check was done | precedent: Chrome Releases "Critical" ratings, and comparing version numbers for a pre-stable build |
| `https://pypi.org/pypi/playwright/json` | releases | 1.64.0 (2026-10-13), 1.64.1 (2026-10-22), 1.65.0 (2026-11-09), 1.65.1 (2026-11-11). Latest 1.65.1. None yanked |
| macOS arm64 wheels for 1.63.0/1.64.1/1.65.0/1.65.1 from PyPI, `playwright/driver/package/browsers.json` | which build each installs | 1.63.0 installs 153.0.8010.12 (r1243). 1.64.1 installs 156.0.8078.4 (r1248). 1.65.0 and 1.65.1 install 158.0.8127.18 (r1254) |
| `gh api repos/microsoft/playwright-python/releases/tags/v1.64.1, v1.65.0, v1.65.1` | cross-check | release notes: "Chromium 156.0.8078.4" / "Chromium 158.0.8127.18" (x2) |
| `https://chromereleases.googleblog.com/search/label/Stable%20updates` (WebFetch) | advisories | dead end: the page renders by script, so no post bodies came back |
| `https://chromereleases.googleblog.com/feeds/posts/default/-/Stable%20updates?alt=json&max-results=40` | advisories | all 13 desktop stable posts from 2026-09-17 to 2026-11-11, with their versions and Critical CVEs (table in § 3) |
| NVD API `keywordSearch=Google Chrome prior to 158` / `prior to 159` / `prior to 157` | an advisory against 158 that Chrome Releases does not carry | 0 / 0 / 259 results. The Critical ones in the third set are those of the 2026-11-03 post |
| `gh api /advisories?ecosystem=pip&affects=playwright` | package advisories | none |
| `gh api /advisories?ecosystem=npm&affects=playwright` | package advisories | GHSA-7mvr-c777-76hp, rated high (not critical), 2025 |
| wheel METADATA, 1.63.0 against 1.65.1 | why the lock drops pyee | 1.63.0 needs `pyee<14,>=13` and greenlet. 1.65.1 needs only greenlet |
| `lib/coreBundle.js` in 1.63.0 (L34858) and 1.65.1 (L36583) | the conftest claim | `--disable-back-forward-cache` is still in chromiumSwitches |
| `git grep -n -i playwright -- ':!**/trail/**'` | pins | 3 manifests and 3 locks. The instance root's `pyproject.toml` has no playwright. `tests/e2e/test_moves.py:L515` pins the build string |

### Critical advisories (Chrome Releases desktop stable; window = published + 30 days, against 2026-11-13)

| Published | Fixed in | Critical CVEs | More than 30 days old on 2026-11-13? |
|---|---|---|---|
| 2026-09-17 | 153.0.8010.52 | 2 | yes |
| 2026-09-22 | 154.0.8037.57 | 11 | yes |
| 2026-09-29 | 154.0.8037.92 | 1 | yes |
| 2026-10-01 | 154.0.8037.97 | 1 | yes |
| 2026-10-06 | 155.0.8059.39 | 4 | yes |
| 2026-10-13 | 155.0.8059.79 | 7 | yes (31 days) |
| 2026-10-15 | 155.0.8059.84 | 1 | no (29 days) |
| 2026-10-20 | 156.0.8078.47 | 7 | no |
| 2026-10-27 | 156.0.8078.73 | 4 | no |
| 2026-10-29 | 156.0.8078.79 | 1 | no |
| 2026-11-03 | 157.0.8103.38 | 7 | no |
| 2026-11-09 | 157.0.8103.50 | 0 | no |
| 2026-11-11 | 157.0.8103.78 | 5 | no |

Verdict per release:
- **1.65.1 / 1.65.0 (158.0.8127.18):** the build's version is above every fixed version. It passes.
- **1.64.1 (156.0.8078.4):** by version it is above every fix more than 30 days old, so it passes today. But it is below 156.0.8078.47/.73/.79, so the 12 Critical CVEs of 2026-10-20 to 2026-10-29 are against it. They pass 30 days from 2026-11-20 on.
- **Chosen: 1.65.1**, the newest release that passes.

## 3. Claims and anchors

| Claim | Anchor | Brief |
|---|---|---|
| PyPI lists 1.64.1, 1.65.0, 1.65.1 | PyPI JSON above | confirmed, and PyPI also lists 1.64.0 |
| old build is 153.0.8010.12 | 1.63.0 wheel `browsers.json` | confirmed |
| known pins | `core/templates/behave-starter/pyproject.toml:L8`, `products/tracker17/.behave/pyproject.toml:L8`, `products/tracker17/pyproject.toml:L17` + 3 locks | confirmed. The root `pyproject.toml` pins only pytest and pytest-xdist |
| a test pins the build | `products/tracker17/tests/e2e/test_moves.py:L515`, imported by `test_delete_project.py:L19` and `test_delete_task.py:L20` | it did. Moved to 158.0.8127.18 |
| conftest comment named 1.63.0 | `products/tracker17/tests/e2e/conftest.py:L140` | now 1.65.1. The switch is checked in the driver |
| starter copy is byte-identical | `diff -r core/templates/behave-starter products/tracker17/.behave`, before and after: no output | confirmed |
| `uv lock` (uv 0.11.14), each folder | output: "Updated playwright v1.63.0 -> v1.65.1", "Removed pyee v13.0.1" (x3) | the lock moves a second package (§ 6) |
| installed browser | `uv run --locked --project products/tracker17 playwright install chromium` exit 0. Then `chromium.launch().version` printed headless `158.0.8127.18`, and `channel='chromium'` printed full `158.0.8127.18` | — |
| full suite | `uv run --locked --project products/tracker17 pytest products/tracker17/tests/ -q` gave `3272 passed, 2 skipped, 6 warnings in 409.42s (0:06:49)` | — |
| e2e suite | `uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/ -q -p no:warnings` gave `122 passed in 237.87s (0:03:57)`. I added `-p no:warnings` to shorten output, and it does not change the count | — |
| Behave | in `products/tracker17/.behave`: `uv run --locked behave` gave `3 features passed, 0 failed, 0 skipped` / `3 scenarios passed, 0 failed, 0 skipped` / `11 steps passed, 0 failed, 0 skipped`, exit 0 | — |
| core tools | `uv run --locked pytest core/tools/test_behave_starter.py core/tools/test_install_behave_starter.py core/tools/test_start_checks.py -q` gave `216 passed in 51.77s` | — |
| nothing broke | every run is green. Nothing needed fixing beyond the pin string. Main was not measured as a baseline, because nothing failed | — |

The warnings are pytest `rm_rf` cleanup errors in the system temp folder, not test failures.

### Lines under `products/tracker17/docs/` naming `1.63.0` or `153.0.8010.12` (trail excluded; `git grep -n -E "1\.63\.0|153\.0\.8010\.12"`), 34 lines

| path:line | text |
|---|---|
| `products/tracker17/docs/SDD.md:383` | library does. For the pin in `pyproject.toml`, `playwright==1.63.0`, that library's documentation |
| `products/tracker17/docs/SDD.md:1602` | playwright 1.63.0 and Chromium 153.0.8010.12 (`pytest tests/e2e/`, 18 passed; |
| `products/tracker17/docs/SDD.md:1614` | library, `playwright==1.63.0` (`pyproject.toml`). The browser build is asserted by the run and |
| `products/tracker17/docs/SDD.md:1616` | asserts `browser.version` equals `PINNED_BROWSER`, `153.0.8010.12`, on the full Chromium of that |
| `products/tracker17/docs/SDD.md:2605` | `test_moves.py` asserts `browser.version == PINNED_BROWSER`, `153.0.8010.12`, inside |
| `products/tracker17/docs/SDD.md:2607` | focus tests' headless shell comes from, both from `playwright==1.63.0`, and R-2 says exactly |
| `products/tracker17/docs/SDD.md:2940` | resolved 17 packages, `uv.lock` names `mypy` 2.4.0, `playwright` 1.63.0, `pytest` 9.1.1 and |
| `products/tracker17/docs/SDD.md:3008` | `Version 1.63.0`; `uv run pytest tests/unit tests/architecture`, 670 passed in 4.72 s; `uv run |
| `products/tracker17/docs/SDD.md:3386` | declares `behave==1.3.3`, `httpx==0.28.1` and `playwright==1.63.0` and nothing else; `.behave/uv.lock` |
| `products/tracker17/docs/adr/0010-pending-confirmation-answered-202-move-pages-not-stored.md:72` | the build the pinned library installs, Chromium 153.0.8010.12 under `playwright==1.63.0`, and not |
| `products/tracker17/docs/adr/0012-pending-confirmation-answered-202-confirmed-action-pages-not-stored.md:106` | installs, Chromium 153.0.8010.12 under `playwright==1.63.0`, and not the operator's current stable |
| `products/tracker17/docs/adr/0015-pending-confirmation-answered-202-while-data-is-served-confirmed-action-pages-not-stored.md:117` | installs, Chromium 153.0.8010.12 under `playwright==1.63.0`, and not the operator's current stable |
| `products/tracker17/docs/nfdr.md:147` | instead of loaded. Layer 5 proves the build the pinned library installs, Chromium 153.0.8010.12 |
| `products/tracker17/docs/nfdr.md:148` | under `playwright==1.63.0`, and not the operator's current stable Chrome. **The unreadable-data |
| `products/tracker17/docs/nfdr.md:421` | and `playwright==1.63.0`, are declared in `.behave/pyproject.toml` and fixed by `.behave/uv.lock`, |
| `products/tracker17/docs/nfdr.md:457` | of the day the advisory is published**. Today both sets pin `playwright==1.63.0`, so that is one |
| `products/tracker17/docs/nfdr.md:458` | build, Chromium 153.0.8010.12. A fix moves the pin; where none comes within the window, the |
| `products/tracker17/docs/nfdr.md:704` | it runs where the pinned browser-driving library does — for `playwright==1.63.0`, the Debian and |
| `products/tracker17/docs/nfdr.md:923` | (`pytest products/tracker17/tests/e2e/`, 18 passed), with playwright 1.63.0 and Chromium |
| `products/tracker17/docs/nfdr.md:924` | 153.0.8010.12 (SDD § 11 R-2, RN-41). The second is the added comment, given `tabindex="-1" |
| `products/tracker17/docs/nfdr.md:928` | at `<a commit not in the public history>` with playwright 1.63.0, and 33 passed at `<a commit not in the public history>`, whose product code and tests |
| `products/tracker17/docs/nfdr.md:929` | match `<a commit not in the public history>`, with playwright 1.63.0 and Chromium 153.0.8010.12. The confirmation of SDD § 4 |
| `products/tracker17/docs/nfdr.md:936` | clone at `<a commit not in the public history>` (`tests/e2e/`, 67 passed), with the pinned library, `playwright==1.63.0`. That |
| `products/tracker17/docs/nfdr.md:938` | `test_history_matrix_revalidates_current_saved_status` asserts `153.0.8010.12` on the full Chromium |
| `products/tracker17/docs/nfdr.md:1175` | `playwright==1.63.0` was chosen on 2026-10-07, when no Playwright release on PyPI installed a fixed |
| `products/tracker17/docs/nfdr.md:1183` | for the browser build `playwright==1.63.0` installs, has no answer, so it stays in the companion |
| `products/tracker17/docs/nfdr.md:1190` | Chromium build `playwright==1.63.0` installs, `153.0.8010.12`, stays past QC-40's 30-day window for |
| `products/tracker17/docs/nfdr.md:1199` | still 1.63.0, uploaded 2026-09-15 (`https://pypi.org/pypi/playwright/json`, read 2026-10-10), and |
| `products/tracker17/docs/nfdr.md:1226` | `playwright==1.63.0`. `git diff --stat <a commit not in the public history> HEAD -- products/tracker17 |
| `products/tracker17/docs/nfdr.md:1428` | as R-2 does: the run pinned `playwright==1.63.0`, and asserted `153.0.8010.12` on the full Chromium |
| `products/tracker17/docs/nfdr.md:1437` | `tests/e2e/conftest.py`, `playwright==1.63.0` in `pyproject.toml` and `tests/requirements.txt`, and |
| `products/tracker17/docs/nfdr.md:1882` | `.behave/pyproject.toml` declares `behave==1.3.3`, `httpx==0.28.1` and `playwright==1.63.0` and |
| `products/tracker17/docs/nfdr.md:1890` | browser clause reads "each" because both sets pin `playwright==1.63.0`, which installs Chromium |
| `products/tracker17/docs/nfdr.md:1891` | 153.0.8010.12 (the `browserVersion` in the installed library's `browsers.json`), so today the two |

Related, outside the docs (not edited):
- `system/upkeep.md:L10`: the row "end the browser exception by moving the `playwright==1.63.0` pin". Its action is now done, and closing the row is the upkeep owner's.
- `SDD.md:L383` and `nfdr.md:L704` derive supported platforms from "the pinned library's documentation" for 1.63.0. Whether 1.65.1 supports the same platforms was not checked.
- `SDD.md:L2940` records "resolved 17 packages" at `e38121b11`. That figure is dated and still true for that commit. tracker17's lock now resolves 16, and `.behave` resolves 17 (18 before), because pyee is gone.

## 4. Decisions

| Fork | Chosen | Rejected, and why |
|---|---|---|
| release | 1.65.1 | 1.65.0 installs the same build but is older. 1.64.1 passes today but has 12 Critical CVEs that cross 30 days from 2026-11-20 |
| meaning of "critical" | Chromium's own severity in Chrome Releases, as cycle-7 did | NVD CVSS. Not used, because the precedent used the vendor's rating |
| how to judge a pre-stable build | compare version numbers (the self_answer-10 L97 precedent). 158 is above every published fix | — |
| pyee removed from the locks | accepted, because playwright 1.65.1 no longer declares it and no pin names it | pinning pyee back. Rejected: that would add a dependency |
| changelog | one tracker17 `### Upgrading` entry, in its own commit (precedent `5cead9697`), citing the pin commit. A merge into main refuses a branch with no `[Unreleased]` entry (`core/tools/CHANGELOG.md`, the builder-merge entry) | a `core/tools/CHANGELOG.md` entry for the starter. Not added: `core/templates/` is neither `core/tools/` nor a root file (`kensaiapp_structure.md` § The changelog) |

## 5. Problems hit

- The Chrome Releases HTML page returned no post bodies through WebFetch. The Blogger JSON feed worked in its place.
- The brief named three releases. PyPI also holds 1.64.0, which is older and was not assessed.
- The brief did not mention the changelog obligation. I found it in the structure map and the merge guard.
- The main checkout's browser cache held no `chromium-1243`, so the old build was not installed on this machine. That did not matter, because no baseline run was needed.

## 6. Surfaced, not settled

1. **The lock drops pyee 13.0.1** in all three locks. The brief said "change no other dependency". This is a transitive removal that playwright makes itself. Recommendation: accept it.
2. **The docs lines above** (34), and QC-40 L457-L458 and RN-33 in particular, for the product-architecture and product-sdd runs. Companion § 3.1 now closes as (a), with the build 158.0.8127.18.
3. **The `system/upkeep.md:L10` row** is now done. Retiring it is not this run's job.
4. **Platform support** of 1.65.1 compared with what `nfdr.md:L704` states for 1.63.0 was not verified.
5. **The 158 build is pre-stable.** Chrome Releases rates no advisories against it yet. The next review checks it afresh, as QC-40 requires.

## 7. Commits

| SHA | Covers |
|---|---|
| `c39e74abe` | pin move: 3 pyproject, 3 uv.lock, test_moves.py PINNED_BROWSER, conftest comment |
| `0bda6a502` | tracker17 CHANGELOG Upgrading entry |
| (this commit) | this report |
