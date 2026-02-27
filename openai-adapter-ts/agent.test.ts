/**
 * Tests for the OpenAI adapter example.
 *
 * Demonstrates:
 * - Basic chat completion trace assertions
 * - Tool calling trace assertions
 * - Token and cost tracking
 */
import { attestExpect } from "@attest-ai/core";
import { evaluate } from "@attest-ai/vitest";
import { describe, it, expect } from "vitest";
import { chatAgent, toolCallingAgent } from "./agent";

describe("openai chat agent", () => {
  it("answers questions with cost tracking", async () => {
    const result = chatAgent({ question: "What is the capital of France?" });

    const chain = attestExpect(result)
      .outputContains("Paris")
      .outputNotContains("error")
      .costUnder(0.01)
      .tokensUnder(100)
      .latencyUnder(2000);

    const evaluated = await evaluate(chain);
    expect(evaluated.passed).toBe(true);
  });
});

describe("openai tool calling agent", () => {
  it("calls tools and returns results", async () => {
    const result = toolCallingAgent({
      query: "What is the weather in Paris?",
    });

    const chain = attestExpect(result)
      .outputContains("Paris")
      .outputContains("sunny")
      .requiredTools(["get_weather"])
      .forbiddenTools(["delete_data"])
      .toolsCalledInOrder(["get_weather"])
      .costUnder(0.01)
      .tokensUnder(200);

    const evaluated = await evaluate(chain);
    expect(evaluated.passed).toBe(true);
  });
});
