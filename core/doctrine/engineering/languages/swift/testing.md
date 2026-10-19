---
version: "1.1.0"
---

# Swift — testing

Swift's implementation of the layer model in `testing_doctrine.md`: the tool, the file location and
the run command for each layer. The gates a change must pass are `quality_gates.md`, and none of the
layers below is one of them. What a test target and a test file are called is `layout.md`
§ Naming; this file uses those names.

Read `testing_doctrine.md` first. It owns what each layer is, who writes it, and which layers are
optional. This file only says what each one is made of in Swift.

## One framework, Swift Testing, and one runner, `swift test`

**Tests are written with Swift Testing.** It "is included in officially-supported Swift toolchains,
including those for Apple platforms, Linux, and Windows", and "You don't need to declare a package
dependency to use Swift Testing"
(https://github.com/swiftlang/swift-testing/blob/main/README.md). `swift package init` generates a
Swift Testing test by default (measured 2026-09-23 with Swift 6.3.3: `import Testing` and an `@Test`
function, with `#expect` named in its comment). **Choosing it over XCTest for new tests is the packet
author's call, 2026-09-23.** The grounds are that it ships where the toolchain ships, with no
dependency, and that the toolchain's own generator already chose it. XCTest tests a product already
has stay as they are: "you can run them side-by-side with newer tests written using Swift Testing"
(same README).

**`swift test` builds the test targets and runs them.** It takes `--filter` and `--skip`, both
regular expressions, and the filter's format is `'<test-target>.<test-case>'`
(https://github.com/swiftlang/swift-package-manager/blob/swift-6.3.3-RELEASE/Sources/PackageManagerDocs/Documentation.docc/SwiftTest.md).
`swift test list` prints the identifiers a filter is matched against, in the form
`CoreUnitTests.theHarnessRunsAndCanReachTheErrorType()` (measured 2026-09-23).

## Layers 1–5 — code-time

**Each layer is its own test target, and the layer word in its name selects it. That is the packet
author's call, 2026-09-23.** A test target is named `<Target><Layer>Tests` (`layout.md` § Naming),
so the layer is the end of the first segment of every test's identifier, and one anchored regular
expression selects one layer across every target of the package. Measured 2026-09-23: in a package
with `CoreUnitTests`, `CoreIntegrationTests` and `AppEndToEndTests`, the layer-1 pattern ran only
the `CoreUnitTests` test, and the layers 1–4 command ran the unit and integration tests and not the
end-to-end one.

| Layer | Tool | Location | Run command |
|---|---|---|---|
| 1 — Unit | Swift Testing | `Tests/<Target>UnitTests/`, a test target depending on `<Target>` | `swift test --filter '^[A-Za-z0-9_]+UnitTests\.'` |
| 2 — Integration | Swift Testing | `Tests/<Target>IntegrationTests/` | `swift test --filter '^[A-Za-z0-9_]+IntegrationTests\.'` |
| 3 — Application | Swift Testing | `Tests/<Target>ApplicationTests/` | `swift test --filter '^[A-Za-z0-9_]+ApplicationTests\.'` |
| 4 — UI | Swift Testing, rendering the real component in process | `Tests/<UITarget>UITests/`, depending on the target that holds the views | `swift test --filter '^[A-Za-z0-9_]+UITests\.'` |
| 5 — End-to-end | Swift Testing, launching the built executable as a separate process | `Tests/<Executable>EndToEndTests/`, a test target with no dependency on the executable target, where `<Executable>` is the executable target's name | `swift build -c release && PRODUCT_BIN="$(swift build -c release --show-bin-path)/<product>" swift test --filter '^[A-Za-z0-9_]+EndToEndTests\.'` |

**The layers 1–4 suite is `swift test --skip '^[A-Za-z0-9_]+(EndToEnd|Specification)Tests\.'`.** A
plain `swift test` would also run layers 5 and 7, whose targets sit in the same package. That is
how a Swift product meets `testing_doctrine.md`'s "Layer 5 runs separately": end-to-end tests are
"not part of the layers 1–4 suite".

## The rules that make that table work

- **A filter that matches nothing passes, so every layer's run is preceded by a check that it
  selects something.** Measured 2026-09-23: `swift test --filter '^NoSuchTests\.'` built, ran
  `0 tests`, and exited `0`. So a CI step writes the test list to a file once, and before each
  layer's command checks that file for the layer's pattern, failing when the layer is empty:

  ```sh
  swift test list > .build/test-list.txt
  grep -q -E '^[A-Za-z0-9_]+UnitTests\.' .build/test-list.txt
  ```

  The list goes to a file rather than straight into `grep -q`, because `grep -q` stops reading at
  its first match: `swift test list` then gets `SIGPIPE`, and a shell running with `set -o
  pipefail` reports the pipeline as failed. Measured 2026-09-23 on a test target holding 2500 tests,
  under `bash` with `set -eo pipefail`: `swift test list | grep -q -E '<pattern>'` exited `141` on 3
  of 3 runs although the layer was not empty; the two-step form above exited `0` on 3 of 3 runs, and
  `1` for a UI pattern that matched no test. A layer that is optional for the product
  (`testing_doctrine.md`) and absent from it has no CI step at all, rather than a step that runs
  nothing.
- **Layers 1 to 3 reach the code by `import`.** A test target lists the targets it tests in
  `dependencies:`, as the generated `.testTarget(name: "DemoTests", dependencies: ["Demo"])` does. The
  logic they test sits in library targets because of `layout.md`'s library-first rule, whose ground
  is `arch_defaults.md` and not a limit of SwiftPM: a test can import an executable target too
  (`layout.md` § *Logic lives in a library target*).
- **`@testable import` is for layer 1 only.** It exposes a target's `internal` declarations to the
  test. `swift test` builds the modules it tests for testability in any configuration: its
  `--enable-testable-imports` option is "Enable or disable testable imports. Enabled by default."
  (https://github.com/swiftlang/swift-package-manager/blob/swift-6.3.3-RELEASE/Sources/PackageManagerDocs/Documentation.docc/SwiftTest.md),
  and a debug build also compiles with "`-enable-testing`: Enable the Swift compiler's testability
  feature"
  (https://github.com/swiftlang/swift-package-manager/blob/swift-6.3.3-RELEASE/Sources/PackageManagerDocs/Documentation.docc/UsingBuildConfigurations.md).
  Layers 2 and 3 use a plain `import` and see only what a caller in another target would see. The
  split mirrors `testing_doctrine.md`'s rule that a test enters through the same door production
  does. **Scoping `@testable` this way is the packet author's call, 2026-09-23.**
- **Layer 3 and layer 5 differ by the door.** `testing_doctrine.md` fixes the distinction: layer 3
  "calls the use case in-process, bypassing the entry point", and layer 5 "enters *outside* it,
  through the real entry point". In Swift the door shows in the manifest. A layer-3 target depends on
  the library target and calls the use case. A layer-5 target depends on nothing in the package: it
  starts the built executable with `Process`, reading its path from the `PRODUCT_BIN` environment
  variable the run command sets. `swift build -c release --show-bin-path` prints the release
  directory the executable is in (`.build/<triple>/release`, measured 2026-09-23); without `-c
  release` it prints the debug one. The test unwraps the variable with `try #require(…)`, so a run
  without it fails rather than passing. Measured 2026-09-23: with the variable set, a layer-5 test
  launched the built executable and checked its output; without it, the same run exited `1`.
  **The `PRODUCT_BIN` convention is the packet author's call, 2026-09-23.** The ground is that the
  test then runs the same binary a user runs, built in the configuration that ships. A product that
  ships an app bundle, not a bare executable, points the variable at the executable inside its
  bundle, built by its own bundling step, and records that step in its own `docs/nfdr.md` § 9.
- **Layer 4 renders the real component, in process.** `testing_doctrine.md` defines the layer as "A
  component renders truthfully given state — no full system, no driven session", and its mock table
  keeps "real component + real render" and mocks "the application layer behind it". In Swift that
  means constructing the real view with the state under test, laying it out, and asserting on what
  it shows. Measured 2026-09-23: a Swift Testing test marked `@MainActor` built an AppKit `NSView`
  subclass holding an `NSTextField`, set its frame, called `layoutSubtreeIfNeeded()`, and asserted on
  the label's text and fitted width, and it passed under `swift test`. The view's target carries
  `.defaultIsolation(MainActor.self)` (`conventions.md`, the concurrency rules), so the test is
  `@MainActor` too. What layer 4 does not do is drive a launched app's interface: that is a session,
  and a session is layer 5's. A product with no UI takes the exemption `testing_doctrine.md` gives
  it: "Layer 4 is optional, and inapplicable without a UI".
- **What is mocked is `testing_doctrine.md`'s table, and the seam is a protocol.** The subject stays
  real. The collaborator arrives through the protocol `conventions.md` requires, and the test passes
  in a type conforming to it that records what it received. The doctrine's own words for what this
  protects are "A test hands the unit a fake through the same door production wires the real one
  through" (`testing_doctrine.md` § Layers 1–5 — Code-Time (TDD)).
- **A test unwraps with `#require`, and a thrown error is matched by pattern.** An `Optional` value
  the test needs is unwrapped with `try #require(…)`, the form the framework's own examples use
  (Swift Testing README, above), and a call that throws is called with plain `try` in a `throws`
  test; product code's replacements for `!` and `try!` are `errors_logging.md`'s. A thrown error is
  checked with `#expect(throws: TheError.self) { … }`, or captured with `let error = try
  #require(throws: TheError.self) { … }` and matched with `guard case .someCase = error`. Matching
  by pattern keeps working when the error enum loses `Equatable` to a case carrying `any Error`
  (`errors_logging.md` § Wrapping and propagating). Measured 2026-09-23: both forms passed against an
  enum with such a case.
- **Tests run in parallel by default, and a test that shares state gets its own state.** Swift
  Testing tests "run in parallel by default" (Swift Testing README, above). A test that touches
  shared state — a file path, a user default, a global — is therefore wrong unless that state is its
  own. **Fixing that by giving the test its own state, not by serializing, is the packet author's
  call, 2026-09-23.** The framework does offer serialization, the `.serialized` trait
  (`public static var serialized: Testing.ParallelizationTrait` in the Command Line Tools' `Testing`
  interface, read 2026-09-23). The ground for not reaching for it first is that a serialized suite
  still shares the state, so the tests stay order-dependent and only stop colliding. A suite that
  exercises a resource which truly cannot be duplicated — one system-wide setting — takes
  `.serialized`, with a `//` comment naming the resource.

## Where the suite runs

On a Mac the suite needs Xcode's toolchain or a swift.org one; the Command Line Tools alone cannot
compile `import Testing` (`toolchain.md` § *Toolchain version*).

## Layers 6–7 — acceptance-time

Owned by the QA role and written from the design and the specs before code, per
`testing_doctrine.md`, which also says where a project with no active QA role records that.

**Layer 6 runs as commands over the package and its build, from a check script, not as a test
target. That is the packet author's call, 2026-09-23, and it departs from the Rust and TypeScript
packets, which run layer 6 on their test runners.** A test target could run these rules: SwiftPM's
lock is on a build directory, and a test that gave its own `swift package` call its own
`--scratch-path` read the manifest inside `swift test` and passed (measured 2026-09-23), where the
same call without one waited on `Another instance of SwiftPM … is already running using
'<package>/.build'` until it was killed. The ground for the script is what the rules are made of.
Both are shell commands over SwiftPM and the compiler, and the framework rule is a second, clean
build of the whole package into its own scratch path. As a test, each would be the same commands
wrapped in `Process` calls, and every layers 1–4 run that included it would carry a second full
build. As a script they run as written, in one CI step, apart from the in-process layers.

| Rule over | What checks it | Location |
|---|---|---|
| The target graph — which target may depend on which | the manifest, read as data | the product's check script, beside the allowed-graph file |
| That the code imports only what the graph declares | the compiler | the type gate's `--explicit-target-dependency-import-check error` (`quality_gates.md` § Types) |
| A framework a target must never load, directly or through an umbrella import | the compiler's loaded-module trace | the product's check script |

The check script's path is the product's, named in its `docs/nfdr.md` § 9 beside the rules it runs.
Each command runs from the package root.

**The target graph**, compared with the allowed-graph file:

```sh
swift package dump-package | jq -r '.targets[] | "\(.name) ->" + ([.dependencies[] | " " + (.byName // .target // .product)[0]] | sort | join(""))' | sort | diff - allowed-graph.txt
```

The command prints one line per target, `<target> -> <dependency> <dependency>`, with the targets
and each target's dependencies sorted, no trailing space, and `<target> ->` alone for a target with
no dependencies. The allowed-graph file is written in exactly that form, one line per target;
`allowed-graph.txt` is the name used here, and the product chooses its own. Measured 2026-09-23 on a
probe package: the command printed `App -> Core`, `Core ->` and `CoreUnitTests -> Core` (checked with
`cat -e` for trailing whitespace), and `diff` exited `0` against a hand-written file with those three
lines.

**A forbidden framework**, for each target and framework the product's rule names:

```sh
rm -rf .build/layer6 && swift build --scratch-path .build/layer6 -Xswiftc -emit-loaded-module-trace && jq -e '[.swiftmodules[] | select(test("/<Framework>\\.swiftmodule/"))] | length == 0' .build/layer6/debug/<Target>.build/<Target>.trace.json > /dev/null
```

- **It reads the compiler, not the source.** A search for `import AppKit` misses the ways a target
  can load AppKit without writing that line: measured 2026-09-23, a library target with `import
  Cocoa`, or with `@preconcurrency import struct AppKit.NSEdgeInsets`, built, and a `grep` for
  `^import AppKit` found nothing. The trace lists every Swift module the target loaded, and in both
  cases it listed AppKit's, so the check exited `1`; after the import was removed it exited `0`. Two
  limits, both measured the same day: the trace is written fresh only by a clean build (an
  incremental build left AppKit in a trace after the import was gone), which is why the command
  builds into its own emptied scratch path; and `swiftmodules` lists modules that have a Swift
  interface, so a framework reached only as a C module is outside it. The check ends in `jq -e`, so
  a missing trace file fails it (`jq` exits `2`) instead of passing.
- **A declared target edge is enforced only under the import check.** A plain build compiled an
  undeclared import between sibling targets in one package shape and refused it in another
  (`quality_gates.md` § Types), so a layer-6 rule about targets relies on the type gate having run
  with the flag.

The reasoning for what runs each rule is the one the TypeScript packet states in
`languages/typescript/testing.md` § Layers 6–7 — acceptance-time: **what** a layer-6 rule says is
the product's and varies, and **what runs** the rule is the language's and does not. Here what runs
it is SwiftPM and the compiler, through the commands above, and the product supplies only the
allowed graph and the forbidden framework names.

**Layer 7 runs through layer 5's mechanism.** A specification-level scenario enters the product
through its real entry point, so it is a test target named `<Executable>SpecificationTests`, where
`<Executable>` is the executable target's name, launching the same `PRODUCT_BIN`, run with
`--filter '^[A-Za-z0-9_]+SpecificationTests\.'`, and kept out of the layers 1–4 suite by its
`--skip`. Its test files are named for the scenario they cover, not for a production file.

**Where the rule itself lives.** The content of a layer-6 or layer-7 rule is the product's, in its
own `docs/nfdr.md`, and the entry there names the layer in its `verified by:` tail. This file says
only what runs it.
