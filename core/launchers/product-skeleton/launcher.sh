#!/usr/bin/env bash
#
# launcher.sh (product-skeleton) — the owner-run command that gives a product its skeleton,
# deterministically, once its foundation step has settled. No AI runs here.
#
# Version: 1.9.1 — the idea cut reads the owner's words, not its own — a checked brief, a report beside it, back in the Principal PM group, no launcher
# Version: 1.9.0 — re-running the card leaves a built product's code alone — the skeleton places a frame whole or not at all
# Version: 1.8.3 — each prompt one skill reads moves under that skill as prompts/rich.md
# Version: 1.8.2 — the neutrality check reads fixtures and .claude/, declares platform names, and repairs fixture hits itself; the ratify launcher is deleted
# Version: 1.8.1 — seeds-from-product-docs launches through the skill launcher from its launcher.md, and its dedicated launcher is removed
# Version: 1.8.0 — the skeleton launcher anchors ignore patterns as git does; two tree-doc contradictions the Swift run found are closed
# Version: 1.7.2 — Swift joins the language family — a packet under the registry and a starter tree the skeleton launcher copies, twice blind-audited
# Version: 1.7.1 — the first refactor sweep of core/launchers: four behaviour-neutral packets and its report
# Version: 1.7.0 — a run keeps the version it started on — every launcher enters a pin of core/, .claude/ and skills/
# Version: 1.6.0 — product-skeleton builds each unit from the SDD's language and kind
# Version: 1.5.0 — a launcher may live nested under core/launchers/development/, and its reach resolves <CORE> from its own location instead of counting folders
# Version: 1.4.0 — the setup step exists: a product's settled documents write its card and README, then the skeleton lands where the card says
# Version: 1.3.1 — the vendored layer names no product, and the rule that licensed it is gone
# Version: 1.3.0 — the run commits what it wrote, through the one builder
#   <CORE>/launchers/product-skeleton/ (no relocation, no prior name, so no provenance block).
#
# THE MODEL, AND THE ONE PLACE THIS DIVERGES FROM EVERY SIBLING
#   The argument surface and card resolution follow the shape the `seeds-from-product-docs`
#   launcher had until it was removed on 2026-09-25, the skill launching through
#   `core/launchers/skill/`: one positional that is a PROJECT
#   NAME (a path is refused, the exact inverse of the bare-word rule the `seeds-from-idea`
#   launcher held until it was removed on 2026-10-24),
#   `--instance-root <dir>` accepted first, `--dry-run`, the project card resolved through
#   `system/projects/<project>/project.md`, and its `Product path:` line read through the trailing
#   HTML comment exactly as every sibling reads it.
#
#   THE DIVERGENCE, AND IT IS THE WHOLE DESIGN DIFFERENCE: every sibling launcher SPAWNS A MODEL —
#   a fixed `claude --bg` prompt, an `--agent` seat, a completion watcher. This one spawns nothing.
#   It is a copier: it reads the project's card and its product's settled SDD, copies the language
#   trees `core/templates/skeleton-templates/` already carries, materializes each unit the SDD's § 3
#   names according to its Language and Kind, commits that through `<CORE>/tools/commit_builder.py`,
#   and exits. A pre-units SDD retains the original one-directory-per-part behavior. No
#   `claude`, no `--agent`, no `--permission-mode`, no prompt, and therefore no completion watcher
#   and no `--keep-awake` — the commit is the one thing it does that a sibling's agent would have
#   done for itself, and it carries `Surface: product-skeleton` with no `Co-Authored-By:` to say so.
#
# WHY A LAUNCHER, EVEN WITH NO MODEL BEHIND IT
#   The owner's own ruling (2026-09-02): "after `foundation` is done, I run a launcher that creates
#   the skeleton. no AI." The job is the same for every product — copy the language frame, lay out
#   the parts the SDD already named — so it belongs to a deterministic command the owner runs, not
#   to a seat's judgment. `skills/principal-pm/.claude/skills/seeds-from-product-docs/prompts/rich.md` § *Before you cut — the
#   skeleton is not yours* already sends the owner here.
#
# WHERE THE THREE INPUTS LIVE
#   - The project card (`system/projects/<project>/project.md`) supplies `Languages:` (which trees
#     to copy) and `Package slug:` (the `__PROJECT__` substitution value, except for a tree placed
#     at an SDD unit, where the value is the unit's last path segment).
#   - The product's `docs/SDD.md` § 3 supplies the parts and units tables — each unit's path,
#     language and kind say what the launcher creates. `sdd_template.md` § 3 states explicitly:
#     "Both tables are read by a
#     tool, not only by a person... That is why the shape below is fixed rather than left to the
#     run."
#   - `core/templates/skeleton-templates/<language>/` supplies the tree itself, matched with the
#     card's spelling LOWERCASED — the trees are lowercase and a card spells the language in prose.
#     One of the six language answers (`shell/`) is a declared absence — a folder holding only its
#     own `README.md` — and is skipped rather than copied or refused.
#
# IT NEVER OVERWRITES
#   A file or directory the launcher would create that already exists in the product is left alone
#   and reported. Re-running against a product that already has its skeleton is safe. The same
#   guarantee holds BETWEEN two declared languages: five of the six trees carry a `.gitignore` of
#   their own, so on a multi-language product the first language on the card places the shared path
#   and every later one is skipped and reported — never a silent replacement of what this same run
#   has just written.
#
#   AND A FRAME IS PLACED WHOLE OR NOT AT ALL AGAINST WHAT THE PRODUCT ALREADY HOLDS. Each tree
#   placed at one spot (a language root, a unit of the SDD's units table, or a language's
#   product-level tree) is one frame. When any of its files other than a `.gitkeep` already sits at
#   its destination, the frame was placed before or code was built over it, so none of its files
#   are placed and the frame is reported as already built. A `.gitkeep` does not count, because
#   trees share them. Within one run, two trees claiming the same path still follow the rule below:
#   the first wins. A per-file guard is not enough: measured
#   2026-10-14 on a built product, it placed `src/main.rs` beside a library crate's `src/lib.rs`,
#   which made the crate a binary and failed the build, and placed Swift sources for targets the
#   package did not declare. A unit the SDD adds later still gets its frame, because nothing of it
#   is there yet.
#
#   ONE FILE IS EXEMPT, AND IT IS THE ONLY ONE: `.gitignore`. It is not a frame the product might
#   already have its own version of — it is the list of what a language's toolchain generates, so a
#   product that declares the language needs every entry of it whether or not a file already sits at
#   that path. Skipping it is correct by the rule above and wrong in fact: measured 2026-09-03 on
#   the first two live runs, one product gained Rust and was left with no `/target`, the other
#   gained JavaScript and was left with no `node_modules/`, and both files were skipped exactly as
#   designed.
#   The same loss hit a product with NO `.gitignore`, where the first tree placed its file and every
#   later tree's was dropped as a collision.
#
#   SO IT IS COMBINED, NOT REPLACED. The product's own file is kept whole and leads, byte for byte;
#   each declared language's missing entries follow in card order under a block naming where they
#   came from. An entry already present contributes nothing, so a re-run leaves the file byte for
#   byte as it was, and a comment in a tree's file does not travel — it describes that tree, not the
#   product's file. Nothing is ever removed or reordered. The owner's call, 2026-09-03.
#
# A PART DIRECTORY CARRIES A .gitkeep, BECAUSE GIT HOLDS NO EMPTY DIRECTORY
#   A part is named in the SDD before any of its code exists, so every directory this launcher
#   creates from § 3 is empty by construction — and git stores no empty directory. Without a file
#   in it, the whole point of reading § 3 evaporates at the owner's first `git add`: measured
#   2026-09-03 on the first two live runs, where 20 of 21 part directories were invisible to
#   `git status --untracked-files=all` across the two products. The language trees already answer
#   this the same way — seven `.gitkeep` files between them — so the parts take the tree's answer
#   rather than a second one.
#
#   ONLY WHERE IT IS NEEDED. A part directory that already holds something is tracked by that
#   content and gets no marker; one this run is about to write a file into gets none either. An
#   existing but empty part directory DOES get one, so a product whose skeleton predates this
#   behaviour is repaired by re-running rather than by hand.
#
# THE THREE REFUSALS THAT FIRE BEFORE ANYTHING IS WRITTEN
#   No `Languages:` line, no `docs/SDD.md`, or an SDD § 3 with no parts table — each is a refusal,
#   never a partial write. This launcher extends the same guarantee to every other refusal it can
#   raise (an unregistered language, a malformed part slug, a `Lives in` cell that is not a path):
#   everything is validated and planned before the first byte is written, real run or `--dry-run`
#   alike.
#
# IT DOES NOT INSPECT WHAT IT COPIES, AND THAT IS DELIBERATE
#   It substitutes one token and copies the rest byte for byte. It used to also scan each copied
#   file for a placeholder-shaped token it did not know and refuse the run — but the trees are
#   OURS, vendored under `<CORE>/templates/skeleton-templates/`, so that scan checked our own
#   artifacts on the owner's machine at copy time, which is the last moment anything can be done
#   about it and long after the bad tree shipped. It is now a test over the trees themselves
#   (`<CORE>/tools/test_skeleton_trees.py`), which runs in CI, knows which files are code and
#   which are markup, and cannot refuse anyone's `Vec<String>`, `<head>` or `__name__`.
#
# TEMPLATES ROOT, AND WHY IT IS OVERRIDABLE
#   This script lives under `<CORE>/launchers/product-skeleton/`, shared across every instance that
#   binds `<CORE>` — so it resolves the
#   templates root from ITS OWN location via CORE_DIR (a prefix strip at the `/launchers/`
#   boundary, not a fixed number of parent steps), never from the caller's instance root, which
#   may not be the instance this exact file was vendored into.
#   `LAUNCH_PRODUCT_SKELETON_TEMPLATES_ROOT` overrides it — unlike `<CORE>` itself, a suite that
#   builds its own fake trees (rather than reading the real, ever-changing ones) needs a seam to
#   stand a fixture tree in the real one's place, the same reason `$WATCHER` is overridable on every
#   sibling launcher that spawns one.
#
# USAGE
#   <CORE>/launchers/product-skeleton/launcher.sh <project> [--dry-run]
#            (run from the instance root)
#     <project>     a project under system/projects/<project>/ — a NAME, never a path.
#     --dry-run     print everything the run would create (every file, every directory) and create
#                   nothing; every refusal still fires under it.
#     --instance-root <dir>   override the instance root (default: cwd); must come first
#   The one positional is required. Anything after it that is not a known flag is REFUSED, never
#   silently ignored, and every refusal happens before anything is created.
#
set -euo pipefail

