# project-setup

Starting a product in kensaiapp used to take knowing the machinery: run `project-stamp`, launch the
PRD, answer its companion, launch the Agari, answer that one. A newcomer knows none of it. This
skill is the front door for a project in a kensaiapp: one conversation in plain words, after which the project exists and its
first two documents are being written from the owner's own answers.

## What It Does

- Interviews the owner with `AskUserQuestion` screens and chat questions, in plain language
- Records what kind of product it is (software or not), where it lives, what it looks after outside
  itself, and what material it starts from — on the project card
- Stamps the project through `project-stamp`'s script
- Writes the owner's answers as round 0 of the PRD's and the Agari's companions, in the templates'
  exact shape (`scripts/write_companion.py`), and commits them
- Starts `chain-agari`, which writes the PRD and then the Agari, answering its own follow-up
  questions as every chain does

## File Structure

```
project-setup/
├── SKILL.md                      # the flow — interview, stamp, companions, commit, chain
├── README.md                     # this file
├── scripts/
│   └── write_companion.py        # renders a round-0 companion from its template and the answers
└── tests/
    └── test_write_companion.py   # the rendered shape matches each template
```

## Depends On

- `project-stamp` — its `scripts/stamp_project.py` creates the project and writes the card
- `core/launchers/chain-agari/` — the chain it starts at the end
- `product-prd` and `project-agari` — the runs that read the companions it writes

## When to Use

When someone wants to start a new project or product — especially someone new to kensaiapp who
has an idea and does not know where to begin. For a project that already exists, use the document
skills directly; for only the management folder with no interview, use `project-stamp`.
