/**
 * Simple customer support agent for Attest quickstart example.
 *
 * TypeScript port of the Python quickstart — same agent, same trace structure.
 */
import { agent, type TraceBuilder } from "@attest-ai/core";

export const customerSupport = agent(
  "customer-support",
  (builder: TraceBuilder, args: Record<string, unknown>) => {
    const orderId = args.order_id as string;

    // Simulate LLM call to understand the customer's request
    builder.addLlmCall("gpt-4", {
      args: {
        messages: [
          {
            role: "user",
            content: `Customer wants to return order ${orderId}. Process the refund.`,
          },
        ],
      },
      result: { response: "I will process the refund for this order." },
    });

    // First tool: look up the order details
    builder.addToolCall("lookup_order", {
      args: { order_id: orderId },
      result: {
        order_id: orderId,
        status: "delivered",
        amount: 89.99,
        customer: "John Doe",
      },
    });

    // Second tool: process the refund
    builder.addToolCall("process_refund", {
      args: { order_id: orderId, amount: 89.99 },
      result: { refund_id: "RFD-001", status: "processed" },
    });

    // Set metadata
    builder.setMetadata({
      total_tokens: 150,
      cost_usd: 0.005,
      latency_ms: 1200,
      model: "gpt-4",
    });

    return {
      message: `Your refund of $89.99 has been processed successfully. Refund ID: RFD-001. The funds will appear in your account within 3-5 business days.`,
      structured: {
        refund_id: "RFD-001",
        amount: 89.99,
        status: "processed",
      },
    };
  },
);