# --- resolve this script's own location and the shared CORE via CORE_DIR -----------
#   Sibling of core/tools/ under <CORE>/launchers/<identity>/ — the templates root this launcher
#   reads lives at <CORE>/templates/skeleton-templates: CORE_DIR resolves it from this folder's own location, at any
#   nesting depth, never through the instance root.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # <CORE>/launchers/product-skeleton
CORE_DIR="${SCRIPT_DIR%/launchers/*}"
[ "$CORE_DIR" != "$SCRIPT_DIR" ] || { echo "product-skeleton: no /launchers/ ancestor above $SCRIPT_DIR — refusing to guess <CORE>" >&2; exit 1; }
SCRIPT_PATH="$SCRIPT_DIR/$(basename "${BASH_SOURCE[0]}")"
# shellcheck source=/dev/null
source "$CORE_DIR/tools/pin_run.sh"
pin_enter "$CORE_DIR" "$SCRIPT_PATH" "$@" || exit $?
TEMPLATES_ROOT="${LAUNCH_PRODUCT_SKELETON_TEMPLATES_ROOT:-$CORE_DIR/templates/skeleton-templates}"

# --- resolve the instance root (the caller's cwd) and cd there ----------------------
#   The instance is the caller's cwd; --instance-root overrides. The card this launcher reads
#   (system/projects/<project>/project.md) is always resolved against THIS root, never CORE_DIR.
INSTANCE_ROOT="$PWD"
[ "${1:-}" = "--instance-root" ] && { INSTANCE_ROOT="$2"; shift 2; }
cd "$INSTANCE_ROOT"
INSTANCE_ROOT="$PWD"   # re-resolved absolute, even when --instance-root was given relative

