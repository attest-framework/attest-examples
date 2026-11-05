#!/usr/bin/env bash
# Usage: evaluate-policy.sh <attest command...>   e.g. evaluate-policy.sh uv run attest
#
# Run from an example directory. Evaluates attest-report.json against the merge policy and
# maps exit 2 (warnings only) to success. Inputs (env):
#   BASELINE_FOUND   "true" when fetch-main-report.sh downloaded a main report
#   MAIN_REPORT_DIR  where it downloaded the report
#   POLICY           policy file (default ../attest.policy.yaml)
#
# With a usable main report the baseline is pinned as tag `main` and the policy runs with
# --baseline main, so a regression rule applies. Without one (new example, or a main report
# with no assertion results, which `attest baseline pin` rejects) there is nothing to compare:
# the same policy runs minus its top-level `block_on_regression` and `regression` rules, since
# attest exits 3 when either rule runs without --baseline. fetch-main-report.sh has already
# failed the job when a baseline is required and missing.
set -uo pipefail

[ "$#" -gt 0 ] || { echo "usage: evaluate-policy.sh <attest command...>" >&2; exit 2; }
policy="${POLICY:-../attest.policy.yaml}"
args=(--report attest-report.json)
baseline=""

if [ "${BASELINE_FOUND:-false}" = "true" ]; then
  main_report="$(find "${MAIN_REPORT_DIR:?}" -name attest-report.json -print -quit)"
  if jq -e '.results | length > 0' "$main_report" >/dev/null; then
    "$@" baseline pin --tag main --report "$main_report" || exit 1
    baseline="main"
  else
    echo "::notice::the main report holds no assertion results; skipping the regression comparison"
  fi
fi

if [ -n "$baseline" ]; then
  args+=(--policy "$policy" --baseline "$baseline")
else
  stripped="$(mktemp -d)/policy.json"
  uv run --no-project --no-config --with pyyaml==6.0.2 python \
    "$(dirname "$0")/strip-regression-rules.py" "$policy" "$stripped" || exit 1
  args+=(--policy "$stripped")
fi

"$@" policy evaluate "${args[@]}"
code=$?
if [ "$code" -eq 2 ]; then
  echo "::warning::attest policy: warnings only (exit 2)"
  exit 0
fi
exit "$code"
