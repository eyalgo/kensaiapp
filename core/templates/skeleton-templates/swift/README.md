# Swift skeleton tree

What a copy of this tree gives a Swift product, what it deliberately leaves out, and, per file,
which of the Swift language packet's six destination files fixed the choice (`toolchain.md`,
`layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`, `testing.md`, all under
`core/doctrine/engineering/languages/swift/`). Each packet citation below names the section or the
rule it rests on, and was checked against it on 2026-09-23. Every claim about what the toolchain
does was measured the same day with Apple Swift 6.3.3 on a Mac with the Command Line Tools only,
except the proof table, which was re-run the same day with Xcode 27.0 (Apple Swift 6.4).

This tree carries no `version:` marker. It is a script-copied shape, not a doctrine file, and the
governing rule is that a script-read template is the file itself, content only, with nothing that
must not survive the copy (its own home's README, § *Adding a script-facing template*, step 3).

## The `__PROJECT__` token, and why the target names are fixed

`core/launchers/product-skeleton/launcher.sh` substitutes `__PROJECT__` when it copies this tree,
in paths and in contents. For a unit placement it also substitutes `__UNIT__`; this tree carries no
`__UNIT__`, and `core/tools/test_skeleton_trees.py` holds that it carries no token but
`__PROJECT__`. Which token set applies is the consuming script's (`core/templates/README.md`
§ *Adding a script-facing template*, step 2).

**The value is not always the package slug.** When the product's SDD § 3 names this tree's unit as
a `package` at some path, the launcher copies the tree to that path, and the token becomes that
path's last segment, so a unit at `app-mac` gives `app-mac`. With no units table, the tree goes to
the product root (or the card's `Language roots:`), and the token is the card's `Package slug:`.
Either way, **the value can carry a hyphen.**

That decides where the token can go: the package name and the executable product's name, where a
hyphen is kept as written. Measured 2026-09-23, a copy stamped as `demo-mac` built and linked a
binary named `demo-mac`. It does not go in a target name. SwiftPM accepts a hyphenated target but
derives its module name by replacing the hyphen — a target `demo-mac` is imported as `demo_mac`
(`layout.md` § Naming, measured) — and the launcher's plain string replace would write
`import demo-mac` into every source and test file, which does not compile. So the targets carry
fixed names, `App`, `Core` and `CoreUnitTests`, each a valid identifier as `layout.md` § Naming
asks. **The fixed names are this tree's call and not the packet's.** `Core` names no responsibility,
which `layout.md` § *Where a new file goes* rules out for a module, so it stands only until the
product has code to name it for. A product renames `Core` to what its SDD calls the part: a
directory rename plus the matching edits in `Package.swift` and in each `import`.

## What is here, and which packet file fixed it

| File | What it is | Fixed by |
|---|---|---|
| `Package.swift` `// swift-tools-version: 6.2` | the floor, and the first manifest API that carries the three settings below | `toolchain.md` § *Toolchain version* |
| `Package.swift` `swiftLanguageModes: [.v6]` | the language mode, written out | `toolchain.md` § *Language mode* |
| `Package.swift` `.treatAllWarnings(as: .error)` on every target | warnings fail every build, not only the gate's | `quality_gates.md` § *Types*, the packet author's call; on every target, unconditionally, per `conventions.md`'s manifest rule |
| `Package.swift` `.strictMemorySafety()` on every target | an unsafe use must be marked `unsafe` where it occurs | `quality_gates.md` § *Types*, the packet author's call |
| `Package.swift` `.defaultIsolation(MainActor.self)` on `App` only | the executable runs on the main actor, and the library does not | `conventions.md`, the default-isolation rule under § *The constructs this house prefers* |
| `Package.swift` `platforms: [.macOS(.v14)]` | a starter deployment target | § *The deployment target* below |
| `Sources/App/main.swift` | the composition root, in the entry file the packet names, with nothing to wire yet | `layout.md` § *Logic lives in a library target*; `arch_defaults.md` § Composition Root |
| `Sources/Core/CoreError.swift` | the product's single named base error, a `package` `enum` with no cases yet | `errors_logging.md` § *Raising* (with one raising target, its enum is the product's base); `arch_defaults.md` § Exception shape; `conventions.md` § *The constructs this house prefers*, the access rule (`package`, because only targets in this package read it) |
| `Tests/CoreUnitTests/CoreErrorTests.swift` | one layer-1 Swift Testing test, named for the production file it covers | `testing.md` § *Layers 1–5*; `layout.md` § Naming |
| `.swift-format` | the format and lint gate's config: `version` 1 and `indentation.spaces` 4 | `quality_gates.md` § *Format and lint*, the packet author's call |
| `.gitignore` | what SwiftPM and Xcode generate | § *`.gitignore`* below |

