# Olist e-commerce sales and delivery analysis

Portfolio project built on the [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). The source contains roughly 100,000 Brazilian marketplace orders from 2016–2018. This workspace does not include the Kaggle files, so no findings or KPI values are fabricated.

## Project contents

- `sql/01_build_model.sql` — PostgreSQL staging imports, safe-grain fact views, and window-function analysis queries.
- `powerbi/Measures.dax` — core DAX measures for revenue, AOV, delivery, and reviews.
- `powerbi/PowerQuery.m` — CSV import queries and typed model tables.
- `scripts/check_data.py` — standard-library checks for expected CSV files, headers, and basic row counts.
- `scripts/build_exports.py` — builds the Power BI fact CSVs directly from the source files without extra Python packages.
- `data/raw/` — place the extracted Olist CSVs here (not committed).
- `data/exports/` — SQL result exports for Power BI (not committed).

## Load the data

Download and extract the Kaggle dataset, then copy its CSVs into `data/raw/`. The minimum set used here is orders, order items, payments, reviews, customers, products, sellers, and `product_category_name_translation`.

Run the file check from the project root:

```powershell
python scripts/check_data.py
```

From the project root, create a database named `olist_sales`, then run `psql -h localhost -U postgres -d olist_sales -f sql/02_load_olist.psql`. This creates the staging tables, loads all eight CSVs, builds the views, prints the analysis query results, and writes both Power BI exports into `data/exports/`. In Power BI Desktop, use **Get Data → Text/CSV** to load both exports, create the single-direction relationship `fact_order[order_id]` (one) to `fact_order_item[order_id]` (many), then add the measures from `powerbi/Measures.dax`.

## Dashboard layout

Create one report page titled **Sales & Delivery Pulse** with a date slicer and customer-state slicer:

1. KPI cards: Revenue, Orders, AOV, Average review, Late delivery rate.
2. Monthly line chart: AOV by order purchase month; optionally add revenue as a second visual to retain currency scale.
3. Category bar chart: Revenue by English product category, descending, top 10 plus an “Other” group if desired.
4. Regional bar/map: Revenue by customer state; use state abbreviation and label the geography as Brazil.
5. Delivery impact: average review score by delivery-delay bucket (`On time`, `1–3 days late`, `4–7 days late`, `8+ days late`, `Not delivered`). Add order count to tooltips. Exclude non-delivered orders from delay buckets and show them separately.

## Metric definitions and caveats

- Revenue is merchandise value (`order_items.price`) and excludes freight; it is not company net revenue or profit.
- AOV is merchandise revenue divided by distinct orders in the selected context. Category AOV is not used because category rows repeat orders.
- Customer region uses the customer state; seller state is available on item rows for seller analysis.
- Delay is delivered timestamp minus estimated delivery timestamp, in calendar days. Positive values are late. The review comparison is observational and does not establish causation.
- Payment and review tables can have multiple rows per order. They are aggregated to order grain before joining to prevent duplicated item revenue.
- The dataset is historical (2016–2018), anonymized, and should not be presented as current market performance.

## Questions answered by the model

`sql/01_build_model.sql` includes ranking/window queries for category and state revenue, monthly AOV, and review score by delay bucket. Populate the source tables and run the export steps before interpreting results.
