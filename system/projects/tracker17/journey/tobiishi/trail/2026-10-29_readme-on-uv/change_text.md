# Change Text — the README sets up the test suite with uv

**Date:** 2026-10-29
**Category:** nfdr
**Behaviour:** changing

---

## Text

Every string below is the README's own Markdown source, exact in its characters, backticks included.
A one-line string is quoted after `>`. A string that spans lines, or holds a command block, is given
inside a four-backtick fence, and its lines are the README's lines. The strings in each place are
listed in the order the reader meets them, and a place's text not listed here stays as it is.

### The README's Running the tests section

The section, from just under its heading down to the heading `## Where it came from`, holds these
six paragraphs and one command block, in this order, and nothing else. The heading
`### Running the tests` itself stays as it is.

**1. The opening paragraph, directly under the heading**

> The tests need uv, which the tracker itself doesn't. Install uv first. Get it from https://docs.astral.sh/uv/getting-started/installation/. Setting up the tests needs a network connection, for `uv sync --locked` and `uv run playwright install chromium` only. Open a terminal at the top of your copy and type these commands.

When the person sees it: they want to run the suite, and they learn the one thing to install first, where the network is needed, and where to open the terminal.

**2. The Linux paragraph, after the opening paragraph and before the command block**

> On Linux, where the commands say `uv run playwright install chromium`, type `uv run playwright install --with-deps chromium` instead. That command also installs the system libraries the browser needs, using the operating system's package manager. It asks for administrator rights. The tracker and `uv run pytest tests/` need none of what it installs. On Linux, the end-to-end tests need Debian 12 or 13, or Ubuntu 22.04, 24.04 or 26.04, on x86-64 or arm64.

When the person sees it: a Linux reader learns which one command to type differently, what it does to their machine, and which systems the end-to-end tests run on.

**3. The command block**

````
```
cd products/tracker17
uv sync --locked
uv run playwright install chromium
uv run pytest tests/
uv run pytest tests/e2e/
```
````

When the person sees it: they type the five lines in order from the top of their copy.

**4. The paragraph on what the commands do, directly after the command block**

> `uv sync --locked` makes the tests' virtual environment and installs the test dependencies into it. Every test command is then typed through `uv run`, which runs it in that virtual environment. `uv run pytest tests/` runs every test except the end-to-end ones. `uv run pytest tests/e2e/` runs the end-to-end tests, which drive Chromium.

When the person sees it: they have the block in front of them and learn what each kind of line does, and which test command leaves out the browser.

**5. The paragraph on where the virtual environment is kept**

> Keep the virtual environment in `.venv`, inside `products/tracker17`, where `uv sync --locked` makes it. The tests read the Python in `products/tracker17` as the tracker's own, except in directories whose names start with a dot. A virtual environment anywhere else inside `products/tracker17` stops them passing.

When the person sees it: they learn where the environment lives and why moving it, or making another one in the tracker's directory, breaks the tests.

**6. The paragraph on running the tests again in a new terminal**

> In a new terminal, run the tests again inside `products/tracker17` with `uv run pytest tests/` or `uv run pytest tests/e2e/`. They use the virtual environment `uv sync --locked` already made.

When the person sees it: they've set the tests up once, opened another terminal, and learn they can type the test commands again straight away.

**7. The paragraph on the Git repository, last in the section**

Unchanged. The paragraph that begins `For every test to pass, your copy needs to be a Git repository`
stays as it is today, byte for byte, as the section's last paragraph.

### How it's built bullets

**The first bullet, Python and its standard library**

Only its link changes, in visible text and in target. The bullet reads:

````
- **Python 3.11 or later, and nothing outside its standard library.** There's no web framework and no
  template engine, and the tracker needs no network connection to run
  ([ADR-0013](docs/adr/0013-standard-library-only-no-web-framework-suite-environment-made-by-uv.md)).
````

When the person sees it: they read why the tracker has no dependencies, and the link opens the architecture decision that holds that choice today.

**The test bullet, the last in the list**

````
- **Tests in pytest**, at three layers: unit, integration and end-to-end. The end-to-end tests drive
  Chromium. Only the tests have dependencies, each fixed to an exact version, installed into a
  virtual environment made by uv (`docs/SDD.md` § 4 RT-4, TS-1).
````

When the person sees it: they read how the suite is built, and that its environment comes from the same tool the Running the tests section tells them to install.

### The documents list

**The line for the architecture decisions, last in the list**

> - `docs/adr/` — the architecture decisions, indexed in `docs/adr/README.md`.

When the person sees it: they learn where the architecture decisions are and which file lists them, with no count that a new decision would make wrong.

---

## Wording decisions