The one test exists because a test run with no tests passes and so proves nothing. Measured
2026-09-23: the same package with its `@Test` function removed ran `0 tests` and exited `0`. It is
scaffolding, not a test of the product, and it goes once `Core` has a real test.

## The gates this tree wires

Each is `quality_gates.md` § *The gates*, run from the package root. Their commands are stated
there and not copied here. On the stamped copy below, all four exit `0`: format and lint, link, the
dependency claim (this tree declares no `dependencies:`, no binary target and no system library),
and types.

## Proof, 2026-09-23

A copy of this tree was stamped with `__PROJECT__` replaced by `verify-mac`, and each command ran
from its root, as written, with Xcode 27.0 selected (Apple Swift 6.4).

| Command | Exit | Last line |
|---|---|---|
| `swift build -c release` | 0 | `Build complete!` |
| `swift test` | 0 | `Test run with 1 test in 0 suites passed` |
| the format and lint gate | 0 | (no output) |
| the type gate | 0 | `Build complete!` |
| the link gate | 0 | `Build complete!` |
| the dependency-claim gate | 0 | (no output) |
| `swift test list`, written to a file, then `grep` for the layer-1 pattern | 0 | `CoreUnitTests.theHarnessRunsAndCanReachTheErrorType()` |

On the Command Line Tools alone, the same `swift test` and type gate fail with `no such module
'Testing'`; `toolchain.md` § *Toolchain version* records why.

The real launcher placed this tree too. A fake instance's card declared `Languages: Swift`, and its
SDD § 3 named a unit `demo-mac` of kind `package`. `launcher.sh demo` exited `0` and wrote
`demo-mac/Package.swift` with `name: "demo-mac"`. `swift build --package-path demo-mac -c release`
then exited `0`, the test run exited `0`, and `git status --untracked-files=all`
in the product showed nothing under `demo-mac/.build`. `test_product_skeleton.py`'s
`test_a_real_swift_package_unit_places_the_real_tree_at_its_unit` repeats that placement against
the current tree on every run: it asserts the files land under the unit, that the two re-anchored
`.swiftpm` entries come back under it, and that `Package.swift` carries the unit's name.

## `.gitignore`

The entries are the ones `swift package init` writes into a new package's `.gitignore` (Swift 6.3.3,
2026-09-23), verbatim and in the same order. Four of them are anchored: `/.build` and `/Packages` by
their leading slash, and the two `.swiftpm/...` entries by the slash in their middle. "If there is a
separator at the beginning or middle (or both) of the pattern, then the pattern is relative to the
directory level of the particular `.gitignore` file itself" (https://git-scm.com/docs/gitignore,
read 2026-09-23). The launcher merges every tree's `.gitignore` into the product root's file and
re-anchors each anchored pattern under the unit's path, so all four land as `/<unit>/...`.

## The deployment target

