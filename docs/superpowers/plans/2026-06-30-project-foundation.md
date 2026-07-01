# Project Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the repository foundation for `ecommerce-spark-warehouse` so later crawler, warehouse, Spark, backend, frontend, deployment, and GitHub sync work has stable structure and verification commands.

**Architecture:** This phase creates the project skeleton, minimal runnable service shells, documentation entry points, and validation scripts. It does not build the full data warehouse yet; it prepares clean module boundaries for the next implementation plans.

**Tech Stack:** Git, PowerShell, Python, pytest, FastAPI, Vue 3, ECharts, Docker Compose, HDFS, Hive, Spark, MySQL.

---

## Scope Check

The approved design covers multiple independent subsystems: crawler, warehouse, Spark jobs, backend API, frontend dashboard, deployment, and GitHub synchronization. Implementing all of them in one plan would be too large and hard to verify. This plan is the first phase: project foundation. Later phases should each get their own plan:

- Crawler pipeline and raw data landing.
- HDFS, Hive schemas, and warehouse SQL.
- Spark offline jobs and ADS export.
- FastAPI dashboard API.
- Vue + ECharts dashboard.
- Docker Compose integration and server deployment docs.

## File Structure

This phase creates or modifies these files:

- Modify: `.gitignore` to keep local artifacts out of Git.
- Delete: `architecture-options.html`, the temporary visual brainstorming file.
- Create: `README.md` as the project entry point.
- Create: `.env.example` with non-secret local configuration.
- Create: `docker-compose.yml` with named services and stable ports.
- Create: `crawler/README.md` for crawler module boundaries.
- Create: `crawler/config/sources.json` for configurable data sources.
- Create: `crawler/tests/test_sources_config.py` to validate crawler source config.
- Create: `backend/app/main.py` with a health endpoint.
- Create: `backend/requirements.txt` with runtime and test dependencies.
- Create: `backend/tests/test_health.py` for the health endpoint.
- Create: `frontend/package.json` for Vue dashboard dependencies and scripts.
- Create: `frontend/src/main.js` and `frontend/src/App.vue` as a minimal dashboard shell.
- Create: `warehouse/README.md` to explain warehouse layer ownership.
- Create: `deploy/scripts/check.ps1` to validate expected files exist.
- Create: `docs/github-workflow.md` with GitHub sync rules.

## Task 1: Repository Housekeeping

**Files:**
- Modify: `.gitignore`
- Delete: `architecture-options.html`

- [ ] **Step 1: Remove the temporary architecture HTML file**

Run:

```powershell
Remove-Item -LiteralPath "architecture-options.html"
```

Expected: command exits with code 0 when the file exists. If the file is already gone, run:

```powershell
Test-Path -LiteralPath "architecture-options.html"
```

Expected: `False`.

- [ ] **Step 2: Confirm `.gitignore` keeps local artifacts out of Git**

Ensure `.gitignore` contains:

```gitignore
.env
.env.*
!.env.example
__pycache__/
*.py[cod]
.pytest_cache/
.venv/
venv/
node_modules/
dist/
build/
.vite/
data/raw/
data/output/
data/tmp/
logs/
*.log
volumes/
docker-data/
.superpowers/
.DS_Store
Thumbs.db
.idea/
.vscode/
```

- [ ] **Step 3: Verify repository status**

Run:

```powershell
git status --short
```

Expected: `architecture-options.html` is no longer listed.

## Task 2: Root Project Files

**Files:**
- Create: `README.md`
- Create: `.env.example`
- Create: `docker-compose.yml`

- [ ] **Step 1: Create `README.md`**

Write:

