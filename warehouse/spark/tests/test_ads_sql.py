from warehouse.spark.jobs import ads_sql


def test_render_all_sql_uses_batch_date_and_dependency_order():
    statements = ads_sql.render_all_sql("2026-07-01")

    names = [statement.name for statement in statements]
    assert set(ads_sql.STATEMENT_ORDER) == set(ads_sql.SQL_TEMPLATES)
    assert len(ads_sql.STATEMENT_ORDER) == 15
    assert len(ads_sql.SQL_TEMPLATES) == 15
    assert names == list(ads_sql.STATEMENT_ORDER)
    first_dws_index = next(index for index, name in enumerate(names) if name.startswith("dws_"))
    first_ads_index = next(index for index, name in enumerate(names) if name.startswith("ads_"))
    assert all(name.startswith("dim_") for name in names[:first_dws_index])
    assert all(name.startswith("dws_") for name in names[first_dws_index:first_ads_index])
    assert all(name.startswith("ads_") for name in names[first_ads_index:])
    assert names[-1] == "ads_funnel_daily"
    assert all("2026-07-01" in statement.sql for statement in statements)


def test_dim_date_uses_dashed_batch_date_id():
    statement = ads_sql.render_statement("dim_date", "2026-07-01").lower()

    assert "'2026-07-01' as date_id" in statement
    assert "regexp_replace('{batch_date}', '-', '') as date_id" not in statement
    assert "regexp_replace('2026-07-01', '-', '') as date_id" not in statement


def test_dws_sales_sql_deduplicates_cart_totals():
    statement = ads_sql.render_statement("dws_sales_daily", "2026-07-01").lower()

    assert "select distinct cart_id" in statement
    assert "sum(cart_discounted_total)" in statement
    assert "count(distinct user_id)" in statement


def test_dws_sales_sql_coalesces_empty_batch_aggregates():
    statement = ads_sql.render_statement("dws_sales_daily", "2026-07-01").lower()

    assert "cast(coalesce(sum(cart_total), 0) as decimal(18,2)) as total_sales_amount" in statement
    assert (
        "cast(coalesce(sum(cart_discounted_total), 0) as decimal(18,2)) as discount_sales_amount"
        in statement
    )
    assert "else coalesce(sum(cart_discounted_total), 0) / count(distinct cart_id)" in statement
    assert "coalesce(sum(total_quantity), 0) as total_quantity" in statement


def test_dimension_sql_normalizes_blank_categories():
    product_sql = ads_sql.render_statement("dim_product", "2026-07-01").lower()
    category_sql = ads_sql.render_statement("dim_category", "2026-07-01").lower()
    normalized_category = "coalesce(nullif(trim(category), ''), 'unknown')"

    assert f"{normalized_category} as category" in product_sql
    assert normalized_category in category_sql
    assert "lower(regexp_replace(category, '[^a-za-z0-9]+', '_')) as category_id" in category_sql
    assert "category as category_name" in category_sql
    assert "group by category" in category_sql


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