`platforms: [.macOS(.v14)]` is a starter default, and a product replaces it on day one with the
value its NFDR states. The packet fixes no deployment target, because that is the product's decision
(the packet's `README.md` § *What the packet leaves to the product*). A value is written here
anyway, for the tree's own test:

- **Without one, the tree's test does not build on the Command Line Tools.** Measured 2026-09-23
  with no `platforms:` line: `error: 'isolation()' is only available in macOS 10.15 or newer`, from
  inside Swift Testing's expansion. In the 6.3.3 release SwiftPM derives a test target's deployment
  target from the platform's `XCTest.framework`, and where it cannot find one — on the Command Line
  Tools alone — it falls back to the oldest supported version
  (https://github.com/swiftlang/swift-package-manager/blob/swift-6.3.3-RELEASE/Sources/PackageModel/MinimumDeploymentTarget.swift).
- **14 is the minimum the toolchain's own `Testing.framework` declares.** `xcrun vtool -show-build`
  on the Command Line Tools' `Testing.framework` reported `minos 14.0` (measured 2026-09-23), so
  a test bundle linking it runs on macOS 14 and later. SwiftPM's `main` has since added a
  hard-coded `14.0` minimum for test targets
  (https://github.com/swiftlang/swift-package-manager/blob/main/Sources/PackageModel/MinimumDeploymentTarget.swift),
  which the 6.3.3 release does not carry.

So the value is the lowest one the tree's test framework supports, written out so that the test
builds on both toolchains. What it also does is set the executable's deployment target, which is the
product's, and a product stamped from this tree ships for macOS 14 and later until it says
otherwise. Nothing flags that it has not.

## What this tree deliberately omits, and why

- **An Xcode project or workspace.** `toolchain.md` § *Build system and package manager*: a product
  here is a SwiftPM package.
- **A `Package.resolved` and any `dependencies:`.** `toolchain.md` § *Adding, pinning and locking a
  dependency*: "A package with no dependencies has no `Package.resolved`, and none is created for
  it". The builds above left none behind.
- **A `.swift-version`.** `toolchain.md` § *Toolchain version*: it binds only swiftly, and a product
  that uses swiftly commits it.
- **A C target, a binary target or a system-library target.** `layout.md` § *C interop* gives all
  three, and which one applies depends on where the product's C comes from. The tree does not guess
  the bridge.
- **An app bundle, `Info.plist`, entitlements or signing.** These are outside the language, and the
  packet leaves them to the product's own records.
- **A logger.** `errors_logging.md` § Logging: a `Logger` needs no setup, and its subsystem is an
  identifier this tree does not know.
- **Tests for layers 2 to 5 and 7, and the layer-6 check script.** `testing.md` § *Layers 1–5 —
  code-time* and § *Layers 6–7 — acceptance-time*: each layer is its own test target, named for the
  target it tests, and a target is named for a part the product has not written yet; the content of
  a layer-6 or layer-7 rule is the product's.

## A product that ships a library, not an executable

The tree always declares `App` and an executable product, because the composition root is part of
the frame of a product that runs. A product that ships only a library removes them: delete
`Sources/App/`, delete the `.executableTarget(name: "App", …)` entry, and replace
`.executable(name: "__PROJECT__", targets: ["App"])` with `.library(name: "<LibraryName>", targets:
["Core"])`, the product kind SwiftPM names "libraries" (`toolchain.md` § *Build system and package
manager*). The `strict` settings, `Core` and `CoreUnitTests` stay as they are. A library published
for other packages then makes `CoreError` `public`, because other packages read it
(`conventions.md` § *The constructs this house prefers*, the access rule).

## A product whose executable is not main-actor code

`App` carries `.defaultIsolation(MainActor.self)` because an app's entry code runs on the main
actor. An executable that is itself highly concurrent, such as a server, does not
(`conventions.md`, the default-isolation rule), and its product removes `+
[.defaultIsolation(MainActor.self)]` from the `App` target, leaving `swiftSettings: strict`.

## Where a part from the SDD lands

The two ways the launcher reads SDD § 3 place parts differently, and the Swift route is the units
table (§ *The `__PROJECT__` token* above).

- **With a units table, the launcher creates no directory for a part.** Every part's `Lives in`
  must name a unit, and a `package` unit gets this tree and nothing else
  (`core/launchers/product-skeleton/launcher.sh`: part directories are built only when the SDD has
  no units table). So a part that lives in the Swift package names the package's unit in its
  `Lives in` — for example `app-mac` — and the product creates the part's place in the package when
  it writes the part's code, by `layout.md`'s rules: a subdirectory of an existing target, or a new
  target with its own `Sources/<Target>/` and a manifest entry. Measured 2026-09-23 with the real
  launcher: an SDD with two parts both living in `app-mac`, and one unit `app-mac | Swift |
  package`, placed the tree and committed `5 files and 0 part directories`. A `Lives in` naming a
  path inside the package, such as `app-mac/Sources/Core`, is refused unless that path is itself a
  unit (the launcher's check that every distinct `Lives in` value is a unit).
- **With no units table, the launcher creates `<Lives in>/<part slug>/` with a `.gitkeep`.** The
  part slug is lower-case kebab-case (the launcher's `PART_SLUG_RE`), and a target name is
  `UpperCamelCase` (`layout.md` § Naming), so a part directory that is to become a target is renamed
  first — `Sources/file-tree/` becomes `Sources/FileTree/` — and then gets its
  `.target(name: "FileTree")` entry. A directory the manifest does not name is inert
  (`layout.md` § *The tree SwiftPM already fixes*, measured).

**Making a part its own target is the product's move, not the skeleton's.** A target is a manifest
entry and a place in the dependency graph, and a skeleton that guessed it would be deciding the
architecture the SDD already chose. A target added that way carries the `strict` settings,
unconditionally (`conventions.md`, the manifest rule).