```markdown
# ecommerce-spark-warehouse

电商 Spark 离线数仓分析与可视化系统。

## Project Goal

This project builds an offline ecommerce data warehouse using Spark, HDFS, and Hive. It collects ecommerce-like data through a configurable crawler, stores raw data in HDFS, builds layered Hive tables, computes offline metrics with Spark SQL, exposes ADS metrics through FastAPI, and presents them in a Vue + ECharts dashboard.

## Tech Stack

- Data collection: Python crawler
- Storage: HDFS
- Warehouse: Hive
- Compute: Spark SQL
- Result store: MySQL
- API: FastAPI
- Dashboard: Vue 3 + ECharts
- Deployment: Docker Compose

## Planned Data Flow

```text
Crawler -> Local raw files -> HDFS -> Hive ODS/DWD/DIM/DWS/ADS
        -> Spark offline jobs -> MySQL ADS result tables
        -> FastAPI -> Vue + ECharts dashboard
```

## Repository Structure

```text
crawler/      Data collection module
warehouse/    HDFS, Hive, and Spark warehouse assets
backend/      FastAPI dashboard API
frontend/     Vue + ECharts dashboard
deploy/       Local and server deployment scripts
docs/         Architecture, data model, deployment, and GitHub workflow docs
```

## First Verification

```powershell
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```
```

- [ ] **Step 2: Create `.env.example`**

Write:

```dotenv
PROJECT_NAME=ecommerce-spark-warehouse
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_DATABASE=ecommerce_ads
MYSQL_USER=ecommerce
MYSQL_PASSWORD=ecommerce_password
HDFS_NAMENODE=hdfs://namenode:8020
HIVE_SERVER_HOST=hive-server2
HIVE_SERVER_PORT=10000
SPARK_MASTER_URL=spark://spark-master:7077
BACKEND_PORT=8000
FRONTEND_PORT=8080
```

- [ ] **Step 3: Create `docker-compose.yml`**

Write:

```yaml
name: ecommerce-spark-warehouse

services:
  namenode:
    image: apache/hadoop:3.3.6
    container_name: esw-namenode
    command: ["hdfs", "namenode"]
    ports:
      - "9870:9870"
      - "8020:8020"
    volumes:
      - namenode-data:/tmp/hadoop-root/dfs/name

  datanode:
    image: apache/hadoop:3.3.6
    container_name: esw-datanode
    command: ["hdfs", "datanode"]
    depends_on:
      - namenode
    ports:
      - "9864:9864"
    volumes:
      - datanode-data:/tmp/hadoop-root/dfs/data

  mysql:
    image: mysql:8.4
    container_name: esw-mysql
    environment:
      MYSQL_ROOT_PASSWORD: root_password
      MYSQL_DATABASE: ecommerce_ads
      MYSQL_USER: ecommerce
      MYSQL_PASSWORD: ecommerce_password
    ports:
      - "3306:3306"
    volumes:
      - mysql-data:/var/lib/mysql

  spark-master:
    image: bitnami/spark:3.5
    container_name: esw-spark-master
    environment:
      SPARK_MODE: master
    ports:
      - "7077:7077"
      - "8081:8080"

  spark-worker:
    image: bitnami/spark:3.5
    container_name: esw-spark-worker
    environment:
      SPARK_MODE: worker
      SPARK_MASTER_URL: spark://spark-master:7077
    depends_on:
      - spark-master

  hive-metastore:
    image: apache/hive:4.0.0
    container_name: esw-hive-metastore
    environment:
      SERVICE_NAME: metastore
      DB_DRIVER: mysql
      SERVICE_OPTS: "-Djavax.jdo.option.ConnectionURL=jdbc:mysql://mysql:3306/ecommerce_ads -Djavax.jdo.option.ConnectionDriverName=com.mysql.cj.jdbc.Driver -Djavax.jdo.option.ConnectionUserName=ecommerce -Djavax.jdo.option.ConnectionPassword=ecommerce_password"
    depends_on:
      - mysql
      - namenode
    ports:
      - "9083:9083"

  hive-server2:
    image: apache/hive:4.0.0
    container_name: esw-hive-server2
    environment:
      SERVICE_NAME: hiveserver2
      HIVE_METASTORE_URI: thrift://hive-metastore:9083
    depends_on:
      - hive-metastore
    ports:
      - "10000:10000"

volumes:
  namenode-data:
  datanode-data:
  mysql-data:
```

