/**
 * Support ticket classifier — demonstrates Layer 4 content assertions.
 *
 * Returns a classification response that must contain specific keywords,
 * match patterns, and avoid forbidden content (PII, profanity).
 */
import { agent, type TraceBuilder } from "@attest-ai/core";

export const classifierAgent = agent(
  "ticket-classifier",
  (builder: TraceBuilder, args: Record<string, unknown>) => {
    const ticket = args.ticket as string;

    builder.addLlmCall("gpt-4.1-mini", {
      args: {
        messages: [
          {
            role: "system",
            content:
              "Classify support tickets. Return category, priority, and a brief summary.",
          },
          { role: "user", content: ticket },
        ],
      },
      result: {
        completion:
          "Category: billing. Priority: high. The customer reports a double charge on order ORD-5678.",
      },
    });

    builder.setMetadata({
      total_tokens: 62,
      cost_usd: 0.001,
      latency_ms: 400,
      model: "gpt-4.1-mini",
    });

    return {
      message:
        "Category: billing. Priority: high. The customer reports a double charge on order ORD-5678. Recommended action: escalate to billing team for immediate refund review.",
      category: "billing",
      priority: "high",
      order_id: "ORD-5678",
    };
  },
);

export const summaryAgent = agent(
  "article-summarizer",
  (builder: TraceBuilder, args: Record<string, unknown>) => {
    const article = args.article as string;
    const maxWords = (args.max_words as number) ?? 50;

    builder.addLlmCall("gpt-4.1", {
      args: {
        messages: [
          {
            role: "user",
            content: `Summarize in under ${maxWords} words: ${article}`,
          },
        ],
      },
      result: {
        completion:
          "Researchers developed a new testing framework for AI agents that validates outputs across eight assertion layers, from schema checks to LLM-as-judge evaluation.",
      },
    });

    builder.setMetadata({
      total_tokens: 95,
      cost_usd: 0.003,
      latency_ms: 700,
      model: "gpt-4.1",
    });

    return {
      message:
        "Researchers developed a new testing framework for AI agents that validates outputs across eight assertion layers, from schema checks to LLM-as-judge evaluation.",
    };
  },
);
