import csv
import random
from pathlib import Path
from time import perf_counter

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = BASE_DIR / "reports"


def main():
    with (DATA_DIR / "customers.csv").open(
        newline="", encoding="utf-8"
    ) as file:
        customers = list(csv.DictReader(file))

    customer_index = {
        customer["customer_id"]: customer
        for customer in customers
    }

    rng = random.Random(42)
    queries = [
        rng.choice(customers)["customer_id"]
        for _ in range(10000)
    ]

    start = perf_counter()
    linear_results = [
        next(
            (customer for customer in customers
             if customer["customer_id"] == customer_id),
            None
        )
        for customer_id in queries
    ]
    linear_time = perf_counter() - start

    start = perf_counter()
    indexed_results = [
        customer_index.get(customer_id)
        for customer_id in queries
    ]
    indexed_time = perf_counter() - start

    assert linear_results == indexed_results

    speedup = (
        linear_time / indexed_time
        if indexed_time > 0 else 0
    )

    results = [
        "Customer Lookup Performance Benchmark",
        f"Customers: {len(customers)}",
        f"Lookup operations: {len(queries)}",
        f"Linear search time: {linear_time:.6f} seconds",
        f"Dictionary lookup time: {indexed_time:.6f} seconds",
        f"Measured speedup: {speedup:.2f}x",
        "Result verification: PASSED"
    ]

    REPORT_DIR.mkdir(exist_ok=True)
    report_path = REPORT_DIR / "performance_report.txt"
    report_path.write_text("\n".join(results) + "\n", encoding="utf-8")

    print("\n".join(results))
    print(f"\nReport saved: {report_path}")


if __name__ == "__main__":
    main()