die() { echo "product-skeleton: $*" >&2; exit 1; }

usage="usage: <CORE>/launchers/product-skeleton/launcher.sh <project> [--dry-run]"

# --- args --------------------------------------------------------------------------
#   One positional: the project name. Everything after it that is not a known flag is REFUSED,
#   never silently ignored — a caller cannot append prose to what this run acts on.
project="${1:-}"
case "$project" in
  ""|--*) die "$usage
    <project> is required — a project under system/projects/<project>/" ;;
esac
shift

# A path-shaped positional is refused outright — this launcher takes a PROJECT NAME, and every
# file it reads is derived from it (system/projects/<project>/project.md), never typed directly.
case "$project" in
  */*|.*) die "'$project' looks like a path — this launcher takes a PROJECT NAME, and the files it
    reads are derived from it (system/projects/<project>/project.md), never typed directly. $usage" ;;
esac

dry_run=""
for arg in "$@"; do
  case "$arg" in
    --dry-run) dry_run=1 ;;
    *) die "unknown argument: $arg - this launcher takes only the project name and --dry-run. $usage" ;;
  esac
done

# --- the project must resolve --------------------------------------------------------
project_md="$INSTANCE_ROOT/system/projects/$project/project.md"
[ -f "$project_md" ] || die "no project card at $project_md (is '$project' a real project?)"

# --- resolve the Product path (strip the '**Product path:**' label + trailing comment) ----------
#   A card with no Product path: line is a refusal — the product's docs/SDD.md and its own root
#   (where the skeleton lands) are only reachable through it.
raw_path="$(grep -m1 -E '^\*\*Product path:\*\*' "$project_md" \
  | sed -E 's/^\*\*Product path:\*\*[[:space:]]*//; s/[[:space:]]*<!--.*$//; s/[[:space:]]*$//' || true)"
[ -n "$raw_path" ] || die "no 'Product path:' line in $project_md — the product's docs/SDD.md and its
    own root live there, so this run cannot proceed without one"

