---
version: "1.0.0"
---

# Swift — errors and logging

How a Swift product here raises a failure, wraps one, propagates one, and emits an event. Naming and
shape rules that are not about a failure or an event are `conventions.md`. The commands that check
any of this are `quality_gates.md`.

## Raising

- **A function that can fail `throws`, and the throw is untyped.** SE-0413 added typed throws and
  still concluded that "the existing (untyped) `throws` remains the better default error-handling
  mechanism for most Swift code", because typed throws "constrains the evolution of that function's
  implementation" and "errors are usually propagated or rendered, but not exhaustively handled"
  (https://github.com/swiftlang/swift-evolution/blob/main/proposals/0413-typed-throws.md). `throws(E)`
  is used only in the three cases that proposal lists. The first is code that "stays within a module
  or package where you always want to handle the error". The second is generic code that only passes
  errors through. The third is dependency-free code for a constrained environment. The proposal
  also warns against the most tempting reason: "Resist the temptation to use typed throws because
  there is only a single kind of error that the implementation can throw" (same page).
- **A thrown error is not an exception, and throwing costs about what returning costs.** "Unlike
  exception handling in many languages… error handling in Swift doesn't involve unwinding the call
  stack", and "the performance characteristics of a `throw` statement are comparable to those of a
  `return` statement"
  (https://github.com/swiftlang/swift-book/blob/main/TSPL.docc/LanguageGuide/ErrorHandling.md). The
  untyped `throws` above adds the cost of boxing the error as `any Error`, which SE-0413 names as
  "the overhead associated with existential types"; it matters only in the constrained environments
  that proposal's third case covers.
  So an expected failure — a malformed input, a missing file, a refused permission — is thrown and
  never turned into a crash to save a code path.
- **The product has one named base error, and each condition is one enum case.** The rule is
  `arch_defaults.md` § Exception shape, which is language-agnostic: "One product-level base error
  type… That is what lets an interface layer catch the product's failures in one clause", and "One
  type per distinct condition… because callers map types to distinct outputs — exit codes, HTTP
  statuses, messages — and cannot map a string." Swift has no error inheritance, so its spelling is
  the packet author's call, 2026-09-23:
  - **Each target that raises failures defines one `enum` conforming to `Error`, with one case per
    condition.** That is the construct the Swift book recommends: "Swift enumerations are
    particularly well suited to modeling a group of related error conditions, with associated values
    allowing for additional information about the nature of an error to be communicated" (same
    page).
  - **With one such target, its enum is the product's base.** With more than one, the base is a
    protocol refining `Error`, and each target's enum conforms to it. The protocol lives in a
    target every raising target depends on; if the product has none, it gets one, holding the
    protocol and nothing else. It is `package` unless another package reads it, and then `public`
    (`conventions.md`, the access rule). Its name is the product's; `ProductFailure` below is an
    example.
  - **The interface layer catches the product's failures in one clause, and everything else in a
    second.** The first clause is `catch let failure as any ProductFailure`; the second is a plain
    `catch`, which receives any other error — a `CancellationError`, an error from the SDK that was
    not translated — and turns it into the interface's generic failure output, logged at `error`.
    The second clause is required. Measured 2026-09-23: the first clause alone in a non-throwing
    function failed to compile with `errors thrown from here are not handled because the enclosing
    catch is not exhaustive`, and at the top level of a `main.swift` it compiled and the process
    died with `Fatal error: Error raised at top level: Swift.CancellationError()`, exit `133`. With
    the second clause the same program caught the `CancellationError` there and exited `0`; two
    enums conforming to one protocol were both caught by the first.
  - Every error is already `Sendable` (`public protocol Error : Swift.Sendable` in the macOS SDK's
    `Swift.swiftinterface`, read 2026-09-23), so a case's associated values have to be `Sendable`
    too. The Swift 6 mode reports a non-`Sendable` associated value as a warning (`associated value
    'bad' of 'Sendable'-conforming enum 'E1' has non-Sendable type 'Box'`, measured 2026-09-23), and
    it is the packet's warnings-as-errors setting that fails the build on it (`quality_gates.md`
    § Types).
