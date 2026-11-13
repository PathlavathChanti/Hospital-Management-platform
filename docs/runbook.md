# Operational Runbook

## Common Operations

### Deploy / Update
```bash
# Pull latest image and restart
docker compose pull app
docker compose up -d app
```

### Restart All Services
```bash
docker compose restart
```

### View Logs
```bash
# All services
docker compose logs -f

# App only
docker compose logs -f app

# Last 100 lines
docker compose logs --tail=100 app
```

### Health vs Readiness

| Endpoint | Purpose | DB Required | Use Case |
|---|---|---|---|
| `GET /health` | Liveness | No | Container orchestrator restart check |
| `GET /ready` | Readiness | Yes (SELECT 1) | Load balancer traffic routing |

If `/health` fails → the process is hung, restart the container.
If `/ready` fails → the app is running but cannot reach the DB.

### Backup
```bash
bash scripts/backup.sh
```

### Restore
```bash
bash scripts/restore.sh backups/db_2024-01-15_1430.sql.gz
```

### Rollback
```bash
bash scripts/rollback.sh ghcr.io/pathlavathchanti/hospital-management-platform:git-abc1234
```

## Incident Response

| Symptom | Check | Fix |
|---|---|---|
| App returns 502/503 | `docker compose ps` – is `app` running? | `docker compose restart app` |
| `/ready` returns 503 | `docker compose logs db` – is Postgres healthy? | `docker compose restart db`, then `docker compose restart app` |
| 409 Conflict spikes | Check if a client is retrying rapidly | Review client code; the partial unique index is working correctly |
| TLS certificate errors | `curl -vk https://localhost/health` | Caddy regenerates internal certs on restart: `docker compose restart caddy` |
| Disk full | `df -h` and `docker system df` | `docker system prune`, delete old backups, expand disk |
| Slow responses | `docker compose logs app` – check latency_ms | Scale resources, check DB query plans |
| Auth failures (401) | Verify JWT_SECRET matches between app restarts | Ensure `.env` has correct JWT_SECRET |
| Data loss suspected | Check pgdata volume | Restore from latest backup: `bash scripts/restore.sh <file>` |
