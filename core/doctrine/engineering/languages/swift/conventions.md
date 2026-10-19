---
version: "1.0.2"
---

# Swift — conventions

Naming, the constructs this house prefers and avoids, and how each floor rule lands in Swift. What
the code does at a failure or an event is `errors_logging.md`. Where a file goes, and what a file,
target or module is called, is `layout.md`.

**Most rules here only a reader can apply. Where a tool also checks part of a rule, the rule says
so where it stands, marked "(also checked: …)".** Those rules stay here because they are naming and
construct rules, which this concern owns (`languages/README.md` § The seven concerns); the gates that
run the checks, and their commands, are `quality_gates.md`. Where this file cites swift-format's
default configuration it is the configuration shipped with Swift 6.3.3, read on 2026-09-23.

The Swift API Design Guidelines are the base this file refines
(https://www.swift.org/documentation/api-design-guidelines/, read 2026-09-23). It adds to them where
the floor, `<CORE>/doctrine/engineering/languages/developer_standards.md`, asks for something they do not state,
and it departs from them in one place, marked where it happens (§ Documentation comments). A
quotation below attributed to "the guidelines" is from that page; a quotation attributed to "the
floor" is from `<CORE>/doctrine/engineering/languages/developer_standards.md`.

## Casing

The guidelines: "Names of types and protocols are `UpperCamelCase`. Everything else is
`lowerCamelCase`." That covers functions, methods, properties, variables, constants, enum cases and
argument labels alike. The compiler accepts `SCREAMING_SNAKE_CASE` and `snake_case` names (`let
MAX_RETRIES = 3` compiled, measured 2026-09-23); the house does not use them. (Also checked: the
format and lint gate's default rules `AlwaysUseLowerCamelCase` and `TypeNamesShouldBeCapitalized`
reject both.)

**An acronym that is written in capitals in English takes the case of its position.** The
guidelines: "Acronyms and initialisms that commonly appear as all upper case in American English
should be uniformly up- or down-cased according to case conventions", with the examples `utf8Bytes`
and `isRepresentableAsASCII`. So a property is `url` or `htmlBody`, and a type is `URLSession` or
`HTMLParser`, never `Url`. An acronym that is not written that way is an ordinary word: "Other
acronyms should be treated as ordinary words", as in `radarDetector: RadarScanner`.

## Naming

- **Clarity at the point of use first.** The guidelines: "Clarity at the point of use is your most
  important goal", and "Clarity is more important than brevity". A name is judged where it is
  called, with its argument labels, not where it is declared.
- **A name states a role, not a type.** The guidelines: "Name variables, parameters, and associated
  types according to their roles, rather than their type constraints" — `greeting`, not `string`.
  This is how Swift lands the floor's "Intent-revealing names".
- **No abbreviations.** The guidelines: "Avoid abbreviations. Abbreviations, especially non-standard
  ones, are effectively terms-of-art". The floor states the same rule ("no abbreviations"), and the
  guidelines add the reason.
- **Side effects decide the grammar.** The guidelines: functions and methods "without side-effects
  should read as noun phrases, e.g. `x.distance(to: y)`", and those "with side-effects should read as
  imperative verb phrases, e.g., `print(x)`, `x.sort()`". A mutating/non-mutating pair is `sort()` /
  `sorted()`, or for a noun, `union(_:)` / `formUnion(_:)`.
- **A Boolean reads as an assertion** about its receiver. The guidelines: "Uses of Boolean methods
  and properties should read as assertions about the receiver" — `isEmpty`, `intersects(_:)`.
- **A protocol is a noun when it says what something is, and ends in `-able`, `-ible` or `-ing` when
  it says what something can do.** The guidelines: "Protocols that describe what something is should
  read as nouns", and "Protocols that describe a capability should be named using the suffixes
  `able`, `ible`, or `ing`" — `Collection`, `Equatable`, `ProgressReporting`.
- **A factory method begins with `make`**, as the guidelines direct — `makeIterator()`.
- **No type is named for no responsibility.** The floor rejects "generic labels (`manager`,
  `handler`, `utils`)", so there is no `DataManager` or `EventHandler` type. The same rule for files,
  targets and modules is `layout.md` § *Where a new file goes*.

## Documentation comments, and the floor's one comment exception

The floor states that "A comment that says *what* the code does is the smell". It allows one
exception, for "a comment recording *why* the code is shaped this way and not the obvious other way,
with a citation", and leaves the language-specific form to this file. In Swift the form is two
comment kinds doing two different jobs:

