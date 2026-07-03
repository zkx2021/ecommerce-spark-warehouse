from dataclasses import dataclass


@dataclass(frozen=True)
class SqlStatement:
    name: str
    sql: str


STATEMENT_ORDER = (
    "dim_date",
    "dim_product",
    "dim_category",
    "dim_user",
    "dws_sales_daily",
    "dws_product_daily",
    "dws_category_daily",
    "dws_user_profile_daily",
    "dws_funnel_daily",
    "ads_kpi_daily",
    "ads_sales_trend_daily",
    "ads_product_rank_daily",
    "ads_category_share_daily",
    "ads_user_profile_daily",
    "ads_funnel_daily",
)


SQL_TEMPLATES: dict[str, str] = {
    "dim_date": """
INSERT OVERWRITE TABLE ecommerce_dim.dim_date PARTITION (dt='{batch_date}')
SELECT
    '{batch_date}' AS date_id,
    to_date('{batch_date}') AS date_value,
    year(to_date('{batch_date}')) AS year,
    quarter(to_date('{batch_date}')) AS quarter,
    month(to_date('{batch_date}')) AS month,
    dayofmonth(to_date('{batch_date}')) AS day,
    weekofyear(to_date('{batch_date}')) AS week_of_year,
    dayofweek(to_date('{batch_date}')) AS day_of_week,
    CASE WHEN dayofweek(to_date('{batch_date}')) IN (1, 7) THEN true ELSE false END AS is_weekend
""",
    "dim_product": """
INSERT OVERWRITE TABLE ecommerce_dim.dim_product PARTITION (dt='{batch_date}')
SELECT
    product_id,
    product_name,
    COALESCE(NULLIF(trim(category), ''), 'unknown') AS category,
    brand,
    CAST(price AS DECIMAL(18,2)) AS price,
    stock,
    availability_status
FROM ecommerce_dwd.dwd_product_info
WHERE dt = '{batch_date}'
""",
    "dim_category": """
INSERT OVERWRITE TABLE ecommerce_dim.dim_category PARTITION (dt='{batch_date}')
SELECT
    lower(regexp_replace(category, '[^a-zA-Z0-9]+', '_')) AS category_id,
    category AS category_name,
    COUNT(DISTINCT product_id) AS product_count
FROM (
    SELECT
        product_id,
        COALESCE(NULLIF(trim(category), ''), 'unknown') AS category
    FROM ecommerce_dwd.dwd_product_info
    WHERE dt = '{batch_date}'
) normalized_products
GROUP BY category
""",
    "dim_user": """
INSERT OVERWRITE TABLE ecommerce_dim.dim_user PARTITION (dt='{batch_date}')
SELECT
    user_id,
    username,
    gender,
    age,
    age_group,
    city,
    state,
    country,
    role
FROM ecommerce_dwd.dwd_user_info
WHERE dt = '{batch_date}'
""",
    "dws_sales_daily": """
INSERT OVERWRITE TABLE ecommerce_dws.dws_sales_daily PARTITION (dt='{batch_date}')
SELECT
    '{batch_date}' AS date_id,
    COUNT(DISTINCT cart_id) AS order_count,
    COUNT(DISTINCT user_id) AS pay_user_count,
    CAST(COALESCE(SUM(cart_total), 0) AS DECIMAL(18,2)) AS total_sales_amount,
    CAST(COALESCE(SUM(cart_discounted_total), 0) AS DECIMAL(18,2)) AS discount_sales_amount,
    CAST(
        CASE WHEN COUNT(DISTINCT cart_id) = 0 THEN 0
             ELSE COALESCE(SUM(cart_discounted_total), 0) / COUNT(DISTINCT cart_id)
        END AS DECIMAL(18,2)
    ) AS avg_order_amount,
    COALESCE(SUM(total_quantity), 0) AS total_quantity
FROM (
    SELECT DISTINCT cart_id, user_id, cart_total, cart_discounted_total, total_quantity
    FROM ecommerce_dwd.dwd_order_cart_detail
    WHERE dt = '{batch_date}'
) cart_totals
""",
    "dws_product_daily": """
INSERT OVERWRITE TABLE ecommerce_dws.dws_product_daily PARTITION (dt='{batch_date}')
SELECT
    '{batch_date}' AS date_id,
    detail.product_id,
    COALESCE(product.product_name, detail.product_name) AS product_name,
    product.category,
    product.brand,
    SUM(detail.quantity) AS sales_quantity,
    CAST(SUM(detail.line_discounted_total) AS DECIMAL(18,2)) AS sales_amount,
    COUNT(DISTINCT detail.cart_id) AS order_count
FROM ecommerce_dwd.dwd_order_cart_detail detail
LEFT JOIN ecommerce_dim.dim_product product
    ON detail.product_id = product.product_id
   AND product.dt = '{batch_date}'
WHERE detail.dt = '{batch_date}'
GROUP BY detail.product_id, COALESCE(product.product_name, detail.product_name), product.category, product.brand
""",
    "dws_category_daily": """
INSERT OVERWRITE TABLE ecommerce_dws.dws_category_daily PARTITION (dt='{batch_date}')
SELECT
    '{batch_date}' AS date_id,
    product_daily.category,
    MAX(category.product_count) AS product_count,
    SUM(product_daily.sales_quantity) AS sales_quantity,
    CAST(SUM(product_daily.sales_amount) AS DECIMAL(18,2)) AS sales_amount,
    SUM(product_daily.order_count) AS order_count
FROM ecommerce_dws.dws_product_daily product_daily
LEFT JOIN ecommerce_dim.dim_category category
    ON product_daily.category = category.category_name
   AND category.dt = '{batch_date}'
WHERE product_daily.dt = '{batch_date}'
GROUP BY product_daily.category
""",
    "dws_user_profile_daily": """
INSERT OVERWRITE TABLE ecommerce_dws.dws_user_profile_daily PARTITION (dt='{batch_date}')
SELECT
    '{batch_date}' AS date_id,
    user_dim.age_group,
    user_dim.gender,
    user_dim.country,
    COUNT(DISTINCT user_dim.user_id) AS user_count,
    COUNT(DISTINCT cart_totals.user_id) AS buyer_count,
    COUNT(DISTINCT cart_totals.cart_id) AS order_count,
    CAST(COALESCE(SUM(cart_totals.cart_discounted_total), 0) AS DECIMAL(18,2)) AS sales_amount
FROM ecommerce_dim.dim_user user_dim
LEFT JOIN (
    SELECT DISTINCT cart_id, user_id, cart_discounted_total
    FROM ecommerce_dwd.dwd_order_cart_detail
    WHERE dt = '{batch_date}'
) cart_totals
    ON user_dim.user_id = cart_totals.user_id
WHERE user_dim.dt = '{batch_date}'
GROUP BY user_dim.age_group, user_dim.gender, user_dim.country
""",
    "dws_funnel_daily": """
INSERT OVERWRITE TABLE ecommerce_dws.dws_funnel_daily PARTITION (dt='{batch_date}')
SELECT
    '{batch_date}' AS date_id,
    0 AS view_count,
    metrics.cart_count,
    metrics.order_count,
    metrics.payment_count,
    CAST(0 AS DECIMAL(10,4)) AS cart_rate,
    CAST(CASE WHEN metrics.cart_count = 0 THEN 0 ELSE metrics.order_count / metrics.cart_count END AS DECIMAL(10,4)) AS order_rate,
    CAST(CASE WHEN metrics.order_count = 0 THEN 0 ELSE metrics.payment_count / metrics.order_count END AS DECIMAL(10,4)) AS payment_rate
FROM (
    SELECT
        COUNT(DISTINCT cart_id) AS cart_count,
        COUNT(DISTINCT cart_id) AS order_count,
        COUNT(DISTINCT cart_id) AS payment_count
    FROM ecommerce_dwd.dwd_order_cart_detail
    WHERE dt = '{batch_date}'
) metrics
""",
    "ads_kpi_daily": """
INSERT OVERWRITE TABLE ecommerce_ads.ads_kpi_daily PARTITION (dt='{batch_date}')
SELECT
    sales.date_id,
    sales.total_sales_amount,
    sales.order_count AS total_order_count,
    sales.pay_user_count AS paid_user_count,
    sales.avg_order_amount,
    funnel.payment_rate AS payment_conversion_rate
FROM ecommerce_dws.dws_sales_daily sales
LEFT JOIN ecommerce_dws.dws_funnel_daily funnel
    ON sales.date_id = funnel.date_id
   AND funnel.dt = '{batch_date}'
WHERE sales.dt = '{batch_date}'
""",
    "ads_sales_trend_daily": """
INSERT OVERWRITE TABLE ecommerce_ads.ads_sales_trend_daily PARTITION (dt='{batch_date}')
SELECT
    date_id,
    total_sales_amount AS sales_amount,
    order_count,
    pay_user_count AS paid_user_count
FROM ecommerce_dws.dws_sales_daily
WHERE dt = '{batch_date}'
""",
    "ads_product_rank_daily": """
INSERT OVERWRITE TABLE ecommerce_ads.ads_product_rank_daily PARTITION (dt='{batch_date}')
SELECT
    date_id,
    rank_no,
    product_id,
    product_name,
    category,
    sales_quantity,
    sales_amount
FROM (
    SELECT
        date_id,
        product_id,
        product_name,
        category,
        sales_quantity,
        sales_amount,
        ROW_NUMBER() OVER (ORDER BY sales_amount DESC, sales_quantity DESC) AS rank_no
    FROM ecommerce_dws.dws_product_daily
    WHERE dt = '{batch_date}'
) ranked
WHERE rank_no <= 10
""",
    "ads_category_share_daily": """
INSERT OVERWRITE TABLE ecommerce_ads.ads_category_share_daily PARTITION (dt='{batch_date}')
SELECT
    category_sales.date_id,
    category_sales.category,
    category_sales.sales_amount,
    category_sales.sales_quantity,
    CAST(
        CASE WHEN total_sales_amount = 0 THEN 0
             ELSE category_sales.sales_amount / total_sales_amount
        END AS DECIMAL(10,4)
    ) AS sales_share
FROM ecommerce_dws.dws_category_daily category_sales
CROSS JOIN (
    SELECT COALESCE(SUM(sales_amount), 0) AS total_sales_amount
    FROM ecommerce_dws.dws_category_daily
    WHERE dt = '{batch_date}'
) totals
WHERE category_sales.dt = '{batch_date}'
""",
    "ads_user_profile_daily": """
INSERT OVERWRITE TABLE ecommerce_ads.ads_user_profile_daily PARTITION (dt='{batch_date}')
SELECT
    date_id,
    'age_group' AS dimension_type,
    age_group AS dimension_value,
    SUM(user_count) AS user_count,
    SUM(buyer_count) AS buyer_count,
    CAST(SUM(sales_amount) AS DECIMAL(18,2)) AS sales_amount
FROM ecommerce_dws.dws_user_profile_daily
WHERE dt = '{batch_date}'
GROUP BY date_id, age_group
UNION ALL
SELECT
    date_id,
    'gender' AS dimension_type,
    gender AS dimension_value,
    SUM(user_count) AS user_count,
    SUM(buyer_count) AS buyer_count,
    CAST(SUM(sales_amount) AS DECIMAL(18,2)) AS sales_amount
FROM ecommerce_dws.dws_user_profile_daily
WHERE dt = '{batch_date}'
GROUP BY date_id, gender
UNION ALL
SELECT
    date_id,
    'country' AS dimension_type,
    country AS dimension_value,
    SUM(user_count) AS user_count,
    SUM(buyer_count) AS buyer_count,
    CAST(SUM(sales_amount) AS DECIMAL(18,2)) AS sales_amount
FROM ecommerce_dws.dws_user_profile_daily
WHERE dt = '{batch_date}'
GROUP BY date_id, country
""",
    "ads_funnel_daily": """
INSERT OVERWRITE TABLE ecommerce_ads.ads_funnel_daily PARTITION (dt='{batch_date}')
SELECT
    date_id,
    'cart' AS stage_name,
    1 AS stage_order,
    cart_count AS stage_count,
    CAST(CASE WHEN view_count = 0 OR view_count IS NULL THEN 0 ELSE cart_count / view_count END AS DECIMAL(10,4)) AS conversion_rate
FROM ecommerce_dws.dws_funnel_daily
WHERE dt = '{batch_date}'
UNION ALL
SELECT
    date_id,
    'order' AS stage_name,
    2 AS stage_order,
    order_count AS stage_count,
    CAST(CASE WHEN cart_count = 0 THEN 0 ELSE order_count / cart_count END AS DECIMAL(10,4)) AS conversion_rate
FROM ecommerce_dws.dws_funnel_daily
WHERE dt = '{batch_date}'
UNION ALL
SELECT
    date_id,
    'payment' AS stage_name,
    3 AS stage_order,
    payment_count AS stage_count,
    CAST(CASE WHEN order_count = 0 THEN 0 ELSE payment_count / order_count END AS DECIMAL(10,4)) AS conversion_rate
FROM ecommerce_dws.dws_funnel_daily
WHERE dt = '{batch_date}'
""",
}


def render_statement(name: str, batch_date: str) -> str:
    return SQL_TEMPLATES[name].format(batch_date=batch_date)


def render_all_sql(batch_date: str) -> list[SqlStatement]:
    return [SqlStatement(name=name, sql=render_statement(name, batch_date)) for name in STATEMENT_ORDER]
