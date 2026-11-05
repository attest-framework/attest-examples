#!/usr/bin/env bash
# Usage: fetch-main-report.sh <artifact-pattern> <dest-dir>
#
# Downloads the Attest report artifact(s) of the latest successful push run of ci.yml on
# main into <dest-dir> (one subdirectory per artifact) and writes `found=true|false` to
# $GITHUB_OUTPUT. Needs GH_TOKEN (actions: read, contents: read) and GH_REPO.
#
# BASELINE_REQUIRED=true turns a missing main report into a failure. A pull request that
# adds or renames an example cannot have a main report for it yet: for a
# single artifact `attest-report-<example>` the failure applies only when the main run has no
# attest-report-* artifact at all, or <example> exists on the pull request's base commit
# ($BASE_SHA). Otherwise the script warns "new example" and reports found=false, and the
# caller evaluates without the regression comparison.
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

# True when <dir> exists on the pull request's base commit. A 404 means absent; any other
# API failure is fatal rather than guessed. --silent: a directory's contents are an array.
exists_on_base() {
  local out
  if out="$(gh api --silent "repos/${GH_REPO}/contents/${1}?ref=${BASE_SHA:?BASE_SHA is required}" 2>&1)"; then
    return 0
  fi
  case "$out" in
    *"HTTP 404"*) return 1 ;;
    *) echo "::error::cannot check ${1} on the base commit: ${out}"; exit 1 ;;
  esac
}

run_id="$(gh run list --workflow ci.yml --branch main --event push --status success \
  --limit 1 --json databaseId --jq '.[0].databaseId // empty')"
[ -n "$run_id" ] || missing "no successful push run of ci.yml on main"

names="$(gh api --paginate "repos/${GH_REPO}/actions/runs/${run_id}/artifacts" \
  --jq '.artifacts[] | select(.expired | not) | .name')"
matched=0
while IFS= read -r name; do
  # shellcheck disable=SC2053  # $pattern is a glob on purpose, as for gh run download
  if [[ -n "$name" && "$name" == $pattern ]]; then matched=1; fi
done <<< "$names"

if [ "$matched" = 0 ]; then
  case "$pattern" in
    attest-report-?*)
      example="${pattern#attest-report-}"
      case "$example" in
        *[!A-Za-z0-9_-]*) ;;  # a glob, not one example: fall through to missing
        *)
          if grep -q '^attest-report-' <<< "$names" && ! exists_on_base "$example"; then
            echo "::warning::new example: no baseline on main yet (${example}); evaluating without the regression comparison"
            echo "found=false" >> "$GITHUB_OUTPUT"
            exit 0
          fi
          ;;
      esac
      ;;
  esac
  missing "run ${run_id} has no artifact matching ${pattern}"
fi

# The artifacts exist, so a failed download is a storage or network error (artifact
# storage answers 503 under load), not a missing baseline: retry, then fail with the cause.
mkdir -p "$dest"
for attempt in 1 2 3 4; do
  if err="$(gh run download "$run_id" --pattern "$pattern" --dir "$dest" 2>&1)"; then
    break
  fi
  if [ "$attempt" = 4 ]; then
    echo "::error::downloading ${pattern} from main run ${run_id} failed 4 times; re-run this job: ${err}"
    exit 1
  fi
  echo "::warning::downloading ${pattern} from main run ${run_id} failed (attempt ${attempt}); retrying: ${err}"
  rm -rf "$dest" && mkdir -p "$dest"
  sleep $((attempt * 15))
done
[ -n "$(find "$dest" -name attest-report.json -print -quit)" ] \
  || missing "run ${run_id} artifacts hold no attest-report.json"

echo "baseline: main run ${run_id}"
echo "found=true" >> "$GITHUB_OUTPUT"
