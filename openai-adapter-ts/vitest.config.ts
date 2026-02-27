import { defineConfig } from "vitest/config";
import { attestGlobalSetup } from "@attest-ai/vitest/setup";

export default defineConfig({
  test: {
    globalSetup: [attestGlobalSetup()],
  },
});
