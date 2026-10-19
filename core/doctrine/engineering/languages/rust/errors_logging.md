---
version: "1.1.0"
---

# Rust — errors and logging

How a Rust product here raises a failure, wraps one, propagates one, and emits an event. Naming and
shape rules that are not about a failure or an event are `conventions.md`. The commands that check
any of this are `quality_gates.md`.

## Raising

- **A function that can fail returns `Result`.** The Book states it as the default and this packet
  keeps it: "Returning `Result` is a good default choice when you're defining a function that might
  fail" (https://doc.rust-lang.org/book/ch09-03-to-panic-or-not-to-panic.html). Returning `Result`
  leaves the handling to the caller; `panic!` "make[s] the decision that a situation is unrecoverable
  on behalf of the caller" (same page).
- **`panic!` is for a broken invariant, not for an expected failure.** The Book's own test: panic
  when "some assumption, guarantee, contract, or invariant has been broken" *and* the bad state is
  unexpected, or the code after that point relies on not being in it, or there is no good way to
  encode the state in the types (same page). Its counter-examples are the ordinary ones — "A parser
  being given malformed data", "An HTTP request returning a status indicating a rate limit" — and
  each of those is a `Result`.
- **`unwrap` and `expect` are correct in tests and examples, and are a claim in product code.** In a
  test, "`panic!` is how a test is marked as a failure, calling `unwrap` or `expect` is exactly what
  should happen" (same page). In product code an `expect` is the invariant written down, so its
  message states the invariant rather than the operation — the reader of the panic needs to know what
  was assumed, not that a call returned `None`.
- **A library crate defines one error type, with one variant per condition.** That is
  `arch_defaults.md` § Exception shape, which is language-agnostic — "A single named base… One type
  per distinct condition… because callers map types to distinct outputs — exit codes, HTTP statuses,
  messages — and cannot map a string." The Rust spelling of both halves at once is an `enum`: the
  enum is the single named type the caller matches on, and each variant is one condition.
