#!/usr/bin/env python3


import sys
from pathlib import Path


from importlib import import_module

def main():
    print("\n" + "=" * 70)
    print("  RETAIL DATA PLATFORM - MEDALLION ARCHITECTURE PIPELINE")
    print("=" * 70 + "\n")

    # Bronze
    bronze = import_module("01_bronze_ingestion")
    bronze.run_bronze()

    # Silver
    silver = import_module("02_silver_cleaning")
    silver.run_silver()

    # Gold
    gold = import_module("03_gold_star_schema")
    gold.run_gold()

    print("=" * 70)
    print("  PIPELINE FINISHED SUCCESSFULLY")
    print("  Outputs available under data/bronze, data/silver, data/gold")
    print("  Query-ready SQLite DB: data/gold/retail_dw.db")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
