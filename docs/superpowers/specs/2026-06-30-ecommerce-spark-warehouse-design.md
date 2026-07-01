# Ecommerce Spark Warehouse Design

## Project Name

- Repository name: `ecommerce-spark-warehouse`
- Chinese name: 电商 Spark 离线数仓分析与可视化系统
- Project root: `D:\Codex Projects\spark`

## Goal

Build a course/graduation-project style offline data warehouse for ecommerce analysis. The system collects ecommerce data through a crawler, stores raw data in HDFS, builds Hive warehouse layers, computes offline metrics with Spark, exposes analysis results through FastAPI, and displays them in a Vue + ECharts dashboard.

The implementation should first run locally through Docker Compose, then include documentation for server deployment.

## Scope

In scope:

- Stable crawler-based data collection from public ecommerce-like APIs or static pages.
- HDFS raw data storage.
- Hive warehouse modeling with ODS, DWD, DIM, DWS, and ADS layers.
- Spark SQL offline metric computation.
- MySQL storage for dashboard-facing ADS metrics.
- FastAPI dashboard API.
- Vue + ECharts ecommerce operations dashboard.
- Docker Compose local deployment.
- Server deployment documentation.
- GitHub synchronization with staged commits.

Out of scope for the first version:

- Real-time streaming warehouse.
- Complex anti-crawler bypassing.
- Production-grade high availability cluster.
- User login, permissions, or admin system for the dashboard.

## Architecture

The data flow is:

```text
Crawler -> Local raw files -> HDFS -> Hive ODS/DWD/DIM/DWS/ADS
        -> Spark offline jobs -> MySQL ADS result tables
        -> FastAPI -> Vue + ECharts dashboard
```

The local deployment uses Docker Compose to manage the core services:

- `namenode`: HDFS NameNode.
- `datanode`: HDFS DataNode.
- `hive-metastore`: Hive metadata service.
- `hive-server2`: Hive SQL service.
- `spark-master`: Spark master service.
- `spark-worker`: Spark worker service.
- `mysql`: Hive metadata storage and ADS metric storage.
- `backend`: FastAPI service.
- `frontend`: Vue dashboard served by Nginx.

## Module Structure

```text
spark/
  README.md
  docker-compose.yml
  .gitignore

  crawler/
    spiders/
    pipelines/
    config/
    data/raw/

  warehouse/
    hdfs/
    hive/
      ods/
      dwd/
      dim/
      dws/
      ads/
    spark/
      jobs/
      submit/

  backend/
    app/
    requirements.txt
    Dockerfile

  frontend/
    src/
    public/
    package.json
    Dockerfile

  deploy/
    local/
    server/
    scripts/

  docs/
    architecture.md
    data-model.md
    warehouse-layers.md
    deployment.md
    github-workflow.md
```

## Data Model

The first version models a complete but manageable ecommerce operation domain.

Default crawler source:

- Use DummyJSON as the first data source because it provides stable ecommerce-like `products`, `carts`, and `users` JSON resources.
- The crawler should still be written as a configurable pipeline so another public API or static page can be added later without changing warehouse SQL.

Core entities:

- `product`: product ID, name, category, brand, price, shop, rating.
- `user`: user ID, gender, age group, region, registration time.
- `order`: order ID, user ID, product ID, quantity, amount, payment status, order time.
- `behavior`: page view, favorite, cart, order, payment events.
- `region`: province, city, region code.
- `category`: first-level and second-level categories.

## Warehouse Layers

- ODS: stores raw crawler data with minimal transformation.
- DWD: cleans and normalizes detailed fact data.
- DIM: stores reusable product, category, user, and region dimensions.
- DWS: aggregates by business subjects such as product, user behavior, order, and region.
- ADS: stores dashboard-ready indicators.

## Dashboard Metrics

The ADS layer supports a comprehensive ecommerce operations dashboard.

Core KPI metrics:

- Total sales amount.
- Total order count.
- Paid user count.
- Average order value.
- Payment conversion rate.

Trend metrics:

- 7-day and 30-day sales trend.
- Order count trend.
- Active user trend.

