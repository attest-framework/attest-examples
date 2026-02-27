/**
 * Tests for the customer support agent.
 *
 * Demonstrates Attest assertions across layers 1-4:
 * - Layer 1: Schema validation
 * - Layer 2: Cost and performance constraints
 * - Layer 3: Trace structure (tool ordering)
 * - Layer 4: Content validation
 */
import { attestExpect } from "@attest-ai/core";
import { evaluate } from "@attest-ai/vitest";
import { describe, it, expect } from "vitest";
import { customerSupport } from "./agent";

describe("customer support agent", () => {
  it("processes refunds correctly", async () => {
    const result = customerSupport({ order_id: "ORD-12345" });

    const chain = attestExpect(result)
      // Layer 1: Schema validation
      .outputMatchesSchema({
        type: "object",
        properties: {
          refund_id: { type: "string" },
          amount: { type: "number" },
          status: { type: "string" },
        },
        required: ["refund_id", "status"],
      })
      // Layer 2: Cost and performance constraints
      .costUnder(0.01)
      .latencyUnder(5000)
      .tokensUnder(500)
      // Layer 3: Trace structure
      .toolsCalledInOrder(["lookup_order", "process_refund"])
      .requiredTools(["lookup_order", "process_refund"])
      .forbiddenTools(["delete_order", "cancel_refund"])
      // Layer 4: Content validation
      .outputContains("refund")
      .outputContains("processed")
      .outputNotContains("error");

    const evaluated = await evaluate(chain);
    expect(evaluated.passed).toBe(true);
  });
});
