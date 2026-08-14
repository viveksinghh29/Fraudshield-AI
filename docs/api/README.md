# API Reference

Interactive docs (Swagger UI): `http://localhost:8000/docs` when running.
Interactive docs (ReDoc): `http://localhost:8000/redoc`.
Raw OpenAPI schema: `http://localhost:8000/openapi.json`.

All endpoints are prefixed with `/api/v1`. All require `Authorization: Bearer <access_token>` except `/auth/*` and `/health`.

## Auth

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/auth/register` | Public | Password requires 1 uppercase + 1 digit, min 8 chars |
| POST | `/auth/login` | Public | Returns `{access_token, refresh_token, token_type}` |
| POST | `/auth/refresh` | Refresh token | Issues a new access token |
| POST | `/auth/logout` | Refresh token | Revokes the session (reuse afterward → 401) |

## Users

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/users/me` | Any authenticated user | |
| GET | `/users` | Admin only | Paginated |
| GET | `/users/{user_id}` | Admin only | |
| POST | `/users/{user_id}/deactivate` | Admin only | |
| POST | `/users/{user_id}/reactivate` | Admin only | |

## Prediction

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/predict` | Any authenticated user | Body: `{Time, Amount, V1..V28}`. Returns `503 model_not_loaded` if no active model is registered |
| POST | `/predict/batch` | Any authenticated user | Query param `batch_id` (from a prior upload). Enqueues a Celery task, returns immediately |
| GET | `/predict/batch/{batch_id}/status` | Any authenticated user | Poll for `queued` / `processing` / `completed` |

## Transactions

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/transactions/upload` | Any authenticated user | Multipart CSV upload. Enforces `MAX_CSV_UPLOAD_SIZE_MB` (default 10MB, bounded chunked read) and `MAX_CSV_UPLOAD_ROWS` (default 50,000) |
| GET | `/transactions` | Any authenticated user | Paginated; filters: `risk_level`, `predicted_class`, `batch_id` |
| GET | `/transactions/{transaction_id}` | Any authenticated user | Full detail including all 28 raw feature values |

## Explainability

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/explain` | Any authenticated user | Body: `{transaction_id}`. Cached after first computation — repeat calls return the persisted explanation, not a recomputed one |

## Model Management

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/model/info` | Any authenticated user | Active model's algorithm, metrics (precision/recall/F1/ROC-AUC/PR-AUC, confusion matrix, calibration, SHAP importance) |

## Dashboard & Analytics

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/dashboard` | Any authenticated user | KPI summary + recent predictions |
| GET | `/analytics` | Any authenticated user | Query param `days` (default 30). Fraud trend, risk distribution, average confidence |

## Audit

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/audit-logs` | Admin only | Paginated; filter by `action` |

## Analyst AI Assistant

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/chat` | Any authenticated user | Body: `{message, transaction_id?}`. Grounded (real SHAP + prediction data) when `transaction_id` is given, general-purpose otherwise. Rejects prompt-injection patterns with `400` before any LLM call |
| GET | `/chat/history/{transaction_id}` | Any authenticated user | Persisted turns for that transaction |

## Health

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/health` | Public | Liveness + DB connectivity check. Never rate-limited |

## Standard error shape

Every error response (except FastAPI's own 422 validation errors, which use Pydantic's own shape) follows:

```json
{
  "error": "not_found",
  "message": "Transaction ...  not found.",
  "details": {}
}
```

| `error` code | HTTP status | Meaning |
|---|---|---|
| `not_found` | 404 | |
| `validation_error` | 422 | |
| `authentication_error` | 401 | |
| `authorization_error` | 403 | |
| `conflict` | 409 | e.g. duplicate email on register |
| `rate_limit_exceeded` | 429 | includes `retry_after_seconds` in `details` |
| `model_not_loaded` | 503 | no active model registered yet |
| `llm_provider_error` | 502 | the configured LLM provider (Ollama/Groq/OpenAI-compatible) failed or is unreachable |
| `prompt_injection_detected` | 400 | |

## Rate limits

- General endpoints: `RATE_LIMIT_PER_MINUTE` (default 60), keyed by user id (falls back to IP for unauthenticated requests)
- `/auth/login` and `/auth/register`: `AUTH_RATE_LIMIT_PER_MINUTE` (default 10), tracked separately from the general limit