- [ ] **Step 4: Validate Compose syntax without starting containers**

Run:

```powershell
docker compose config
```

Expected: exit code 0 and rendered service configuration. If Docker is unavailable, record the exact error in the implementation notes.

- [ ] **Step 5: Commit root project files**

Run:

```powershell
git add README.md .env.example docker-compose.yml .gitignore
git commit -m "chore: initialize project foundation"
```

Expected: commit succeeds.

## Task 3: Crawler Module Skeleton

**Files:**
- Create: `crawler/README.md`
- Create: `crawler/config/sources.json`
- Create: `crawler/tests/test_sources_config.py`

- [ ] **Step 1: Create `crawler/README.md`**

Write:

```markdown
# Crawler Module

The crawler module collects stable ecommerce-like data for the offline warehouse.

The default data source is DummyJSON:

- `https://dummyjson.com/products`
- `https://dummyjson.com/carts`
- `https://dummyjson.com/users`

Raw crawler output will be written under `crawler/data/raw/` during implementation. That directory is ignored by Git.
```

- [ ] **Step 2: Create `crawler/config/sources.json`**

Write:

```json
{
  "sources": [
    {
      "name": "products",
      "url": "https://dummyjson.com/products",
      "entity": "product"
    },
    {
      "name": "carts",
      "url": "https://dummyjson.com/carts",
      "entity": "order"
    },
    {
      "name": "users",
      "url": "https://dummyjson.com/users",
      "entity": "user"
    }
  ]
}
```

- [ ] **Step 3: Write the config validation test**

Write `crawler/tests/test_sources_config.py`:

```python
import json
from pathlib import Path


def test_sources_config_contains_required_dummyjson_sources():
    config_path = Path(__file__).resolve().parents[1] / "config" / "sources.json"
    data = json.loads(config_path.read_text(encoding="utf-8"))

    names = {source["name"] for source in data["sources"]}

    assert names == {"products", "carts", "users"}


def test_each_source_has_url_and_entity():
    config_path = Path(__file__).resolve().parents[1] / "config" / "sources.json"
    data = json.loads(config_path.read_text(encoding="utf-8"))

    for source in data["sources"]:
        assert source["url"].startswith("https://dummyjson.com/")
        assert source["entity"] in {"product", "order", "user"}
```

- [ ] **Step 4: Run crawler config tests**

Run:

```powershell
python -m pytest crawler/tests/test_sources_config.py -v
```

Expected: 2 tests pass. If pytest is not installed, create a root `requirements-dev.txt` with `pytest==8.2.2`, install it in the local environment, and rerun the command.

- [ ] **Step 5: Commit crawler skeleton**

Run:

```powershell
git add crawler/README.md crawler/config/sources.json crawler/tests/test_sources_config.py
git commit -m "feat: add crawler source configuration"
```

Expected: commit succeeds.

## Task 4: Backend API Skeleton

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/requirements.txt`
- Create: `backend/tests/test_health.py`

- [ ] **Step 1: Create `backend/requirements.txt`**

Write:

```text
fastapi==0.111.0
uvicorn[standard]==0.30.1
pytest==8.2.2
httpx==0.27.0
```

- [ ] **Step 2: Write a failing health endpoint test**

Write `backend/tests/test_health.py`:

```python
from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_endpoint_returns_project_status():
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ecommerce-spark-warehouse-api"
    }
```

- [ ] **Step 3: Run the test and verify it fails before implementation**

Run:

```powershell
python -m pytest backend/tests/test_health.py -v
```

Expected before `backend/app/main.py` exists: FAIL with `ModuleNotFoundError`.

- [ ] **Step 4: Implement `backend/app/main.py`**

Write:

```python
from fastapi import FastAPI


app = FastAPI(title="Ecommerce Spark Warehouse API")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ecommerce-spark-warehouse-api"
    }
```

- [ ] **Step 5: Run the backend health test**

Run:

```powershell
python -m pytest backend/tests/test_health.py -v
```

