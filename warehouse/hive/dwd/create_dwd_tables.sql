CREATE DATABASE IF NOT EXISTS ecommerce_dwd;

USE ecommerce_dwd;

CREATE EXTERNAL TABLE IF NOT EXISTS dwd_product_info (
  product_id BIGINT,
  product_name STRING,
  category STRING,
  brand STRING,
  price DECIMAL(18,2),
  discount_percentage DECIMAL(10,2),
  rating DECIMAL(10,2),
  stock INT,
  availability_status STRING,
  thumbnail STRING,
  source STRING,
  batch_date STRING
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION '/warehouse/ecommerce/dwd/product_info';

CREATE EXTERNAL TABLE IF NOT EXISTS dwd_user_info (
  user_id BIGINT,
  username STRING,
  full_name STRING,
  gender STRING,
  age INT,
  age_group STRING,
  email STRING,
  phone STRING,
  city STRING,
  state STRING,
  country STRING,
  latitude DECIMAL(18,6),
  longitude DECIMAL(18,6),
  role STRING,
  source STRING,
  batch_date STRING
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION '/warehouse/ecommerce/dwd/user_info';

CREATE EXTERNAL TABLE IF NOT EXISTS dwd_order_cart_detail (
  cart_id BIGINT,
  user_id BIGINT,
  product_id BIGINT,
  product_name STRING,
  unit_price DECIMAL(18,2),
  quantity INT,
  line_total DECIMAL(18,2),
  discount_percentage DECIMAL(10,2),
  line_discounted_total DECIMAL(18,2),
  cart_total DECIMAL(18,2),
  cart_discounted_total DECIMAL(18,2),
  total_products INT,
  total_quantity INT,
  source STRING,
  batch_date STRING
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION '/warehouse/ecommerce/dwd/order_cart_detail';
