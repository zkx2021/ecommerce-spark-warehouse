CREATE DATABASE IF NOT EXISTS ecommerce_ads;

USE ecommerce_ads;

CREATE EXTERNAL TABLE IF NOT EXISTS ads_kpi_daily (
  date_id STRING,
  total_sales_amount DECIMAL(18,2),
  total_order_count BIGINT,
  paid_user_count BIGINT,
  avg_order_amount DECIMAL(18,2),
  payment_conversion_rate DECIMAL(10,4)
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION '/warehouse/ecommerce/ads/kpi_daily';

CREATE EXTERNAL TABLE IF NOT EXISTS ads_sales_trend_daily (
  date_id STRING,
  sales_amount DECIMAL(18,2),
  order_count BIGINT,
  paid_user_count BIGINT
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION '/warehouse/ecommerce/ads/sales_trend_daily';

CREATE EXTERNAL TABLE IF NOT EXISTS ads_product_rank_daily (
  date_id STRING,
  rank_no INT,
  product_id BIGINT,
  product_name STRING,
  category STRING,
  sales_quantity BIGINT,
  sales_amount DECIMAL(18,2)
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION '/warehouse/ecommerce/ads/product_rank_daily';

CREATE EXTERNAL TABLE IF NOT EXISTS ads_category_share_daily (
  date_id STRING,
  category STRING,
  sales_amount DECIMAL(18,2),
  sales_quantity BIGINT,
  sales_share DECIMAL(10,4)
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION '/warehouse/ecommerce/ads/category_share_daily';

CREATE EXTERNAL TABLE IF NOT EXISTS ads_user_profile_daily (
  date_id STRING,
  dimension_type STRING,
  dimension_value STRING,
  user_count BIGINT,
  buyer_count BIGINT,
  sales_amount DECIMAL(18,2)
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION '/warehouse/ecommerce/ads/user_profile_daily';

CREATE EXTERNAL TABLE IF NOT EXISTS ads_funnel_daily (
  date_id STRING,
  stage_name STRING,
  stage_order INT,
  stage_count BIGINT,
  conversion_rate DECIMAL(10,4)
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION '/warehouse/ecommerce/ads/funnel_daily';
