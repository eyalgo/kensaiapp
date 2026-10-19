---
version: "1.1.0"
---

# Swift — packet router

Routes each of the seven language-packet concerns to the file that answers it for Swift, and answers
none of them itself. The concern set, the router rule, the resolution chain, precedence and the
packet lifecycle are one level up, in `languages/README.md`.

## The seven concerns and where each is answered

| Concern | Destination |
|---|---|
| Toolchain | `toolchain.md` |
| Layout | `layout.md` |
| Quality gates | `quality_gates.md` |
| Conventions | `conventions.md` |
| Errors and logging | `errors_logging.md` |
| Testing | `testing.md` |
| Gate environment | `environment.md` |

Each destination is a file in this folder, beside this one.

Every one of the seven refines `<CORE>/doctrine/engineering/languages/developer_standards.md`, the language-agnostic
floor, and none replaces it. A rule the floor states and this packet never mentions is still in force
over Swift code.

## What the packet leaves to the product

Which kind of project a Swift product here is — a SwiftPM package, not an Xcode project — is the
Toolchain concern's answer, in `toolchain.md` § *Build system and package manager*. The packet's
default of zero dependencies, and how a product departs from it, are also `toolchain.md`'s, in
§ *Adding, pinning and locking a dependency*.

What sits outside the language is the product's to record in its own decision files, which outrank
this packet per `languages/README.md` § Precedence: how an app bundle is assembled and signed, which
entitlements it carries, and which platforms and deployment targets it supports.

## What the registry row claims

`.swift`, and no second extension. `Package.swift` is Swift source as well as the manifest, so the
row reaches it. `.h`, `.c` and `module.modulemap` files in a package are C and Clang, which a Swift
package can host (`layout.md` § *C interop*), and they are not Swift source.

**A Swift product is reached by extension inference only once it has source tracked in git.** Step 3 of
`languages/README.md` § The resolution chain infers the language from "the file extensions present
under the working root", so a product at design stage is reached through step 1 or step 2 instead:
its `project.md` `Languages:` line, or the invocation.

## Where this packet's rules come from

No Swift product source is tracked in this instance. The only Swift files are the skeleton tree's,
`core/templates/skeleton-templates/swift/`, which this packet's rules produced rather than came
from. On 2026-09-23 this command printed `0`:

```sh
git ls-files '*.swift' 'Package.swift' 'Package.resolved' '*.modulemap' | grep -v '^core/templates/skeleton-templates/swift/' | wc -l
```

So no rule here was
read off code in this repository. Each rule instead names its source in the sentence that states it,
and the sources are of five kinds:

- the Swift project's own documentation — swift.org, the Swift Package Manager, Swift Evolution,
  swift-format, swift-testing, swiftly and swift-migration-guide repositories, The Swift Programming
  Language, and the Swift Forums;
- Apple's developer documentation and the interfaces in Apple's SDK;
- a published practice, with its URL — the Google Swift style guide, and the READMEs of third-party
  tools the packet weighs (SwiftLint, SwiftFormat, SwiftLog, OWASP Dependency-Check);
- this house's own doctrine — `arch_defaults.md`, `quality_defaults.md`, `testing_doctrine.md` and
  the floor, `<CORE>/doctrine/engineering/languages/developer_standards.md`;
- a measurement taken on 2026-09-23 with Apple Swift 6.3.3 on a Mac with the Command Line Tools
  only, or with Xcode 27.0 (Apple Swift 6.4) where the sentence says so, with the command stated.

Where a call was the packet author's rather than a source's, the sentence says so and gives the
ground.

**The SwiftPM documentation is cited at its source files in `github.com/swiftlang/swift-package-manager`,
pinned to the `swift-6.3.3-RELEASE` tag, and that is the packet author's call, 2026-09-23.** The
ground is that the packet measured its rules against Apple Swift 6.3.3, so the text it quotes is the
text that ships with that release, not the development tip. On 2026-09-23 every quotation from a
file at that tag was checked present there. Two files are cited at `main` instead, and the
sentence citing each says why: `ModuleMaps.md`, which does not exist at the 6.3.3 tag, and
`MinimumDeploymentTarget.swift`, where `main` differs from the release. The rendered articles are
also live at `docs.swift.org/latest/documentation/packagemanagerdocs/<article>` (measured 2026-09-23:
`…/gettingstarted` returned `200`, a made-up article under the same path returned `404`), but
`latest` follows the newest release, while the tag stays on the one the packet measured. The older
`docs.swift.org/swiftpm/documentation/packagemanagerdocs/<article>` addresses redirect to a page that
returns `404`.

**A rule here is checked against the first Swift tree this instance writes.** Where that tree
contradicts a rule, the correction lands in this packet, not as a local departure inside the product.
`languages/README.md` § Precedence ranks a packet above "the surrounding code's own habits", and that
is what makes the packet the thing that moves.
