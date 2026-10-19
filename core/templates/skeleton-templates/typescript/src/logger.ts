/**
 * The one module that owns the console sink. Nothing else in the
 * product calls `console` directly, so the level floor, the format and the destination each
 * change in this one file.
 */

type LogContext = Record<string, unknown>;

export const logger = {
  /** Detail useful while tracing one operation, off in a production build. */
  debug(message: string, context?: LogContext): void {
    if (context === undefined) console.debug(message);
    else console.debug(message, context);
  },
  /** An event a reader would want in a normal session. */
  info(message: string, context?: LogContext): void {
    if (context === undefined) console.info(message);
    else console.info(message, context);
  },
  /** A degraded outcome the product continued past. */
  warn(message: string, context?: LogContext): void {
    if (context === undefined) console.warn(message);
    else console.warn(message, context);
  },
  /** A failure the product could not complete, logged once, where it stops. */
  error(message: string, context?: LogContext): void {
    if (context === undefined) console.error(message);
    else console.error(message, context);
  },
} as const;
