#!/usr/bin/env bash

set -euo pipefail

BRANCH_NAME="bump-hwloc-$(date +%Y%m%d)"

echo "Fetching latest hwloc commit from open-mpi/hwloc master..."
LATEST_COMMIT=$(gh api repos/open-mpi/hwloc/branches/master --jq '.commit.sha')

CURRENT_COMMIT=$(cat dev/hwloc_version)
if [[ "${LATEST_COMMIT}" == "${CURRENT_COMMIT}" ]]; then
    echo "Already up to date: ${CURRENT_COMMIT}"
    if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
        {
            echo "changed=false"
            echo "current_commit=${CURRENT_COMMIT}"
            echo "latest_commit=${LATEST_COMMIT}"
        } >> "${GITHUB_OUTPUT}"
    fi
    exit 0
fi

echo "Current: ${CURRENT_COMMIT}"
echo "Latest:  ${LATEST_COMMIT}"

if [[ -z "${GITHUB_OUTPUT:-}" ]]; then
    git checkout -b "${BRANCH_NAME}"
fi

printf '%s' "${LATEST_COMMIT}" > dev/hwloc_version

if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
    {
        echo "changed=true"
        echo "current_commit=${CURRENT_COMMIT}"
        echo "latest_commit=${LATEST_COMMIT}"
    } >> "${GITHUB_OUTPUT}"
fi

if [[ -z "${GITHUB_OUTPUT:-}" ]]; then
    git add dev/hwloc_version
    git commit -m "Bump hwloc to ${LATEST_COMMIT}"

    echo "Branch '${BRANCH_NAME}' created with updated hwloc_version."
else
    echo "Updated dev/hwloc_version; commit skipped."
fi
