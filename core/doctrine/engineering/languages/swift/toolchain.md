---
version: "1.1.1"
---

# Swift — toolchain

The build system, the package and dependency manager, the toolchain-version policy, the language
mode, how a compiled library is linked, and how a dependency is added, pinned and locked. Where a
file of a given kind goes is `layout.md`. Which checks run over it, and the manifest settings those
checks rely on, are `quality_gates.md`. Which targets run on the main actor is `conventions.md`.

## Build system and package manager — SwiftPM

The Swift Package Manager is both, and it reads one manifest for all of it. "A Swift package is a
directory that contains sources, dependencies, and has a `Package.swift` manifest file at its root",
and "The package manifest defines what is in the package, which is itself written in Swift"
(https://github.com/swiftlang/swift-package-manager/blob/swift-6.3.3-RELEASE/Sources/PackageManagerDocs/Documentation.docc/CreatingSwiftPackage.md).
A package declares products of three kinds: "libraries, executables, and plugins"
(https://github.com/swiftlang/swift-package-manager/blob/swift-6.3.3-RELEASE/Sources/PackageManagerDocs/Documentation.docc/IntroducingPackages.md).

**A product here is a SwiftPM package rather than an Xcode project, and that is the packet author's
call, 2026-09-23.** It covers a package that ships an app, a command-line tool or a library. The
ground is where this packet's gates read the targets from. Every build, test and manifest command in
`quality_gates.md` and `testing.md` is a SwiftPM command — `swift build`, `swift test`, `swift
package` — and SwiftPM takes the package's targets from `Package.swift` (and the resolved versions
from `Package.resolved`). The format gate reads source files and `.swift-format`, not targets. An
Xcode project would be a second description of the same targets, which none of those commands reads,
so a gate could pass over a target the project builds differently. A product whose shape needs a project file records that in its own `docs/adr/`,
which outranks this packet per `languages/README.md` § Precedence.

**Two build configurations, and the release one is named on the command line.** "By default,
running `swift build` builds the package using its debug configuration", and "To build in release
mode, type `swift build -c release`". Each lands in its own directory, `debug` or `release`, "under
the `.build` folder"
(https://github.com/swiftlang/swift-package-manager/blob/swift-6.3.3-RELEASE/Sources/PackageManagerDocs/Documentation.docc/UsingBuildConfigurations.md).
A SwiftPM command run from outside the package names the package with `--package-path <dir>`
(https://github.com/swiftlang/swift-package-manager/blob/swift-6.3.3-RELEASE/Sources/PackageManagerDocs/Documentation.docc/SwiftTest.md).
That flag is SwiftPM's. It is not accepted by every command a gate runs, and `quality_gates.md`
says where each gate runs from.

## Toolchain version — the `swift-tools-version` line

**Every manifest opens with `// swift-tools-version:`, and the line is a floor, not a pin.** "The
tools version declares the minimum version of the Swift compiler required to use the package, as
well as how to parse the `Package.swift` manifest", and `swift package init` sets it "automatically
to the current version"
(https://github.com/swiftlang/swift-package-manager/blob/swift-6.3.3-RELEASE/Sources/PackageManagerDocs/Documentation.docc/SettingSwiftToolsVersion.md).
The same line also decides which manifest API the package may call. **A package here declares `6.2`
or later**, because three build settings this packet puts in the manifest are each marked "First
available in PackageDescription 6.2"
(https://github.com/swiftlang/swift-package-manager/blob/swift-6.3.3-RELEASE/Sources/Runtimes/PackageDescription/BuildSettings.swift):
`.treatAllWarnings(as:)` and `.strictMemorySafety()` (`quality_gates.md` § Types), and
`.defaultIsolation(_:)` (`conventions.md`, the concurrency rule). A lower line cannot state them.

**The packet fixes no file that pins an exact toolchain, and that is the packet author's call,
2026-09-23.** One such file exists: swiftly, the swift.org toolchain manager, "uses the
`.swift-version` file, if present in your working directory (or parent), to select the toolchain
that is in use"
(https://github.com/swiftlang/swiftly/blob/main/Documentation/SwiftlyDocs.docc/use-toolchains.md).
swiftenv, a third-party version manager, reads the same file name: "Setting the local swift
version will write the version to the `.swift-version` file in the current working directory", and
"This version overrides the global version"
(https://swiftenv.fuller.li/en/latest/commands.html, read 2026-09-23). Both pages describe their own
tool's selection and nothing else, so a Mac building through Xcode's toolchain has no documented
reason to read the file, and a committed `.swift-version` would claim a pin that only those tools'
users honour. A product that installs its toolchains through swiftly commits the file.

**Where there is no pin file, the product records the toolchain version its CI builds with, in its
own `docs/nfdr.md`.** That is the packet author's call, 2026-09-23. The ground is the format gate:
swift-format ships inside the toolchain (`quality_gates.md` § *Format and lint*), so the formatter's
rules move with the toolchain version, and a developer and a CI runner on different toolchains can
get different verdicts from the same gate command. The record — an Xcode version, or a swift.org
toolchain version — is what a reader checks a local toolchain against when the two disagree.

**On macOS the toolchain is Xcode's or a swift.org one, and the Command Line Tools alone do not run
tests.** Measured 2026-09-23 on a Mac with only the Command Line Tools (Apple Swift 6.3.3, CLT package
`26.6.0.0.1781586589`): `swift test` on a package fresh from `swift package init` failed with `error:
no such module 'Testing'`, and an XCTest version of the same test failed with `no such module
'XCTest'`. `Testing.framework` is present in the Command Line Tools'
`Library/Developer/Frameworks`, and the verbose build showed SwiftPM passing that directory as `-I`
and never as a framework search path `-F`. That matches the cause the Swift Forums user
`smontgomery` gave in September 2024, for Swift 6.0: "the version of SwiftPM in CommandLineTools does
not yet have this change landed on `main` which configures the necessary search paths to locate
`Testing.framework`". The same post gave two ways out, "a Swift 6 macOS toolchain from Swift.org",
and a later one "the copy of swift test in Xcode 16"
(https://forums.swift.org/t/error-no-such-module-testing/74784, read 2026-09-23). The Xcode one
is verified: on the same machine with Xcode 27.0 installed and selected (Apple Swift 6.4), a plain
`swift test` on a stamped skeleton passed, and every gate in `quality_gates.md` § *The gates* exited
`0` as written, measured 2026-09-23. The swift.org toolchain is not verified here.

## Language mode — Swift 6, stated in the manifest

**A package here builds in the Swift 6 language mode, with the mode written out.** "A `Package.swift`
file that uses `swift-tools-version` of `6.0` enables the Swift 6 language mode for all targets", and
"By default, Swift 6 enables full data race safety checking"
(https://github.com/swiftlang/swift-migration-guide/blob/main/Guide.docc/EnableDataRaceSafety.md).
The tools-version floor above already implies the mode. The manifest still states
`swiftLanguageModes: [.v6]`, because that is what `swift package init` writes into the manifest it
generates (measured 2026-09-23 with Swift 6.3.3). A reader then sees the mode without having to know
the rule that implies it.

**A target that is not ready for the Swift 6 mode steps down alone, and says so.** The mode can be
changed "on a per-target basis using the new `swiftLanguageMode` build setting", for example
`.swiftLanguageMode(.v5)` on that one target (same page). Lowering the mode of the whole package to
spare one target is not the move. A target on `.v5` is a decision the product records in its own
`docs/adr/`, with the reason, because **it removes that module's data-race checks outright**.
Measured 2026-09-23: a target with a mutable `public var` global written from an `async` function
and a non-`Sendable` class captured in `Task.detached` built with no diagnostic at all under
`.swiftLanguageMode(.v5)` and `.treatAllWarnings(as: .error)`. Without the step-down, the same
source failed with `error: var 'counter' is not concurrency-safe because it is nonisolated global
shared mutable state`. The errors do not become warnings, so warnings-as-errors does not catch them.

**So a stepped-down target also carries `.enableUpcomingFeature("StrictConcurrency")`.** The page
this section cites gives it, § "Enable data-race safety checking as warnings", as the way to keep
the checks on a Swift 5 mode target (same page). Measured 2026-09-23: the same `.v5` target with
that feature added failed again, with `error: var 'counter' is not concurrency-safe … this is an
error in the Swift 6 language mode`, because the packet's warnings-as-errors turns the restored
warnings into errors. So under this packet the feature restores the checks at full strength, and a
target that cannot pass them yet is one whose ADR says so and drops the feature too. That is the
packet author's call, 2026-09-23: the step-down buys source compatibility, not silence.

## Linking a C library built by another toolchain

Where the C interface and its module map sit in the tree is `layout.md` § *C interop*. How the
package links the compiled library is this file's.

**A static library the product builds with another toolchain is linked through a local
static-library artifact bundle, and that is the packet author's call, 2026-09-23.** SE-0482 adds the
`staticLibrary` artifact type to artifact bundles: an `info.json` whose variant names the `.a` file,
its `supportedTriples`, and `staticLibraryMetadata` with `headerPaths` and a `moduleMapPath`
(https://github.com/swiftlang/swift-evolution/blob/main/proposals/0482-swiftpm-static-library-binary-target-non-apple-platforms.md,
"Implemented (Swift 6.2)"). The package declares it with `.binaryTarget(name:path:)`. The proposal's
title scopes it to non-Apple platforms, so this rule rests on a measurement: on 2026-09-23 with Swift
6.3.3 and the Command Line Tools, a `Bridge.artifactbundle` holding `libbridge.a`, `include/bridge.h`,
`include/module.modulemap` and an `info.json` with `"supportedTriples": ["arm64-apple-macosx"]`
built with a plain `swift build`, and the executable that imported it ran and printed the C
function's result. Only `arm64-apple-macosx` was measured. A product that ships for another
architecture lists that architecture's triple too, with a library built for it; that is unmeasured
here. The ground for choosing it over the three alternatives:

- **A system-library target** is SwiftPM's route for "a library that users install separately on
  their systems"
  (https://github.com/swiftlang/swift-package-manager/blob/main/Sources/PackageManagerDocs/Documentation.docc/ModuleMaps/ModuleMaps.md).
  Its documented search path comes from `pkgConfig`, or else from `-Xcc -I` and `-Xlinker -L` flags
  on every `swift build`
  (https://github.com/swiftlang/swift-package-manager/blob/swift-6.3.3-RELEASE/Sources/PackageManagerDocs/Documentation.docc/Dependencies/AddingSystemLibraryDependency.md).
  A library the product itself builds is not installed on the system, and a flag every build must
  remember is a build that differs between a developer and CI.
- **A manifest linker flag**, `linkerSettings: [.unsafeFlags(["-L<dir>"])]`, keeps the command
  plain, but "the use of unsafe flags makes the products containing this target ineligible for use by
  other packages" (`BuildSettings.swift`, cited above).
- **An XCFramework binary target** is SwiftPM's documented binary route on Apple platforms, "an
  Xcode-oriented format called XCFramework, and only for Apple platforms" (SE-0482, § Motivation).
  Creating one takes `xcodebuild -create-xcframework`, and on the Command Line Tools alone
  `xcodebuild` does not run: measured 2026-09-23, `xcodebuild -version` answered `tool 'xcodebuild'
  requires Xcode`. The artifact bundle is built with `ar` and a JSON file, which every toolchain has.

The artifact bundle has none of these costs.

**The `path:` route is for a library built from the product's own source, in its own repository.**
A binary target with a `url:` downloads a third party's artifact, and a third party's prebuilt
library copied into the repository is the same thing kept locally: both are dependencies, under the
dependency rules below. The dependency-claim gate counts the first and cannot see the second
(`quality_gates.md` § *Dependency claim*), so for a vendored binary the rule rests on the reader.

**The static library is built for the package's deployment target.** Measured 2026-09-23: a
`libbridge.a` compiled for the host's macOS 26 and linked into a package declaring `.macOS(.v14)`
built with `ld: warning: object file … was built for newer 'macOS' version (26.0) than being linked
(14.0)`, and `.treatAllWarnings(as: .error)` did not fail it, because the setting governs the Swift
compiler and not the linker. Compiled with `clang -mmacosx-version-min=14.0`, the same library
linked with no warning, and so did one compiled with `MACOSX_DEPLOYMENT_TARGET=14.0` set in the
environment (`vtool -show-build` reported `minos 14.0`). The product's build step for the library
sets that variable to the package's deployment target, which is the packet author's call,
2026-09-23: it is one mechanism for any compiler that honours it, where a compiler flag differs by
compiler. The rustc documentation lists the same variable for Apple targets
(https://doc.rust-lang.org/rustc/platform-support/apple-darwin.html); that is read, not measured
here. The link gate in `quality_gates.md` is what fails the build when the library is still too
new.

## Adding, pinning and locking a dependency

- **A dependency is a decision, and the smallest one is none. A product departs from zero in its own
  `docs/adr/`**, naming the dependency and the reason, because the departure is a decision that
  outranks this packet (`languages/README.md` § Precedence). The floor's YAGNI rule
  (`<CORE>/doctrine/engineering/languages/developer_standards.md`, "YAGNI — implement what is needed now") means
  here: reach for the standard library, Foundation or the platform SDK before reaching for a package.
  SwiftPM's own documentation names the cost: "adding dependencies to a project has an associated
  coordination cost"
  (https://github.com/swiftlang/swift-package-manager/blob/swift-6.3.3-RELEASE/Sources/PackageManagerDocs/Documentation.docc/IntroducingPackages.md).
  **Zero dependencies is this packet's default, and a package with no `dependencies:` at all is a
  complete and legitimate shape.** On Apple platforms the packet names no third-party package: its
  formatter and linter ship with the toolchain (`quality_gates.md`), its test framework ships with
  the toolchain (`testing.md`), and its logger is the operating system's (`errors_logging.md`). A
  product that also targets a platform without the `os` module has a logging decision to make, which
  may add a dependency (`errors_logging.md` § Logging).
- **A dependency is added with SwiftPM, and the manifest is formatted afterwards.** `swift package
  add-dependency <url> --from <version>` writes the package entry, and `swift package
  add-target-dependency <product> <target> --package <package>` wires it into the target that uses it.
  Those are two separate steps, because "Adding the dependency makes it available to the package, but
  doesn't include it by default into the targets within the package"
  (https://github.com/swiftlang/swift-package-manager/blob/swift-6.3.3-RELEASE/Sources/PackageManagerDocs/Documentation.docc/GettingStarted.md).
  **Using the commands rather than a hand edit is the packet author's call, 2026-09-23**, on the
  ground that the command writes the entry in the shape SwiftPM itself parses, and a reviewer can
  re-run it. The written manifest does not pass the format gate as it stands. Measured 2026-09-23 on
  a stamped skeleton: after the two commands, `swift format lint --strict` reported two
  `[TrailingComma]` errors in `Package.swift`. After `swift format --in-place --recursive .` it
  reported none. So the step after adding a dependency is that format run.
- **A package with dependencies commits `Package.resolved`, whether it ships an app or a library.**
  "The package manager records the result of dependency resolution in a file named
  `Package.resolved` at the top-level of the package", and the documentation's own example is to
  "keep a `Package.resolved` file in source control… in order to ensure another build uses the same
  versions of dependencies"
  (https://github.com/swiftlang/swift-package-manager/blob/swift-6.3.3-RELEASE/Sources/PackageManagerDocs/Documentation.docc/ResolvingPackageVersions.md).
  **For a library it pins the library's own builds and CI, and not its consumers.** "The
  `Package.resolved` only helps to resolve dependencies to the specific versions it defines for leaf
  projects", and "those versions are ignored by the package that depends on your library" (same
  page). The library's own CI is a leaf build of it, and the `--force-resolved-versions` rule below
  needs the file there. **A package with no dependencies has no `Package.resolved`, and none is
  created for it.** There is nothing to resolve, so the file's absence is the correct state.
- **In CI, every `swift build` and `swift test` of a package with dependencies carries
  `--force-resolved-versions`** — the type gate, the link gate and every layer command in
  `testing.md` included. `--force-resolved-versions` means "Only use versions from the
  Package.resolved file and fail resolution if it is out-of-date"
  (https://github.com/swiftlang/swift-package-manager/blob/swift-6.3.3-RELEASE/Sources/PackageManagerDocs/Documentation.docc/SwiftTest.md).
  It goes on every command rather than on one resolve step first, because each SwiftPM command
  resolves again before it runs: "Most SwiftPM commands implicitly invoke dependency resolution
  before running" (`ResolvingPackageVersions.md`, above). Without the flag, "In most cases, the
  resolve command performs no changes unless the `Package.swift` manifest or `Package.resolved` file
  has changed" (same page), and a manifest change whose new requirement the recorded version no
  longer satisfies is re-resolved and rewritten, which is how a version nobody reviewed reaches a
  build. Measured 2026-09-23 with a local git dependency tagged `1.0.0` and `1.1.0`: moving the
  requirement from `exact: "1.0.0"` to `from: "1.0.0"` kept `1.0.0` in the file, with or without
  the flag; moving it to `from: "1.1.0"` made a plain `swift build` rewrite the file to `1.1.0`,
  while `swift build --force-resolved-versions` and `swift test --force-resolved-versions` both
  stopped with `error: an out-of-date resolved file was detected`. A package with no dependencies has
  nothing for the flag to enforce, and its zero-dependency claim is checked by `quality_gates.md`
  § *Dependency claim* instead.
- **A version requirement in the manifest is a range, and `Package.resolved` is the resolution.** A
  dependency review therefore reads the `Package.resolved` diff, not the manifest diff.

## Dependency auditing

**The packet fixes no dependency-advisory gate, and that is the packet author's call, 2026-09-23.**
The ground is that no first-party gate exists to point at. `swift package --help` (Swift 6.3.3)
lists no advisory subcommand; its one audit command, `experimental-audit-binary-artifact`, audits a
static-library binary artifact, not dependency advisories. A web search on 2026-09-23 found only
third-party scanners, such as the Swift analyzer in OWASP Dependency-Check
(https://jeremylong.github.io/DependencyCheck/analyzers/swift.html), and none that ships with the
Swift toolchain or is published by the Swift project. The packet's default of zero dependencies also
leaves such a gate nothing to scan. A product that takes dependencies records how it audits them in
its own `docs/nfdr.md`. The day one Swift product here does, that record is the evidence this
section is revised against.
