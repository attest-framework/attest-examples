import { AttestReporter } from "@attest-ai/vitest/reporter";
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    // A runner with an empty HOME downloads the attest engine on the first evaluate() (about 5s
    // here, longer on a slow link) and Mastra starts cold: vitest's 5s default is not enough.
    testTimeout: 60_000,
    // Prints the replay summary (`N replayed · N live model calls`) and writes report-v2.
    reporters: ["default", new AttestReporter({ outputFile: "attest-report.json" })],
  },
});
