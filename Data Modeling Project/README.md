# Retail Data Platform – Medallion Architecture

A complete end-to-end data engineering project that transforms raw, inconsistent CRM & ERP data into an analytics-ready **Star Schema** using the **Medallion Architecture** (Bronze → Silver → Gold).

---

## Problem Statement

A global retail organization stores transactional data across CRM and ERP systems in inconsistent formats and silos. Business teams struggle with fragmented data, calculation errors, and non-standardized categorical values (gender, marital status, country codes).

This project builds a centralized backend data platform that:

1. **Ingests** raw data without transformation (Bronze)
2. **Cleans, deduplicates, standardizes** and applies historical tracking (Silver)
3. **Models** the data into a high-performance Star Schema with surrogate keys (Gold)

---

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Source Systems │     │                 │     │                 │
│  CRM + ERP      │────▶│  Bronze Layer   │────▶│  Silver Layer   │
│  (CSV files)    │     │  Raw, immutable │     │  Clean + SCD    │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │   Gold Layer    │
                                                │  Star Schema    │
                                                │  Fact + Dims    │
                                                └─────────────────┘
```

### Bronze Layer
- Direct copy of source files
- No transformations – full data lineage preserved
- Ingestion metadata logged

### Silver Layer
- Deduplication (customers, products, sales)
- Standardization of gender, marital status, country
- Missing-value handling & data-type normalization
- Sales amount calculation fixes (`sales = quantity × price`)
- **SCD Type 2** on products (effective dates + `is_current` flag)
- Customer enrichment by joining CRM + ERP (birthdate, gender, country)
- Product enrichment with category hierarchy

### Gold Layer – Star Schema
| Table            | Type      | Description                                      |
|------------------|-----------|--------------------------------------------------|
| `fact_sales`     | Fact      | Sales transactions with measures & foreign keys  |
| `dim_customers`  | Dimension | Customer attributes + surrogate key              |
| `dim_products`   | Dimension | Product attributes + SCD history                 |
| `dim_dates`      | Dimension | Calendar attributes (year, quarter, month…)      |
| `dim_geography`  | Dimension | Country / region                                 |

All dimensions use **integer surrogate keys** for efficient joins.

---

## Project Structure

```
medallion_data_platform/
├── data/
│   ├── raw/
│   │   ├── crm/          # Original CRM CSVs
│   │   └── erp/          # Original ERP CSVs
│   ├── bronze/           # Raw ingested files + log
│   ├── silver/           # Cleaned intermediate tables
│   └── gold/             # Star schema CSVs + retail_dw.db
├── scripts/
│   ├── 01_bronze_ingestion.py
│   ├── 02_silver_cleaning.py
│   ├── 03_gold_star_schema.py
│   ├── 04_sample_analytics.sql
│   └── run_pipeline.py   # End-to-end orchestrator
├── docs/
└── README.md
```

---

## Source Datasets

| File                    | Source | Description                  | Approx. Rows |
|-------------------------|--------|------------------------------|--------------|
| `cust_info.csv`         | CRM    | Customer master              | 18 493       |
| `prd_info.csv`          | CRM    | Product master (with SCD)    | 397          |
| `sales_details.csv`     | CRM    | Sales transactions           | 60 398       |
| `CUST_AZ12.csv`         | ERP    | Customer birthdate & gender  | 18 483       |
| `LOC_A101.csv`          | ERP    | Customer country             | 18 484       |
| `PX_CAT_G1V2.csv`       | ERP    | Product category hierarchy   | 36           |

---

## How to Run

### Prerequisites
- Python 3.9+
- pandas, numpy (install via `pip install pandas numpy`)

### Execute full pipeline
```bash
cd medallion_data_platform
python scripts/run_pipeline.py
```

Or run layers individually:
```bash
python scripts/01_bronze_ingestion.py
python scripts/02_silver_cleaning.py
python scripts/03_gold_star_schema.py
```

### Query the Gold layer
```bash
sqlite3 data/gold/retail_dw.db
```
Then paste any query from `scripts/04_sample_analytics.sql`.

---

## Key Design Decisions

1. **Surrogate Keys** – Integer SKs on every dimension for join performance and SCD stability.
2. **SCD Type 2** – Product dimension retains history via `effective_from` / `effective_to` / `is_current`.
3. **Date Dimension** – Generated from the full range of order/ship/due dates; uses `YYYYMMDD` integer keys.
4. **Calculation Fixes** – Sales amount is recalculated when it does not match `quantity × price`.
5. **Key Harmonization** – CRM and ERP customer identifiers are normalized so they can be joined cleanly.
6. **SQLite Warehouse** – A ready-to-query database is produced alongside flat CSV files for BI tool consumption.

---

## Sample Insights Enabled

- Sales trends by year / quarter / month
- Top products by revenue
- Regional performance
- Customer demographic breakdowns
- Average order value by product line

---

## Author Notes

This implementation demonstrates production-style data engineering practices:

- Layered architecture with clear separation of concerns
- Idempotent scripts
- Explicit data quality corrections
- Dimensional modeling best practices
- Reproducible pipeline via a single entry-point script
