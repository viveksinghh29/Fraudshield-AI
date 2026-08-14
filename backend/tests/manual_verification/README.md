# Manual Verification Utilities

This directory holds test utilities that are **not** part of the pytest
suite (`tests/unit/`, `tests/integration/`) — they were used for one-off
live verification of the full HTTP stack in an environment with no
network access to Ollama, Groq, or OpenAI.

## `mock_llm_server.py`

A minimal FastAPI app mimicking Ollama's `/api/chat` and the OpenAI-
compatible `/chat/completions` response shapes, closely enough to
genuinely exercise the real provider code (`OllamaProvider`,
`GroqProvider`, `OpenAICompatibleProvider`) end-to-end over a real
HTTP round trip.

This is **not** what the automated `httpx.MockTransport`-based tests in
`tests/unit/test_llm_providers.py` use — those are self-contained and
don't need a separate running process. This script was used for one
additional, higher-confidence check: pointing the *entire running app*
at it (`LLM_PROVIDER=ollama`, `OLLAMA_BASE_URL=http://127.0.0.1:9501`)
and confirming a real `POST /chat` request flows correctly through
every layer — API → ChatAssistantService → ExplanationService →
context_builder → a genuine network call — and back.

To reproduce:
```bash
# terminal 1
uvicorn tests.manual_verification.mock_llm_server:app --port 9501

# terminal 2
export LLM_PROVIDER=ollama
export OLLAMA_BASE_URL=http://127.0.0.1:9501
uvicorn app.main:app --port 8000
```

Then `POST /api/v1/chat` as normal — the mock server's reply will
confirm exactly how many characters of grounded system-prompt context
it received, proving the grounding pipeline actually ran.

**This verifies plumbing, not response quality.** It says nothing about
how a real Ollama/Groq/OpenAI model would actually answer — only that
the request reaches the provider correctly formatted and the response
is parsed and persisted correctly. Point `LLM_PROVIDER` at a real
backend to evaluate actual answer quality.
