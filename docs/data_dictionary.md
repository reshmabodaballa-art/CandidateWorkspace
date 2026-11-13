# Data Dictionary

## 1. customers

Stores customer master records.

| Column | Type | Rules |
|---|---|---|
| customer_id | String(50) | Primary key |
| name | String(150) | Required |
| email | String(255) | Required, unique |
| created_at | DateTime | Defaults to UTC timestamp |

## 2. orders

Stores customer order records.

| Column | Type | Rules |
|---|---|---|
| order_id | String(50) | Primary key |
| customer_id | String(50) | Required, foreign key to customers.customer_id |
| amount | Numeric(12,2) | Required, must be positive |
| status | String(30) | Required, must be a valid order status |
| created_at | DateTime | Required |
| updated_at | DateTime | Required |

**Grain:** One row per order.

## 3. ingestion_runs

Tracks each pipeline execution.

| Column | Type | Rules |
|---|---|---|
| run_id | String(36) | Primary key, generated UUID |
| status | String(30) | Defaults to running |
| started_at | DateTime | Defaults to UTC timestamp |
| ended_at | DateTime | Nullable |
| input_count | Integer | Defaults to 0 |
| output_count | Integer | Defaults to 0 |
| rejected_count | Integer | Defaults to 0 |
| error_message | Text | Nullable |

## 4. checkpoints

Stores pagination progress for each endpoint.

| Column | Type | Rules |
|---|---|---|
| endpoint | String(100) | Primary key |
| next_cursor | String(500) | Nullable |
| last_successful_run_id | String(36) | Nullable |
| updated_at | DateTime | Tracks checkpoint update time |

## 5. raw_api_responses

Preserves original API page responses for traceability.

| Column | Type | Rules |
|---|---|---|
| response_id | String(36) | Primary key, generated UUID |
| run_id | String(36) | Required, foreign key to ingestion_runs |
| endpoint | String(100) | Required |
| page_number | Integer | Required |
| request_cursor | String(500) | Nullable |
| next_cursor | String(500) | Nullable |
| http_status | Integer | Required |
| response_body | JSON | Required |
| fetched_at | DateTime | Defaults to UTC timestamp |

## 6. rejected_records

Stores records that fail validation or publishing.

| Column | Type | Rules |
|---|---|---|
| reject_id | String(36) | Primary key, generated UUID |
| run_id | String(36) | Required, foreign key to ingestion_runs |
| endpoint | String(100) | Required |
| source_record_id | String(100) | Nullable |
| raw_record | JSON | Required |
| rejection_reason | Text | Required |
| rejected_at | DateTime | Defaults to UTC timestamp |

## 7. order_history

Preserves previous order versions when newer versions are published.

| Column | Type | Rules |
|---|---|---|
| history_id | String(36) | Primary key, generated UUID |
| order_id | String(50) | Required |
| run_id | String(36) | Required, foreign key to ingestion_runs |
| record_snapshot | JSON | Required |
| captured_at | DateTime | Defaults to UTC timestamp |

## Relationships

- One customer can have multiple orders.
- Each order references one customer.
- Each raw API response belongs to an ingestion run.
- Each rejected record belongs to an ingestion run.
- Each order history snapshot belongs to an ingestion run.

## Business Rules

1. Customer IDs and order IDs must be unique.
2. Customer email addresses must be unique.
3. Every order must reference an existing customer.
4. Order amounts must be positive.
5. Required fields must not be missing or null.
6. Invalid records must be quarantined with rejection reasons.
7. Reprocessing identical records must not create duplicates.
8. Older order versions must not overwrite newer versions.
9. Newer order versions must preserve the previous version in order_history.
10. Timestamps are normalized to UTC for comparisons.
