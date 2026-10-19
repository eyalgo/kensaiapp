---
version: "1.0.1"
---

# TypeScript — conventions

Naming, the constructs this house prefers and avoids, and how each rule of
`<CORE>/doctrine/engineering/languages/developer_standards.md` lands in TypeScript. Nothing here is a command — the
commands are `quality_gates.md`. What the code does at a failure or an event is `errors_logging.md`.
Where files go and what they are called is `layout.md`.

Some rules below are enforceable by the lint gate and some are not, and that changes nothing about
their force: a rule here is a requirement whether or not a tool can see it.

## Naming

| Kind | Case | Example |
|---|---|---|
| Type, interface, class, enum-like constant object | `PascalCase` | `FileTree`, `EditorView` |
| Function, method, variable, parameter, property | `camelCase` | `selectedPath`, `readWorkspace` |
| Module-level constant with a fixed value | `SCREAMING_SNAKE_CASE` | `DEFAULT_SIDEBAR_WIDTH` |
| Type parameter | `PascalCase`, and a word | `Entry` or `Item`, never `TNode` or `T` |

- **No prefix that encodes the kind.** Not `IFileTree` for an interface, not `TNode` for a type
  parameter, not `_private` for a private field. The type system already says what each one is, and
  a prefix is a second statement of it that goes stale on its own.
- **A boolean reads as a claim about the subject** — `isReadOnly`, `hasUnstagedChanges`,
  `canOpenFile`. A boolean named for the branch it drives (`flag`, `check`, `doIt`) names the caller
  rather than the value.
- **The floor's ban on generic labels applies to names inside a module, not only to filenames**
  (`<CORE>/doctrine/engineering/languages/developer_standards.md`, "no generic labels"). A `Manager` class and a
  `handleData` function are the same defect as a `utils.ts`.

## The constructs this packet prefers

- **`type` for a data shape; `interface` only where declaration merging or `implements` is
  wanted.** The packet author's call, 2026-08-21. The reason: an `interface` can be reopened by any
  later declaration of the same name in the same scope, and a `type` cannot, so `type` is the form
  that says the shape is closed. Where the shape is deliberately an extension point, `interface` says
  so.
- **A closed set of values is a union of string literals, never an `enum`.** This is where the
  floor's rule that a "string with a closed value set" becomes an enum
  (`<CORE>/doctrine/engineering/languages/developer_standards.md`) lands in TypeScript, and it lands differently
  because `erasableSyntaxOnly` errors on `enum` declarations
  (https://www.typescriptlang.org/tsconfig/erasableSyntaxOnly.html; `quality_gates.md` requires the
  option). The TypeScript form of the floor's rule is the union, plus a frozen object when the
  values also need to be iterated:

  ```ts
  export type SidebarMode = "files" | "git";

  export const SIDEBAR_MODES = ["files", "git"] as const satisfies readonly SidebarMode[];
  ```

- **`satisfies` where a literal must be checked against a type without losing its own narrower
  type.** A plain annotation widens the literal and takes the precision with it; `satisfies` checks
  and keeps.
- **`readonly` on every property and array a caller is not meant to change**, and a function returns
  a new value rather than mutating its argument. This is the floor's "Immutable data structures
  unless mutability is required" made checkable by the type gate.
- **`#field` rather than `private field` where the field must actually be unreachable.**
  `private` is erasable syntax — it survives `erasableSyntaxOnly`, which errors on the class syntax
  that does have runtime behaviour, parameter properties
  (https://www.typescriptlang.org/tsconfig/erasableSyntaxOnly.html) — so it is a claim the type gate
  checks and the built output no longer carries. `#` is enforced by the runtime. `private` stays
  correct where the intent is only to keep the field out of the public contract.
- **Modules are ESM, and a relative specifier carries no file extension** — `import { readTree } from
  "./file-tree"`. `moduleResolution: "bundler"` in `quality_gates.md` is what makes that resolve,
  and it is the resolution Vite performs.
- **A type-only import says so** — `import type { FileTree } from "./file-tree"`. Under
  `verbatimModuleSyntax` an import is emitted as written, so an unmarked type import becomes a real
  runtime import of a module that may hold no runtime value at all.

## The constructs this packet avoids

- **`any`.** A value whose type is genuinely unknown at a boundary is `unknown`, and it is narrowed
  before it is used. `any` does not describe an unknown value — it switches the type gate off for
  every expression the value touches.
- **The non-null assertion `!`.** It asserts what the code has not checked. Where the value really
  cannot be absent, the check that proves it is cheap; where it can, `!` is where the runtime error
  comes from.
- **`as` outside a validated boundary.** A cast at the edge of a parse, immediately after the code
  that validated the shape, is a statement about work just done. A cast in the middle of a module is
  an assertion nothing backs.
- **A default export.** A named export has one spelling at every import site; a default export is
  renamed freely, and a search for the symbol then misses most of its uses.
- **A namespace.** `erasableSyntaxOnly` errors on namespaces with runtime code
  (https://www.typescriptlang.org/tsconfig/erasableSyntaxOnly.html), and a module is already the
  unit of scope.

## Comments

The floor states that a comment saying *what* the code does is the smell, allows one exception for a
comment recording *why* the code is shaped this way and not the obvious other way, and leaves each
language to say which comment form carries that exception
(`<CORE>/doctrine/engineering/languages/developer_standards.md`). For TypeScript:

- **The why-comment is a `//` line directly above the code it explains**, and it names the
  alternative that was rejected and the reason. A why-comment with no rejected alternative in it is
  a what-comment in the exception's clothing.
- **A TSDoc block `/** … */` sits above an exported declaration and carries its contract** — the
  invariants, the conditions under which it throws, and the units or ranges the types cannot
  express. This is the floor's "Every public interface has an explicit contract" in TypeScript, and
  it is the only comment form that belongs on an export.
- **A `@param` or `@returns` tag that restates the signature is deleted.** The signature is checked
  by the type gate and the tag is not, so the two drift in one direction only.
