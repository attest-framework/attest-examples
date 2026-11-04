"""Scripted model server for capturing the framework examples (stdlib only, no keys, no network).

Used only to (re)capture fixtures; tests replay the committed fixtures and never start it.

Serves OpenAI Chat Completions (/v1/chat/completions), OpenAI Responses (/v1/responses) and
Anthropic Messages (/v1/messages), streaming and non-streaming, with one generic script:

- request declares tools and carries no tool result yet -> call the first declared tool, filling
  every required string property with "O-1" (other required types get a neutral value);
- otherwise -> final text "Order O-1 has shipped."

Requests are logged to stderr as `scripted-model: <api> stream=<bool> tools=<n> -> <tool_call|text>`.
GET /_admin/stats returns {"requests": N}. Usage: python server.py [--port 8765]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

FINAL = "Order O-1 has shipped."
STATS = {"requests": 0}


def neutral(schema: dict[str, Any]) -> Any:
    kind = schema.get("type")
    if isinstance(kind, list):
        kind = next((k for k in kind if k != "null"), "string")
    if "enum" in schema and schema["enum"]:
        return schema["enum"][0]
    return {"integer": 1, "number": 1, "boolean": True, "array": [], "object": {}}.get(
        kind or "string", "O-1"
    )


def arguments_for(schema: dict[str, Any] | None) -> dict[str, Any]:
    schema = schema or {}
    props = schema.get("properties") or {}
    required = schema.get("required") or list(props)
    return {name: neutral(props.get(name, {})) for name in required}


def tools_of(api: str, body: dict[str, Any]) -> list[tuple[str, dict[str, Any] | None]]:
    out = []
    for t in body.get("tools") or []:
        if api == "chat" and t.get("type") == "function":
            fn = t.get("function") or {}
            out.append((fn.get("name"), fn.get("parameters")))
        elif api == "responses" and t.get("type") == "function":
            out.append((t.get("name"), t.get("parameters")))
        elif api == "messages" and t.get("name"):
            out.append((t["name"], t.get("input_schema")))
    return [(n, s) for n, s in out if n]


def has_tool_result(api: str, body: dict[str, Any]) -> bool:
    if api == "chat":
        return any(m.get("role") == "tool" for m in body.get("messages") or [])
    if api == "responses":
        items = body.get("input")
        return isinstance(items, list) and any(
            isinstance(i, dict) and i.get("type") == "function_call_output" for i in items
        )
    for m in body.get("messages") or []:
        content = m.get("content")
        if isinstance(content, list) and any(
            isinstance(c, dict) and c.get("type") == "tool_result" for c in content
        ):
            return True
    return False


def decide(api: str, body: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    tools = tools_of(api, body)
    if tools and not has_tool_result(api, body):
        name, schema = tools[0]
        return name, arguments_for(schema)
    return None


USAGE_IN, USAGE_OUT = 12, 7


def chat_body(model: str, call: tuple[str, dict[str, Any]] | None) -> dict[str, Any]:
    if call:
        msg: dict[str, Any] = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": call[0], "arguments": json.dumps(call[1])},
                }
            ],
        }
        finish = "tool_calls"
    else:
        msg, finish = {"role": "assistant", "content": FINAL}, "stop"
    return {
        "id": "chatcmpl-1",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "message": msg, "finish_reason": finish, "logprobs": None}],
        "usage": {
            "prompt_tokens": USAGE_IN,
            "completion_tokens": USAGE_OUT,
            "total_tokens": USAGE_IN + USAGE_OUT,
        },
    }


def chat_stream(model: str, call: tuple[str, dict[str, Any]] | None, usage: bool) -> list[Any]:
    base = {"id": "chatcmpl-1", "object": "chat.completion.chunk", "created": int(time.time()),
            "model": model}
    chunks = [{**base, "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""},
                                   "finish_reason": None}]}]
    if call:
        chunks.append({**base, "choices": [{"index": 0, "delta": {"tool_calls": [{
            "index": 0, "id": "call_1", "type": "function",
            "function": {"name": call[0], "arguments": ""}}]}, "finish_reason": None}]})
        chunks.append({**base, "choices": [{"index": 0, "delta": {"tool_calls": [{
            "index": 0, "function": {"arguments": json.dumps(call[1])}}]},
            "finish_reason": None}]})
        finish = "tool_calls"
    else:
        chunks.append({**base, "choices": [{"index": 0, "delta": {"content": FINAL},
                                           "finish_reason": None}]})
        finish = "stop"
    chunks.append({**base, "choices": [{"index": 0, "delta": {}, "finish_reason": finish}]})
    if usage:
        chunks.append({**base, "choices": [], "usage": {
            "prompt_tokens": USAGE_IN, "completion_tokens": USAGE_OUT,
            "total_tokens": USAGE_IN + USAGE_OUT}})
    return [("", c) for c in chunks] + [("", "[DONE]")]


def responses_item(call: tuple[str, dict[str, Any]] | None) -> dict[str, Any]:
    if call:
        return {"type": "function_call", "id": "fc_1", "call_id": "call_1", "name": call[0],
                "arguments": json.dumps(call[1]), "status": "completed"}
    return {"type": "message", "id": "msg_1", "role": "assistant", "status": "completed",
            "content": [{"type": "output_text", "text": FINAL, "annotations": [],
                         "logprobs": []}]}


def responses_body(model: str, call: tuple[str, dict[str, Any]] | None,
                   status: str = "completed") -> dict[str, Any]:
    return {
        "id": "resp_1", "object": "response", "created_at": int(time.time()), "status": status,
        "model": model, "output": [responses_item(call)] if status == "completed" else [],
        "parallel_tool_calls": True, "tool_choice": "auto", "tools": [], "error": None,
        "incomplete_details": None, "instructions": None, "metadata": {}, "temperature": 1.0,
        "top_p": 1.0, "text": {"format": {"type": "text"}}, "truncation": "disabled",
        "usage": {"input_tokens": USAGE_IN, "output_tokens": USAGE_OUT,
                  "total_tokens": USAGE_IN + USAGE_OUT,
                  "input_tokens_details": {"cached_tokens": 0},
                  "output_tokens_details": {"reasoning_tokens": 0}},
    }


def responses_stream(model: str, call: tuple[str, dict[str, Any]] | None) -> list[Any]:
    item = responses_item(call)
    seq = iter(range(1000))
    ev: list[Any] = []

    def add(kind: str, **kw: Any) -> None:
        ev.append((kind, {"type": kind, "sequence_number": next(seq), **kw}))

    add("response.created", response=responses_body(model, call, "in_progress"))
    add("response.in_progress", response=responses_body(model, call, "in_progress"))
    if call:
        add("response.output_item.added", output_index=0, item={**item, "arguments": "",
                                                                  "status": "in_progress"})
        add("response.function_call_arguments.delta", output_index=0, item_id="fc_1",
            delta=item["arguments"])
        add("response.function_call_arguments.done", output_index=0, item_id="fc_1",
            arguments=item["arguments"])
    else:
        add("response.output_item.added", output_index=0,
            item={**item, "content": [], "status": "in_progress"})
        add("response.content_part.added", output_index=0, item_id="msg_1", content_index=0,
            part={"type": "output_text", "text": "", "annotations": []})
        add("response.output_text.delta", output_index=0, item_id="msg_1", content_index=0,
            delta=FINAL, logprobs=[])
        add("response.output_text.done", output_index=0, item_id="msg_1", content_index=0,
            text=FINAL, logprobs=[])
        add("response.content_part.done", output_index=0, item_id="msg_1", content_index=0,
            part=item["content"][0])
    add("response.output_item.done", output_index=0, item=item)
    add("response.completed", response=responses_body(model, call))
    return ev


def messages_body(model: str, call: tuple[str, dict[str, Any]] | None) -> dict[str, Any]:
    if call:
        content = [{"type": "tool_use", "id": "toolu_1", "name": call[0], "input": call[1]}]
        stop = "tool_use"
    else:
        content, stop = [{"type": "text", "text": FINAL}], "end_turn"
    return {"id": "msg_1", "type": "message", "role": "assistant", "model": model,
            "content": content, "stop_reason": stop, "stop_sequence": None,
            "usage": {"input_tokens": USAGE_IN, "output_tokens": USAGE_OUT,
                      "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}}


def messages_stream(model: str, call: tuple[str, dict[str, Any]] | None) -> list[Any]:
    full = messages_body(model, call)
    start = {**full, "content": [], "stop_reason": None,
             "usage": {**full["usage"], "output_tokens": 1}}
    ev: list[Any] = [("message_start", {"type": "message_start", "message": start})]
    if call:
        ev.append(("content_block_start", {"type": "content_block_start", "index": 0,
                   "content_block": {"type": "tool_use", "id": "toolu_1", "name": call[0],
                                     "input": {}}}))
        ev.append(("content_block_delta", {"type": "content_block_delta", "index": 0,
                   "delta": {"type": "input_json_delta", "partial_json": json.dumps(call[1])}}))
    else:
        ev.append(("content_block_start", {"type": "content_block_start", "index": 0,
                   "content_block": {"type": "text", "text": ""}}))
        ev.append(("content_block_delta", {"type": "content_block_delta", "index": 0,
                   "delta": {"type": "text_delta", "text": FINAL}}))
    ev.append(("content_block_stop", {"type": "content_block_stop", "index": 0}))
    ev.append(("message_delta", {"type": "message_delta",
               "delta": {"stop_reason": full["stop_reason"], "stop_sequence": None},
               "usage": {"output_tokens": USAGE_OUT}}))
    ev.append(("message_stop", {"type": "message_stop"}))
    return ev


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: Any) -> None:
        pass

    def send_json(self, status: int, body: Any) -> None:
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_sse(self, events: list[Any]) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()
        for name, data in events:
            payload = data if isinstance(data, str) else json.dumps(data)
            block = (f"event: {name}\n" if name else "") + f"data: {payload}\n\n"
            self.wfile.write(block.encode())
            self.wfile.flush()
        self.close_connection = True

    def do_GET(self) -> None:
        path = self.path.split("?")[0]
        if path == "/_admin/stats":
            self.send_json(200, STATS)
        elif path.endswith("/models"):
            self.send_json(200, {"object": "list", "data": [{"id": "fake-model",
                                                             "object": "model"}]})
        else:
            self.send_json(404, {"error": {"message": f"no route GET {path}"}})

    def do_POST(self) -> None:
        path = self.path.split("?")[0]
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            self.send_json(400, {"error": {"message": "invalid json"}})
            return
        if path.endswith("/chat/completions"):
            api = "chat"
        elif path.endswith("/responses"):
            api = "responses"
        elif path.endswith("/messages"):
            api = "messages"
        else:
            self.send_json(404, {"error": {"message": f"no route POST {path}"}})
            return
        STATS["requests"] += 1
        model = str(body.get("model") or "fake-model")
        stream = bool(body.get("stream"))
        call = decide(api, body)
        sys.stderr.write(
            f"scripted-model: {api} stream={stream} tools={len(tools_of(api, body))} -> "
            f"{'tool_call ' + call[0] if call else 'text'}\n"
        )
        sys.stderr.flush()
        if api == "chat":
            if stream:
                usage = bool((body.get("stream_options") or {}).get("include_usage"))
                self.send_sse(chat_stream(model, call, usage))
            else:
                self.send_json(200, chat_body(model, call))
        elif api == "responses":
            if stream:
                self.send_sse(responses_stream(model, call))
            else:
                self.send_json(200, responses_body(model, call))
        else:
            if stream:
                self.send_sse(messages_stream(model, call))
            else:
                self.send_json(200, messages_body(model, call))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    sys.stderr.write(f"scripted-model: listening on http://{args.host}:{args.port}\n")
    sys.stderr.flush()
    server.serve_forever()


if __name__ == "__main__":
    main()
