# Data Dictionary – Gold Star Schema

## fact_sales

| Column           | Type     | Description                                      |
|------------------|----------|--------------------------------------------------|
| sales_sk         | INTEGER  | Surrogate key (primary)                          |
| order_number     | TEXT     | Business order number (e.g. SO43697)             |
| customer_sk      | INTEGER  | FK → dim_customers.customer_sk                   |
| product_sk       | INTEGER  | FK → dim_products.product_sk                     |
| geography_sk     | INTEGER  | FK → dim_geography.geography_sk                  |
| order_date_key   | INTEGER  | FK → dim_dates.date_key (YYYYMMDD)               |
| ship_date_key    | INTEGER  | FK → dim_dates.date_key                          |
| due_date_key     | INTEGER  | FK → dim_dates.date_key                          |
| sales_amount     | REAL     | Extended sales amount (qty × price, corrected)   |
| quantity         | INTEGER  | Units sold                                       |
| price            | REAL     | Unit price                                       |

## dim_customers

| Column           | Type     | Description                                      |
|------------------|----------|--------------------------------------------------|
| customer_sk      | INTEGER  | Surrogate key (primary)                          |
| customer_id_nk   | INTEGER  | Natural key from CRM                             |
| customer_key     | TEXT     | Business key (AWxxxxxxxx)                        |
| first_name       | TEXT     | First name                                       |
| last_name        | TEXT     | Last name                                        |
| full_name        | TEXT     | Concatenated name                                |
| marital_status   | TEXT     | Married / Single / n/a                           |
| gender           | TEXT     | Male / Female / n/a                              |
| create_date      | DATE     | Customer creation date                           |
| birthdate        | DATE     | Date of birth (from ERP)                         |
| age              | REAL     | Approximate age as of 2014-01-01                 |
| country          | TEXT     | Standardized country                             |

## dim_products

| Column             | Type    | Description                                    |
|--------------------|---------|------------------------------------------------|
| product_sk         | INTEGER | Surrogate key (primary)                        |
| product_id_nk      | INTEGER | Natural key from CRM                           |
| product_key        | TEXT    | Full product key                               |
| product_key_short  | TEXT    | Key used in sales transactions                 |
| product_name       | TEXT    | Product name                                   |
| product_cost       | REAL    | Cost                                           |
| product_line       | TEXT    | Product line code                              |
| start_date         | DATE    | Version start (SCD)                            |
| end_date           | DATE    | Version end (SCD, null = current)              |
| is_current         | BOOLEAN | Current version flag                           |
| effective_from     | DATE    | SCD effective from                             |
| effective_to       | DATE    | SCD effective to                               |
| cat_id             | TEXT    | Category key (links to ERP categories)         |
| category           | TEXT    | Category name                                  |
| subcategory        | TEXT    | Subcategory name                               |
| maintenance        | TEXT    | Maintenance flag                               |

## dim_dates

| Column        | Type    | Description                          |
|---------------|---------|--------------------------------------|
| date_key      | INTEGER | YYYYMMDD (primary / surrogate)       |
| full_date     | DATE    | Calendar date                        |
| year          | INTEGER | Year                                 |
| quarter       | INTEGER | Quarter (1-4)                        |
| month         | INTEGER | Month number                         |
| month_name    | TEXT    | Month name                           |
| day           | INTEGER | Day of month                         |
| day_of_week   | INTEGER | 1=Monday … 7=Sunday                  |
| day_name      | TEXT    | Weekday name                         |
| week_of_year  | INTEGER | ISO week number                      |
| is_weekend    | BOOLEAN | Weekend flag                         |

## dim_geography

| Column        | Type    | Description                          |
|---------------|---------|--------------------------------------|
| geography_sk  | INTEGER | Surrogate key (primary)              |
| country       | TEXT    | Standardized country name            |
| region        | TEXT    | Geographic region                    |
