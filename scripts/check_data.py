"""Check that the expected Olist CSV extracts are present and readable."""
from csv import DictReader
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
EXPECTED = {
    "olist_orders_dataset.csv": {"order_id", "customer_id", "order_status", "order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"},
    "olist_order_items_dataset.csv": {"order_id", "order_item_id", "product_id", "seller_id", "price", "freight_value"},
    "olist_order_payments_dataset.csv": {"order_id", "payment_value", "payment_type"},
    "olist_order_reviews_dataset.csv": {"order_id", "review_id", "review_score"},
    "olist_customers_dataset.csv": {"customer_id", "customer_state"},
    "olist_products_dataset.csv": {"product_id", "product_category_name"},
    "olist_sellers_dataset.csv": {"seller_id", "seller_state"},
    "product_category_name_translation.csv": {"product_category_name", "product_category_name_english"},
}

def main() -> int:
    missing = []
    errors = []
    for filename, required in EXPECTED.items():
        path = RAW / filename
        if not path.is_file():
            missing.append(filename)
            continue
        try:
            with path.open(encoding="utf-8-sig", newline="") as stream:
                reader = DictReader(stream)
                absent = required - set(reader.fieldnames or [])
                count = sum(1 for _ in reader)
            if absent:
                errors.append(f"{filename}: missing columns {', '.join(sorted(absent))}")
            else:
                print(f"OK  {filename}: {count:,} rows")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{filename}: {exc}")
    if missing:
        print("Missing CSVs:")
        print("\n".join(f"  {name}" for name in missing))
    if errors:
        print("Problems:")
        print("\n".join(f"  {error}" for error in errors))
    if missing or errors:
        print(f"\nExpected files under: {RAW}")
        return 1
    print("\nAll expected extracts are present and have the required columns.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
