# System Architecture

```mermaid
flowchart TD
    A[Mock REST API] --> B[API Client]
    B --> C[Authentication and Retry Handling]
    C --> D[Pagination and Checkpoint Manager]
    D --> E[Raw API Response Storage]
    D --> F[Data Validation]
    F -->|Valid records| G[Transformation]
    F -->|Invalid records| H[Rejected Records / Quarantine]
    G --> I[Database Publisher]
    I --> J[(SQLite Database)]
    I --> K[Order History]
    D --> L[Ingestion Run Monitoring]
    F --> L
    I --> L
    M[Pytest Automated Tests] --> B
    M --> D
    M --> F
    M --> I
