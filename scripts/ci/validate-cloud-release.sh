#!/usr/bin/env bash

set -euo pipefail

TAG="${GITHUB_REF_NAME:-}"

if [[ -z "$TAG" ]]; then
  echo "::error::GITHUB_REF_NAME is required"
  exit 1
fi

if [[ ! "$TAG" =~ ^cloud-v([0-9]+)\.([0-9]+)\.([0-9]+)(-(dev|test|beta|rc)\.([1-9][0-9]*))?$ ]]; then
  echo "::error::Invalid cloud release tag: $TAG"
  echo "::error::Expected cloud-vX.Y.Z, cloud-vX.Y.Z-dev.N, cloud-vX.Y.Z-test.N, cloud-vX.Y.Z-beta.N, or cloud-vX.Y.Z-rc.N"
  exit 1
fi

BASE_VERSION="${BASH_REMATCH[1]}.${BASH_REMATCH[2]}.${BASH_REMATCH[3]}"
STAGE="${BASH_REMATCH[5]:-}"
RELEASE_VERSION="${TAG#cloud-}"

case "$STAGE" in
  "")
    EXPECTED_BRANCH="main"
    PRERELEASE="false"
    TARGET_ENV="production"
    ;;
  dev)
    EXPECTED_BRANCH="develop"
    PRERELEASE="true"
    TARGET_ENV="dev"
    ;;
  test)
    EXPECTED_BRANCH="test"
    PRERELEASE="true"
    TARGET_ENV="test"
    ;;
  beta|rc)
    EXPECTED_BRANCH="staging"
    PRERELEASE="true"
    TARGET_ENV="staging"
    ;;
  *)
    echo "::error::Unsupported cloud release stage: $STAGE"
    exit 1
    ;;
esac

PROJECT_VERSION="$(
  python3 - <<'PY'
import tomllib

with open("service/pyproject.toml", "rb") as pyproject:
    data = tomllib.load(pyproject)

print(data["project"]["version"])
PY
)"

echo "Tag: $TAG"
echo "Release version: $RELEASE_VERSION"
echo "Project version: $PROJECT_VERSION"
echo "Expected branch: $EXPECTED_BRANCH"

if [[ "$BASE_VERSION" != "$PROJECT_VERSION" ]]; then
  echo "::error::Version mismatch: tag base version ($BASE_VERSION) does not match service/pyproject.toml project.version ($PROJECT_VERSION)"
  exit 1
fi

git fetch --force --prune --no-tags origin "+refs/heads/${EXPECTED_BRANCH}:refs/remotes/origin/${EXPECTED_BRANCH}"
TAG_COMMIT="$(git rev-list -n 1 "$TAG")"

if ! git merge-base --is-ancestor "$TAG_COMMIT" "origin/${EXPECTED_BRANCH}"; then
  echo "::error::Tag $TAG commit $TAG_COMMIT is not in origin/${EXPECTED_BRANCH}"
  exit 1
fi

OWNER="$(printf '%s' "$GITHUB_REPOSITORY_OWNER" | tr '[:upper:]' '[:lower:]')"
IMAGE_NAME="ghcr.io/${OWNER}/metatrader5-service"

{
  echo "tag=$TAG"
  echo "tag_commit=$TAG_COMMIT"
  echo "release_version=$RELEASE_VERSION"
  echo "prerelease=$PRERELEASE"
  echo "target_env=$TARGET_ENV"
  echo "image_name=$IMAGE_NAME"
  echo "image_tag=$RELEASE_VERSION"
} >> "$GITHUB_OUTPUT"
