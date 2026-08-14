# Testing Guide

## Running the test suite

```bash
cd backend
export SECRET_KEY="any-value-for-local-testing"
export POSTGRES_HOST=localhost
export REDIS_HOST=localhost
export APP_ENV=test   # required -- see note below
export PYTHONPATH=.

pytest tests/ -v
```

**`APP_ENV=test` is required**, not optional, when running the API-level
tests (`tests/integration/test_api_*.py`). Those tests drive the real
FastAPI app through `httpx.AsyncClient` + `ASGITransport`, and every
request in a test file shares one client identity (no distinct real IPs
the way production traffic has) -- with the rate limiter's fix from
Phase 14 actually working, unrelated tests in the same file would trip
each other's rate limit otherwise. `RateLimiterMiddleware` skips
limiting when `APP_ENV=test` specifically to avoid this, while
`tests/integration/test_rate_limiter.py`'s own tests pass
`force_enabled=True` to verify real limiting behavior regardless.

## Running with coverage

```bash
pytest tests/ --cov=app --cov-report=term-missing
# or, for a browsable HTML report:
pytest tests/ --cov=app --cov-report=html:docs/coverage
```

Current state: **201 tests, 86% line coverage** (up from 158 tests / 66%
at the start of Phase 15). An HTML report is checked into
`docs/coverage/index.html`.

## Test organization

- **`tests/unit/`** — pure logic, no database, no network. ML pipeline
  stages, SHAP explainer math, guardrails pattern matching, config
  validation, provider request-building (via `httpx.MockTransport`).
- **`tests/integration/`** — real Postgres, real repositories, and
  (for the `test_api_*.py` files) the real FastAPI app driven end-to-end
  over HTTP via `api_client` (see `conftest.py`).
- **`tests/manual_verification/`** — not part of the pytest suite; a
  mock LLM server used for one-off live verification of the full HTTP
  stack when no real Ollama/Groq/OpenAI endpoint is reachable (see its
  own README).

## Known, deliberate coverage gaps

Not every line is covered, and that's a deliberate choice, not an
oversight:

- **`app/ml/pipeline/train.py`, `tuning.py` (0%)** — the full training
  orchestrator and Optuna tuning loop. These were verified extensively
  via real end-to-end runs throughout Phases 6–15 (actual training on
  real data, real Optuna trials, real model registration), which is a
  stronger form of verification than a unit test mocking Optuna would
  provide -- but that means they don't show up as pytest coverage.
  Worth adding a fast smoke test (1 trial, tiny dataset) in a future
  pass if this project continues.
- **`app/main.py` lines 33-47 (lifespan Redis connection)** — ASGI
  lifespan hooks aren't triggered by `ASGITransport` without an
  explicit `LifespanManager`; low-risk code (a try/except around an
  optional connection) not worth the added test complexity here.
- **Router lines still uncovered** — mostly defensive branches (e.g.
  a `NotFoundError` path already covered by one test but not every
  permutation of it) rather than untested features.

## Regression tests worth knowing about

A few tests exist specifically because they caught a real bug during
development, and are the permanent guard against it recurring:

| Test | Bug it guards against |
|---|---|
| `test_rate_limiter.py::test_general_endpoint_blocks_after_limit_with_429` | Rate limiting was silently disabled entirely (Phase 2→14): middleware captured a `None` Redis client at import time, before the app's lifespan ever ran |
| `test_prediction_service.py::test_predict_single_persists_transaction_with_correct_field_casing` | `POST /predict` 500'd on every call: raw-row dict keys (`Time`, `V1`...) were passed straight into the ORM constructor, whose columns are lowercase |
| `test_prepare_data_leakage.py`, `test_split.py` | The data pipeline's scaler/imputer were fit on train+test combined before the split ever happened |
| `test_model_training.py::test_threshold_is_selected_on_validation_not_test` | The decision threshold was being tuned directly on the test set |
| `test_config_security.py` | `SECRET_KEY` validation referenced a class attribute Pydantic silently reinterpreted as a private-attribute descriptor, making the check a no-op |
| `test_api_batch_prediction.py` (indirectly) | Celery's `asyncio.run()` bridge broke when called from an already-running event loop (e.g. eager-mode testing) |
