# Hive Image

This image extends `apache/hive:4.0.0` with MySQL Connector/J 8.4.0 at `/opt/hive/lib/mysql-connector-j.jar`.

The connector is required by the external Hive metastore configuration in `docker-compose.yml`, which uses MySQL as the backing database for metastore state.

The Compose Hive services mount Hadoop configuration files into `/opt/hive/conf` so Hive can resolve warehouse paths against the Compose HDFS namespace, including `hdfs://namenode:8020/user/hive/warehouse`.
