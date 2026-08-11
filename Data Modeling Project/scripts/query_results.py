import sqlite3
import pandas as pd
import os

# Always resolve DB path relative to this script's location
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "gold", "retail_dw.db")

conn = sqlite3.connect(DB_PATH)

print("=== Tables in Warehouse ===")
tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
print(tables.to_string(index=False))

print()
print("=== fact_sales (first 5 rows) ===")
df = pd.read_sql("SELECT * FROM fact_sales LIMIT 5", conn)
print(df.to_string(index=False))

print()
print("=== Top 5 Countries by Sales ===")
df2 = pd.read_sql("""
    SELECT g.country, ROUND(SUM(f.sales_amount),2) as total_sales, COUNT(*) as num_orders
    FROM fact_sales f
    JOIN dim_geography g ON f.geography_sk = g.geography_sk
    GROUP BY g.country
    ORDER BY total_sales DESC
    LIMIT 5
""", conn)
print(df2.to_string(index=False))

print()
print("=== Top 5 Products by Revenue ===")
df3 = pd.read_sql("""
    SELECT p.product_name, ROUND(SUM(f.sales_amount),2) as revenue
    FROM fact_sales f
    JOIN dim_products p ON f.product_sk = p.product_sk
    GROUP BY p.product_name
    ORDER BY revenue DESC
    LIMIT 5
""", conn)
print(df3.to_string(index=False))

print()
print("=== Record Counts ===")
for t in ["fact_sales", "dim_customers", "dim_products", "dim_dates", "dim_geography"]:
    cnt = pd.read_sql(f"SELECT COUNT(*) as cnt FROM {t}", conn).iloc[0, 0]
    print(f"  {t}: {cnt:,} rows")

conn.close()
print("\nDone! Your retail_dw.db warehouse is fully queryable.")
