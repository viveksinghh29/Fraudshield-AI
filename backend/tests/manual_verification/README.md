# Manual Verification Utilities

This directory contains utilities for **manual end-to-end verification** that are separate from the automated pytest suite.

These scripts were used to verify the full HTTP stack in environments without network access to Ollama, Groq, or OpenAI.

## `mock_llm_server.py`

A lightweight FastAPI mock server that reproduces the response formats of:

* Ollama `/api/chat`
* OpenAI-compatible `/chat/completions`

It allows the real LLM provider implementations to be tested over an actual HTTP connection without requiring an external LLM service.

### What it verifies

The mock server can validate the complete request flow:

```text
API
 ↓
ChatAssistantService
 ↓
ExplanationService
 ↓
Context Builder
 ↓
LLM Provider
 ↓
HTTP Request
 ↓
Mock LLM Server
 ↓
Response Parsing
 ↓
Persistence
```

This provides an additional end-to-end check beyond the unit tests that use `httpx.MockTransport`.

### Run

**Terminal 1 — Start mock LLM server**

```bash
uvicorn tests.manual_verification.mock_llm_server:app --port 9501
```

**Terminal 2 — Configure and start the application**

```bash
export LLM_PROVIDER=ollama
export OLLAMA_BASE_URL=http://127.0.0.1:9501

uvicorn app.main:app --port 8000
```

Then send a normal `POST /api/v1/chat` request.

The mock response confirms that the request reached the provider with the expected grounded context and that the response was correctly parsed and persisted.

> **Note:** This verifies integration and request/response plumbing, not LLM response quality. Actual answer quality must be evaluated using a real Ollama, Groq, or OpenAI-compatible model.
