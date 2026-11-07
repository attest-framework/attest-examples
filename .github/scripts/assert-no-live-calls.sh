#!/usr/bin/env bash
# Usage: assert-no-live-calls.sh <example> <report>
#
# Fails when an example's Attest report shows a live model call.
#   - Strict replay examples (STRICT below) must carry a replay summary with
#     live == 0 and replayed > 0, so a test that silently stopped replaying fails.
#   - The Claude Agent SDK examples have no replay test (Claude Code embeds the
#     working directory, OS and date in its requests): they must show no live
#     calls and every assertion passed.
#   - The remaining examples (LENIENT) only fail on a live call when a replay summary exists.
# Every example in the ci.yml matrices must be listed in exactly one of the three lists
# below; an unlisted example fails, so a new example cannot skip the assertion unnoticed.
set -euo pipefail

example="${1:?example name}"
report="${2:?report path}"

STRICT=" pydantic-ai openai-agents langgraph vercel-ai-ts mastra-ts "
CLAUDE=" claude-agent-sdk claude-agent-sdk-ts "
LENIENT=" quickstart continuous-eval crewai-adapter customer-service-agent drift-detection google-adk langchain-agent llamaindex-agent llm-judge multi-agent-workflow plugin-system rag-chatbot relational-effects semantic-similarity simulation quickstart-ts schema-assertions-ts content-assertions-ts openai-adapter-ts relational-effects-ts "

fail() {
  echo "::error::${example}: $1"
  exit 1
}

[ -f "$report" ] || fail "no Attest report at ${report}"

if [[ "$STRICT$CLAUDE$LENIENT" != *" $example "* ]]; then
  fail "not classified in assert-no-live-calls.sh"
fi

if [[ "$STRICT" == *" $example "* ]]; then
  jq -e '.summary.replay != null and .summary.replay.live == 0 and .summary.replay.replayed > 0' "$report" >/dev/null \
    || fail "expected a replay summary with 0 live model calls and at least one replayed call, got: $(jq -c '.summary.replay' "$report")"
else
  jq -e '(.summary.replay // null) == null or .summary.replay.live == 0' "$report" >/dev/null \
    || fail "live model calls in CI: $(jq -c '.summary.replay' "$report")"
  if [[ "$CLAUDE" == *" $example "* ]]; then
    jq -e '.summary.total > 0 and .summary.passed == .summary.total' "$report" >/dev/null \
      || fail "not every assertion passed: $(jq -c '.summary | {total, passed, soft_fail, hard_fail, not_evaluated}' "$report")"
  fi
fi

echo "${example}: 0 live model calls ($(jq -c '.summary.replay // "no replay summary"' "$report"))"
