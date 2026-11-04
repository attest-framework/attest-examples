import { AttestReporter } from "@attest-ai/vitest/reporter";
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    // Prints the replay summary (`N replayed · N live model calls`) and writes report-v2.
    reporters: ["default", new AttestReporter({ outputFile: "attest-report.json" })],
  },
});
