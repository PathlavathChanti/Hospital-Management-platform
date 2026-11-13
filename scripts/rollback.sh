#!/usr/bin/env bash
set -euo pipefail

# -------------------------------------------------------------------
# rollback.sh <previous-image-tag> – Roll back to a previous image
# -------------------------------------------------------------------
if [ $# -lt 1 ]; then
  echo "Usage: $0 <previous-image-tag>"
  echo "  e.g. $0 ghcr.io/pathlavathchanti/hospital-management-platform:git-abc1234"
  exit 1
fi

PREVIOUS_TAG="$1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "[$(date -Iseconds)] Rolling back to image: ${PREVIOUS_TAG}"

# Update IMAGE_TAG in .env
if grep -q '^IMAGE_TAG=' "${PROJECT_DIR}/.env"; then
  sed -i "s|^IMAGE_TAG=.*|IMAGE_TAG=${PREVIOUS_TAG}|" "${PROJECT_DIR}/.env"
else
  echo "IMAGE_TAG=${PREVIOUS_TAG}" >> "${PROJECT_DIR}/.env"
fi

export IMAGE_TAG="${PREVIOUS_TAG}"

echo "[$(date -Iseconds)] Pulling new image and restarting..."
docker compose -f "${PROJECT_DIR}/docker-compose.yml" pull app
docker compose -f "${PROJECT_DIR}/docker-compose.yml" up -d app

# Wait for readiness
echo "[$(date -Iseconds)] Waiting for /ready..."
for i in $(seq 1 30); do
  if curl -sk https://localhost/ready 2>/dev/null | grep -q '"ready"'; then
    echo "[$(date -Iseconds)] Rollback successful – /ready is healthy"
    exit 0
  fi
  sleep 2
done

echo "[$(date -Iseconds)] WARNING: /ready did not become healthy within 60s"
exit 1
