---
version: "1.0.0"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->
<!-- The single source of a product changelog's shape. Lands at `<Product path>/CHANGELOG.md`.

     MODEL-FACING: whoever writes or edits a product's changelog reads this shape and writes the file
     fresh, so everything here may explain itself and none of it survives into the result. No script
     stamps it.

     WHAT THIS FILE OWNS: the file's headings, its groups and the shape of one entry. Nothing else.
     Where the file sits, what earns an entry, which project an entry names, which root files are
     logged where, and what happens to the entries at a release cut are
     `<CORE>/doctrine/setup/kensaiapp_structure.md` § 3 Product, *The changelog — one file per
     product path records what changed for a user of a fresh clone*. They are not restated here.

     THE FORMAT is Keep a Changelog 1.1.0 (https://keepachangelog.com/en/1.1.0/), with one group
     added. The file opens with an H1 heading and its lead sentences. `## [Unreleased]` is always the
     first `## ` heading. Each release the product has cut follows it, newest first, under a heading
     of the form `## [<version>] - <YYYY-MM-DD>`, with the date written as year, month and day.

     THE GROUPS are a closed set of seven `### ` headings. Under a release heading they are written
     in this order:

         ### Upgrading
         ### Added
         ### Changed
         ### Deprecated
         ### Removed
         ### Fixed
         ### Security

     `### Upgrading` holds a change a clone must act on to keep working, and it comes first whenever
     it is present. The other six are Keep a Changelog's own. No other group heading is used.

     A GROUP IS WRITTEN ONLY WHERE IT HOLDS AN ENTRY. A product's file carries no empty group heading.
     An `## [Unreleased]` with no entries is the heading alone.

     ONE ENTRY is one Markdown list item, `- `, under a group. It begins with the one project it
     names, in bold: a folder name under `system/projects/<name>/`. Then comes ` — `, then the change
     as its user meets it, in one or more short sentences. It ends with the commits that made the
     change, in parentheses: each an abbreviated SHA of at least 9 hex digits in an inline code span,
     separated by commas. One entry may cite every commit of one change. An entry names exactly one
     project, so a change made under two projects is two entries. A made-up entry, shown for its
     form only:

         - **example-project** — The `build` launcher prints its usage line when it is given no argument. (`1a2b3c4d5`, `6e7f8a9b0`)

     THE BODY BELOW IS AN ILLUSTRATION, not a product's history. Each placeholder entry stands for
     any number of real ones, and a real file writes only the groups its entries need. The release
     heading shows the form a cut release takes. A product's file carries no release heading until
     the product has cut one, so a first changelog holds `## [Unreleased]` and nothing below it. -->

# Changelog — `<product path>`

Each entry records a change to what a user of a fresh clone installs, runs, types or reads in <what this file covers>. It names the project the change was made under and cites the commits that made it. The format follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Upgrading

- **<project>** — <what a clone must install, re-run or type differently, and how to do it>. (`<commit>`)

### Added

- **<project>** — <the change, as its user meets it>. (`<commit>`, `<commit>`)

## [<version>] - <YYYY-MM-DD>

### Changed

- **<project>** — <the change, as its user meets it>. (`<commit>`)
