
import os
import shutil
from pathlib import Path
from datetime import datetime
import pandas as pd

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_CRM = BASE_DIR / "data" / "raw" / "crm"
RAW_ERP = BASE_DIR / "data" / "raw" / "erp"
BRONZE_DIR = BASE_DIR / "data" / "bronze"

def ensure_dirs():
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)

def ingest_file(src_path: Path, dest_name: str) -> dict:
    dest = BRONZE_DIR / dest_name
    shutil.copy2(src_path, dest)
    df = pd.read_csv(src_path)
    meta = {
        "source_file": src_path.name,
        "bronze_file": dest_name,
        "rows": len(df),
        "columns": list(df.columns),
        "ingested_at": datetime.utcnow().isoformat() + "Z",
        "size_bytes": dest.stat().st_size,
    }
    print(f"[BRONZE] Ingested {src_path.name} -> {dest_name} | rows={meta['rows']}")
    return meta

def run_bronze():
    ensure_dirs()
    print("=" * 60)
    print("BRONZE LAYER - Raw Ingestion (No Transformations)")
    print("=" * 60)

    sources = [
        (RAW_CRM / "cust_info.csv", "crm_cust_info.csv"),
        (RAW_CRM / "prd_info.csv", "crm_prd_info.csv"),
        (RAW_CRM / "sales_details.csv", "crm_sales_details.csv"),
        (RAW_ERP / "CUST_AZ12.csv", "erp_cust_az12.csv"),
        (RAW_ERP / "LOC_A101.csv", "erp_loc_a101.csv"),
        (RAW_ERP / "PX_CAT_G1V2.csv", "erp_px_cat_g1v2.csv"),
    ]

    metadata = []
    for src, dest_name in sources:
        if not src.exists():
            raise FileNotFoundError(f"Missing source file: {src}")
        metadata.append(ingest_file(src, dest_name))

    # Write ingestion log
    log_path = BRONZE_DIR / "_ingestion_log.csv"
    pd.DataFrame(metadata).to_csv(log_path, index=False)
    print(f"\n[BRONZE] Ingestion log written to {log_path}")
    print("[BRONZE] Complete.\n")
    return metadata

if __name__ == "__main__":
    run_bronze()
