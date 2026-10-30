# Flow Findings — development-plan  (audited 2026-10-30)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

- **[non-blocking · change-local · contract realized]** The scope gate for CP-745 ("only `README.md` changes among product files") is `git diff --exit-code <merge-base> -- products/tracker17/ ':!…README.md'`, and `git diff` does not see untracked files. A new untracked file under the product would pass it. Where: `tl_instruction.md` Task 1, Verification gate. Detail: add an untracked-file check (for example `git status --porcelain -- products/tracker17`) so the contract holds by construction rather than because the Developer adds no file.

Cross-checks that held: Category `feature` / Behaviour `changing` copied verbatim from the spec and design; every rule CP-736–CP-746 and Examples 1–13 maps to V1–V13 or a gate command; the design's explicit running-case scope for CP-742 is carried into V4–V8; the departures from the design (no § 3, comparing against the merge base instead of a fixed commit) are recorded in `## TL Review Notes`; the plan names no downstream role's decision and fixes no published sentence. The product has ADRs, NFDR and SDD; no conflict found.
