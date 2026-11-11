[![Attest Examples](assets/banner.png)](https://github.com/attest-framework/attest-examples)

# attest-examples

Small, copyable examples for [Attest](https://github.com/attest-framework/attest), a framework for testing what AI agents say, which tools they call, and what they change. Start with a no-key example, then choose the feature or framework you use. Documentation: [attest-framework.github.io](https://attest-framework.github.io/).

All 27 runnable examples pin the stable **1.1.0** release: Python uses `attest-ai==1.1.0`; TypeScript uses `@attest-ai/core` and `@attest-ai/vitest` at `1.1.0`. The `scripted-model/` helper supports capture without a real model. For an incident, reproduction, fix and blocked regression in one application, see [refund-desk](https://github.com/attest-framework/refund-desk).

To add Attest to your own project instead of running this repository:

```bash
# Python
uv add "attest-ai>=1.1.0" pytest

# TypeScript
npm install -D "@attest-ai/core@>=1.1.0" "@attest-ai/vitest@>=1.1.0" "vitest@^4"
```

## Start here

Install [uv](https://docs.astral.sh/uv/) for Python examples, or [pnpm](https://pnpm.io/) and Node.js for TypeScript (CI uses Node.js 22 and pnpm 10). Run the Python commands below from the repository root:

```bash
make setup EXAMPLE=quickstart
make test EXAMPLE=quickstart
```

The [quickstart walkthrough](quickstart/README.md) uses a scripted customer-support agent. It does not call a model or need an API key, and checks output shape, budgets, tool calls and message content.

For TypeScript, enter the example directory first:

```bash
cd quickstart-ts
pnpm install
npx attest doctor
pnpm test
```

Run `npx attest doctor` once before your first TypeScript test: it downloads and checks the matching engine outside Vitest's default 5-second test timeout. Without this warm-up, the first download on a cold machine can time out. It does not call a judge or a model.

**Offline** below means no model-provider requests once dependencies, the engine and any local embedding model are installed. Initial installation and engine download need network access. It does not mean `ATTEST_SIMULATION=1`: deterministic assertions normally run against the real engine.

## Python examples

Each row's commands run from the repository root. `make setup` runs `uv sync` in that example; `make test` runs `uv run pytest -v`. You can run those same `uv` commands directly from the example directory. Most examples require Python 3.10 or later; framework examples may require a newer version, as specified in their `pyproject.toml`.

| Example | What it shows / feature guide | API key or offline behavior | Run |
| --- | --- | --- | --- |
| [quickstart](quickstart/) | Test a scripted refund agent's output, budgets, tools and content; [test and evaluation basics](https://github.com/attest-framework/attest/blob/main/docs/guides/verdicts.md). | Offline; no key. | `make setup EXAMPLE=quickstart && make test EXAMPLE=quickstart` |
| [customer-service-agent](customer-service-agent/) | Test a refund flow that delegates to a specialist, including output and cross-agent budgets; [multi-agent assertions](https://github.com/attest-framework/attest/blob/main/docs/guides/multi-agent.md). | Offline; no key. Covers layers 1–4 and 7, not all eight layers. | `make setup EXAMPLE=customer-service-agent && make test EXAMPLE=customer-service-agent` |
| [semantic-similarity](semantic-similarity/) | Compare translations and summaries by meaning rather than exact text; [embedding configuration](https://github.com/attest-framework/attest/blob/main/docs/guides/configuration.md). | L5 needs an embedding provider: OpenAI needs a key; local ONNX needs its model/runtime. Without a provider, tests skip as not evaluated. | `make setup EXAMPLE=semantic-similarity && make test EXAMPLE=semantic-similarity` |
| [rag-chatbot](rag-chatbot/) | Check a scripted retrieval-and-answer trace, then judge whether its answer is grounded; [judges](https://github.com/attest-framework/attest/blob/main/docs/guides/judges.md) and [embeddings](https://github.com/attest-framework/attest/blob/main/docs/guides/configuration.md). | Basic checks are offline; L5/L6 tests need configured providers or skip as not evaluated. | `make setup EXAMPLE=rag-chatbot && make test EXAMPLE=rag-chatbot` |
| [llm-judge](llm-judge/) | Score complaint responses and moderation decisions against a rubric; [LLM judges](https://github.com/attest-framework/attest/blob/main/docs/guides/judges.md). | Needs a configured judge; no provider means not-evaluated skips. Hosted judges can cost money. | `make setup EXAMPLE=llm-judge && make test EXAMPLE=llm-judge` |
| [simulation](simulation/) | Replace flight-booking tools with controlled responses and inspect built-in user personas; [simulation](https://github.com/attest-framework/attest/blob/main/docs/guides/simulation.md). | Offline; no key. Mock tools/personas are not a numbered assertion layer. | `make setup EXAMPLE=simulation && make test EXAMPLE=simulation` |
| [multi-agent-workflow](multi-agent-workflow/) | Check researcher/writer delegation, trace-tree structure and combined budgets; [multi-agent assertions (L7)](https://github.com/attest-framework/attest/blob/main/docs/guides/multi-agent.md). | Offline; no key. | `make setup EXAMPLE=multi-agent-workflow && make test EXAMPLE=multi-agent-workflow` |
| [relational-effects](relational-effects/) | Sum partial refunds per order and match notification recipients in a local payments service; [world-effect contracts](https://github.com/attest-framework/attest/blob/main/docs/guides/world-fixtures.md#relational-effects-totals-and-recipients). | No key or model; real HTTP to an isolated local world. | `make setup EXAMPLE=relational-effects && make test EXAMPLE=relational-effects` |
| [langchain-agent](langchain-agent/) | Capture a live LangChain agent with callbacks and assert on its trace; [framework adapters](https://github.com/attest-framework/attest/blob/main/docs/guides/framework-adapters.md). | Needs `OPENAI_API_KEY`; otherwise tests skip. Live calls can cost money. | `make setup EXAMPLE=langchain-agent && make test EXAMPLE=langchain-agent` |
| [llamaindex-agent](llamaindex-agent/) | Capture and test a live LlamaIndex query pipeline; [framework adapters](https://github.com/attest-framework/attest/blob/main/docs/guides/framework-adapters.md). | Needs `OPENAI_API_KEY`; otherwise tests skip. Live calls can cost money. | `make setup EXAMPLE=llamaindex-agent && make test EXAMPLE=llamaindex-agent` |
| [google-adk](google-adk/) | Turn Google ADK agent events into a trace and test it; [framework adapters](https://github.com/attest-framework/attest/blob/main/docs/guides/framework-adapters.md). | Needs `GOOGLE_API_KEY` or `GEMINI_API_KEY`; otherwise tests skip. Live calls can cost money. | `make setup EXAMPLE=google-adk && make test EXAMPLE=google-adk` |
| [crewai-adapter](crewai-adapter/) | Test manually built crew traces that illustrate what a CrewAI adapter captures; [framework adapters](https://github.com/attest-framework/attest/blob/main/docs/guides/framework-adapters.md). | Offline; no key or CrewAI installation required for these tests. | `make setup EXAMPLE=crewai-adapter && make test EXAMPLE=crewai-adapter` |
| [pydantic-ai](pydantic-ai/) | Record native OpenTelemetry spans, check the fixture and replay the real Pydantic AI agent; [capture](https://github.com/attest-framework/attest/blob/main/docs/guides/capture.md#frameworks) / [replay](https://github.com/attest-framework/attest/blob/main/docs/guides/replay.md). | Offline fixture + strict replay; no key. | `make setup EXAMPLE=pydantic-ai && make test EXAMPLE=pydantic-ai` |
| [openai-agents](openai-agents/) | Capture OpenAI Agents SDK spans through alpha OTel instrumentation, then replay the agent; [capture](https://github.com/attest-framework/attest/blob/main/docs/guides/capture.md#frameworks) / [replay](https://github.com/attest-framework/attest/blob/main/docs/guides/replay.md). | Offline fixture + strict replay; no key. | `make setup EXAMPLE=openai-agents && make test EXAMPLE=openai-agents` |
| [langgraph](langgraph/) | Capture LangGraph through LangSmith's local OTel mode, then replay the agent; [capture](https://github.com/attest-framework/attest/blob/main/docs/guides/capture.md#frameworks) / [replay](https://github.com/attest-framework/attest/blob/main/docs/guides/replay.md). | Offline fixture + strict replay; no key or hosted LangSmith service. | `make setup EXAMPLE=langgraph && make test EXAMPLE=langgraph` |
| [claude-agent-sdk](claude-agent-sdk/) | Check a Claude Agent SDK capture and its subprocess environment isolation; [capture](https://github.com/attest-framework/attest/blob/main/docs/guides/capture.md#frameworks). | Offline recorded-trace + environment tests; no key. No real-agent replay test; see its README. | `make setup EXAMPLE=claude-agent-sdk && make test EXAMPLE=claude-agent-sdk` |
| [continuous-eval](continuous-eval/) | Queue and evaluate traces in a background runner with sampling; [continuous evaluation](https://github.com/attest-framework/attest/blob/main/docs/guides/continuous-eval.md). | Offline; no key. | `make setup EXAMPLE=continuous-eval && make test EXAMPLE=continuous-eval` |
| [drift-detection](drift-detection/) | Compare baseline and degraded traces against cost, token and latency budgets; [continuous-evaluation drift concepts](https://github.com/attest-framework/attest/blob/main/docs/guides/continuous-eval.md). | Offline; no key. A manual comparison, not an alerting service or persisted CLI baseline. | `make setup EXAMPLE=drift-detection && make test EXAMPLE=drift-detection` |
| [plugin-system](plugin-system/) | Register and directly test custom profanity, response-length and efficiency checks; [plugins (L8)](https://github.com/attest-framework/attest/blob/main/docs/guides/plugins.md). | Offline; no key. | `make setup EXAMPLE=plugin-system && make test EXAMPLE=plugin-system` |

## TypeScript examples

Run each command from the repository root; it enters the example directory. Every package defines `test` (`vitest run`) and `typecheck` (`tsc --noEmit`), so you can also run `pnpm typecheck` there. The commands include the first-run engine warm-up described above.

| Example | What it shows / feature guide | API key or offline behavior | Run |
| --- | --- | --- | --- |
| [quickstart-ts](quickstart-ts/) | Test a scripted refund agent's schema, budgets, tools and content; [test and evaluation basics](https://github.com/attest-framework/attest/blob/main/docs/guides/verdicts.md). | Offline; no key. | `cd quickstart-ts && pnpm install && npx attest doctor && pnpm test` |
| [schema-assertions-ts](schema-assertions-ts/) | Validate output schemas, individual fields and tool arguments/results; [assertion verdicts](https://github.com/attest-framework/attest/blob/main/docs/guides/verdicts.md). | Offline; no key. | `cd schema-assertions-ts && pnpm install && npx attest doctor && pnpm test` |
| [content-assertions-ts](content-assertions-ts/) | Check required keywords, regular expressions and forbidden output text; [assertion verdicts](https://github.com/attest-framework/attest/blob/main/docs/guides/verdicts.md). | Offline; no key. | `cd content-assertions-ts && pnpm install && npx attest doctor && pnpm test` |
| [openai-adapter-ts](openai-adapter-ts/) | Build OpenAI-shaped chat and tool-calling traces by hand, then assert on them; [framework adapters](https://github.com/attest-framework/attest/blob/main/docs/guides/framework-adapters.md). | Offline; no key. These tests do not call the OpenAI adapter or API. | `cd openai-adapter-ts && pnpm install && npx attest doctor && pnpm test` |
| [relational-effects-ts](relational-effects-ts/) | Check refund totals and notification recipients across related rows; [world-effect contracts](https://github.com/attest-framework/attest/blob/main/docs/guides/world-fixtures.md#relational-effects-totals-and-recipients). | No key or model; real HTTP to an isolated local world. | `cd relational-effects-ts && pnpm install && npx attest doctor && pnpm test` |
| [vercel-ai-ts](vercel-ai-ts/) | Capture Vercel AI SDK 7 native OTel spans and replay the real agent; [capture](https://github.com/attest-framework/attest/blob/main/docs/guides/capture.md#frameworks) / [replay](https://github.com/attest-framework/attest/blob/main/docs/guides/replay.md). | Offline fixture + strict replay; no key. | `cd vercel-ai-ts && pnpm install && npx attest doctor && pnpm test` |
| [mastra-ts](mastra-ts/) | Capture Mastra's native OTel spans and replay the real agent; [capture](https://github.com/attest-framework/attest/blob/main/docs/guides/capture.md#frameworks) / [replay](https://github.com/attest-framework/attest/blob/main/docs/guides/replay.md). | Offline fixture + strict replay; no key. | `cd mastra-ts && pnpm install && npx attest doctor && pnpm test` |
| [claude-agent-sdk-ts](claude-agent-sdk-ts/) | Check a Claude Agent SDK capture and its subprocess environment isolation; [capture](https://github.com/attest-framework/attest/blob/main/docs/guides/capture.md#frameworks). | Offline recorded-trace + environment tests; no key. No real-agent replay test; see its README. | `cd claude-agent-sdk-ts && pnpm install && npx attest doctor && pnpm test` |

## Capture helper

| Directory | What it shows / feature guide | API key or offline behavior | Run from the repository root |
| --- | --- | --- | --- |
| [scripted-model](scripted-model/) | Serve fixed OpenAI/Anthropic responses while recording framework fixtures; [capture](https://github.com/attest-framework/attest/blob/main/docs/guides/capture.md). | Local server; no real key or model. Not a test project. | `python3 scripted-model/server.py --port 8791` (stop with Ctrl-C); see framework READMEs for capture commands. |

`assets/` holds the README banner, not an example.

The seven OTel framework examples commit the fixture and contracts drafted by capture. Five also run the real agent in strict replay, with provider egress blocked. The two Claude Agent SDK examples instead test recorded traces and environment isolation: Claude Code includes machine/date-specific request text that strict replay does not normalize. Their READMEs explain the limitation. Re-capture against the local `scripted-model/` helper; running committed tests does not require capture first.

## Providers and simulation

No real provider key is needed for the default CI run. Tests that need a live agent are skipped without the key listed in the table. Missing embedding or judge providers produce `not_evaluated: provider_not_configured`, and pytest skips the affected tests rather than calling them passes. Provider configuration is documented in [judges](https://github.com/attest-framework/attest/blob/main/docs/guides/judges.md) and [engine configuration](https://github.com/attest-framework/attest/blob/main/docs/guides/configuration.md).

If you want deterministic assertion checks only, run a synthetic example in simulation mode:

```bash
ATTEST_SIMULATION=1 make test EXAMPLE=rag-chatbot
```

Simulation evaluates layers 1–4 and 7, but marks L5/L6 as not evaluated. It does not replace a framework's own live model calls, so it does not make the three live-key examples offline. Mock tools and personas in `simulation/` are a separate feature. The assertion layers are schema (L1), constraints (L2), trace (L3), content (L4), embeddings (L5), judge (L6), trace tree (L7), and plugins (L8).

`make test-all` sets up and tests every Python example in sequence; it does not run TypeScript examples or the scripted server. Live-key examples can make paid calls if their keys are configured, so choose a single offline example when that is not intended.

## CI

[Examples CI](.github/workflows/ci.yml) runs on every pull request, including documentation-only changes, and on pushes to `main`. It runs all 19 Python and eight TypeScript projects against their pinned release, asserts zero live model calls, uploads Attest reports and evaluates [`attest.policy.yaml`](attest.policy.yaml). TypeScript jobs warm the engine with `attest doctor` before typechecking and testing.

A separate annotation job holds the only pull-request write permission. It posts a summary and failure annotations without running example code. An advisory `edge` job runs all Python and TypeScript examples against attest `main`.

Pull requests compare against main's reports (`--baseline main`): a previously passing assertion that stops passing, or a removed assertion, blocks the merge. Not-evaluated assertions warn under this repository's policy; a warning is not proof that the check passed. See [merge gates](https://github.com/attest-framework/attest/blob/main/docs/guides/merge-gate.md) and [policies](https://github.com/attest-framework/attest/blob/main/docs/guides/policies.md).

## Related

- [attest](https://github.com/attest-framework/attest) — SDKs, engine and feature guides
- [refund-desk](https://github.com/attest-framework/refund-desk) — End-to-end double-refund regression example
- [attest-ai on PyPI](https://pypi.org/project/attest-ai/)

## License

[Apache-2.0](LICENSE)
