
import re
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
BRONZE = BASE_DIR / "data" / "bronze"
SILVER = BASE_DIR / "data" / "silver"

def ensure_dirs():
    SILVER.mkdir(parents=True, exist_ok=True)

# ---------- Helpers ----------
def clean_string(s):
    if pd.isna(s):
        return None
    return str(s).strip()

def standardize_gender(val):
    if pd.isna(val) or str(val).strip() == "":
        return "n/a"
    v = str(val).strip().upper()
    if v in ("M", "MALE"):
        return "Male"
    if v in ("F", "FEMALE"):
        return "Female"
    return "n/a"

def standardize_marital(val):
    if pd.isna(val) or str(val).strip() == "":
        return "n/a"
    v = str(val).strip().upper()
    if v in ("M", "MARRIED"):
        return "Married"
    if v in ("S", "SINGLE"):
        return "Single"
    return "n/a"

def standardize_country(val):
    if pd.isna(val) or str(val).strip() == "":
        return "n/a"
    v = str(val).strip()
    mapping = {
        "US": "United States",
        "USA": "United States",
        "United States": "United States",
        "DE": "Germany",
        "Germany": "Germany",
        "UK": "United Kingdom",
        "United Kingdom": "United Kingdom",
        "AU": "Australia",
        "Australia": "Australia",
        "CA": "Canada",
        "Canada": "Canada",
        "FR": "France",
        "France": "France",
    }
    return mapping.get(v, v.title() if v else "n/a")

def parse_date(val):
    """Handle various date formats including YYYYMMDD integers.
    Rejects unrealistic years outside 1990-2030.
    """
    if pd.isna(val) or str(val).strip() in ("", "0", "None", "nan"):
        return pd.NaT
    s = str(val).strip()
    # Only accept pure 8-digit YYYYMMDD
    if re.fullmatch(r"\d{8}", s):
        try:
            dt = pd.to_datetime(s, format="%Y%m%d")
            if 1990 <= dt.year <= 2030:
                return dt
            return pd.NaT
        except Exception:
            return pd.NaT
    # Fallback for ISO-like strings
    try:
        dt = pd.to_datetime(s)
        if 1990 <= dt.year <= 2030:
            return dt
        return pd.NaT
    except Exception:
        return pd.NaT

# ---------- CRM Customers ----------
def process_crm_customers():
    df = pd.read_csv(BRONZE / "crm_cust_info.csv")
    print(f"[SILVER] CRM customers raw: {len(df)} rows")

    # Clean strings
    for col in ["cst_firstname", "cst_lastname", "cst_key"]:
        df[col] = df[col].apply(clean_string)

    df["cst_gndr"] = df["cst_gndr"].apply(standardize_gender)
    df["cst_marital_status"] = df["cst_marital_status"].apply(standardize_marital)
    df["cst_create_date"] = pd.to_datetime(df["cst_create_date"], errors="coerce")

    # Deduplicate: keep latest by create_date for same cst_id
    df = df.sort_values("cst_create_date", ascending=False)
    before = len(df)
    df = df.drop_duplicates(subset=["cst_id"], keep="first")
    print(f"[SILVER] CRM customers after dedup: {len(df)} (removed {before - len(df)})")

    df = df.rename(columns={
        "cst_id": "customer_id",
        "cst_key": "customer_key",
        "cst_firstname": "first_name",
        "cst_lastname": "last_name",
        "cst_marital_status": "marital_status",
        "cst_gndr": "gender",
        "cst_create_date": "create_date",
    })
    return df

# ---------- ERP Customer (BDATE + GEN) ----------
def process_erp_customer():
    df = pd.read_csv(BRONZE / "erp_cust_az12.csv")
    print(f"[SILVER] ERP cust_az12 raw: {len(df)} rows")

    df["CID"] = df["CID"].apply(clean_string)
    # Extract trailing digits to join with CRM (e.g. NASAW00011000 / AW-00011000 -> 00011000)
    df["key_digits"] = df["CID"].str.extract(r"(\d+)$")[0]

    df["birthdate"] = pd.to_datetime(df["BDATE"], errors="coerce")
    # Filter unrealistic birth years
    mask_bad = df["birthdate"].notna() & ((df["birthdate"].dt.year < 1920) | (df["birthdate"].dt.year > 2015))
    df.loc[mask_bad, "birthdate"] = pd.NaT
    df["gender"] = df["GEN"].apply(standardize_gender)

    before = len(df)
    df = df.drop_duplicates(subset=["CID"], keep="first")
    print(f"[SILVER] ERP cust after dedup: {len(df)} (removed {before - len(df)})")

    return df[["CID", "key_digits", "birthdate", "gender"]].rename(columns={"CID": "erp_cid"})

