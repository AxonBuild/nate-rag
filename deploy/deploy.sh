#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
SPEC_TEMPLATE="$SCRIPT_DIR/app-spec.yaml"

# Load env files
for f in "$REPO_DIR/backend/app/.env" "$REPO_DIR/frontend/.env"; do
  if [ -f "$f" ]; then
    set -a
    source "$f"
    set +a
  fi
done

SPEC=$(envsubst < "$SPEC_TEMPLATE")

APP_NAME="nate-rag"
APP_ID=$(doctl apps list --format ID,Spec.Name --no-header | awk -v n="$APP_NAME" '$2==n {print $1}')

if [ -n "$APP_ID" ]; then
  echo "Updating app $APP_ID ..."
  echo "$SPEC" | doctl apps update "$APP_ID" --spec -
else
  echo "Creating app ..."
  echo "$SPEC" | doctl apps create --spec -
fi

echo "Done."
