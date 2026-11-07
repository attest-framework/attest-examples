import { fileURLToPath } from "node:url";
import { attestExpect, related } from "@attest-ai/core";
import { evaluate, useWorld } from "@attest-ai/vitest";
import { it } from "vitest";
import { refundOrder } from "./agent";

it.each(["O-2077", "O-2078"])("refunds and notifies the customer of %s", async (orderId) => {
  const world = await useWorld(fileURLToPath(new URL("./payments.world.yaml", import.meta.url)));
  const trace = await refundOrder({ order_id: orderId });
  const snapshot = await world.state();
  await evaluate(attestExpect(trace)
    .world(snapshot)
    .sum("refunds", "amount_cents", { atMost: related("orders", "amount_cents", { on: "order_id" }) })
    .world(snapshot)
    .matches("notifications", "customer_id", related("orders", "customer_id", { on: "order_id" })));
});
