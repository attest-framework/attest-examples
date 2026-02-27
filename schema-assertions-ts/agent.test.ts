/**
 * Tests for schema assertions (Layer 1).
 *
 * Demonstrates:
 * - outputMatchesSchema: validate full output structure
 * - outputFieldMatchesSchema: validate a single field
 * - toolArgsMatchSchema: validate tool call arguments
 * - toolResultMatchesSchema: validate tool call results
 */
import { attestExpect } from "@attest-ai/core";
import { evaluate } from "@attest-ai/vitest";
import { describe, it, expect } from "vitest";
import { recommendationAgent } from "./agent";

describe("schema assertions", () => {
  it("validates output schema", async () => {
    const result = recommendationAgent({
      category: "electronics",
      budget: 100,
    });

    const chain = attestExpect(result).outputMatchesSchema({
      type: "object",
      required: ["recommendations"],
      properties: {
        recommendations: {
          type: "array",
          minItems: 1,
          items: {
            type: "object",
            required: ["id", "name", "price"],
            properties: {
              id: { type: "string" },
              name: { type: "string" },
              price: { type: "number", minimum: 0 },
              category: { type: "string" },
              in_stock: { type: "boolean" },
            },
          },
        },
      },
    });

    const evaluated = await evaluate(chain);
    expect(evaluated.passed).toBe(true);
  });

  it("validates individual output fields", async () => {
    const result = recommendationAgent({
      category: "electronics",
      budget: 100,
    });

    const chain = attestExpect(result)
      .outputFieldMatchesSchema("recommendations", {
        type: "array",
        minItems: 1,
        items: {
          type: "object",
          required: ["id", "name", "price"],
        },
      })
      .outputFieldMatchesSchema("message", {
        type: "string",
        minLength: 1,
      });

    const evaluated = await evaluate(chain);
    expect(evaluated.passed).toBe(true);
  });

  it("validates tool call arguments and results", async () => {
    const result = recommendationAgent({
      category: "electronics",
      budget: 100,
    });

    const chain = attestExpect(result)
      .toolArgsMatchSchema("search_products", {
        type: "object",
        required: ["category", "max_price"],
        properties: {
          category: { type: "string" },
          max_price: { type: "number", minimum: 0 },
        },
      })
      .toolResultMatchesSchema("search_products", {
        type: "object",
        required: ["products"],
        properties: {
          products: {
            type: "array",
            items: {
              type: "object",
              required: ["id", "name", "price"],
            },
          },
        },
      });

    const evaluated = await evaluate(chain);
    expect(evaluated.passed).toBe(true);
  });
});