# ---------- ERP Location ----------
def process_erp_location():
    df = pd.read_csv(BRONZE / "erp_loc_a101.csv")
    print(f"[SILVER] ERP location raw: {len(df)} rows")

    df["CID"] = df["CID"].apply(clean_string)
    df["key_digits"] = df["CID"].str.extract(r"(\d+)$")[0]
    df["country"] = df["CNTRY"].apply(standardize_country)

    before = len(df)
    df = df.drop_duplicates(subset=["CID"], keep="first")
    print(f"[SILVER] ERP location after dedup: {len(df)} (removed {before - len(df)})")

    return df[["CID", "key_digits", "country"]].rename(columns={"CID": "erp_cid"})

# ---------- CRM Products + SCD Type 2 ----------
def process_crm_products():
    df = pd.read_csv(BRONZE / "crm_prd_info.csv")
    print(f"[SILVER] CRM products raw: {len(df)} rows")

    df["prd_nm"] = df["prd_nm"].apply(clean_string)
    df["prd_line"] = df["prd_line"].apply(lambda x: clean_string(x) if pd.notna(x) else None)
    df["prd_cost"] = pd.to_numeric(df["prd_cost"], errors="coerce")
    df["prd_start_dt"] = pd.to_datetime(df["prd_start_dt"], errors="coerce")
    df["prd_end_dt"] = pd.to_datetime(df["prd_end_dt"], errors="coerce")

    # Category id = first two segments joined by underscore (matches ERP PX_CAT)
    # e.g. CO-RF-FR-R92B-58 -> CO_RF
    df["cat_id"] = df["prd_key"].str.extract(r"^([A-Z]{2}-[A-Z]{2})")[0]
    df["cat_id"] = df["cat_id"].str.replace("-", "_", regex=False)
    # Short key used by sales_details (strip first two segments)
    # e.g. CO-RF-FR-R92B-58 -> FR-R92B-58 ; BI-RB-BK-R93R-62 -> BK-R93R-62
    df["product_key_short"] = df["prd_key"].str.replace(r"^[A-Z]{2}-[A-Z]{2}-", "", regex=True)

    # SCD Type 2: for products with end dates we keep history.
    # Flag current records
    df["is_current"] = df["prd_end_dt"].isna()
    df["effective_from"] = df["prd_start_dt"]
    df["effective_to"] = df["prd_end_dt"].fillna(pd.Timestamp("9999-12-31"))

    # Deduplicate exact duplicates
    before = len(df)
    df = df.drop_duplicates(subset=["prd_id", "prd_start_dt"], keep="first")
    print(f"[SILVER] CRM products after dedup: {len(df)} (removed {before - len(df)})")

    df = df.rename(columns={
        "prd_id": "product_id",
        "prd_key": "product_key",
        "prd_nm": "product_name",
        "prd_cost": "product_cost",
        "prd_line": "product_line",
        "prd_start_dt": "start_date",
        "prd_end_dt": "end_date",
    })
    return df

# ---------- ERP Product Categories ----------
def process_erp_categories():
    df = pd.read_csv(BRONZE / "erp_px_cat_g1v2.csv")
    print(f"[SILVER] ERP categories raw: {len(df)} rows")

    df["ID"] = df["ID"].apply(clean_string)
    df["CAT"] = df["CAT"].apply(clean_string)
    df["SUBCAT"] = df["SUBCAT"].apply(clean_string)
    df["MAINTENANCE"] = df["MAINTENANCE"].apply(lambda x: clean_string(x).title() if pd.notna(x) else "n/a")

    before = len(df)
    df = df.drop_duplicates(subset=["ID"], keep="first")
    print(f"[SILVER] ERP categories after dedup: {len(df)} (removed {before - len(df)})")

    return df.rename(columns={
        "ID": "category_id",
        "CAT": "category",
        "SUBCAT": "subcategory",
        "MAINTENANCE": "maintenance",
    })

