import csv
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = BASE_DIR / "reports"


def read_csv(filename):
    with (DATA_DIR / filename).open(
        "r", newline="", encoding="utf-8"
    ) as file:
        return list(csv.DictReader(file))


def reconcile():
    customers = read_csv("customers.csv")
    orders = read_csv("orders.csv")

    customer_ids = [row["customer_id"] for row in customers]
    customer_id_set = set(customer_ids)

    order_ids = [row["order_id"] for row in orders]
    order_counts = Counter(order_ids)

    duplicate_orders = sum(
        count - 1 for count in order_counts.values() if count > 1
    )

    missing_customer_refs = sum(
        row["customer_id"] not in customer_id_set for row in orders
    )

    invalid_amounts = sum(
        not row["amount"]
        or float(row["amount"] or 0) <= 0
        for row in orders
    )

    invalid_statuses = sum(
        row["status"] not in {"pending", "completed", "cancelled"}
        for row in orders
    )

    duplicate_customers = len(customer_ids) - len(customer_id_set)

    results = [
        f"Customer rows: {len(customers)}",
        f"Order rows: {len(orders)}",
        f"Unique customers: {len(customer_id_set)}",
        f"Duplicate customers: {duplicate_customers}",
        f"Duplicate order rows: {duplicate_orders}",
        f"Missing customer references: {missing_customer_refs}",
        f"Invalid or missing amounts: {invalid_amounts}",
        f"Invalid order statuses: {invalid_statuses}",
    ]

    REPORT_DIR.mkdir(exist_ok=True)
    report_path = REPORT_DIR / "reconciliation_report.txt"
    report_path.write_text("\n".join(results) + "\n", encoding="utf-8")

    print("\n".join(results))
    print(f"\nReport saved: {report_path}")


if __name__ == "__main__":
    reconcile()
