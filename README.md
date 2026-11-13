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
|-- mock_api/
|-- src/
|   |-- database/
|   |-- ingestion/
|   |-- transformation/
|   |-- validation/
|   |-- monitoring/
|   |-- config.py
|-- tests/
|-- data/
|-- docs/
|-- reports/
|-- logs/
|-- frontend/
|-- .env.example
|-- .gitignore
|-- requirements.txt
|-- README.md
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
12. Automated validation tests.

## Setup Instructions

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd CandidateWorkspace
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

Create your local `.env` file from the example:

```powershell
Copy-Item .env.example .env
```

Update `.env` if required.

## Running the Project

### 1. Start the mock API

Open the first terminal:

```powershell
python -m uvicorn mock_api.app:app --host 127.0.0.1 --port 8000
```

Keep this terminal running.

### 2. Initialize the database

Open a second terminal and activate the virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
python -m src.database.init_db
```

### 3. Ingest customers

```powershell
python -c "from src.ingestion.pipeline import run_ingestion; print(run_ingestion('customers'))"
```

### 4. Ingest orders

```powershell
python -c "from src.ingestion.pipeline import run_ingestion; print(run_ingestion('orders'))"
```

### 5. Run automated tests

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

Six automated validation tests passed:

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

## Author

**Reshma Bodaballa**

B.Tech - Computer Science and Engineering