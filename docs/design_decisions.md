# Design Decisions and Trade-offs

## 1. Python

**Decision:** Use Python for ingestion, validation, transformation, and testing.

**Reason:** Python provides a simple ecosystem for API integration, data processing, and automated testing.

**Trade-off:** Python may require performance optimization for very large workloads.

## 2. FastAPI Mock API

**Decision:** Use a local FastAPI service to simulate paginated REST API responses.

**Reason:** It makes development and evaluation reproducible without depending on an external service.

**Trade-off:** The mock API does not fully represent every behavior of a production API.

## 3. SQLite Database

**Decision:** Use SQLite as the default local database.

**Reason:** It requires minimal setup and makes the project easy to run and evaluate.

**Trade-off:** SQLite has limited concurrency and scaling compared with PostgreSQL or other production databases.

## 4. SQLAlchemy ORM

**Decision:** Use SQLAlchemy for database operations.

**Reason:** It provides structured models, relationships, and database-independent query logic.

**Trade-off:** ORM operations can introduce overhead compared with carefully optimized raw SQL.

## 5. Retry Handling

**Decision:** Retry temporary connection failures and retryable HTTP status codes using backoff and Retry-After.

**Reason:** Temporary network and service failures should not immediately terminate ingestion.

**Trade-off:** Retries increase execution time when the API remains unavailable.

## 6. Checkpoint-Based Recovery

**Decision:** Store pagination progress in a checkpoint table.

**Reason:** A failed ingestion can resume from its saved cursor instead of restarting from the beginning.

**Trade-off:** Checkpoint correctness depends on committing progress safely with processed data.

## 7. Raw Response Retention

**Decision:** Store original API page responses.

**Reason:** Raw responses support auditing, debugging, and investigation of rejected records.

**Trade-off:** Retaining raw data increases database storage requirements.

## 8. Rejected Record Quarantine

**Decision:** Store invalid records separately with their rejection reasons.

**Reason:** Invalid records remain traceable without blocking valid records from being published.

**Trade-off:** Rejected records require a separate review and correction process.

## 9. Idempotent Publishing

**Decision:** Compare incoming records with existing records before inserting or updating.

**Reason:** Repeated ingestion should not create unintended duplicate records.

**Trade-off:** Comparing records and tracking versions adds processing complexity.

## 10. Order History

**Decision:** Preserve previous order snapshots when a newer version is published.

**Reason:** Historical changes remain available for auditing and troubleshooting.

**Trade-off:** History records increase storage usage.

## 11. Automated Testing

**Decision:** Use pytest for API retries, checkpoint recovery, validation, and publishing behavior.

**Reason:** Automated tests make important pipeline behavior reproducible and reduce regressions.

**Trade-off:** Tests require maintenance when business rules or implementation details change.
