"""
Pluggable model client layer.

If real API keys are present in the environment (OPENAI_API_KEY,
ANTHROPIC_API_KEY), the arena calls the real APIs and measures real
latency/cost. If no keys are set, it falls back to a MOCK mode that
simulates realistic latency and token cost so the whole project runs
and is demo-able with zero external dependencies / zero cost.

Set MOCK_MODE=false in .env once you add real keys to switch over.
"""

import os
import time
import random
import httpx

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"

# Registered models available in the arena.
AVAILABLE_MODELS = [
    "gpt-4o-mini",
    "claude-haiku",
    "claude-sonnet",
    "gemini-flash",
    "llama-3-8b",
    "mistral-7b",
]

# Rough $ per 1K output tokens, used for cost estimation (mock + display only)
COST_PER_1K_TOKENS = {
    "gpt-4o-mini": 0.0006,
    "claude-haiku": 0.0008,
    "claude-sonnet": 0.003,
    "gemini-flash": 0.0004,
    "llama-3-8b": 0.0002,
    "mistral-7b": 0.0002,
}

_MOCK_SNIPPETS = [
    "Here's a concise explanation: {topic} works by breaking the problem into smaller steps and reasoning through each one.",
    "In short, {topic} can be understood as a trade-off between accuracy and speed, depending on the constraints given.",
    "Let me walk through this. {topic} typically involves three stages: setup, processing, and evaluation.",
    "Good question — {topic} is best approached by first clarifying assumptions, then testing a small example.",
    "{topic} is a well-studied problem; the key insight is to reduce it to a simpler, previously solved case.",
]


def _mock_generate(model_name: str, prompt: str):
    """Simulates a model response with realistic latency + token cost."""
    base_latency = {
        "gpt-4o-mini": 400,
        "claude-haiku": 350,
        "claude-sonnet": 900,
        "gemini-flash": 300,
        "llama-3-8b": 250,
        "mistral-7b": 220,
    }.get(model_name, 400)

    latency_ms = base_latency + random.uniform(-80, 250)
    time.sleep(min(latency_ms, 1200) / 1000.0)  # actually simulate the wait, capped

    topic = prompt.strip()[:60] if prompt.strip() else "this topic"
    text = random.choice(_MOCK_SNIPPETS).format(topic=topic)

    output_tokens = max(20, len(text.split()) * 1.3)
    cost = round((output_tokens / 1000) * COST_PER_1K_TOKENS.get(model_name, 0.0005), 6)

    return text, round(latency_ms, 2), cost


def _real_generate_openai(model_name: str, prompt: str):
    api_key = os.getenv("OPENAI_API_KEY")
    start = time.time()
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 300,
        },
        timeout=30,
    )
    latency_ms = (time.time() - start) * 1000
    data = resp.json()
    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    out_tokens = usage.get("completion_tokens", 100)
    cost = round((out_tokens / 1000) * COST_PER_1K_TOKENS.get(model_name, 0.001), 6)
    return text, round(latency_ms, 2), cost


def _real_generate_anthropic(model_name: str, prompt: str):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    start = time.time()
    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model_name,
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )
    latency_ms = (time.time() - start) * 1000
    data = resp.json()
    text = "".join(block.get("text", "") for block in data.get("content", []))
    usage = data.get("usage", {})
    out_tokens = usage.get("output_tokens", 100)
    cost = round((out_tokens / 1000) * COST_PER_1K_TOKENS.get(model_name, 0.003), 6)
    return text, round(latency_ms, 2), cost


def generate_response(model_name: str, prompt: str):
    """
    Returns (response_text, latency_ms, cost_usd).
    Routes to a real API if MOCK_MODE is false and the model is
    recognized as OpenAI/Anthropic; otherwise uses the mock generator
    so the project runs standalone with no API keys required.
    """
    if not MOCK_MODE:
        try:
            if "gpt" in model_name and os.getenv("OPENAI_API_KEY"):
                return _real_generate_openai(model_name, prompt)
            if "claude" in model_name and os.getenv("ANTHROPIC_API_KEY"):
                return _real_generate_anthropic(model_name, prompt)
        except Exception as exc:  # fall back to mock on any API error
            print(f"[warn] real API call failed for {model_name}: {exc}, falling back to mock")

    return _mock_generate(model_name, prompt)


def pick_two_models(preferred_a=None, preferred_b=None):
    pool = AVAILABLE_MODELS.copy()
    model_a = preferred_a if preferred_a in pool else random.choice(pool)
    remaining = [m for m in pool if m != model_a]
    model_b = preferred_b if preferred_b in remaining else random.choice(remaining)
    return model_a, model_b
