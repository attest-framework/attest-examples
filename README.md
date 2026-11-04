[![Attest Examples](assets/banner.png)](https://github.com/attest-framework/attest-examples)

---

# attest-examples

Showcase examples for [Attest](https://github.com/attest-framework/attest) — the AI agent evaluation framework. Documentation: [attest-framework.github.io](https://attest-framework.github.io/).

This repository holds one small, copyable example per feature or framework, and every example runs on the latest published release: `attest-ai==1.0.0rc5` and `@attest-ai/core` / `@attest-ai/vitest` `1.0.0-rc.5`. For one end-to-end story — incident, reproduction, fix, blocked regression — see [refund-desk](https://github.com/attest-framework/refund-desk).

| Repo | Role | Tracks |
|---|---|---|
| `attest-examples` | One small, copyable example per feature or framework | Latest published release |
| [`refund-desk`](https://github.com/attest-framework/refund-desk) | One end-to-end story: incident → reproduction → fix → blocked regression | attest `main` until 1.0.0, then 1.0.x |

To add Attest to your own project:

```bash
uv add "attest-ai==1.0.0rc5"                                                         # Python
npm install -D "@attest-ai/core@1.0.0-rc.5" "@attest-ai/vitest@1.0.0-rc.5" vitest   # TypeScript
```

---

## Getting Started

Start with [quickstart/](quickstart/) — a minimal end-to-end example that runs a single assertion against a live agent response.

```bash
make setup EXAMPLE=quickstart
make test EXAMPLE=quickstart
```

See [quickstart/README.md](quickstart/README.md) for a step-by-step walkthrough.

---

## Assertion Layers

Each example targets a specific layer of Attest's assertion stack.

| Example                                            | Layer                      | Description                                               |
| -------------------------------------------------- | -------------------------- | --------------------------------------------------------- |
| [semantic-similarity/](semantic-similarity/)       | L5 — Embeddings            | Cosine-similarity checks on response vectors              |
| [rag-chatbot/](rag-chatbot/)                       | L5 + Retrieval             | Embedding assertions combined with retrieval faithfulness |
| [llm-judge/](llm-judge/)                           | L6 — Quality gates         | LLM-as-judge scoring with pass/fail thresholds            |
| [simulation/](simulation/)                         | L7 — Mock tools & personas | Simulated tool calls and synthetic user personas          |
| [multi-agent-workflow/](multi-agent-workflow/)     | L8 — Trace trees           | Assertion over multi-hop agent trace graphs               |
| [customer-service-agent/](customer-service-agent/) | All 8 layers               | Full-stack evaluation across every assertion layer        |

---

## Framework Integrations

| Example                                | Description                                     |
| -------------------------------------- | ----------------------------------------------- |
| [langchain-agent/](langchain-agent/)   | Wrap a LangChain agent with Attest assertions   |
| [llamaindex-agent/](llamaindex-agent/) | Evaluate a LlamaIndex query pipeline            |
| [google-adk/](google-adk/)             | Assert over Google Agent Development Kit agents |
| [crewai-adapter/](crewai-adapter/)     | Plug Attest into a CrewAI multi-agent crew      |

---

## Production Patterns

| Example                              | Description                                   |
| ------------------------------------ | --------------------------------------------- |
| [continuous-eval/](continuous-eval/) | Run assertions in CI on every deployment      |
| [drift-detection/](drift-detection/) | Alert on assertion score regression over time |
| [plugin-system/](plugin-system/)     | Register custom assertion plugins             |

---

## TypeScript Examples

TypeScript ports using `@attest-ai/core` and `@attest-ai/vitest` with vitest.

| Example                                              | Description                                    |
| ---------------------------------------------------- | ---------------------------------------------- |
| [quickstart-ts/](quickstart-ts/)                     | Customer support agent — layers 1-4            |
| [openai-adapter-ts/](openai-adapter-ts/)             | OpenAI chat + tool calling traces              |
| [schema-assertions-ts/](schema-assertions-ts/)       | Layer 1 schema validation (output, fields, tools) |
| [content-assertions-ts/](content-assertions-ts/)     | Layer 4 content checks (keywords, regex, forbids) |

```bash
cd quickstart-ts && pnpm install && pnpm test
```

---

## Running Examples

```bash
# Set up and test a single example
make setup EXAMPLE=llm-judge
make test  EXAMPLE=llm-judge

# Run all examples in sequence
make test-all
```

Requires [uv](https://github.com/astral-sh/uv) for Python and [pnpm](https://pnpm.io) for TypeScript.

No API key is needed. Every example evaluates against the real Attest engine: schema, constraint, trace, content and trace-tree assertions (layers 1–4 and 7) run on every test. Without a provider key, tests that also use embeddings (L5) or an LLM judge (L6) are skipped as `not evaluated: provider_not_configured`, and the framework examples that call a live model (`langchain-agent`, `llamaindex-agent`, `google-adk`) are skipped with the key they need. Export the keys listed in [`.env.example`](.env.example) to run them.

## CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs each example on the pinned release, writes an Attest report, evaluates [`attest.policy.yaml`](attest.policy.yaml) (any hard failure blocks; not-evaluated assertions warn) and annotates the pull request with each failed assertion at its test's line. An advisory `edge` job runs the same examples against attest `main`.

---

## Related

- [attest](https://github.com/attest-framework/attest) — SDK and core framework
- [attest-bench](https://github.com/attest-framework/attest-bench) — Benchmarks (private, for contributors)
- [attest-ai on PyPI](https://pypi.org/project/attest-ai/)

---

## License

[Apache-2.0](LICENSE)
