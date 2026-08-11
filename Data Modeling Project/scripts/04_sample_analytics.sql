
SELECT
    d.year,
    d.quarter,
    SUM(f.sales_amount) AS total_sales,
    SUM(f.quantity) AS total_units,
    COUNT(DISTINCT f.order_number) AS order_count
FROM fact_sales f
JOIN dim_dates d ON f.order_date_key = d.date_key
GROUP BY d.year, d.quarter
ORDER BY d.year, d.quarter;

-- 2. Top 10 products by revenue
SELECT
    p.product_name,
    p.category,
    p.subcategory,
    SUM(f.sales_amount) AS revenue,
    SUM(f.quantity) AS units_sold
FROM fact_sales f
JOIN dim_products p ON f.product_sk = p.product_sk
GROUP BY p.product_name, p.category, p.subcategory
ORDER BY revenue DESC
LIMIT 10;

-- 3. Sales by country / region
SELECT
    g.country,
    g.region,
    SUM(f.sales_amount) AS total_sales,
    COUNT(DISTINCT f.customer_sk) AS unique_customers
FROM fact_sales f
JOIN dim_geography g ON f.geography_sk = g.geography_sk
GROUP BY g.country, g.region
ORDER BY total_sales DESC;

-- 4. Customer demographics overview
SELECT
    c.gender,
    c.marital_status,
    COUNT(*) AS customer_count,
    AVG(c.age) AS avg_age
FROM dim_customers c
GROUP BY c.gender, c.marital_status
ORDER BY customer_count DESC;

-- 5. Monthly sales trend
SELECT
    d.year,
    d.month,
    d.month_name,
    SUM(f.sales_amount) AS monthly_sales
FROM fact_sales f
JOIN dim_dates d ON f.order_date_key = d.date_key
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month;

-- 6. Average order value by product line
SELECT
    p.product_line,
    COUNT(DISTINCT f.order_number) AS orders,
    SUM(f.sales_amount) AS revenue,
    ROUND(SUM(f.sales_amount) * 1.0 / COUNT(DISTINCT f.order_number), 2) AS avg_order_value
FROM fact_sales f
JOIN dim_products p ON f.product_sk = p.product_sk
WHERE p.product_line IS NOT NULL
GROUP BY p.product_line
ORDER BY revenue DESC;
