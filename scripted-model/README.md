# scripted-model

A stdlib Python model server for capturing the framework examples without a provider key. It serves OpenAI Chat Completions (`/v1/chat/completions`), OpenAI Responses (`/v1/responses`) and Anthropic Messages (`/v1/messages`), streaming or not. Each request gets the same script: when the request declares tools and carries no tool result yet, the server calls the first declared tool with `"O-1"` for every required string argument; otherwise it answers `Order O-1 has shipped.`.

It is used only to (re)capture fixtures. Tests replay the committed fixtures and never start it. The directory has no `pyproject.toml`, so `make test-all` skips it.

```bash
python3 scripted-model/server.py --port 8791 &
```

Point `attest capture` at it by setting `OPENAI_BASE_URL` (or `ANTHROPIC_BASE_URL`) to the server before the command; the recording proxy forwards each model call to that upstream. See each example's README for the full command.

Each request is logged to stderr as `scripted-model: <api> stream=<bool> tools=<n> -> <tool_call|text>`. `GET /_admin/stats` returns the request count.