- **`///` documents the declaration that follows it**, and it is where a declaration's contract
  goes. The guidelines give the markup for the parts of a contract, `- Parameter`, `- Returns`,
  `- Throws`, and ask for a doc comment beginning with a summary. A `public` or `package`
  declaration always carries one, which satisfies the floor's "Every public interface has an
  explicit contract".
  **This is the one place the file departs from the guidelines, and it is the packet author's call,
  2026-09-23.** The guidelines say "Write a documentation comment for every declaration". Here an
  `internal`, `fileprivate` or `private` declaration carries one only when its contract is not
  already stated by its name and signature. The ground is the floor's comment rule: a `///` on a
  private helper whose name says what it does is the comment the floor calls a smell. swift-format's
  `AllPublicDeclarationsHaveDocumentation` rule is `false` in its default configuration, so no gate
  checks either half; it is a reader's rule.
- **`//` is an ordinary comment, and it is where the floor's exception lives.** A `//` line that says
  *what* the next line does is the smell the floor names. A `//` line saying *why* this shape and not
  the obvious other one, with its citation, is the exception the floor grants.

## The constructs this house prefers

- **A binding is `let` unless it is written to.** The Swift book: "If a stored value in your code
  won't change, always declare it as a constant with the `let` keyword"
  (https://github.com/swiftlang/swift-book/blob/main/TSPL.docc/LanguageGuide/TheBasics.md). This is
  the Swift form of the floor's "Immutable data structures unless mutability is required". A `var`
  is a claim that something writes to it, and a reader is entitled to check that claim. For a local,
  the build checks it: `var x = 1; return x` fails under warnings-as-errors with `variable 'x' was
  never mutated` (measured 2026-09-23). (Also checked, for a local only: the compiler warns, and the
  warnings-as-errors setting fails the build.) A stored property is not checked, and is the
  reader's.
- **A type is a `struct` unless it needs to be a class.** That is a separate question from `let`:
  it is about value versus reference semantics. Apple's guidance is "Use structures by default", and
  use classes "when you need Objective-C interoperability" or "when you need to control the identity
  of the data you're modeling"
  (https://developer.apple.com/documentation/swift/choosing-between-structures-and-classes, read
  2026-09-23). A subclass of an AppKit class such as `NSView` is a class by the first case; a model
  whose instances are shared by identity is a class by the second.
- **A value with a closed set of possibilities is an `enum`, never a `String`.** The floor asks the
  implementer to "Upgrade imprecise constructs encountered during implementation (string with a
  closed value set → enum)". Swift's enum cases carry associated values, so the upgrade loses nothing
  a string was providing.
- **A `switch` over an enum names every case, and adds `@unknown default:` only for an enum that can
  gain cases the product has not compiled against. That is the packet author's call, 2026-09-23.**
  A `switch` must be exhaustive, and a `default:` satisfies that for every case added later, so a new
  case would silently take the default branch. Without it, a new case is a compile error at every
  `switch` that has to decide what it means. That holds for the product's own enums and for an enum
  from another SwiftPM package, which is compiled from source with the product: measured
  2026-09-23, after a case was added to a path dependency's `public enum`, the product's `switch`
  without a default failed with `switch must be exhaustive`, and a `default:` after every listed case
  failed the build with `default will never be executed`. An enum from the SDK is different, because
  the SDK is built for library evolution and can gain cases after the product ships: listing every
  case of `ProcessInfo.ThermalState` and nothing else failed with `switch covers known cases, but
  'ProcessInfo.ThermalState' may have additional unknown values`. A `switch` over an SDK enum
  therefore lists every known case and ends in `@unknown default:`, which still requires the known
  cases: the same `switch` listing one case plus `@unknown default:` failed with `switch must be
  exhaustive` under the packet's warnings-as-errors setting. (Also checked: all three failures are
  compiler diagnostics, fatal under warnings-as-errors.)
- **A magic value is a named constant, and that is the packet author's call, 2026-09-23, for the
  shape.** At file scope it is a `private let`: it is used by this file only, and `private` is the
  narrowest level that reaches the whole file (the access rule below). A group of related values is
  a `static let` on a caseless `enum` used as a namespace; the ground is that a caseless enum cannot
  be instantiated, so it holds constants and nothing else. Either way it is `lowerCamelCase`
  (§ Casing). This is the floor's "No magic numbers or strings — named constants".
