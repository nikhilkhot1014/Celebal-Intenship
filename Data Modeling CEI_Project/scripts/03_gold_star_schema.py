
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
SILVER = BASE_DIR / "data" / "silver"
GOLD = BASE_DIR / "data" / "gold"

def ensure_dirs():
    GOLD.mkdir(parents=True, exist_ok=True)

def build_dim_dates(sales_df: pd.DataFrame) -> pd.DataFrame:
    """Generate a robust date dimension covering all order/ship/due dates."""
    dates = pd.concat([
        sales_df["order_date"].dropna(),
        sales_df["ship_date"].dropna(),
        sales_df["due_date"].dropna(),
    ])
    dates = dates[(dates >= "2000-01-01") & (dates <= "2030-12-31")]
    dates = dates.drop_duplicates().sort_values()

    if dates.empty:
        start = pd.Timestamp("2010-01-01")
        end = pd.Timestamp("2015-12-31")
    else:
        start = max(pd.Timestamp("2010-01-01"), dates.min().normalize() - pd.Timedelta(days=7))
        end = min(pd.Timestamp("2015-12-31"), dates.max().normalize() + pd.Timedelta(days=7))

    date_range = pd.date_range(start=start, end=end, freq="D")
    dim = pd.DataFrame({"full_date": date_range})
    dim["date_key"] = dim["full_date"].dt.strftime("%Y%m%d").astype(int)
    dim["year"] = dim["full_date"].dt.year
    dim["quarter"] = dim["full_date"].dt.quarter
    dim["month"] = dim["full_date"].dt.month
    dim["month_name"] = dim["full_date"].dt.month_name()
    dim["day"] = dim["full_date"].dt.day
    dim["day_of_week"] = dim["full_date"].dt.dayofweek + 1  # 1=Mon
    dim["day_name"] = dim["full_date"].dt.day_name()
    dim["week_of_year"] = dim["full_date"].dt.isocalendar().week.astype(int)
    dim["is_weekend"] = dim["day_of_week"].isin([6, 7])
    return dim