- **That enum implements `std::error::Error`.** The trait "represents the basic expectations for
  error values" and requires `Debug` and `Display`, with `Debug` for the debugging representation and
  `Display` for the message a person reads
  (https://doc.rust-lang.org/std/error/trait.Error.html). std's own guidance on the message is worth
  keeping: error messages are "concise lowercase sentences without trailing punctuation" (same page).
- **`thiserror` writes those implementations, and this packet uses it in a library crate.** Its
  derive macro generates `Display` from `#[error("...")]` attributes, the `Error` implementation
  including `source()`, and `From` for variants marked `#[from]`; the crate "deliberately does not
  appear in your public API", so a consumer sees a plain `enum` implementing a std trait
  (https://docs.rs/thiserror). The reason to prefer it over writing the two implementations by hand
  is not typing saved — it is that a hand-written `Display` drifts from the variant it describes
  when a field is added, and the attribute cannot.

## Wrapping and propagating

- **`?` is how an error travels, and the conversion is `From`.** With `?`, "the `Err` will be
  returned from the whole function as if we had used the `return` keyword so that the error value
  gets propagated to the calling code", and the value goes "through the `from` function, defined in
  the `From` trait in the standard library… the error type received is converted into the error type
  defined in the return type of the current function"
  (https://doc.rust-lang.org/book/ch09-02-recoverable-errors-with-result.html). `#[from]` on a
  variant is what makes `?` work across a boundary without a hand-written `map_err` at every call.
- **An error crossing a boundary keeps the original, and keeps it once.** std states the rule and its
  exclusive-or plainly: in an error type that wraps an underlying error, either return it via
  `Error::source()` or render it in the `Display` implementation, not both
  (https://doc.rust-lang.org/std/error/trait.Error.html). Rendering it in `Display` as well as
  exposing it as `source()` prints the same cause twice in any chain-walking reporter.
- **A binary crate propagates with `anyhow` and adds context on the way up.** `anyhow` is a "Flexible
  concrete Error type built on std::error::Error"; `anyhow::Result<T>` is `Result<T, anyhow::Error>`,
  and `.context()` turns a low-level message such as "No such file or directory" into one that names
  what was being attempted (https://docs.rs/anyhow).
- **The split between the two crates is the crate kind, and both crates say so.** thiserror's own
  documentation "notes that **anyhow** is recommended for applications, while thiserror suits library
  code" (https://docs.rs/thiserror), and anyhow's says the same from its side — anyhow "suits
  application-level error handling", thiserror "is recommended for library code where you want to
  define specific, domain-specific error types that library consumers can handle"
  (https://docs.rs/anyhow). A library that reached for `anyhow` would hand its callers an opaque
  error they cannot match on, which is the thing `arch_defaults.md` § Exception shape exists to
  prevent.
- **An error is never discarded.** `let _ = fallible();` and a `match` arm that returns `Ok(())` on
  the error path both turn a failure into behaviour nobody can find. Where continuing really is
  correct, the error is logged at `warn` and the line says why continuing is correct.

## Logging

- **A library crate depends on the facade and initializes nothing.** Both crates state it in the
  same words: libraries "should depend only on the `log` crate and use its macros to record
  diagnostic information" (https://docs.rs/log), and libraries "should link only to the `tracing`
  crate, and use the provided macros to record whatever information will be useful to downstream
  consumers" (https://docs.rs/tracing). Neither initializes anything, for the same reason: the
  consumer picks the backend, and a library that picked one would impose it on every product that
  links it.
- **A binary crate selects an implementation and initializes it once, early.** On `log`, executables
  "must select a logging implementation and initialize it early in program execution", because "The
  logging system may only be initialized once" and anything logged before that is discarded
  (https://docs.rs/log); on `tracing` they "use a `Subscriber` implementation compatible with
  `tracing`" (https://docs.rs/tracing). Same obligation, two names. `layout.md` puts that call in
  `src/main.rs`, which is already the composition root.
- **The ladder is the same five macros whichever crate is chosen** — `error!`, `warn!`, `info!`,
  `debug!`, `trace!`, highest priority first (https://docs.rs/log); `tracing` exposes the same five
  "which may be invoked with the same syntax as the similarly-named macros from the `log` crate"
  (https://docs.rs/tracing). What belongs at each is the packet author's call, 2026-09-02, written so
  that a reader can place a line without asking:

  | Level | What belongs at it |
  |---|---|
  | `error!` | a failure the product could not complete, logged once, where it stops |
  | `warn!` | a degraded outcome the product continued past, with the reason it was safe to continue |
  | `info!` | an event a reader would want in a normal session — a resource opened, a command accepted |
  | `debug!` | detail useful while tracing one operation |
  | `trace!` | per-item or per-iteration detail, off outside an investigation |

- **A failure is logged once, at the point that stops.** A layer that logs and then propagates
  produces one failure several times at several levels, and the reader cannot tell one failure from
  three. Everything between the raise and the stop adds context with `?` and `.context()` rather than
  a log line.
- **A secret never enters a log line or an error message.** That rule is not this packet's — it is
  `quality_defaults.md` § Secrets, "A secret is never written to a log, an error message, or a
  completion report" — and it binds the `Display` implementation of an error type as much as it binds
  a `log` call, because a `Display` that interpolates a value has put that value into every reporter
  downstream.

### Which facade — `log` or `tracing`

**Either. The packet fixes no default; the product chooses and records the choice in its own
`docs/nfdr.md`.** Owner's call, 2026-09-02, relaxing this file's first shape, which made `log` the
default and `tracing` the exception. The ground for relaxing it: this packet's own method. Every
other rule in it names the source in the sentence that states it, and the `log` default named none —
there was no house practice to generalise from, because this instance had no Rust at all when the
packet was written, and the crate docs establish the two as alternatives rather than ranking them. A
default with no source is a preference stated as a rule, and it is the one shape this packet said it
would not write.

**Every rule above holds under both, which is what makes the choice cheap.** The facade-in-a-library
split, the initialize-once-in-the-binary rule and the five-macro ladder are each stated by both
crates in the same terms, cited where they appear. So the choice moves the crate name and nothing
else in this file.

**What actually discriminates, when a product has to decide.** `tracing` is "Application-level
tracing for Rust", and what it adds is the span — a period of time with a beginning and an end,
tracking execution flow through a context — plus "typed data as well as textual messages" recorded as
fields (https://docs.rs/tracing). So: diagnostics that have to be **queried by field, or attributed
to a concurrent operation**, want `tracing`; diagnostics **read as lines** do not, and `log` is the
smaller dependency. A product that cannot tell which it has, has the second.

**It is not a fork paid for twice.** `tracing` "provides interoperability with the `log` crate through
optional feature flags", `tracing-log` lets a subscriber consume `log` records as tracing events, and
converting a project can "begin with a simple drop-in replacement" (https://docs.rs/tracing). A
library on `log` is readable from a binary on `tracing`, which is why the library rule above does not
need to know what the binary chose — and why a product that chose wrong is not stuck with it.

**Recording it is the part that is not optional.** The choice belongs in the product's own
`docs/nfdr.md`, not in a habit spread across its crates: a product where the answer is whatever the
last file did has no answer, and `languages/README.md` § Precedence — which ranks a packet above "the
surrounding code's own habits" — has nothing to rank.
