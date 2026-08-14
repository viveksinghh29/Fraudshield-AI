# Architecture

FraudShield AI follows Clean Architecture: routers validate and delegate, services hold business logic, repositories own data access, and the ML/LLM engines are consumed through narrow, swappable interfaces.

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│           React + TS + Vite Analyst Console (frontend/)          │
└───────────────────────────┬───────────────────────────────────────┘
                             │ HTTPS / REST / JWT
┌───────────────────────────▼───────────────────────────────────────┐
│                API LAYER  (app/api/v1/routers/*.py)                │
│  Pydantic validation • JWT/RBAC guards • rate limiting              │
│  Routes call services only — no business logic here                │
└───────────────────────────┬───────────────────────────────────────┘
                             │
┌───────────────────────────▼───────────────────────────────────────┐
│                  SERVICE LAYER (app/services/*.py)                  │
│  PredictionService • ExplanationService • ChatAssistantService      │
│  TransactionService • AnalyticsService • AuthService • ModelService  │
└───────┬───────────────┬──────────────┬──────────────┬─────────────┘
        │               │              │              │
┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼──────┐ ┌─────▼──────────┐
│ REPOSITORY   │ │  ML ENGINE  │ │ LLM ENGINE │ │  CACHE / QUEUE  │
│ LAYER        │ │ predictor.py│ │ 3 providers│ │  Redis + Celery │
│ (app/        │ │ explainer.py│ │ (Ollama/   │ │  (batch predict │
│ repositories)│ │ registry.py │ │ Groq/OpenAI│ │  + rate limits) │
└───────┬──────┘ └─────────────┘ └────────────┘ └─────────────────┘
        │
┌───────▼────────────────────────────────────────────────────────────┐
│                          DATA LAYER                                  │
│     PostgreSQL (8 tables, Alembic-migrated) + versioned .joblib      │
│     model artifacts (model, scaler, threshold, SHAP background)     │
└──────────────────────────────────────────────────────────────────┘
```

## Key design decisions and why

**Repository pattern, not raw ORM calls in services.** Every service depends on a repository interface, not SQLAlchemy directly — this is what let the test suite swap in a real (but disposable) Postgres transaction per test without touching business logic.

**One self-contained model artifact per version.** Each `.joblib` bundles the fitted model, its exact feature-column order, its optimal decision threshold, the training-fit `RobustScaler`, and a SHAP background sample. This was a deliberate fix during Phase 8: earlier, the scaler was saved separately with no link to a specific model version, which meant retraining had no way to guarantee the right scaler was paired with the right model at serve time.

**Grounded LLM context, not a system prompt alone.** The Analyst AI Assistant is never asked a question with only general knowledge — `context_builder.py` assembles the real prediction, real SHAP attributions, and real transaction fields into a structured block the model is explicitly instructed to answer only from. See `app/llm/prompt_templates.py`.

**Train → validate → test, not train → test.** The ML pipeline uses a genuine three-way split (Phase 6). An earlier version fit the scaler and cleaning statistics on train+test combined before splitting, and separately tuned the decision threshold directly on the test set — both real data-leakage bugs caught by a dedicated audit and fixed; see `app/ml/pipeline/split.py`'s docstring and `tests/integration/test_prepare_data_leakage.py`.

**Rate limiting keyed by user, with a separate stricter bucket for auth endpoints.** Discovered during Phase 14 that this had been silently non-functional since Phase 2 (the middleware captured a `None` Redis client at import time, before the app's lifespan ever ran) — see `app/core/rate_limiter.py`.

## Directory structure

```
fraudshield-ai/
├── backend/
│   ├── app/
│   │   ├── api/v1/routers/       # thin HTTP layer
│   │   ├── services/             # business logic
│   │   ├── repositories/         # data access
│   │   ├── models/               # SQLAlchemy ORM models
│   │   ├── schemas/               # Pydantic request/response DTOs
│   │   ├── ml/
│   │   │   ├── pipeline/         # data prep, training, evaluation
│   │   │   └── engine/           # inference-time predictor + explainer
│   │   ├── llm/                  # provider abstraction, guardrails, grounding
│   │   ├── tasks/                # Celery batch prediction
│   │   ├── core/                 # config, security, logging, rate limiting
│   │   └── db/                   # session/engine setup
│   ├── alembic/                  # migrations
│   └── tests/
│       ├── unit/
│       ├── integration/          # real Postgres, real HTTP via ASGITransport
│       └── manual_verification/  # mock LLM server for live-testing without network access
├── frontend/
│   └── src/
│       ├── pages/                # one file per route
│       ├── components/           # shared layout, charts, panels
│       ├── api/                  # typed client + React Query hooks
│       └── store/                # Zustand auth store
├── ml_research/                  # synthetic dataset generator + training reports
└── docs/                         # this directory
```

## Sequence: a single prediction, end to end

```
Analyst UI → POST /predict → PredictionService
    → ModelService (cached Predictor for the active model version)
    → Predictor.predict() (scaler.transform → model.predict_proba → risk bucket)
    → TransactionRepository.create() + PredictionRepository.create()
    → AuditRepository.log("PREDICTION_CREATED")
    → 200 { transaction_id, predicted_class, fraud_probability, risk_level }
```

## Sequence: a grounded chat turn

```
Analyst UI → POST /chat → ChatAssistantService
    → sanitize_user_input() (rejects prompt-injection patterns before any LLM call)
    → ExplanationService.explain_transaction() (real prediction + real SHAP)
    → context_builder.build_transaction_context() + render_context_as_text()
    → prompt_templates.build_system_prompt(context_block)
    → LLMProvider.generate(system_prompt, conversation_history)
    → ChatRepository persists both turns (context_snapshot only on the assistant's turn)
    → 200 { message, grounded: true, context_used: {...} }
```

Full request/response schemas: see `docs/api/README.md` or the live Swagger UI at `/docs`.
