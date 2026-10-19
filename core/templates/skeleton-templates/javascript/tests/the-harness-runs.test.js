// One passing test, so a freshly stamped product's test gate proves something.
//
// `node --test` exits 0 with no test files at all, which is a pass that proves nothing ran. This
// proves the harness is wired — the runner matched the glob in `package.json`, loaded an ES module,
// and imported the product's own module.
//
// Delete it once this product has a real test. It is scaffolding, not a test of the product.

import assert from 'node:assert/strict'
import { test } from 'node:test'

import { BaseError } from '../errors.js'

test('the harness runs and can import the product', () => {
  assert.ok(BaseError.prototype instanceof Error)
})
