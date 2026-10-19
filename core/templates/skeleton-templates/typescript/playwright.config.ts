import { defineConfig } from "@playwright/test";

// testing.md: "Layer 5 is Playwright, and it drives the built output rather than the dev
// server." A product wires `webServer` / `use.baseURL` at the built output once it has one to
// build; the frame fixes only where the layer-5 spec files live.
export default defineConfig({
  testDir: "tests/e2e",
});
