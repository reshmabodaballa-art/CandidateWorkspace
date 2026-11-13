import argparse
import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

SEED = 42
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

STATUSES = ["pending", "completed", "cancelled"]


def generate_dataset(customer_count=1000, order_count=10000, seed=SEED):
    rng = random.Random(seed)
    DATA_DIR.mkdir(exist_ok=True)

    customers = []
    for i in range(1, customer_count + 1):
        customers.append({
            "customer_id": f"CUST-{i:06d}",
            "name": f"Customer {i}",
            "email": f"customer{i}@example.com",
            "created_at": (
                datetime(2026, 1, 1, tzinfo=timezone.utc)
                + timedelta(days=i)
            ).isoformat(),
            "record_label": "normal"
        })

    orders = []
    for i in range(1, order_count + 1):
        created = datetime(2026, 2, 1, tzinfo=timezone.utc) + timedelta(
            minutes=i * 10
        )
        orders.append({
            "order_id": f"ORD-{i:08d}",
            "customer_id": f"CUST-{rng.randint(1, customer_count):06d}",
            "amount": round(rng.uniform(10, 5000), 2),
            "status": rng.choice(STATUSES),
            "created_at": created.isoformat(),
            "updated_at": (created + timedelta(hours=1)).isoformat(),
            "record_label": "normal"
        })

    # Add labelled edge cases when enough records are available.
    if orders:
        orders[0]["amount"] = 0
        orders[0]["record_label"] = "boundary_zero_amount"

    if len(orders) >= 2:
        orders[1]["customer_id"] = "CUST-MISSING"
        orders[1]["record_label"] = "invalid_customer_reference"

    if len(orders) >= 3:
        duplicate = orders[2].copy()
        duplicate["record_label"] = "duplicate_order"
        orders.append(duplicate)

    if len(orders) >= 4:
        orders[3]["status"] = "invalid_status"
        orders[3]["record_label"] = "invalid_status"

    if len(orders) >= 5:
        orders[4]["amount"] = ""
        orders[4]["record_label"] = "missing_amount"

    if len(orders) >= 6:
        orders[5]["updated_at"] = (
            datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat()
        )
        orders[5]["record_label"] = "late_or_out_of_order"

    write_csv(DATA_DIR / "customers.csv", customers)
    write_csv(DATA_DIR / "orders.csv", orders)

    print(f"Customers generated: {len(customers)}")
    print(f"Orders generated: {len(orders)}")
    print(f"Random seed: {seed}")
    print(f"Output directory: {DATA_DIR}")


def write_csv(path, records):
    if not records:
        return

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate reproducible customer and order datasets"
    )
    parser.add_argument("--customers", type=int, default=1000)
    parser.add_argument("--orders", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    if args.customers < 1 or args.orders < 0:
        parser.error("Customers must be at least 1 and orders cannot be negative")

    generate_dataset(args.customers, args.orders, args.seed)
