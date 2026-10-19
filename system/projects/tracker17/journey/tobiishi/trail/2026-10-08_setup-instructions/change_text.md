# Change Text — Setup instructions a reader follows alone, and the console pointing to them

**Date:** 2026-10-08
**Category:** feature
**Behaviour:** changing

---

## Text

These are the words this change publishes, in three places: the setup instructions, the status note
and opening paragraph above them, and the terminal line for saved data the start can't read. The
setup instructions and the status note are a Markdown document. Each of their strings is given as
the exact Markdown a person reads, inside a four-backtick fence. The fence is not part of the
string. Everything inside it is, including headings, blank lines and the three-backtick command
blocks.

**The order a person reads the document in, top to bottom:**

1. The title, `# tracker17`, unchanged.
2. The opening paragraph, from § *The status note above them*.
3. `## Status` and its text, from § *The status note above them*.
4. `## Setup instructions`, its opening, and its seven sections in the order given in
   § *The setup instructions*.
5. `## How it's built` and `## The documents`, each byte for byte as they stand today, headings
   included.

### The setup instructions

**The heading and opening a reader sent to "the setup instructions" lands on**

````markdown
## Setup instructions

These are tracker17's setup instructions. Read them in order, and type each command in a terminal exactly as shown.
````

When the person sees it: they have a fresh copy, or a terminal line that pointed them to the setup instructions. The opening tells them they're in the right document and how to use it.

**Section 1, the prerequisites, read before any command is typed**

````markdown
### What you need

The tracker needs Python 3.11 or later. To see which version you have, type this command.

```
python3 --version
```

If it shows a version lower than 3.11, or the terminal can't find `python3`, install Python 3.11 or later from https://www.python.org/downloads/. Then type the command again.

The tracker runs on macOS and Linux. It has been checked on macOS only. Windows isn't supported.

The tracker needs no network connection to set up or run. Setting up the tests needs one, once, to fetch their dependencies and the browser the end-to-end tests drive.
````

When the person sees it: they have nothing installed beyond what their machine came with. After this section they know whether their Python and their system will do, and what to install if the Python won't.

**Section 2, the commands from a fresh copy to the tracker in the browser**

````markdown
### From a fresh copy to the tracker in your browser

Open a terminal at the top of your copy, the directory that holds `products`. Then type these commands.

```
cd products/tracker17
python3 main.py
```

The first command moves into `products/tracker17`, the tracker's directory, and the second starts the tracker. Neither command installs anything or needs a network connection.
````

When the person sees it: their Python is 3.11 or later. With the version check in section 1, these are the third and last commands on the way to the Projects page.

**Section 3, what the start prints and the address to open**

````markdown
### What the start prints

When the tracker is ready, the terminal shows one line like this one.

```
The tracker is running. Open http://127.0.0.1:8017 in your browser. Saved data is kept at /Users/sam/copy/products/tracker17/data.
```

