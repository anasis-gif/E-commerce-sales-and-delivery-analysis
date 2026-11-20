"""Print compact findings from the Power BI-ready fact CSVs."""
from collections import defaultdict
from csv import DictReader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "data" / "exports"

def read(name):
    with (EXPORTS / name).open(encoding="utf-8-sig", newline="") as f:
        yield from DictReader(f)

def main():
    orders = {r["order_id"]: r for r in read("fact_order.csv")}
    category = defaultdict(float)
    state_revenue = defaultdict(float)
    state_orders = defaultdict(set)
    monthly_revenue = defaultdict(float)
    monthly_orders = defaultdict(set)
    for item in read("fact_order_item.csv"):
        order_id = item["order_id"]
        value = float(item["item_price"] or 0)
        category[item["product_category"]] += value
        order = orders.get(order_id, {})
        state = order.get("customer_state") or "Unknown"
        state_revenue[state] += value
        state_orders[state].add(order_id)
        month = (order.get("order_purchase_timestamp") or "")[:7]
        if month:
            monthly_revenue[month] += value
            monthly_orders[month].add(order_id)

    delay_groups = defaultdict(list)
    for order in orders.values():
        score, delay = order.get("review_score", ""), order.get("delivery_delay_days", "")
        if not score:
            continue
        if not delay:
            bucket = "Not delivered / missing dates"
        else:
            d = int(float(delay))
            bucket = "On time" if d <= 0 else "1-3 days late" if d <= 3 else "4-7 days late" if d <= 7 else "8+ days late"
        delay_groups[bucket].append(float(score))

    total = sum(category.values())
    print(f"Merchandise revenue: R$ {total:,.2f}")
    print("Top 10 categories:")
    for name, value in sorted(category.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {name.replace('_', ' ')}: R$ {value:,.2f} ({value/total:.1%})")
    print("Top 10 customer states:")
    for state, value in sorted(state_revenue.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {state}: R$ {value:,.2f}; {len(state_orders[state]):,} orders")
    print("Monthly AOV (complete months, Jan 2017-Aug 2018):")
    monthly = [(month, monthly_revenue[month]/len(monthly_orders[month]), len(monthly_orders[month])) for month in sorted(monthly_orders)]
    complete = [(m, a, n) for m, a, n in monthly if "2017-01" <= m <= "2018-08"]
    for month, aov, count in complete:
        print(f"  {month}: R$ {aov:,.2f}; {count:,} orders")
    print("Review score by delivery bucket:")
    for bucket in ("On time", "1-3 days late", "4-7 days late", "8+ days late", "Not delivered / missing dates"):
        scores = delay_groups.get(bucket, [])
        if scores:
            print(f"  {bucket}: {sum(scores)/len(scores):.2f}/5; {len(scores):,} reviewed orders")

if __name__ == "__main__":
    main()
