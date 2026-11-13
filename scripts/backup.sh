#!/usr/bin/env bash
set -euo pipefail

# -------------------------------------------------------------------
# backup.sh – Dump Postgres via docker compose, gzip, retain last N
# -------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_DIR}/backups"
RETAIN=${RETAIN:-7}
TIMESTAMP=$(date +%Y-%m-%d_%H%M)
OUTPUT="${BACKUP_DIR}/db_${TIMESTAMP}.sql.gz"
EVIDENCE_DIR="${PROJECT_DIR}/docs/evidence"

# Load env vars
if [ -f "${PROJECT_DIR}/.env" ]; then
  set -a; source "${PROJECT_DIR}/.env"; set +a
fi

mkdir -p "${BACKUP_DIR}" "${EVIDENCE_DIR}"

echo "[$(date -Iseconds)] Starting backup..."
docker compose -f "${PROJECT_DIR}/docker-compose.yml" exec -T db \
  pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" | gzip > "${OUTPUT}"

echo "[$(date -Iseconds)] Backup saved to ${OUTPUT} ($(du -h "${OUTPUT}" | cut -f1))"

# Retain only last N backups
cd "${BACKUP_DIR}"
ls -1t db_*.sql.gz | tail -n +$((RETAIN + 1)) | xargs -r rm -v

echo "[$(date -Iseconds)] Backup complete. Files retained: $(ls -1 db_*.sql.gz | wc -l)"

# Tee evidence
echo "Backup created: ${OUTPUT}" | tee "${EVIDENCE_DIR}/backup_output.txt"
