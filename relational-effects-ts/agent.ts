/** Real HTTP side effects against the local world; no model or provider key. */
import { Agent, type TraceBuilder } from "@attest-ai/core";

async function request(path: string, body?: Record<string, unknown>) {
  const response = await fetch(process.env.PAYMENTS_BASE_URL + path, {
    method: body === undefined ? "GET" : "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) throw new Error(`payments ${path}: ${response.status}`);
  return await response.json() as Record<string, unknown>;
}

export const refundOrder = new Agent("relational-refunds", async (
  builder: TraceBuilder, args: Record<string, unknown>,
) => {
  const orderId = args.order_id as string;
  const order = await request(`/orders/${orderId}`);
  builder.addToolCall("lookup_order", { args: { order_id: orderId }, result: order });
  // Each payment alone is within the amount; only their sum proves the cap.
  for (const amount of [1200, (order.amount_cents as number) - 1200]) {
    const body = { order_id: orderId, amount_cents: amount };
    const result = await request("/refunds", body);
    builder.addToolCall("issue_refund", { args: body, result });
  }
  const body = { order_id: orderId, customer_id: order.customer_id };
  const result = await request("/notifications", body);
  builder.addToolCall("notify_customer", { args: body, result });
  return { message: `Refunded ${orderId} and notified its customer.` };
});
