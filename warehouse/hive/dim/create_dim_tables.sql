CREATE DATABASE IF NOT EXISTS ecommerce_dim;

USE ecommerce_dim;

CREATE EXTERNAL TABLE IF NOT EXISTS dim_date (
  date_id STRING,
  date_value DATE,
  year INT,
  quarter INT,
  month INT,
  day INT,
  week_of_year INT,
  day_of_week INT,
  is_weekend BOOLEAN
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION '/warehouse/ecommerce/dim/date';

CREATE EXTERNAL TABLE IF NOT EXISTS dim_product (
  product_id BIGINT,
  product_name STRING,
  category STRING,
  brand STRING,
  price DECIMAL(18,2),
  stock INT,
  availability_status STRING
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION '/warehouse/ecommerce/dim/product';

CREATE EXTERNAL TABLE IF NOT EXISTS dim_category (
  category_id STRING,
  category_name STRING,
  product_count BIGINT
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION '/warehouse/ecommerce/dim/category';

CREATE EXTERNAL TABLE IF NOT EXISTS dim_user (
  user_id BIGINT,
  username STRING,
  gender STRING,
  age INT,
  age_group STRING,
  city STRING,
  state STRING,
  country STRING,
  role STRING
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION '/warehouse/ecommerce/dim/user';
