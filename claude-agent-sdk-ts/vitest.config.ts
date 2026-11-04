import { AttestReporter } from "@attest-ai/vitest/reporter";
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    // Writes report-v2.
    reporters: ["default", new AttestReporter({ outputFile: "attest-report.json" })],
  },
});