case "$raw_path" in
  "~"/*) product_path="${HOME}/${raw_path#\~/}" ;;
  /*)    product_path="$raw_path" ;;
  *)     product_path="$INSTANCE_ROOT/$raw_path" ;;
esac

echo "Project:   $project"
echo "Product:   $product_path"

# --- everything past this point is deterministic file work, no model, no process spawn ----------
#   The heavy lifting (reading Languages:/Package slug:, parsing the SDD's § 3 tables, copying
#   each unit's language-and-kind tree with __PROJECT__/__UNIT__ substituted, the never-overwrite guard, and the
#   --dry-run listing) is embedded here rather than split into a
#   second file, per the plan's scope fence: only launcher.sh, its test file, and the manifest.
#   WHAT COMES BACK, AND WHY IT COMES BACK ON STDOUT. The commit below needs the exact set of paths
#   the Python half wrote. It arrives as marker-prefixed lines in the captured output rather than
#   through a temp file, because the bash half is forbidden from touching the filesystem at all
#   (test_the_bash_half_creates_nothing_before_the_python_half_is_reached) — a refusal must leave
#   nothing behind, and a scratch file created before the Python half has decided is exactly that.
{
python3 - "$INSTANCE_ROOT" "$product_path" "$project_md" "$TEMPLATES_ROOT" "${dry_run:-0}" <<'PYEOF'
import os
import re
import sys

instance_root, product_path, project_md, templates_root, dry_run_flag = sys.argv[1:6]
dry_run = dry_run_flag == "1"


def die(msg):
    print(f"product-skeleton: {msg}", file=sys.stderr)
    sys.exit(1)


def read_field(text, name):
    """`**<name>:** <value>` — strips a trailing `<!-- -->` comment, exactly as the launcher's own
    Product path: read does in the bash half above. Absent line or empty value -> None."""
    m = re.search(rf"^\*\*{re.escape(name)}:\*\*[ \t]*(.*)$", text, re.MULTILINE)
    if not m:
        return None
    val = re.sub(r"[ \t]*<!--.*$", "", m.group(1)).strip()
    return val or None


def reanchor_gitignore(text, lang_root):
    """Move a tree's ANCHORED ignore patterns under `lang_root`.

    Every `.gitignore` the six trees carry is merged into ONE file at the product root, and that
    keeps working unchanged for an ordinary pattern: git matches a pattern containing no slash, or
    only a trailing one, at any depth — so `node_modules/` in the root file covers `ui/node_modules/`
    with nothing done to it.

    A slash anywhere but the end is the exception. "If there is a separator at the beginning or
    middle (or both) of the pattern, then the pattern is relative to the directory level of the
    particular .gitignore file itself" (git-scm.com/docs/gitignore). So `/target` written for a Rust
    tree rooted at `ui/` would ignore `<product>/target` — a path nothing writes — and leave
    `<product>/ui/target` tracked, and `gen/out` does the same with no leading slash to show it.
    Both become `/ui/...`. A `**/` pattern is left alone: it matches at any depth already.

    A negation keeps its `!` and is re-anchored on the pattern behind it, since `!/build` is the same
    kind of anchored path. A comment and a blank line pass through untouched.
    """
    if not lang_root:
        return text
    out = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            out.append(line)
            continue
        negated = stripped.startswith("!")
        body = stripped[1:] if negated else stripped
        if "/" in body.rstrip("/") and not body.startswith("**/"):
            body = f"/{lang_root}/{body.lstrip('/')}"
            out.append(f"!{body}" if negated else body)
        else:
            out.append(line)
    return "\n".join(out)


def section_three_lines(sdd_text):
    """The lines of the SDD's section 3, from its heading up to the next level-two heading or the
    end of the text. None when section 3 is not found. Both table parsers read through this."""
    m = re.search(r"^## 3\.", sdd_text, re.MULTILINE)
    if not m:
        return None
    start = m.start()
    m2 = re.search(r"^## ", sdd_text[start + 1 :], re.MULTILINE)
    end = start + 1 + m2.start() if m2 else len(sdd_text)
    return sdd_text[start:end].splitlines()


def parse_parts_table(sdd_text):
    """`## 3. The parts, and the seams between them` — return [(part_slug, lives_in), ...] from the
    **parts** table specifically (identified by a header carrying both `Part` and `Lives in`, which
    distinguishes it from the seams table beside it). None when § 3 itself is not found."""
    lines = section_three_lines(sdd_text)
    if lines is None:
        return None
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("|") and "Part" in line and "Lives in" in line:
            header_cells = [c.strip() for c in line.strip("|").split("|")]
            part_idx = lives_idx = None
            for idx, cell in enumerate(header_cells):
                bare = cell.strip("`* ").lower()
                if bare == "part":
                    part_idx = idx
                if "lives in" in cell.lower():
                    lives_idx = idx
            if part_idx is None or lives_idx is None:
                i += 1
                continue
            j = i + 1
            if j < len(lines) and re.match(r"^\|[\s:|-]+\|?$", lines[j].strip()):
                j += 1
            rows = []
            while j < len(lines) and lines[j].strip().startswith("|"):
                cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
                if len(cells) > max(part_idx, lives_idx):
                    part = cells[part_idx].strip("`").strip()
                    lives = cells[lives_idx].strip("`").strip()
                    if part:
                        rows.append((part, lives))
                j += 1
            return rows
        i += 1
    return None


def parse_units_table(sdd_text):
    """Return the fixed § 3 units table, or None for a pre-units SDD."""
    lines = section_three_lines(sdd_text)
    if lines is None:
        return None
    for i, raw in enumerate(lines):
        if not raw.strip().startswith("|"):
            continue
        headers = [cell.strip("`* ").lower() for cell in raw.strip().strip("|").split("|")]
        if headers != ["unit", "language", "kind"]:
            continue
        j = i + 1
        if j < len(lines) and re.match(r"^\|[\s:|-]+\|?$", lines[j].strip()):
            j += 1
        rows = []
        while j < len(lines) and lines[j].strip().startswith("|"):
            cells = [cell.strip().strip("`").strip() for cell in lines[j].strip().strip("|").split("|")]
            if len(cells) >= 3 and (cells[0] or cells[1] or cells[2]):
                rows.append(tuple(cells[:3]))
            j += 1
        return rows
    return None


# --- the three refusals, all before anything is written ---------------------------------------
card_text = open(project_md, encoding="utf-8").read()

languages_raw = read_field(card_text, "Languages")
if not languages_raw:
    die(
        f"{project_md}: no 'Languages:' line — the skeleton launcher needs it to know which trees "
        "to copy"
    )
languages = [entry.strip() for entry in languages_raw.split(",") if entry.strip()]

sdd_path = os.path.join(product_path, "docs", "SDD.md")
if not os.path.isfile(sdd_path):
    die(
        f"{sdd_path}: not found — the skeleton launcher reads its § 3 parts table before creating "
        "anything"
    )

sdd_text = open(sdd_path, encoding="utf-8").read()
parts = parse_parts_table(sdd_text)
if not parts:
    die(
        f"{sdd_path}: § 3 carries no parts table — the skeleton launcher reads it for the parts to "
        "create"
    )
units = parse_units_table(sdd_text)

# An UNFILLED § 3 still parses. `sdd_template.md`'s own placeholder row is a well-formed table row,
# so "the table exists" is not the same question as "the table was written". Taken at face value it
# makes a directory literally named `<slug>` inside one named after a whole guidance sentence — on a
# product whose § 3 nobody has filled in. An angle-bracketed cell is the template still speaking.
#
# THIS CHECK NO LONGER DECIDES LEGALITY — IT ONLY DECIDES WHICH REFUSAL YOU GET. Both columns are
# whitelisted below (the slug immediately after this, `Lives in` further down), so anything this
# misses is still refused. What it buys is the message: "you have not filled in the template" is a
# different problem from "your slug is malformed", and it is fixed in a different place. Running
# first, it takes the rows it can name precisely and leaves the rest to the whitelist.
#
# Because it decides nothing, it matches ANYWHERE in a cell rather than over the whole of it. The
# fullmatch it used to do split the template's own row in two: `<slug>` was caught and `<slug>-unit`
# — the same unfilled row with one word typed into it — was not, and became a real directory. No
# legal value of either column can contain `<`, so widening this costs nothing it was protecting.
#
# This is the parts-table twin of the unknown-token scan further down: that one guards what is copied
# OUT of a tree, this one guards what is read IN from a document, and neither covers the other's
# ground.
placeholder_parts = [
    (slug, lives_in)
    for slug, lives_in in parts
    if re.search(r"<[^>]+>", slug) or re.search(r"<[^>]+>", lives_in or "")
]
if placeholder_parts:
    shown = ", ".join(f"`{slug}`" for slug, _ in placeholder_parts[:3])
    die(
        f"{sdd_path}: § 3's parts table still carries the template's placeholder rows ({shown}) — "
        "it parses, but nobody has filled it in. Write the product's real parts before running this, "
        "or the skeleton is named after the template rather than the design."
    )

# The part slug BECOMES A DIRECTORY NAME, verbatim, so its form is load-bearing in exactly the way
# `Lives in`'s is — and it is enforced the same way, by a stated legal shape with everything else
# refused. A blacklist here could only ever refuse the shapes someone thought to list: it caught the
# template's `<slug>` row and passed `P-1`, `the connect unit` and `Connect_Unit` straight through
# into real directories at exit 0.
#
# The shape is the template's, not this script's: `sdd_template.md` § 3 — "Lowercase letters and
# digits, single hyphens between them, and nothing else". Digits are in because the template states
# them; inventing a stricter shape than the contract states would refuse a legal SDD. What this
# CANNOT see is that a slug names a position rather than a thing — `P-1` is refused for its capital,
# but a lowercase `p-1` is a well-formed slug and passes. § 3 says so in the same paragraph: that
# half stays a rule for the author, not for this script.
#
# IT RUNS ON THE RAW CELL, AND IT SITS ABOVE THE `Package slug:` READ SO THAT IT CANNOT DO OTHERWISE
# — `substitute()` does not exist yet at this line. That asymmetry with `Lives in` (which IS checked
# substituted) is deliberate and follows the code: the part directory is built from the raw slug
# (`rel_dir = f"{lives_sub}/{slug}"`), never a substituted one, so a `__PROJECT__` in this column
# would land as a directory literally called `__PROJECT__-core`. `Lives in` may legitimately name a
# package after the product; the slug names a part, and no part is named after the whole product.
PART_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
bad_slugs = [slug for slug, _lives_in in parts if not PART_SLUG_RE.fullmatch(slug)]
if bad_slugs:
    shown = "; ".join(repr(slug) for slug in bad_slugs[:3])
    die(
        f"{sdd_path}: § 3's `Part` column must be a slug — lowercase letters and digits in "
        f"kebab-case, single hyphens between them and nothing else. These are not ({shown}). "
        "A positional label (`P-1`, `C-3`), a capital, a space, an underscore, a dot, or a "
        "leftover `__PROJECT__` all fail here — the cell becomes a directory name exactly as "
        "written, and it is never substituted. The shape is stated in "
        "`core/templates/product-templates/sdd_template.md` § 3."
    )


# --- Package slug: supplies the __PROJECT__ substitution value -----------------------------------
package_slug = read_field(card_text, "Package slug")
if not package_slug:
    die(f"{project_md}: no 'Package slug:' line — it supplies the __PROJECT__ substitution value")


def substitute(text):
    return text.replace("__PROJECT__", package_slug)


def substitute_unit(text, unit_path):
    unit_name = os.path.basename(unit_path.rstrip("/")) or package_slug
    return substitute(text).replace("__UNIT__", unit_name)

# `Lives in` is JOINED TO A SLUG TO MAKE A REAL DIRECTORY, so its value form is load-bearing and
# this is the only place that can enforce it. A settled SDD written before the template fixed the
# form carries prose there — one real cell read "`app-core`, behind the **Sync port**", which
# becomes a directory of that name, punctuation and all, at exit 0. And a cell climbing out of the
# product root with `..` writes wherever it points, which is the same defect with a worse ending.
#
# A bare, product-root-relative path with no `..` and no leading `/`. Empty is fine and means the
# part sits at the product root. Anything else is refused with the cell shown, because the fix is
# in the SDD and the author needs to see what their cell actually says.
LIVES_IN_RE = re.compile(r"^[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*$")


def is_bare_relative_path(path):
    """True when path is one bare value relative to the product root: it matches LIVES_IN_RE and
    no segment of it is a parent reference. The one rule for Lives in, Language roots and units."""
    return bool(LIVES_IN_RE.fullmatch(path)) and ".." not in path.split("/")


malformed = [
    (slug, lives_in)
    for slug, lives_in in parts
    if substitute(lives_in or "").strip()
    and not is_bare_relative_path(substitute(lives_in).strip())
]
if malformed:
    shown = "; ".join(f"`{slug}` → {substitute(lives_in).strip()!r}" for slug, lives_in in malformed[:3])
    die(
        f"{sdd_path}: § 3's `Lives in` column must be a bare path relative to the product root — "
        f"one value, no `..`, no leading `/`, no prose and no markup. These are not ({shown}). "
        "The column is joined to the part's slug to make a directory, so anything else becomes a "
        "directory name with the punctuation in it, or writes outside the product entirely."
    )

# A PRE-UNITS SDD still takes `Language roots:` as its migration path: a language not named there
# lands at the product root, preserving every product written before the units table existed. Its
# grammar is `Lives in`'s, deliberately —
# both columns place something relative to the product root under the same constraints, and a second
# grammar is a second thing for an author to get wrong. `.` is accepted and means the product root,
# so a card may state the default explicitly.
#
# IT IS REFUSED HERE, above every write, for the same reason `Lives in` is: the value is joined to a
# copied file's relative path to make a real destination, so a cell with `..` in it writes outside the
# product and a cell with prose in it makes a directory with the punctuation in the name.
#
# A language named here that the card does not declare is refused too. It is always a mistake — a
# typo, or a language removed from `Languages:` and left behind here — and silently ignoring it means
# the frame lands at the root while the card says otherwise, which is exactly the defect this field
# exists to end.
language_roots = {}
roots_raw = read_field(card_text, "Language roots")
if roots_raw and units is None:
    malformed_roots = []
    for entry in [e.strip() for e in roots_raw.split(",") if e.strip()]:
        name, sep, dest = entry.partition("=")
        name = name.strip()
        dest = dest.strip().strip("/")
        if not sep or not name:
            malformed_roots.append((entry, "not a `<language>=<path>` pair"))
            continue
        if dest in ("", "."):
            language_roots[name] = ""
            continue
        if not is_bare_relative_path(dest):
            malformed_roots.append((entry, "not a bare product-root-relative path"))
            continue
        language_roots[name] = dest
    if malformed_roots:
        shown = "; ".join(f"{entry!r} — {why}" for entry, why in malformed_roots[:3])
        die(
            f"{project_md}: `Language roots:` must be `<language>=<path>` pairs, comma-separated, "
            f"each path bare and relative to the product root with no `..` and no leading `/`. "
            f"These are not ({shown}). The value is joined to every file the language's frame "
            "carries, so anything else lands the frame somewhere the card does not say."
        )
    unknown = [name for name in language_roots if name not in languages]
    if unknown:
        die(
            f"{project_md}: `Language roots:` names {', '.join(repr(n) for n in unknown[:3])}, which "
            f"`Languages:` does not declare. A root for a language this product does not have places "
            "nothing, and is always a typo or a language removed from one line and left on the other."
        )

# A current SDD's units table is the complete build plan. Older settled SDDs have no such table and
# retain the card's legacy `Language roots:` path above so they remain runnable during migration.
scoped_units = []


def kind_tree_for(language, kind):
    language_tree = os.path.join(templates_root, language.lower())
    scoped = os.path.join(language_tree, kind)
    if os.path.isdir(scoped):
        return scoped
    if kind == "crate":
        legacy_crate = os.path.join(language_tree, "crates", "__PROJECT__")
        if os.path.isdir(legacy_crate):
            return legacy_crate
    if kind == "package" and os.path.isdir(language_tree):
        return language_tree
    return scoped


if units is not None:
    if not units:
        die(f"{sdd_path}: § 3's units table has no rows")
    seen_units = set()
    for raw_unit, language, kind in units:
        unit = substitute(raw_unit).strip().strip("/")
        if unit and not is_bare_relative_path(unit):
            die(f"{sdd_path}: unit path {raw_unit!r} must be bare and relative to the product root")
        if unit in seen_units:
            die(f"{sdd_path}: § 3's units table names {unit!r} more than once")
        seen_units.add(unit)
        if language != "none" and language not in languages:
            die(f"{sdd_path}: unit {unit!r} names language {language!r}, which the project card does not declare")
        if kind not in {"crate", "package", "module root", "directory"}:
            die(f"{sdd_path}: unit {unit!r} has unknown Kind {kind!r}")
        if kind in {"crate", "package"} and language == "none":
            die(f"{sdd_path}: buildable unit {unit!r} has Kind {kind!r} but no language")
        scoped_units.append((unit, language, kind))

    lives_units = {substitute(lives or "").strip().strip("/") for _slug, lives in parts}
    missing = sorted(lives_units - seen_units)
    extra = sorted(seen_units - lives_units)
    if missing or extra:
        details = []
        if missing:
            details.append("missing units for " + ", ".join(repr(path) for path in missing))
        if extra:
            details.append("units with no `Lives in` value: " + ", ".join(repr(path) for path in extra))
        die(f"{sdd_path}: § 3 requires one unit per distinct `Lives in` value — {'; '.join(details)}")

    for unit, language, kind in scoped_units:
        if kind not in {"crate", "package"}:
            continue
        kind_tree = kind_tree_for(language, kind)
        if not os.path.isdir(kind_tree):
            die(f"no {kind} skeleton for language {language!r} — looked for {kind_tree}")
# --- phase 1: validate + plan every write, for every language, before anything is written ------
#   `claimed_by` makes the never-overwrite guarantee hold ACROSS trees as well as against the
#   product. Two declared languages claiming the same product-root path is the ordinary
#   multi-language case, not a defect — five of the six real trees carry a `.gitignore` of their
#   own — so the first language on the card wins and the later one is reported, exactly as a file
#   already present in the product is. It is not fatal: the plan enumerates every refusal this
#   launcher raises, and a collision is not among them.
lang_reports = []          # ("copy" | "skip", language)
files_to_write = []        # (relpath, content)
files_skipped_existing = []
files_skipped_claimed = []  # (relpath, the language that placed it first)
frames_left_built = []      # (where the frame would land, language, the first of its files already there)
claimed_by = {}             # relpath -> that language
GITIGNORE = ".gitignore"
# Read by the bash half out of this run's captured stdout, then stripped before the owner sees it.
MARKER_PATH = "__SKELETON_PATH__"
MARKER_SUMMARY = "__SKELETON_SUMMARY__"
gitignore_sources = []      # (language, that tree's .gitignore text), in card order


def plan_tree(tree_dir, lang, destination="", unit_path=None, excluded_top_dirs=()):
    entries = []
    for root, dirs, files in os.walk(tree_dir):
        if root == tree_dir:
            dirs[:] = [d for d in dirs if d not in excluded_top_dirs]
        for fname in files:
            entries.append(os.path.join(root, fname))
    non_readme = [p for p in entries if os.path.relpath(p, tree_dir) != "README.md"]
    if not non_readme:
        return "skip"
    planned = []
    for src in sorted(non_readme):
        rel = os.path.relpath(src, tree_dir)
        with open(src, encoding="utf-8") as fh:
            content = fh.read()
        if unit_path is None:
            rel_sub = substitute(rel)
            content_sub = substitute(content)
        else:
            language_tree = os.path.join(templates_root, lang.lower())
            legacy_unit_tree = tree_dir == language_tree or os.path.basename(tree_dir) == "__PROJECT__"
            if legacy_unit_tree:
                unit_name = os.path.basename(unit_path.rstrip("/")) or package_slug
                rel_sub = rel.replace("__PROJECT__", unit_name).replace("__UNIT__", unit_name)
                content_sub = content.replace("__PROJECT__", unit_name).replace("__UNIT__", unit_name)
            else:
                rel_sub = substitute_unit(rel, unit_path)
                content_sub = substitute_unit(content, unit_path)
        if rel_sub == GITIGNORE:
            gitignore_sources.append((lang, reanchor_gitignore(content_sub, destination)))
            continue
        rel_sub = f"{destination}/{rel_sub}" if destination else rel_sub
        planned.append((rel_sub, content_sub))
    # A frame is placed whole or not at all: one of its files already in the product means the frame
    # was placed before or code was built over it, and the rest of it would land inside that code.
    # A `.gitkeep` is not evidence: several trees ship the same one (`tests/e2e/.gitkeep`), so another
    # language's frame at the same root would make this one look built.
    built = [
        rel
        for rel, _content in planned
        if os.path.basename(rel) != ".gitkeep" and os.path.exists(os.path.join(product_path, rel))
    ]
    if built:
        files_skipped_existing.extend(built)
        frames_left_built.append((destination or ".", lang, built[0]))
        return "built"
    for rel_sub, content_sub in planned:
        if rel_sub in claimed_by:
            files_skipped_claimed.append((rel_sub, claimed_by[rel_sub]))
        else:
            claimed_by[rel_sub] = lang
            files_to_write.append((rel_sub, content_sub))
    return "copy"


if units is None:
    for lang in languages:
        tree_dir = os.path.join(templates_root, lang.lower())
        if not os.path.isdir(tree_dir):
            die(f"no skeleton tree for language '{lang}' — looked for {tree_dir}")
        lang_reports.append((plan_tree(tree_dir, lang, language_roots.get(lang, "")), lang))
else:
    scoped_languages = []
    for _unit, language, _kind in scoped_units:
        if language != "none" and language not in scoped_languages:
            scoped_languages.append(language)
    for lang in scoped_languages:
        product_tree = os.path.join(templates_root, lang.lower(), "product")
        if os.path.isdir(product_tree):
            plan_tree(product_tree, lang)
        else:
            language_tree = os.path.join(templates_root, lang.lower())
            legacy_crate = os.path.join(language_tree, "crates", "__PROJECT__")
            if os.path.isdir(legacy_crate):
                plan_tree(language_tree, lang, excluded_top_dirs=("crates",))
    for unit, language, kind in scoped_units:
        if kind in {"crate", "package"}:
            outcome = plan_tree(kind_tree_for(language, kind), language, unit, unit)
            lang_reports.append((outcome, f"{language} {kind} at {unit}"))

# --- .gitignore: the product's own file is kept whole, and what it lacks is appended -------------
#
# Every declared language contributes. The product's file leads, byte for byte; each tree's missing
# entries follow in card order under a block that names where they came from. An entry already
# present contributes nothing, which is what makes a re-run leave the file byte-identical.
gitignore_plan = None          # (existing_text, [(lang, [entries…]), …]) or None when nothing to do
if gitignore_sources:
    gitignore_path = os.path.join(product_path, GITIGNORE)
    if os.path.exists(gitignore_path):
        with open(gitignore_path, encoding="utf-8") as fh:
            base = fh.read()
    else:
        base = ""

    def entries_of(text):
        """The lines that are rules. A comment describes the tree it came from, not the product's
        file, so it does not travel; a blank line carries nothing."""
        out = []
        for raw in text.splitlines():
            line = raw.strip()
            if line and not line.startswith("#"):
                out.append(line)
        return out

    have = set(entries_of(base))
    additions = []
    for lang, content in gitignore_sources:
        missing = []
        for entry in entries_of(content):
            if entry not in have:
                have.add(entry)
                missing.append(entry)
        if missing:
            additions.append((lang, missing))
    if additions:
        gitignore_plan = (base, additions)

# --- legacy part directories, or current directory/module-root units -----------------------------
part_dirs_to_create = []
part_dirs_skipped_existing = []
if units is None:
    directories = [
        f"{substitute(lives_in).strip('/')}/{slug}" if substitute(lives_in).strip("/") else slug
        for slug, lives_in in parts
    ]
else:
    directories = [unit for unit, _language, kind in scoped_units if kind in {"module root", "directory"}]
for rel_dir in directories:
    if os.path.isdir(os.path.join(product_path, rel_dir)):
        part_dirs_skipped_existing.append(rel_dir)
    else:
        part_dirs_to_create.append(rel_dir)

# Git holds no empty directory, and a part directory is empty by construction — so a part gets a
# `.gitkeep`, the same answer the language trees already give their own empty directories. Only
# where it is needed: a part that already holds content is tracked by it, and a part this run is
# about to write a file into will be tracked by that.
about_to_hold = {os.path.dirname(relpath) for relpath, _content in files_to_write}
for rel_dir in part_dirs_to_create + part_dirs_skipped_existing:
    abs_dir = os.path.join(product_path, rel_dir)
    if os.path.isdir(abs_dir) and os.listdir(abs_dir):
        continue
    if rel_dir in about_to_hold:
        continue
    keep = f"{rel_dir}/.gitkeep"
    if keep in claimed_by:
        files_skipped_claimed.append((keep, claimed_by[keep]))
    else:
        claimed_by[keep] = "parts"
        files_to_write.append((keep, ""))


def ancestors(relpath):
    out = []
    d = os.path.dirname(relpath)
    while d and d not in (".", ""):
        out.append(d)
        d = os.path.dirname(d)
    return out


dirs_needed = set()
for relpath, _content in files_to_write:
    for d in ancestors(relpath):
        if not os.path.isdir(os.path.join(product_path, d)):
            dirs_needed.add(d)
for rel_dir in part_dirs_to_create:
    if not os.path.isdir(os.path.join(product_path, rel_dir)):
        dirs_needed.add(rel_dir)
    for d in ancestors(rel_dir):
        if not os.path.isdir(os.path.join(product_path, d)):
            dirs_needed.add(d)

# --- language reports print in both modes -------------------------------------------------------
for kind, lang in lang_reports:
    if kind == "skip":
        print(f"{lang}: README-only skeleton — skipped")
for where, lang, found in frames_left_built:
    print(f"{lang} frame at {where}: already built ({found} is there) — none of it is placed")

def render_gitignore(base, additions):
    """The product's file whole, then one titled block per contributing language."""
    out = base
    if out and not out.endswith("\n"):
        out += "\n"
    for lang, entries in additions:
        out += f"\n# Added by the product-skeleton launcher — what the {lang} toolchain generates\n"
        out += "".join(f"{entry}\n" for entry in entries)
    return out


