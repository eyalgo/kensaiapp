# PRD open issues — tracker17

> **Round 0.** Written by `project-setup` from the owner's interview — every answer below is the owner's own, given before any draft existed.

> Companion to `PRD.md`. The CPO authored the PRD non-interactively; this file holds
> what it could not settle from the inputs. **Answer inline** — fill each **Answer** /
> **Confirm-or-override** slot — **commit this file**, then re-run `product-prd`. It folds
> your answers into the PRD and drops the resolved items. When nothing is left unresolved,
> `product-prd` clears this file: no file = the PRD is done.
>
> **Commit before re-running.** The run that finishes a round removes this file, and git
> refuses to remove a file with uncommitted edits in it — so an uncommitted answer stops
> that run before it can commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the CPO folds them in, it first copies
> this file whole to `docs/trail/prd/` — so what you decided, and why, stays readable
> and citable for good.
>
> **§§ 1–3 are the CPO's own questions. § 4 is not.** It holds what a seat downstream of the PRD —
> one that never wrote a line of it — found missing while working from the documents the PRD
> grounds. Same file, same fold, different asker.

---

## 1. Open issues — product-defining questions with no answer yet

### 1.1 In a sentence or two, what is it?
- **Why it matters:** PRD: Blurb, Purpose
- **Reasoning / what would settle it:** Asked of the owner in the project-setup interview; answered there.
- **Answer:** A simple local web app task tracker for a small team. It runs on your own machine and you use it in the browser. It manages projects, tasks, assignees, a status workflow, priorities, labels, due dates and comments, with filtering, sorting and project summaries. Built with TDD, with unit, integration and end-to-end tests.

### 1.2 Who is it for?
- **Why it matters:** PRD: Target Users
- **Reasoning / what would settle it:** Asked of the owner in the project-setup interview; answered there.
- **Answer:** Someone who is interested in seeing how kensaiapp builds apps.

### 1.3 What's painful for them today that this removes?
- **Why it matters:** PRD: Problem Statement, Why This
- **Reasoning / what would settle it:** Asked of the owner in the project-setup interview; answered there.
- **Answer:** There's no SIMPLE example of a kensaiapp product.

### 1.4 What are the 3–5 main things they'll do with it?
- **Why it matters:** PRD: Key Use Cases, Core Features
- **Reasoning / what would settle it:** Asked of the owner in the project-setup interview; answered there.
- **Answer:** Look at the code, see if it works, and see if it's simple to set up on a machine.

### 1.5 What is it deliberately not?
- **Why it matters:** PRD: Out of Scope
- **Reasoning / what would settle it:** Asked of the owner in the project-setup interview; answered there.
- **Answer:** Not hosted or multi-user over a network. No login or access control, no real-time collaboration, no notifications, no export. No threaded comments, no multi-value filters, no multi-field sort, no moving tasks between projects, and no cross-project summary.

### 1.6 How will you know it's working?
- **Why it matters:** PRD: Goals, Success Metrics
- **Reasoning / what would settle it:** Asked of the owner in the project-setup interview; answered there.
- **Answer:** I will run it locally and see it works.

### 1.7 Does it handle people's personal data?
- **Why it matters:** PRD: Data & Privacy
- **Reasoning / what would settle it:** Asked of the owner in the project-setup interview; answered there.
- **Answer:** No.

### 1.8 Does it rely on other services — a login, payments, an API?
- **Why it matters:** PRD: Dependencies / Integrations
- **Reasoning / what would settle it:** Asked of the owner in the project-setup interview; answered there.
- **Answer:** No.

### 1.9 Where will people use it?
- **Why it matters:** PRD: UX Notes
- **Reasoning / what would settle it:** Asked of the owner in the project-setup interview; answered there.
- **Answer:** Web.

## 2. Choices to confirm — the CPO drafted a best-effort answer; confirm or override

## 3. Directives — an external action the owner confirms as a gate

## 4. Raised from downstream — an item from a seat that did not write the PRD
