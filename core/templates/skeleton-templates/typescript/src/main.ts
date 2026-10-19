/**
 * The composition root. A product wires its own concrete implementations to abstractions here, once
 * those exist — this frame ships the wiring point and nothing to wire.
 *
 * It is not empty, and deliberately so: `index.html` loads this module, and a file holding only
 * comments is one `oxlint` refuses under `unicorn(no-empty-file)`, so a freshly stamped product
 * would fail its own `pnpm lint`. What it holds instead is the shape the root actually has — one
 * `start()` that a product fills in, called once at module load.
 */

import { logger } from "./logger";

/** Wires the product's dependencies and hands control to it. Empty until there is something to wire. */
export function start(): void {
  logger.debug("__PROJECT__ started");
}

start();
