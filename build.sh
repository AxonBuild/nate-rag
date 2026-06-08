#!/usr/bin/env bash
set -euo pipefail

IMAGE="hsn37/nate-rag"
TAG="${1:-latest}"

VITE_CLERK_KEY="${VITE_CLERK_PUBLISHABLE_KEY:-}"
if [ -z "$VITE_CLERK_KEY" ] && [ -f frontend/.env ]; then
  VITE_CLERK_KEY=$(grep '^VITE_CLERK_PUBLISHABLE_KEY=' frontend/.env | cut -d= -f2-)
fi

if [ -z "$VITE_CLERK_KEY" ]; then
  echo "Error: VITE_CLERK_PUBLISHABLE_KEY not set and not found in frontend/.env" >&2
  exit 1
fi

echo "Building ${IMAGE}:${TAG} ..."
docker build \
  --platform linux/amd64 \
  --build-arg VITE_CLERK_PUBLISHABLE_KEY="$VITE_CLERK_KEY" \
  -t "${IMAGE}:${TAG}" .

echo "Pushing ${IMAGE}:${TAG} ..."
docker push "${IMAGE}:${TAG}"

if [ "$TAG" != "latest" ]; then
  docker tag "${IMAGE}:${TAG}" "${IMAGE}:latest"
  docker push "${IMAGE}:latest"
fi

echo "Done: ${IMAGE}:${TAG}"
