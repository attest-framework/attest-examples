// Contracts drafted by `attest capture` from fixture "claude-agent-sdk-ts".
//
// Review and edit before committing: they check the captured trace without running
// the agent. Re-capturing does not overwrite this file.
import { attestExpect, loadFixture, type ExpectChain } from "@attest-ai/core";
import { evaluate } from "@attest-ai/vitest";
import { describe, it } from "vitest";

const FIXTURE = loadFixture(new URL("./fixtures/claude-agent-sdk-ts.attest.json", import.meta.url));

function contracts(): ExpectChain {
  return attestExpect(FIXTURE.trace)
    // tools-called: calls lookup_order
    .trajectory(["lookup_order"], { mode: "superset" });
}

describe("claude-agent-sdk-ts", () => {
  it("keeps its drafted contracts", async () => {
    await evaluate(contracts());
  });
});
