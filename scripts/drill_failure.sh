#!/usr/bin/env bash
set -euo pipefail

# -------------------------------------------------------------------
# drill_failure.sh – Simulate failures and demonstrate detection/recovery
# -------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
EVIDENCE_DIR="${PROJECT_DIR}/docs/evidence"
mkdir -p "${EVIDENCE_DIR}"
OUTPUT="${EVIDENCE_DIR}/drill_output.txt"

echo "" > "${OUTPUT}"

log() {
  echo "[$(date -Iseconds)] $*" | tee -a "${OUTPUT}"
}

check_ready() {
  HTTP_CODE=$(curl -sk -o /dev/null -w '%{http_code}' https://localhost/ready 2>/dev/null || echo "000")
  echo "${HTTP_CODE}"
}

# ---- Drill 1: App failure ----
log "==== DRILL 1: Simulate App Failure ===="
log "Stopping app container..."
docker compose -f "${PROJECT_DIR}/docker-compose.yml" stop app
sleep 3

HTTP=$(check_ready)
log "/ready returned: ${HTTP} (expected: 000 or 502)"
log "Container status:"
docker compose -f "${PROJECT_DIR}/docker-compose.yml" ps | tee -a "${OUTPUT}"

log "Restarting app container..."
docker compose -f "${PROJECT_DIR}/docker-compose.yml" start app
sleep 5

HTTP=$(check_ready)
log "/ready after recovery: ${HTTP} (expected: 200)"

# ---- Drill 2: Database failure ----
log ""
log "==== DRILL 2: Simulate Database Failure ===="
log "Killing db container..."
docker compose -f "${PROJECT_DIR}/docker-compose.yml" kill db
sleep 3

HTTP=$(check_ready)
log "/ready returned: ${HTTP} (expected: 503)"

log "Restarting db container..."
docker compose -f "${PROJECT_DIR}/docker-compose.yml" start db
sleep 8

HTTP=$(check_ready)
log "/ready after DB recovery: ${HTTP} (expected: 200)"

# ---- Verify data persistence ----
log ""
log "==== Verifying data persistence ===="
if [ -f "${PROJECT_DIR}/.env" ]; then
  set -a; source "${PROJECT_DIR}/.env"; set +a
fi
ROW_COUNT=$(docker compose -f "${PROJECT_DIR}/docker-compose.yml" exec -T db \
  psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -t -c "SELECT COUNT(*) FROM doctors;" 2>/dev/null || echo "ERROR")
log "Doctor rows after recovery: ${ROW_COUNT}"

log ""
log "==== Drill complete ===="
