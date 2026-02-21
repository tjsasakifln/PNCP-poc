#!/usr/bin/env bash
# create-release.sh — Create a git release tag and push to origin.
#
# Usage:
#   bash scripts/create-release.sh v0.5.1
#   bash scripts/create-release.sh v1.0.0 "Optional release message"
#
# Behavior:
#   - Creates an annotated git tag with the given version
#   - Pushes the tag to origin
#   - Idempotent: gracefully exits if tag already exists (exit 0)
#
# GTM-GO-003 AC3

set -euo pipefail

VERSION="${1:-}"

if [ -z "$VERSION" ]; then
  echo "Usage: bash scripts/create-release.sh <version> [message]"
  echo "Example: bash scripts/create-release.sh v0.5.1"
  exit 1
fi

# Validate version format (vX.Y.Z)
if ! echo "$VERSION" | grep -qE '^v[0-9]+\.[0-9]+\.[0-9]+$'; then
  echo "Error: Version must match format vX.Y.Z (e.g., v0.5.1)"
  exit 1
fi

# Check if tag already exists
if git rev-parse "$VERSION" >/dev/null 2>&1; then
  echo "Tag $VERSION already exists — skipping."
  exit 0
fi

MESSAGE="${2:-Release $VERSION}"

echo "Creating tag $VERSION..."
git tag -a "$VERSION" -m "$MESSAGE"

echo "Pushing tag $VERSION to origin..."
git push origin "$VERSION"

echo "Release $VERSION created and pushed successfully."
echo "Verify at: https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/releases/tag/$VERSION"
