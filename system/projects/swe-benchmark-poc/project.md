# Project Context — swe-benchmark-poc

**Product path:** products/swe-benchmark-poc   <!-- relative → internal product. A folder of the ten issues' patches, each `patch.diff` beside its `LICENSE.upstream`, so a reader can see them; not an issue's clone, which is a path on the owner's machine. -->
**Source material:** <blank>   <!-- optional; read by product-prd at PRD time. Point at the product-intent source — proposal/brief docs, a legacy repo, links — or leave blank if the intent is supplied in conversation. Free-form; the scaffolder fills it from --source-material, else leaves <blank>. -->
**Type:** software                    <!-- software | no-code — what the product is: an app or tool with code, or something without (a profile, a body of writing, a public presence). -->
**Definition:** none      <!-- full | prd-agari | none. None on the owner's call, 2026-10-14: no PRD, no product-definition documents; chain-change walks each issue directly. -->
**Manages:** none                     <!-- The issues' repositories are worked on in local clones, never pushed to. -->
**Execution type:** headless          <!-- headless (claude -p) | docker -->
**Package slug:** swe-benchmark-poc              <!-- auto-derived from project name -->
**Test command:** none       <!-- The folder of patches has no suite. -->
**Setup command:** none               <!-- `none`, or a shell command that makes a new change worktree ready to run its suite, e.g. `uv sync --locked`; development-specs runs it once through /bin/sh when it creates the change's worktree, in the directory Test command: runs in. A non-zero exit halts the change there and leaves the worktree in place. The change halts there too when the interpreter Test command: names is a relative path, such as `.venv/bin/python3`, with nothing at it. -->
**Languages:** <blank>                <!-- optional; comma-separated, order carries no meaning; omit for a project with no code; resolves to packets per languages/README.md. Spell each language in prose — `Rust, TypeScript, Shell`. The skeleton tree and the packet folder are both lowercase on disk and the skeleton launcher lowercases this value before it looks one up, so the prose spelling is the one to write. The SDD § 3 units table places each language's buildable units; the card does not repeat that design fact. -->
**Parallelism:** N/A — headless       <!-- docker-only; N/A for headless -->
