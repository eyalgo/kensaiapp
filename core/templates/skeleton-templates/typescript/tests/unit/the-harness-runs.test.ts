/**
 * One passing test, so a freshly stamped product's test gate proves something.
 *
 * Without it `vitest run` finds no test files and exits 1, and the product fails a gate while
 * working exactly as intended. Making the empty case pass would fix the exit code and prove nothing;
 * this proves the harness is wired — vitest resolved the `node` project's `include`, compiled a
 * TypeScript module, and imported the product's own.
 *
 * Delete it once this product has a real test. It is scaffolding, not a test of the product.
 */

import { describe, expect, it } from "vitest";

import { AppError } from "../../src/app-error";

describe("the harness", () => {
  it("runs and can import the product", () => {
    expect(new AppError("probe")).toBeInstanceOf(Error);
  });
});
