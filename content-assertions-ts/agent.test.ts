/**
 * Tests for content assertions (Layer 4).
 *
 * Demonstrates:
 * - outputContains / outputNotContains: substring checks
 * - outputMatchesRegex: pattern matching
 * - outputHasAllKeywords / outputHasAnyKeyword: keyword presence
 * - outputForbids: ensure no forbidden terms appear
 */
import { attestExpect } from "@attest-ai/core";
import { evaluate } from "@attest-ai/vitest";
import { describe, it, expect } from "vitest";
import { classifierAgent, summaryAgent } from "./agent";

describe("content assertions - ticket classifier", () => {
  it("contains required classification fields", async () => {
    const result = classifierAgent({
      ticket: "I was charged twice for order ORD-5678",
    });

    const chain = attestExpect(result)
      .outputContains("billing")
      .outputContains("high")
      .outputContains("ORD-5678")
      .outputNotContains("error")
      .outputNotContains("unknown");

    const evaluated = await evaluate(chain);
    expect(evaluated.passed).toBe(true);
  });

  it("matches expected patterns", async () => {
    const result = classifierAgent({
      ticket: "I was charged twice for order ORD-5678",
    });

    const chain = attestExpect(result)
      .outputMatchesRegex("Category:\\s+\\w+")
      .outputMatchesRegex("Priority:\\s+(low|medium|high|critical)")
      .outputMatchesRegex("ORD-\\d+");

    const evaluated = await evaluate(chain);
    expect(evaluated.passed).toBe(true);
  });

  it("has all required keywords", async () => {
    const result = classifierAgent({
      ticket: "I was charged twice for order ORD-5678",
    });

    const chain = attestExpect(result)
      .outputHasAllKeywords(["category", "priority", "billing"])
      .outputHasAnyKeyword(["refund", "escalate", "review"]);

    const evaluated = await evaluate(chain);
    expect(evaluated.passed).toBe(true);
  });

  it("forbids sensitive information", async () => {
    const result = classifierAgent({
      ticket: "I was charged twice for order ORD-5678",
    });

    const chain = attestExpect(result).outputForbids([
      "password",
      "ssn",
      "credit card number",
      "social security",
    ]);

    const evaluated = await evaluate(chain);
    expect(evaluated.passed).toBe(true);
  });
});

describe("content assertions - summarizer", () => {
  it("produces relevant summaries", async () => {
    const result = summaryAgent({
      article: "A long article about AI agent testing frameworks...",
      max_words: 50,
    });

    const chain = attestExpect(result)
      .outputContains("testing")
      .outputContains("agents")
      .outputNotContains("error")
      .outputHasAnyKeyword(["framework", "assertion", "validation"]);

    const evaluated = await evaluate(chain);
    expect(evaluated.passed).toBe(true);
  });
});
