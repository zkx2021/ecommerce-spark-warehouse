CREATE DATABASE IF NOT EXISTS ecommerce_ods;

USE ecommerce_ods;

CREATE EXTERNAL TABLE IF NOT EXISTS ods_products (
  entity STRING,
  source STRING,
  batch_date STRING,
  data STRING
)
PARTITIONED BY (dt STRING)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS TEXTFILE
LOCATION '/warehouse/ecommerce/ods/products';

CREATE EXTERNAL TABLE IF NOT EXISTS ods_carts (
  entity STRING,
  source STRING,
  batch_date STRING,
  data STRING
)
PARTITIONED BY (dt STRING)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS TEXTFILE
LOCATION '/warehouse/ecommerce/ods/carts';

CREATE EXTERNAL TABLE IF NOT EXISTS ods_users (
  entity STRING,
  source STRING,
  batch_date STRING,
  data STRING
)
PARTITIONED BY (dt STRING)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS TEXTFILE
LOCATION '/warehouse/ecommerce/ods/users';