# ---------- CRM Sales ----------
def process_crm_sales():
    df = pd.read_csv(BRONZE / "crm_sales_details.csv")
    print(f"[SILVER] CRM sales raw: {len(df)} rows")

    df["sls_ord_num"] = df["sls_ord_num"].apply(clean_string)
    df["sls_prd_key"] = df["sls_prd_key"].apply(clean_string)
    df["sls_cust_id"] = pd.to_numeric(df["sls_cust_id"], errors="coerce")

    df["order_date"] = df["sls_order_dt"].apply(parse_date)
    df["ship_date"] = df["sls_ship_dt"].apply(parse_date)
    df["due_date"] = df["sls_due_dt"].apply(parse_date)

    df["sales_amount"] = pd.to_numeric(df["sls_sales"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["sls_quantity"], errors="coerce")
    df["price"] = pd.to_numeric(df["sls_price"], errors="coerce")

    # Fix calculation errors: if sales != quantity * price, recalculate sales
    mask = (df["quantity"].notna()) & (df["price"].notna())
    calculated = df["quantity"] * df["price"]
    mismatch = mask & (df["sales_amount"].isna() | (df["sales_amount"] != calculated))
    fixed = int(mismatch.sum())
    df.loc[mismatch, "sales_amount"] = calculated.loc[mismatch]
    print(f"[SILVER] Fixed {fixed} sales amount calculation errors")

    # Remove rows with invalid key data
    before = len(df)
    df = df.dropna(subset=["sls_ord_num", "sls_prd_key", "sls_cust_id"])
    print(f"[SILVER] CRM sales after null-key removal: {len(df)} (removed {before - len(df)})")

    # Deduplicate on order + product
    before = len(df)
    df = df.drop_duplicates(subset=["sls_ord_num", "sls_prd_key"], keep="first")
    print(f"[SILVER] CRM sales after dedup: {len(df)} (removed {before - len(df)})")

    df = df.rename(columns={
        "sls_ord_num": "order_number",
        "sls_prd_key": "product_key",
        "sls_cust_id": "customer_id",
    })
    return df[["order_number", "product_key", "customer_id", "order_date", "ship_date",
               "due_date", "sales_amount", "quantity", "price"]]

# ---------- Main ----------
def run_silver():
    ensure_dirs()
    print("=" * 60)
    print("SILVER LAYER - Cleaning, Standardization & SCD")
    print("=" * 60)

    # Process each entity
    crm_cust = process_crm_customers()
    erp_cust = process_erp_customer()
    erp_loc = process_erp_location()
    crm_prd = process_crm_products()
    erp_cat = process_erp_categories()
    sales = process_crm_sales()

    # Enrich customers: join CRM + ERP birthdate/gender + location via trailing digits
    crm_cust["key_digits"] = crm_cust["customer_key"].str.extract(r"(\d+)$")[0]

    cust = crm_cust.merge(
        erp_cust[["key_digits", "birthdate", "gender"]].rename(columns={"gender": "erp_gender"}),
        on="key_digits", how="left"
    )
    cust = cust.merge(
        erp_loc[["key_digits", "country"]],
        on="key_digits", how="left"
    )

    # Prefer CRM gender if present, else ERP
    cust["gender"] = cust["gender"].where(cust["gender"] != "n/a", cust["erp_gender"])
    cust["gender"] = cust["gender"].fillna("n/a")
    cust["country"] = cust["country"].fillna("n/a")
    cust = cust.drop(columns=["key_digits", "erp_gender"], errors="ignore")

    # Enrich products with categories
    crm_prd = crm_prd.merge(
        erp_cat,
        left_on="cat_id",
        right_on="category_id",
        how="left"
    )
    crm_prd["category"] = crm_prd["category"].fillna("n/a")
    crm_prd["subcategory"] = crm_prd["subcategory"].fillna("n/a")
    crm_prd["maintenance"] = crm_prd["maintenance"].fillna("n/a")

    # Write silver tables
    tables = {
        "silver_customers.csv": cust,
        "silver_products.csv": crm_prd,
        "silver_categories.csv": erp_cat,
        "silver_sales.csv": sales,
    }
    for name, df in tables.items():
        path = SILVER / name
        df.to_csv(path, index=False)
        print(f"[SILVER] Wrote {path.name} | rows={len(df)}")

    print("[SILVER] Complete.\n")
    return tables

if __name__ == "__main__":
    run_silver()
