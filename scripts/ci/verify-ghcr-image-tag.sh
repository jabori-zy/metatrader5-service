#!/usr/bin/env bash

set -euo pipefail

IMAGE_NAME="${1:-}"
IMAGE_TAG="${2:-}"

if [[ -z "$IMAGE_NAME" || -z "$IMAGE_TAG" ]]; then
  echo "::error::Usage: bash scripts/ci/verify-ghcr-image-tag.sh <image_name> <image_tag>"
  exit 1
fi

if [[ -z "${GITHUB_TOKEN:-}" || -z "${GITHUB_ACTOR:-}" ]]; then
  echo "::error::GITHUB_TOKEN and GITHUB_ACTOR are required"
  exit 1
fi

IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"
echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_ACTOR" --password-stdin

if docker buildx imagetools inspect "$IMAGE" >/dev/null 2>&1; then
  echo "::error::GHCR image tag already exists: $IMAGE"
  exit 1
fi
