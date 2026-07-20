# 项目验收说明

本文档用于课程设计、毕设答辩或项目交付时说明 `ecommerce-spark-warehouse` 的验收范围、功能清单、运行证据和通过标准。

## 1. 项目定位

本项目是一个面向电商经营分析的离线大数据数仓项目。系统通过爬虫采集电商商品、购物车订单和用户数据，将原始数据写入 HDFS，并基于 Hive 和 Spark SQL 构建 ODS、DWD、DIM、DWS、ADS 多层数据仓库。最终 ADS 指标导出到 MySQL，由 FastAPI 提供接口，并通过 Vue/ECharts 大屏展示经营分析结果。

核心链路如下：

```text
Crawler -> Local raw/processed files -> HDFS -> Hive ODS
        -> Spark DWD -> Spark DIM/DWS/ADS -> MySQL ADS
        -> FastAPI ADS API -> Vue/ECharts dashboard
```

## 2. 技术栈验收

| 模块 | 技术 | 验收说明 |
| --- | --- | --- |
| 数据采集 | Python crawler | 从公开电商数据接口采集商品、购物车和用户数据 |
| 分布式存储 | HDFS | ODS 数据按批次日期写入 HDFS 分区目录 |
| 数据仓库 | Hive | 建立 ODS、DWD、DIM、DWS、ADS 多层 Hive 表 |
| 离线计算 | Spark SQL / PySpark | 执行明细清洗、维表、汇总层和应用层指标计算 |
| 指标服务 | MySQL + FastAPI | ADS 结果导出到 MySQL，并由 API 对外提供 |
| 可视化 | Vue 3 + ECharts | 展示 KPI、趋势、商品排行、品类占比、用户画像和转化漏斗 |
| 部署 | Docker Compose | 本地一键启动 Hadoop、Hive、Spark、MySQL、API 和大屏服务 |

## 3. 数据来源

爬虫配置文件：`crawler/config/sources.json`

当前数据源：

| 数据集 | URL | 说明 |
| --- | --- | --- |
| products | `https://dummyjson.com/products?limit=200` | 商品基础信息，包含商品名称、类目、价格等 |
| carts | `https://dummyjson.com/carts` | 购物车和订单明细，用于销售指标计算 |
| users | `https://dummyjson.com/users` | 用户基础信息，用于用户画像分析 |

批次数据会落到：

```text
crawler/data/raw/<batch-date>/
crawler/data/processed/<batch-date>/
```

## 4. 数仓分层验收

| 层级 | 目录 | 作用 |
| --- | --- | --- |
| ODS | `warehouse/hive/ods` | 原始数据层，按来源贴源建表 |
| DWD | `warehouse/hive/dwd` | 明细数据层，清洗商品、用户、购物车订单明细 |
| DIM | `warehouse/hive/dim` | 公共维度层，沉淀商品、类目、用户、日期等维度 |
| DWS | `warehouse/hive/dws` | 汇总服务层，形成面向主题的日汇总数据 |
| ADS | `warehouse/hive/ads` | 应用数据层，产出大屏直接使用的指标 |
| MySQL ADS | `deploy/mysql/init/02-create-ads-tables.sql` | 存储 API 查询所需的 ADS 结果表 |

## 5. 指标与大屏验收

大屏地址：`http://127.0.0.1:8088`

API 地址：`http://127.0.0.1:8000/api/ads/overview?date=2026-07-01`

验收指标：

| 模块 | 指标 |
| --- | --- |
| KPI 卡片 | 销售额、订单数、支付用户、支付转化率 |
| 销售趋势 | 销售额、订单数、支付用户 |
| 商品销售排行 | Top 商品、销售额、销量 |
| 品类销售占比 | Top 6 品类 + 其他，按销售额占比展示 |
| 用户画像 | 年龄段、国家、性别维度的访问和购买用户 |
| 转化漏斗 | cart、order、payment 阶段转化 |

## 6. 最终验证记录

最近一次全量验证：

| 项目 | 结果 |
| --- | --- |
| 批次日期 | `2026-07-01` |
| 运行 ID | `20260720-190621` |
| 运行状态 | `success` |
| 运行摘要 | `logs/offline-batch/2026-07-01/20260720-190621/run-summary.json` |
| 质量报告 | `logs/offline-batch/2026-07-01/20260720-190621/quality-report.json` |

全量链路阶段结果：

```text
crawler -> success
ods_check -> success
ods_ddl -> success
ods_load -> success
dwd -> success
ads -> success
mysql_export -> success
quality_check -> success
smoke_test -> success
```

关键数据结果：

| 指标 | 数值 |
| --- | --- |
| 商品数据 | 194 条 |
| 购物车数据 | 30 条 |
| 用户数据 | 30 条 |
| ADS 销售额 | 725,678.95 |
| ADS 订单数 | 30 |
| ADS 支付用户 | 30 |
| ADS 支付转化率 | 100.0% |
| 数据质量规则 | 26 条全部通过 |

## 7. 验收通过标准

项目验收时建议按以下标准确认：

1. `docker compose ps` 显示 Hadoop、Hive、Spark、MySQL、backend、frontend 关键服务正在运行。
2. `warehouse/scripts/run_offline_batch.ps1` 可以从 `crawler` 开始完整跑通。
3. `run-summary.json` 中所有阶段状态均为 `success`。
4. `quality-report.json` 中 `failed` 和 `failed_critical` 均为 `0`。
5. FastAPI ADS 接口可以返回指定日期的 KPI、趋势、排行、品类、画像和漏斗数据。
6. Vue/ECharts 大屏可以正常访问，并显示真实 API 数据状态。
7. 项目基础检查 `deploy/scripts/check.ps1` 可以通过。

## 8. 交付物清单

| 交付物 | 路径 |
| --- | --- |
| 项目总览 | `README.md` |
| 部署集成说明 | `docs/deployment-integration.md` |
| 演示运行手册 | `docs/demo-runbook.md` |
| GitHub 工作流 | `docs/github-workflow.md` |
| 爬虫模块 | `crawler/` |
| 数仓模块 | `warehouse/` |
| 后端 API | `backend/` |
| 前端大屏 | `frontend/` |
| 本地部署 | `docker-compose.yml`、`deploy/` |

