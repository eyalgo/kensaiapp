---
version: "1.0.1"
---

# Swift — layout

The source and test tree, where a new file of each kind goes, and how files, targets, test targets
and packages are named. What a type, function or variable is called is `conventions.md`. What each
testing layer is made of and how it runs is `testing.md`. This file owns where a test target sits
and what it is called. The tools version, the language mode and how a compiled library is linked are
`toolchain.md`; the settings the type gate relies on are `quality_gates.md` § Types; which targets
carry main-actor default isolation is `conventions.md`.

## The tree SwiftPM already fixes

SwiftPM finds a package's targets by directory, so most of this layout is the tool's rather than
this packet's. "Swift sources are collected by target name under the `Sources` directory, and tests
collected, also by target name, under the `Tests` directory"
(https://github.com/swiftlang/swift-package-manager/blob/swift-6.3.3-RELEASE/Sources/PackageManagerDocs/Documentation.docc/CreatingSwiftPackage.md):

```
Package.swift          the manifest — toolchain.md
Package.resolved       the resolution, present only when there are dependencies — toolchain.md
.swift-format          the format and lint gate's config — quality_gates.md
Sources/
  <Target>/            one directory per target, named exactly as the manifest names the target
Tests/
  <Target><Layer>Tests/  one directory per test target, named by § Naming below
.build/                build output, "the .build folder", ignored and never committed
```

`.build` is where SwiftPM puts both configurations' artifacts and the checked-out sources of
dependencies (`UsingBuildConfigurations.md` and `GettingStarted.md` in the same documentation
folder). It is output, not source.

**A directory under `Sources/` that the manifest does not name is inert.** Measured 2026-09-23 with
Swift 6.3.3: a package whose manifest declares its targets explicitly built clean with an undeclared
`Sources/Reader/` holding only a `.gitkeep`, and with a `.gitkeep` inside a declared target's
subdirectory. So a directory created ahead of its code costs the build nothing, and it also builds
nothing. It becomes a target only when the manifest names it.

## Logic lives in a library target, and the executable is thin

**A package that ships an executable puts its logic in library targets and keeps the executable
target small.** The rule is `arch_defaults.md` § Application Layer's, "Entry-point thinning — CLI
handlers and other adapters carry no logic", and it rests on that alone. It is not a limit of
SwiftPM: a test target can depend on an executable target and `@testable import` it. Measured
2026-09-23: a Swift Testing test called an `internal` function defined in an executable target's
`main.swift` and passed. The executable target stays thin because its job is wiring, not because
tests cannot reach it.

**The executable target is the composition root**, the only module that names a concrete
implementation and wires it to an abstraction. That is `arch_defaults.md` § Composition Root ("the
only place that wires concrete implementations to abstractions… It owns wiring, not flow"), which is
language-agnostic. How every other target is given its collaborators is `conventions.md`'s protocol
rule.

**Its entry file is `main.swift`, holding top-level code, and no file in the target carries
`@main`. That is the packet author's call, 2026-09-23.** `swift package init --type executable`
generates the other shape, an `@main struct` in a file named for the target (measured 2026-09-23).
The two do not mix: measured the same day, a target with top-level code in `main.swift` and an
`@main struct` in a second file failed with `'main' attribute cannot be used in a module that
contains top-level code`. A type that a framework expects to be the entry point — a SwiftUI `App`, a
type with a `static func main()` — is declared without `@main` and started from `main.swift` by
calling its `main()`; measured the same day, `Entry.main()` called from `main.swift` built and ran.
The ground for `main.swift` is that the composition root then has one fixed file name in every Swift
product here, so a reader opens it without searching for the attribute.

## Where a new file goes

- **A file is named for the primary type it holds.** "A file that primarily contains a single type
  has the name of that type", and a file holding one extension that adds a conformance is
  `MyType+MyProtocol.swift` (https://google.github.io/swift/, the Google Swift style guide, § File
  Names, read 2026-09-23). A type named `FileTree` lives in `FileTree.swift`. The guide names a
  file of declarations "not otherwise scoped under a common type or namespace" descriptively, "for
  example, `Math.swift`", and leaves "more complex situations" to "best judgment" (same section).
  This packet does the same, subject to the generic-label rule below.
- **A bounded area inside a target is a subdirectory of that target**, not a file that keeps
  growing, and that is the packet author's call, 2026-09-23. The ground is the floor's Single
  Responsibility rule (`<CORE>/doctrine/engineering/languages/developer_standards.md`, "one class, one reason to
  change"), applied to a directory: an area with its own reason to change gets its own place.
  `Sources/Reader/Parsing/` holds a `Reader` target's parsing area. SwiftPM compiles a target's
  subdirectories as part of that target. Measured 2026-09-23: a `public` function in
  `Sources/A/sub/Deep.swift` was callable from another target through a plain `import A`.
- **A file name is unique within its target, across all its subdirectories.** SwiftPM compiles a
  target's files into one module, keyed by file name. Measured 2026-09-23: `Sources/Core/Parsing/Step.swift`
  and `Sources/Core/Rendering/Step.swift` in one target failed with `couldn't build …
  Step.swift.o because of multiple producers`. A second file that would take a name already used in
  the target is named more specifically — `ParseStep.swift`, `RenderStep.swift` — and the same pair
  renamed so built.
- **A bounded area that needs its boundary enforced is its own target.** A declaration's default
  access level is `internal`, visible only inside its module
  (https://github.com/swiftlang/swift-book/blob/main/TSPL.docc/LanguageGuide/AccessControl.md), and
  SE-0386 exists because "to access a symbol in another module, that symbol needs to be declared
  `public`"
  (https://github.com/swiftlang/swift-evolution/blob/main/proposals/0386-package-access-modifier.md).
  So a target boundary hides everything not marked `package` or `public`. **A declared target edge
  is not enforced by every build, though.** `quality_gates.md` § *Types* records that a plain
  `swift build` can compile an import of a sibling target the manifest never declared, and it gives
  the flag that refuses one.
- **No file, target or module is named for no responsibility** — no `Utils.swift`, no
  `Helpers.swift`, no `Extensions.swift`, no `Common` target. The floor rejects generic labels
  (`<CORE>/doctrine/engineering/languages/developer_standards.md`, "no generic labels (`manager`, `handler`,
  `utils`)"), and a file or module named for no responsibility is where every item nobody placed
  ends up. A module's name also appears in every `import` of it. An extension lives in the file of
  the type it extends, or in a `Type+Protocol.swift` of its own. An extension that adds no
  conformance to a type from another module — methods on `URL`, say — goes in a file named for that
  type and what the extension is for, `URL+PackageRoot.swift`; that is the packet author's call,
  2026-09-23, following the Google guide's `MyType+` prefix for extensions (same section) with a
  purpose in place of its generic `Additions`. This section owns the rule for files and modules;
  `conventions.md` owns it for types.

## C interop

A Swift package reaches C through a module map, and where the C comes from decides which kind of
target carries it. Module maps "Define how C and C++ headers are exposed to Swift for system library
targets, precompiled libraries, or C Language targets"
(https://github.com/swiftlang/swift-package-manager/blob/main/Sources/PackageManagerDocs/Documentation.docc/ModuleMaps/ModuleMaps.md).

| Where the C comes from | Target | Where its files go |
|---|---|---|
| C source the package owns | a C target | `Sources/<CTarget>/`, public headers in `Sources/<CTarget>/include/` |
| A library the product builds from its own source with another toolchain | a binary target, `.binaryTarget(name:path:)`, over a local artifact bundle | `<Name>.artifactbundle/` at the package root: the `.a`, `include/` with the header and `module.modulemap`, and `info.json` |
| A library installed on the system separately | a system-library target, `.systemLibrary` | `Sources/<CName>/module.modulemap` beside a shim header |

A third party's prebuilt library is a dependency, whichever of these routes carries it
(`toolchain.md` § *Linking a C library built by another toolchain*). **The two locations in the
last column for a binary and a system-library target are the packet author's call, 2026-09-23**:
SwiftPM fixes neither — its own system-library example uses `SystemLibraries/CSystemLib` (`ModuleMaps.md`,
above) — and the ground is one place per kind, so a reader finds every C bridge where the table
says. Both were measured on 2026-09-23: a `.systemLibrary(name: "CBridge")` at `Sources/CBridge/`
and a `Bridge.artifactbundle` at the package root each built, and the executable using each ran.

- **A C target.** "C language targets are structured similarly to Swift targets, with the additional
  of a directory, commonly named `include`, to hold public header files", and SwiftPM "automatically
  generates a module map for each C language library target", falling back to treating `include`
  as an umbrella directory. A hand-written `module.modulemap` goes in `include` "In case of
  complicated `include` layouts or headers that are not compatible with modules"
  (https://github.com/swiftlang/swift-package-manager/blob/swift-6.3.3-RELEASE/Sources/PackageManagerDocs/Documentation.docc/CreatingCLanguageTargets.md).
- **A binary target** is the route for a compiled library the product owns. Why it is chosen over
  the other two for that case, the `info.json` shape, and how the library is built for the
  package's deployment target are `toolchain.md` § *Linking a C library built by another
  toolchain*.
- **A system-library target** is for "a library that users install separately on their systems"
  (`ModuleMaps.md`, above). Its module map names the header, the library to `link`, and what to
  `export`
  (https://github.com/swiftlang/swift-package-manager/blob/swift-6.3.3-RELEASE/Sources/PackageManagerDocs/Documentation.docc/Dependencies/AddingSystemLibraryDependency.md).
- **A module map's header path is relative.** "Specify header paths relative to the module map
  file's location", and "Don't use absolute paths or parent directory references (`../`)"
  (`ModuleMaps.md`, above).

## Naming

| What | Case | Source |
|---|---|---|
| Package (`Package(name:)`) | the product's slug as it stands, hyphens allowed | packet author's call, 2026-09-23: the package name never appears in an `import`, so it can carry the product's own spelling. Measured 2026-09-23: packages named `demo-mac` and `ledger-mac` built. |
| Target, and therefore its `Sources/` directory | `UpperCamelCase`, a valid Swift identifier | packet author's call, 2026-09-23. SwiftPM's own examples are `UpperCamelCase` (`PlayingCard`, `DeckOfPlayingCards`, `GettingStarted.md` in the same documentation folder). A hyphen is accepted, but SwiftPM then derives a different module name: `swift package init --name demo-mac` created target `demo-mac` whose module is `demo_mac`, imported as `import demo_mac` (measured 2026-09-23). A target named as a valid identifier keeps the target, the directory and the `import` the same string. |
| Test target | `<Target><Layer>Tests`, the layer word being `Unit`, `Integration`, `Application`, `UI`, `EndToEnd` or `Specification`. `<Target>` is the target the tests cover; for `EndToEnd` and `Specification`, which depend on no target, it is the executable target's name (`App`, not the hyphenated product name). | packet author's call, 2026-09-23. The layer word lets one anchored `--filter` select one layer across every target; which word goes with which layer, and why, is `testing.md` (§ *Layers 1–5 — code-time* for the first five, § *Layers 6–7 — acceptance-time* for `Specification`). This departs from `swift package init`, which generates `<Target>Tests`. |
| Test file | `<Type>Tests.swift` for the production file `<Type>.swift` it covers, at the same subdirectory path inside the test target as the production file has inside its target (`Sources/Reader/Parsing/Parser.swift` → `Tests/ReaderUnitTests/Parsing/ParserTests.swift`). An end-to-end or specification test file covers no production file and is named for the flow or scenario it drives. | `testing_doctrine.md`: "**Test files mirror production structure.** A test file's location and naming follow the production module it covers." The subdirectory mirroring is the packet author's call, 2026-09-23, reading "mirror" literally. |
| Executable product | the name the built binary should carry, hyphens allowed | measured 2026-09-23: `.executable(name: "demo-mac", targets: ["App"])` linked a binary named `demo-mac` |
| Executable entry file | `main.swift` | § *Logic lives in a library target* above |
| Source file | the primary type's name, `UpperCamelCase.swift` | § *Where a new file goes* above |

What a type, protocol, function or property inside those files is called is `conventions.md`.
