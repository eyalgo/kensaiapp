import { defineConfig } from "vitest/config";
import { playwright } from "@vitest/browser-playwright";

// testing.md's own reason for this file: "test.projects, which is what lets layers 1-3 run in
// Node while layer 4 runs in the browser." Layer 6 (architecture) is a Vitest assertion over the
// module tree, not the DOM, so it runs in the same Node project as layers 1-3.
export default defineConfig({
  test: {
    projects: [
      {
        test: {
          name: "node",
          environment: "node",
          include: [
            "tests/unit/**/*.test.ts",
            "tests/integration/**/*.test.ts",
            "tests/application/**/*.test.ts",
            "tests/architecture/**/*.test.ts",
          ],
        },
      },
      {
        test: {
          name: "ui",
          include: ["tests/ui/**/*.test.ts"],
          browser: {
            enabled: true,
            provider: playwright(),
            instances: [{ browser: "chromium" }],
          },
        },
      },
    ],
  },
});