# --- phase 2: apply, or list under --dry-run ----------------------------------------------------
if dry_run:
    print("DRY RUN — would create:")
    for relpath, _content in sorted(files_to_write):
        print(f"  file: {relpath}")
    for rel_dir in sorted(dirs_needed):
        print(f"  dir: {rel_dir}")
    for where, _lang, _found in frames_left_built:
        print(f"  already built (skip): {where}")
    for relpath in sorted(files_skipped_existing):
        print(f"  exists (skip): {relpath}")
    for relpath, owner in sorted(files_skipped_claimed):
        print(f"  placed by the {owner} tree (skip): {relpath}")
    for rel_dir in sorted(part_dirs_skipped_existing):
        print(f"  exists (skip): {rel_dir}")
    if gitignore_plan:
        _base, additions = gitignore_plan
        verb = "would append to" if _base else "would create"
        for lang, entries in additions:
            print(f"  {verb} {GITIGNORE}: {len(entries)} from the {lang} tree: {', '.join(entries)}")
    elif gitignore_sources:
        print(f"  {GITIGNORE}: already carries every entry the declared languages need")
    sys.exit(0)

for kind, lang in lang_reports:
    if kind == "copy":
        print(f"Copied {lang} tree.")

for relpath, content in files_to_write:
    dest = os.path.join(product_path, relpath)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(content)
