// This product's single named base error type. Every typed error derives from it, and none
// derives directly from the language's root error type — so one `catch` at an entry point can
// tell this product's failures from everything else. A typed error for one condition subclasses
// this rather than throwing `Error` directly, once a caller needs to branch on the type. A wrap
// preserves the original: pass `{ cause }` through the constructor below.

export class BaseError extends Error {
  constructor(message, options) {
    super(message, options)
    this.name = this.constructor.name
  }
}
