CREATE DATABASE IF NOT EXISTS ecommerce_ads CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS hive_metastore CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

GRANT ALL PRIVILEGES ON ecommerce_ads.* TO 'ecommerce'@'%';
GRANT ALL PRIVILEGES ON hive_metastore.* TO 'ecommerce'@'%';

FLUSH PRIVILEGES;
