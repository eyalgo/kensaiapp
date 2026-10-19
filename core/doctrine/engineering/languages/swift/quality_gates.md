---
version: "1.1.0"
---

# Swift — quality gates

The checks that must pass, each with the command that runs it and the file that configures it. A rule
no tool can fail the build on is not a gate and is not here. It is in `conventions.md`.

## The gates

| Gate | Tool | Config file | When |
|---|---|---|---|
| Format and lint | swift-format, shipped in the toolchain | `.swift-format` | every change |
| Types | the Swift compiler, through SwiftPM | `Package.swift`: the tools version, `swiftLanguageModes`, and the two settings in § Types | every change |
| Link | the linker, through SwiftPM (Apple platforms) | `Package.swift`, and how any linked library was built (`toolchain.md` § *Linking a C library built by another toolchain*) | every change |
| Dependency claim | SwiftPM's manifest dump, read by `jq` | `Package.swift` | every change, in a product that declares no dependencies |

Each command below runs with the package root as its working directory. The commands sit in fenced
blocks, not in the table, so that what a run copies out of this file is the command itself: a
pipeline in a table cell has its `|` escaped as `\|`, and measured 2026-09-23 such a line run from
the file's source failed (`swift package dump-package` answered `Unknown option '-e'`, exit `64`).

**Format and lint:**

```sh
test ! -e Packages && swift format lint --strict --parallel --recursive .
```

**Types:**

```sh
swift build --build-tests --explicit-target-dependency-import-check error
```

**Link**, on Apple platforms:

```sh
swift build -c release -Xlinker -fatal_warnings
```

**Dependency claim:**

```sh
swift package dump-package | jq -e '(.dependencies | length) + ([.targets[] | select(.url != null or .type == "system")] | length) == 0' > /dev/null && test ! -e Package.resolved
```

**None of them is run from a parent directory with a path argument**, for two measured reasons:
swift-format has no `--package-path` option (`swift format lint --package-path <dir>` exits `64` with
`Unknown option`), and `test ! -e Package.resolved` looks in the working directory whatever `swift
package` was pointed at. The format gate runs before the type gate, because a reformatting diff
mixed into a type fix hides the fix.

**In a package with dependencies, the type and link gates also carry `--force-resolved-versions`**,
as every SwiftPM command in its CI does (`toolchain.md` § *Adding, pinning and locking a
dependency*), and the dependency-claim gate does not run.

**The type gate needs Xcode's toolchain or a swift.org one**, because `--build-tests` compiles
`import Testing`, which the Command Line Tools alone cannot (`toolchain.md` § *Toolchain version*).

