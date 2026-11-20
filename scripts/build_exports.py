"""Build the two Power BI model CSVs from the Olist source extracts (stdlib only)."""
from collections import defaultdict
from csv import DictReader, DictWriter
from datetime import date
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "exports"

def rows(name):
    with (RAW / name).open(encoding="utf-8-sig", newline="") as f:
        yield from DictReader(f)

def write_csv(name, columns, records):
    with (OUT / name).open("w", encoding="utf-8-sig", newline="") as f:
        writer = DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

def main():
    OUT.mkdir(parents=True, exist_ok=True)

    customers = {r["customer_id"]: r for r in rows("olist_customers_dataset.csv")}
    payments = defaultdict(list)
    for r in rows("olist_order_payments_dataset.csv"):
        payments[r["order_id"]].append(float(r["payment_value"] or 0))
    reviews = defaultdict(list)
    for r in rows("olist_order_reviews_dataset.csv"):
        if r["review_score"]:
            reviews[r["order_id"]].append(int(r["review_score"]))

    order_records = []
    for o in rows("olist_orders_dataset.csv"):
        customer = customers.get(o["customer_id"], {})
        delivered = o["order_delivered_customer_date"][:10]
        estimated = o["order_estimated_delivery_date"][:10]
        delay = (date.fromisoformat(delivered) - date.fromisoformat(estimated)).days if delivered and estimated else ""
        pvals = payments.get(o["order_id"], [])
        scores = reviews.get(o["order_id"], [])
        purchase = o["order_purchase_timestamp"]
        order_records.append({
            "order_id": o["order_id"], "customer_id": o["customer_id"],
            "customer_state": customer.get("customer_state", ""),
            "customer_city": customer.get("customer_city", ""), "order_status": o["order_status"],
            "order_purchase_timestamp": purchase, "purchase_month": purchase[:7] + "-01" if purchase else "",
            "order_delivered_customer_date": o["order_delivered_customer_date"],
            "order_estimated_delivery_date": o["order_estimated_delivery_date"], "delivery_delay_days": delay,
            "payment_value": f"{sum(pvals):.2f}" if pvals else "",
            "payment_transaction_count": len(pvals) if pvals else "",
            "review_score": f"{mean(scores):.3f}" if scores else "", "review_count": len(scores) if scores else "",
        })
    write_csv("fact_order.csv", [
        "order_id", "customer_id", "customer_state", "customer_city", "order_status", "order_purchase_timestamp",
        "purchase_month", "order_delivered_customer_date", "order_estimated_delivery_date", "delivery_delay_days",
        "payment_value", "payment_transaction_count", "review_score", "review_count",
    ], order_records)

    products = {r["product_id"]: r for r in rows("olist_products_dataset.csv")}
    sellers = {r["seller_id"]: r for r in rows("olist_sellers_dataset.csv")}
    translations = {r["product_category_name"]: r["product_category_name_english"]
                    for r in rows("product_category_name_translation.csv")}
    item_records = []
    for i in rows("olist_order_items_dataset.csv"):
        product = products.get(i["product_id"], {})
        seller = sellers.get(i["seller_id"], {})
        category = product.get("product_category_name", "")
        item_records.append({
            "order_id": i["order_id"], "order_item_id": i["order_item_id"], "product_id": i["product_id"],
            "seller_id": i["seller_id"], "product_category": (translations.get(category, "") or category or "Unknown").replace("_", " "),
            "seller_state": seller.get("seller_state", ""), "item_price": i["price"], "freight_value": i["freight_value"],
        })
    write_csv("fact_order_item.csv", [
        "order_id", "order_item_id", "product_id", "seller_id", "product_category", "seller_state", "item_price", "freight_value",
    ], item_records)

    print(f"Wrote {len(order_records):,} orders to {OUT / 'fact_order.csv'}")
    print(f"Wrote {len(item_records):,} line items to {OUT / 'fact_order_item.csv'}")

if __name__ == "__main__":
    main()
