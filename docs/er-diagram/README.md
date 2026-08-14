# Entity-Relationship Diagram

Renders natively on GitHub (Mermaid). 8 tables, all created via Alembic migrations in `backend/alembic/versions/`.

```mermaid
erDiagram
    USERS ||--o{ USER_SESSIONS : "has"
    USERS ||--o{ TRANSACTIONS : "uploads"
    USERS ||--o{ CHAT_HISTORY : "writes"
    USERS ||--o{ AUDIT_LOGS : "triggers"
    TRANSACTIONS ||--o{ PREDICTIONS : "scored by"
    TRANSACTIONS ||--o{ CHAT_HISTORY : "referenced in"
    PREDICTIONS ||--o| FRAUD_EXPLANATIONS : "explained by"
    MODEL_VERSIONS ||--o{ PREDICTIONS : "produces"

    USERS {
        uuid id PK
        string email UK
        string hashed_password
        string full_name
        enum role "admin | analyst | viewer"
        bool is_active
        timestamp created_at
        timestamp updated_at
    }

    USER_SESSIONS {
        uuid id PK
        uuid user_id FK
        string refresh_token_hash UK "SHA-256, never the raw token"
        string ip_address
        string user_agent
        timestamp expires_at
        bool revoked
    }

    TRANSACTIONS {
        uuid id PK
        string external_ref
        float time
        numeric amount
        float v1_to_v28 "28 PCA feature columns"
        uuid uploaded_by FK "nullable"
        uuid batch_id "nullable, groups CSV uploads"
        timestamp created_at
    }

    PREDICTIONS {
        uuid id PK
        uuid transaction_id FK
        uuid model_version_id FK
        enum predicted_class "fraud | legitimate"
        float fraud_probability
        enum risk_level "low | medium | high | critical"
        timestamp created_at
    }

    FRAUD_EXPLANATIONS {
        uuid id PK
        uuid prediction_id FK UK "one-to-one"
        jsonb shap_values
        jsonb top_features
        float base_value
        string value_space "probability | log_odds"
        text narrative_summary
    }

    MODEL_VERSIONS {
        uuid id PK
        string version_tag UK
        string algorithm
        jsonb metrics "precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix, calibration, SHAP importance"
        string artifact_path
        bool is_active "partial unique index enforces exactly one"
        timestamp trained_at
    }

    CHAT_HISTORY {
        uuid id PK
        uuid user_id FK
        uuid transaction_id FK "nullable, if not transaction-scoped"
        enum role "user | assistant"
        text message
        jsonb context_snapshot "grounding data used for this turn, assistant turns only"
        timestamp created_at
    }

    AUDIT_LOGS {
        uuid id PK
        uuid user_id FK "nullable, system events"
        string action
        string resource_type
        uuid resource_id
        jsonb log_metadata
        timestamp created_at
    }
```

## Notable constraints beyond the FK/PK relationships shown above

- **`model_versions`**: a partial unique index (`WHERE is_active = true`) guarantees at most one active model at the database level — added as defense-in-depth after the service-layer `ModelVersionRepository.activate()` logic, in case that invariant is ever bypassed by a direct write.
- **`fraud_explanations.prediction_id`** is unique, enforcing the one-to-one relationship with `predictions` at the schema level, not just in application code.
- **`user_sessions.refresh_token_hash`** stores a SHA-256 hash, never the raw token — the same principle as password hashing, so a database leak alone can't be used to forge sessions.
- **`audit_logs.log_metadata`** (not `metadata`) — `metadata` is a reserved attribute name on SQLAlchemy's declarative base and would have silently broken the model if used directly; caught during Phase 3.
