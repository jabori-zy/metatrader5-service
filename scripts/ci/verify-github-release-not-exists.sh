#!/usr/bin/env bash

set -euo pipefail

TAG="${1:-}"

if [[ -z "$TAG" ]]; then
  echo "::error::Usage: bash scripts/ci/verify-github-release-not-exists.sh <tag>"
  exit 1
fi

if gh release view "$TAG" --repo "$GITHUB_REPOSITORY" >/dev/null 2>&1; then
  echo "::error::GitHub Release already exists for tag $TAG"
  exit 1
fi
