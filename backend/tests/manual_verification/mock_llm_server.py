"""Mock LLM server for testing provider HTTP requests, response parsing, and error handling."""

from fastapi import FastAPI, HTTPException, Request

app = FastAPI()

# Toggled by tests to exercise error-handling paths without restarting the server.
STATE = {"fail_mode": None}


@app.post("/api/chat")
async def ollama_chat(request: Request):
    """Mimics Ollama's /api/chat non-streaming response shape."""
    if STATE["fail_mode"] == "http_error":
        raise HTTPException(status_code=500, detail="simulated Ollama failure")
    if STATE["fail_mode"] == "malformed":
        return {"unexpected": "shape"}

    body = await request.json()
    last_user_message = body["messages"][-1]["content"]
    system_prompt = body["messages"][0]["content"]

    reply = (
        f"[mock-ollama:{body['model']}] Echoing back — I received a system prompt of "
        f"{len(system_prompt)} chars and your message: '{last_user_message[:80]}'"
    )
    return {
        "model": body["model"],
        "message": {"role": "assistant", "content": reply},
        "done": True,
    }


@app.post("/openai-mock/chat/completions")
async def openai_compatible_chat(request: Request):
    """Mimics the OpenAI/Groq /chat/completions response shape."""
    if STATE["fail_mode"] == "http_error":
        raise HTTPException(status_code=401, detail="simulated auth failure")
    if STATE["fail_mode"] == "malformed":
        return {"unexpected": "shape"}

    body = await request.json()
    auth_header = request.headers.get("authorization", "")
    last_user_message = body["messages"][-1]["content"]
    system_prompt = body["messages"][0]["content"]

    reply = (
        f"[mock-openai-compat:{body['model']}] auth={'present' if auth_header else 'missing'}, "
        f"system_prompt_len={len(system_prompt)}, your message: '{last_user_message[:80]}'"
    )
    return {
        "id": "mock-completion-1",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": reply}, "finish_reason": "stop"}],
    }


@app.post("/_test/set_fail_mode")
async def set_fail_mode(request: Request):
    body = await request.json()
    STATE["fail_mode"] = body.get("mode")
    return {"fail_mode": STATE["fail_mode"]}
