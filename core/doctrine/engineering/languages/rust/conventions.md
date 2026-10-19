---
version: "1.0.1"
---

# Rust — conventions

Naming, the constructs this house prefers and avoids, and how each floor rule lands in Rust. Every
rule here is one a reader applies, because a rule a tool can fail the build on belongs in
`quality_gates.md` instead. What the code does at a failure or an event is `errors_logging.md`. Where
a file goes and what the file is called is `layout.md`.

## Casing

The casing is RFC 430's, and this packet adds nothing to it
(https://rust-lang.github.io/api-guidelines/naming.html):

| Item | Case |
|---|---|
| Modules | `snake_case` |
| Types, traits, enum variants | `UpperCamelCase` |
| Functions, methods, local variables | `snake_case` |
| Macros | `snake_case!` |
| Statics and constants | `SCREAMING_SNAKE_CASE` |
| Type parameters | concise `UpperCamelCase`, usually a single letter — `T` |
| Lifetimes | short lowercase, usually a single letter — `'a`, `'de`, `'src` |

The shape behind the table, in the guidelines' own words: "Rust tends to use `UpperCamelCase` for
'type-level' constructs (types and traits) and `snake_case` for 'value-level' constructs" (same
page). A constructor is `new`, or `with_more_details` where it takes options, and a conversion
constructor is `from_some_other_type` (same page).

## Documentation comments, and the floor's one comment exception

The floor states that "A comment that says *what* the code does is the smell", allows one exception
for "a comment recording *why* the code is shaped this way and not the obvious other way, with a
citation", and hands the language-specific form to this file
(`<CORE>/doctrine/engineering/languages/developer_standards.md`). In Rust the form is three comment kinds doing
three different jobs:

- **`///` documents the item that follows it** — a function, a type, a trait
  (https://doc.rust-lang.org/rustdoc/how-to-write-documentation.html). This is where a public item's
  contract goes, and it satisfies the floor's "Every public interface has an explicit contract".
- **`//!` documents the enclosing item** — the module or the crate, written at the top of `lib.rs` or
  of a module file (same page). `layout.md` puts the crate-level `//!` in `src/lib.rs`.
- **`//` is an ordinary comment, and it is where the floor's exception lives.** A `//` line that says
  *what* the next line does is the smell the floor names; a `//` line saying *why* this shape and not
  the obvious other one, with its citation, is the exception the floor grants.

**A `///` on a public item carries a worked example, and the example is a test.** "Running
`cargo test` will run the code examples in your documentation as tests", and the run reports them
under a `Doc-tests` heading (https://doc.rust-lang.org/book/ch14-02-publishing-to-crates-io.html).
That is the reason this packet asks for the example rather than treating it as decoration: a contract
stated in prose cannot fail, and a contract stated as an example does, the moment the code moves
away from it. `testing.md` says where doc tests sit relative to the seven testing layers.

## The constructs this house prefers

- **A binding is immutable unless it is written to.** Rust's default is already this — "by default,
  variables are immutable" — and the Book's reason for it is the same one the floor gives for
  preferring immutable data: "If one part of our code operates on the assumption that a value will
  never change and another part of our code changes that value, it's possible that the first part of
  the code won't do what it was designed to do"
  (https://doc.rust-lang.org/book/ch03-01-variables-and-mutability.html). So `mut` is not a style
  choice to be minimised for tidiness; it is a claim the reader is entitled to check, since "Adding
  `mut` also conveys intent to future readers of the code by indicating that other parts of the code
  will be changing this variable's value" (same page). This is the Rust landing of the floor's
  "Immutable data structures unless mutability is required".
- **A value with a closed set of possibilities is an `enum`, never a string.** The floor asks the
  implementer to "Upgrade imprecise constructs encountered during implementation (string with a
  closed value set → enum) — even if the input contract did not say so"
  (`<CORE>/doctrine/engineering/languages/developer_standards.md`). Rust's enums carry data per variant, so the
  upgrade costs nothing that a string was buying, and the compiler's exhaustiveness check then makes
  a forgotten case a build failure rather than a runtime branch nobody took.
- **A magic value is a `const` at module scope.** Constants "are values that are bound to a name and
  are not allowed to change", the type "must be annotated", and the naming convention "is to use all
  uppercase with underscores between words"
  (https://doc.rust-lang.org/book/ch03-01-variables-and-mutability.html). This is the floor's "No
  magic numbers or strings — named constants", with the annotation requirement making the constant's
  meaning explicit as well as its name.
- **A unit is given its collaborators through a trait.** `arch_defaults.md` § Dependency Graph Rules
  states the rule language-agnostically — "Only the composition root imports concrete
  implementations. Every other module depends on abstractions" — and the trait is Rust's abstraction.
  Whether the collaborator arrives as a generic parameter bounded by that trait or as a trait object
  (`Box<dyn Trait>`, `&dyn Trait`) is the product's call: both satisfy the rule, and the choice is
  about dispatch cost and object safety rather than about the seam. What does not satisfy the rule is
  a unit that constructs its own collaborator, because `testing_doctrine.md` then has no door to hand
  a fake through — "Where the subject offers no door to hand a fake through, the defect is the
  subject's shape and not the test's" (`testing_doctrine.md` § Layers 1–5 — Code-Time (TDD)).

## The constructs this house avoids

- **A generic label for a type or a module.** The floor rejects "generic labels (`manager`,
  `handler`, `utils`)" (`<CORE>/doctrine/engineering/languages/developer_standards.md`), and Rust gives that rule an
  extra edge: a module's name is part of every path that reaches into it, so `utils::parse` tells a
  reader at the call site nothing that `parsing::parse` would not have told them better.
- **A single-letter name outside the two places the casing table sanctions them.** Type parameters
  and lifetimes are conventionally single letters (§ Casing above); a local variable is not, and the
  floor's "Intent-revealing names — no abbreviations" governs it.
- **`unsafe`.** It is refused by default rather than discouraged by convention, so the rule and its
  one escape hatch are `quality_gates.md` § Where the lint levels are written.
