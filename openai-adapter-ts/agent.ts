/**
 * OpenAI adapter example — demonstrates tracing OpenAI chat completions.
 *
 * Uses TraceBuilder to manually construct a trace matching what the OpenAI
 * adapter would capture from a real API call. In production, use the
 * OpenAIAdapter class to capture traces automatically.
 */
import { agent, type TraceBuilder } from "@attest-ai/core";

export const chatAgent = agent(
  "openai-chat",
  (builder: TraceBuilder, args: Record<string, unknown>) => {
    const question = args.question as string;

    // Simulate an OpenAI chat completion call
    builder.addLlmCall("gpt-4.1", {
      args: {
        model: "gpt-4.1",
        messages: [
          { role: "system", content: "You are a helpful assistant." },
          { role: "user", content: question },
        ],
        temperature: 0.7,
      },
      result: {
        id: "chatcmpl-abc123",
        model: "gpt-4.1",
        choices: [
          {
            message: {
              role: "assistant",
              content:
                "The capital of France is Paris. It has been the capital since the late 10th century.",
            },
          },
        ],
        usage: {
          prompt_tokens: 24,
          completion_tokens: 22,
          total_tokens: 46,
        },
      },
    });

    builder.setMetadata({
      total_tokens: 46,
      cost_usd: 0.0014,
      latency_ms: 820,
      model: "gpt-4.1",
    });

    return {
      message:
        "The capital of France is Paris. It has been the capital since the late 10th century.",
    };
  },
);

export const toolCallingAgent = agent(
  "openai-tool-caller",
  (builder: TraceBuilder, args: Record<string, unknown>) => {
    const query = args.query as string;

    // Simulate LLM deciding to call a tool
    builder.addLlmCall("gpt-4.1", {
      args: {
        model: "gpt-4.1",
        messages: [{ role: "user", content: query }],
        tools: [
          {
            type: "function",
            function: {
              name: "get_weather",
              parameters: {
                type: "object",
                properties: { city: { type: "string" } },
                required: ["city"],
              },
            },
          },
        ],
      },
      result: {
        choices: [
          {
            message: {
              tool_calls: [
                {
                  function: {
                    name: "get_weather",
                    arguments: { city: "Paris" },
                  },
                },
              ],
            },
          },
        ],
      },
    });

    // Tool execution
    builder.addToolCall("get_weather", {
      args: { city: "Paris" },
      result: { temp_f: 72, condition: "sunny" },
    });

    // Final LLM call with tool result
    builder.addLlmCall("gpt-4.1", {
      args: {
        messages: [
          { role: "user", content: query },
          { role: "tool", content: '{"temp_f": 72, "condition": "sunny"}' },
        ],
      },
      result: {
        choices: [
          {
            message: {
              content: "The weather in Paris is 72F and sunny.",
            },
          },
        ],
        usage: { prompt_tokens: 80, completion_tokens: 15, total_tokens: 95 },
      },
    });

    builder.setMetadata({
      total_tokens: 141,
      cost_usd: 0.004,
      latency_ms: 1500,
      model: "gpt-4.1",
    });

    return {
      message: "The weather in Paris is 72F and sunny.",
    };
  },
);
