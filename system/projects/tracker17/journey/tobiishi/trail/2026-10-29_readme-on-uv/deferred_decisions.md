# Deferred Decisions — readme-on-uv

What this change held back, for `shukuba-refine` to place after the unit lands. Three kinds of entry, each stamped with the stage that wrote it and shaped below:

- a **direction** decision the spec could not responsibly make — destructive / irreversible, or no safe default existed (development-specs, Step 5 *Direction ambiguity*);
- a **record gap** — a behaviour a product document states, binding nothing this change adds or alters, that the product does not have today and the request does not ask for — or one the request explicitly rules out (development-specs, Step 5 *A record's unbuilt behaviour is handed on*);
- a **reading set aside** — spec lines the design did not carry, because another reading kept every existing contract and delivered the request (development-design, Step 7).

**Collection, read after the unit lands.** Downstream stages (development-design, development-plan, development-implementation) append their own entries, creating the file from this template when it is absent; `shukuba-refine` reads the collection and acts on the route for each entry that has lost its owner. Fill only the fields of the entry's own kind.

---

## uv named in the prerequisites section — record gap, handed on by development-specs (2026-10-29)
**Record:** SDD § 6 S-1 *Artifact*: the prerequisites section holds, "for the test suite only, uv and a network connection needed once". It pulls against SDD § 4 RT-4 and ADR-0013 § Decision, which both say the tracker's own setup names uv nowhere. The SDD does not say whether the prerequisites section counts as the tracker's own setup.
**Product today:** `products/tracker17/README.md:17-29`, `### What you need`, names Python 3.11 or later, macOS and Linux, and the network connection the tests need once. It does not name uv.
**Why not this change:** the request rules it out: "The tracker's own setup text (`## Setup instructions` down to `### Running the tests`) names uv nowhere". The station's reached-when item 4 checks the same range. Settling it is the SDD's call on which of its two sentences holds, not a README edit.
**Owner:** none — for shukuba-refine
**Status:** open

---

## Dependency graph coverage of uv.lock — record gap, handed on by development-design (2026-10-29)
**Record:** `products/tracker17/docs/nfdr.md:383-391`, QC-40, requires the first review after the lock lands to verify that the repository dependency graph lists its packages. A graph listing none is a discrepancy for the Principal Architect.
**Product today:** The authenticated command `gh api repos/<owner>/<repository>/dependency-graph/sbom` returned `Not Found (HTTP 404)`, exit 1. The graph's contents are unknown; this response is not evidence that the graph is empty. The exact 16 registry versions in the product's `uv.lock` returned no matching advisories from `https://api.osv.dev/v1/querybatch` on 2026-10-29, which does not verify GitHub's feed.
**Why not this change:** CP-682 limits product edits to the README. No dependency or lock-format change is requested. Verify the repository's dependency graph with access that can read it, and surface any missing lock-file coverage to the Principal Architect under QC-40.
**Owner:** Principal Architect — for shukuba-refine to place
**Status:** open
