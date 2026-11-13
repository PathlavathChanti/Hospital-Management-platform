# Hospital Management Platform

A Doctor Appointment API built with FastAPI, PostgreSQL, Docker, and Caddy – designed to demonstrate production-style CI/CD, reliability, and operations.

## Overview

This project implements a small but complete **Doctor Appointment API** with:
- JWT-based authentication (patient / receptionist / admin roles)
- CRUD operations for appointments with business-rule validation
- Concurrency-safe booking via a PostgreSQL partial unique index
- Structured JSON logging with request-ID tracing
- Audit trail for all state-changing operations

## Prerequisites

- **Docker** & **Docker Compose** (v2+)
- **Git**
- **curl** (for smoke tests)
- (Optional) Python 3.12+ for local development

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/PathlavathChanti/Hospital-Management-platform.git
cd Hospital-Management-platform

# 2. Create .env from the example
cp .env.example .env

# 3. Build and start all services
docker compose up -d --build

# 4. Seed the database with demo data
docker compose exec app python -m app.seed

# 5. Run the smoke test
bash scripts/smoke_test.sh
```

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `POSTGRES_USER` | PostgreSQL username | `hospital_user` |
| `POSTGRES_PASSWORD` | PostgreSQL password | *(must set)* |
| `POSTGRES_DB` | Database name | `hospital_db` |
| `DATABASE_URL` | Full connection string | *(auto-constructed)* |
| `JWT_SECRET` | Secret key for JWT signing | *(must set)* |
| `JWT_EXPIRE_MINUTES` | Token expiry in minutes | `60` |
| `LOG_LEVEL` | Application log level | `INFO` |
| `IMAGE_TAG` | Docker image tag | `ghcr.io/pathlavathchanti/hospital-management-platform:latest` |

## Port Map

| Port | Service | Exposure |
|---|---|---|
| 443 | Caddy (HTTPS) | Public |
| 80 | Caddy (HTTP → HTTPS) | Public |
| 8000 | FastAPI app | Internal only |
| 5432 | PostgreSQL | Internal only |

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | None | Liveness probe |
| GET | `/ready` | None | Readiness probe (checks DB) |
| POST | `/auth/login` | None | Returns JWT |
| GET | `/doctors` | None | List all doctors |
| GET | `/doctors/{id}/slots?date=YYYY-MM-DD` | Bearer | 30-min slots with booking status |
| POST | `/appointments/` | Bearer | Create appointment |
| GET | `/appointments/` | Bearer | List appointments (role-filtered) |
| PATCH | `/appointments/{id}` | Bearer | Reschedule |
| DELETE | `/appointments/{id}` | Bearer | Cancel (soft-delete) |

## Demo Credentials (seed data only)

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | admin |
| `reception` | `reception123` | receptionist |
| `patient01`–`patient08` | `patient123` | patient |

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push and PR:

1. **Lint** – `ruff check` and `ruff format --check`
2. **Test** – `pytest` against a real PostgreSQL service container
3. **Build & Scan** – Docker buildx build, Trivy image + filesystem scan
4. **Publish** – Push to GHCR with SHA and semantic version tags

## Rollback Procedure

```bash
# Roll back to a previous image tag
bash scripts/rollback.sh ghcr.io/pathlavathchanti/hospital-management-platform:git-<previous-sha>
```

The script updates `IMAGE_TAG` in `.env`, pulls the image, restarts the app, and waits for `/ready` to confirm health.

## Operations Scripts

| Script | Purpose |
|---|---|
| `scripts/backup.sh` | Dump DB to gzipped SQL, retain last 7 |
| `scripts/restore.sh <file>` | Restore from a backup dump |
| `scripts/rollback.sh <tag>` | Roll back to a previous image |
| `scripts/drill_failure.sh` | Simulate app/DB failures and recovery |
| `scripts/smoke_test.sh` | Quick API smoke test |

## Security Notes

- No real secrets are committed; `.env` is in `.gitignore`.
- The Docker image runs as a non-root user (`appuser`).
- Caddy provides automatic HTTPS with `tls internal` (self-signed for local).
- Network segmentation: the database is on an internal-only network.
- JWT secrets, DB passwords must be strong in production.

## Known Limitations & Assumptions

- **Self-signed TLS**: The Caddy config uses `tls internal`, suitable for local development only.
- **No horizontal scaling**: Single-instance deployment; for HA, use a container orchestrator.
- **UTC times**: All slot times are treated as UTC.
- **No rate limiting**: Consider adding for production use.
- **Seed passwords**: Demo passwords are weak and intended only for testing.