- **A unit is given its collaborators through a protocol.** `arch_defaults.md` § Dependency Graph
  Rules states the rule language-agnostically: "Only the composition root imports concrete
  implementations. Every other module depends on abstractions". In Swift the abstraction is a
  protocol. A collaborator the unit stores arrives as a generic type parameter constrained to that
  protocol (`struct Service<Backend: Storing>`) or as an existential (`any Storing`). A collaborator
  passed to one function only can also be `some Storing`. An opaque `some` type cannot be a stored
  property's type without an initializer: measured 2026-09-23, `let backend: some Storing` assigned
  in `init` failed with `property declares an opaque return type, but has no initializer expression
  from which to infer an underlying type`. Generic parameter or existential is the product's choice,
  because it is about dispatch and type erasure rather than about the seam. What does not satisfy
  the rule is a unit that constructs its own collaborator. `testing_doctrine.md` then has no door to
  hand a fake through, and it says what that means: "Where the subject offers no door to hand a fake
  through, the defect is the subject's shape and not the test's" (`testing_doctrine.md` § Layers 1–5
  — Code-Time (TDD)).
- **The narrowest access level that works.** A declaration's default is `internal`
  (https://github.com/swiftlang/swift-book/blob/main/TSPL.docc/LanguageGuide/AccessControl.md). A
  declaration is `public` only when another package reads it. When only another target in the same
  package does, it is `package`, the level SE-0386 added because `public` allows a symbol "to be
  accessed from any module at all"
  (https://github.com/swiftlang/swift-evolution/blob/main/proposals/0386-package-access-modifier.md).
  A member used only inside its own type and that type's extensions in the same file is `private`.
  A **member** used by other types in the same file is `fileprivate`, because a `private` member does
  not reach them: measured 2026-09-23, a `private var` read by a second struct in the same file
  failed with `'secret' is inaccessible due to 'private' protection level`. A **file-scope**
  declaration used only in its file is `private`, which at file scope already reaches the whole
  file. (Also checked: the lint gate's `FileScopedDeclarationPrivacy` rule rejects `fileprivate` on
  a file-scope declaration — measured 2026-09-23, `fileprivate let fp = 1` failed with `replace
  'fileprivate' with 'private' on file-scoped declarations`, while a `fileprivate` member passed.)
- **Shared mutable state lives in an `actor` or on the main actor, and a value crossing between
  concurrent code is `Sendable`.** The Swift book: "Actors let you safely share information between
  concurrent code", and a type is sendable when, for example, it is "a structure with stored
  properties that are sendable or an enumeration with associated values that are sendable"
  (https://github.com/swiftlang/swift-book/blob/main/TSPL.docc/LanguageGuide/Concurrency.md). So a
  value passed between tasks is preferably a `struct` or `enum` of sendable parts. A class guarded by
  a lock and marked `@unchecked Sendable` is a claim the compiler no longer checks, and it is written
  with a `//` comment saying why the lock is enough.
- **`.defaultIsolation(MainActor.self)` goes on a target whose code runs on the main actor, and not
  on a target meant to be used from any isolation domain.** SE-0466 added the setting because "most
  executables, such as apps, command-line tools, and scripts, start running on the main actor and
  stay there unless some part of the code does something concurrent (like creating a `Task`)". It
  kept `nonisolated` as the language default because "`MainActor` isolation is the wrong default for
  many kinds of modules, including libraries that offer APIs that can be used from any isolation
  domain, and highly-concurrent server applications"
  (https://github.com/swiftlang/swift-evolution/blob/main/proposals/0466-control-default-actor-isolation.md).
  Reading the two together, **the packet author's call, 2026-09-23**, is: an app's executable
  target, and a target holding its UI code (views and the code that turns state into what they
  show), carry the setting; a target whose API is called from any isolation domain — the logic
  library, a C bridge, anything a background task calls — does not; and an executable that is itself
  highly concurrent, such as a server, does not either. No tool checks which targets carry it. The
  setting needs tools version 6.2 (`toolchain.md` § *Toolchain version*).
- **Every target the package builds carries the quality gates' manifest settings, unconditionally.**
  The type gate relies on `.treatAllWarnings(as: .error)` and `.strictMemorySafety()` being on each
  Swift target, and on `.treatAllWarnings(as: .error)` on each C and C++ target (`quality_gates.md`
  § Types). So a target carries them with no `.when(…)` condition, and with no `.treatWarning(_:as:
  .warning)` that downgrades a group, unless the product's own `docs/adr/` records the relaxation for
  that target. No gate checks this: a manifest review does.

## The constructs this house avoids

- **A type named for no responsibility** — § Naming above.
- **Force-unwrapping (`!`) and `try!` in product code.** Both are runtime assertions with no room
  for a message. What product code writes instead, and why, is `errors_logging.md` § Raising, which
  owns failures and invariants.
- **Unmarked unsafe code, including `nonisolated(unsafe)`.** It is refused by the build rather than
  discouraged by convention. The rule and the way to relax it are `quality_gates.md` § Types.