**The dependency-claim gate ends in `jq -e`, not in a numeric `test`, so a missing tool fails it.**
`jq -e` exits non-zero when the expression is false and when it gets no input (`4`, measured
2026-09-23 on empty input), and a missing `jq` is a command-not-found. The obvious spelling,
`test "$(… | jq '… | length')" -eq 0`, does not fail closed: measured 2026-09-23, zsh's `test "" -eq
0` exits `0`, while bash and sh exit `2`. Under zsh an empty result — no `jq`, or a failed `dump-package`
— would pass the gate.

**What no gate checks: that every target carries the two manifest settings of § Types,
unconditionally.** No gate over the manifest dump checks it, because a gate that is right about it
is not simple: it would have to read
each setting's `.when(…)` condition, a per-group `.treatWarning(_:as: .warning)` downgrade, C and
C++ targets, macro targets, array-valued settings such as `.unsafeFlags`, and a list of targets a
product's `docs/adr/` relaxes on purpose. The rule stands as a reader's rule in `conventions.md`, and
a manifest review checks it.

swift-format ships in the toolchain (§ *Format and lint*). `jq` does not; on the Mac these gates
were measured on it is `/usr/bin/jq`, part of the operating system, and anywhere else a product's CI
image installs it. Nothing here is a package dependency.

## Format and lint — swift-format

**One tool is both gates, because swift-format's lint mode reports formatting and rule violations
together.** Its `lint` subcommand "checks one or more Swift source files… for style violations", and
`-s/--strict` makes "lint warnings… cause the tool to exit with a non-zero exit code (failure)"
(https://github.com/swiftlang/swift-format/blob/main/README.md). The formatting half is measured, not
assumed. On 2026-09-23, `swift format lint --strict` over a stamped Swift skeleton (4-space
indentation) under the tool's default configuration reported `[Indentation]` errors and exited `1`.

**The gate lints `.`, because swift-format passes a path that does not exist.** Measured 2026-09-23:
`swift format lint --strict --recursive Nonexistent` exited `0` with no output, although the README
says a fatal error such as "trying to lint a file that does not exist" makes the tool exit
unsuccessfully (same page). A gate that listed `Sources Tests` would pass green when run from the
wrong directory or with a mistyped path, and would never see a `Plugins/` or `Snippets/` directory.
With `.`, every Swift file under the package root is linted: the same run over a package holding a
badly named constant in `Plugins/P/p.swift` exited `1`, and one in `.build/x/` or `.hidden/` was not
reported, so hidden directories — `.build` among them — are skipped. `Packages/` is not hidden, and
it is where `swift package edit` puts a dependency being edited, so `.` would lint that third
party's code; measured 2026-09-23, a bad constant in `Packages/Q/q.swift` failed the plain lint. The
gate therefore refuses to run while `Packages/` exists: with the directory present the command
exits `1`, and without it `0` on a clean package (measured the same day). Editing a dependency in
place is a local, temporary state, and the gate is run after it ends.

**`swift format --in-place --recursive .` fixes the formatting half, and only that half.** `-i` /
`--in-place` "Overwrites the input files when formatting" (same page). Measured 2026-09-23: after it,
a `public let Bad_Name = 1` still failed the gate with `[AlwaysUseLowerCamelCase]`. A rule finding is
fixed by hand.

**It ships with the toolchain, so the packet names no second formatter and no separate linter.**
"Swift 6 (included with Xcode 16) and above include swift-format in the toolchain. You can run
`swift-format` from anywhere on the system using `swift format`" (same page). **Taking swift-format
for both is the packet author's call, 2026-09-23.** The ground is that it is the only choice with
nothing to install and pin: every toolchain that can build the package already carries the version
of the formatter that matches it. The alternatives each add one. SwiftLint is installed with `brew
install swiftlint`, Mint, a `.pkg` or Docker, or as a package dependency through
`.package(url: "https://github.com/SimplyDanny/SwiftLintPlugins", …)`
(https://github.com/realm/SwiftLint/blob/main/README.md), and the package route also breaks the
packet's zero-dependency default (`toolchain.md`). SwiftFormat is installed with `brew install
swiftformat` (https://github.com/nicklockwood/SwiftFormat/blob/main/README.md). A product that wants
SwiftLint's rule set records it in its own `docs/adr/`, with how the tool is installed.

**`.swift-format` is committed, and it departs from the tool's defaults in one setting,
`indentation.spaces: 4`.** swift-format reads "a JSON-formatted file named `.swift-format`", looking
in the file's own directory and then upward, and falls back to a default configuration when none is
found (same README). The default indents by 2 (`swift format dump-configuration`, measured
2026-09-23). The code the toolchain itself generates indents by 4: `swift package init` writes a
4-space `Package.swift`, and The Swift Programming Language's examples are 4-space
(https://github.com/swiftlang/swift-book/blob/main/TSPL.docc/LanguageGuide/ErrorHandling.md).
Measured 2026-09-23 on a fresh `swift package init --type library`: under the default configuration
the lint reported 23 `[Indentation]`, 2 `[LineLength]` and 1 `[TrailingComma]` findings; under the
committed `.swift-format`, only the `[TrailingComma]` one, which `swift format --in-place` fixes. At
4 the house style agrees with the code the toolchain and the book write; at 2 every indented line
would be reformatted. **Setting it to 4 is the packet author's call, 2026-09-23**, on that ground. Every other setting stays at the tool's default,
including `lineLength: 100`. The tool makes no claim that its defaults are a standard: "No default
Swift code style guidelines have yet been proposed. The style that is currently applied by
`swift-format` is just one possibility" (same README). They are taken because they are one written
answer rather than none. A product that departs on another setting adds it to its own
`.swift-format`, and the file then shows the departure as a diff.

## Types — the compiler, with warnings as errors

Swift's type checker is the compiler, so the type gate is a build. `--build-tests` extends it over
the test targets, which are otherwise unchecked code that later gets copied into product code. **The
build also enforces two rules that live in the manifest**, warnings as errors and strict memory
safety, and **one that lives on the gate's command line**, the import check. The two manifest
settings are this file's because they are the type gate's configuration; which targets carry them
is a manifest rule in `conventions.md`.

**Warnings are errors, and the level is set in the manifest, on every target.** SE-0480 gave SwiftPM
`.treatAllWarnings(as: .error)`. Before it, controlling warnings forced "developers to either use
`unsafeFlags` or accept the default warning settings"
(https://github.com/swiftlang/swift-evolution/blob/main/proposals/0480-swiftpm-warning-control.md).
The Swift setting is "equivalent to passing `-warnings-as-errors`… to the Swift compiler", and it
exists separately for C and C++ targets, "equivalent to passing `-Werror`"
(https://github.com/swiftlang/swift-package-manager/blob/swift-6.3.3-RELEASE/Sources/Runtimes/PackageDescription/BuildSettings.swift).
So a Swift target carries it in `swiftSettings`, a C target in `cSettings`, and a C++ target in
`cxxSettings`. Measured
2026-09-23: a C target's `if (x = 2)` built with a warning, and with `cSettings:
[.treatAllWarnings(as: .error)]` it failed with `error: … [-Werror,-Wparentheses]`.
**Putting it in the manifest rather than on the gate's command line is the packet author's call,
2026-09-23.** The ground is that the manifest is read by every build: the gate's, a developer's plain
`swift build`, and a CI's `swift build -c release`. A level that lives only in one command is skipped
by every other command. The setting does not reach code the product does not own. For a target
pulled from a dependency, SwiftPM "will strip all of the warning control flags… and substitute them
with options for suppressing warnings" (SE-0480, § Remote targets behavior). It also stays
overridable for one run, because `-Xswiftc` flags "are appended **after** the flags generated from
the package manifest" (SE-0480, § Interaction with command-line flags). **Because the setting is per
target, a target added without it is ungated**, and no gate here catches that (§ The gates).

**Strict memory safety is on for every Swift target, and that is the packet author's call,
2026-09-23.** SE-0458 makes it "an opt-in strict memory safety checking mode that identifies all uses
of unsafe behavior within the given module", reported as warnings in the `StrictMemorySafety` group
(https://github.com/swiftlang/swift-evolution/blob/main/proposals/0458-strict-memory-safety.md), and
SwiftPM spells it `.strictMemorySafety()` (`BuildSettings.swift`, above). Combined with warnings as
errors, an unmarked unsafe use fails the build. Measured 2026-09-23: `p.pointee` on an
`UnsafePointer<Int>` failed with `error: expression uses unsafe constructs but is not marked with
'unsafe' [#StrictMemorySafety]`, and `unsafe p.pointee` built. The ground is that an unsafe
construct is the one piece of code none of the other gates can see. The mechanism does not forbid
unsafe code; it requires every use to carry the `unsafe` keyword at the site, which is what SE-0458
says it is for: "it identifies those constructs that aren't safe, encouraging the use of safe
alternatives and making it easier to audit for unsafe behavior". A C bridge is the ordinary place
those markings accumulate. A plain C call with value arguments needs none (measured the same day,
with a C function taking two `Int32`s), and a pointer crossing the bridge does. A product that finds
the markings too costly relaxes the setting on the target concerned, and records why in its own
`docs/adr/`.

**An import the manifest did not declare is refused only with the import check, because without it
the result depends on build order.** Measured 2026-09-23 with Swift 6.3.3, target `C` importing
sibling target `D` without listing it in `dependencies:`:

- in a package of targets `C` and `D` only, a plain `swift build` from an empty `.build` failed 3 of
  3 times with `no such module 'D'`;
- in a package where `D` also sat among other targets `C` did not depend on, the same plain build
  from an empty `.build` exited `0` 3 of 3 times, and so did a later incremental build;
- with `--explicit-target-dependency-import-check error`, the build failed in every case with
  `error: Target C imports another target (D) in the package without declaring it a dependency.`

So a plain build sometimes catches an undeclared import and sometimes compiles it, depending on
whether the imported module happens to be built first. The flag makes the refusal independent of
that, which is why it is on the type gate's command, and why `testing.md`'s layer 6 can treat a
declared target edge as enforced whenever the type gate passed.

## Dependency claim

**A product whose records say it has no dependencies checks that on every change.** SwiftPM leaves a
package with no dependencies nothing to resolve, and it writes no `Package.resolved` for one
(`toolchain.md` § *Adding, pinning and locking a dependency*). A dependency can enter in two ways,
and the gate reads both:

- **A package dependency** appears in the manifest dump's `dependencies` array, and a
  `Package.resolved` appears on the next resolve. `swift package dump-package` printed
  `"dependencies": []` for the zero-dependency skeleton on 2026-09-23, and `swift package
  show-dependencies` printed `No external dependencies found`, so a reader can also check it by eye.
- **A binary target with a `url:`** downloads a third party's artifact and does not appear in
  `dependencies` at all. Measured 2026-09-23: a manifest with `.binaryTarget(name: "Blob", url:
  "https://example.com/Blob.xcframework.zip", checksum: …)` dumped `"dependencies": []`, and the
  target showed under `targets` as `"type": "binary"` with its `"url"`. The gate counts targets with
  a `url`. A binary target with a `path:` built from the product's own source has `"url": null` and
  is not counted (`toolchain.md` § *Linking a C library built by another toolchain*). Measured the
  same day: the gate exits `1` on the `url:` manifest and `0` on the skeleton.

A product that does take dependencies does not run this gate. It commits `Package.resolved` and
resolves with `--force-resolved-versions` instead (`toolchain.md`).