- **An invariant is checked with `precondition`, not thrown.** Assertions and preconditions "aren't
  used for recoverable or expected errors", because "a failed assertion or precondition indicates an
  invalid program state" and "there's no way to catch a failed assertion". The two differ in when
  they are checked: "Assertions are checked only in debug builds, but preconditions are checked in
  both debug and production builds"
  (https://github.com/swiftlang/swift-book/blob/main/TSPL.docc/LanguageGuide/TheBasics.md). An
  invariant the product relies on in production is therefore a `precondition` (or a
  `preconditionFailure` in the branch that finds it broken), and its message states the invariant,
  not the operation. Whoever reads the crash needs to know what was assumed. **A broken invariant is
  never continued past.** The same page gives the reason: "Recovering from an invalid state is
  impossible", because "you don't know why it's invalid or whether an additional state is also
  invalid", and "Stopping execution as soon as an invalid state is detected also helps limit the
  damage caused by that invalid state".
- **Product code does not use `!` or `try!`, and that is the packet author's call, 2026-09-23.**
  `try!` wraps "the call in a runtime assertion that no error will be thrown" (`ErrorHandling.md`,
  above), and `!` is "effectively, a shorter spelling of `fatalError(_:file:line:)`"
  (`TheBasics.md`, above). Neither takes a message, so neither can state the invariant the rule
  above asks for. An invariant is written `guard let value = optional else { preconditionFailure("<the
  invariant>") }`, and a call that cannot throw in practice is `do { try call() } catch {
  preconditionFailure("<why it cannot throw>: \(error)") }`. How a test unwraps a value is
  `testing.md`'s.

## Wrapping and propagating

- **`try` is how an error travels.** "You can propagate the error from a function to the code that
  calls that function" (`ErrorHandling.md`, above). A function between the throw and the handler adds
  `try`. The one other thing it may add is the translation in the next rule, at a target boundary.
  It adds no log line (the last rule in this section).
- **An error crossing a target boundary is translated once, and it keeps the original.** A target
  that catches a lower target's error and throws its own wraps it in a case that carries the
  underlying error as an associated value, for example `case readFailed(path: String, underlying: any
  Error)` (type-checks in the Swift 6 mode, measured 2026-09-23). Its callers still match on this
  target's cases, and the cause is still there for a reporter to show. **That shape is the packet
  author's call, 2026-09-23.** The ground is `arch_defaults.md` § Exception shape, which puts the
  matching at the product's own types. The standard library's `Error` protocol carries no underlying
  error, so the associated value is where the cause goes. Such a case also removes the enum's
  synthesized `Equatable`, because `any Error` is not `Equatable`; a test then matches the thrown
  case by pattern rather than by `==` (`testing.md`). Foundation's `NSError` does have one,
  `underlyingErrors` (macOS 11.3 and later, `NSError.h` in the macOS SDK), and an error bridged from
  an Apple API may already carry its cause there; the associated value keeps the product's own
  errors independent of Foundation.
- **An error is never discarded.** `try?` handles an error "by converting it to an optional value",
  and "If an error is thrown while evaluating the `try?` expression, the value of the expression is
  `nil`" (`ErrorHandling.md`, above). The error itself is gone. `try?` is therefore correct only where
  `nil` is the whole meaning of the failure, such as a lookup that may simply miss. It is never
  correct on a call that returns nothing: there `nil` carries no meaning at all. That case is also
  the silent one. Measured 2026-09-23: `try? h()` on a function returning `Int` warns `result of
  'try?' is unused`, and `try? g()` on a function returning `Void` compiles with no diagnostic, so no
  gate catches it and a reader has to. `_ = try? something()` is never correct either. Where
  continuing past a failure really is correct, the error is caught and logged at `error` with the
  reason continuing is safe, and the line says so.
- **A failure is logged once, where it is handled.** A layer that logs and then rethrows produces one
  failure several times, and a reader cannot tell one failure from three. The function that handles
  the failure — by stopping, or by deciding to continue past it — logs it. Every function between the
  throw and that point adds `try`, or a translation into its own case, and no log line.

## Logging

- **On Apple platforms the logger is the operating system's, `Logger` from the `os` module.** It is
  "An object for writing interpolated string messages to the unified logging system", created with
  "an optional subsystem and category string"
  (https://developer.apple.com/documentation/os/logger, read 2026-09-23). It is part of the SDK, so
  it adds no dependency, which keeps `toolchain.md`'s zero-dependency default intact there.
- **The subsystem is one reverse-DNS identifier per product, and the category is the target's
  name.** The subsystem "identifies a large functional area within your app or apps" and uses
  "reverse-DNS notation, such as `com.example.myapp`". The category "identifies a particular
  component or module in a given subsystem"
  (https://developer.apple.com/documentation/os/generating-log-messages-from-your-code, read
  2026-09-23). **Which identifier is the packet author's call, 2026-09-23**, by product kind:
  - an app uses its bundle identifier;
  - a command-line tool, which a SwiftPM build gives no bundle identifier, uses the reverse-DNS
    identifier its `docs/nfdr.md` records for it;
  - a library published for other packages uses its own reverse-DNS identifier, fixed in its source,
    because it cannot know the product that will link it.

  A target creates its own `Logger` with its own category, and there is nothing global to set up
  first.
- **The ladder is five of the system's levels**, in increasing severity: debug, info, notice (the
  default), error and fault (same page). By default only notice, error and fault are written to
  disk; debug is kept in memory only, and info is written to disk "Only when collected with the log
  tool" (same page). `Logger` also has `trace`, `warning` and `critical`, which map onto debug, error
  and fault, and `log(_:)` and `log(level:_:)`, which take the level as an argument
  (`os.swiftmodule` interface in the macOS SDK, read 2026-09-23). **Code here calls only the five
  level names, and that is the packet author's call, 2026-09-23**, so that two lines at one level
  read the same. What belongs at each level is
  also the packet author's call, written so that a reader can place a line without asking. The
  `error` row follows the system's own definition, "Captures errors seen during the execution of
  your code" (same page), which covers a failure continued past as well as one that stopped:

  | Level | What belongs at it |
  |---|---|
  | `fault` | a broken invariant, logged in the branch that detects it just before its `preconditionFailure` (§ Raising), so the unified log holds it beside the crash — a bug, not a condition |
  | `error` | a failure, logged once where it is handled: where the product stopped, or where it continued past it, with the reason that was safe |
  | `notice` | an event a reader would want from a normal session — a folder opened, a command accepted |
  | `info` | detail helpful while troubleshooting, and not needed otherwise |
  | `debug` | per-item or per-step detail, useful only while tracing one operation |

- **What the system redacts by default depends on the value's type.** "By default, the system doesn't
  redact integer, floating-point and Boolean values, but it does redact the contents of dynamic
  strings and complex dynamic objects"
  (https://developer.apple.com/documentation/os/generating-log-messages-from-your-code). So a
  sensitive number — an identifier, an amount — is written in clear unless the line marks it
  `privacy: .private`, and it is marked. A string or object stays at its redacted default, and
  `privacy: .public` goes on one only when it is known not to be sensitive. An enum case is logged
  through its `rawValue`, or through a `CustomStringConvertible` conformance: measured 2026-09-23, a
  plain `enum` interpolated into a `Logger` message failed to compile with `requires that 'Mode'
  conform to 'CustomStringConvertible'`, and `\(mode.rawValue, privacy: .public)` compiled.
- **An error value is logged as `String(describing: error)`, never interpolated as the error
  itself.** `os`'s interpolation of an `any Error` bridges it to `NSError`, and in a module that does
  not import Foundation that bridge traps at runtime. Measured 2026-09-23: in a library target
  importing only `os`, `logger.error("failed: \(error)")` compiled with no diagnostic and the
  process died with `Swift/BridgeObjectiveC.swift:130: Fatal error`, exit `133`; `logger.error("failed:
  \(String(describing: error))")` in the same target logged and the process exited `0`. The string is
  dynamic, so it stays redacted by default (the rule above), which is the right default for an error
  description that may carry a path or a value. An `error`-level line names the operation that failed
  and carries that description; the operation name is static text, visible in clear.
- **A secret never enters a log line or an error message at all.** That rule is not this packet's but
  `quality_defaults.md` § Secrets: "A secret is never written to a log, an error message, or a
  completion report". Redaction does not satisfy it, because a redacted value is still written, and
  a privacy marker changed later publishes it.
- **A product that also runs where `os` does not exist makes a logging choice, and records it in
  its own `docs/adr/` when the choice adds a dependency** (`toolchain.md`, the dependency rule). The
  `os` module is Apple's. The Swift ecosystem's cross-platform logging API is SwiftLog, which
  "provides a unified, performant, and ergonomic logging API that can be adopted by libraries and
  applications across the Swift ecosystem". It is "an API package", and its README points to
  "community-maintained logging backends … for production use"
  (https://github.com/apple/swift-log/blob/main/README.md). With no backend chosen it logs through
  its own `StreamLogHandler`, the default "if you don't define otherwise"
  (`Sources/Logging/LoggingSystem.swift` in the same repository). So SwiftLog is one package
  dependency, and a backend would be a second. The packet takes neither on a product's behalf; the
  choice between SwiftLog and a minimal logger of the product's own belongs to that product.
