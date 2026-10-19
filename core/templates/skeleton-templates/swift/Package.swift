// swift-tools-version: 6.2
// 6.2 is the floor, not a pin: it is the first PackageDescription that carries the three settings
// below. <CORE>/doctrine/engineering/languages/swift/toolchain.md § Toolchain version.
import PackageDescription

// Warnings are errors in the manifest, so every build enforces them and not only the gate's.
// Unsafe code must be marked `unsafe` where it is used, which is how a reviewer finds it.
// Both: <CORE>/doctrine/engineering/languages/swift/quality_gates.md § Types.
let strict: [SwiftSetting] = [
    .treatAllWarnings(as: .error),
    .strictMemorySafety(),
]

let package = Package(
    name: "__PROJECT__",
    // A starter default the product replaces with its own. The tree's test needs some deployment
    // target, because Swift Testing fails below macOS 10.15 where SwiftPM cannot derive one; 14 is
    // the minimum the toolchain's own Testing.framework declares.
    // <CORE>/templates/skeleton-templates/swift/README.md § The deployment target.
    platforms: [.macOS(.v14)],
    products: [
        .executable(name: "__PROJECT__", targets: ["App"])
    ],
    targets: [
        // The composition root, on the main actor. The library target is not.
        // <CORE>/doctrine/engineering/languages/swift/conventions.md, the concurrency rules.
        .executableTarget(
            name: "App",
            dependencies: ["Core"],
            swiftSettings: strict + [.defaultIsolation(MainActor.self)]
        ),
        .target(
            name: "Core",
            swiftSettings: strict
        ),
        .testTarget(
            name: "CoreUnitTests",
            dependencies: ["Core"],
            swiftSettings: strict
        ),
    ],
    swiftLanguageModes: [.v6]
)
