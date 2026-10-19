import Core
import Testing

// One passing test, so a freshly stamped product's test run proves something: `swift test` with
// no tests passes too, and that pass proves nothing ran. Layer 1, per
// <CORE>/doctrine/engineering/languages/swift/testing.md. Delete it once `Core` has a real test.
@Test func theHarnessRunsAndCanReachTheErrorType() {
    let noError: CoreError? = nil
    #expect(noError == nil)
}
