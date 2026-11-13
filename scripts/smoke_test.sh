#!/usr/bin/env bash
set -euo pipefail

# -------------------------------------------------------------------
# smoke_test.sh – Quick smoke test of the deployed API
# -------------------------------------------------------------------
BASE_URL="https://localhost"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
EVIDENCE_DIR="${PROJECT_DIR}/docs/evidence"
mkdir -p "${EVIDENCE_DIR}"
OUTPUT="${EVIDENCE_DIR}/smoke_test_output.txt"
echo "" > "${OUTPUT}"

log() {
  echo "[$(date -Iseconds)] $*" | tee -a "${OUTPUT}"
}

log "==== Smoke Test ===="

# Health check
log "GET /health"
curl -sk "${BASE_URL}/health" | tee -a "${OUTPUT}"
echo "" | tee -a "${OUTPUT}"

# Readiness
log "GET /ready"
curl -sk "${BASE_URL}/ready" | tee -a "${OUTPUT}"
echo "" | tee -a "${OUTPUT}"

# Login as admin
log "POST /auth/login (admin)"
TOKEN=$(curl -sk -X POST "${BASE_URL}/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
log "Token obtained: ${TOKEN:0:20}..."

# List doctors
log "GET /doctors"
curl -sk -H "Authorization: Bearer ${TOKEN}" "${BASE_URL}/doctors" | python3 -m json.tool | tee -a "${OUTPUT}"

log ""
log "==== Smoke test passed ===="