if gitignore_plan:
    base, additions = gitignore_plan
    with open(os.path.join(product_path, GITIGNORE), "w", encoding="utf-8") as fh:
        fh.write(render_gitignore(base, additions))
    for lang, entries in additions:
        verb = "Appended to" if base else "Wrote"
        print(f"{verb} {GITIGNORE}: {len(entries)} entry(s) from the {lang} tree: {', '.join(entries)}")
elif gitignore_sources:
    print(f"{GITIGNORE}: already carries every entry the declared languages need — untouched")

for relpath in files_skipped_existing:
    print(f"{relpath}: already exists — skipped")
for relpath, owner in files_skipped_claimed:
    print(f"{relpath}: already placed by the {owner} tree — skipped")

for rel_dir in part_dirs_to_create:
    os.makedirs(os.path.join(product_path, rel_dir), exist_ok=True)
    print(f"Created {rel_dir}/")
for rel_dir in part_dirs_skipped_existing:
    print(f"{rel_dir}: already exists — skipped")

# --- what this run actually changed, for the commit the shell makes next ------------------------
# Paths only, one per line: every file written plus `.gitignore` when it was combined. A part
# directory needs no line of its own — the `.gitkeep` inside it is what git can hold, and a part
# that got no marker was one a written file already lands in.
touched = [relpath for relpath, _content in files_to_write]
if gitignore_plan:
    touched.append(GITIGNORE)