Expected: 1 test passes.

- [ ] **Step 6: Commit backend skeleton**

Run:

```powershell
git add backend/app/main.py backend/requirements.txt backend/tests/test_health.py
git commit -m "feat: add fastapi health endpoint"
```

Expected: commit succeeds.

## Task 5: Frontend Dashboard Skeleton

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/src/main.js`
- Create: `frontend/src/App.vue`

- [ ] **Step 1: Create `frontend/package.json`**

Write:

```json
{
  "name": "ecommerce-spark-warehouse-dashboard",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --host 0.0.0.0",
    "build": "vite build",
    "preview": "vite preview --host 0.0.0.0"
  },
  "dependencies": {
    "@vitejs/plugin-vue": "5.0.5",
    "echarts": "5.5.0",
    "vite": "5.3.1",
    "vue": "3.4.29"
  },
  "devDependencies": {}
}
```

- [ ] **Step 2: Create `frontend/src/main.js`**

Write:

```javascript
import { createApp } from 'vue'
import App from './App.vue'

createApp(App).mount('#app')
```

- [ ] **Step 3: Create `frontend/src/App.vue`**

Write:

```vue
<template>
  <main class="dashboard">
    <header class="dashboard__header">
      <p class="eyebrow">Ecommerce Spark Warehouse</p>
      <h1>电商经营分析大屏</h1>
      <p class="subtitle">Spark + HDFS + Hive 离线数仓指标展示</p>
    </header>

    <section class="kpi-grid" aria-label="核心指标">
      <article v-for="item in kpis" :key="item.label" class="kpi-card">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </article>
    </section>
  </main>
</template>

<script setup>
const kpis = [
  { label: '销售额', value: '0.00' },
  { label: '订单数', value: '0' },
  { label: '支付用户', value: '0' },
  { label: '转化率', value: '0%' }
]
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  padding: 32px;
  background: #07111f;
  color: #eef5ff;
  font-family: "Microsoft YaHei", system-ui, sans-serif;
}

.dashboard__header {
  margin-bottom: 28px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #26d9c7;
  font-size: 14px;
}

h1 {
  margin: 0;
  font-size: 32px;
}

.subtitle {
  margin: 10px 0 0;
  color: #9fb1c9;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.kpi-card {
  border: 1px solid #2b4262;
  border-radius: 8px;
  padding: 18px;
  background: #101b2e;
}

.kpi-card span {
  display: block;
  color: #9fb1c9;
  font-size: 14px;
}

.kpi-card strong {
  display: block;
  margin-top: 10px;
  font-size: 28px;
}

@media (max-width: 860px) {
  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 520px) {
  .dashboard {
    padding: 20px;
  }

  .kpi-grid {
    grid-template-columns: 1fr;
  }
}
</style>
```

- [ ] **Step 4: Install frontend dependencies**

Run:

```powershell
Set-Location frontend
npm install
Set-Location ..
```

Expected: `frontend/package-lock.json` is created and install exits with code 0.

- [ ] **Step 5: Run frontend build**

Run:

```powershell
Set-Location frontend
npm run build
Set-Location ..
```

Expected: Vite build exits with code 0.

- [ ] **Step 6: Commit frontend skeleton**

Run:

```powershell
git add frontend/package.json frontend/package-lock.json frontend/src/main.js frontend/src/App.vue
git commit -m "feat: add vue dashboard shell"
```

Expected: commit succeeds.

## Task 6: Warehouse and Deployment Documentation Skeleton

**Files:**
- Create: `warehouse/README.md`
- Create: `deploy/scripts/check.ps1`
- Create: `docs/github-workflow.md`

- [ ] **Step 1: Create `warehouse/README.md`**

Write:

```markdown
# Warehouse Module

This module owns HDFS directory planning, Hive warehouse SQL, Spark jobs, and ADS export assets.

Layer ownership:

