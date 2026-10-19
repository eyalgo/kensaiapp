# Flow Findings — development-specs  (audited 2026-10-07)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

- **[non-blocking · change-local · evidence that could have failed]** CP-32 says a request refused for its host is still refused 403 with an empty body, but `## Verified Claims` ran only the `Sec-Fetch-Site: cross-site` refusal. No wrong-`Host` request was run, though the product has that refusal (`tests/integration/test_routes.py:179-180`, `test_a_wrong_host_is_refused`). Where: `change_spec.md §Verified Claims` row "A refused request and a non-GET request…". The claim about what the host check decides rests on the existing test, not on a run in the record. Direction: run a wrong-`Host` `GET /projects/99` and record the answer.

Lenses 1–6 and 8: clean. Every rule maps to Examples and to a CP-38 test, and the rule-implied edges are covered (long id, `/projects/`, trailing slash, query string, non-GET, refused). Category `feature` and Behaviour `changing` are in vocabulary. Each of Gap 1–8 is recorded with its reason. No downstream role is named or enacted. The `## Verified Claims` section is present and the other claims were run, with command, tree and result. Lenses 9 and 10 do not apply to this step.
