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


BREVITY = (
    "\nKeep the answer tight: list only the steps and warnings that answer the "
    "question. Do not restate the question, do not add commentary about the "
    "sources, and do not repeat the same point in different words."
)


def _post(payload):
    req = urllib.request.Request(
        _api("/api/chat"),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=900) as resp:
        return json.loads(resp.read().decode("utf-8"))


def generate(system, prompt):
    """Generate an answer locally. Raises on failure (caller handles the fallback)."""
    payload = {
        "model": config.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system + BREVITY},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        # Reasoning models (e.g. qwen3.6) otherwise spend the whole budget on a
        # hidden "thinking" pass and return an EMPTY answer. We are restating
        # text that is already in the prompt, so we don't need it.
        "think": False,
        "options": {
            "num_ctx": 8192,
            "temperature": 0.2,
            # Hard ceiling so a rambling model can't make the user wait minutes.
            "num_predict": config.OLLAMA_MAX_TOKENS,
        },
    }
    try:
        out = _post(payload)
    except urllib.error.HTTPError:
        # Older models reject the "think" option - retry without it.
        payload.pop("think", None)
        out = _post(payload)

    msg = out.get("message") or {}
    text = (msg.get("content") or "").strip()
    if not text and (msg.get("thinking") or "").strip():
        raise ValueError(
            "the model spent its whole budget reasoning - raise OLLAMA_MAX_TOKENS"
        )
    return text
