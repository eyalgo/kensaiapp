---
version: "2.0.0"
---

# Swift — gate environment

Where Swift's gates run, how that environment is provisioned, and how it is held to the toolchain the
product's CI builds with. It also holds the one statement of how the macOS guest is set up, which
every packet whose gates run in the guest points at. The defaults every language shares are
`languages/README.md` § Gate environment defaults: the CI runner deciding the environment, the
container runtime and its architecture, a product's override, and the product with no CI. This file
restates none of them. The toolchain-version policy is `toolchain.md`'s, and the gates themselves are
`quality_gates.md` and `testing.md`.

## Default and CI alignment

**Swift's gates run in a Tart macOS guest, on image `ghcr.io/cirruslabs/macos-tahoe-xcode:26.5`,
which carries Apple Swift 6.3.2.** That is the owner's ruling of 2026-10-14.

**The guest's Swift is held to the toolchain version the product's CI builds with.** The product writes
that version down as `toolchain.md` § Toolchain version — the `swift-tools-version` line states: a
committed `.swift-version` where the product installs its toolchains through swiftly, and otherwise a
record in its own `docs/nfdr.md`. The guest's `swift --version` is compared with that record. The
`swift-tools-version` line is not the comparison, because "the line is a floor, not a pin" (same
section).

**A patch-level gap between the guest's Swift and CI's Swift is accepted.** That is the owner's ruling
of 2026-10-14.

**Swift has no container default.** A Swift product whose CI runs on Linux can use neither environment
this packet names, so it states its environment in its own decision files
(`languages/README.md` § Gate environment defaults).

## In the macOS guest

| Tool | Folder |
|---|---|
| `swift` | — |

The image carries it: inside the guest, `command -v swift` prints `/usr/bin/swift`, a folder on the
guest's own PATH. So there is no install step.

## macOS guest provisioning

One macOS guest serves every gate on a host that runs in the guest, whichever instance, project,
worktree or core copy the gate comes from. The guest is started once, at the owner's login, with a
fixed set of shares, and is kept running. A gate reaches its checkout inside the guest through the
share that holds it — the share proves the guest reaches the checkout, and step 4 says where the
gate builds — so no guest is ever started or shared for one checkout.

**The host's guest is named `kensai-macos`.** The name says what the guest is for on the host, and
names no product and no satellite. It is the architect's choice, 2026-10-15.

**The guest is started with these shares and no others:**

- `products` — the products root, the folder that holds the products' own repositories.
- One share for each instance repository that holds a product inside it, named by the repository's
  folder name.

