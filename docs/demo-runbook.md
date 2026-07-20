# 演示运行手册

本文档用于本地演示 `ecommerce-spark-warehouse`，覆盖环境启动、全量跑批、结果验证、API 查看和大屏展示。

## 1. 演示目标

通过一次完整演示证明项目具备以下能力：

1. 通过爬虫获取电商数据。
2. 将数据导入 HDFS 和 Hive ODS。
3. 使用 Spark 完成 DWD、DIM、DWS、ADS 离线计算。
4. 将 ADS 结果导出到 MySQL。
5. 通过 FastAPI 提供 ADS 查询接口。
6. 通过 Vue/ECharts 大屏展示电商经营分析结果。

推荐演示批次日期：`2026-07-01`

## 2. 演示前准备

确认本机已安装：

- Docker Desktop
- Git
- Python
- Node.js
- PowerShell

如果本机网络需要代理，先设置代理环境变量。项目当前常用代理端口为 `7897`：

```powershell
$env:HTTP_PROXY='http://127.0.0.1:7897'
$env:HTTPS_PROXY='http://127.0.0.1:7897'
```

进入项目根目录：

```powershell
cd "D:\Codex Projects\spark"
```

## 3. 启动本地服务

启动完整 Docker Compose 环境：

```powershell
docker compose up -d --build
```

检查服务状态：

```powershell
docker compose ps
```

关键服务应包含：

```text
namenode
datanode
hive-metastore
hive-server2
spark-master
spark-worker
mysql
backend
frontend
```

## 4. 执行全量离线链路

执行一键全量跑批：

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_offline_batch.ps1 -BatchDate 2026-07-01
```

该命令会按顺序执行：

```text
crawler -> ods_check -> ods_ddl -> ods_load -> dwd -> ads -> mysql_export -> quality_check -> smoke_test
```

跑批成功后终端会输出：

```text
Offline batch completed for batch date 2026-07-01.
Summary: logs/offline-batch/2026-07-01/<run-id>/run-summary.json
```

## 5. 查看运行日志

每次跑批都会生成一个独立日志目录：

```text
logs/offline-batch/<batch-date>/<run-id>/
```

重点查看：

| 文件 | 作用 |
| --- | --- |
| `run-summary.json` | 全链路阶段状态 |
| `crawler.log` | 爬虫采集结果 |
| `dwd.log` | DWD Spark 明细处理日志 |
| `ads.log` | DIM/DWS/ADS Spark 计算日志 |
| `mysql_export.log` | ADS 导出 MySQL 日志 |
| `quality-report.json` | 数据质量检查结果 |
| `smoke_test.log` | API 和大屏冒烟测试结果 |

最近一次验收日志示例：

```text
logs/offline-batch/2026-07-01/20260720-190621/
```

## 6. 验证 API

健康检查：

```powershell
Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/health' -UseBasicParsing
```

查看 ADS 总览：

```powershell
Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/ads/overview?date=2026-07-01' -UseBasicParsing
```

验收时需要确认返回内容包含：

```text
kpi
trend
product_rank
category_share
user_profile
funnel
```

## 7. 查看大屏

浏览器打开：

```text
http://127.0.0.1:8088
```

演示时建议按以下顺序介绍：

1. 顶部说明数据日期和 API 数据状态。
2. KPI 卡片展示销售额、订单数、支付用户和支付转化率。
3. 品类销售占比展示 Top 6 品类和“其他”。
4. 商品销售排行展示 Top 商品销售表现。
5. 用户画像展示人群维度。
6. 转化漏斗展示 cart、order、payment 阶段。

## 8. 数据质量验证

数据质量检查由离线跑批自动执行，也可以单独运行：

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_quality_check.ps1 -BatchDate 2026-07-01
```

验收标准：

```text
status = passed
failed = 0
failed_critical = 0
```

最近一次验证结果：

```text
total_rules = 26
passed = 26
failed = 0
failed_critical = 0
```

## 9. 冒烟测试

严格验证 API 和大屏：

```powershell
powershell -ExecutionPolicy Bypass -File deploy/scripts/smoke_test.ps1 -BackendBaseUrl http://127.0.0.1:8000 -FrontendBaseUrl http://127.0.0.1:8088
```

如果还没有 ADS 数据，只想确认服务可访问，可以加上：

```powershell
-AllowMissingAds
```

## 10. 常见问题

### Docker 拉取镜像失败

如果网络需要代理，先设置：

```powershell
$env:HTTP_PROXY='http://127.0.0.1:7897'
$env:HTTPS_PROXY='http://127.0.0.1:7897'
```

再重新执行 Docker 或跑批命令。

### 某个阶段失败

先查看对应日志：

```text
logs/offline-batch/<batch-date>/<run-id>/<stage>.log
```

修复问题后可以从失败阶段继续，例如：

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_offline_batch.ps1 -BatchDate 2026-07-01 -StartFrom dwd
```

### 大屏显示 Mock 数据

大屏会在 API 不可用时显示 Mock 数据。验收真实链路时需要确认：

1. backend 服务健康。
2. ADS 数据已经导出到 MySQL。
3. `http://127.0.0.1:8000/api/ads/overview?date=2026-07-01` 可以返回真实数据。
4. 大屏顶部状态为 `API 数据`。

### 品类占比显示“其他”

这是大屏展示策略，不是数据缺失。ADS 接口保留完整品类明细，大屏为了避免标签重叠，将 Top 6 以后的品类合并为“其他”展示。