for relpath in sorted(touched):
    print(f"{MARKER_PATH} {relpath}")

langs_copied = [lang for kind, lang in lang_reports if kind == "copy"]
print(
    f"{MARKER_SUMMARY} {len(files_to_write)} files and {len(part_dirs_to_create)} "
    f"part directories, from: {', '.join(langs_copied) if langs_copied else 'no tree'}"
)
PYEOF
} | {
# --- the run commits, through the one builder ----------------------------------------------------
#   Nothing else was going to. Every sibling launcher spawns an agent that commits its own work;
#   this one spawns nothing, so the tree it wrote sat uncommitted until someone remembered — which
#   is exactly what happened on the first two live runs (2026-09-03).
#
#   THROUGH THE BUILDER, NEVER `git commit`. `<CORE>/tools/commit_builder.py` is the one place a
#   commit's trailer block is constructed (`commit_format.md`), and it stages what it is told to
#   stage. Two of its values are this launcher's own: `Surface: product-skeleton`, and NO
#   `Co-Authored-By:` at all — no model authored these bytes, and the absence says so.
#
#   WHY A PIPE AND NOT `$(...)`. The Python half hands back the paths it wrote as marker-prefixed
#   lines, and bash must read them without writing a scratch file (the bash half creates nothing).
#   The obvious shape — capturing the heredoc in a command substitution — is a LANDMINE: inside
#   `$( )` or `<( )` bash keeps parsing the quoted heredoc body and chokes on an ODD number of
#   backticks in it, which the Python half's own comments carry (97 of them, 2026-09-03). It passes
#   `bash -n` and fails only at runtime, with "bad substitution: no closing )". A pipe off a brace
#   group does no such re-parse. macOS ships bash 3.2, so there is no `lastpipe` and no `mapfile`:
#   the right-hand side is a subshell, which is why the commit happens INSIDE it rather than
#   collecting paths for a parent that would never see them.
#
#   THE COMMIT NEVER COSTS THE RUN ITS TREE. Writing the skeleton is the job; committing it is
#   bookkeeping on top. A product that is not a git repo yet, or a builder that refuses because
#   someone else's work is already staged, is reported and the run still succeeds — the files are on
#   disk either way, and failing here would tell the owner nothing was written when everything was.
paths=()
summary=""
while IFS= read -r line; do
  case "$line" in
    "__SKELETON_PATH__ "*)    paths+=("${line#__SKELETON_PATH__ }") ;;
    "__SKELETON_SUMMARY__ "*) summary="${line#__SKELETON_SUMMARY__ }" ;;
    *)                        printf '%s\n' "$line" ;;
  esac
