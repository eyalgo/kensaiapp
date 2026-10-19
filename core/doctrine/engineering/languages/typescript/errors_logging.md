---
version: "1.1.1"
---

# TypeScript — errors and logging

How a TypeScript product here raises a failure, wraps one, propagates one, and emits an event.
Naming and shape rules that are not about a failure or an event are `conventions.md`. The commands
that check any of this are `quality_gates.md`.

## Raising

- **Only an `Error`, or a subclass of one, is thrown.** A thrown string or object literal carries no
  stack, and every `catch` in the product then has to handle a shape the type system cannot describe.
- **A product declares one named base error and every typed error extends it** —
  `class AcmeError extends Error {}` in a product called acme, then
  `class FileNotFound extends AcmeError {}`. This is
  `arch_defaults.md` § *Exception shape*, which is language-agnostic and reaches TypeScript directly —
  the Python spellings are `arch_defaults_python.md`'s, not the body's (the owner's call, 2026-08-30).
  What it buys is the same: one `catch` at the entry point can distinguish the product's own
  failures from everything else.
- **An error subclass sets its own `name` in the constructor** — `this.name = "FileNotFound"`. The
  built-in `name` is inherited from `Error` and reads as `"Error"`, and a bundler is free to rename
  the class itself, so `constructor.name` is not a stable label in a built product.
- **A message says what failed and on what**, and it carries the identifier the reader needs —
  `Cannot read workspace file: ${path}`. A message that only says an operation failed sends the
  reader back to the stack for the one fact the message was supposed to carry.

## Wrapping and propagating

- **An error crossing a boundary is rethrown with the original as its `cause`**, never swallowed and
  never replaced. The form is the one in the platform's own documentation:

  ```ts
  try {
    connectToDatabase();
  } catch (err) {
    throw new Error("Connecting to database failed.", { cause: err });
  }
  ```

  (https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Error/cause —
  `cause` is Baseline widely available, across browsers since September 2021, which is why
  `quality_gates.md` sets `target` to ES2022 rather than lower.)

- **A caught value is `unknown` and is narrowed before it is read.** `useUnknownInCatchVariables`
  makes that the type (https://www.typescriptlang.org/tsconfig/useUnknownInCatchVariables.html), so
  `catch (err) { log(err.message) }` fails the type gate. `err instanceof Error` is the narrowing;
  the `else` branch is real, because a value thrown from a dependency may be anything.
- **An empty `catch` block is never correct.** Where continuing really is safe, the block logs at
  `warn` and the log line says why continuing is safe. A silent catch turns a failure into behaviour
  nobody can find.
- **A promise is awaited or its rejection is handled, never left floating.** An unhandled rejection
  is reported by the runtime rather than by the code that caused it, which puts the report a long way
  from the cause. The type-aware lint gate is what catches this one.
- **A failure the caller is expected to handle in normal operation is a return value, not a throw.**
  A function that returns `FileTree | undefined` for a path that is absent describes an ordinary
  outcome; throwing for it makes every caller write a `try` around the normal case.

## Logging

- **One module owns the sink.** `src/logger.ts` exports the level functions, and nothing else in the
  product calls `console` directly. The reason to keep one seam: the level floor, the format and the
  destination each change in one file, and a product that scatters `console.log` has no such file to
  change.
- **The ladder has four levels, and it is the platform's own** — `debug`, `info`, `warn`, `error`.
  Each names a `console` method the browser documents as carrying that level, in the form "Outputs a
  message to the console with the debug log level", and "you can use the filtering controls provided
  by your browser to view only the kinds of output that interest you"
  (https://developer.mozilla.org/en-US/docs/Web/API/console). `console.log` is described there
  without a level — "Outputs a message to the console" — so it carries none, and it never appears in
  product code.

  | Level | What belongs at it |
  |---|---|
  | `debug` | detail useful while tracing one operation, off in a production build |
  | `info` | an event a reader would want in a normal session — a workspace opened, a file selected |
  | `warn` | a degraded outcome the product continued past |
  | `error` | a failure the product could not complete, logged once, where it stops |

- **Context is passed as an object, not interpolated into the message.** The form is
  `logger.info("file selected", { path, language })`, not a template literal that flattens both
  into one string.
  The reason: the browser console renders an object as an inspectable structure and a string as one
  line, and a machine reading the output later can key on `path` only if `path` is still a field.
- **A failure is logged once, at the point that stops.** A layer that logs and rethrows produces the
  same failure several times at several levels, and the reader cannot tell one failure from three.
- **A secret, a token, a credential or the contents of a user's file never enter a log line.** This
  binds the object form above as much as the message: a context object logged whole is a context
  object whose fields were all chosen deliberately.
