# YottaFlex AI - Data Engineering Pipeline

## Project Overview

A Python-based data engineering pipeline that ingests customer and order data from a paginated REST API, validates and transforms records, and publishes clean data into a relational database.

The project demonstrates API authentication, pagination, retry handling, checkpoint tracking, raw response retention, data validation, rejected-record quarantine, and safe database publishing.

## Technology Stack

- Python 3.13
- FastAPI - Mock REST API
- Requests - API communication
- SQLAlchemy - Database operations and ORM
- SQLite - Relational database
- python-dotenv - Environment configuration
- Pytest - Automated testing

## Project Structure

```text
CandidateWorkspace/
├── mock_api/
├── src/
│   ├── database/
│   ├── ingestion/
│   ├── transformation/
│   ├── validation/
│   ├── monitoring/
│   └── config.py
├── tests/
├── scripts/
├── docs/
├── data/
├── reports/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Features

1. REST API ingestion with Bearer token authentication.
2. Paginated data extraction.
3. Retry handling for temporary API failures.
4. Page-level checkpoint tracking.
5. Raw API response retention in the database.
6. Customer and order data transformation.
7. Data validation and rejected-record quarantine.
8. Customer-order relationship validation.
9. Safe publishing with duplicate and update handling.
10. Order history tracking.
11. Ingestion run monitoring and record counts.
12. Automated testing.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/reshmabodaballa-art/CandidateWorkspace.git
cd CandidateWorkspace
```

### 2. Create and Activate a Virtual Environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```powershell
Copy-Item .env.example .env
```

Update `.env` if required.

## Running the Project

### 1. Start the Mock API

Open the first terminal:

```powershell
python -m uvicorn mock_api.app:app --host 127.0.0.1 --port 8000
```

Keep this terminal running.

### 2. Initialize the Database

Open a second terminal:

```powershell
.\venv\Scripts\Activate.ps1
python -m src.database.init_db
```

### 3. Ingest Customers

```powershell
python -c "from src.ingestion.pipeline import run_ingestion; print(run_ingestion('customers'))"
```

### 4. Ingest Orders

```powershell
python -c "from src.ingestion.pipeline import run_ingestion; print(run_ingestion('orders'))"
```

### 5. Run Automated Tests

```powershell
python -m pytest -v
```

## Data Quality and Validation

The pipeline validates:

- Required fields.
- Valid customer references.
- Duplicate order identifiers.
- Positive numeric order amounts.
- Valid order statuses.
- Timezone-aware timestamps.

Invalid records are stored in the rejected-records table with their rejection reasons.

## Database Tables

- customers
- orders
- ingestion_runs
- checkpoints
- raw_api_responses
- rejected_records
- order_history

## Test Results

The full automated test suite currently passes **21 tests**.

Validation test cases include:

- Valid order.
- Unknown customer.
- Invalid amount.
- Duplicate order.
- Non-object record.
- Missing required field.

## Sample Data Results

| Metric | Result |
|---|---:|
| Customers | 10 |
| Orders | 100 |
| Missing customer references | 0 |
| Rejected records | 0 |
| Validation tests passed | 6/6 |

## Additional Documentation

- `docs/data_dictionary.md` - Database schemas, relationships, and business rules.
- `docs/architecture.md` - Pipeline architecture diagram.
- `docs/design_decisions.md` - Technical decisions and trade-offs.

## Scalable Dataset Generation

Generate a reproducible dataset:

```powershell
python scripts/generate_dataset.py --customers 1000 --orders 100000 --seed 42
```

The generator includes labelled edge cases such as duplicate orders, missing customer references, invalid statuses, missing amounts, and late/out-of-order records.

## Data Reconciliation

Run:

```powershell
python scripts/reconcile_dataset.py
```

Report: `reports/reconciliation_report.txt`

## Lookup Performance Benchmark

Run:

```powershell
python scripts/benchmark_lookup.py
```

Report: `reports/performance_report.txt`

Note: This is a lookup microbenchmark, not a full pipeline benchmark.

## Author

**Reshma Bodaballa**

B.Tech - Computer Science and Engineering