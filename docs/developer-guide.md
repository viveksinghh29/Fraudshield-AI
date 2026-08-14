# Developer Guide

## Adding a new API endpoint

1. **Schema** — add request/response Pydantic models in `app/schemas/`.
2. **Repository method** (if new data access is needed) — add to the relevant `app/repositories/*.py`, extending `BaseRepository` for standard CRUD.
3. **Service method** — business logic goes in `app/services/`, never in the router. A service takes an `AsyncSession` in its constructor and orchestrates repositories/engines.
4. **Router** — thin: validate via the Pydantic schema, call `Depends(get_current_user)` or `Depends(require_role(...))` for auth, call the service, return the response schema. No business logic here.
5. **Wire it up** — add the router to `app/api/v1/api.py`.
6. **Test it** — add an API-level test in `tests/integration/test_api_*.py` using the `api_client` fixture (see `docs/testing-guide.md`), not just a service-layer unit test. This is the layer that historically caught real bugs (see the testing guide's regression table).

## Adding a new ML model candidate

1. Add a branch to `build_model()` and `default_search_space()` in `app/ml/pipeline/model_candidates.py`.
2. If it's a tree-based model, add it to `TREE_MODEL_TYPES` in `app/ml/engine/explainer.py` so SHAP explanations use the fast native `TreeExplainer` path rather than falling back to the much slower model-agnostic explainer (verified: ~1-20ms vs ~800-6800ms per explanation — see that file's docstring for the benchmark).
3. If its SHAP output isn't naturally in probability space (only Logistic Regression currently isn't), decide how to label `value_space` and make sure `fraud_probability` in responses always comes from `predict_proba()` directly, never reconstructed from SHAP values.

## Adding a new LLM provider

1. Implement `LLMProvider` (`app/llm/base_provider.py`) — just one method, `generate(system_prompt, messages) -> str`.
2. Accept an optional `http_client: httpx.AsyncClient | None` in the constructor (for `httpx.MockTransport`-based testing — see `tests/unit/test_llm_providers.py`).
3. Add a branch in `app/llm/provider_factory.py`.
4. Add the Literal value to `Settings.LLM_PROVIDER` in `app/core/config.py`.

## Database migrations

```bash
cd backend
alembic revision --autogenerate -m "description of the change"
```

**Always inspect the generated migration before applying it.** Autogenerate has at least two known false-positive/false-negative patterns in this codebase:
- It proposes dropping the `model_versions` partial unique index every time, because that index was created via raw `op.execute()` (Postgres partial indexes aren't expressible in SQLAlchemy's declarative layer) and autogenerate can't see it in the model metadata. Remove that line from the generated migration.
- Native Postgres ENUM types aren't dropped by a downgrade when their owning table is dropped — if you add a new enum column, add an explicit `sa.Enum(name='...').drop(op.get_bind(), checkfirst=True)` to the downgrade, or a later `alembic downgrade && alembic upgrade` cycle will fail with "type already exists" (this happened once already; see migration `2bb6878dd99a`'s downgrade for the pattern).

## Code style

- Type hints everywhere; `from __future__ import annotations` isn't used, so stick to `X | None` (Python 3.12+ union syntax) rather than `Optional[X]`.
- Repositories/services take `AsyncSession` via constructor injection, not `Depends()` directly (that's for routers).
- Custom exceptions (`app/core/exceptions.py`) over raw `HTTPException` — the global handler in `main.py` converts them to a consistent JSON shape automatically.
- Docstrings that explain *why*, not just *what*, especially anywhere a non-obvious decision was made (see almost any file in `app/ml/` or `app/llm/` for the pattern this codebase follows).

## Frontend conventions

- One file per route under `src/pages/`, wrapped in `<Protected>` (auth-gated + shared layout) in `App.tsx`.
- All server state goes through React Query hooks in `src/api/hooks.ts` — no ad-hoc `useEffect` fetches.
- Shared visual components (`RiskBadge`, `ExplanationPanel`, chart components) live in `src/components/`; reuse them rather than duplicating markup across pages.
- Tailwind only — no separate CSS files except `index.css`'s `@layer components` for genuinely repeated utility combinations (see `.input`).

## Known gaps / next steps if this project continues

- Real Kaggle dataset training run (everything so far verified against a synthetic, schema-matched stand-in — see `ml_research/README.md`).
- A live LLM backend (Ollama/Groq/OpenAI-compatible) has never actually been reachable in this build environment; the full request/response plumbing is verified (`tests/manual_verification/`), but real answer *quality* hasn't been.
- Fast smoke tests for `app/ml/pipeline/train.py`/`tuning.py` (currently 0% pytest coverage — verified instead via many real end-to-end training runs; see `docs/testing-guide.md`'s coverage-gaps section).
- Frontend bundle is a single ~750KB chunk; code-splitting (`React.lazy` per route) would help load time at scale.
