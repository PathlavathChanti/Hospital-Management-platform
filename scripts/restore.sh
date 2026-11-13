#!/usr/bin/env bash
set -euo pipefail

# -------------------------------------------------------------------
# restore.sh <backup-file> – Restore a pg_dump into Postgres
# -------------------------------------------------------------------
if [ $# -lt 1 ]; then
  echo "Usage: $0 <backup-file.sql.gz>"
  exit 1
fi

BACKUP_FILE="$1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
EVIDENCE_DIR="${PROJECT_DIR}/docs/evidence"

if [ ! -f "${BACKUP_FILE}" ]; then
  echo "ERROR: File not found: ${BACKUP_FILE}"
  exit 1
fi

# Load env vars
if [ -f "${PROJECT_DIR}/.env" ]; then
  set -a; source "${PROJECT_DIR}/.env"; set +a
fi

mkdir -p "${EVIDENCE_DIR}"

echo "[$(date -Iseconds)] Stopping app..." | tee "${EVIDENCE_DIR}/restore_output.txt"
docker compose -f "${PROJECT_DIR}/docker-compose.yml" stop app

echo "[$(date -Iseconds)] Dropping and recreating database..." | tee -a "${EVIDENCE_DIR}/restore_output.txt"
docker compose -f "${PROJECT_DIR}/docker-compose.yml" exec -T db \
  psql -U "${POSTGRES_USER}" -d postgres \
  -c "DROP DATABASE IF EXISTS ${POSTGRES_DB};" \
  -c "CREATE DATABASE ${POSTGRES_DB};"

echo "[$(date -Iseconds)] Restoring from ${BACKUP_FILE}..." | tee -a "${EVIDENCE_DIR}/restore_output.txt"
gunzip -c "${BACKUP_FILE}" | docker compose -f "${PROJECT_DIR}/docker-compose.yml" exec -T db \
  psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"

echo "[$(date -Iseconds)] Starting app..." | tee -a "${EVIDENCE_DIR}/restore_output.txt"
docker compose -f "${PROJECT_DIR}/docker-compose.yml" start app

# Verify
sleep 5
ROW_COUNT=$(docker compose -f "${PROJECT_DIR}/docker-compose.yml" exec -T db \
  psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -t -c "SELECT COUNT(*) FROM appointments;")
echo "[$(date -Iseconds)] Restore complete. Appointment rows: ${ROW_COUNT}" | tee -a "${EVIDENCE_DIR}/restore_output.txt"
