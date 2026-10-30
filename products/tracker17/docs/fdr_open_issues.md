# FDR open issues — tracker17

> Companion to `fdr.md`. The Principal PM authored the FDR non-interactively; this file holds what the
> run could not settle from its inputs — the PRD, the SRS and the SDD.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**, then
> re-run `product-fdr`. It folds your answers into the FDR and drops the resolved items. When nothing is
> left open, `product-fdr` **deletes this file**: no file = the FDR is done.
>
> Your answers are never thrown away. Each time the Principal PM folds them in, it first copies this
> file whole to `docs/trail/fdr/` — so what you decided, and why, stays readable and citable for good.
>
> **§ 3 is the odd one, and worth reading twice.** The Principal PM writes the FDR *and* is the seat
> most likely to raise an item against it later, cutting the same product's documents into seeds. The
> two are different acts at different times, and § 3 keeps the later one visible instead of letting
> it be quietly folded back into § 1 as though the authoring run had asked it.

Every `R-n`, `PD-n`, `OOS-n` and `RN-n` below is an entry of `products/tracker17/docs/fdr.md`, version 5.
Every `PRD`, `SRS` and `SDD` reference is to `products/tracker17/docs/PRD.md`,
`products/tracker17/docs/SRS.md` and `products/tracker17/docs/SDD.md`.

---

## 1. Open issues — behavioural questions with no answer yet

None.

## 2. Choices to confirm — the Principal PM drafted a best-effort answer; confirm or override

### 2.1 The inputs moved after FDR version 4 read them, and the FDR now follows them
- **Drafted into the FDR:**
  - **The Description** names the second purpose, kensaiapp's own testing ground.
  - **R-121, R-122 and R-123 (new):** the README carries the setup instructions and a reader arrives at it first, its opening paragraph names both purposes, and of the earlier versions that paragraph names only tracker16-X. An earlier reading of this item proposed one rule. The FDR states three, because SRS FR-41 states three things and a rule carries one.
  - **R-124, R-125 and R-126 (new):** the prerequisites name the tool that makes the test suite's environment and say the suite alone needs it, the suite's instructions say how to install it, and the commands that reach the tracker do not use it. The rules leave the tool's name, uv, to SDD § 4 RT-4.
  - **R-127 (new):** a return through Back or Forward to a confirmation's page shows what the saved data allows at that moment, and never a confirmation of an action the data no longer allows.
  - **R-128 (new):** a filter or sort value its control cannot hold is refused with the reason, and no result is shown.
  - **RN-11** gains drop-lines for SDD § 3's `application` row, RT-4's mechanisms, RT-8's definition of a submission, RT-11's status codes and headers, and the PRD's second purpose and public-release sentence. It lands TO-8 and TO-9, and it names the question SDD § Open Questions now holds. **RN-15** records all of the above.
  - **The *Inputs read* line** reads PRD version 7, SRS version 6, SDD version 18 and UXD version 11.
  - **Unchanged:** R-106, PD-11 and OOS-1, each read against the changes and still true as written.
- **Rationale:** the FDR's only permitted deltas are an owner's answer and an upstream change, and this item reports the upstream changes so you can see the foundation moved. PRD § Purpose ends "A reader learns both purposes from the first thing they read about tracker17", and SRS FR-41 and AC-21 carry that want, with no rule here until now. SDD RT-4 has the prerequisites section name uv as the suite's alone, on the owner's own call (`products/tracker17/docs/trail/sdd/cycle-12.md` § 5.1). R-9 to R-11 and R-119 already carry what RT-1, RT-3 and RT-4 give the instructions, so leaving this out would leave RT-4 half carried. R-127 and R-128 go past the drop-lines an earlier reading of this item proposed. On this reading SDD § 9 TO-8 has a consequence a user sees: "a return through Back that shows the saved status". SDD RT-8 now names "a value its control cannot hold" as a refusal that no rule here stated. The product does both: `tests/e2e/test_moves.py`, `test_real_history_traversal_revalidates_the_confirmation`, and `domain/filtering.py`, `InvalidFilterStatus`. The product falls short of R-124 today: `products/tracker17/README.md` § What you need does not name uv, and SDD RN-65 says that section "is owed one sentence, and which unit carries it is the PM's". Confirming R-124 does not write that sentence.
- **If overridden:** with "drop R-121 to R-123", FR-41 has no rule here, and the Product Owner and QA read no behavioural line for it. With "name uv", R-124 to R-126 name it, and a later change of tool becomes a change to this document as well as to the SDD. With "drop R-124 to R-126", those rules go, RN-11 returns them to mechanism, and the instructions' uv content rests on the SDD alone. With "drop R-127", or "drop R-128", that rule and its Examples rows go, and RN-11 records the source as a drop-line. A different answer on the second purpose is a change to the PRD (the CPO's) and the SRS (the CTO's) first.
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

## 3. Raised from downstream — an item raised against the FDR after it settled

None.