done

# No markers means the Python half wrote nothing — a refusal, a --dry-run, or a re-run that found
# everything already in place. Each is silent here; the refusal's own message already went to stderr.
[ ${#paths[@]} -gt 0 ] || exit 0

if ! git -C "$product_path" rev-parse --git-dir >/dev/null 2>&1; then
  echo "product-skeleton: $product_path is not a git repository — ${#paths[@]} paths written, not committed."
  exit 0
fi

# One flag, every path — `--add` carries action=extend, so the whole set rides one flag.
if ! python3 "$CORE_DIR/tools/commit_builder.py" --repo "$product_path" commit \
    --add "${paths[@]}" \
    --subject "skeleton: $summary" \
    --body "Written by <CORE>/launchers/product-skeleton/launcher.sh, run by the owner after the foundation step settled. No model ran: language frames are copied from <CORE>/templates/skeleton-templates/, and the product's own SDD section 3 determines each unit's path, language and kind." \
    --role "Product" \
    --directional "Agari: $project — progress: the product has the frame its declared languages call for and a directory per part its SDD names" \
    --surface "product-skeleton"; then
  echo "product-skeleton: the tree is written; the commit did not land (see above). Nothing was lost — commit it yourself." >&2
fi
}

# The Python half's exit status, not the subshell's — a refusal must still refuse.
skeleton_status=${PIPESTATUS[0]}
[ "$skeleton_status" -eq 0 ] || exit "$skeleton_status"
