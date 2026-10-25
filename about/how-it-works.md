# How it works

This guide explains how KensaiApp checks a change, what it does with what the checks find, and how
it decides what comes next: after a change, when the Principal PM cuts seeds from the product's
documents, and when a seed is walked and closed. The [README](../README.md#how-a-change-moves) shows the pipeline one change
goes through. This guide is about what happens around it.

## Three checks on every change

After the developer's last commit, three checks read the change, each in a separate agent run by a
role that did not write the code. Two of them check the product. The third checks KensaiApp itself.

| Check | Role | What it checks | Can it stop the change? |
|---|---|---|---|
| Prove | Senior engineer | The product: that the code does what the change intends. It adds the tests nobody wrote, corrects a test read off the code instead of the intent, and fixes the code where a correct test fails | Yes. A change whose proof fails does not reach the seal |
| Security | Senior engineer | The product: its dependency audit, and the change's code read for security holes. It fixes what its rules allow and reports the rest | Only when a fix needs a move it is not allowed to make. It then stops once, with every such question for you |
| Audit | Auditor | KensaiApp: how well each step of the pipeline did its job on this change. It reviews the spec, the design, the plan, the content where it ran, and the code, each in a run of its own, all at the same time. It looks for gaps a step left, a step working at the wrong level of detail, a departure nobody recorded, or new logic placed outside the part that owns it. It lists what it finds and never fixes it | No. It judges the pipeline's work, not the product, so the product's own checks decide whether the change goes on |

Each audit finding is graded `blocking` or `non-blocking`, and tagged by what it is about:
`change-local`, this change's output, or `skill-general`, a weakness in the skill that produced it. A
`blocking` finding does not stop the change either. It is the first thing the PM's review deals with.

The security check is a first iteration. It leaves `security-report.md`, whose first line says
`clean`, `fixed`, `reported` or `stopped`. For an advisory in a dependency the product does not reach,
it writes an exception, with a reminder to look at it again. Planned next: its bookkeeping moves into
a tested tool, and the check always runs `osv-scanner`, Semgrep's community edition and `gitleaks`.

## Where what the checks find goes

What the checks find goes one of two ways: back into the product's plan, or to KensaiApp's own
findings.

| What was found | Where it goes |
|---|---|
| A defect in the product the senior engineer could not fix on the change's branch | Back into the plan: the PM's review places it on the route, or recommends a new seed for it |
| A security hole, or an advisory with no fix, left for the PM | Back into the plan: onto the seed or station that carries the work, or a new security seed, which is picked before feature work |
| An audit finding about this change that leaves work no one owns, or that shows a defect in the product | Back into the plan, in the PM's next review |
| A gap in a product document | A question on that document, which its own writer answers on its next run |
| An audit finding about a skill, a prompt or the pipeline | KensaiApp's findings: it is raised as an improvement to the skill, and fixed by hand for now ([Two kinds of finding](#two-kinds-of-finding)) |

So the product's issues are answered by the journey itself, and KensaiApp's issues are answered by
improving KensaiApp.

## The PM's review of the route

After each change is sealed, or halts, the PM reviews the project's route (`shukuba-refine`). It reads
what the change left first: every audit findings file, the code-integrity report and the security
report. It then reads what moved in the product's documents, the project's seeds and stations, the
project's definition of done, and the product as it stands now. Where a record and the product
disagree, the product wins.

The review can make six moves:

| Move | When |
|---|---|
| Change a seed | A station still ahead is re-cut, split, added or amended. A station already walked is never touched |
| Change a station | The open one, or a parked one, where the change shifted the ground under it |
| Park a station | It can no longer be walked as written, and should wait |
| Un-pick the active seed | It is blocked, and leaving it in place holds the project still |
| Raise a question on a product document | The document has a gap. The question goes into the document's open questions, and the document's own writer answers it on its next run |
| Drop a halted change | The work will not be done as written: the product has nothing for it to build, or the document it serves moved away from it |

What the PM may not do itself, it leaves for the Principal PM as recommendations: cutting new seeds,
dropping seeds, fixing a defect. When a seed's checklist is walked and the seed is retired, the
Principal PM answers every one of them (`nemawashi-refine`). Each waiting seed is kept, changed or
dropped, and new seeds are cut where work has no owner.

The review ends by writing the next moves, which `build-idea` runs as a queue: close a reached
station, retire a walked seed, pick the next one, or open the next change.

## The route is re-decided after every change

The plan is not fixed. After every change, the PM re-plans the stations still ahead from what that
change found. It can reorder, split, park or drop them. It decides within fixed bounds:

- **What was asked for does not move.** The route is re-cut; what the work is, is not.
- **The project's definition of done is the judge.** A move that brings the project no closer to it
  is not made.
- **The product's documents are not edited.** A gap in one is raised as a question for its own
  writer.
- **The past is not rewritten.** A station already walked is never touched, and every change to a
  seed is logged in it with its reason.
- **What is still moving is held.** A seed or station that a running walk may still change is left
  alone.
- **A person decides past a limit.** A station whose goal two reviews have re-aimed goes to you.

## How the Principal PM cuts seeds from the product's documents

A seed is a candidate route toward the project's done, with a checklist of stations. Most seeds come
from the product's settled documents: the Principal PM cuts them with `seeds-from-product-docs`, once
the documents chain has settled, and again whenever earlier seeds have been walked.

**What it reads.** It draws from four documents: the software design (SDD), whose slices of work are
the main source, the functional rules (FDR), the architecture decision records (ADR) and the
non-functional rules (NFDR). Before it orders anything, it checks every rule, decision and obligation
in them against the product as it stands, not against what the documents claim. What the product does
not yet meet is work to cut. A line a sealed change's security report left for the PM, and that the
product still does not meet, is cut as a security seed.

**What it cuts.** Each candidate becomes one of four kinds of seed:

| Kind | What it is | When it is done |
|---|---|---|
| Work on the product | A slice of the design, or a rule, decision or obligation the product does not meet yet. Most seeds are this kind | Its checklist is walked |
| A missing document | A document the product's records name, such as a runbook, that nobody has written | It is written |
| A question upstream | Something only a document above can fix, such as two settled documents that disagree. The cut does not edit that document: it raises the question in the document's open questions, and the seed tracks it | The answer is folded into the document |
| A new project | Work no project's definition of done claims, so a project must exist before its seeds can be written | The project exists |

**How it orders them.** A seed is cut through the product, not across it: one path all the way from
storage to what a person meets, so each seed leaves something working. Seeds go in the order what
must be settled first allows, and the riskiest go early, so that a wrong assumption costs one seed,
not four. Where neither decides, a quality seed, a security seed among them, goes ahead of a feature
seed.

**What it does not do.** It reads the project's seedbed first, and does not cut again work that is
being walked, is waiting, or is already done. It never picks a seed and never opens a station: those
are the PM's. It ends by saying which parts of the documents it left uncut, and which questions it
raised upstream.

## Quality and security come first

A seed that makes the product's footing hold, such as its tests, its test harness, its CI, its
security or a clean tree, is a quality seed. A seed cut to close what a change's security check left
is one too. Quality seeds come before feature seeds, at each seat that orders the work:

- **The PM's pick.** When a quality seed competes with a feature seed, the PM picks the quality seed,
  even where the order the seeds were queued in put the feature first. The pick says so in one line,
  and does not ask you.
- **The Principal PM's cut.** Where neither what must come first nor risk decides the order, the cut
  puts quality seeds ahead of feature seeds, so the order it proposes is the one the pick will keep.
- **The answer to a walked seed.** A security hole a change left is answered as product work, never as
  a question on a document, so it becomes a seed rather than waiting on a document's next run.

An order you state outright still wins.

## When a seed is walked: closing it, and what follows

When the last station of a seed's checklist is closed, the seed is closed in two steps.

1. **The Scrum Master retires it** (`nemawashi-retire`). This step is mechanical and decides nothing.
   It checks that every item of the checklist is ticked and that no station or change is left open,
   then moves the seed to the project's trail, where walked seeds are kept.
2. **The Principal PM answers it** (`nemawashi-refine`). It works through every recommendation the
   PM's reviews left during the seed's walk, and re-reads every seed still waiting.

Each recommendation is answered one way, with its reason:

| Answer | When |
|---|---|
| A question on a product document | The work is something a document should state. The question goes into the document's open questions, and a cut from the documents draws the work out once the document is updated |
| A cut from the documents | A document already states the work, and no seed carries it |
| An existing seed | A waiting seed carries it, as it is or once changed |
| A drop | A waiting seed was overtaken, ruled out or superseded (`nemawashi-drop`) |
| A cut from an idea | The work is something no product document should state, such as hygiene or tooling in the instance itself |
| Another project | The work spans projects, and is named for a Principal PM session to route |
| Ignored | It no longer holds. The reason is written down |

**A cut from an idea uses `seeds-from-idea`.** The Principal PM writes the recommendation as a brief,
quoting it at its lines, and runs `seeds-from-idea` on it, inside its own run. Nobody is asked to
confirm this brief: the quote is checked against the file before the cut reads anything else. The
new seeds land among the waiting ones, and the cut's report says what it did with each line of the
recommendation. In a session with you, the same skill starts from a brief you confirm
([Cutting seeds from an idea](operations.md#cutting-seeds-from-an-idea)).

A security hole a change left is product work, so it is never a question on a document. It is a cut
from the documents where the NFDR already names that kind of check, and a cut from an idea otherwise.

The Principal PM's answer never cuts from the documents itself, never picks and never opens a
station. It ends by naming the next moves, each with who runs it: the sweep of the documents' open
questions, a cut from the documents where one is owed, and the PM's next pick.

## Two limits

- **The response comes one change late.** What the checks leave for the PM is answered in the review
  after the change, never inside it. No step sends a sealed change back to be reworked.
- **KensaiApp's own issues are fixed by hand.** A finding about a skill, a prompt or the pipeline is
  not the PM's to move on, and no step of the loop picks it up yet. A person carries it to a fix
  (next section).

## Two kinds of finding

KensaiApp uses the word for two things.

| | An audit finding | A finding about KensaiApp |
|---|---|---|
| What it is about | How well one step of the pipeline did its job on one change | KensaiApp itself: a skill, a prompt, a rule, a hook or a launcher |
| Who writes it | The auditor, one file per step it reviews | Any run, or you, noticing a defect while doing something else |
| Where it is kept | The change's `flow_findings/<step>.md` | `docs/findings/<date>_<slug>.md`, in the instance where it was noticed |
| What follows | The PM's next review of the route. One about a skill is also raised as an improvement to that skill | A small one is fixed in place. A larger one becomes a seed. The rest wait for a person to carry them to a fix, by hand for now |

[Findings](operations.md#findings) in the operations guide says how to write one, and what a
satellite does with one.

## When a walk stops for you

Once the journey starts, it runs without you. It stops when:

- it needs an act only you can do, such as pushing a branch, or walking a station only you can walk;
- it needs a question only you can answer, such as a fix the security check may not make;
- a step fails, such as a test suite that is red;
- you stop it, with `--stop`.

A run never stops to ask a question while it writes a document. It writes the question in a companion
file beside the document, and an answering run decides what it may
([How a document's open questions get answered](architecture.md#how-a-documents-open-questions-get-answered)).

The chain's closing message names where it stopped and why, and the panel shows what it needs from you
([See where things stand](operations.md#see-where-things-stand)). You settle the cause, then run the
same launcher again, and it carries on from what is on disk.

## What a change costs

Every step is a Claude Code run, and each costs tokens. With telemetry on
([How to collect telemetry](how-to.md#how-to-collect-telemetry)), every run is labelled with its
instance, project, step, model and effort, so the cost can be read back by any of them.

[What building ka-telemetry cost](https://github.com/eyalgo/ka-telemetry/blob/main/docs/build_cost.md)
is one such report, for a product KensaiApp built: the cost of a change, every walk it took counted,
the cost by step and by model and effort, and how large each step's context grows. It counts launched
Claude runs only. Runs on other providers, and interactive sessions, are not in it.
