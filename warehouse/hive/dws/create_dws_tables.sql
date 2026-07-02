CREATE DATABASE IF NOT EXISTS ecommerce_dws;

USE ecommerce_dws;

CREATE EXTERNAL TABLE IF NOT EXISTS dws_sales_daily (
  date_id STRING,
  order_count BIGINT,
  pay_user_count BIGINT,
  total_sales_amount DECIMAL(18,2),
  discount_sales_amount DECIMAL(18,2),
  avg_order_amount DECIMAL(18,2),
  total_quantity BIGINT
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION '/warehouse/ecommerce/dws/sales_daily';

CREATE EXTERNAL TABLE IF NOT EXISTS dws_product_daily (
  date_id STRING,
  product_id BIGINT,
  product_name STRING,
  category STRING,
  brand STRING,
  sales_quantity BIGINT,
  sales_amount DECIMAL(18,2),
  order_count BIGINT
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION '/warehouse/ecommerce/dws/product_daily';

CREATE EXTERNAL TABLE IF NOT EXISTS dws_category_daily (
  date_id STRING,
  category STRING,
  product_count BIGINT,
  sales_quantity BIGINT,
  sales_amount DECIMAL(18,2),
  order_count BIGINT
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION '/warehouse/ecommerce/dws/category_daily';

CREATE EXTERNAL TABLE IF NOT EXISTS dws_user_profile_daily (
  date_id STRING,
  age_group STRING,
  gender STRING,
  country STRING,
  user_count BIGINT,
  buyer_count BIGINT,
  order_count BIGINT,
  sales_amount DECIMAL(18,2)
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION '/warehouse/ecommerce/dws/user_profile_daily';

CREATE EXTERNAL TABLE IF NOT EXISTS dws_funnel_daily (
  date_id STRING,
  view_count BIGINT,
  cart_count BIGINT,
  order_count BIGINT,
  payment_count BIGINT,
  cart_rate DECIMAL(10,4),
  order_rate DECIMAL(10,4),
  payment_rate DECIMAL(10,4)
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION '/warehouse/ecommerce/dws/funnel_daily';
