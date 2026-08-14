# Installation Guide

## Option A — Docker Compose (recommended)

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and set at minimum:
```bash
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
```

Then:
```bash
docker compose up --build
```

- Backend: http://localhost:8000/docs
- Frontend: http://localhost:5173
- Postgres, Redis, and a Celery worker all start automatically

## Option B — Local development (no Docker)

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 16 (or compatible)
- Redis 7 (or compatible)

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt --break-system-packages   # or omit the flag inside a venv

cp .env.example .env
# edit .env: set SECRET_KEY, and point POSTGRES_HOST / REDIS_HOST at localhost

alembic upgrade head
uvicorn app.main:app --reload
```

### Train an initial model

The API needs at least one registered model before `/predict` will work
(`GET /predict` otherwise returns `503 model_not_loaded`). Point this at
the real Kaggle Credit Card Fraud Detection dataset
(`Time, Amount, V1-V28, Class` columns) once you have it — see
`ml_research/README.md` for the synthetic-data stand-in used during
development in a sandboxed environment with no Kaggle access.

```bash
cd backend
python -m app.ml.pipeline.train --input path/to/creditcard.csv --n-trials 15
```

### Celery worker (for batch prediction)

```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Verifying the install

```bash
curl http://localhost:8000/api/v1/health
# {"status":"ok","service":"fraudshield-ai-backend","database":"ok"}
```

Register a user and confirm login works:
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"Password1","full_name":"Your Name","role":"admin"}'

curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"Password1"}'
```

## Running tests

See `docs/testing-guide.md`.

## Common issues

| Symptom | Likely cause |
|---|---|
| `503 model_not_loaded` on `/predict` | No model has been trained/registered yet — run the training command above |
| `502 llm_provider_error` on `/chat` | No real Ollama/Groq/OpenAI-compatible endpoint configured or reachable — set `LLM_PROVIDER` and its corresponding config in `.env` |
| `database: unavailable` in `/health` | Postgres isn't running or `POSTGRES_HOST`/credentials are wrong |
| Alembic migration fails on a fresh DB | Confirm `DATABASE_URL` (or the individual `POSTGRES_*` vars) point at an empty, existing database |
