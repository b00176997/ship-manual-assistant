"""Local offline LLM via Ollama — used by the 'Offline AI' search depth.
Free, runs without internet. If Ollama isn't installed/running or the model
isn't pulled, the caller falls back to showing manual excerpts only."""
import json
import urllib.request

import config


def _api(path):
    return config.OLLAMA_URL.rstrip("/") + path


def is_available():
    """True only if the Ollama server is reachable AND the configured model is present."""
    try:
        with urllib.request.urlopen(_api("/api/tags"), timeout=2) as resp:
            tags = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return False
    names = [m.get("name", "") for m in tags.get("models", [])]
    want = config.OLLAMA_MODEL
    # Must match the exact tag we will ask for, otherwise generate() would fail with
    # "model not found". Only when no tag is configured do we accept any variant.
    if ":" in want:
        return want in names
    return any(n.split(":")[0] == want for n in names)


def generate(system, prompt):
    """Generate an answer locally. Raises on failure (caller handles the fallback)."""
    payload = {
        "model": config.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {"num_ctx": 8192, "temperature": 0.2},
    }
    req = urllib.request.Request(
        _api("/api/chat"),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        out = json.loads(resp.read().decode("utf-8"))
    return (out.get("message") or {}).get("content", "").strip()
