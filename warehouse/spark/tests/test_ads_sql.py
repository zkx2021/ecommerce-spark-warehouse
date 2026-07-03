from warehouse.spark.jobs import ads_sql


def test_render_all_sql_uses_batch_date_and_dependency_order():
    statements = ads_sql.render_all_sql("2026-07-01")

    names = [statement.name for statement in statements]
    assert names[0].startswith("dim_")
    assert names.index("dws_sales_daily") < names.index("ads_kpi_daily")
    assert names[-1] == "ads_funnel_daily"
    assert all("2026-07-01" in statement.sql for statement in statements)


def test_dws_sales_sql_deduplicates_cart_totals():
    statement = ads_sql.render_statement("dws_sales_daily", "2026-07-01").lower()

    assert "select distinct cart_id" in statement
    assert "sum(cart_discounted_total)" in statement
    assert "count(distinct user_id)" in statement


def test_ads_product_rank_uses_top_10_window():
    statement = ads_sql.render_statement("ads_product_rank_daily", "2026-07-01").lower()

    assert "row_number() over" in statement
    assert "order by sales_amount desc, sales_quantity desc" in statement
    assert "rank_no <= 10" in statement


def test_share_and_funnel_sql_guard_divide_by_zero():
    category_sql = ads_sql.render_statement("ads_category_share_daily", "2026-07-01").lower()
    funnel_sql = ads_sql.render_statement("ads_funnel_daily", "2026-07-01").lower()

    assert "case when total_sales_amount = 0 then 0" in category_sql
    assert "case when order_count = 0 then 0" in funnel_sql