Your own copy's location appears in place of `/Users/sam/copy/products/tracker17/data`. Open http://127.0.0.1:8017 in your browser to see the Projects page. If the line starts with `The tracker didn't start` instead, it says why and what to do next.

The tracker keeps running in that terminal until you stop it. To stop it, press Ctrl-C in that terminal.
````

When the person sees it: they've just typed `python3 main.py` and are reading the line it printed. Next they open the address. Without this section they wouldn't know that the terminal must stay open, or how to stop the tracker.

**Section 4, where the saved data is kept**

````markdown
### Where the saved data is kept

The tracker keeps its saved data in `data/`, inside `products/tracker17`, the directory that holds `main.py`. It's the same directory whichever directory you start the tracker from, and the start prints its full location.

Git ignores `data/`, so the saved data isn't committed with your changes. For the same reason, a clean that removes ignored files deletes the saved data. Both `git clean -dX` and `git clean -dx` delete it.
````

When the person sees it: the tracker is running, or they're about to clean their copy. They learn where their work is, and that a clean of ignored files deletes it.

**Section 5, `Starting the tracker again`, reached after the tracker has stopped or from the browser's can't-reach page**

````markdown
### Starting the tracker again

If your browser says it can't reach http://127.0.0.1:8017, the tracker isn't running. To start it again, open a new terminal at the top of your copy and type these commands.

```
cd products/tracker17
python3 main.py
```

The tracker reads its saved data as it starts, so every project you created before it stopped is still listed.
````

When the person sees it: the tracker has stopped, by Ctrl-C, a closed terminal or a restart, and their browser can't reach the address. The section says what that means and gives the two commands that bring the tracker back with the same projects.

**Section 6, `Setting saved data aside`, reached to start fresh or from the terminal line for saved data the start can't read**

````markdown
### Setting saved data aside

Setting saved data aside moves it out of the tracker's reach and deletes nothing, so the next start is empty. Do it to start fresh, or when the tracker didn't start because it couldn't read its saved data.

Stop the tracker first if it's running, by pressing Ctrl-C in its terminal. Then open a terminal at the top of your copy and type these commands.

```
cd products/tracker17
mkdir -p ~/tracker17-set-aside
mv data ~/tracker17-set-aside/$(date +%Y-%m-%d-%H%M%S)
```

Your saved data is now in a new directory inside `tracker17-set-aside`, in your home directory. The new directory is named for the date and time you set the data aside, such as `2026-10-08-143205`. To list everything you've set aside, type `ls ~/tracker17-set-aside`.

If `mv` says there's no such file or directory instead, there was no saved data to set aside.

Start the tracker again with `python3 main.py`. It starts empty, with no projects.
````

When the person sees it: they want an empty tracker on purpose, or the start told them it couldn't read its saved data and sent them here by this section's name. They leave with an empty tracker, and their earlier saved data kept whole in a directory they can find.

**Section 7, running the tests**

````markdown
### Running the tests

The tests run in a virtual environment that holds their dependencies. Setting it up needs a network connection, for the install commands only. Open a terminal at the top of your copy and type these commands.

```
cd products/tracker17
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r tests/requirements.txt
python -m playwright install chromium
pytest tests/
pytest tests/e2e/
```

`pytest tests/` runs every test except the end-to-end ones. `pytest tests/e2e/` runs the end-to-end tests, which drive Chromium.

Keep the virtual environment in `.venv`, where the second command makes it. The tests read the Python in `products/tracker17` as the tracker's own, except in directories whose names start with a dot. A virtual environment anywhere else inside `products/tracker17` stops them passing.

In a new terminal, type `source .venv/bin/activate` inside `products/tracker17` before you run `pytest` again.

In a copy that isn't a Git repository, such as one unpacked from a download, one test doesn't pass. That test checks that Git ignores the saved data.
````

When the person sees it: the tracker runs, and they want to run its tests. They have a network connection for the installs. They leave with both suites run, and with what to type in a later terminal.

### The status note above them

**The opening paragraph, read first, before the status note**

````markdown
This is tracker17, a small task tracker you run on your own machine and use in your browser. It exists so someone curious about kensaiapp can read and run a whole product kensaiapp built. They can also judge what it takes to set up.
````

When the person sees it: they've just opened the document. They learn what tracker17 is and why it exists, before anything about its state.

**The status note**

````markdown
## Status

You can start the tracker with `python3 main.py` and create projects in your browser. Projects you create are still listed after you stop the tracker and start it again. The tracker holds projects and nothing else yet.
````

When the person sees it: they're deciding whether there's anything to run. They learn that there is, the one command that starts it, and that projects are all it holds.

### The terminal message a start shows when it can't read its saved data

**The start found saved data it couldn't read, stopped, and changed nothing**

> The tracker didn't start, because it couldn't read its saved data at {location}. Nothing in it was changed. See Setting saved data aside in the setup instructions.

`{location}` is the saved data's absolute location, as the start already shows it today, such as `/Users/sam/copy/products/tracker17/data`. It is the only variable part. The line is one line, and the closing sentence quotes section 6's heading exactly.

When the person sees it: they typed the start command and got this line instead of the ready line. They know where the data is and that it's untouched. The heading the line names is the section that gets them to an empty tracker without losing the data.

---

## Wording decisions

- **Each command block is introduced by a sentence ending in a full stop, never a colon.** The obvious form is "type these commands:", and CONTENT § Grammar and mechanics, "Banned punctuation", allows a colon only in a page title, inside a time, and inside an address or a path.
- **The instructions never say that nothing asks for an account, a key, a sign-up or a payment.** CP-56 forbids the instructions from asking for any of these. It doesn't require them to say so, and CONTENT § Terminology bans "account" in anything a person sees ("sign in, sign out, log in, account, profile, welcome", say instead "Nothing"). The rule is met by what the instructions don't contain.
- **The version check is in section 1 only, and section 2 has two commands.** Typing it again in section 2 would bring CP-57's count to four. Section 1's `python3 --version`, then `cd products/tracker17` and `python3 main.py`, make three, the same three the spec's Verified Claims ran.
- **"Directory", not "folder", for a place on disk.** CONTENT § Terminology lists "folder" among the rejected names for a project, so the word already carries a meaning in this product that a reader could misapply. "Directory" is also the word in the `mv` message section 6 tells the reader to watch for.
- **Saved data is set aside into `~/tracker17-set-aside/<date and time>`, outside the copy.** Several properties had to hold together. CP-61 requires that `git status` not list the set-aside data. A plain move inside the copy is listed (spec Verified Claims, `?? data-set-aside/tracker.json`). Outside the copy, the test suite doesn't read it (`change_design.md` § 4, Code Strategy), and section 4's clean doesn't delete it. The design's § 4 requires a second set-aside not to overwrite or merge into the first, so each set-aside gets its own directory named by the time to the second. Minute precision would let two set-asides in one minute land in one directory. I ran the three commands twice in a disposable `git archive` copy on 2026-10-08, with `HOME` pointed inside it. The first run moved `data` to its own directory with its `shasum` unchanged (`11a4124d…`). The second, after new saved data the start couldn't read, made a second directory and left the first untouched.
- **The directory-name example, `2026-10-08-143205`, carries seconds and no colon.** It is a name the `date` command writes, not a time the tracker writes as text, so CONTENT's `HH:MM` rule isn't applied to it. That reading is mine, and a finding below asks for the rule.
- **Section 6 adds a sentence for `mv` saying there's no such file or directory.** No upstream document gives this state words. It is the state of a reader who runs the section with no saved data, or runs it a second time before a new start. Nothing is moved and nothing is deleted. I ran it on GNU `mv` on 2026-10-08, which printed `mv: cannot stat 'data': No such file or directory`. macOS's `mv` wasn't run here. It reports the same system error text, so the sentence quotes only the shared words, "no such file or directory". The macOS check is the owner's run.
- **Section 5 says "If your browser says it can't reach", not "can't reach this page".** The spec quotes the Chrome and Edge page. Safari and Firefox word theirs differently. The smaller true thing covers every browser.
- **"Press Ctrl-C", where CP-58 says "Ctrl-C typed there".** CONTENT § Grammar and mechanics, "Verbs for pressing", fixes "pressed" for a button and "typed" for text, and says nothing about a key combination. A key is pressed, and "type Ctrl-C" would read as typing the letters. A finding below asks for the rule.
- **Section 3 adds one sentence for a start that prints `The tracker didn't start` instead of the ready line.** The spec's Out of Scope excludes listing the failure messages, and this sentence lists none. Without it, a reader whose start fails reads a section that describes only the ready line. Both failure lines the start prints give a reason and an action (CONTENT § Message patterns, Error, "Terminal messages", the address-taken example, and the spec's CP-65 line), so "it says why and what to do next" holds for each.
- **Section 7 states where the virtual environment must sit, and why.** This is the property in `change_design.md` § 4, Code Strategy. The suite reads no dot-named directory, so a `venv/` or `env/` in `products/tracker17` is read as a sixth part of the tracker. The commands make `.venv`. The added sentence keeps a reader who prefers another name from breaking the suite without seeing why.
- **Section 7 says one test doesn't pass in a copy that isn't a Git repository.** The spec's Verified Claims found one test, the one that checks version control ignores the saved data, not passing in a `git archive` copy, and Gap 11 left the test and the prerequisites alone. The sentence changes neither. It states the smaller true thing, so a reader who unpacked a download isn't left guessing at a failure that the section's own words would otherwise not explain.
- **Section 7 doesn't promise that both suites pass.** The end-to-end suite has been run on macOS only by the owner, and on Linux its browser couldn't start here (spec Verified Claims, `libglib-2.0.so.0`). The section says what each command runs and claims no result.
- **The ready line's example location is `/Users/sam/copy/products/tracker17/data`, not CONTENT's `/Users/sam/tracker17/data`.** CONTENT's examples illustrate. A reader of these instructions starts from the top of a copy that holds `products/tracker17`, so the location the start prints has that shape. The example then differs from what a reader sees only in the part before `products`, which is what CP-58 asks.
- **Sections 4 to 7 say "Git", not "version control".** The section names `git clean`, and CONTENT § Grammar and mechanics, "Abbreviations", lets the setup instructions name tools as their owners write them. One name for the tool reads as one thing.
- **The headings of sections 1 to 4 and 7 are "What you need", "From a fresh copy to the tracker in your browser", "What the start prints", "Where the saved data is kept" and "Running the tests".** CP-55 fixes only sections 5 and 6. Read in order with those two, the seven headings follow a reader from before the first command to the tests, in sentence case with no end punctuation (CONTENT § Grammar and mechanics, "Case" and "Sentence endings").
- **The seven sections sit under one `## Setup instructions` heading, whose first sentence names the document as tracker17's setup instructions.** CP-54 requires the instructions to name themselves, and CONTENT § Terminology makes "setup instructions" the term and rejects "README". The two fixed headings are level-three headings, which the design's CP-55 and CP-67 tests accept at any level.
- **The status note names only what the running tracker offers: starting it, creating projects, and projects that stay.** The running tracker offers the Projects page, a project's page and creating a project, which is what SDD § 6 S-1 delivers and no more (spec CP-63, Examples, "It does not say tasks exist"). "Nothing else yet" is true as this change leaves the product, and CP-63's three phrases don't appear.
- **The opening paragraph is reworded, which the request didn't ask for.** Its first sentence began with `tracker17`, which CONTENT § Grammar and mechanics, "Case", says never starts a sentence. Its last sentence used "simple", which CONTENT § Terminology bans in anything a person sees. Its second sentence ran to 23 words, over the 20-word bar. Under `<CORE>/doctrine/governance/found_while_walking.md` § *The rule*, clause 1, a small defect found on the branch is fixed in place. The meaning is unchanged: what tracker17 is, who it's for, and that the reader judges the setup. The design's `Publishes text:` line names no place for the paragraph by itself. It is filed here, with the status note, because it sits with that note above the instructions. CP-64 protects only `How it's built` and `The documents`.
- **The terminal message is the spec's CP-65 line, unchanged.** It is CONTENT § Message patterns, Error, "Terminal messages", third example, word for word, with the location as the variable.

---

## Findings for the Content Manager

- **The `mv` line in section 6, `mv data ~/tracker17-set-aside/$(date +%Y-%m-%d-%H%M%S)`, and the directory name `2026-10-08-143205`.** CONTENT § Grammar and mechanics says its punctuation bans "govern the tracker's own words", and § Localization says the commands in the setup instructions are never translated. Neither rule says whether a command, or a name a command produces, counts as the tracker's own words. That matters for the parentheses in the command, and for the date-and-time form of the name, which is not CONTENT's `YYYY-MM-DD HH:MM`. Meanwhile: commands, and names they produce, are treated as not the tracker's words. They are written as the shell needs them, and the directory name is not read against the date and time rule.
- **"Press Ctrl-C", in sections 3 and 6.** CONTENT § Grammar and mechanics, "Verbs for pressing", gives the verb for a button, a link, an option and typed text, and none for a keyboard key or key combination. Meanwhile: "press", the verb the rule already gives for a control a person acts on with one press.
- **"Directory", throughout the setup instructions.** CONTENT § Terminology has no row for a place on disk. "Folder" appears only as a rejected name for a project. Meanwhile: "directory", for the reason in § Wording decisions.