- **The opening paragraph says the tracker itself doesn't need uv.** The request asks only that uv be installed first. `### What you need` names no uv, so a reader who skipped to this section could take uv for a prerequisite of the tracker. SDD § 4 RT-4 states it is "a prerequisite of the suite and not of the tracker", so the sentence claims nothing the records don't hold.
- **"Get it from https://docs.astral.sh/uv/getting-started/installation/." copies the form of the README's own Python sentence**, "Get it from https://www.python.org/downloads/." in `### What you need`. One way of pointing at a tool's own page is kept in the setup instructions. The page is named, and the installer command is left with uv (CP-668, and the spec's Out of Scope).
- **The network sentence names its two commands in place of "the install commands".** The new block has one line with the word install in it, so "the install commands" would read as that line alone and leave `uv sync --locked`, which fetches the dependencies, unnamed. The sentence keeps "only", so the network is still needed only for setting up (CP-675).
- **The opening paragraph's last sentence, "Open a terminal at the top of your copy and type these commands.", is kept word for word.** The block's first line moves into `products/tracker17` from there (CP-669).
- **One term, "virtual environment", in the section and in How it's built.** The old section used it, the SDD uses it for `.venv` (§ 4 RT-4, "makes the virtual environment at `.venv`"), and the sentence that stays word for word, "A virtual environment anywhere else inside `products/tracker17` stops them passing.", needs it. That sentence is about any virtual environment a reader makes, and "environment" alone would not say so.
- **The two sentences on `pytest tests/` and `pytest tests/e2e/` move into paragraph 4 with their `uv run` forms.** They follow the sentence that says every test command is typed through `uv run`, so the reader meets the rule and then its two cases. No bare `pytest` command is left in the section (CP-672).
- **The new-terminal paragraph names the two test commands whole and says what they use.** The request says to reword it with no activation step. Saying there is nothing to do first, in any wording that holds the word for it, fails the README's own check (CP-680). The second sentence says the smaller true thing instead: the commands use the virtual environment `uv sync --locked` made. It names no step before them (CP-674). Its first sentence is held to 20 words, the standard's limit (`docs/CONTENT.md` § Grammar and mechanics, Sentence length).
- **The Linux paragraph changes only its three commands, to their `uv run` forms.** Every other statement in it is kept word for word (CP-671).
- **The paragraphs keep their old order.** The Linux paragraph stays before the block, as it is today, so a Linux reader meets the one command to type differently before typing it.
- **No sentence starts with uv.** A sentence that starts with a lowercase tool name reads as a broken capital, and writing it "Uv" breaks the rule that a tool's name is written as its owner writes it (`docs/CONTENT.md` § Grammar and mechanics, Abbreviations). Each sentence is ordered so the name falls inside it, and a command in backticks may start one, as the README's `pytest tests/` sentence does today. The standard states no such rule, so it is a finding below.
- **"made by uv" in the test bullet, where the old bullet said "made with Python's `venv`".** uv makes the environment and fills it (SDD § 4 RT-4, "made and filled by uv"), and "by" names the tool as the one that makes it, as the request asks.
- **The ADR link's visible text is "ADR-0013", as the other links in the list name their records.**
- **The documents line states no count.** The design takes the spec's no-count form (`change_design.md`, Architect Review Notes, "Decision count"). The index stays the one owner of the count, so a new record can't make the README wrong.
- **The changed lines in How it's built and The documents keep their lists' own forms**: the citation in parentheses on both bullets, and the dash between the path and its description on the documents line. Every sibling line in those two lists is written that way, and both lists are outside the spec's edit except for these lines. Whether the standard's punctuation bans reach those two sections is a finding below.
- **Banned-word check.** Every string was checked against the banned table in `docs/CONTENT.md` § Terminology, every inflection included, and none holds a banned word. The strings were also checked against the README's own fixed-string grep (CP-680), and none matches. The product carries no check of its own that reads its vocabulary: the two tests that name a banned list read imports, not words.

---

## Findings for the Content Manager

- **The changed lines in How it's built and The documents** — the standard doesn't say whether § Grammar and mechanics governs the README's sections outside `## Setup instructions`. § Terminology calls the whole document "setup instructions", and § Scope says the language governs "the written setup instructions". Read that way, its bans on the em dash and on parentheses outside "(unassigned)", and its rule that a colon appears only in a page title, a time, an address or a path, reach every line of How it's built and The documents, and every line there breaks one of them today. Meanwhile, the changed lines keep the form their lists already use, so each list reads as one.
- **Paragraphs 1, 4 and 6 of the Running the tests section, and the test bullet** — the standard doesn't say how a tool name whose owner writes it in lower case is placed at the start of a sentence. § Grammar and mechanics fixes this only for `tracker17` ("never starts a sentence"). Meanwhile, no sentence starts with uv, and a command in backticks may start one.
