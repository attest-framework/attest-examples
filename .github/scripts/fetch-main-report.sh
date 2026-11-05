#!/usr/bin/env bash
# Usage: fetch-main-report.sh <artifact-pattern> <dest-dir>
#
# Downloads the Attest report artifact(s) of the latest successful push run of ci.yml on
# main into <dest-dir> (one subdirectory per artifact) and writes `found=true|false` to
# $GITHUB_OUTPUT. Needs GH_TOKEN (actions: read) and GH_REPO.
#
# BASELINE_REQUIRED=true turns a missing main report into a failure. It stays "false"
# until a main run has uploaded reports and the policy carries a regression rule.
set -euo pipefail

pattern="${1:?artifact pattern}"
dest="${2:?destination directory}"
: "${GH_TOKEN:?}" "${GH_REPO:?}" "${GITHUB_OUTPUT:?}"
required="${BASELINE_REQUIRED:-false}"

missing() {
  if [ "$required" = "true" ]; then
    echo "::error::no main baseline report ($1); re-run CI on main, then re-run this job"
    exit 1
  fi
  echo "::warning::no main baseline report ($1); the policy runs without a baseline. Re-run CI on main to create one."
  echo "found=false" >> "$GITHUB_OUTPUT"
  exit 0
}

run_id="$(gh run list --workflow ci.yml --branch main --event push --status success \
  --limit 1 --json databaseId --jq '.[0].databaseId // empty')"
[ -n "$run_id" ] || missing "no successful push run of ci.yml on main"

mkdir -p "$dest"
gh run download "$run_id" --pattern "$pattern" --dir "$dest" 2>/dev/null \
  || missing "run ${run_id} has no artifact matching ${pattern}"
[ -n "$(find "$dest" -name attest-report.json -print -quit)" ] \
  || missing "run ${run_id} artifacts hold no attest-report.json"

echo "baseline: main run ${run_id}"
echo "found=true" >> "$GITHUB_OUTPUT"
