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
