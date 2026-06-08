#!/usr/bin/env bash
set -euo pipefail

# Load backend env
ENV_FILE="backend/app/.env"
if [ ! -f "$ENV_FILE" ]; then
  echo "Error: $ENV_FILE not found" >&2
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

# Render the app spec with env vars substituted
SPEC=$(envsubst < app-spec.yaml)

APP_NAME="nate-rag"
APP_ID=$(doctl apps list --format ID,Spec.Name --no-header | awk -v n="$APP_NAME" '$2==n {print $1}')

if [ -n "$APP_ID" ]; then
  echo "Updating existing app ${APP_ID} ..."
  echo "$SPEC" | doctl apps update "$APP_ID" --spec -
else
  echo "Creating new app ..."
  echo "$SPEC" | doctl apps create --spec -
fi

echo "Done. Check status with: doctl apps list"
