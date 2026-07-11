# Deployment Integration Implementation Plan

> Execution rule: each task is started only after the user explicitly sends `执行 Task N`.

## Goal

Integrate the existing ecommerce warehouse services into a deployable local stack:

```text
MySQL ADS tables -> FastAPI ADS API -> Vue/ECharts dashboard
```

The phase should make the project easier to start, verify, and demo after the Vue/ECharts dashboard work merged in PR #7.

## Current Baseline

- `docker-compose.yml` already defines Hadoop, Hive, Spark, and MySQL services.
- FastAPI backend exists under `backend/` and exposes `/api/health` plus ADS endpoints.
- Vue/ECharts dashboard exists under `frontend/` and uses `/api/ads/overview`.
- Vite dev proxy forwards local `/api` calls to `http://127.0.0.1:8000`.
- `deploy/scripts/check.ps1` validates project foundation paths.

## Out Of Scope

- New ADS tables or warehouse metric semantics.
- Authentication.
- Cloud provider provisioning.
- Kubernetes deployment.
- Rewriting the dashboard UX.

## Task 1: Backend Container Packaging

**Files:**
- Create: `backend/Dockerfile`
- Create or modify only if needed: `.dockerignore`
- Modify: `deploy/scripts/check.ps1`

**Requirements:**
- Build a FastAPI backend image from the repo root or backend context.
- Install `backend/requirements.txt`.
- Run `uvicorn backend.app.main:app` on `0.0.0.0:8000`.
- Preserve environment-driven MySQL configuration.
- Add foundation checks for new Docker assets.

**Verification:**

```powershell
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
docker build -f backend/Dockerfile -t ecommerce-spark-warehouse-backend:local .
```

## Task 2: Frontend Production Container Packaging

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/nginx.conf`
- Modify: `deploy/scripts/check.ps1`

**Requirements:**
- Build Vue dashboard with `npm ci` / `npm run build`.
- Serve `frontend/dist` through Nginx.
- Proxy `/api/` to backend service inside Docker Compose.
- Support SPA fallback to `index.html`.
- Add foundation checks for new frontend deployment assets.

**Verification:**

```powershell
npm.cmd run test:assets --prefix frontend
npm.cmd run build --prefix frontend
docker build -f frontend/Dockerfile -t ecommerce-spark-warehouse-frontend:local frontend
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

## Task 3: Docker Compose Service Integration

**Files:**
- Modify: `docker-compose.yml`
- Modify: `.env.example`
- Modify: `deploy/scripts/check.ps1` if needed

**Requirements:**
- Add `backend` service connected to `mysql`.
- Add `frontend` service connected to `backend`.
- Keep existing Hadoop/Hive/Spark/MySQL services intact.
- Use MySQL service hostname `mysql` for backend container defaults.
- Expose backend on `8000` and frontend on `5173` or `8088` with a stable documented port.
- Add health checks where practical.

**Verification:**

```powershell
docker compose config
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

## Task 4: Deployment Smoke Test Script

**Files:**
- Create: `deploy/scripts/smoke_test.ps1`
- Modify: `deploy/scripts/check.ps1`

**Requirements:**
- Check:
  - backend health endpoint
  - ADS overview endpoint shape
  - frontend page availability
- Allow configurable URLs through parameters:
  - `-BackendBaseUrl`
  - `-FrontendBaseUrl`
- Print clear pass/fail messages.
- Exit non-zero on failure.

**Verification:**

```powershell
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
powershell -ExecutionPolicy Bypass -File deploy/scripts/smoke_test.ps1 -BackendBaseUrl http://127.0.0.1:8000 -FrontendBaseUrl http://127.0.0.1:5173
```

If services are not running, the smoke test is expected to fail with a clear message.

## Task 5: Local Deployment Documentation

**Files:**
- Create: `docs/deployment-integration.md`
- Modify: `README.md`

**Requirements:**
- Document local startup paths:
  - foundation check
  - MySQL/Hadoop/Hive/Spark stack
  - backend API
  - frontend dashboard
  - smoke test
- Document environment variables and service ports.
- Explain mock fallback vs real FastAPI/MySQL data path.
- Keep docs concise and operational.

**Verification:**

```powershell
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

## Task 6: Integrated Verification

**Files:**
- No implementation files unless verification exposes a blocker.

**Requirements:**
- Run the full local verification set:

```powershell
npm.cmd run test:assets --prefix frontend
npm.cmd run build --prefix frontend
python -m pytest backend/tests -q
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
docker compose config
```

- If Docker is available, build the backend and frontend images.
- If services can be started locally, run `deploy/scripts/smoke_test.ps1`.
- Request final code review.
- Fix Critical and Important findings.

## Task 7: Push And PR

**Files:**
- No implementation files unless final review finds a blocker.

**Requirements:**
- Push branch `codex/phase8-deployment-integration`.
- Create a ready PR against `main`.
- PR body includes:
  - Summary
  - Verification commands
  - Docker/smoke test status
  - Any known local environment limitations

## Completion Criteria

- Backend and frontend have production container packaging.
- Docker Compose includes dashboard-facing backend/frontend services.
- A smoke test script exists for API and frontend availability.
- Documentation explains how to run and verify the integrated stack.
- Final PR is open and ready for review.
