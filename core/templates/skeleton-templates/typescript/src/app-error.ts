/**
 * The product's single named base error. Every typed error the product declares extends this one and
 * none derives directly from `Error`, so one `catch` at the entry point can distinguish the
 * product's own failures from everything else.
 *
 * `AppError` is a placeholder name: what is fixed is that a single base must exist and that
 * every product-specific error extends it, not what the base is called. A product commonly
 * renames it for its own identity — the product's own name followed by Error, extending Error.
 */
export class AppError extends Error {}