def run_gold():
    ensure_dirs()
    print("=" * 60)
    print("GOLD LAYER - Star Schema + Surrogate Keys")
    print("=" * 60)

    customers = pd.read_csv(
        SILVER / "silver_customers.csv",
        parse_dates=["create_date", "birthdate"]
    )
    products = pd.read_csv(
        SILVER / "silver_products.csv",
        parse_dates=["start_date", "end_date", "effective_from", "effective_to"]
    )
    sales = pd.read_csv(
        SILVER / "silver_sales.csv",
        parse_dates=["order_date", "ship_date", "due_date"]
    )

    # ---------- dim_customers ----------
    dim_cust = customers.copy().reset_index(drop=True)
    dim_cust.insert(0, "customer_sk", range(1, len(dim_cust) + 1))
    dim_cust = dim_cust.rename(columns={"customer_id": "customer_id_nk"})
    dim_cust["full_name"] = (
        dim_cust["first_name"].fillna("") + " " + dim_cust["last_name"].fillna("")
    ).str.strip()
    # Age relative to a fixed reference
    dim_cust["age"] = (
        (pd.Timestamp("2014-01-01") - dim_cust["birthdate"]).dt.days / 365.25
    ).round(0)
    print(f"[GOLD] dim_customers: {len(dim_cust)} rows")

    # ---------- dim_products ----------
    dim_prod = products.copy().reset_index(drop=True)
    dim_prod.insert(0, "product_sk", range(1, len(dim_prod) + 1))
    dim_prod = dim_prod.rename(columns={"product_id": "product_id_nk"})
    # Ensure short key exists for joining to sales
    if "product_key_short" not in dim_prod.columns:
        dim_prod["product_key_short"] = dim_prod["product_key"].str.replace(
            r"^[A-Z]{2}-[A-Z]{2}-", "", regex=True
        )
    print(f"[GOLD] dim_products: {len(dim_prod)} rows (includes SCD history)")

    # ---------- dim_geography ----------
    geo = (
        customers[["country"]]
        .drop_duplicates()
        .dropna()
        .query("country != 'n/a'")
        .reset_index(drop=True)
    )
    geo.insert(0, "geography_sk", range(1, len(geo) + 1))
    region_map = {
        "United States": "North America",
        "Canada": "North America",
        "Australia": "Oceania",
        "United Kingdom": "Europe",
        "Germany": "Europe",
        "France": "Europe",
    }
    geo["region"] = geo["country"].map(region_map).fillna("Other")
    print(f"[GOLD] dim_geography: {len(geo)} rows")

    # ---------- dim_dates ----------
    dim_dates = build_dim_dates(sales)
    print(f"[GOLD] dim_dates: {len(dim_dates)} rows")

    # ---------- fact_sales ----------
    # Customer map: business key customer_id_nk -> customer_sk
    cust_map = dim_cust.set_index("customer_id_nk")["customer_sk"].to_dict()

    # Product map: prefer current version, match on product_key_short
    if "is_current" in dim_prod.columns:
        prod_current = dim_prod[dim_prod["is_current"] == True]
        if prod_current.empty:
            prod_current = dim_prod
    else:
        prod_current = dim_prod

    prod_map = (
        prod_current
        .drop_duplicates(subset=["product_key_short"], keep="last")
        .set_index("product_key_short")["product_sk"]
        .to_dict()
    )
    # Fallback any version
    prod_map_all = (
        dim_prod
        .drop_duplicates(subset=["product_key_short"], keep="last")
        .set_index("product_key_short")["product_sk"]
        .to_dict()
    )
    prod_map = {**prod_map_all, **prod_map}

    geo_map = geo.set_index("country")["geography_sk"].to_dict()
    cust_country = dim_cust.set_index("customer_id_nk")["country"].to_dict()

    fact = sales.copy()
    fact["customer_sk"] = fact["customer_id"].map(cust_map)
    fact["product_sk"] = fact["product_key"].map(prod_map)
    fact["geography_sk"] = fact["customer_id"].map(cust_country).map(geo_map)

    # Date keys
    fact["order_date_key"] = fact["order_date"].dt.strftime("%Y%m%d").astype("Int64")
    fact["ship_date_key"] = fact["ship_date"].dt.strftime("%Y%m%d").astype("Int64")
    fact["due_date_key"] = fact["due_date"].dt.strftime("%Y%m%d").astype("Int64")

    fact = fact.reset_index(drop=True)
    fact.insert(0, "sales_sk", range(1, len(fact) + 1))

    fact["sales_amount"] = fact["sales_amount"].fillna(0)
    fact["quantity"] = fact["quantity"].fillna(0)
    fact["price"] = fact["price"].fillna(0)

    fact_final = fact[[
        "sales_sk",
        "order_number",
        "customer_sk",
        "product_sk",
        "geography_sk",
        "order_date_key",
        "ship_date_key",
        "due_date_key",
        "sales_amount",
        "quantity",
        "price",
    ]].copy()

    before = len(fact_final)
    fact_final = fact_final.dropna(subset=["customer_sk", "product_sk"])
    print(f"[GOLD] fact_sales: {len(fact_final)} rows (dropped {before - len(fact_final)} unresolved FKs)")

    # ---------- Write outputs ----------
    outputs = {
        "dim_customers.csv": dim_cust,
        "dim_products.csv": dim_prod,
        "dim_geography.csv": geo,
        "dim_dates.csv": dim_dates,
        "fact_sales.csv": fact_final,
    }
    for name, df in outputs.items():
        path = GOLD / name
        df.to_csv(path, index=False)
        print(f"[GOLD] Wrote {path.name} | rows={len(df)}")

    # SQLite warehouse (skip huge intermediate if needed)
    import sqlite3
    db_path = GOLD / "retail_dw.db"
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    dim_cust.to_sql("dim_customers", conn, if_exists="replace", index=False)
    dim_prod.to_sql("dim_products", conn, if_exists="replace", index=False)
    geo.to_sql("dim_geography", conn, if_exists="replace", index=False)
    dim_dates.to_sql("dim_dates", conn, if_exists="replace", index=False)
    fact_final.to_sql("fact_sales", conn, if_exists="replace", index=False)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_fact_cust ON fact_sales(customer_sk)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_fact_prod ON fact_sales(product_sk)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_fact_date ON fact_sales(order_date_key)")
    conn.close()
    print(f"[GOLD] SQLite warehouse written to {db_path}")

    print("[GOLD] Complete.\n")
    return outputs

if __name__ == "__main__":
    run_gold()
