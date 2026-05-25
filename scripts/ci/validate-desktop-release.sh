#!/usr/bin/env bash

set -euo pipefail

TAG="${GITHUB_REF_NAME:-}"

if [[ -z "$TAG" ]]; then
  echo "::error::GITHUB_REF_NAME is required"
  exit 1
fi

if [[ ! "$TAG" =~ ^desktop-v([0-9]+)\.([0-9]+)\.([0-9]+)(-(dev|test|beta|rc)\.([1-9][0-9]*))?$ ]]; then
  echo "::error::Invalid desktop release tag: $TAG"
  echo "::error::Expected desktop-vX.Y.Z, desktop-vX.Y.Z-dev.N, desktop-vX.Y.Z-test.N, desktop-vX.Y.Z-beta.N, or desktop-vX.Y.Z-rc.N"
  exit 1
fi

BASE_VERSION="${BASH_REMATCH[1]}.${BASH_REMATCH[2]}.${BASH_REMATCH[3]}"
STAGE="${BASH_REMATCH[5]:-}"
RELEASE_VERSION="${TAG#desktop-}"

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
    echo "::error::Unsupported desktop release stage: $STAGE"
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

if gh release view "$TAG" --repo "$GITHUB_REPOSITORY" >/dev/null 2>&1; then
  echo "::error::GitHub Release already exists for tag $TAG"
  exit 1
fi

git fetch --force --prune --no-tags origin "+refs/heads/${EXPECTED_BRANCH}:refs/remotes/origin/${EXPECTED_BRANCH}"
TAG_COMMIT="$(git rev-list -n 1 "$TAG")"

if ! git merge-base --is-ancestor "$TAG_COMMIT" "origin/${EXPECTED_BRANCH}"; then
  echo "::error::Tag $TAG commit $TAG_COMMIT is not in origin/${EXPECTED_BRANCH}"
  exit 1
fi

{
  echo "tag=$TAG"
  echo "tag_commit=$TAG_COMMIT"
  echo "release_version=$RELEASE_VERSION"
  echo "prerelease=$PRERELEASE"
  echo "target_env=$TARGET_ENV"
  echo "desktop_windows_asset=metatrader5-service-desktop-${RELEASE_VERSION}-windows-x64.zip"
} >> "$GITHUB_OUTPUT"