Product metrics:

- Top 10 hot-selling products.
- Category sales share.
- Price range distribution.

User metrics:

- User region distribution.
- Age group distribution.
- New vs returning user share.

Behavior metrics:

- Behavior funnel: view -> cart -> order -> payment.

Region metrics:

- Province sales ranking.
- City order distribution.

## API Design

FastAPI exposes dashboard-oriented endpoints:

- `GET /api/kpi`
- `GET /api/sales-trend`
- `GET /api/category-rank`
- `GET /api/product-rank`
- `GET /api/region-map`
- `GET /api/user-profile`
- `GET /api/funnel`

API responses should be shaped for ECharts consumption to keep frontend transformation minimal.

## Deployment Design

Local deployment uses Docker Compose and PowerShell scripts:

- `deploy/scripts/start.ps1`: start the environment.
- `deploy/scripts/stop.ps1`: stop the environment.
- `deploy/scripts/init-hdfs.ps1`: initialize HDFS directories.
- `deploy/scripts/run-crawler.ps1`: run crawler collection.
- `deploy/scripts/run-warehouse.ps1`: create Hive tables and run Spark jobs.
- `deploy/scripts/export-ads.ps1`: export ADS metrics to MySQL.
- `deploy/scripts/check.ps1`: check service health.

Server deployment documentation should explain:

- Required host resources.
- Port mapping.
- Environment variables.
- Data volume directories.
- Startup order.
- Common troubleshooting steps.

## GitHub Synchronization

The GitHub repository name is `ecommerce-spark-warehouse`.

Branch strategy:

- Use `main` as the main branch.
- Keep commits small and aligned with project stages.

Suggested staged commit history:

- `chore: initialize project structure`
- `feat: add crawler pipeline`
- `feat: add hive warehouse layers`
- `feat: add spark offline jobs`
- `feat: add fastapi dashboard api`
- `feat: add vue ecommerce dashboard`
- `docs: add deployment and warehouse documentation`
- `chore: verify docker compose deployment`

Before each commit:

- Run `git status`.
- Run the current stage verification command.
- Ensure secrets, logs, temporary data, local volumes, `.env`, and generated raw data are not staged.

## Acceptance Criteria

Environment:

- Docker Compose starts HDFS, Hive, Spark, MySQL, FastAPI, and frontend services.
- HDFS, Hive, Spark, MySQL, API, and dashboard are reachable.

Crawler:

- The crawler collects stable ecommerce data from a public API or static page.
- Raw JSON or CSV data is saved locally and uploaded to HDFS.

Warehouse:

- Hive creates ODS, DWD, DIM, DWS, and ADS tables successfully.
- SQL files are organized by warehouse layer.
- Field meanings, partitions, and metric definitions are documented.

Spark:

- Spark jobs read Hive tables and generate dashboard metrics.
- Sales, orders, users, products, regions, and behavior funnel metrics are computed.

Backend:

- FastAPI returns dashboard data through the planned API endpoints.
- API responses are documented and testable.

Frontend:

- Vue + ECharts displays KPI cards, trend charts, rankings, region distribution, and behavior funnel.
- Dashboard data is fetched from the FastAPI service.

Documentation:

- README explains the project background, tech stack, directory structure, deployment steps, running flow, GitHub workflow, and troubleshooting.
- Server deployment documentation is included after local deployment is verified.

GitHub:

- The local repository is initialized.
- The remote repository is connected as `ecommerce-spark-warehouse`.
- Stage-based commits are clear.
- The final verified version is pushed to GitHub.

## Risks and Mitigations

- Public ecommerce pages may change or block crawling. Use stable public APIs or static ecommerce-like pages for the first version.
- Docker-based big data services can consume significant memory. Keep the first version small and document minimum resource requirements.
- Hive/Spark integration may be sensitive to image versions. Pin Docker image versions once the stack is verified.
- Dashboard scope can grow quickly. Keep the first version focused on the listed ADS metrics.

## Open Decisions

- Exact Docker image versions will be pinned during environment implementation.
- The GitHub remote URL will be configured when repository access is confirmed in the implementation phase.


