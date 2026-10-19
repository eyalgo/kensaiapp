use thiserror::Error;

/// __PROJECT__'s single named base error. One variant per distinct failure condition.
#[derive(Debug, Error)]
pub enum Error {
    // One variant per condition this crate raises, e.g.:
    // #[error("...")]
    // SomeCondition,
}

#[cfg(test)]
mod tests {
    //! One passing test, so a freshly stamped product's test gate proves something.
    //!
    //! `cargo test` exits 0 with nothing to run, which is a pass that proves nothing ran. This
    //! proves the harness is wired — cargo compiled the crate with `cfg(test)` and ran a test
    //! against this module's own type.
    //!
    //! Layer 1, `#[cfg(test)] mod tests` inside the module's own file, per
    //! `<CORE>/doctrine/engineering/languages/rust/testing.md`. An integration test under `tests/`
    //! would have to name the crate, and the crate is named from the product's package slug — a
    //! slug with a hyphen is a legal Cargo package name and an illegal Rust identifier.
    //!
    //! Delete it once this module has a real test. It is scaffolding, not a test of the product.

    use super::Error;

    #[test]
    fn the_harness_runs_and_can_reach_the_error_type() {
        // `Error` has no variants yet, so there is nothing to construct — that this compiles at all
        // is what proves the crate built under cfg(test) and the type is reachable.
        fn _accepts_the_error_type(_: Option<Error>) {}
    }
}