**The home directory is never a share.** A share is read-write by default ("mount this directory
share in read-only mode instead of the default read-write", `tart run --help`, Tart 2.41.0, the
`--dir` option's `ro` text). On this reading, a shared home directory would hand the guest everything
in it, the owner's credentials file included.

**The shares are virtiofs shares, mounted inside the guest under `/Volumes/My Shared Files`.** By
default "the "com.apple.virtio-fs.automount" mount tag is used for all directory shares. On macOS,
this causes the directories to be automatically mounted to "/Volumes/My Shared Files" directory"
(`tart run --help`, Tart 2.41.0, the `--dir` option's `tag=` text). A share's name is its folder
there: "These names will be used as directory names under the mounting point inside guests" (the
same option). A checkout is reached inside the guest at its path under its share. A worktree at
`<products root>/<product>/.worktrees/<key>` is at
`/Volumes/My Shared Files/products/<product>/.worktrees/<key>`.

1. **Clone the image into the base, once.** `tart clone` "Creates a local virtual machine by
   cloning either a remote or another local virtual machine" (`tart clone --help`, Tart 2.41.0).

   ```sh
   tart clone ghcr.io/cirruslabs/macos-tahoe-xcode:26.5 kensai-macos-base
   ```

   The base is the provisioned guest. It is kept as provisioned, and no gate runs in it.

   **Then install into the base the tools of the languages the cards declare, and no others.** The
   languages are the `Languages:` of each project card whose product's CI runs on macOS. For each
   one, its packet's § In the macOS guest names the tool its gates run with and the step that
   installs it. A Swift-only card adds nothing, because the image already carries Swift. A card
   that declares Rust adds rustup. A language no card declares is not installed.

   `<CORE>/tools/gate_suite.py` looks in the guest, before it issues a suite, for the tool of each
   language the run resolves, and for no other. Those are the languages
   `languages/README.md` § The resolution chain reaches: the card's `Languages:`, else the
   invocation's, else the ones inferred from the product's tracked files. For a card that declares
   its languages, that is exactly the set installed here. A card that declares none can have a
   language inferred that the base was never given, and its run stops at the probe; the fix is to
   declare the languages on the card. The tool also refuses a resolved language whose packet names
   no guest tool. So a guest built without a resolved language's tool stops the run as not run,
   not as a failing suite. The install goes into the base, because step 5 re-clones the guest from
   the base and so erases anything installed in the guest itself. Start the base, run the install
   step of each declared language in it, and stop it:

   ```sh
   tart run --no-graphics kensai-macos-base &
   tart exec -i kensai-macos-base sh <<'EOF'
   <the install step a packet names>
   EOF
   tart stop kensai-macos-base
   ```

   The step goes to the guest's shell on standard input, so its own quotes reach it as written:
   `-i` is "Attach host's standard input to a remote command" (`tart exec --help`, Tart 2.41.0), and
   the quoted `'EOF'` keeps the host's shell from expanding anything inside it.

   `tart exec` answers once the guest has booted. Until `tart exec kensai-macos-base true` exits 0,
   the install step has nothing to run in.

   A card that later declares a language the base lacks is met the same way: install that
   language's tool into the base, then reset the guest from the base as step 5 states.

2. **Clone the guest that runs from the base.**

   ```sh
   tart clone kensai-macos-base kensai-macos
   ```

3. **Start the guest at the owner's login, with its shares, and keep it running.** A launchd agent,
   `local.kensaiapp.macos-guest`, does it. Write it to
   `~/Library/LaunchAgents/local.kensaiapp.macos-guest.plist`, the folder of "Per-user agents
   provided by the user" (`man launchd`, FILES). `RunAtLoad` launches the job "once at the time the
   job is loaded", and `KeepAlive` set to true is "to unconditionally keep the job alive"
   (`man launchd.plist`). `--no-graphics` runs the guest with no window: "Don't open a UI window"
   (`tart run --help`).

   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
     <key>Label</key>
     <string>local.kensaiapp.macos-guest</string>
     <key>ProgramArguments</key>
     <array>
       <string><path to tart></string>
       <string>run</string>
       <string>--no-graphics</string>
       <string>--dir=products:<products root></string>
       <string>--dir=<instance>:<instance repository></string>
       <string>kensai-macos</string>
     </array>
     <key>RunAtLoad</key>
     <true/>
     <key>KeepAlive</key>
     <true/>
   </dict>
   </plist>
   ```

   `<path to tart>` is the absolute path `command -v tart` prints. `<products root>` and each
   `<instance repository>` are absolute host paths. Repeat the `--dir=<instance>:<instance repository>`
   line once for each instance repository that holds a product, with `<instance>` its folder name.
   These `--dir` arguments are the record a gate's caller reads its shares from
   (`<CORE>/prompts/gate_suite.md` § Step 3, The guest).

   Load the agent now, without waiting for the next login:

   ```sh
   launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/local.kensaiapp.macos-guest.plist
   ```

   `gui/<uid>` is the owner's login domain: `man launchctl` calls it "Another form of the login
   specifier", and "A user-login domain is created when the user logs in at the GUI". The reason to
   expect the guest to start at every later login is that launchd loads the agents in
   `~/Library/LaunchAgents` into that domain when the owner logs in.
   `launchctl print gui/$(id -u)/local.kensaiapp.macos-guest` after a login shows whether it did, and
   `tart list` shows `kensai-macos` with the state `running`.

4. **Run each gate inside the guest, in a copy of its checkout on the guest's own disk.** `tart exec`
   runs a command in a running guest, and it "Requires Tart Guest Agent running in a guest VM", which
   "all non-vanilla Cirrus Labs VM images already have" (`tart exec --help`, Tart 2.41.0). Its `-i`
   option will "Attach host's standard input to a remote command" (same help), so the checkout is
   streamed in from the host:

   ```sh
   tar -C <checkout> --no-mac-metadata --exclude '^./<package>/.build' -cf - . \
     | tart exec -i kensai-macos sh -c 'mkdir /tmp/<copy> && tar -C /tmp/<copy> -xf -'
   tart exec kensai-macos sh -c 'cd /tmp/<copy> && <gate command>'
   tart exec kensai-macos sh -c 'rm -rf /tmp/<copy>'
   ```

   `<gate command>` is a command from the language's Quality gates or Testing answer.

   **A gate never builds on the share, and never copies through it.** The guest's view of a share
   goes stale for a file the host replaced by renaming a new one over it. Editors, compilers and
   Python's byte-code cache all write that way. Opening the file in the guest then fails with "No
   such file or directory" while the guest still lists it, and it still failed 45 minutes later.
   Measured 2026-10-17, Tart 2.41.0, guest `kensai-macos`: a file written on the host and then
   replaced by `mv` could not be read in the guest, and `ditto` and `rsync` copies through the share
   failed on it. Builds on the share failed the same way, with errors that were not the code's. The
   SwiftPM errors were "failed to rename … No such file or directory" and "input file
   '…/runner.swift' was modified during the build". Five runs on one tree exited 1, 0, 1, 1, 1. A
   copy built in the guest, not read through the share, passed.

   `<CORE>/tools/gate_suite.py` does this for a gate. It refuses a checkout under none of the
   shares, and finds the checkout through its share to prove the guest reaches it. It streams the
   copy without build output: the `.build` folder beside each tracked `Package.swift` and the
   `target` folder beside each tracked `Cargo.toml`, each matched by its exact path from the
   checkout's root. Build output holds the absolute paths it was built at, and the build in the copy
   makes its own. A folder or file of those names anywhere else is copied. It removes any copy an earlier run left, then runs
   the gate command in the new copy, then removes it. It runs one gate in the guest at a time: a
   second gate waits until the first gate's copy is removed. It never starts, stops or restarts the
   guest.

   **What the tool reports as the environment's failure, and what it does not.** A copy that fails
   is reported as the environment's failure, and no suite is issued, so a broken copy never reads as
   a red suite. A failure inside the gate command itself is the gate command's exit, whatever caused
   it. The tool does not read a build's output to tell the environment's errors from the code's.

5. **Reset the guest to the base when it drifts.** Caches and tools that runs leave behind are
   cleared by deleting the guest and re-cloning it from the base. Unload the agent first, because
   `KeepAlive` would otherwise start the guest again:

   ```sh
   launchctl bootout gui/$(id -u)/local.kensaiapp.macos-guest
   ```

   Wait until `tart list` shows `kensai-macos` with the state `stopped`, and run
   `tart stop kensai-macos` if it does not. Then delete the guest, re-clone it and load the agent
   again:

   ```sh
   tart delete kensai-macos
   tart clone kensai-macos-base kensai-macos
   launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/local.kensaiapp.macos-guest.plist
   ```

**The build cost of a share, measured.** One clean build of a Rust package and one of a Swift package
were each timed twice in the same guest: once with the source and its build output on a virtiofs
share, and once with the same source on the guest's own disk. Each build started with no build
output, and the two locations shared no build cache.

| Build | Source and build output | Command | Wall-clock time |
|---|---|---|---|
| Rust | a virtiofs share | `cd "/Volumes/My Shared Files/measure/rust" && /usr/bin/time -p cargo build --release` | 20.68 s |
| Rust | the guest's own disk | `cd /Users/admin/own/rust && /usr/bin/time -p cargo build --release` | 20.57 s |
| Swift | a virtiofs share | `cd "/Volumes/My Shared Files/measure/swift" && /usr/bin/time -p swift build -c release` | 89.94 s |
| Swift | the guest's own disk | `cd /Users/admin/own/swift && /usr/bin/time -p swift build -c release` | 87.67 s |

Measured on 2026-10-15, with Tart 2.41.0, in a guest cloned from
`ghcr.io/cirruslabs/macos-tahoe-xcode:26.5` for the measurement and deleted afterwards. The Rust
package was a generated library crate of 200 modules, built with rustc and cargo 1.98.1, a package with no dependencies. The Swift package was a generated SwiftPM package of 150 source files, built with Swift 6.3.2, a package with no dependencies.