- `hive/ods`: raw mapped tables.
- `hive/dwd`: cleaned detailed tables.
- `hive/dim`: shared dimension tables.
- `hive/dws`: subject summary tables.
- `hive/ads`: dashboard-ready metric tables.
- `spark/jobs`: Spark SQL and PySpark offline jobs.
- `spark/submit`: submit scripts.
```

- [ ] **Step 2: Create `deploy/scripts/check.ps1`**

Write:

```powershell
$ErrorActionPreference = "Stop"

$requiredPaths = @(
  "README.md",
  ".env.example",
  "docker-compose.yml",
  "crawler/config/sources.json",
  "backend/app/main.py",
  "frontend/package.json",
  "warehouse/README.md",
  "docs/github-workflow.md"
)

foreach ($path in $requiredPaths) {
  if (-not (Test-Path -LiteralPath $path)) {
    throw "Missing required path: $path"
  }
}

Write-Host "Project foundation check passed."
```

- [ ] **Step 3: Create `docs/github-workflow.md`**

Write:

```markdown
# GitHub Workflow

Repository name: `ecommerce-spark-warehouse`

## Branches

- `main` is the main branch.
- Keep implementation commits small and aligned with project stages.

## Commit Pattern

- `chore: initialize project foundation`
- `feat: add crawler pipeline`
- `feat: add hive warehouse layers`
- `feat: add spark offline jobs`
- `feat: add fastapi dashboard api`
- `feat: add vue ecommerce dashboard`
- `docs: add deployment and warehouse documentation`
- `chore: verify docker compose deployment`

## Before Commit

Run:

```powershell
git status --short
```

Check that generated data, logs, secrets, local volumes, and `.env` files are not staged.
```

- [ ] **Step 4: Run foundation check**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

Expected:

```text
Project foundation check passed.
```

- [ ] **Step 5: Commit warehouse and deployment skeleton**

Run:

```powershell
git add warehouse/README.md deploy/scripts/check.ps1 docs/github-workflow.md
git commit -m "docs: add warehouse and github workflow skeleton"
```

Expected: commit succeeds.

## Task 7: Final Foundation Verification

**Files:**
- Read: `docs/superpowers/specs/2026-06-30-ecommerce-spark-warehouse-design.md`
- Read: `README.md`
- Read: `docs/github-workflow.md`

- [ ] **Step 1: Run all foundation checks**

Run:

```powershell
python -m pytest crawler/tests/test_sources_config.py backend/tests/test_health.py -v
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
git status --short
```

Expected:

- Crawler config tests pass.
- Backend health test passes.
- Foundation check prints `Project foundation check passed.`
- `git status --short` is empty or only lists intentionally untracked local files.

- [ ] **Step 2: Inspect commit history**

Run:

```powershell
git log --oneline -5
```

Expected: recent commits include the foundation, crawler config, backend health endpoint, frontend shell, and documentation skeleton commits.

- [ ] **Step 3: Stop and ask for GitHub remote confirmation**

Ask the user for the exact GitHub repository full name or remote URL for `ecommerce-spark-warehouse`.

Do not push until the user confirms the remote repository target.

## Self-Review

Spec coverage:

- Project foundation maps to the approved architecture and module structure.
- DummyJSON crawler source is captured in crawler config.
- Backend and frontend shells create stable places for dashboard implementation.
- Warehouse and deployment documentation entry points exist.
- GitHub workflow rules are documented.

Remaining planned work after this phase:

- Implement actual crawler fetch and raw data persistence.
- Implement HDFS upload scripts.
- Implement Hive SQL layers.
- Implement Spark offline jobs.
- Implement MySQL ADS export.
- Implement complete FastAPI dashboard endpoints.
- Implement full Vue + ECharts dashboard.
- Verify Docker Compose service compatibility and server deployment docs.

Placeholder scan:

- No incomplete marker strings or unspecified implementation steps are intentionally present.

Type and naming consistency:

- Project name consistently uses `ecommerce-spark-warehouse`.
- API health endpoint consistently uses `/api/health`.
- Crawler source names consistently use `products`, `carts`, and `users`.

