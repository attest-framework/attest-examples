/**
 * Product recommendation agent — demonstrates Layer 1 schema assertions.
 *
 * Returns structured output that must conform to a strict JSON Schema:
 * an array of product recommendations with required fields.
 */
import { agent, type TraceBuilder } from "@attest-ai/core";

export const recommendationAgent = agent(
  "product-recommender",
  (builder: TraceBuilder, args: Record<string, unknown>) => {
    const category = args.category as string;
    const budget = args.budget as number;

    builder.addLlmCall("gpt-4.1", {
      args: {
        messages: [
          {
            role: "user",
            content: `Recommend products in ${category} under $${budget}`,
          },
        ],
      },
      result: {
        completion: "Here are my recommendations based on your criteria.",
      },
    });

    builder.addToolCall("search_products", {
      args: { category, max_price: budget },
      result: {
        products: [
          { id: "P001", name: "Widget Pro", price: 29.99 },
          { id: "P002", name: "Gadget Plus", price: 49.99 },
        ],
      },
    });

    builder.setMetadata({
      total_tokens: 85,
      cost_usd: 0.002,
      latency_ms: 650,
      model: "gpt-4.1",
    });

    return {
      message: "Here are my top recommendations for you.",
      recommendations: [
        {
          id: "P001",
          name: "Widget Pro",
          price: 29.99,
          category: "electronics",
          in_stock: true,
        },
        {
          id: "P002",
          name: "Gadget Plus",
          price: 49.99,
          category: "electronics",
          in_stock: true,
        },
      ],
    };
  },
);
