#!/usr/bin/env bash

set -euo pipefail

IMAGE_NAME="${1:-}"
IMAGE_TAG="${2:-}"
TAG_COMMIT="${3:-}"

if [[ -z "$IMAGE_NAME" || -z "$IMAGE_TAG" || -z "$TAG_COMMIT" ]]; then
  echo "::error::Usage: bash scripts/ci/build-and-push-cloud-image.sh <image_name> <image_tag> <tag_commit>"
  exit 1
fi

if [[ -z "${GITHUB_TOKEN:-}" || -z "${GITHUB_ACTOR:-}" || -z "${GITHUB_REPOSITORY:-}" ]]; then
  echo "::error::GITHUB_TOKEN, GITHUB_ACTOR, and GITHUB_REPOSITORY are required"
  exit 1
fi

IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"
BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_ACTOR" --password-stdin

if docker buildx imagetools inspect "$IMAGE" >/dev/null 2>&1; then
  echo "::error::GHCR image tag already exists: $IMAGE"
  exit 1
fi

docker build \
  --platform linux/amd64 \
  --build-arg VERSION="$IMAGE_TAG" \
  --build-arg BUILD_DATE="$BUILD_DATE" \
  --label "org.opencontainers.image.revision=$TAG_COMMIT" \
  --label "org.opencontainers.image.source=https://github.com/${GITHUB_REPOSITORY}" \
  -t "$IMAGE" \
  .

docker push "$IMAGE"
